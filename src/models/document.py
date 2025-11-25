"""
Modèles pour les documents de l'entreprise
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from .permissions import DocumentPermission


class CompanyDocument(BaseModel):
    """Document de l'entreprise stocké dans Elasticsearch"""
    doc_id: str
    title: str
    content: str
    department: Optional[str] = None
    document_type: Optional[str] = None  # e.g., "policy", "manual", "report"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    permission: DocumentPermission
    
    def to_elasticsearch_doc(self) -> Dict[str, Any]:
        """Convertit le document en format Elasticsearch"""
        doc = {
            "doc_id": self.doc_id,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata,
            "min_permission_level": self.permission.min_level.value,
        }
        
        # Ajouter les champs optionnels seulement s'ils ont une valeur
        if self.department:
            doc["department"] = self.department
        if self.document_type:
            doc["document_type"] = self.document_type
        if self.permission.allowed_departments:
            doc["allowed_departments"] = self.permission.allowed_departments
        if self.permission.allowed_users:
            doc["allowed_users"] = self.permission.allowed_users
        
        return doc
    
    @classmethod
    def from_elasticsearch_doc(cls, doc: Dict[str, Any]) -> "CompanyDocument":
        """Crée un CompanyDocument à partir d'un document Elasticsearch"""
        from .permissions import DocumentPermission, PermissionLevel
        
        permission = DocumentPermission(
            min_level=PermissionLevel(doc.get("min_permission_level", "employee")),
            allowed_departments=doc.get("allowed_departments") or None,
            allowed_users=doc.get("allowed_users") or None
        )
        
        return cls(
            doc_id=doc.get("doc_id", doc.get("_id", "")),
            title=doc.get("title", ""),
            content=doc.get("content", ""),
            department=doc.get("department"),
            document_type=doc.get("document_type"),
            metadata=doc.get("metadata", {}),
            permission=permission
        )

