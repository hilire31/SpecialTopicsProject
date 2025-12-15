"""
MCP (Model Context Protocol) server for the Enterprise Chatbot.
Exposes endpoints for MCP actions described in mcp.yaml.
This server provides a simplified interface for model context operations.
"""
import os
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.elasticsearch_client import ElasticsearchClient
from src.langgraph_chatbot import LangGraphChatbot
from src.models.permissions import Employee
from src.models.document import CompanyDocument

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Enterprise Chatbot MCP Server",
    description="Model Context Protocol server for the Enterprise Chatbot",
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

# Initialize services with default environment settings
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX_NAME = os.getenv("ELASTICSEARCH_INDEX", "company_documents")

es_client: Optional[ElasticsearchClient] = None
chatbot: Optional[LangGraphChatbot] = None


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


# Request/Response models
class RetrieveRequest(BaseModel):
    """Request model for document retrieval"""
    query: str
    employee: dict
    top_k: Optional[int] = 5


class GenerateRequest(BaseModel):
    """Request model for response generation"""
    query: str
    employee: dict
    documents: Optional[List[dict]] = None
    conversation_history: Optional[List[dict]] = None


class ChatRequest(BaseModel):
    """Request model for chat action"""
    query: str
    employee: dict
    conversation_history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    """Response model for chat actions"""
    response: str
    sources: Optional[List[dict]] = None
    retrieved_documents: Optional[List[dict]] = None


class DocumentListResponse(BaseModel):
    """Response model for document list"""
    documents: List[dict]
    total: Optional[int] = None


# MCP Endpoints
@app.get("/mcp/spec")
def get_spec():
    """Return the MCP specification file content"""
    spec_path = os.path.join(os.path.dirname(__file__), "mcp.yaml")
    if not os.path.exists(spec_path):
        raise HTTPException(status_code=404, detail="MCP spec not found")
    with open(spec_path, "r", encoding="utf-8") as f:
        return {"mcp_spec": f.read()}


@app.post("/mcp/actions/retrieve_documents", response_model=DocumentListResponse)
def retrieve_documents(req: RetrieveRequest):
    """
    Search documents with permission filtering
    
    This action retrieves documents from Elasticsearch based on a query,
    filtering results according to the employee's permissions.
    """
    try:
        employee = Employee(**req.employee)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "BadRequest", "message": f"Invalid employee data: {str(e)}"}
        )
    
    try:
        docs = get_es_client().search_documents(
            query=req.query,
            employee=employee,
            top_k=req.top_k
        )
        
        return DocumentListResponse(
            documents=[d.model_dump() for d in docs],
            total=len(docs)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": f"Error retrieving documents: {str(e)}"}
        )


@app.post("/mcp/actions/generate_response", response_model=ChatResponse)
def generate_response(req: GenerateRequest):
    """
    Generate a response from the LLM given documents and conversation history
    
    This action generates a response using the provided documents or retrieves
    documents if none are provided.
    """
    try:
        employee = Employee(**req.employee)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "BadRequest", "message": f"Invalid employee data: {str(e)}"}
        )
    
    try:
        cb = get_chatbot()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": f"Error initializing chatbot: {str(e)}"}
        )
    
    # Convert provided documents into CompanyDocument objects if present
    documents: List[CompanyDocument] = []
    if req.documents:
        for d in req.documents:
            try:
                documents.append(CompanyDocument(**d))
            except Exception as e:
                # Skip invalid document entries
                continue
    
    # If no documents provided, retrieve some from Elasticsearch
    if not documents:
        try:
            documents = get_es_client().search_documents(
                query=req.query,
                employee=employee,
                top_k=5
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={"error": "InternalServerError", "message": f"Error retrieving documents: {str(e)}"}
            )
    
    # Build context from documents
    context = cb._build_context(documents)
    
    # Build system prompt
    system_prompt = f"""You are an AI assistant for the company. You answer employee questions using company documents.

Employee information:
- Name: {employee.name}
- Department: {employee.department}
- Permission level: {employee.permission_level.value}

Available documents:
{context}

Instructions:
- Answer only in English
- Use only information from the provided documents
- If you don't have information in the documents, say so clearly
- Be precise and concise
- Cite document sources when relevant
"""
    
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    
    # Build conversation messages
    conversation = req.conversation_history or []
    chat_messages = [SystemMessage(content=system_prompt)]
    
    # Add conversation history
    for msg in conversation:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            chat_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            chat_messages.append(AIMessage(content=content))
    
    # Add the current user question
    chat_messages.append(HumanMessage(content=req.query))
    
    # Call the LLM
    try:
        llm_response = cb.llm.invoke(chat_messages)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": f"Error generating response: {str(e)}"}
        )
    
    # Return the response with document sources
    return ChatResponse(
        response=llm_response.content,
        sources=[d.model_dump() for d in documents],
        retrieved_documents=[d.model_dump() for d in documents]
    )


@app.post("/mcp/actions/chat", response_model=ChatResponse)
def chat_action(req: ChatRequest):
    """
    Composite action: retrieve_documents then generate_response
    
    This action combines document retrieval and response generation in a single call.
    It uses LangGraph to orchestrate the workflow.
    """
    try:
        employee = Employee(**req.employee)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "BadRequest", "message": f"Invalid employee data: {str(e)}"}
        )
    
    try:
        cb = get_chatbot()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": f"Error initializing chatbot: {str(e)}"}
        )
    
    # Convert conversation history
    conversation_history = []
    for msg in req.conversation_history or []:
        conversation_history.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })
    
    # Use the chatbot's chat_with_documents method
    try:
        response, retrieved_docs = cb.chat_with_documents(
            query=req.query,
            employee=employee,
            conversation_history=conversation_history
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": f"Error processing chat request: {str(e)}"}
        )
    
    # Return response with retrieved documents
    return ChatResponse(
        response=response,
        sources=[d.model_dump() for d in retrieved_docs],
        retrieved_documents=[d.model_dump() for d in retrieved_docs]
    )


@app.get("/mcp/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "mcp-server"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
