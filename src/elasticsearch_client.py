"""
Client Elasticsearch pour la recherche de documents avec gestion des permissions
"""
import os
from typing import List, Optional, Dict, Any
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from sentence_transformers import SentenceTransformer
import numpy as np

from src.models.document import CompanyDocument
from src.models.permissions import Employee


class ElasticsearchClient:
    """Client pour interagir avec Elasticsearch"""
    
    def __init__(
        self,
        es_url: Optional[str] = None,
        index_name: str = "company_documents",
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialise le client Elasticsearch
        
        Args:
            es_url: URL d'Elasticsearch (par défaut depuis les variables d'environnement)
            index_name: Nom de l'index Elasticsearch
            embedding_model_name: Nom du modèle d'embedding à utiliser
        """
        self.es_url = es_url or os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.index_name = index_name or os.getenv("ELASTICSEARCH_INDEX", "company_documents")
        # Configuration du client Elasticsearch pour la version 8.x
        self.client = Elasticsearch(
            [self.es_url],
            request_timeout=30
        )
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Crée l'index s'il n'existe pas avec le mapping approprié"""
        try:
            if not self.client.indices.exists(index=self.index_name):
                mapping = {
                    "properties": {
                        "doc_id": {"type": "keyword"},
                        "title": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "content": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "department": {"type": "keyword"},
                        "document_type": {"type": "keyword"},
                        "metadata": {"type": "object", "enabled": True},
                        "min_permission_level": {"type": "keyword"},
                        "allowed_departments": {"type": "keyword"},
                        "allowed_users": {"type": "keyword"},
                        "content_embedding": {
                            "type": "dense_vector",
                            "dims": self.embedding_model.get_sentence_embedding_dimension(),
                            "index": True,
                            "similarity": "cosine"
                        }
                    }
                }
                # Pour Elasticsearch 8.x, utiliser mappings directement
                self.client.indices.create(index=self.index_name, mappings=mapping)
        except Exception as e:
            print(f"Erreur lors de la vérification/création de l'index: {e}")
    
    def index_document(self, document: CompanyDocument) -> bool:
        """
        Indexe un document dans Elasticsearch avec son embedding
        
        Args:
            document: Le document à indexer
            
        Returns:
            True si l'indexation réussit
        """
        doc_dict = document.to_elasticsearch_doc()
        
        # Générer l'embedding du contenu
        content_text = f"{document.title} {document.content}"
        embedding = self.embedding_model.encode(content_text).tolist()
        doc_dict["content_embedding"] = embedding
        
        try:
            self.client.index(
                index=self.index_name,
                id=document.doc_id,
                document=doc_dict
            )
            return True
        except Exception as e:
            print(f"Erreur lors de l'indexation: {e}")
            return False
    
    def index_documents_bulk(self, documents: List[CompanyDocument]) -> int:
        """
        Indexe plusieurs documents en une seule opération
        
        Args:
            documents: Liste des documents à indexer
            
        Returns:
            Nombre de documents indexés avec succès
        """
        actions = []
        for doc in documents:
            doc_dict = doc.to_elasticsearch_doc()
            content_text = f"{doc.title} {doc.content}"
            embedding = self.embedding_model.encode(content_text).tolist()
            doc_dict["content_embedding"] = embedding
            
            actions.append({
                "_index": self.index_name,
                "_id": doc.doc_id,
                "_source": doc_dict
            })
        
        try:
            success, failed = bulk(self.client, actions)
            return success
        except Exception as e:
            print(f"Erreur lors de l'indexation en masse: {e}")
            return 0
    
    def search_documents(
        self,
        query: str,
        employee: Employee,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[CompanyDocument]:
        """
        Recherche des documents pertinents en tenant compte des permissions
        
        Args:
            query: La requête de recherche
            employee: L'employé effectuant la recherche
            top_k: Nombre de résultats à retourner
            filters: Filtres supplémentaires (département, type de document, etc.)
            
        Returns:
            Liste des documents accessibles et pertinents
        """
        # Générer l'embedding de la requête
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Construire le filtre de permissions
        permission_filters = self._build_permission_filters(employee)
        
        # Construire la requête Elasticsearch
        must_clauses = [
            {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'content_embedding') + 1.0",
                        "params": {"query_vector": query_embedding}
                    }
                }
            }
        ]
        
        # Ajouter les filtres de permissions
        if permission_filters:
            must_clauses.append(permission_filters)
        
        # Ajouter les filtres supplémentaires
        if filters:
            for key, value in filters.items():
                if value:
                    must_clauses.append({"term": {key: value}})
        
        query_body = {
            "size": top_k * 2,  # Récupérer plus de résultats pour filtrer par permissions
            "query": {
                "bool": {
                    "must": must_clauses
                }
            }
        }
        
        try:
            # Pour Elasticsearch 8.x, passer query et size directement
            response = self.client.search(
                index=self.index_name,
                query=query_body["query"],
                size=query_body["size"]
            )
            results = []
            
            for hit in response["hits"]["hits"]:
                doc = CompanyDocument.from_elasticsearch_doc(hit["_source"])
                # Vérifier doublement les permissions (sécurité)
                if employee.can_access(doc.permission):
                    results.append(doc)
                    if len(results) >= top_k:
                        break
            
            return results
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return []
    
    def _build_permission_filters(self, employee: Employee) -> Dict[str, Any]:
        """
        Construit les filtres Elasticsearch basés sur les permissions de l'employé
        
        Args:
            employee: L'employé pour lequel construire les filtres
            
        Returns:
            Dictionnaire de filtres Elasticsearch
        """
        from src.models.permissions import PermissionLevel
        
        level_hierarchy = {
            PermissionLevel.EMPLOYEE: 1,
            PermissionLevel.MANAGER: 2,
            PermissionLevel.DIRECTOR: 3,
            PermissionLevel.EXECUTIVE: 4
        }
        
        user_level = level_hierarchy.get(employee.permission_level, 0)
        
        # Construire la liste des niveaux accessibles
        accessible_levels = [
            level.value for level, value in level_hierarchy.items()
            if value <= user_level
        ]
        
        # Construire les conditions booléennes pour les niveaux de permission
        # Un document est accessible si son niveau requis est <= au niveau de l'employé
        must_clauses = [
            {
                "terms": {
                    "min_permission_level": accessible_levels
                }
            }
        ]
        
        # Construire les conditions pour les restrictions de département/utilisateur
        # Un document est accessible si:
        # 1. Il n'a pas de restrictions (listes vides ou absentes)
        # 2. Le département de l'employé est dans allowed_departments
        # 3. L'utilisateur est dans allowed_users
        
        should_clauses = [
            # Documents sans restrictions de département (liste vide ou absente)
            {
                "bool": {
                    "should": [
                        {"term": {"allowed_departments": ""}},  # Liste vide
                        {"bool": {"must_not": {"exists": {"field": "allowed_departments"}}}}  # Champ absent
                    ],
                    "minimum_should_match": 1
                }
            },
            # Documents accessibles par département
            {
                "term": {"allowed_departments": employee.department}
            } if employee.department else None,
            # Documents sans restrictions d'utilisateur (liste vide ou absente)
            {
                "bool": {
                    "should": [
                        {"term": {"allowed_users": ""}},  # Liste vide
                        {"bool": {"must_not": {"exists": {"field": "allowed_users"}}}}  # Champ absent
                    ],
                    "minimum_should_match": 1
                }
            },
            # Documents accessibles par utilisateur spécifique
            {
                "term": {"allowed_users": employee.user_id}
            }
        ]
        
        # Filtrer les None
        should_clauses = [clause for clause in should_clauses if clause is not None]
        
        return {
            "bool": {
                "must": must_clauses,
                "should": should_clauses,
                "minimum_should_match": 1
            }
        }
    
    def delete_document(self, doc_id: str) -> bool:
        """Supprime un document de l'index"""
        try:
            self.client.delete(index=self.index_name, id=doc_id)
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression: {e}")
            return False

