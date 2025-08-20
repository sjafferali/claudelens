# ClaudeLens MCP Workflows

## Recovering from Conversation Compaction

### The Problem

When working on complex projects in Claude Code, conversations can become too long and get "compacted" - Claude loses access to earlier parts of the conversation. This is frustrating when you need to:

- Reference earlier decisions or implementations
- Understand why certain approaches were taken
- Continue work that was discussed but not completed
- Debug issues that relate to earlier code
- Maintain context across multiple coding sessions

### The Solution

The ClaudeLens MCP server provides perfect memory across all your Claude conversations, making compaction a non-issue and enabling true long-term project continuity.

## Primary Workflow: Database Migration Recovery

### Scenario
You've been working with Claude Code for hours on a complex database migration. The conversation got compacted, and now Claude doesn't remember:
- The schema design decisions
- Migration scripts already written
- Error patterns you encountered
- Solutions you already tried

### Step-by-Step Recovery

#### 1. Find the Previous Session
```
Claude: "I'll help you continue the database migration. Let me first check our previous conversations about this project."

*Uses resource:* claudelens://sessions
*Finds session from 2 hours ago titled "Database Migration - User Tables"*
```

#### 2. Search for Specific Context
```
Claude: "Let me search for the migration scripts we discussed earlier."

*Uses tool:* search_code with query "CREATE TABLE users"
*Finds 3 code blocks with the schema definitions*

*Uses tool:* search_messages with query "foreign key constraint error"
*Finds the error you encountered and the solution attempted*
```

#### 3. Reconstruct the Full Context
```
Claude: "I'll retrieve the complete conversation to understand the full context."

*Uses resource:* claudelens://sessions/abc-123/messages
*Reviews all 150 messages from the previous session*

*Uses tool:* export_session with session_id "abc-123"
*Gets structured export with thread navigation*
```

#### 4. Analyze What Was Accomplished
```
Claude: "Let me analyze what was completed and what remains."

*Uses prompt:* Session Analysis for session abc-123
*Generates summary of:*
- ✅ User table schema designed
- ✅ Initial migration script created
- ⚠️ Foreign key issue encountered
- ❌ Indexes not yet added
- ❌ Rollback script not written
```

#### 5. Continue From Where You Left Off
```sql
-- Claude: "Based on our previous conversation, here's where we left off:"

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    organization_id UUID REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- We still need to add these indexes:
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_users_email ON users(email);

-- And create the rollback script...
```

## Additional Workflows

### 1. Debug Pattern Recognition

**Purpose:** Find and apply solutions to recurring errors

```markdown
Workflow: "Find All Similar Errors"
1. Current error: "TypeError: Cannot read property 'map' of undefined"
2. Search previous conversations: search_messages "TypeError" + "map"
3. Find 5 previous occurrences with solutions
4. Identify the pattern that worked before
5. Apply the proven solution
```

**Example Usage:**
```
You: "I'm getting a TypeError with map again"
Claude: *searches for similar errors*
Claude: "I found this error occurred 3 times before. In all cases, the issue was that the API response wasn't an array. Here's the solution we used that worked..."
```

### 2. Code Refactoring Continuity

**Purpose:** Resume interrupted refactoring sessions

```markdown
Workflow: "Resume Refactoring Session"
1. Search for refactoring discussions: search_messages "refactor" AND "component"
2. Get the refactoring plan: get_message_context for planning message
3. Check what was completed: search_code "// TODO: Refactor"
4. List remaining refactoring tasks
5. Continue from the next uncompleted task
```

**Example Usage:**
```
You: "We were refactoring the user components yesterday, can we continue?"
Claude: *retrieves refactoring plan and progress*
Claude: "I found our refactoring session. We completed 3 of 7 components. The next one is UserProfile component, which needs to be converted to use hooks instead of class components..."
```

### 3. Architecture Decision History

**Purpose:** Understand and reference past architectural decisions

```markdown
Workflow: "Why Did We Choose This?"
1. Search for architecture discussions: search_messages "architecture" OR "design pattern"
2. Find the session where decision was made
3. Export full session for documentation
4. Reference specific messages with reasoning
5. Create decision record
```

**Example Usage:**
```
You: "Why did we choose Redux over Context API for state management?"
Claude: *searches for architecture discussions*
Claude: "Found the discussion from last week. The decision was based on: 1) Need for time-travel debugging, 2) Complex state updates across 15+ components, 3) Team familiarity with Redux..."
```

### 4. Learning From Past Mistakes

**Purpose:** Avoid repeating previous issues

```markdown
Workflow: "Avoid Previous Issues"
1. Starting similar project type
2. Search for problems in related work: search_messages "performance issue" project_id="similar-project"
3. Review solutions that worked
4. Create checklist of things to avoid
5. Proactively implement fixes
```

**Example Usage:**
```
You: "Starting a new React app with real-time updates"
Claude: *searches for issues in similar projects*
Claude: "In your last real-time React app, you encountered these issues: 1) Memory leaks from WebSocket listeners - solved by cleanup in useEffect, 2) Re-render storms - solved by memoization..."
```

### 5. Cross-Session Code Evolution

**Purpose:** Track how code evolved across sessions

