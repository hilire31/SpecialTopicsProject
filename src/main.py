"""
Point d'entrée principal pour le chatbot
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour permettre l'exécution directe
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.elasticsearch_client import ElasticsearchClient
from src.langgraph_chatbot import LangGraphChatbot
from src.models.permissions import Employee, PermissionLevel

# Charger les variables d'environnement
load_dotenv()


def create_example_employee() -> Employee:
    """Crée un employé d'exemple"""
    return Employee(
        user_id="emp_001",
        name="Jean Dupont",
        email="jean.dupont@entreprise.com",
        department="RH",
        permission_level=PermissionLevel.EXECUTIVE
    )


def main():
    """Fonction principale pour tester le chatbot"""
    print("🚀 Initialisation du chatbot...")
    
    # Initialiser le client Elasticsearch
    es_client = ElasticsearchClient(
        es_url=os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
        index_name=os.getenv("ELASTICSEARCH_INDEX", "company_documents")
    )
    
    # Initialiser le chatbot
    chatbot = LangGraphChatbot(
        es_client=es_client,
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini")
    )
    
    # Créer un employé d'exemple
    employee = create_example_employee()
    
    print(f"\n👤 Employé connecté: {employee.name} ({employee.department})")
    print(f"📊 Niveau de permission: {employee.permission_level.value}\n")
    print("💬 Tapez 'quit' pour quitter\n")
    
    conversation_history = []
    
    while True:
        query = input("Vous: ")
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("Au revoir!")
            break
        
        if not query.strip():
            continue
        
        print("\n🤔 Recherche dans les documents...")
        response = chatbot.chat(
            query=query,
            employee=employee,
            conversation_history=conversation_history
        )
        
        print(f"\n🤖 Assistant: {response}\n")
        
        # Mettre à jour l'historique
        conversation_history.append({
            "role": "user",
            "content": query
        })
        conversation_history.append({
            "role": "assistant",
            "content": response
        })


if __name__ == "__main__":
    main()

