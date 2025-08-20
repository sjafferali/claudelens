# ClaudeLens MCP Quick Reference

## Installation Quick Start

```bash
# 1. Start backend
cd /path/to/claudelens
docker-compose up -d

# 2. Install MCP server
cd mcp-server
uv add .
uv run mcp install claudelens_mcp/server.py --name "ClaudeLens"

# 3. Restart Claude Desktop
```

## Resource URIs

| Resource | Description |
|----------|-------------|
| `claudelens://sessions` | List all sessions |
| `claudelens://sessions/{id}` | Get session details |
| `claudelens://sessions/{id}/messages` | Get session messages |
| `claudelens://conversations/structured` | Hierarchical view |
| `claudelens://messages/{id}` | Get specific message |

## Tools Quick Reference

### Search Messages
```yaml
tool: search_messages
params:
  query: "search text"
  session_ids: ["id1", "id2"]  # optional
  message_types: ["user", "assistant"]  # optional
  models: ["claude-3-opus"]  # optional
  limit: 20
  highlight: true
  is_regex: false
```

### Search Code
```yaml
tool: search_code
params:
  query: "function name"
  language: "python"  # optional
```

### Get Conversation Thread
```yaml
tool: get_conversation_thread
params:
  session_id: "abc123"
  message_uuid: "xyz789"
  depth: 10
```

### Generate Summary
```yaml
tool: generate_summary
params:
  session_id: "abc123"
```

### Get Message Context
```yaml
tool: get_message_context
params:
  message_id: "msg123"
  before: 5
  after: 5
```

### Export Session
```yaml
tool: export_session
params:
  session_id: "abc123"
  format: "json"  # or "markdown"
  include_metadata: true
  include_costs: true
  flatten_threads: false
```

### List Projects
```yaml
tool: list_projects
# No parameters required
```

### Get Session Analytics
```yaml
tool: get_session_analytics
params:
  session_id: "abc123"
```

### Get Recent Searches
```yaml
tool: get_recent_searches
params:
  limit: 10
```

## Prompts

### Session Analysis
```yaml
prompt: Session Analysis
params:
  session_id: "abc123"
```

### Search and Summarize
```yaml
prompt: Search and Summarize
params:
  query: "error handling"
  limit: 20
```

### Code Search Analysis
```yaml
prompt: Code Search Analysis
params:
  query: "async await"
  language: "javascript"  # optional
```

## Common Commands

### Continue Previous Work
```
"Show me our last conversation about [topic]"
"Continue the [feature] we were working on"
"What's left to do on [project]?"
```

### Search and Debug
```
"Find all times we encountered [error]"
"Search for [function] implementations"
"Show me all [pattern] usage"
```

### Analysis and Review
```
"Analyze session [id] for insights"
"Summarize our work on [feature]"
"Generate documentation for [project]"
```

### Navigation
```
"Show me the evolution of [code]"
"Navigate to parent message of [uuid]"
"Get context around message [id]"
```

## Workflow Shortcuts

### Find Recent Work
```
Use: claudelens://sessions
Then: Look for recent timestamps
```

### Debug Pattern
```
1. search_messages for error text
2. get_message_context for full picture
3. Apply previous solution
```

### Code Evolution
```
1. search_code for function name
2. get_conversation_thread for each result
3. Track changes across sessions
```

### Project Overview
```
1. list_projects
2. claudelens://conversations/structured
3. Generate summaries for key sessions
```

## Search Tips

### Effective Queries
- Use exact error messages
- Include function/class names
- Use quotes for phrases: `"exact phrase"`
- Combine terms: `error AND authentication`

### Regex Patterns
- `import.*from.*react` - Find React imports
- `async\s+function` - Find async functions
- `TODO:.*database` - Find database TODOs
- `class\s+\w+Controller` - Find controller classes

### Filters
- Limit by session: `session_ids: ["id1"]`
- Filter by role: `message_types: ["assistant"]`
- Specific model: `models: ["claude-3-opus"]`

## Environment Variables

```bash
# .env file in mcp-server directory
CLAUDELENS_API_URL=http://localhost:8080
CLAUDELENS_API_KEY=your-optional-api-key
```

## Troubleshooting

| Issue | Quick Fix |
|-------|-----------|
| No MCP server | Restart Claude Desktop |
| Connection failed | Check backend: `curl http://localhost:8080/health` |
| No sessions | Verify MongoDB has data |
| Search fails | Check MongoDB text indexes |
| Export error | Verify session ID exists |

## Performance Tips

1. **Limit large queries**: Use `limit` parameter
2. **Use specific searches**: Avoid broad terms
3. **Paginate results**: Don't retrieve all at once
4. **Cache common searches**: Note frequent results
5. **Batch related operations**: Group similar requests

## Best Practices

1. **Name your sessions** in ClaudeLens
2. **Use markers** like TODO:, DECISION:, ISSUE:
3. **Regular summaries** at milestones
4. **Export critical work** for backup
5. **Be specific** in searches
6. **Document decisions** explicitly
7. **Tag related work** for easy finding

## Quick Test

Test your MCP installation:
```bash
cd mcp-server
python test_mcp_server.py
```

Expected output:
```
✓ Backend is accessible
✓ API Client tests completed
✓ MCP Server setup validated
✅ All tests passed!
```

## Getting Help

1. Check test output for specific errors
2. Verify backend logs: `docker-compose logs -f backend`
3. Enable debug mode in `.env`
4. Check Claude Desktop logs
5. Review [MCP-WORKFLOWS.md](./MCP-WORKFLOWS.md) for examples
