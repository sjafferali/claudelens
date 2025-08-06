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

### Example 4: Real-World Tool Operation from Test Data

This example shows actual message structure from our test dataset with real UUIDs and field values:

**Raw Claude Export (assistant message with tool_use):**
```json
{
  "type": "assistant",
  "uuid": "msg-3",
  "parentUuid": "msg-2",
  "sessionId": "test-session-001",
  "timestamp": "2025-08-06T10:00:08Z",
  "message": {
    "role": "assistant",
    "content": [
      {
        "type": "tool_use",
        "id": "tool-001",
        "name": "LS",
        "input": {
          "path": "/home/user/project"
        }
      }
    ]
  },
  "model": "claude-opus-4-1-20250805",
  "isSidechain": false
}
```

**After Ingest Processing (extracted messages):**

1. **Original Assistant Message (modified):**
```json
{
  "type": "assistant",
  "uuid": "msg-3",
  "parentUuid": "msg-2",
  "sessionId": "test-session-001",
  "content": "📁 Listing directory: /home/user/project",
  "model": "claude-opus-4-1-20250805"
}
```

2. **Extracted Tool Use Message:**
```json
{
  "type": "tool_use",
  "uuid": "msg-3_tool_0",
  "parentUuid": "msg-3",  // Should point to containing assistant message
  "sessionId": "test-session-001",
  "timestamp": "2025-08-06T10:00:09Z",
  "content": "{\"type\":\"tool_use\",\"name\":\"LS\",\"input\":{\"path\":\"/home/user/project\"}}",
  "isSidechain": true
}
```

3. **Extracted Tool Result Message:**
```json
{
  "type": "tool_result",
  "uuid": "msg-3_result_0",
  "parentUuid": "msg-3_tool_0",  // Points to tool_use message
  "sessionId": "test-session-001",
  "timestamp": "2025-08-06T10:00:10Z",
  "content": "src/\nconfig.json\npackage.json\nREADME.md\ntests/",
  "isSidechain": true
}
```

**Resulting Hierarchy:**
```
msg-2 (user: "analyze project")
└── msg-3 (assistant: "listing directory")
    ├── msg-3_tool_0 (tool_use: LS)
    │   └── msg-3_result_0 (tool_result: directory contents)
    └── msg-4 (assistant continuation or next user message)
```

**Key Points:**
- Tool operations are extracted from assistant message content blocks
- Each tool message gets a UUID based on the pattern: `{assistant_uuid}_tool_{index}`
- Tool results are children of tool_use messages
- All tool messages should have `isSidechain: true`
- The parent assistant message content is replaced with a summary

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

## Sidechain Detection Logic

ClaudeLens uses a dual-layer approach to identify and process sidechain messages. Understanding this logic is crucial for proper UI functionality and data processing.

### Detection Criteria

A message is considered a sidechain if it meets **ANY** of the following criteria:

#### 1. Explicit Sidechain Flag
- `isSidechain: true` in the message document
- Set automatically during ingest for extracted tool messages
- Can be set manually for other auxiliary operations

#### 2. Tool Message Types
- `type === "tool_use"` (tool invocation messages)
- `type === "tool_result"` (tool execution results)
- Recognized even if `isSidechain` flag is missing or false

### Backend Detection (Ingest Process)

**Location**: `backend/app/services/ingest.py`

During message ingestion, the system automatically marks messages as sidechains:

```python
# Tool use messages
tool_doc = {
    "type": "tool_use",
    "parentUuid": message.uuid,  # Points to containing assistant
    "isSidechain": True,         # Explicit sidechain marking
    # ... other fields
}

# Tool result messages
result_doc = {
    "type": "tool_result",
    "parentUuid": tool_uuid,     # Points to corresponding tool_use
    "isSidechain": True,         # Explicit sidechain marking
    # ... other fields
}
```

