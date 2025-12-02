# Enterprise Chatbot with LangGraph and Elasticsearch

An intelligent chatbot for company employees that uses LangGraph for orchestration, Elasticsearch for document search, and a permission management system to control document access.

## Use Case

- User wants to add a document and specifies its access level
- User asks the chatbot for information whose accreditation level is compatible with their rank
- User asks the chatbot for information whose accreditation level is incompatible with their rank
- User with manager level or higher adds a user
- A user modifies a document they have access to
- A user deletes a document they have access to


## 🎯 Features

- **RAG (Retrieval-Augmented Generation) Search**: Semantic search in company documents
- **Permission Management**: Access control based on hierarchical level, department, and users
- **LangGraph**: Conversation flow orchestration with search and generation
- **Elasticsearch**: Document storage and vector search

## 📋 Prerequisites

- Python 3.9+
- Docker and Docker Compose
- OpenAI API Key (for embeddings and LLM)

## 🚀 Installation

1. **Clone the project** (if applicable)

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

4. **Start Elasticsearch**:
```bash
docker-compose up -d
```

5. **Index sample documents**:
```bash
python scripts/index_documents.py
```

## 💻 Usage

### Basic usage

```bash
python src/main.py
```

### Programmatic usage

```python
from src.elasticsearch_client import ElasticsearchClient
from src.langgraph_chatbot import LangGraphChatbot
from src.models.permissions import Employee, PermissionLevel

# Create an employee
employee = Employee(
    user_id="emp_001",
    name="John Doe",
    email="john.doe@company.com",
    department="HR",
    permission_level=PermissionLevel.MANAGER
)

# Initialize the chatbot
es_client = ElasticsearchClient()
chatbot = LangGraphChatbot(es_client=es_client)

# Ask a question
response = chatbot.chat(
    query="What is the paid leave policy?",
    employee=employee
)
print(response)
```

## 🏗️ Architecture

### Project structure

```
.
├── src/
│   ├── models/
│   │   ├── permissions.py      # Permission models
│   │   └── document.py         # Document models
│   ├── elasticsearch_client.py # Elasticsearch client
│   ├── langgraph_chatbot.py    # Chatbot with LangGraph
│   └── main.py                 # Main entry point
├── scripts/
│   └── index_documents.py      # Indexing script
├── docker-compose.yml          # Elasticsearch configuration
├── requirements.txt            # Python dependencies
└── README.md                   # Documentation
```

### Processing flow

1. **Employee question** → The chatbot receives a question
2. **Document search** → Elasticsearch searches for relevant documents
3. **Permission filtering** → Only accessible documents are returned
4. **Response generation** → The LLM generates a response based on found documents

### Permission levels

- `EMPLOYEE`: Base level (all employees)
- `MANAGER`: Intermediate level
- `DIRECTOR`: High level
- `EXECUTIVE`: Very high level

## 🔐 Permission Management

Documents can have restrictions based on:
- **Minimum permission level**: Required hierarchical level
- **Allowed departments**: List of departments with access
- **Allowed users**: Specific list of users

## 📝 Adding Documents

To add your own documents:

```python
from src.elasticsearch_client import ElasticsearchClient
from src.models.document import CompanyDocument
from src.models.permissions import DocumentPermission, PermissionLevel

es_client = ElasticsearchClient()

document = CompanyDocument(
    doc_id="doc_006",
    title="My Document",
    content="Document content...",
    department="IT",
    document_type="manual",
    permission=DocumentPermission(
        min_level=PermissionLevel.MANAGER
    )
)

es_client.index_document(document)
```

## 🧪 Testing

To test the system with different permission levels:

```python
# Base employee
employee = Employee(
    user_id="emp_001",
    name="Test Employee",
    email="test@company.com",
    department="IT",
    permission_level=PermissionLevel.EMPLOYEE
)

# Manager
manager = Employee(
    user_id="emp_002",
    name="Test Manager",
    email="manager@company.com",
    department="HR",
    permission_level=PermissionLevel.MANAGER
)
```

## 🔧 Configuration

Environment variables available in `.env`:

- `OPENAI_API_KEY`: OpenAI API key (required)
- `ELASTICSEARCH_URL`: Elasticsearch URL (default: http://localhost:9200)
- `ELASTICSEARCH_INDEX`: Index name (default: company_documents)
- `EMBEDDING_MODEL`: Embedding model (default: text-embedding-3-small)
- `LLM_MODEL`: LLM model (default: gpt-4o-mini)

## 📚 Documentation

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [LangChain Documentation](https://python.langchain.com/)

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or a pull request.

## 📄 License

This project is licensed under the MIT License.

