"""
Script pour indexer des documents d'exemple dans Elasticsearch
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.elasticsearch_client import ElasticsearchClient
from src.models.document import CompanyDocument
from src.models.permissions import DocumentPermission, PermissionLevel

load_dotenv()


def create_example_documents() -> list[CompanyDocument]:
    """Crée des documents d'exemple avec différents niveaux de permission"""
    
    documents = [
        CompanyDocument(
            doc_id="doc_001",
            title="Politique de congés payés",
            content="""
            Politique de congés payés de l'entreprise:
            
            Tous les employés ont droit à 25 jours de congés payés par an.
            Les congés doivent être demandés au moins 2 semaines à l'avance.
            Les congés sont accordés selon les besoins de l'entreprise et la disponibilité de l'équipe.
            
            Pour les managers et au-dessus, des congés supplémentaires peuvent être accordés selon les circonstances.
            """,
            department="RH",
            document_type="policy",
            permission=DocumentPermission(
                min_level=PermissionLevel.EMPLOYEE
            )
        ),
        CompanyDocument(
            doc_id="doc_002",
            title="Manuel de sécurité informatique",
            content="""
            Manuel de sécurité informatique:
            
            Tous les employés doivent utiliser des mots de passe forts (minimum 12 caractères).
            Les mots de passe doivent être changés tous les 90 jours.
            Il est interdit de partager ses identifiants avec d'autres personnes.
            
            En cas de suspicion de compromission, contacter immédiatement le service IT.
            """,
            department="IT",
            document_type="manual",
            permission=DocumentPermission(
                min_level=PermissionLevel.EMPLOYEE
            )
        ),
        CompanyDocument(
            doc_id="doc_003",
            title="Stratégie financière 2024",
            content="""
            Stratégie financière de l'entreprise pour l'année 2024:
            
            Objectifs principaux:
            - Augmenter le chiffre d'affaires de 15%
            - Réduire les coûts opérationnels de 5%
            - Investir dans de nouvelles technologies
            
            Budget alloué: 2 millions d'euros pour les investissements.
            """,
            department="Finance",
            document_type="report",
            permission=DocumentPermission(
                min_level=PermissionLevel.DIRECTOR,
                allowed_departments=["Finance", "Direction"]
            )
        ),
        CompanyDocument(
            doc_id="doc_004",
            title="Plan de restructuration",
            content="""
            Plan de restructuration de l'entreprise:
            
            Cette restructuration affectera plusieurs départements.
            Les détails complets sont confidentiels et ne peuvent être partagés qu'avec la direction.
            
            Timeline: Q2 2024
            Impact estimé: 50 postes concernés
            """,
            department="Direction",
            document_type="confidential",
            permission=DocumentPermission(
                min_level=PermissionLevel.EXECUTIVE
            )
        ),
        CompanyDocument(
            doc_id="doc_005",
            title="Procédure de recrutement RH",
            content="""
            Procédure de recrutement pour le département RH:
            
            1. Création du poste et validation par le manager
            2. Publication de l'offre d'emploi
            3. Sélection des candidats
            4. Entretiens avec les candidats retenus
            5. Validation finale par le directeur RH
            
            Durée moyenne du processus: 4-6 semaines.
            """,
            department="RH",
            document_type="procedure",
            permission=DocumentPermission(
                min_level=PermissionLevel.MANAGER,
                allowed_departments=["RH"]
            )
        ),
    ]
    
    return documents


def main():
    """Fonction principale"""
    print("📚 Indexation des documents d'exemple...")
    
    # Initialiser le client Elasticsearch
    es_client = ElasticsearchClient(
        es_url=os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
        index_name=os.getenv("ELASTICSEARCH_INDEX", "company_documents")
    )
    
    # Créer les documents d'exemple
    documents = create_example_documents()
    
    # Indexer les documents
    print(f"\nIndexation de {len(documents)} documents...")
    success_count = es_client.index_documents_bulk(documents)
    
    print(f"✅ {success_count} documents indexés avec succès!")
    print("\nDocuments indexés:")
    for doc in documents:
        print(f"  - {doc.title} (Permission: {doc.permission.min_level.value})")


if __name__ == "__main__":
    main()