**Detection Rules:**
1. **Assistant Messages with tool_use content**: Tool operations are extracted as separate messages
2. **Automatic Flagging**: All extracted tool messages get `isSidechain: true`
3. **Parent Relationships**: Proper parent-child hierarchy established during extraction
4. **UUID Patterns**: Tool messages follow `{parent_uuid}_tool_{index}` and `{parent_uuid}_result_{index}` patterns

### Frontend Detection (UI Processing)

**Location**: `frontend/src/components/SidechainPanel.tsx`

The frontend uses a comprehensive detection strategy:

```typescript
// Dual detection logic
const isSidechainMessage =
  message.isSidechain ||                    // Explicit flag
  message.type === 'tool_use' ||           // Tool invocation
  message.type === 'tool_result';          // Tool result

// Additional requirements for grouping
if (isSidechainMessage && message.parent_uuid) {
  // Group by parent for sidechain panel display
}
```

**Frontend Logic Benefits:**
1. **Redundancy**: Works even if backend flag is missing
2. **Backwards Compatibility**: Handles data from different ingest versions
3. **Type Safety**: Explicit type checking for tool messages
4. **Robust Filtering**: Multiple criteria ensure complete detection

### Detection Flow Example

**Step 1: Original Claude Export**
```json
{
  "type": "assistant",
  "uuid": "msg-123",
  "message": {
    "content": [
      {"type": "tool_use", "name": "Read", "input": {...}}
    ]
  }
}
```

**Step 2: Backend Processing**
- Detects tool_use in content array
- Extracts as separate message
- Sets `isSidechain: true` automatically
- Establishes parent relationship

**Step 3: Database Storage**
```json
{
  "type": "tool_use",
  "uuid": "msg-123_tool_0",
  "parentUuid": "msg-123",
  "isSidechain": true          // Explicit marking
}
```

**Step 4: Frontend Processing**
- Checks `isSidechain` flag ✓
- Checks `type === 'tool_use'` ✓
- Has valid `parent_uuid` ✓
- **Result**: Included in sidechain panel

### Edge Cases and Handling

#### Messages with Missing Flags
**Scenario**: Tool messages without `isSidechain: true`
**Solution**: Frontend type checking catches these via `message.type` comparison

#### Orphaned Tool Messages
**Scenario**: Tool messages without `parent_uuid`
**Solution**: Excluded from sidechain grouping but still detected as sidechains

#### Mixed Message Types
**Scenario**: Sessions with both flagged and unflagged sidechains
**Solution**: Dual detection ensures comprehensive coverage

#### Legacy Data
**Scenario**: Messages from older ingest versions
**Solution**: Frontend type checking provides backwards compatibility

### Debugging Sidechain Detection

The SidechainPanel includes comprehensive debug logging:

```typescript
console.log('[SidechainPanel] Total messages:', messages.length);
console.log('[SidechainPanel] Sidechain messages found:', sidechainCount);
console.log('[SidechainPanel] Tool messages (tool_use/tool_result):', toolMessageCount);
console.log('[SidechainPanel] Tool messages with parent_uuid:', withParentCount);
```

**Common Debug Scenarios:**
- **No sidechains detected**: Check message types and `isSidechain` flags
- **Sidechains not grouping**: Verify `parent_uuid` values are set correctly
- **Missing tool operations**: Check if extraction during ingest completed successfully

### Performance Considerations

**Efficient Detection:**
- Frontend filtering is O(n) single pass through messages
- Backend marking happens once during ingest
- No complex graph traversal required

**Memory Optimization:**
- Sidechain grouping uses Map data structure for O(1) parent lookup
- Messages sorted within groups only when needed
- Lazy evaluation of debug logging

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

## Troubleshooting Message Hierarchy Issues

This section provides solutions for common message hierarchy problems and debugging techniques.

### Common Issues and Solutions

#### 1. Sidechain Panel Shows "0 groups"

**Symptoms:**
- Sidechain panel displays "No sidechains to display"
- Tool operations not appearing in dedicated panel
- Messages appear in main flow instead of grouped

**Causes & Solutions:**

