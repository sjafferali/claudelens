# Claude Message Hierarchy and Structure

## Overview

This document describes the correct message hierarchy for Claude conversations, particularly focusing on how tool operations (tool_use and tool_result) should be structured within the conversation tree.

## Table of Contents
1. [Message Types](#message-types)
2. [Hierarchy Structure](#hierarchy-structure)
3. [Tool Operation Flow](#tool-operation-flow)
4. [Field Mapping](#field-mapping)
5. [Examples](#examples)

---

## Message Types

### Core Message Types
- **user**: User messages to Claude
- **assistant**: Claude's responses (may contain tool_use blocks)
- **tool_use**: Extracted tool operation messages (created during ingest)
- **tool_result**: Tool execution results (created during ingest)
- **summary**: Session metadata (not part of conversation flow)

### Sidechain Classification
Messages that should be treated as sidechains (auxiliary operations):
- Messages with `isSidechain: true` flag
- Messages with `type: "tool_use"`
- Messages with `type: "tool_result"`
- Assistant messages containing tool_use content blocks

---

## Hierarchy Structure

### Correct Parent-Child Relationships

```
User Message
└── Assistant Message (response)
    └── Assistant Message (with tool_use content)
        ├── Tool Use Message (extracted)
        │   └── Tool Result Message (extracted)
        └── Next User Message (or Assistant continuation)
```

### Key Principles

1. **Assistant Chains**: When Claude uses tools, it creates a chain of assistant messages
2. **Tool Extraction**: Tool operations are extracted as children of their containing assistant message
3. **Parent Relationships**: Each message has exactly one parent (except conversation starters)
4. **Sidechain Grouping**: Tool messages group under their assistant parent in the sidechain panel

---

## Tool Operation Flow

### 1. User Request Requiring Tools
```json
{
  "type": "user",
  "uuid": "user-msg-123",
  "parentUuid": "previous-assistant-msg",
  "content": "Can you read the config.json file and tell me what it contains?"
}
```

### 2. Assistant Initial Response
```json
{
  "type": "assistant",
  "uuid": "assistant-msg-456",
  "parentUuid": "user-msg-123",
  "content": "I'll read the config.json file for you.",
  "model": "claude-opus-4-1-20250805"
}
```

### 3. Assistant with Tool Use
```json
{
  "type": "assistant",
  "uuid": "assistant-msg-789",
  "parentUuid": "assistant-msg-456",
  "message": {
    "content": [
      {
        "type": "tool_use",
        "id": "tool-call-001",
        "name": "Read",
        "input": {
          "file_path": "/path/to/config.json"
        }
      }
    ]
  }
}
```

### 4. Extracted Tool Use Message
```json
{
  "type": "tool_use",
  "uuid": "assistant-msg-789_tool_0",
  "parentUuid": "assistant-msg-789",  // Points to containing assistant
  "sessionId": "session-xyz",
  "content": "{\"type\": \"tool_use\", \"name\": \"Read\", \"input\": {\"file_path\": \"/path/to/config.json\"}}",
  "isSidechain": true
}
```

### 5. Extracted Tool Result Message
```json
{
  "type": "tool_result",
  "uuid": "assistant-msg-789_result_0",
  "parentUuid": "assistant-msg-789_tool_0",  // Points to tool_use message
  "sessionId": "session-xyz",
  "content": "{\"port\": 3000, \"debug\": true, \"database\": \"mongodb://localhost:27017\"}",
  "isSidechain": true
}
```

### 6. Assistant Continuation (Optional)
```json
{
  "type": "assistant",
  "uuid": "assistant-msg-101",
  "parentUuid": "assistant-msg-789",
  "content": "The config.json file contains settings for port 3000, debug mode enabled, and MongoDB connection."
}
```

---

## Field Mapping

### Database Fields (MongoDB)
All fields use camelCase in the database:
- `uuid`: Unique message identifier
- `parentUuid`: Reference to parent message
- `sessionId`: Session identifier
- `type`: Message type
- `timestamp`: ISO timestamp
- `isSidechain`: Boolean flag for auxiliary operations
- `content`: Message content (string or JSON string)
- `messageData`: Original message data structure
- `costUsd`: Cost in USD (for assistant messages)
- `model`: Model identifier (for assistant messages)

### API Response Fields
The API returns fields in snake_case (Python convention):
- `uuid`
- `parent_uuid` (database: `parentUuid`)
- `session_id` (database: `sessionId`)
- `cost_usd` (database: `costUsd`)
- `created_at` (database: `createdAt`)
- `message_uuid` (alias field)
- `parent_uuid_alias` (alias field)
- `session_id_alias` (alias field)

### Frontend Type Definitions
The frontend should use snake_case fields to match API responses:
```typescript
interface Message {
  _id: string;
  uuid: string;
  parent_uuid?: string;  // Changed from parentUuid
  session_id: string;     // Changed from sessionId
  type: 'user' | 'assistant' | 'tool_use' | 'tool_result';
  content: string;
  timestamp: string;
  isSidechain?: boolean;  // May need to become is_sidechain
  model?: string;
  cost_usd?: number;      // Changed from costUsd
  created_at?: string;    // Changed from createdAt
  usage?: {
    input_tokens?: number;  // Changed from inputTokens
    output_tokens?: number; // Changed from outputTokens
  };
}
```

---

## Examples

### Example 1: Simple Tool Use Flow

**Conversation:**
1. User asks to read a file
2. Claude responds and uses the Read tool
3. Tool returns content
4. User asks follow-up question

**Hierarchy:**
```
User: "What's in README.md?"
└── Assistant: "I'll read that for you"
    └── Assistant: [tool_use: Read]
        ├── Tool Use: Read(README.md)
        ├── Tool Result: "# Project Title..."
        └── User: "Can you summarize it?"
            └── Assistant: "The README contains..."
```

### Example 2: Multiple Tool Uses

**Conversation:**
1. User asks to analyze multiple files
2. Claude uses multiple tools
3. Claude provides analysis

**Hierarchy:**
```
User: "Compare config.json and package.json"
└── Assistant: "I'll read both files"
    └── Assistant: [tool_use: Read config.json]
        ├── Tool Use: Read(config.json)
        ├── Tool Result: {config content}
        └── Assistant: [tool_use: Read package.json]
            ├── Tool Use: Read(package.json)
            ├── Tool Result: {package content}
            └── Assistant: "Here's the comparison..."
                └── User: "Thanks!"
```

### Example 3: Complex Tool Chain

**Conversation:**
1. User asks to update multiple files
2. Claude reads, edits, and writes files
3. Multiple tool operations in sequence

**Hierarchy:**
```
User: "Update all test files to use the new API"
└── Assistant: "I'll update the test files"
    └── Assistant: [tool_use: Glob *.test.js]
        ├── Tool Use: Glob(*.test.js)
        ├── Tool Result: ["test1.js", "test2.js"]
        └── Assistant: [tool_use: Read test1.js]
            ├── Tool Use: Read(test1.js)
            ├── Tool Result: {content}
            └── Assistant: [tool_use: Edit test1.js]
                ├── Tool Use: Edit(test1.js)
                ├── Tool Result: "Success"
                └── Assistant: [tool_use: Read test2.js]
                    ├── Tool Use: Read(test2.js)
                    ├── Tool Result: {content}
                    └── Assistant: [tool_use: Edit test2.js]
                        ├── Tool Use: Edit(test2.js)
                        ├── Tool Result: "Success"
                        └── Assistant: "All test files have been updated"
```

---

## Sidechain Panel Grouping

With the correct hierarchy, the sidechain panel can properly group tool operations:

### Grouped Display
```
Main Conversation:
- User: "Update all test files"
- Assistant: "I'll update the test files"
- Assistant: "All test files have been updated"

Sidechain Panel:
▼ Assistant: "I'll update the test files"
  - 🔍 Glob: *.test.js
  - 📄 Read: test1.js
  - ✏️ Edit: test1.js
  - 📄 Read: test2.js
  - ✏️ Edit: test2.js
```

### Benefits
1. **Clean Main Flow**: Only user and summary assistant messages in main view
2. **Organized Operations**: All tool operations grouped by triggering assistant
3. **Collapsible Groups**: Can expand/collapse each assistant's operations
4. **Clear Relationships**: Parent-child relationships preserve operation context

---

## Migration Considerations

### From Current Structure to Correct Structure

**Current (Incorrect):**
- Tool messages have `parentUuid` pointing to same parent as assistant
- Tool messages are siblings of assistant messages
- Frontend expects camelCase but API returns snake_case fields

**Target (Correct):**
- Tool messages have `parentUuid` pointing to containing assistant
- Tool messages are children of assistant messages
- Frontend uses snake_case fields to match API responses

### Migration Steps
1. Update ingest process to set correct `parentUuid` for tool messages
2. Update frontend to use snake_case field names (parent_uuid, session_id, etc.)
3. Run migration script to update existing messages
4. Update frontend to handle both old and new structures during transition

---

## Performance Considerations

### Query Optimization
- Index on `parentUuid` for efficient tree traversal
- Index on `type` for filtering tool messages
- Index on `isSidechain` for sidechain queries
- Compound index on `sessionId` + `timestamp` for ordered retrieval

### Tree Building
- Build tree incrementally as messages load
- Cache parent-child relationships
- Use virtual scrolling for large conversations
- Lazy-load sidechain content

---

## Validation Rules

### Message Validation
1. Every message (except starters) must have a `parentUuid`
2. `parentUuid` must reference an existing message in the same session
3. Tool messages must have `isSidechain: true`
4. Tool result messages must have a tool_use parent
5. Assistant messages with tool_use content should have tool message children

### Consistency Checks
- No circular parent references
- No orphaned tool messages
- Tool operations properly paired (use → result)
- Timestamps maintain chronological order within branches
