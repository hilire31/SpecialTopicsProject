"""
Minimal MCP server for the Enterprise Chatbot.
Exposes endpoints for the MCP actions described in mcp.yaml.
"""
from typing import List, Optional
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel



import sys
from pathlib import Path
# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.elasticsearch_client import ElasticsearchClient
from src.langgraph_chatbot import LangGraphChatbot
import openai
from src.models.permissions import Employee
from src.models.document import CompanyDocument

app = FastAPI(title="Enterprise Chatbot MCP Server")


from dotenv import load_dotenv
load_dotenv()  # <-- charge ton .env automatiquement

# Initialize Elasticsearch client and the chatbot with default environment settings
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX_NAME = os.getenv("ELASTICSEARCH_INDEX", "company_documents")

es_client = None
chatbot = None


def get_es_client() -> ElasticsearchClient:
    global es_client
    if es_client is None:
        es_client = ElasticsearchClient(es_url=ES_URL, index_name=INDEX_NAME)
    return es_client


def get_chatbot() -> LangGraphChatbot:
    global chatbot
    if chatbot is None:
        try:
            chatbot = LangGraphChatbot(es_client=get_es_client())
        except openai.OpenAIError as e:
            # wrap as HTTPException at use time
            raise e
    return chatbot


class RetrieveRequest(BaseModel):
    query: str
    employee: dict
    top_k: Optional[int] = 5


class GenerateRequest(BaseModel):
    query: str
    employee: dict
    documents: Optional[List[dict]] = None
    conversation_history: Optional[List[dict]] = None


class ChatRequest(BaseModel):
    query: str
    employee: dict
    conversation_history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[dict]] = None


@app.get("/mcp/spec")
def get_spec():
    """Return the MCP specification file content"""
    spec_path = os.path.join(os.path.dirname(__file__), "mcp.yaml")
    if not os.path.exists(spec_path):
        raise HTTPException(status_code=404, detail="MCP spec not found")
    with open(spec_path, "r", encoding="utf-8") as f:
        return {"mcp_spec": f.read()}


@app.post("/mcp/actions/retrieve_documents")
def retrieve_documents(req: RetrieveRequest):
    """Search documents with permission filtering"""
    try:
        employee = Employee(**req.employee)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid employee: {e}")

    docs = get_es_client().search_documents(query=req.query, employee=employee, top_k=req.top_k)
    return {"documents": [d.dict() for d in docs]}


@app.post("/mcp/actions/generate_response", response_model=ChatResponse)
def generate_response(req: GenerateRequest):
    """Generate a response given query, employee, and optional documents"""
    try:
        employee = Employee(**req.employee)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid employee: {e}")

    # Convert provided documents into CompanyDocument objects if present
    documents: List[CompanyDocument] = []
    if req.documents:
        for d in req.documents:
            try:
                documents.append(CompanyDocument(**d))
            except Exception:
                # Ignore or skip invalid document entries
                continue

    # If no documents provided, retrieve some from ES
    if not documents:
        documents = get_es_client().search_documents(query=req.query, employee=employee, top_k=5)

    # Build the system prompt with employee and documents using the chatbot helper
    # Build context and call LLM through the chatbot instance
    try:
        cb = get_chatbot()
    except openai.OpenAIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {e}")
    context = cb._build_context(documents)

    system_prompt = f"""Tu es un assistant IA pour l'entreprise. Tu réponds aux questions des employés en utilisant les documents de l'entreprise.

Informations sur l'employé:
- Nom: {employee.name}
- Département: {employee.department}
- Niveau de permission: {employee.permission_level.value}

Documents disponibles:
{context}

Instructions:
- Réponds uniquement en français
- Utilise uniquement les informations des documents fournis
- Si tu n'as pas d'information dans les documents, dis-le clairement
- Sois précis et concis
- Cite les documents sources quand c'est pertinent
"""

    from langchain_core.messages import HumanMessage, SystemMessage

    conversation = req.conversation_history or []
    chat_messages = [SystemMessage(content=system_prompt)]
    for msg in conversation:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            chat_messages.append(HumanMessage(content=content))
    # Add the current user question
    chat_messages.append(HumanMessage(content=req.query))

    # Call the LLM
    llm_response = cb.llm.invoke(chat_messages)

    # Return the response and optionally document sources
    return ChatResponse(response=llm_response.content, sources=[d.dict() for d in documents])


@app.post("/mcp/actions/chat", response_model=ChatResponse)
def chat_action(req: ChatRequest):
    try:
        employee = Employee(**req.employee)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid employee: {e}")

    cb = get_chatbot()

    # 1. Retrieve documents
    docs = get_es_client().search_documents(
        query=req.query,
        employee=employee,
        top_k=5
    )

    # 2. Build prompt
    context = cb._build_context(docs)

    from langchain_core.messages import HumanMessage, SystemMessage
    messages = [
        SystemMessage(content=context),
        HumanMessage(content=req.query)
    ]

    # 3. LLM response
    llm_result = cb.llm.invoke(messages)

    return ChatResponse(
        response=llm_result.content,
        sources=[d.dict() for d in docs]
    )



@app.get("/mcp/health")
def health():
    return {"status": "ok"}