**Cause A: Missing `parent_uuid` in tool messages**
```bash
# Check tool messages in database
db.messages.find({
  "type": {"$in": ["tool_use", "tool_result"]},
  "parentUuid": {"$exists": false}
}).count()
```
*Solution*: Re-run ingest process to establish proper parent relationships

**Cause B: Tool messages not marked as sidechains**
```bash
# Check tool messages without sidechain flag
db.messages.find({
  "type": {"$in": ["tool_use", "tool_result"]},
  "isSidechain": {"$ne": true}
})
```
*Solution*: Update tool messages with sidechain flag or rely on frontend type detection

**Cause C: Frontend not receiving snake_case fields**
```typescript
// Check browser console for parent_uuid values
console.log('Sample tool message:', toolMessages[0]);
console.log('parent_uuid value:', toolMessages[0]?.parent_uuid);
```
*Solution*: Verify API response transformation from camelCase to snake_case

#### 2. Tool Messages Appear as False Branches

**Symptoms:**
- Branch indicators show on assistant messages with tools
- "Branch 1 of 2" appears where only one response exists
- Tree view shows incorrect branching

**Causes & Solutions:**

**Cause A: Tool messages included in branch detection**
```typescript
// Check branch detection logic excludes tool messages
const nonToolBranches = branches.filter(branch =>
  !isToolMessage(branch)
);
```
*Solution*: Ensure `utils/branch-detection.ts` excludes tool message types

**Cause B: Incorrect parent relationships**
```bash
# Find tool messages with wrong parents
db.messages.aggregate([
  {"$match": {"type": "tool_use"}},
  {"$lookup": {
    "from": "messages",
    "localField": "parentUuid",
    "foreignField": "uuid",
    "as": "parent"
  }},
  {"$match": {"parent.type": {"$ne": "assistant"}}}
])
```
*Solution*: Fix tool message parenting to point to containing assistant

#### 3. Messages Not Displaying in Tree View

**Symptoms:**
- Messages missing from conversation tree
- Incomplete tree structure
- React Flow shows fewer nodes than expected

**Causes & Solutions:**

**Cause A: Circular parent references**
```typescript
// Detect circular references
function detectCircularReferences(messages) {
  const visited = new Set();
  const visiting = new Set();

  for (const message of messages) {
    if (hasCircle(message, visited, visiting, messages)) {
      console.error('Circular reference detected:', message.uuid);
    }
  }
}
```
*Solution*: Fix database inconsistencies causing circular parent chains

**Cause B: Orphaned messages**
```bash
# Find messages with non-existent parents
db.messages.aggregate([
  {"$match": {"parentUuid": {"$ne": null}}},
  {"$lookup": {
    "from": "messages",
    "localField": "parentUuid",
    "foreignField": "uuid",
    "as": "parent"
  }},
  {"$match": {"parent": {"$size": 0}}}
])
```
*Solution*: Either fix parent references or mark as root messages

#### 4. Navigation Buttons Not Working

**Symptoms:**
- "Jump to parent" button doesn't scroll
- Message navigation fails silently
- Breadcrumb navigation broken

**Causes & Solutions:**

**Cause A: Missing DOM element IDs**
```typescript
// Check if message elements have proper IDs
const messageElement = document.getElementById(`message-${messageId}`);
if (!messageElement) {
  console.error('Message element not found:', messageId);
}
```
*Solution*: Ensure `MessageList` component adds `id` attributes to message containers

**Cause B: Undefined parent_uuid values**
```typescript
// Check for undefined parent relationships
const brokenNavigation = messages.filter(m =>
  m.parent_uuid === undefined && m.type !== 'user'
);
console.log('Messages with broken navigation:', brokenNavigation);
```
*Solution*: Verify API field transformation and database integrity

#### 5. Cost Calculations Incorrect

**Symptoms:**
- Tool message costs showing as $0.00
- Double-counting in session totals
- Cost missing from sidechain panel

**Causes & Solutions:**

