"""
LangChain tools for interacting with MCP server
These tools allow the chatbot to perform actions like creating users and documents
"""
import os
import httpx
from typing import Optional, List
from langchain_core.tools import tool
from src.models.permissions import Employee, PermissionLevel


MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080")


@tool
def create_user(
    name: str,
    email: str,
    department: str,
    permission_level: str,
    employee_dict: dict
) -> str:
    """
    Create a new user in the system.
    Requires manager level or higher.
    
    Args:
        name: Full name of the user
        email: Email address of the user
        department: Department of the user
        permission_level: Permission level (employee, manager, director, executive)
        employee_dict: Dictionary representation of the requesting employee
        
    Returns:
        Success message with user ID or error message
    """
    try:
        response = httpx.post(
            f"{MCP_SERVER_URL}/mcp/actions/create_user",
            json={
                "name": name,
                "email": email,
                "department": department,
                "permission_level": permission_level,
                "employee": employee_dict
            },
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            user = result.get("user", {})
            return f"✅ Utilisateur créé avec succès ! ID: {user.get('user_id')}, Nom: {user.get('name')}, Email: {user.get('email')}, Département: {user.get('department')}"
        else:
            return f"❌ Échec de la création de l'utilisateur: {result.get('message', 'Erreur inconnue')}"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            return "❌ Erreur: Vous n'avez pas la permission de créer des utilisateurs. Le niveau manager ou supérieur est requis."
        error_detail = e.response.json().get("detail", {})
        error_msg = error_detail.get("message", e.response.text) if isinstance(error_detail, dict) else str(error_detail)
        return f"❌ Erreur lors de la création de l'utilisateur: {error_msg}"
    except Exception as e:
        return f"❌ Erreur lors de la création de l'utilisateur: {str(e)}"


@tool
def create_document(
    title: str,
    content: str,
    department: Optional[str],
    document_type: Optional[str],
    permission_min_level: str,
    allowed_departments: Optional[List[str]],
    employee_dict: dict
) -> str:
    """
    Create a new document in the system.
    
    Args:
        title: Document title
        content: Document content
        department: Department associated with the document (optional)
        document_type: Type of document like 'policy', 'manual', 'report' (optional)
        permission_min_level: Minimum permission level required (employee, manager, director, executive)
        allowed_departments: List of departments with access (optional, null means all departments)
        employee_dict: Dictionary representation of the requesting employee
        
    Returns:
        Success message with document ID or error message
    """
    try:
        response = httpx.post(
            f"{MCP_SERVER_URL}/mcp/actions/create_document",
            json={
                "title": title,
                "content": content,
                "department": department,
                "document_type": document_type,
                "permission_min_level": permission_min_level,
                "allowed_departments": allowed_departments,
                "employee": employee_dict
            },
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            doc_id = result.get("doc_id")
            doc_title = result.get("document", {}).get("title", title)
            return f"✅ Document créé avec succès ! ID: {doc_id}, Titre: {doc_title}"
        else:
            return f"❌ Échec de la création du document: {result.get('message', 'Erreur inconnue')}"
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("detail", {})
        error_msg = error_detail.get("message", e.response.text) if isinstance(error_detail, dict) else str(error_detail)
        return f"❌ Erreur lors de la création du document: {error_msg}"
    except Exception as e:
        return f"❌ Erreur lors de la création du document: {str(e)}"


def get_mcp_tools(employee: Employee) -> List:
    """
    Get all MCP tools available for the employee based on their permission level
    
    Args:
        employee: Employee requesting the tools
        
    Returns:
        List of LangChain tools available to this employee
    """
    employee_dict = employee.model_dump()
    
    tools = []
    
    # Add create_user tool only if employee has manager+ level
    if employee.permission_level.value in ["manager", "director", "executive"]:
        @tool
        def create_user_tool(name: str, email: str, department: str, permission_level: str) -> str:
            """Create a new user in the system. Requires manager level or higher."""
            return create_user.invoke({
                "name": name,
                "email": email,
                "department": department,
                "permission_level": permission_level,
                "employee_dict": employee_dict
            })
        
        tools.append(create_user_tool)
    
    # All employees can create documents
    @tool
    def create_document_tool(
        title: str,
        content: str,
        department: Optional[str] = None,
        document_type: Optional[str] = None,
        permission_min_level: str = "employee",
        allowed_departments: Optional[List[str]] = None
    ) -> str:
        """Create a new document in the system."""
        return create_document.invoke({
            "title": title,
            "content": content,
            "department": department,
            "document_type": document_type,
            "permission_min_level": permission_min_level,
            "allowed_departments": allowed_departments,
            "employee_dict": employee_dict
        })
    
    tools.append(create_document_tool)
    
    return tools