```markdown
Workflow: "Track Code Evolution"
1. Search for all versions: search_code "class UserService"
2. Navigate threads to see evolution: get_conversation_thread
3. Understand why changes were made
4. Document the evolution
5. Make informed decisions about further changes
```

**Example Usage:**
```
You: "Show me how our UserService has evolved"
Claude: *tracks code evolution*
Claude: "UserService evolution: v1 (Monday): Basic CRUD, v2 (Tuesday): Added caching, v3 (Wednesday): Converted to singleton, v4 (Thursday): Added error handling..."
```

### 6. Project Knowledge Transfer

**Purpose:** Onboard new team members or refresh your own memory

```markdown
Workflow: "Project Onboarding"
1. List all project sessions: search by project name
2. Generate summaries for key sessions
3. Identify critical decisions and implementations
4. Create comprehensive project overview
5. Highlight gotchas and important context
```

### 7. Error Resolution Database

**Purpose:** Build a searchable database of solved problems

```markdown
Workflow: "Solution Archive"
1. When error is solved, Claude automatically searches for similar past errors
2. If new, adds to knowledge base
3. If exists, updates with new solution variant
4. Creates linkage between related issues
5. Builds comprehensive troubleshooting guide
```

## Automated Context Recovery

### Claude Code Prompt Template

Add this to your Claude Code conversation starter:

```markdown
When starting a new conversation about an existing project:

1. ALWAYS first check for previous related sessions:
   - Use: list_projects to see all projects
   - Use: claudelens://sessions with search term matching project name

2. If continuing previous work, automatically:
   - Export the last relevant session
   - Search for TODOs and FIXMEs
   - Summarize what was accomplished
   - List what remains to be done

3. Before suggesting solutions:
   - Search for similar problems previously solved
   - Check if this approach was already tried

4. When encountering errors:
   - Search for the exact error message
   - Check if it was encountered before
   - Apply previous successful fixes first
```

## Quick Commands Reference

### Context Recovery Commands

| Command | Action |
|---------|--------|
| "Show me our last conversation about [topic]" | Searches and retrieves relevant session |
| "What did we decide about [feature]?" | Finds specific architectural decisions |
| "Find all the times we encountered [error]" | Searches for error patterns and solutions |
| "Continue the [task] we were working on" | Retrieves incomplete work and context |
| "Show me all code we wrote for [component]" | Aggregates all code versions across sessions |
| "Why did we implement [feature] this way?" | Traces back to original discussions |
| "What's left to do on [project]?" | Analyzes sessions to find incomplete tasks |
| "Show me the evolution of [code/file]" | Tracks changes across sessions |
| "What errors did we face in [project]?" | Lists all errors and their solutions |
| "Summarize our work on [feature]" | Creates comprehensive feature summary |

## Best Practices

### 1. Session Naming
Always give your sessions descriptive names in ClaudeLens so they're easier to find later:
- ❌ "Untitled Session"
- ✅ "Database Migration - User Tables"

### 2. Use Markers in Conversations
Add clear markers in your conversations for easy searching:
- "DECISION: Using PostgreSQL for..."
- "TODO: Implement error handling for..."
- "ISSUE: Performance problem with..."
- "SOLUTION: Fixed by adding index on..."

### 3. Regular Summaries
Ask Claude to generate session summaries periodically:
```
You: "Generate a summary of what we've accomplished so far"
Claude: *uses generate_summary tool*
```

### 4. Project Organization
Keep related sessions in the same project for easier navigation and searching.

### 5. Export Important Sessions
For critical work, export sessions for external backup:
```
You: "Export this session in markdown format"
Claude: *uses export_session tool with format="markdown"*
```

## Advanced Patterns

### Pattern 1: Continuous Learning System
```python
# Claude automatically builds a knowledge base
if error_encountered:
    similar_errors = search_messages(error_message)
    if similar_errors:
        apply_known_solution()
    else:
        solve_and_document_new_error()
```

### Pattern 2: Regression Prevention
```python
# Before making changes
previous_issues = search_messages(f"bug in {component_name}")
if previous_issues:
    add_tests_for_known_issues()
    warn_about_previous_problems()
```

### Pattern 3: Code Review Memory
```python
# During code review
past_reviews = search_messages(f"review {code_pattern}")
if past_reviews:
    apply_previous_feedback()
    check_if_issues_addressed()
```

## Metrics and Analytics

Use the analytics tools to understand your development patterns:

1. **Session Analytics** - Understand time spent, costs, token usage
2. **Project Analytics** - Track project complexity and resource usage
3. **Search Patterns** - See what you search for most often
4. **Error Frequency** - Identify recurring problems

## Conclusion

The ClaudeLens MCP server transforms Claude from a stateless assistant into a system with perfect memory of all your conversations. This enables:

- **Zero Context Loss** - Never lose work due to conversation limits
- **Cumulative Learning** - Each session builds on previous knowledge
- **Team Knowledge Sharing** - Access collective conversation history
- **Intelligent Assistance** - Claude can reference past decisions and solutions
- **Project Continuity** - Seamlessly continue work across sessions

With these workflows, conversation compaction becomes irrelevant, and you gain a powerful development partner with complete historical context.
