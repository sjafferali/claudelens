# ClaudeLens MCP Usage Guide

## Getting Started with Claude Desktop Integration

This guide provides practical instructions for using the ClaudeLens MCP server with Claude Desktop to enhance your development workflow.

## Initial Setup

### 1. Start ClaudeLens Backend
```bash
# Navigate to ClaudeLens directory
cd /path/to/claudelens

# Start the backend services
docker-compose up -d

# Verify backend is running
curl http://localhost:8080/health
```

### 2. Install MCP Server
```bash
# Navigate to MCP server directory
cd mcp-server

# Install dependencies
uv add .

# Run tests to verify setup
python test_mcp_server.py

# Install in Claude Desktop
uv run mcp install claudelens_mcp/server.py --name "ClaudeLens"
```

### 3. Restart Claude Desktop
After installation, restart Claude Desktop to load the new MCP server.

## Basic Usage Patterns

### Accessing Resources

Resources are accessed using special URIs that Claude recognizes:

```markdown
# List all sessions
Use resource: claudelens://sessions

# Get specific session details
Use resource: claudelens://sessions/SESSION_ID

# Get all messages from a session
Use resource: claudelens://sessions/SESSION_ID/messages

# View structured conversations by project
Use resource: claudelens://conversations/structured

# Get a specific message
Use resource: claudelens://messages/MESSAGE_ID
```

### Using Tools

Tools are invoked by name with parameters:

```markdown
# Search for text across all conversations
Use tool: search_messages
Parameters:
- query: "error handling"
- limit: 20
- highlight: true

# Search for code snippets
Use tool: search_code
Parameters:
- query: "async function"
- language: "javascript"

# Navigate conversation threads
Use tool: get_conversation_thread
Parameters:
- session_id: "abc123"
- message_uuid: "xyz789"
- depth: 10

# Generate session summary
Use tool: generate_summary
Parameters:
- session_id: "abc123"

# Export a session
Use tool: export_session
Parameters:
- session_id: "abc123"
- format: "markdown"
```

### Using Prompts

Prompts provide templates for common tasks:

```markdown
# Analyze a session
Use prompt: Session Analysis
Parameters:
- session_id: "abc123"

# Search and summarize
Use prompt: Search and Summarize
Parameters:
- query: "authentication implementation"
- limit: 30

# Analyze code patterns
Use prompt: Code Search Analysis
Parameters:
- query: "database connection"
- language: "python"
```

## Common Usage Scenarios

### Scenario 1: Continuing Yesterday's Work

```markdown
You: "I was working on the authentication system yesterday. Can you help me continue?"

Claude will:
1. Use: search_messages with query "authentication"
2. Use: claudelens://sessions to find recent sessions
3. Use: get_session_messages to retrieve the conversation
4. Summarize what was done and what remains
```

### Scenario 2: Debugging a Recurring Error

```markdown
You: "I'm getting a 'connection refused' error again"

Claude will:
1. Use: search_messages with query "connection refused"
2. Find previous occurrences and solutions
3. Use: get_message_context to understand the full context
4. Apply the solution that worked before
```

### Scenario 3: Code Review Preparation

```markdown
You: "Help me prepare a code review for the user management feature"

Claude will:
1. Use: search_code with query "user management"
2. Use: get_conversation_thread to trace implementation decisions
3. Use: export_session to create documentation
4. Generate a comprehensive review document
```

### Scenario 4: Project Handover

```markdown
You: "I need to create documentation for the project handover"

Claude will:
1. Use: list_projects to see all projects
2. Use: claudelens://conversations/structured for project overview
3. Use: generate_summary for key sessions
4. Create comprehensive handover documentation
```

## Advanced Usage Tips

### 1. Efficient Searching

#### Use Specific Queries
```markdown
# ❌ Too broad
search_messages "error"

# ✅ Specific
search_messages "TypeError in UserComponent"
```

#### Combine Filters
```markdown
search_messages with:
- query: "database migration"
- session_ids: ["session1", "session2"]
- message_types: ["assistant"]
- models: ["claude-3-opus"]
```

#### Use Regex for Complex Searches
```markdown
search_messages with:
- query: "import.*from.*react"
- is_regex: true
```

### 2. Session Management

#### Find Recent Work
```markdown
# Get last 10 sessions
claudelens://sessions

# Filter by date (in natural language)
"Show me sessions from this week about API development"
```

#### Track Progress
```markdown
# Generate summaries for milestone sessions
"Generate summaries for all sessions related to v2.0 release"
```

### 3. Code Navigation

#### Track Code Evolution
```markdown
# Find all versions of a function
search_code "function processPayment"

# See how it changed
"Show me how processPayment function evolved across sessions"
```

#### Find Implementation Patterns
```markdown
# Search for patterns
search_code "useEffect.*cleanup"

# Analyze patterns
"What cleanup patterns have we used in React components?"
```

