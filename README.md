# Chatbot Entreprise avec LangGraph et Elasticsearch

Un chatbot intelligent pour les employés d'une entreprise qui utilise LangGraph pour l'orchestration, Elasticsearch pour la recherche de documents, et un système de gestion des permissions pour contrôler l'accès aux documents.

## Use Case

- L'utilisateur souhaite ajouter un document, il en spécifie le niveau d'accès
- L'utilisateur demande une information dont le niveau d'accréditation est compatible avec son grade au chatbot 
- L'utilisateur demande une information dont le niveau d'accréditation est incompatible avec son grade au chatbot 
- L'utilisateur de niveau manager ou plus ajoute un utilisateur
- Un utilisateur modifie un document dont-il à l'accès
- Un utilisateur supprime un document dont-il à l'accès


## 🎯 Fonctionnalités

- **Recherche RAG (Retrieval-Augmented Generation)**: Recherche sémantique dans les documents de l'entreprise
- **Gestion des permissions**: Contrôle d'accès basé sur le niveau hiérarchique, le département et les utilisateurs
- **LangGraph**: Orchestration du flux de conversation avec recherche et génération
- **Elasticsearch**: Stockage et recherche vectorielle des documents

## 📋 Prérequis

- Python 3.9+
- Docker et Docker Compose
- Clé API OpenAI (pour les embeddings et le LLM)

## 🚀 Installation

1. **Cloner le projet** (si applicable)

2. **Installer les dépendances**:
```bash
pip install -r requirements.txt
```

3. **Configurer les variables d'environnement**:

## 🧭 Model Context Protocol (MCP) Server

This project exposes a minimal MCP server that provides context and actions for models to use. It is located in `mcp_server/` and offers endpoints that match the MCP spec `mcp_server/mcp.yaml`.

Run it locally with `uvicorn`:

```bash
uvicorn mcp_server.server:app --reload --port 8080
```

Useful endpoints:
- `GET /mcp/spec` — returns the MCP spec
- `POST /mcp/actions/retrieve_documents` — retrieve docs for a query and employee
- `POST /mcp/actions/generate_response` — generate a response given documents and history
- `POST /mcp/actions/chat` — composite action running retrieval and generation

```bash
cp .env.example .env
# Éditer .env et ajouter votre clé API OpenAI
```

4. **Démarrer Elasticsearch**:
```bash
docker-compose up -d
```

5. **Indexer des documents d'exemple**:
```bash
python scripts/index_documents.py
```

## 💻 Utilisation

### Utilisation basique

```bash
python src/main.py
```

### Utilisation programmatique

```python
from src.elasticsearch_client import ElasticsearchClient
from src.langgraph_chatbot import LangGraphChatbot
from src.models.permissions import Employee, PermissionLevel

# Créer un employé
employee = Employee(
    user_id="emp_001",
    name="Jean Dupont",
    email="jean.dupont@entreprise.com",
    department="RH",
    permission_level=PermissionLevel.MANAGER
)

# Initialiser le chatbot
es_client = ElasticsearchClient()
chatbot = LangGraphChatbot(es_client=es_client)

# Poser une question
response = chatbot.chat(
    query="Quelle est la politique de congés payés?",
    employee=employee
)
print(response)
```

## 🏗️ Architecture

### Structure du projet

```
.
├── src/
│   ├── models/
│   │   ├── permissions.py      # Modèles de permissions
│   │   └── document.py         # Modèles de documents
│   ├── elasticsearch_client.py # Client Elasticsearch
│   ├── langgraph_chatbot.py    # Chatbot avec LangGraph
│   └── main.py                 # Point d'entrée principal
├── scripts/
│   └── index_documents.py      # Script d'indexation
├── docker-compose.yml          # Configuration Elasticsearch
├── requirements.txt            # Dépendances Python
└── README.md                   # Documentation
```

### Flux de traitement

1. **Question de l'employé** → Le chatbot reçoit une question
2. **Recherche de documents** → Elasticsearch recherche les documents pertinents
3. **Filtrage par permissions** → Seuls les documents accessibles sont retournés
4. **Génération de réponse** → Le LLM génère une réponse basée sur les documents trouvés

### Niveaux de permission

- `EMPLOYEE`: Niveau de base (tous les employés)
- `MANAGER`: Niveau intermédiaire
- `DIRECTOR`: Niveau élevé
- `EXECUTIVE`: Niveau très élevé

## 🔐 Gestion des permissions

Les documents peuvent avoir des restrictions basées sur:
- **Niveau de permission minimum**: Niveau hiérarchique requis
- **Départements autorisés**: Liste des départements ayant accès
- **Utilisateurs autorisés**: Liste spécifique d'utilisateurs

## 📝 Ajouter des documents

Pour ajouter vos propres documents:

```python
from src.elasticsearch_client import ElasticsearchClient
from src.models.document import CompanyDocument
from src.models.permissions import DocumentPermission, PermissionLevel

es_client = ElasticsearchClient()

document = CompanyDocument(
    doc_id="doc_006",
    title="Mon document",
    content="Contenu du document...",
    department="IT",
    document_type="manual",
    permission=DocumentPermission(
        min_level=PermissionLevel.MANAGER
    )
)

es_client.index_document(document)
```

## 🧪 Tests

Pour tester le système avec différents niveaux de permission:

```python
# Employé de base
employee = Employee(
    user_id="emp_001",
    name="Employé Test",
    email="test@entreprise.com",
    department="IT",
    permission_level=PermissionLevel.EMPLOYEE
)

# Manager
manager = Employee(
    user_id="emp_002",
    name="Manager Test",
    email="manager@entreprise.com",
    department="RH",
    permission_level=PermissionLevel.MANAGER
)
```

## 🔧 Configuration

Variables d'environnement disponibles dans `.env`:

- `OPENAI_API_KEY`: Clé API OpenAI (requis)
- `ELASTICSEARCH_URL`: URL d'Elasticsearch (défaut: http://localhost:9200)
- `ELASTICSEARCH_INDEX`: Nom de l'index (défaut: company_documents)
- `EMBEDDING_MODEL`: Modèle d'embedding (défaut: text-embedding-3-small)
- `LLM_MODEL`: Modèle LLM (défaut: gpt-4o-mini)

## 📚 Documentation

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [LangChain Documentation](https://python.langchain.com/)

## 🤝 Contribution

Les contributions sont les bienvenues! N'hésitez pas à ouvrir une issue ou une pull request.

## 📄 Licence

Ce projet est sous licence MIT.

