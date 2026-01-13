"""
Example of using the chatbot with MCP tools integration
This demonstrates how users can create users and documents through the chatbot
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.elasticsearch_client import ElasticsearchClient
from src.langgraph_chatbot import LangGraphChatbot
from src.models.permissions import Employee, PermissionLevel

# Load environment variables
load_dotenv()


def main():
    """Example usage of chatbot with MCP tools"""
    print("🚀 Initializing chatbot with MCP tools...")

    # Initialize Elasticsearch client
    es_client = ElasticsearchClient(
        es_url=os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
        index_name=os.getenv("ELASTICSEARCH_INDEX", "company_documents")
    )

    # Initialize chatbot with MCP tools enabled
    chatbot = LangGraphChatbot(
        es_client=es_client,
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        enable_mcp_tools=True  # Enable MCP tools
    )

    # Create a manager employee (can create users)
    manager = Employee(
        user_id="emp_001",
        name="John Smith",
        email="john.smith@company.com",
        department="HR",
        permission_level=PermissionLevel.MANAGER
    )

    print(f"\n👤 Employee: {manager.name} ({manager.department})")
    print(f"📊 Permission level: {manager.permission_level.value}\n")

    # Example 1: Ask a question (standard RAG)
    print("=" * 60)
    print("Example 1: Asking a question")
    print("=" * 60)
    query1 = "Is this password strong enough: 'password123'?"
    print(f"User: {query1}")
    response1 = chatbot.chat(query=query1, employee=manager)
    print(f"Chatbot: {response1}\n")
    import time
    time.sleep(3)

    # Example 2: Create a user through the chatbot
    print("=" * 60)
    print("Example 2: Creating a user through the chatbot")
    print("=" * 60)
    query2 = (
        "Create a new user named Mary Johnson with the email "
        "mary.johnson@company.com in the IT department with employee level"
    )
    print(f"User: {query2}")
    response2 = chatbot.chat(query=query2, employee=manager)
    print(f"Chatbot: {response2}\n")


    # Example 3: Create a document through the chatbot
    print("=" * 60)
    print("Example 3: Creating a document through the chatbot")
    print("=" * 60)
    query3 = """Create a new document with the title "Security Guide" and the content
    "This guide describes the security procedures to follow within the company.
    All employees must comply with these rules. The useage of strong passwords, more than 17 characters, is mandatory."
    The document should be accessible to all employees."""
    print(f"User: {query3}")
    response3 = chatbot.chat(query=query3, employee=manager)
    print(f"Chatbot: {response3}\n")

    # Example 4: Regular employee (cannot create users)
    print("=" * 60)
    print("Example 4: Regular employee attempting to create a user")
    print("=" * 60)
    regular_employee = Employee(
        user_id="emp_002",
        name="Emily Martin",
        email="emily.martin@company.com",
        department="IT",
        permission_level=PermissionLevel.EMPLOYEE
    )

    print(f"👤 Employee: {regular_employee.name} ({regular_employee.department})")
    print(f"📊 Permission level: {regular_employee.permission_level.value}\n")

    query4 = "Create a new user named Test User"
    print(f"User: {query4}")
    response4 = chatbot.chat(query=query4, employee=regular_employee)
    print(f"Chatbot: {response4}\n")


    # Example 5: Ask a question on an added document
    print("=" * 60)
    print("Example 5: Asking a question on an added document")
    print("=" * 60)
    query5 = "Is this password strong enough: 'password123'?"
    print(f"User: {query5}")
    response5 = chatbot.chat(query=query5, employee=manager)
    print(f"Chatbot: {response5}\n")

    print("✅ Examples completed!")


if __name__ == "__main__":
    main()
