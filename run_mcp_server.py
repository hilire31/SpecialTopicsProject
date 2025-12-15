"""
Run the MCP (Model Context Protocol) server
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "mcp_server.server:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )

