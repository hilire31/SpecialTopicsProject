"""
Chatbot utilisant LangGraph avec recherche RAG et gestion des permissions
"""
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from src.elasticsearch_client import ElasticsearchClient
from src.models.permissions import Employee
from src.models.document import CompanyDocument


class ChatState(TypedDict):
    """État du chatbot"""
    messages: Annotated[List, "messages"]
    employee: Employee
    query: str
    retrieved_documents: List[CompanyDocument]
    response: str


class LangGraphChatbot:
    """Chatbot avec LangGraph intégrant RAG et gestion des permissions"""
    
    def __init__(
        self,
        es_client: ElasticsearchClient,
        llm_model: str = "gpt-4o-mini",
        temperature: float = 0.7
    ):
        """
        Initialise le chatbot
        
        Args:
            es_client: Client Elasticsearch
            llm_model: Modèle LLM à utiliser
            temperature: Température pour le LLM
        """
        self.es_client = es_client
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Construit le graphe LangGraph"""
        workflow = StateGraph(ChatState)
        
        # Ajouter les nœuds
        workflow.add_node("retrieve", self._retrieve_documents)
        workflow.add_node("generate", self._generate_response)
        
        # Définir les arêtes
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        
        return workflow.compile()
    
    def _retrieve_documents(self, state: ChatState) -> ChatState:
        """
        Récupère les documents pertinents depuis Elasticsearch
        
        Args:
            state: État actuel du chatbot
            
        Returns:
            État mis à jour avec les documents récupérés
        """
        query = state["query"]
        employee = state["employee"]
        
        # Rechercher les documents pertinents
        documents = self.es_client.search_documents(
            query=query,
            employee=employee,
            top_k=5
        )
        
        state["retrieved_documents"] = documents
        return state
    
    def _generate_response(self, state: ChatState) -> ChatState:
        """
        Génère la réponse du chatbot en utilisant les documents récupérés
        
        Args:
            state: État actuel du chatbot
            
        Returns:
            État mis à jour avec la réponse générée
        """
        query = state["query"]
        employee = state["employee"]
        documents = state["retrieved_documents"]
        messages = state.get("messages", [])
        
        # Construire le contexte à partir des documents
        context = self._build_context(documents)
        
        # Créer le prompt système
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
        
        # Construire les messages
        chat_messages = [SystemMessage(content=system_prompt)]
        chat_messages.extend(messages)
        chat_messages.append(HumanMessage(content=query))
        
        # Générer la réponse
        response = self.llm.invoke(chat_messages)
        
        state["response"] = response.content
        state["messages"] = messages + [
            HumanMessage(content=query),
            AIMessage(content=response.content)
        ]
        
        return state
    
    def _build_context(self, documents: List[CompanyDocument]) -> str:
        """
        Construit le contexte à partir des documents récupérés
        
        Args:
            documents: Liste des documents
            
        Returns:
            Chaîne de caractères contenant le contexte formaté
        """
        if not documents:
            return "Aucun document pertinent trouvé."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(
                f"\n--- Document {i}: {doc.title} ---\n"
                f"Département: {doc.department or 'Tous'}\n"
                f"Type: {doc.document_type or 'Non spécifié'}\n"
                f"Contenu:\n{doc.content[:1000]}..."  # Limiter la longueur
            )
        
        return "\n".join(context_parts)
    
    def chat(self, query: str, employee: Employee, conversation_history: List = None) -> str:
        """
        Effectue une conversation avec le chatbot
        
        Args:
            query: La question de l'employé
            employee: L'employé qui pose la question
            conversation_history: Historique de la conversation (optionnel)
            
        Returns:
            La réponse du chatbot
        """
        initial_state = {
            "query": query,
            "employee": employee,
            "messages": conversation_history or [],
            "retrieved_documents": [],
            "response": ""
        }
        
        # Exécuter le graphe
        final_state = self.graph.invoke(initial_state)
        
        return final_state["response"]
    
    def stream_chat(self, query: str, employee: Employee, conversation_history: List = None):
        """
        Version streaming de la conversation (pour l'interface)
        
        Args:
            query: La question de l'employé
            employee: L'employé qui pose la question
            conversation_history: Historique de la conversation (optionnel)
            
        Yields:
            Tokens de la réponse au fur et à mesure
        """
        initial_state = {
            "query": query,
            "employee": employee,
            "messages": conversation_history or [],
            "retrieved_documents": [],
            "response": ""
        }
        
        # Exécuter le graphe avec streaming
        for chunk in self.graph.stream(initial_state):
            if "generate" in chunk:
                # Ici on pourrait streamer la réponse du LLM
                # Pour simplifier, on retourne la réponse complète
                yield chunk["generate"]["response"]

