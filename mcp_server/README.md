Model Context Protocol (MCP) Server
==================================

This folder provides a minimal Model Context Protocol server for the Enterprise Chatbot project.

What it does
- Exposes MCP actions to retrieve documents, generate a response, and composite chat flow
- Uses the existing `ElasticsearchClient` and `LangGraphChatbot` to carry out actions
- Useful for experimentation and model orchestration

Endpoints
- `GET /mcp/spec` — returns the `mcp.yaml` spec
- `POST /mcp/actions/retrieve_documents` — body: `{query, employee, top_k}`
- `POST /mcp/actions/generate_response` — body: `{query, employee, documents?, conversation_history?}`
- `POST /mcp/actions/chat` — body: `{query, employee, conversation_history?}`

Run locally
-----------
```bash
uvicorn mcp_server.server:app --reload --port 8080
```

Notes
-----
- The server is intentionally minimal and intended as a starting point to evolve a full MCP server
- Authentication and RBAC are not implemented; add them for production use
