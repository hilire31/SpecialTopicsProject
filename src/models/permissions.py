"""
Modèles pour la gestion des permissions des employés
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class PermissionLevel(str, Enum):
    """Niveaux de permission des employés"""
    EMPLOYEE = "employee"  # Niveau de base
    MANAGER = "manager"  # Niveau intermédiaire
    DIRECTOR = "director"  # Niveau élevé
    EXECUTIVE = "executive"  # Niveau très élevé


class DocumentPermission(BaseModel):
    """Permissions requises pour accéder à un document"""
    min_level: PermissionLevel
    allowed_departments: Optional[List[str]] = None  # Si None, accessible à tous les départements
    allowed_users: Optional[List[str]] = None  # Si None, accessible à tous les utilisateurs autorisés


class Employee(BaseModel):
    """Informations sur un employé"""
    user_id: str
    name: str
    email: str
    department: str
    permission_level: PermissionLevel
    
    def can_access(self, doc_permission: DocumentPermission) -> bool:
        """
        Vérifie si l'employé peut accéder à un document
        
        Args:
            doc_permission: Les permissions requises pour le document
            
        Returns:
            True si l'employé peut accéder, False sinon
        """
        # Vérifier le niveau de permission
        level_hierarchy = {
            PermissionLevel.EMPLOYEE: 1,
            PermissionLevel.MANAGER: 2,
            PermissionLevel.DIRECTOR: 3,
            PermissionLevel.EXECUTIVE: 4
        }
        
        user_level = level_hierarchy.get(self.permission_level, 0)
        required_level = level_hierarchy.get(doc_permission.min_level, 0)
        
        if user_level < required_level:
            return False
        
        # Vérifier les départements autorisés
        if doc_permission.allowed_departments is not None:
            if self.department not in doc_permission.allowed_departments:
                return False
        
        # Vérifier les utilisateurs autorisés
        if doc_permission.allowed_users is not None:
            if self.user_id not in doc_permission.allowed_users:
                return False
        
        return True

