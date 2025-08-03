# Claude Data Directory Structure Documentation

This document provides a comprehensive overview of the Claude data directory structure and message formats that are synced to the ClaudeLens application.

## Directory Structure Overview

```
clauddatadir/
├── __store.db                 # SQLite database (legacy format)
├── config.json               # Configuration file with model selection
├── settings.json             # Application settings (timeouts, model preference)
├── commands/                 # Custom command definitions
│   ├── create-prompt-to-pickup-task.md
│   └── remove-trailing-spaces.md
├── projects/                 # Project-specific conversation data
│   └── {project-path}/      # Sanitized project paths
│       └── {session-id}.jsonl  # JSONL files containing messages
├── shell-snapshots/          # Bash session snapshots
│   └── snapshot-bash-{timestamp}-{id}.sh
├── statsig/                  # Feature flag evaluations
│   └── statsig.cached.evaluations.*
└── todos/                    # Todo lists for each session
    └── {session-id}-agent-{session-id}.json
```

## Message Format

All messages are stored in JSONL (JSON Lines) format within project directories. Each line represents a single message or metadata entry.

### Common Message Fields

All messages (except summaries) share these common fields:

```json
{
  "uuid": "unique-message-id",
  "parentUuid": "parent-message-id or null",
  "sessionId": "session-identifier",
  "type": "user|assistant|summary",
  "timestamp": "2025-08-02T04:52:07.349Z",
  "isSidechain": false,
  "userType": "external",
  "cwd": "/path/to/project",
  "version": "1.0.67",
  "gitBranch": "main"
}
```

## Message Types

### 1. Summary Message

Summary messages provide a brief description of the conversation and are linked to the last message (leaf) of a conversation thread.

**Structure:**
```json
{
  "type": "summary",
  "summary": "Brief description of the conversation topic",
  "leafUuid": "uuid-of-last-message-in-thread"
}
```

**Example:**
```json
{
  "type": "summary",
  "summary": "Scene Details Edit Button Not Functioning Properly",
  "leafUuid": "99cc3e0e-59e5-4d6b-b0ba-6f2a3f874bca"
}
```

**When Generated:** Created when a conversation thread is completed or when Claude generates a summary of the discussion.

### 2. User Messages

User messages represent input from the user, including both direct text input and tool use results.

#### 2.1 Text Input Message

User messages can have either array-based content or direct string content.

**Structure (Array-based):**
```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": "User's input text"
      }
    ]
  }
}
```

**Structure (String-based):**
```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": "User's input text"
  }
}
```

**Example:**
```json
{
  "parentUuid": null,
  "isSidechain": false,
  "userType": "external",
  "cwd": "/Users/sjafferali/github/personal/claudelens",
  "sessionId": "0bce4261-0add-4645-8d72-888c91496f82",
  "version": "1.0.67",
  "gitBranch": "main",
  "type": "user",
  "message": {
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": "Review the docker-compose.yml file. Which of the environment variables are not actually in use?"
      }
    ]
  },
  "uuid": "15e15459-c55e-4c93-8a2e-d95794c41d63",
  "timestamp": "2025-08-02T04:52:07.349Z"
}
```

**When Generated:** When the user types a message or prompt.

#### 2.2 Tool Result Message

**Structure:**
```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [
      {
        "tool_use_id": "tool-invocation-id",
        "type": "tool_result",
        "content": "Result content from tool execution"
      }
    ]
  },
  "toolUseResult": {
    // Tool-specific result data
  }
}
```

**Example - TodoWrite Result:**
```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [
      {
        "tool_use_id": "toolu_01ECz95JHwGJRVVjtsvRSccg",
        "type": "tool_result",
        "content": "Todos have been modified successfully..."
      }
    ]
  },
  "toolUseResult": {
    "oldTodos": [],
    "newTodos": [
      {
        "content": "Find and examine the scene details page component",
        "status": "in_progress",
        "priority": "high",
        "id": "1"
      }
    ]
  }
}
```

**When Generated:** After Claude invokes a tool and receives the result.

### 3. Assistant Messages

Assistant messages represent Claude's responses, including text responses and tool invocations.

#### 3.1 Text Response

**Structure:**
```json
{
  "type": "assistant",
  "message": {
    "id": "msg_id",
    "type": "message",
    "role": "assistant",
    "model": "claude-opus-4-20250514",
    "content": [
      {
        "type": "text",
        "text": "Claude's response text"
      }
    ],
    "stop_reason": null,
    "stop_sequence": null,
    "usage": {
      "input_tokens": 4,
      "cache_creation_input_tokens": 5031,
      "cache_read_input_tokens": 10833,
      "output_tokens": 3,
      "service_tier": "standard"
    }
  },
  "requestId": "req_id",
  "costUsd": 0.0023,  // Optional
  "durationMs": 1234   // Optional
}
```

**Example:**
```json
{
  "type": "assistant",
  "message": {
    "id": "msg_01MUDYPZ137RatQ9E9pbUYPM",
    "type": "message",
    "role": "assistant",
    "model": "claude-opus-4-20250514",
    "content": [
      {
        "type": "text",
        "text": "I'll help you review the docker-compose.yml file and investigate which environment variables are not in use."
      }
    ],
    "usage": {
      "input_tokens": 4,
      "cache_creation_input_tokens": 5031,
      "cache_read_input_tokens": 10833,
      "output_tokens": 3,
      "service_tier": "standard"
    }
  }
}
```

