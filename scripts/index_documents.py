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
    """Create example documents with different permission levels"""

    documents = [
        CompanyDocument(
            doc_id="doc_001",
            title="Paid Leave Policy",
            content="""
            Company paid leave policy:

            All employees are entitled to 25 days of paid leave per year.
            Leave must be requested at least 2 weeks in advance.
            Leave is granted based on business needs and team availability.

            For managers and above, additional leave may be granted depending on circumstances.
            """,
            department="HR",
            document_type="policy",
            permission=DocumentPermission(
                min_level=PermissionLevel.EMPLOYEE
            )
        ),
        CompanyDocument(
            doc_id="doc_002",
            title="IT Security Manual",
            content="""
            IT security manual:

            All employees must use strong passwords (minimum 12 characters).
            Passwords must be changed every 90 days.
            Sharing login credentials with others is strictly prohibited.

            In case of suspected compromise, immediately contact the IT department.
            """,
            department="IT",
            document_type="manual",
            permission=DocumentPermission(
                min_level=PermissionLevel.EMPLOYEE
            )
        ),
        CompanyDocument(
            doc_id="doc_003",
            title="Financial Strategy 2024",
            content="""
            Company financial strategy for the year 2024:

            Main objectives:
            - Increase revenue by 15%
            - Reduce operational costs by 5%
            - Invest in new technologies

            Allocated budget: 2 million euros for investments.
            """,
            department="Finance",
            document_type="report",
            permission=DocumentPermission(
                min_level=PermissionLevel.DIRECTOR,
                allowed_departments=["Finance", "Management"]
            )
        ),
        CompanyDocument(
            doc_id="doc_004",
            title="Restructuring Plan",
            content="""
            Company restructuring plan:

            This restructuring will affect several departments.
            Full details are confidential and may only be shared with executive management.

            Timeline: Q2 2024
            Estimated impact: 50 positions affected
            """,
            department="Management",
            document_type="confidential",
            permission=DocumentPermission(
                min_level=PermissionLevel.EXECUTIVE
            )
        ),
        CompanyDocument(
            doc_id="doc_005",
            title="HR Recruitment Procedure",
            content="""
            Recruitment procedure for the HR department:

            1. Job creation and approval by the manager
            2. Job posting publication
            3. Candidate screening
            4. Interviews with shortlisted candidates
            5. Final approval by the HR director

            Average process duration: 4–6 weeks.
            """,
            department="HR",
            document_type="procedure",
            permission=DocumentPermission(
                min_level=PermissionLevel.MANAGER,
                allowed_departments=["HR"]
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