**Cause A: Cost not propagated to tool messages**
```bash
# Check tool messages with cost data
db.messages.find({
  "type": "tool_use",
  "costUsd": {"$exists": true, "$gt": 0}
}).count()
```
*Solution*: Ensure cost inheritance from parent assistant messages

**Cause B: Double-counting in aggregations**
```typescript
// Check cost calculation logic
const totalCost = messages
  .filter(m => m.type !== 'tool_use' && m.type !== 'tool_result')
  .reduce((sum, m) => sum + (m.cost_usd || 0), 0);
```
*Solution*: Exclude tool messages from cost aggregations

### Debugging Techniques

#### 1. Database Inspection Commands

**Check message hierarchy integrity:**
```bash
# Count messages by type
db.messages.aggregate([
  {"$group": {"_id": "$type", "count": {"$sum": 1}}},
  {"$sort": {"count": -1}}
])

# Find root messages (no parent)
db.messages.find({"parentUuid": null}).count()

# Check parent-child relationships
db.messages.aggregate([
  {"$match": {"parentUuid": {"$ne": null}}},
  {"$lookup": {
    "from": "messages",
    "localField": "parentUuid",
    "foreignField": "uuid",
    "as": "parent"
  }},
  {"$project": {
    "uuid": 1,
    "type": 1,
    "parentExists": {"$size": "$parent"}
  }},
  {"$match": {"parentExists": 0}}
])
```

#### 2. Frontend Debug Console Commands

**Inspect message structure in browser:**
```javascript
// Check loaded messages
console.log('All messages:', window.__messages__);

// Check sidechain detection
const sidechains = window.__messages__.filter(m =>
  m.isSidechain || m.type === 'tool_use' || m.type === 'tool_result'
);
console.log('Detected sidechains:', sidechains);

// Check parent-child relationships
const orphans = window.__messages__.filter(m =>
  m.parent_uuid && !window.__messages__.find(p => p.uuid === m.parent_uuid)
);
console.log('Orphaned messages:', orphans);
```

#### 3. API Response Validation

**Check field transformation:**
```bash
# Test API response format
curl -s "http://localhost:8000/api/v1/sessions/SESSION_ID/messages" | \
  jq '.messages[0] | keys' | grep -E "(parent_uuid|session_id|cost_usd)"

# Verify sidechain detection
curl -s "http://localhost:8000/api/v1/sessions/SESSION_ID/messages" | \
  jq '.messages[] | select(.type == "tool_use") | {uuid, parent_uuid, isSidechain}'
```

### Prevention Best Practices

#### 1. Data Integrity Checks

**Before deploying hierarchy changes:**
- Run database integrity checks
- Verify all tool messages have parent_uuid
- Test sidechain detection with sample data
- Validate API response transformations

#### 2. Monitoring and Alerts

**Set up monitoring for:**
- Messages with missing parent_uuid values
- Tool messages without isSidechain flag
- Circular reference detection in conversation trees
- API response field format validation

#### 3. Testing Scenarios

**Always test with:**
- Conversations containing no tool operations
- Conversations with multiple sequential tools
- Conversations with nested tool operations
- Large conversations (500+ messages)
- Conversations with regenerated responses

### Recovery Procedures

#### 1. Database Repair Scripts

**Fix missing parent relationships:**
```javascript
// MongoDB script to fix tool message parents
db.messages.find({"type": "tool_use", "parentUuid": null}).forEach(function(doc) {
  const parentId = doc.uuid.split('_tool_')[0];
  db.messages.updateOne(
    {"_id": doc._id},
    {"$set": {"parentUuid": parentId}}
  );
});
```

#### 2. Re-ingestion Process

**When to re-ingest:**
- Major hierarchy corruption detected
- Significant number of orphaned messages
- Cost calculation inconsistencies across sessions

**How to re-ingest safely:**
1. Backup current database
2. Export problematic session data
3. Delete corrupted session messages
4. Re-run ingest with fixed logic
5. Verify hierarchy integrity

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
