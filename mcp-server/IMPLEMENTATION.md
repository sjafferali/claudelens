# ClaudeLens MCP Server Implementation

## Overview

The ClaudeLens MCP Server is a Model Context Protocol server that exposes Claude conversation history from the ClaudeLens application as resources and provides tools for searching and analyzing conversations. This allows AI assistants to access and work with historical Claude conversations stored in ClaudeLens.

## Architecture

### Components

1. **MCP Server** (`claudelens_mcp/server.py`)
   - Built using FastMCP for simplified implementation
   - Implements resources, tools, and prompts
   - Manages lifecycle with async context manager for API client

2. **API Client** (`claudelens_mcp/api_client.py`)
   - HTTP client for communicating with ClaudeLens backend
   - Implements all necessary API endpoints
   - Handles authentication if required

3. **Backend Enhancement** (`backend/app/api/api_v1/endpoints/export.py`)
   - New export endpoints added to backend for optimized MCP consumption
   - Structured conversation export
   - Session export with thread navigation

## Features

### Resources (Data Access)

Resources provide read-only access to conversation data:

1. **Session List** (`claudelens://sessions`)
   - Lists all available Claude sessions
   - Shows metadata: timestamps, message count, costs, summaries

2. **Session Details** (`claudelens://sessions/{session_id}`)
   - Detailed information about a specific session
   - Includes initial messages preview

3. **Session Messages** (`claudelens://sessions/{session_id}/messages`)
   - Complete conversation history for a session
   - All messages with content, timestamps, and metadata

4. **Structured Conversations** (`claudelens://conversations/structured`)
   - Hierarchical view organized by projects
   - Comprehensive overview of all conversations

5. **Message Details** (`claudelens://messages/{message_id}`)
   - Individual message information
   - Supports lookup by ID or UUID

### Tools (Actions)

Tools allow AI assistants to perform searches and analysis:

1. **search_messages** - Full-text search with filters
   - Query across all conversations
   - Filter by session, type, model
   - Regex support
   - Highlighting

2. **search_code** - Code-specific search
   - Find code snippets
   - Language filtering
   - Optimized for technical content

3. **get_conversation_thread** - Navigate conversation branches
   - Follow parent-child relationships
   - Handle branching conversations
   - Configurable depth

4. **generate_summary** - AI-powered summaries
   - Create or regenerate session summaries
   - Based on key messages

5. **get_message_context** - Contextual message view
   - Messages before and after
   - Understand conversation flow

6. **list_projects** - Project overview
   - All ClaudeLens projects
   - Session counts and costs

7. **get_session_analytics** - Detailed analytics
   - Token usage
   - Cost analysis
   - Conversation patterns

8. **export_session** - Comprehensive export
   - Full session data
   - Multiple formats (JSON, Markdown)
   - Thread structure preservation

9. **get_recent_searches** - Search history
   - Recent queries for quick access

### Prompts (Templates)

Pre-configured prompts for common tasks:

1. **Session Analysis** - Analyze entire sessions
2. **Search and Summarize** - Search and synthesize findings
3. **Code Search Analysis** - Analyze code patterns

## Data Flow

```
Claude Desktop/MCP Client
        ↓
    MCP Server
        ↓
    API Client
        ↓
ClaudeLens Backend API
        ↓
    MongoDB Database
```

## Configuration

### Environment Variables

- `CLAUDELENS_API_URL` - Backend API URL (default: http://localhost:8080)
- `CLAUDELENS_API_KEY` - Optional API key for authentication

### Installation in Claude Desktop

The server can be installed using the MCP CLI:

```bash
uv run mcp install claudelens_mcp/server.py --name "ClaudeLens"
```

Or manually configured in Claude Desktop settings.

## Backend Enhancements

### New Export Endpoints

1. **`/api/v1/export/sessions/{session_id}/export`**
   - Optimized session export for MCP
   - Structured message format
   - Thread navigation support
   - Multiple export formats

2. **`/api/v1/export/conversations/structured`**
   - Hierarchical conversation organization
   - Project-based grouping
   - Batch retrieval optimization

## Testing

The implementation includes a comprehensive test script (`test_mcp_server.py`) that:

1. Verifies backend connectivity
2. Tests all API client methods
3. Validates MCP server setup
4. Checks resource and tool definitions

Run tests with:
```bash
python test_mcp_server.py
```

## Usage Examples

### Accessing Resources in Claude

```
Use resource: claudelens://sessions
Use resource: claudelens://sessions/abc123/messages
```

### Using Tools

```
Use tool: search_messages with query "error handling"
Use tool: get_conversation_thread for session abc123 message xyz789
```

### Using Prompts

```
Use prompt: Session Analysis for session abc123
```

## Benefits

1. **Historical Context** - Access to all past Claude conversations
2. **Search Capabilities** - Find specific discussions or code
3. **Analytics** - Understand usage patterns and costs
4. **Thread Navigation** - Follow complex branching conversations
5. **Export Options** - Archive or analyze conversations externally

## Future Enhancements

Potential improvements for future versions:

1. **Real-time Updates** - WebSocket integration for live session monitoring
2. **Advanced Analytics** - More sophisticated analysis tools
3. **Caching** - Local caching for frequently accessed data
4. **Filtering** - More granular resource filtering options
5. **Batch Operations** - Bulk export and analysis tools

## Security Considerations

1. **Authentication** - Optional API key support
2. **Data Privacy** - All data stays within user's infrastructure
3. **Access Control** - Can be configured with backend permissions
4. **Audit Logging** - All access can be logged at backend level

## Troubleshooting

Common issues and solutions:

1. **Connection Failed** - Ensure backend is running
2. **Authentication Error** - Check API key configuration
3. **No Data** - Verify database has session data
4. **Search Not Working** - Check MongoDB text indexes

## Summary

The ClaudeLens MCP Server successfully bridges Claude Desktop with the ClaudeLens analytics platform, providing comprehensive access to conversation history through the Model Context Protocol. The implementation is modular, extensible, and ready for production use.
