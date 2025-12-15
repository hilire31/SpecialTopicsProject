# MCP Server

Model Context Protocol (MCP) server for the Enterprise Chatbot.

## Overview

The MCP server provides a simplified interface for model context operations, exposing actions that can be used by AI models to interact with the chatbot system.

## Running the MCP Server

```bash
python run_mcp_server.py
```

Or using uvicorn directly:

```bash
uvicorn mcp_server.server:app --host 0.0.0.0 --port 8080 --reload
```

The server will be available at `http://localhost:8080`

## Endpoints

### MCP Specification
- `GET /mcp/spec` - Returns the MCP specification file (mcp.yaml)

### Actions
- `POST /mcp/actions/retrieve_documents` - Retrieve documents based on a query and employee context
- `POST /mcp/actions/generate_response` - Generate a response from the LLM given documents and conversation history
- `POST /mcp/actions/chat` - Composite action: retrieve_documents then generate_response

### Health Check
- `GET /mcp/health` - Health check endpoint

## Example Usage

### Retrieve Documents

```bash
curl -X POST http://localhost:8080/mcp/actions/retrieve_documents \
  -H "Content-Type: application/json" \
  -d '{
    "query": "paid leave policy",
    "employee": {
      "user_id": "emp_001",
      "name": "Jean Dupont",
      "email": "jean@company.com",
      "department": "HR",
      "permission_level": "manager"
    },
    "top_k": 5
  }'
```

### Generate Response

```bash
curl -X POST http://localhost:8080/mcp/actions/generate_response \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the paid leave policy?",
    "employee": {
      "user_id": "emp_001",
      "name": "Jean Dupont",
      "email": "jean@company.com",
      "department": "HR",
      "permission_level": "manager"
    },
    "conversation_history": []
  }'
```

### Chat Action

```bash
curl -X POST http://localhost:8080/mcp/actions/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the paid leave policy?",
    "employee": {
      "user_id": "emp_001",
      "name": "Jean Dupont",
      "email": "jean@company.com",
      "department": "HR",
      "permission_level": "manager"
    },
    "conversation_history": []
  }'
```

## Differences from Main API

The MCP server provides:
- Simplified interface focused on model context operations
- No authentication required (employee is passed in request body)
- Actions-oriented endpoints rather than REST resources
- Designed for integration with AI models and agents

The main API server (`src/api/server.py`) provides:
- Full REST API matching Swagger specification
- JWT authentication
- Complete CRUD operations for documents and users
- Production-ready error handling

## Integration

The MCP server uses the same underlying services as the main API:
- `ElasticsearchClient` for document search
- `LangGraphChatbot` for response generation
- Same permission system and document models
