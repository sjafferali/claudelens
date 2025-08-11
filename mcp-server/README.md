# ClaudeLens MCP Server

An MCP (Model Context Protocol) server that exposes Claude conversation history from ClaudeLens as resources and provides tools for searching and analyzing conversations.

## Features

### Resources
- **Sessions List** (`claudelens://sessions`) - Browse all Claude sessions
- **Session Details** (`claudelens://sessions/{session_id}`) - View specific session information
- **Session Messages** (`claudelens://sessions/{session_id}/messages`) - Access complete conversation history
- **Message Details** (`claudelens://messages/{message_id}`) - View individual message details

### Tools
- **search_messages** - Full-text search across all conversations with filtering
- **search_code** - Search specifically for code snippets with language filtering
- **get_conversation_thread** - Navigate through branching conversation threads
- **generate_summary** - Generate AI summaries for sessions
- **get_message_context** - View messages with surrounding context
- **list_projects** - List all ClaudeLens projects
- **get_session_analytics** - Get detailed analytics for sessions
- **get_recent_searches** - View recent search queries

### Prompts
- **Session Analysis** - Analyze a complete session for insights
- **Search and Summarize** - Search and summarize findings across conversations
- **Code Search Analysis** - Search and analyze code patterns

## Installation

### Prerequisites
- Python 3.11 or higher
- ClaudeLens backend running (default: http://localhost:8080)
- uv package manager (recommended) or pip

### Install with uv (recommended)

```bash
cd mcp-server
uv add .
```

### Install with pip

```bash
cd mcp-server
pip install -e .
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` to configure:
   - `CLAUDELENS_API_URL` - URL of your ClaudeLens backend (default: http://localhost:8080)
   - `CLAUDELENS_API_KEY` - Optional API key if your backend requires authentication

## Usage

### Running the Server

#### As a standalone server (stdio transport):
```bash
uv run claudelens-mcp
```

Or with the MCP CLI:
```bash
uv run mcp run claudelens_mcp/server.py
```

#### For development and testing:
```bash
uv run mcp dev claudelens_mcp/server.py
```

### Installing in Claude Desktop

To use this MCP server with Claude Desktop:

```bash
uv run mcp install claudelens_mcp/server.py --name "ClaudeLens"
```

Or manually add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "claudelens": {
      "command": "uv",
      "args": ["run", "claudelens-mcp"],
      "env": {
        "CLAUDELENS_API_URL": "http://localhost:8080"
      }
    }
  }
}
```

## Example Usage

Once connected to Claude Desktop or another MCP client:

### Browse Sessions
```
Use the resource: claudelens://sessions
```

### Search for Specific Topics
```
Use the tool: search_messages with query "error handling in Python"
```

### Analyze a Session
```
Use the prompt: Session Analysis with session_id "your-session-id"
```

### Navigate Conversation Threads
```
Use the tool: get_conversation_thread with session_id and message_uuid
```

## Development

### Project Structure
```
mcp-server/
├── claudelens_mcp/
│   ├── __init__.py
│   ├── api_client.py    # ClaudeLens API client
│   └── server.py         # Main MCP server implementation
├── .env.example          # Example configuration
├── pyproject.toml        # Package configuration
└── README.md            # This file
```

### Running Tests
```bash
uv run pytest
```

### Adding New Features

1. **New Resources**: Add resource handlers in `server.py` using the `@mcp.resource()` decorator
2. **New Tools**: Add tool functions with `@mcp.tool()` decorator
3. **New Prompts**: Add prompt templates with `@mcp.prompt()` decorator
4. **API Extensions**: Extend `api_client.py` for new backend endpoints

## Backend API Requirements

This MCP server requires a ClaudeLens backend with the following endpoints:

### Required Endpoints
- `GET /api/v1/sessions` - List sessions
- `GET /api/v1/sessions/{id}` - Get session details
- `GET /api/v1/sessions/{id}/messages` - Get session messages
- `GET /api/v1/messages/{id}` - Get message details
- `POST /api/v1/search` - Search messages

### Optional Endpoints (for full functionality)
- `GET /api/v1/sessions/{id}/thread/{uuid}` - Get conversation threads
- `POST /api/v1/sessions/{id}/generate-summary` - Generate summaries
- `GET /api/v1/messages/{id}/context` - Get message context
- `GET /api/v1/projects` - List projects
- `GET /api/v1/analytics/sessions/{id}` - Session analytics

## Troubleshooting

### Connection Issues
- Ensure ClaudeLens backend is running and accessible
- Check the `CLAUDELENS_API_URL` in your `.env` file
- Verify network connectivity: `curl http://localhost:8080/health`

### Authentication Errors
- If your backend requires authentication, set `CLAUDELENS_API_KEY` in `.env`
- Ensure the API key has proper permissions

### Search Not Working
- Check if text indexes are created in MongoDB
- Verify search endpoint is available in backend

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - See LICENSE file for details
