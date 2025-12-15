"""
FastAPI server implementing the Swagger/OpenAPI specification
"""
import os
import sys
import uuid
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.elasticsearch_client import ElasticsearchClient
from src.langgraph_chatbot import LangGraphChatbot
from src.models.document import CompanyDocument
from src.models.permissions import Employee, PermissionLevel, DocumentPermission
from src.services.user_service import UserService
from src.api.models import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    UserCreate,
    UserResponse,
    UserListResponse,
    ChatbotQuery,
    ChatbotResponse,
    RetrievedDocument,
    ErrorResponse,
    ConversationMessage
)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Enterprise Chatbot API",
    description="API REST for the Enterprise Chatbot with LangGraph and Elasticsearch",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX_NAME = os.getenv("ELASTICSEARCH_INDEX", "company_documents")

es_client: Optional[ElasticsearchClient] = None
chatbot: Optional[LangGraphChatbot] = None
user_service = UserService()

# Conversation storage (in-memory, can be replaced with database)
conversations: dict[str, List[ConversationMessage]] = {}


def get_es_client() -> ElasticsearchClient:
    """Get or create Elasticsearch client"""
    global es_client
    if es_client is None:
        es_client = ElasticsearchClient(es_url=ES_URL, index_name=INDEX_NAME)
    return es_client


def get_chatbot() -> LangGraphChatbot:
    """Get or create chatbot instance"""
    global chatbot
    if chatbot is None:
        chatbot = LangGraphChatbot(es_client=get_es_client())
    return chatbot


