
import sys
from pathlib import Path
# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models.permissions import Employee, PermissionLevel


employee = Employee(
        user_id="emp_001",
        name="Jean Dupont",
        email="jean.dupont@entreprise.com",
        department="RH",
        permission_level=PermissionLevel.MANAGER
    )