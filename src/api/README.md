# Enterprise Chatbot API

REST API implementation matching the Swagger/OpenAPI specification.

## Running the API Server

```bash
python run_api.py
```

Or using uvicorn directly:

```bash
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Authentication

The API uses Bearer token authentication. For now, the token format is simplified:
- Use a user_id or email as the token
- Format: `Bearer emp_001` or `Bearer user@company.com`

Example:
```bash
curl -H "Authorization: Bearer emp_001" http://localhost:8000/documents
```

## Endpoints

### Documents
- `POST /documents` - Create a new document
- `GET /documents` - List documents (with filters)
- `GET /documents/{doc_id}` - Get a specific document
- `PUT /documents/{doc_id}` - Update a document
- `DELETE /documents/{doc_id}` - Delete a document

### Chatbot
- `POST /chatbot/query` - Query the chatbot

### Users
- `POST /users` - Create a new user (requires manager+)
- `GET /users` - List users (requires manager+)

## Example Usage

### Create a document
```bash
curl -X POST http://localhost:8000/documents \
  -H "Authorization: Bearer emp_001" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Company Policy",
    "content": "Policy content...",
    "department": "HR",
    "document_type": "policy",
    "permission": {
      "min_level": "manager",
      "allowed_departments": ["HR"],
      "allowed_users": null
    }
  }'
```

### Query the chatbot
```bash
curl -X POST http://localhost:8000/chatbot/query \
  -H "Authorization: Bearer emp_001" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the paid leave policy?",
    "conversation_history": []
  }'
```

### Create a user (manager+ only)
```bash
curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer emp_001" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane@company.com",
    "department": "IT",
    "permission_level": "employee"
  }'
```

