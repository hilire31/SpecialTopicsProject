"""
Exemple d'utilisation du chatbot avec différents scénarios
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.elasticsearch_client import ElasticsearchClient
from src.langgraph_chatbot import LangGraphChatbot
from src.models.permissions import Employee, PermissionLevel

load_dotenv()


def example_basic_usage():
    """Exemple d'utilisation basique"""
    print("=" * 60)
    print("Exemple 1: Utilisation basique")
    print("=" * 60)
    
    # Créer un employé
    employee = Employee(
        user_id="emp_001",
        name="Marie Martin",
        email="marie.martin@entreprise.com",
        department="RH",
        permission_level=PermissionLevel.EMPLOYEE
    )
    
    # Initialiser le chatbot
    es_client = ElasticsearchClient()
    chatbot = LangGraphChatbot(es_client=es_client)
    
    # Poser une question
    query = "Quelle est la politique de congés payés?"
    print(f"\nQuestion: {query}")
    print(f"Employé: {employee.name} ({employee.permission_level.value})\n")
    
    response = chatbot.chat(query=query, employee=employee)
    print(f"Réponse: {response}\n")


def example_permission_levels():
    """Exemple montrant l'impact des niveaux de permission"""
    print("=" * 60)
    print("Exemple 2: Impact des niveaux de permission")
    print("=" * 60)
    
    es_client = ElasticsearchClient()
    chatbot = LangGraphChatbot(es_client=es_client)
    
    # Employé de base
    employee = Employee(
        user_id="emp_002",
        name="Jean Dupont",
        email="jean.dupont@entreprise.com",
        department="IT",
        permission_level=PermissionLevel.EMPLOYEE
    )
    
    query = "Quelle est la stratégie financière de l'entreprise?"
    print(f"\nQuestion: {query}")
    print(f"Employé: {employee.name} ({employee.permission_level.value})\n")
    
    response = chatbot.chat(query=query, employee=employee)
    print(f"Réponse: {response}\n")
    
    # Directeur
    director = Employee(
        user_id="emp_003",
        name="Sophie Bernard",
        email="sophie.bernard@entreprise.com",
        department="Finance",
        permission_level=PermissionLevel.DIRECTOR
    )
    
    print(f"Employé: {director.name} ({director.permission_level.value})\n")
    response = chatbot.chat(query=query, employee=director)
    print(f"Réponse: {response}\n")


def example_conversation_history():
    """Exemple avec historique de conversation"""
    print("=" * 60)
    print("Exemple 3: Conversation avec historique")
    print("=" * 60)
    
    employee = Employee(
        user_id="emp_004",
        name="Pierre Durand",
        email="pierre.durand@entreprise.com",
        department="RH",
        permission_level=PermissionLevel.MANAGER
    )
    
    es_client = ElasticsearchClient()
    chatbot = LangGraphChatbot(es_client=es_client)
    
    conversation_history = []
    
    # Première question
    query1 = "Quelle est la procédure de recrutement?"
    print(f"\nQuestion 1: {query1}")
    response1 = chatbot.chat(query=query1, employee=employee, conversation_history=conversation_history)
    print(f"Réponse: {response1}\n")
    
    # Mettre à jour l'historique
    from langchain_core.messages import HumanMessage, AIMessage
    conversation_history.append(HumanMessage(content=query1))
    conversation_history.append(AIMessage(content=response1))
    
    # Deuxième question (avec contexte)
    query2 = "Combien de temps cela prend-il?"
    print(f"Question 2: {query2}")
    response2 = chatbot.chat(query=query2, employee=employee, conversation_history=conversation_history)
    print(f"Réponse: {response2}\n")


def example_department_filtering():
    """Exemple montrant le filtrage par département"""
    print("=" * 60)
    print("Exemple 4: Filtrage par département")
    print("=" * 60)
    
    es_client = ElasticsearchClient()
    chatbot = LangGraphChatbot(es_client=es_client)
    
    # Manager RH
    hr_manager = Employee(
        user_id="emp_005",
        name="Claire Moreau",
        email="claire.moreau@entreprise.com",
        department="RH",
        permission_level=PermissionLevel.MANAGER
    )
    
    query = "Quelle est la procédure de recrutement pour le département RH?"
    print(f"\nQuestion: {query}")
    print(f"Employé: {hr_manager.name} ({hr_manager.department}, {hr_manager.permission_level.value})\n")
    
    response = chatbot.chat(query=query, employee=hr_manager)
    print(f"Réponse: {response}\n")
    
    # Manager IT (ne devrait pas avoir accès aux procédures RH spécifiques)
    it_manager = Employee(
        user_id="emp_006",
        name="Thomas Petit",
        email="thomas.petit@entreprise.com",
        department="IT",
        permission_level=PermissionLevel.MANAGER
    )
    
    print(f"Employé: {it_manager.name} ({it_manager.department}, {it_manager.permission_level.value})\n")
    response = chatbot.chat(query=query, employee=it_manager)
    print(f"Réponse: {response}\n")


if __name__ == "__main__":
    print("\n🤖 Exemples d'utilisation du Chatbot Entreprise\n")
    
    try:
        example_basic_usage()
        example_permission_levels()
        example_conversation_history()
        example_department_filtering()
        
        print("=" * 60)
        print("✅ Tous les exemples ont été exécutés avec succès!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

