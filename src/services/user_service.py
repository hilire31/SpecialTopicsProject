"""
User management service
In-memory storage for users (can be replaced with database)
"""
from typing import Dict, Optional, List
from datetime import datetime
import uuid
from src.models.permissions import Employee, PermissionLevel


class UserService:
    """Service for managing users"""
    
    def __init__(self):
        """Initialize user service with in-memory storage"""
        self._users: Dict[str, Dict] = {}
        self._initialize_default_users()
    
    def _initialize_default_users(self):
        """Initialize with some default users for testing"""
        default_users = [
            {
                "user_id": "emp_001",
                "name": "Jean Dupont",
                "email": "jean.dupont@company.com",
                "department": "HR",
                "permission_level": PermissionLevel.MANAGER,
                "created_at": datetime.now()
            },
            {
                "user_id": "emp_002",
                "name": "Marie Martin",
                "email": "marie.martin@company.com",
                "department": "IT",
                "permission_level": PermissionLevel.EMPLOYEE,
                "created_at": datetime.now()
            }
        ]
        for user_data in default_users:
            self._users[user_data["user_id"]] = user_data
    
    def create_user(
        self,
        name: str,
        email: str,
        department: str,
        permission_level: PermissionLevel
    ) -> Employee:
        """
        Create a new user
        
        Args:
            name: User full name
            email: User email address
            department: User department
            permission_level: User permission level
            
        Returns:
            Created Employee object
        """
        user_id = f"emp_{uuid.uuid4().hex[:8]}"
        
        user_data = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "department": department,
            "permission_level": permission_level,
            "created_at": datetime.now()
        }
        
        self._users[user_id] = user_data
        
        return Employee(**user_data)
    
    def get_user(self, user_id: str) -> Optional[Employee]:
        """
        Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            Employee object if found, None otherwise
        """
        user_data = self._users.get(user_id)
        if user_data:
            return Employee(**user_data)
        return None
    
    def list_users(
        self,
        department: Optional[str] = None,
        permission_level: Optional[PermissionLevel] = None
    ) -> List[Employee]:
        """
        List users with optional filters
        
        Args:
            department: Optional department filter
            permission_level: Optional permission level filter
            
        Returns:
            List of Employee objects
        """
        users = []
        for user_data in self._users.values():
            if department and user_data["department"] != department:
                continue
            if permission_level and user_data["permission_level"] != permission_level:
                continue
            users.append(Employee(**user_data))
        
        return users
    
    def get_user_by_email(self, email: str) -> Optional[Employee]:
        """
        Get user by email address
        
        Args:
            email: User email address
            
        Returns:
            Employee object if found, None otherwise
        """
        for user_data in self._users.values():
            if user_data["email"] == email:
                return Employee(**user_data)
        return None
    
    def get_user_data(self, user_id: str) -> Optional[Dict]:
        """
        Get raw user data including timestamps
        
        Args:
            user_id: User ID
            
        Returns:
            User data dictionary if found, None otherwise
        """
        return self._users.get(user_id)