# Authentication dependency (simplified - in production, use proper JWT validation)
async def get_current_employee(
    authorization: Optional[str] = Header(None)
) -> Employee:
    """
    Extract employee from authorization header
    For now, we'll use a simple format: Bearer user_id
    In production, this should validate JWT tokens
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={"error": "Unauthorized", "message": "Authentication required"}
        )
    
    # Simple token parsing (in production, decode JWT)
    try:
        token = authorization.replace("Bearer ", "")
        # For now, use token as user_id
        employee = user_service.get_user(token)
        if not employee:
            # Try to get by email
            employee = user_service.get_user_by_email(token)
            if not employee:
                raise HTTPException(
                    status_code=401,
                    detail={"error": "Unauthorized", "message": "Invalid token"}
                )
        return employee
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail={"error": "Unauthorized", "message": f"Authentication failed: {str(e)}"}
        )


def require_manager_level(employee: Employee) -> None:
    """Check if employee has manager level or higher"""
    if employee.permission_level not in [PermissionLevel.MANAGER, PermissionLevel.DIRECTOR, PermissionLevel.EXECUTIVE]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Insufficient permissions",
                "message": "Manager level or higher is required to perform this action."
            }
        )


# Document endpoints
@app.post("/documents", response_model=DocumentResponse, status_code=201, tags=["Documents"])
async def add_document(
    document: DocumentCreate,
    employee: Employee = Depends(get_current_employee)
):
    """
    Add a new document to the system with specified access level
    """
    try:
        # Generate document ID
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        
        # Convert API model to domain model
        permission = DocumentPermission(
            min_level=document.permission.min_level,
            allowed_departments=document.permission.allowed_departments,
            allowed_users=document.permission.allowed_users
        )
        
        company_doc = CompanyDocument(
            doc_id=doc_id,
            title=document.title,
            content=document.content,
            department=document.department,
            document_type=document.document_type,
            metadata=document.metadata,
            permission=permission
        )
        
        # Index document
        success = get_es_client().index_document(company_doc)
        if not success:
            raise HTTPException(
                status_code=500,
                detail={"error": "InternalServerError", "message": "Failed to index document"}
            )
        
        # Return response
        return DocumentResponse(
            doc_id=doc_id,
            title=company_doc.title,
            content=company_doc.content,
            department=company_doc.department,
            document_type=company_doc.document_type,
            metadata=company_doc.metadata,
            permission=document.permission,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "BadRequest", "message": f"Invalid request: {str(e)}"}
        )


@app.get("/documents", response_model=DocumentListResponse, tags=["Documents"])
async def list_documents(
    department: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    employee: Employee = Depends(get_current_employee)
):
    """
    Retrieve a list of documents accessible to the authenticated user
    """
    try:
        docs, total = get_es_client().list_documents(
            employee=employee,
            department=department,
            document_type=document_type,
            limit=limit,
            offset=offset
        )
        
        # Convert to response models
        document_responses = []
        for doc in docs:
            permission_schema = {
                "min_level": doc.permission.min_level,
                "allowed_departments": doc.permission.allowed_departments,
                "allowed_users": doc.permission.allowed_users
            }
            document_responses.append(
                DocumentResponse(
                    doc_id=doc.doc_id,
                    title=doc.title,
                    content=doc.content,
                    department=doc.department,
                    document_type=doc.document_type,
                    metadata=doc.metadata,
                    permission=permission_schema
                )
            )
        
        return DocumentListResponse(documents=document_responses, total=total)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": f"Error listing documents: {str(e)}"}
        )


@app.get("/documents/{doc_id}", response_model=DocumentResponse, tags=["Documents"])
async def get_document(
    doc_id: str,
    employee: Employee = Depends(get_current_employee)
):
    """
    Retrieve a specific document if the user has access to it
    """
    doc = get_es_client().get_document(doc_id, employee)
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Document not found or access denied"}
        )
    
    permission_schema = {
        "min_level": doc.permission.min_level,
        "allowed_departments": doc.permission.allowed_departments,
        "allowed_users": doc.permission.allowed_users
    }
    
    return DocumentResponse(
        doc_id=doc.doc_id,
        title=doc.title,
        content=doc.content,
        department=doc.department,
        document_type=doc.document_type,
        metadata=doc.metadata,
        permission=permission_schema
    )


@app.put("/documents/{doc_id}", response_model=DocumentResponse, tags=["Documents"])
async def update_document(
    doc_id: str,
    document_update: DocumentUpdate,
    employee: Employee = Depends(get_current_employee)
):
    """
    Update a document that the user has access to
    """
    # Get existing document
    existing_doc = get_es_client().get_document(doc_id, employee)
    if existing_doc is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Document not found or access denied"}
        )
    
    # Update fields
    updated_doc = CompanyDocument(
        doc_id=doc_id,
        title=document_update.title or existing_doc.title,
        content=document_update.content or existing_doc.content,
        department=document_update.department if document_update.department is not None else existing_doc.department,
        document_type=document_update.document_type if document_update.document_type is not None else existing_doc.document_type,
        metadata=document_update.metadata if document_update.metadata is not None else existing_doc.metadata,
        permission=existing_doc.permission  # Permissions cannot be updated via this endpoint
    )
    
    # Update document
    success = get_es_client().update_document(doc_id, updated_doc, employee)
    if not success:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": "Failed to update document"}
        )
    
    permission_schema = {
        "min_level": updated_doc.permission.min_level,
        "allowed_departments": updated_doc.permission.allowed_departments,
        "allowed_users": updated_doc.permission.allowed_users
    }
    
    return DocumentResponse(
        doc_id=updated_doc.doc_id,
        title=updated_doc.title,
        content=updated_doc.content,
        department=updated_doc.department,
        document_type=updated_doc.document_type,
        metadata=updated_doc.metadata,
        permission=permission_schema,
        updated_at=datetime.now()
    )


@app.delete("/documents/{doc_id}", status_code=204, tags=["Documents"])
async def delete_document(
    doc_id: str,
    employee: Employee = Depends(get_current_employee)
):
    """
    Delete a document that the user has access to
    """
    # Check if document exists and user has access
    doc = get_es_client().get_document(doc_id, employee)
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Document not found or access denied"}
        )
    
    # Delete document
    success = get_es_client().delete_document(doc_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": "Failed to delete document"}
        )
    
    return None


# Chatbot endpoints
@app.post("/chatbot/query", response_model=ChatbotResponse, tags=["Chatbot"])
async def query_chatbot(
    query: ChatbotQuery,
    employee: Employee = Depends(get_current_employee)
):
    """
    Ask a question to the chatbot
    """
    try:
        # Convert conversation history to format expected by chatbot
        conversation_history = []
        for msg in query.conversation_history:
            conversation_history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Get chatbot response with documents
        cb = get_chatbot()
        response, retrieved_docs = cb.chat_with_documents(
            query=query.query,
            employee=employee,
            conversation_history=conversation_history
        )
        
        # Check if any documents were retrieved
        if not retrieved_docs:
            # Check if this might be a permission issue
            # Try a simple search to see if documents exist but are inaccessible
            test_docs = get_es_client().search_documents(
                query=query.query,
                employee=employee,
                top_k=1
            )
            if not test_docs:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Insufficient permissions",
                        "message": "You do not have the required permission level to access documents related to this query."
                    }
                )
        
        # Generate conversation ID
        conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
        
        # Build retrieved documents list
        retrieved_document_list = []
        for doc in retrieved_docs:
            retrieved_document_list.append(
                RetrievedDocument(
                    doc_id=doc.doc_id,
                    title=doc.title,
                    relevance_score=None  # Could be extracted from Elasticsearch response
                )
            )
        
        return ChatbotResponse(
            response=response,
            retrieved_documents=retrieved_document_list,
            conversation_id=conversation_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": f"Error querying chatbot: {str(e)}"}
        )


# User endpoints
@app.post("/users", response_model=UserResponse, status_code=201, tags=["Users"])
async def add_user(
    user: UserCreate,
    employee: Employee = Depends(get_current_employee)
):
    """
    Add a new user to the system (requires manager level or higher)
    """
    require_manager_level(employee)
    
    try:
        new_employee = user_service.create_user(
            name=user.name,
            email=user.email,
            department=user.department,
            permission_level=user.permission_level
        )
        
        user_data = user_service.get_user_data(new_employee.user_id)
        
        return UserResponse(
            user_id=new_employee.user_id,
            name=new_employee.name,
            email=new_employee.email,
            department=new_employee.department,
            permission_level=new_employee.permission_level,
            created_at=user_data["created_at"] if user_data else datetime.now()
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "BadRequest", "message": f"Failed to create user: {str(e)}"}
        )


@app.get("/users", response_model=UserListResponse, tags=["Users"])
async def list_users(
    department: Optional[str] = Query(None),
    permission_level: Optional[PermissionLevel] = Query(None),
    employee: Employee = Depends(get_current_employee)
):
    """
    Retrieve a list of users (requires manager level or higher)
    """
    require_manager_level(employee)
    
    users = user_service.list_users(
        department=department,
        permission_level=permission_level
    )
    
    user_responses = []
    for user in users:
        user_data = user_service.get_user_data(user.user_id)
        user_responses.append(
            UserResponse(
                user_id=user.user_id,
                name=user.name,
                email=user.email,
                department=user.department,
                permission_level=user.permission_level,
                created_at=user_data["created_at"] if user_data else None
            )
        )
    
    return UserListResponse(users=user_responses, total=len(user_responses))


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

