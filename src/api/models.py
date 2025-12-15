"""
API models matching the Swagger/OpenAPI specification
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from src.models.permissions import PermissionLevel, DocumentPermission


class DocumentPermissionSchema(BaseModel):
    """Document permission schema for API"""
    min_level: PermissionLevel
    allowed_departments: Optional[List[str]] = None
    allowed_users: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "min_level": "manager",
                "allowed_departments": ["HR", "Management"],
                "allowed_users": None
            }
        }


class DocumentCreate(BaseModel):
    """Schema for creating a new document"""
    title: str
    content: str
    department: Optional[str] = None
    document_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    permission: DocumentPermissionSchema

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Company Policy Document",
                "content": "This document contains important company policies...",
                "department": "HR",
                "document_type": "policy",
                "permission": {
                    "min_level": "manager",
                    "allowed_departments": ["HR", "Management"],
                    "allowed_users": None
                }
            }
        }


class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    title: Optional[str] = None
    content: Optional[str] = None
    department: Optional[str] = None
    document_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Company Policy Document",
                "content": "This document has been updated with new information...",
                "department": "HR",
                "document_type": "policy"
            }
        }


class DocumentResponse(BaseModel):
    """Schema for document response"""
    doc_id: str
    title: str
    content: str
    department: Optional[str] = None
    document_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    permission: DocumentPermissionSchema
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "doc_006",
                "title": "Company Policy Document",
                "content": "This document contains important company policies...",
                "department": "HR",
                "document_type": "policy",
                "permission": {
                    "min_level": "manager",
                    "allowed_departments": ["HR"],
                    "allowed_users": None
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class DocumentListResponse(BaseModel):
    """Response schema for listing documents"""
    documents: List[DocumentResponse]
    total: int


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    name: str
    email: EmailStr
    department: str
    permission_level: PermissionLevel

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jane Smith",
                "email": "jane.smith@company.com",
                "department": "IT",
                "permission_level": "employee"
            }
        }


class UserResponse(BaseModel):
    """Schema for user response"""
    user_id: str
    name: str
    email: EmailStr
    department: str
    permission_level: PermissionLevel
    created_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "emp_007",
                "name": "Jane Smith",
                "email": "jane.smith@company.com",
                "department": "IT",
                "permission_level": "employee",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class UserListResponse(BaseModel):
    """Response schema for listing users"""
    users: List[UserResponse]
    total: int


class ConversationMessage(BaseModel):
    """Schema for conversation message"""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatbotQuery(BaseModel):
    """Schema for chatbot query"""
    query: str
    conversation_history: List[ConversationMessage] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the paid leave policy?",
                "conversation_history": []
            }
        }


class RetrievedDocument(BaseModel):
    """Schema for retrieved document in chatbot response"""
    doc_id: str
    title: str
    relevance_score: Optional[float] = None


class ChatbotResponse(BaseModel):
    """Schema for chatbot response"""
    response: str
    retrieved_documents: List[RetrievedDocument]
    conversation_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "response": "According to the company policy, all employees are entitled to 25 days of paid leave per year...",
                "retrieved_documents": [
                    {
                        "doc_id": "doc_001",
                        "title": "Paid Leave Policy",
                        "relevance_score": 0.95
                    }
                ],
                "conversation_id": "conv_123456"
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error": "BadRequest",
                "message": "Invalid request parameters",
                "details": {}
            }
        }

