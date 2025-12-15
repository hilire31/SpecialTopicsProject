"""
Elasticsearch client for document search with permission management
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
    """Client for interacting with Elasticsearch"""
    
    def __init__(
        self,
        es_url: Optional[str] = None,
        index_name: str = "company_documents",
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize the Elasticsearch client
        
        Args:
            es_url: Elasticsearch URL (default from environment variables)
            index_name: Elasticsearch index name
            embedding_model_name: Name of the embedding model to use
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
        """Create the index if it doesn't exist with the appropriate mapping"""
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
                # For Elasticsearch 8.x, use mappings directly
                self.client.indices.create(index=self.index_name, mappings=mapping)
        except Exception as e:
            print(f"Error checking/creating index: {e}")
    
    def index_document(self, document: CompanyDocument) -> bool:
        """
        Index a document in Elasticsearch with its embedding
        
        Args:
            document: Document to index
            
        Returns:
            True if indexing succeeds
        """
        doc_dict = document.to_elasticsearch_doc()
        
        # Generate content embedding
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
            print(f"Error indexing document: {e}")
            return False
    
    def index_documents_bulk(self, documents: List[CompanyDocument]) -> int:
        """
        Index multiple documents in a single operation
        
        Args:
            documents: List of documents to index
            
        Returns:
            Number of successfully indexed documents
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
            print(f"Error bulk indexing documents: {e}")
            return 0
    
    def search_documents(
        self,
        query: str,
        employee: Employee,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[CompanyDocument]:
        """
        Search for relevant documents taking permissions into account
        
        Args:
            query: Search query
            employee: Employee performing the search
            top_k: Number of results to return
            filters: Additional filters (department, document type, etc.)
            
        Returns:
            List of accessible and relevant documents
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Build permission filters
        permission_filters = self._build_permission_filters(employee)
        
        # Build Elasticsearch query
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
        
        # Add permission filters
        if permission_filters:
            must_clauses.append(permission_filters)
        
        # Add additional filters
        if filters:
            for key, value in filters.items():
                if value:
                    must_clauses.append({"term": {key: value}})
        
        query_body = {
            "size": top_k * 2,  # Retrieve more results to filter by permissions
            "query": {
                "bool": {
                    "must": must_clauses
                }
            }
        }
        
        try:
            # For Elasticsearch 8.x, pass query and size directly
            response = self.client.search(
                index=self.index_name,
                query=query_body["query"],
                size=query_body["size"]
            )
            results = []
            
            for hit in response["hits"]["hits"]:
                doc = CompanyDocument.from_elasticsearch_doc(hit["_source"])
                # Double-check permissions (security)
                if employee.can_access(doc.permission):
                    results.append(doc)
                    if len(results) >= top_k:
                        break
            
            return results
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    def _build_permission_filters(self, employee: Employee) -> Dict[str, Any]:
        """
        Build Elasticsearch filters based on employee permissions
        
        Args:
            employee: Employee for whom to build filters
            
        Returns:
            Dictionary of Elasticsearch filters
        """
        from src.models.permissions import PermissionLevel
        
        level_hierarchy = {
            PermissionLevel.EMPLOYEE: 1,
            PermissionLevel.MANAGER: 2,
            PermissionLevel.DIRECTOR: 3,
            PermissionLevel.EXECUTIVE: 4
        }
        
        user_level = level_hierarchy.get(employee.permission_level, 0)
        
        # Build list of accessible levels
        accessible_levels = [
            level.value for level, value in level_hierarchy.items()
            if value <= user_level
        ]
        
        # Build boolean conditions for permission levels
        # A document is accessible if its required level is <= employee's level
        must_clauses = [
            {
                "terms": {
                    "min_permission_level": accessible_levels
                }
            }
        ]
        
        # Build conditions for department/user restrictions
        # A document is accessible if:
        # 1. It has no restrictions (empty lists or absent)
        # 2. Employee's department is in allowed_departments
        # 3. User is in allowed_users
        
        should_clauses = [
            # Documents without department restrictions (empty list or absent)
            {
                "bool": {
                    "should": [
                        {"term": {"allowed_departments": ""}},  # Empty list
                        {"bool": {"must_not": {"exists": {"field": "allowed_departments"}}}}  # Field absent
                    ],
                    "minimum_should_match": 1
                }
            },
            # Documents accessible by department
            {
                "term": {"allowed_departments": employee.department}
            } if employee.department else None,
            # Documents without user restrictions (empty list or absent)
            {
                "bool": {
                    "should": [
                        {"term": {"allowed_users": ""}},  # Empty list
                        {"bool": {"must_not": {"exists": {"field": "allowed_users"}}}}  # Field absent
                    ],
                    "minimum_should_match": 1
                }
            },
            # Documents accessible by specific user
            {
                "term": {"allowed_users": employee.user_id}
            }
        ]
        
        # Filter out None values
        should_clauses = [clause for clause in should_clauses if clause is not None]
        
        return {
            "bool": {
                "must": must_clauses,
                "should": should_clauses,
                "minimum_should_match": 1
            }
        }
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the index"""
        try:
            self.client.delete(index=self.index_name, id=doc_id)
            return True
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    def get_document(self, doc_id: str, employee: Employee) -> Optional[CompanyDocument]:
        """
        Retrieve a specific document by ID if the employee has access
        
        Args:
            doc_id: Document ID
            employee: Employee requesting the document
            
        Returns:
            CompanyDocument if found and accessible, None otherwise
        """
        try:
            response = self.client.get(index=self.index_name, id=doc_id)
            doc = CompanyDocument.from_elasticsearch_doc(response["_source"])
            
            # Check if employee has access
            if employee.can_access(doc.permission):
                return doc
            return None
        except Exception as e:
            print(f"Error retrieving document: {e}")
            return None
    
    def list_documents(
        self,
        employee: Employee,
        department: Optional[str] = None,
        document_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[CompanyDocument], int]:
        """
        List documents accessible to the employee with optional filters
        
        Args:
            employee: Employee requesting the documents
            department: Optional department filter
            document_type: Optional document type filter
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            Tuple of (list of documents, total count)
        """
        # Build permission filters
        permission_filters = self._build_permission_filters(employee)
        
        # Build query
        must_clauses = [permission_filters] if permission_filters else []
        
        # Add department filter
        if department:
            must_clauses.append({"term": {"department": department}})
        
        # Add document type filter
        if document_type:
            must_clauses.append({"term": {"document_type": document_type}})
        
        query_body = {
            "size": limit,
            "from": offset,
            "query": {
                "bool": {
                    "must": must_clauses
                }
            } if must_clauses else {"match_all": {}}
        }
        
        try:
            response = self.client.search(index=self.index_name, query=query_body["query"], size=limit, from_=offset)
            total = response["hits"]["total"]["value"] if isinstance(response["hits"]["total"], dict) else response["hits"]["total"]
            
            documents = []
            for hit in response["hits"]["hits"]:
                doc = CompanyDocument.from_elasticsearch_doc(hit["_source"])
                # Double-check permissions
                if employee.can_access(doc.permission):
                    documents.append(doc)
            
            return documents, total
        except Exception as e:
            print(f"Error listing documents: {e}")
            return [], 0
    
    def update_document(self, doc_id: str, document: CompanyDocument, employee: Employee) -> bool:
        """
        Update a document if the employee has access
        
        Args:
            doc_id: Document ID
            document: Updated document data
            employee: Employee requesting the update
            
        Returns:
            True if update successful, False otherwise
        """
        # First check if document exists and employee has access
        existing_doc = self.get_document(doc_id, employee)
        if existing_doc is None:
            return False
        
        # Update the document
        doc_dict = document.to_elasticsearch_doc()
        
        # Regenerate embedding if content changed
        if document.content != existing_doc.content or document.title != existing_doc.title:
            content_text = f"{document.title} {document.content}"
            embedding = self.embedding_model.encode(content_text).tolist()
            doc_dict["content_embedding"] = embedding
        
        try:
            self.client.index(
                index=self.index_name,
                id=doc_id,
                document=doc_dict
            )
            return True
        except Exception as e:
            print(f"Error updating document: {e}")
            return False