### 4. Analytics and Insights

#### Session Analytics
```markdown
get_session_analytics for session "abc123"
# Returns: token usage, costs, duration, complexity metrics
```

#### Project Overview
```markdown
list_projects
# Then for each project:
"Analyze the complexity and cost trends for [project]"
```

## Conversation Starters

### For New Sessions
```markdown
"Before we start, check if we have any previous work on [topic]"
```

### For Continuing Work
```markdown
"Let's continue from where we left off. Please retrieve our last session about [topic]"
```

### For Problem Solving
```markdown
"I'm facing [issue]. Check if we've encountered this before"
```

### For Code Review
```markdown
"Review the implementation of [feature] across all our sessions"
```

## Productivity Shortcuts

### Quick Commands

Create these as snippets or aliases:

```markdown
# Show recent work
"@recent" → List last 5 sessions with summaries

# Find todos
"@todos" → Search for "TODO" or "FIXME" in recent sessions

# Error history
"@errors [error_text]" → Search for specific error with solutions

# Code search
"@code [pattern]" → Quick code search across all sessions

# Project status
"@status [project]" → Summary of project progress

# Continue work
"@continue" → Find and resume most recent incomplete task
```

### Batch Operations

```markdown
# Export all sessions for a project
"Export all sessions for project X in markdown format"

# Generate weekly summary
"Summarize all work done this week across all projects"

# Find all decisions
"List all architectural decisions made in the last month"
```

## Best Practices

### 1. Conversation Management

- **Use Clear Markers**: Start important sections with markers like "DECISION:", "TODO:", "ISSUE:"
- **Regular Summaries**: Ask for summaries at natural breakpoints
- **Name Sessions**: Give sessions descriptive names in ClaudeLens
- **Tag Important Messages**: Use consistent tags for easy searching

### 2. Search Optimization

- **Be Specific**: Use exact error messages or function names
- **Use Filters**: Narrow searches with session/project filters
- **Save Common Searches**: Note frequently used search patterns
- **Use Regex Wisely**: For pattern matching, not simple text search

### 3. Context Preservation

- **Export Critical Sessions**: Keep backups of important work
- **Document Decisions**: Explicitly state why choices were made
- **Link Related Work**: Reference previous sessions in new work
- **Create Checkpoints**: Summarize at major milestones

### 4. Performance Tips

- **Limit Large Retrievals**: Use pagination for large result sets
- **Cache Common Searches**: Note results of frequent searches
- **Batch Related Queries**: Group related searches together
- **Use Structured Resources**: Prefer structured endpoints for overview

## Troubleshooting Common Issues

### Issue: "No MCP server available"
**Solution:** Restart Claude Desktop after installation

### Issue: "Cannot connect to ClaudeLens"
**Solution:**
1. Check backend is running: `curl http://localhost:8080/health`
2. Verify `.env` configuration in mcp-server directory
3. Check firewall settings

### Issue: "No sessions found"
**Solution:**
1. Verify ClaudeLens has collected conversation data
2. Check MongoDB is running and accessible
3. Ensure text indexes are created

### Issue: "Search returns no results"
**Solution:**
1. Try broader search terms
2. Check if regex mode is accidentally enabled
3. Verify text indexes in MongoDB

### Issue: "Export fails"
**Solution:**
1. Check session ID is valid
2. Ensure export endpoints are available in backend
3. Verify sufficient memory for large exports

## Integration with Development Workflow

### 1. Git Integration
```markdown
# Before committing
"Review all changes made in this session"
"Generate commit message based on our work"
```

### 2. Documentation
```markdown
# Auto-generate docs
"Create API documentation from our implementation sessions"
"Generate README from project sessions"
```

### 3. Testing
```markdown
# Find test cases
"What test cases did we discuss for [feature]?"
"Show all error scenarios we've encountered"
```

### 4. Code Review
```markdown
# Prepare review
"Summarize implementation decisions for [feature]"
"List all TODOs and FIXMEs from this feature"
```

## Tips for Team Collaboration

### Shared Knowledge Base
- Export important sessions for team documentation
- Create summaries of architectural decisions
- Document error solutions for team reference

### Onboarding
- Use structured conversations to show project overview
- Export key sessions as onboarding materials
- Create learning paths from conversation history

### Code Standards
- Search for patterns to ensure consistency
- Find and document agreed-upon conventions
- Track evolution of coding standards

## Conclusion

The ClaudeLens MCP integration transforms Claude Desktop into a powerful development assistant with perfect memory. By following these usage patterns and best practices, you can:

- Never lose context between sessions
- Build on previous work efficiently
- Learn from past solutions
- Maintain project continuity
- Share knowledge effectively

Remember: The more structured and consistent your conversation patterns, the more valuable your conversation history becomes as a searchable knowledge base.
