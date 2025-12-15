"""
Chatbot using LangGraph with RAG search and permission management
"""
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from src.elasticsearch_client import ElasticsearchClient
from src.models.permissions import Employee
from src.models.document import CompanyDocument


class ChatState(TypedDict):
    """Chatbot state"""
    messages: Annotated[List, "messages"]
    employee: Employee
    query: str
    retrieved_documents: List[CompanyDocument]
    response: str


class LangGraphChatbot:
    """Chatbot with LangGraph integrating RAG and permission management"""
    
    def __init__(
        self,
        es_client: ElasticsearchClient,
        llm_model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        enable_mcp_tools: bool = True
    ):
        """
        Initialize the chatbot
        
        Args:
            es_client: Elasticsearch client
            llm_model: LLM model to use
            temperature: Temperature for the LLM
            enable_mcp_tools: Enable MCP tools for actions (create_user, create_document)
        """
        self.es_client = es_client
        self.enable_mcp_tools = enable_mcp_tools
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph graph"""
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("retrieve", self._retrieve_documents)
        workflow.add_node("generate", self._generate_response)
        
        # Define edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        
        return workflow.compile()
    
    def _retrieve_documents(self, state: ChatState) -> ChatState:
        """
        Retrieve relevant documents from Elasticsearch
        
        Args:
            state: Current chatbot state
            
        Returns:
            Updated state with retrieved documents
        """
        query = state["query"]
        employee = state["employee"]
        
        # Search for relevant documents
        documents = self.es_client.search_documents(
            query=query,
            employee=employee,
            top_k=5
        )
        
        state["retrieved_documents"] = documents
        return state
    
    def _generate_response(self, state: ChatState) -> ChatState:
        """
        Generate chatbot response using retrieved documents and MCP tools
        
        Args:
            state: Current chatbot state
            
        Returns:
            Updated state with generated response
        """
        query = state["query"]
        employee = state["employee"]
        documents = state["retrieved_documents"]
        messages = state.get("messages", [])
        
        # Build context from documents
        context = self._build_context(documents)
        
        # Get MCP tools for this employee if enabled
        tools = []
        available_actions_text = ""
        if self.enable_mcp_tools:
            try:
                from src.tools.mcp_tools import get_mcp_tools
                tools = get_mcp_tools(employee)
                
                # Build available actions text for the prompt
                available_actions = []
                for tool in tools:
                    if tool.name == "create_user":
                        available_actions.append("- create_user: Créer un nouvel utilisateur (niveau manager+ requis)")
                    elif tool.name == "create_document":
                        available_actions.append("- create_document: Créer un nouveau document")
                
                if available_actions:
                    available_actions_text = f"""

Actions disponibles que tu peux effectuer:
{chr(10).join(available_actions)}

Si l'utilisateur demande de créer un utilisateur ou un document, utilise l'outil approprié.
"""
            except Exception as e:
                # If tools can't be loaded, continue without them
                import warnings
                warnings.warn(f"Could not load MCP tools: {e}. Continuing without MCP tools.")
                tools = []
        
        # Create system prompt
        system_prompt = f"""Tu es un assistant IA pour l'entreprise. Tu réponds aux questions des employés en utilisant les documents de l'entreprise.

Informations sur l'employé:
- Nom: {employee.name}
- Département: {employee.department}
- Niveau de permission: {employee.permission_level.value}

Documents disponibles:
{context}{available_actions_text}

Instructions:
- Réponds uniquement en français
- Utilise uniquement les informations des documents fournis pour répondre aux questions
- Si tu n'as pas d'information dans les documents, dis-le clairement
- Si l'utilisateur veut effectuer une action (créer un utilisateur, créer un document), utilise l'outil approprié
- Sois précis et concis
- Cite les documents sources quand c'est pertinent
"""
        
        # Build messages
        chat_messages = [SystemMessage(content=system_prompt)]
        chat_messages.extend(messages)
        chat_messages.append(HumanMessage(content=query))
        
        # Bind tools to LLM if available
        if tools:
            llm_with_tools = self.llm.bind_tools(tools)
        else:
            llm_with_tools = self.llm
        
        # Generate response (may include tool calls)
        response = llm_with_tools.invoke(chat_messages)
        
        # Handle tool calls if any
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Add the AI message with tool calls to the conversation
            chat_messages.append(response)
            
            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                
                # Find and execute the tool
                tool_result = None
                for tool in tools:
                    if tool.name == tool_name:
                        try:
                            tool_result = tool.invoke(tool_args)
                        except Exception as e:
                            tool_result = f"Erreur lors de l'exécution de l'outil {tool_name}: {str(e)}"
                        break
                
                if tool_result:
                    # Add tool message to conversation
                    chat_messages.append(
                        ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_call.get("id")
                        )
                    )
            
            # Get final response from LLM after tool execution
            final_response = llm_with_tools.invoke(chat_messages)
            state["response"] = final_response.content
            chat_messages.append(final_response)
        else:
            state["response"] = response.content
            chat_messages.append(response)
        
        # Update conversation history (only user and assistant messages)
        updated_messages = []
        for msg in chat_messages:
            if isinstance(msg, (HumanMessage, AIMessage)):
                updated_messages.append(msg)
        
        state["messages"] = updated_messages
        
        return state
    
    def _build_context(self, documents: List[CompanyDocument]) -> str:
        """
        Build context from retrieved documents
        
        Args:
            documents: List of documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(
                f"\n--- Document {i}: {doc.title} ---\n"
                f"Department: {doc.department or 'All'}\n"
                f"Type: {doc.document_type or 'Not specified'}\n"
                f"Content:\n{doc.content[:1000]}..."  # Limit length
            )
        
        return "\n".join(context_parts)
    
    def chat(self, query: str, employee: Employee, conversation_history: List = None) -> str:
        """
        Perform a conversation with the chatbot
        
        Args:
            query: Employee's question
            employee: Employee asking the question
            conversation_history: Conversation history (optional)
            
        Returns:
            Chatbot response
        """
        initial_state = {
            "query": query,
            "employee": employee,
            "messages": conversation_history or [],
            "retrieved_documents": [],
            "response": ""
        }
        
        # Execute the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state["response"]
    
    def chat_with_documents(
        self,
        query: str,
        employee: Employee,
        conversation_history: List = None
    ) -> tuple[str, List[CompanyDocument]]:
        """
        Perform a conversation and return both response and retrieved documents
        
        Args:
            query: Employee's question
            employee: Employee asking the question
            conversation_history: Conversation history (optional)
            
        Returns:
            Tuple of (response, list of retrieved documents)
        """
        initial_state = {
            "query": query,
            "employee": employee,
            "messages": conversation_history or [],
            "retrieved_documents": [],
            "response": ""
        }
        
        # Execute the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state["response"], final_state["retrieved_documents"]
    
    def stream_chat(self, query: str, employee: Employee, conversation_history: List = None):
        """
        Streaming version of the conversation (for interface)
        
        Args:
            query: Employee's question
            employee: Employee asking the question
            conversation_history: Conversation history (optional)
            
        Yields:
            Response tokens as they are generated
        """
        initial_state = {
            "query": query,
            "employee": employee,
            "messages": conversation_history or [],
            "retrieved_documents": [],
            "response": ""
        }
        
        # Execute graph with streaming
        for chunk in self.graph.stream(initial_state):
            if "generate" in chunk:
                # Here we could stream the LLM response
                # For simplicity, return the complete response
                yield chunk["generate"]["response"]

