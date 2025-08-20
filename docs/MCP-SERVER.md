# ClaudeLens MCP Server Documentation

## Overview

The ClaudeLens MCP (Model Context Protocol) Server provides a bridge between Claude Desktop and your ClaudeLens conversation history database. It exposes your Claude conversation history as searchable resources and provides powerful tools for analysis and navigation.

## What is MCP?

The Model Context Protocol is a standardized way for AI assistants like Claude to interact with external data sources and tools. Think of it as an API specifically designed for AI interactions, allowing Claude to:
- Access historical conversation data
- Search through past discussions
- Navigate conversation threads
- Analyze patterns and generate insights

## Installation

### Prerequisites
- Python 3.11+
- ClaudeLens backend running (typically on `http://localhost:8080`)
- uv package manager (recommended) or pip
- Claude Desktop application

### Quick Setup

1. **Navigate to the MCP server directory:**
```bash
cd mcp-server
```

2. **Install dependencies:**
```bash
uv add .
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env to set your backend URL if not using default
```

4. **Test the installation:**
```bash
python test_mcp_server.py
```

5. **Install in Claude Desktop:**
```bash
uv run mcp install claudelens_mcp/server.py --name "ClaudeLens"
```

## Features

### Resources (Data Access Points)

Resources provide read-only access to your conversation data:

| Resource URI | Description |
|-------------|-------------|
| `claudelens://sessions` | List all Claude sessions with metadata |
| `claudelens://sessions/{id}` | Get detailed information about a specific session |
| `claudelens://sessions/{id}/messages` | Access complete conversation history |
| `claudelens://conversations/structured` | View sessions organized by project |
| `claudelens://messages/{id}` | Get individual message details |

### Tools (Actions)

Tools allow Claude to perform searches and analysis:

| Tool | Purpose | Key Features |
|------|---------|--------------|
| `search_messages` | Full-text search across all conversations | Regex support, filtering, highlighting |
| `search_code` | Find code snippets | Language filtering, optimized for technical content |
| `get_conversation_thread` | Navigate branching conversations | Parent-child relationships, configurable depth |
| `generate_summary` | Create AI summaries | Based on key messages |
| `get_message_context` | View messages with context | Before/after messages for flow understanding |
| `list_projects` | Overview of all projects | Session counts, costs |
| `get_session_analytics` | Detailed session analytics | Token usage, costs, patterns |
| `export_session` | Export complete sessions | JSON/Markdown formats |
| `get_recent_searches` | Access search history | Quick re-run of common searches |

### Prompts (Templates)

Pre-configured prompt templates for common tasks:

- **Session Analysis** - Comprehensive analysis of entire sessions
- **Search and Summarize** - Search and synthesize findings across conversations
- **Code Search Analysis** - Analyze code patterns and solutions

## Configuration

### Environment Variables

Create a `.env` file in the mcp-server directory:

```env
# Backend API URL (required)
CLAUDELENS_API_URL=http://localhost:8080

# API Key (optional, if backend requires authentication)
CLAUDELENS_API_KEY=your-api-key-here
```

### Claude Desktop Configuration

The MCP server can be configured in Claude Desktop in two ways:

#### Automatic Installation (Recommended)
```bash
uv run mcp install claudelens_mcp/server.py --name "ClaudeLens"
```

#### Manual Configuration
Add to your Claude Desktop settings JSON:

```json
{
  "mcpServers": {
    "claudelens": {
      "command": "uv",
      "args": ["run", "claudelens-mcp"],
      "cwd": "/path/to/claudelens/mcp-server",
      "env": {
        "CLAUDELENS_API_URL": "http://localhost:8080"
      }
    }
  }
}
```

## Architecture

```
┌─────────────────┐
│ Claude Desktop  │
└────────┬────────┘
         │ MCP Protocol
         ↓
┌─────────────────┐
│   MCP Server    │
│  (FastMCP/Python)│
└────────┬────────┘
         │ HTTP/REST
         ↓
┌─────────────────┐
│ ClaudeLens API  │
│   (FastAPI)     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│    MongoDB      │
│   Database      │
└─────────────────┘
```

## Testing

Run the comprehensive test suite to verify your installation:

```bash
python test_mcp_server.py
```

This will:
1. Check backend connectivity
2. Test all API endpoints
3. Validate MCP server setup
4. Verify resource and tool definitions

Expected output:
```
✓ Backend is accessible
✓ API Client tests completed successfully
✓ MCP server imported successfully
✅ All tests passed! The MCP server is ready to use.
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Connection Failed | Ensure ClaudeLens backend is running (`docker-compose up`) |
| Authentication Error | Check `CLAUDELENS_API_KEY` in `.env` file |
| No Sessions Found | Verify database has session data |
| Search Not Working | Check MongoDB text indexes are created |
| MCP Not Appearing in Claude | Restart Claude Desktop after installation |

### Debug Commands

Check backend health:
```bash
curl http://localhost:8080/health
```

Test API access:
```bash
curl http://localhost:8080/api/v1/sessions
```

View MCP server logs:
```bash
uv run claudelens-mcp --debug
```

## Backend Requirements

The MCP server requires these ClaudeLens backend endpoints:

### Core Endpoints
- `GET /api/v1/sessions` - List sessions
- `GET /api/v1/sessions/{id}` - Get session details
- `GET /api/v1/sessions/{id}/messages` - Get messages
- `GET /api/v1/messages/{id}` - Get message details
- `POST /api/v1/search` - Search functionality

### Enhanced Endpoints (Added for MCP)
- `GET /api/v1/export/sessions/{id}/export` - Structured session export
- `GET /api/v1/export/conversations/structured` - Hierarchical conversation view

## Security Considerations

1. **Data Privacy** - All data remains within your local infrastructure
2. **Authentication** - Optional API key support for secured backends
3. **Access Control** - Can be configured with backend-level permissions
4. **Audit Logging** - All access can be logged at the backend level

## Performance Tips

1. **Caching** - The MCP server doesn't cache by default; consider backend caching for frequently accessed data
2. **Pagination** - Use limits when retrieving large datasets
3. **Indexing** - Ensure MongoDB indexes are properly configured for search performance
4. **Connection Pooling** - The API client maintains a connection pool for efficiency

## Next Steps

- Review [MCP Workflows](./MCP-WORKFLOWS.md) for practical usage examples
- Check [MCP Usage Guide](./MCP-USAGE-GUIDE.md) for Claude Desktop integration tips
- See [MCP Implementation Details](./MCP-IMPLEMENTATION.md) for technical details