**When Generated:** When Claude provides a text response.

#### 3.2 Tool Use Message

**Structure:**
```json
{
  "type": "assistant",
  "message": {
    "content": [
      {
        "type": "tool_use",
        "id": "tool-invocation-id",
        "name": "ToolName",
        "input": {
          // Tool-specific parameters
        }
      }
    ],
    "stop_reason": "tool_use"
  }
}
```

**Example - Read Tool:**
```json
{
  "type": "assistant",
  "message": {
    "content": [
      {
        "type": "tool_use",
        "id": "toolu_012Y23HdApDEuKgTHaWa7Jgj",
        "name": "Read",
        "input": {
          "file_path": "/Users/sjafferali/github/personal/claudelens/docker-compose.yml"
        }
      }
    ],
    "stop_reason": "tool_use"
  }
}
```

**When Generated:** When Claude decides to use a tool.

#### 3.3 Thinking Response

Claude can include internal reasoning in a "thinking" content type. This contains Claude's thought process before providing a response.

**Structure:**
```json
{
  "type": "assistant",
  "message": {
    "id": "msg_id",
    "type": "message",
    "role": "assistant",
    "model": "claude-opus-4-20250514",
    "content": [
      {
        "type": "thinking",
        "thinking": "Claude's internal reasoning text...",
        "signature": "cryptographic signature string"
      }
    ],
    "stop_reason": null,
    "stop_sequence": null,
    "usage": { /* token usage */ }
  }
}
```

**Example:**
```json
{
  "type": "assistant",
  "message": {
    "id": "msg_01UqBARwmVg8VLYWzUrmmRGi",
    "content": [
      {
        "type": "thinking",
        "thinking": "The user says that tag filtering is still not working. Let me think about what could be going wrong:\n\n1. The axios parameter serializer looks correct...",
        "signature": "EvcQCkYIBRgCKkAlCuRlSPcM7dFQ..."
      }
    ]
  }
}
```

**When Generated:** When Claude is in "thinking" mode and processes internal reasoning before responding.

#### 3.4 Mixed Content Messages

Assistant messages can contain multiple content types in a single response.

**Structure:**
```json
{
  "type": "assistant",
  "message": {
    "content": [
      {
        "type": "thinking",
        "thinking": "Internal reasoning..."
      },
      {
        "type": "text",
        "text": "Visible response to user..."
      },
      {
        "type": "tool_use",
        "name": "ToolName",
        "input": { /* parameters */ }
      }
    ]
  }
}
```

**When Generated:** When Claude combines thinking, text response, and/or tool use in a single message.

## Tool Types and Their Results

### Common Tools and Result Formats

1. **TodoWrite**
   - Result contains `oldTodos` and `newTodos` arrays
   - Each todo has: `id`, `content`, `status`, `priority`

2. **Read**
   - Result contains file content with line numbers
   - Additional metadata: `filePath`, `numLines`, `startLine`, `totalLines`

3. **Task** (Agent invocation)
   - Result contains agent execution output
   - May include structured data or text output

4. **Glob**
   - Result contains matching file paths
   - Metadata: `numFiles`, `filenames`, `truncated`

5. **Bash**
   - Result contains command output
   - May include `exitCode`, `stdout`, `stderr`

6. **Edit/MultiEdit**
   - Result confirms successful edits
   - May include affected line numbers

7. **WebSearch/WebFetch**
   - Result contains fetched content
   - May include URL redirects or search results

## Session and Project Organization

### Session IDs
- Format: UUID (e.g., `0bce4261-0add-4645-8d72-888c91496f82`)
- Each session represents a single conversation thread
- Sessions are grouped by project based on the working directory

### Project Paths
- Derived from the `cwd` field in messages
- Sanitized by replacing `/` with `-` in the directory structure
- Example: `/Users/user/project` → `-Users-user-project/`

## Special Message Properties

### Sidechain Messages

Some messages have `"isSidechain": true`, indicating they are part of a parallel conversation branch (e.g., when Claude spawns an agent or explores alternatives). These messages:
- Are typically used for internal exploration or agent tasks
- May not be shown in the main conversation flow
- Have the same structure but are marked with the sidechain flag

**Example:**
```json
{
  "parentUuid": null,
  "isSidechain": true,  // Marks this as a sidechain message
  "userType": "external",
  "type": "user",
  "message": {
    "role": "user",
    "content": "Find the main application files..."
  }
}
```

## Additional Files

### Todo Files
- Located in `todos/` directory
- Named: `{session-id}-agent-{session-id}.json`
- Contains array of todo items with their status

### Shell Snapshots
- Located in `shell-snapshots/` directory
- Named: `snapshot-bash-{timestamp}-{random-id}.sh`
- Contains bash session history and state

### Config Files
- `config.json`: Contains model selection and feature flags
- `settings.json`: Application preferences and environment settings

## Data Flow

1. **Message Creation**: User input or Claude response generates a message
2. **JSONL Storage**: Message is appended to the appropriate project/session JSONL file
3. **CLI Sync**: The CLI tool reads these JSONL files and syncs to the backend
4. **Backend Processing**: Messages are validated, deduplicated, and stored in MongoDB
5. **Session Management**: Sessions and projects are automatically created/updated based on message metadata

## Usage Notes

- Messages are immutable once created
- Parent-child relationships form conversation threads
- Tool results are always paired with their invocation
- Summaries are generated for completed conversations
- All timestamps are in ISO 8601 format with timezone
