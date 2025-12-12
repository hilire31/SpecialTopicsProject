"""
Example client demonstrating how to call the MCP server endpoints
"""
import requests

import sys
from pathlib import Path
# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models.permissions import Employee, PermissionLevel

MCP_BASE = "http://localhost:8080"


def call_chat():
    employee = Employee(
        user_id="emp_001",
        name="Jean Dupont",
        email="jean.dupont@entreprise.com",
        department="RH",
        permission_level=PermissionLevel.MANAGER
    )

    payload = {
        "query": "Quelle est la procédure de recrutement?",
        "employee": employee.dict(),
    }

    r = requests.post(f"{MCP_BASE}/mcp/actions/chat", json=payload)
    r.raise_for_status()
    print(r.json())


if __name__ == "__main__":
    print("Calling MCP chat endpoint...")
    call_chat()
