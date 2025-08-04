# Tool Use Formatting Documentation

This document describes how ClaudeLens formats and displays tool usage in conversations. It covers all supported tools, their display formats, examples, and best practices for adding new tool formats.

## Table of Contents

1. [Overview](#overview)
2. [Tool Use Messages](#tool-use-messages)
3. [Tool Result Messages](#tool-result-messages)
4. [Adding New Tool Formats](#adding-new-tool-formats)
5. [Best Practices](#best-practices)

## Overview

ClaudeLens handles two types of tool-related messages:
- **Tool Use Messages**: When Claude calls a tool (type: `tool_use`)
- **Tool Result Messages**: When a tool returns results (type: `tool_result`)

Each tool is formatted to provide clear, concise information while maintaining readability.

## Tool Use Messages

These messages show when Claude invokes a tool with specific parameters.

### File Operations

#### Read
**Purpose**: Display file reading operations clearly
```json
{
  "name": "Read",
  "input": {
    "file_path": "/src/app.js",
    "offset": 100,
    "limit": 50
  }
}
```
**Display Format**:
```
🔧 Tool: Read
📄 Reading: /src/app.js (lines 100-150)
```
**Reasoning**: Shows the file path and line range to help users understand what portion of code Claude is examining.

#### Write
**Purpose**: Show file creation/writing operations
```json
{
  "name": "Write",
  "input": {
    "file_path": "/src/new-component.tsx",
    "content": "import React from 'react'..."
  }
}
```
**Display Format**:
```
🔧 Tool: Write
✏️ Writing to: /src/new-component.tsx
Content: 45 lines
```
**Reasoning**: Displays target file and content size without cluttering with full content.

#### Edit
**Purpose**: Show file editing operations
```json
{
  "name": "Edit",
  "input": {
    "file_path": "/src/config.js",
    "old_string": "port: 3000",
    "new_string": "port: 8080",
    "replace_all": true
  }
}
```
**Display Format**:
```
🔧 Tool: Edit
✏️ Editing: /src/config.js
(replacing all occurrences)
```
**Reasoning**: Shows file being edited and whether it's a single or global replacement.

#### MultiEdit
**Purpose**: Display multiple edits to a single file
```json
{
  "name": "MultiEdit",
  "input": {
    "file_path": "/src/utils.js",
    "edits": [
      {"old_string": "var", "new_string": "const"},
      {"old_string": "function", "new_string": "const"}
    ]
  }
}
```
**Display Format**:
```
🔧 Tool: MultiEdit
✏️ Multiple edits to: /src/utils.js
Edits: 2 changes
```
**Reasoning**: Shows the file and number of edits without listing each change.

### Directory Operations

#### LS
**Purpose**: Show directory listing operations
```json
{
  "name": "LS",
  "input": {
    "path": "/src/components",
    "ignore": ["*.test.js", "*.spec.js"]
  }
}
```
**Display Format**:
```
🔧 Tool: LS
📁 Listing: /src/components
(ignoring: *.test.js, *.spec.js)
```
**Reasoning**: Shows the directory and any filters applied.

#### Glob
**Purpose**: Display file pattern matching
```json
{
  "name": "Glob",
  "input": {
    "pattern": "**/*.tsx",
    "path": "/src"
  }
}
```
**Display Format**:
```
🔧 Tool: Glob
🔍 Pattern: **/*.tsx
In: /src
```
**Reasoning**: Shows the search pattern and scope clearly.

### Search Operations

#### Grep
**Purpose**: Show text search operations
```json
{
  "name": "Grep",
  "input": {
    "pattern": "useState",
    "path": "/src",
    "glob": "*.tsx",
    "-n": true,
    "output_mode": "files_with_matches"
  }
}
```
**Display Format**:
```
🔧 Tool: Grep
🔍 Searching for: useState
In: /src (*.tsx files)
Options: files_with_matches, line numbers
```
**Reasoning**: Shows search term, scope, and key options that affect output.

### Command Execution

#### Bash
**Purpose**: Display shell command execution
```json
{
  "name": "Bash",
  "input": {
    "command": "npm install express mongoose cors",
    "timeout": 30000,
    "description": "Install backend dependencies"
  }
}
```
**Display Format**:
```
🔧 Tool: Bash
💻 Command: npm install express mongoose cors
Description: Install backend dependencies
Timeout: 30s
```
**Reasoning**: Shows command, purpose, and timeout to set expectations.

### Web Operations

#### WebSearch
**Purpose**: Show web search queries
```json
{
  "name": "WebSearch",
  "input": {
    "query": "React 18 concurrent features",
    "allowed_domains": ["reactjs.org", "developer.mozilla.org"]
  }
}
```
**Display Format**:
```
🔧 Tool: WebSearch
🌐 Searching web for: "React 18 concurrent features"
Allowed domains: reactjs.org, developer.mozilla.org
```
**Reasoning**: Shows search query and any domain restrictions.

#### WebFetch
**Purpose**: Display web content fetching
```json
{
  "name": "WebFetch",
  "input": {
    "url": "https://api.github.com/repos/facebook/react",
    "prompt": "Extract the current star count and latest release version"
  }
}
```
**Display Format**:
```
🔧 Tool: WebFetch
🌐 Fetching: https://api.github.com/repos/facebook/react
Purpose: Extract the current star count and latest release ver...
```
**Reasoning**: Shows URL and intent, truncating long prompts.

### Task Management

#### TodoWrite
**Purpose**: Display todo list management with actual tasks
```json
{
  "name": "TodoWrite",
  "input": {
    "todos": [
      {"id": "1", "content": "Implement user authentication", "status": "in_progress", "priority": "high"},
      {"id": "2", "content": "Add unit tests for auth module", "status": "pending", "priority": "medium"},
      {"id": "3", "content": "Update documentation", "status": "completed", "priority": "low"}
    ]
  }
}
```
**Display Format**:
```
🔧 Tool: TodoWrite
📝 Todo list: 3 items
  ⏳ Pending: 1 | 🔄 In Progress: 1 | ✅ Completed: 1

  Tasks:
  1. 🔄 🔴 Implement user authentication
  2. ⏳ 🟡 Add unit tests for auth module
  3. ✅ 🟢 Update documentation
```
**Reasoning**: Shows task counts, statuses, priorities, and actual content to give users full visibility into Claude's task tracking.

#### Task
**Purpose**: Show autonomous agent task delegation
```json
{
  "name": "Task",
  "input": {
    "description": "Research React performance optimization techniques",
    "subagent_type": "general-purpose",
    "prompt": "Find and summarize the top 5 React performance optimization techniques..."
  }
}
```
**Display Format**:
```
🔧 Tool: Task
🤖 Agent task: Research React performance optimization techniques (general-purpose)
```
**Reasoning**: Shows task description and agent type for transparency.

### Planning

#### ExitPlanMode / exit_plan_mode
**Purpose**: Show plan mode completion
```json
{
  "name": "ExitPlanMode",
  "input": {
    "plan": "1. Set up project structure\n2. Install dependencies\n3. Create base components\n4. Implement routing"
  }
}
```
**Display Format**:
```
🔧 Tool: ExitPlanMode
📋 Exiting plan mode (4 line plan)
```
**Reasoning**: Shows plan completion with line count indicator.

### Notebook Operations

#### NotebookRead
**Purpose**: Display Jupyter notebook reading
```json
{
  "name": "NotebookRead",
  "input": {
    "notebook_path": "/analysis/data-exploration.ipynb",
    "cell_id": "cell-5"
  }
}
```
**Display Format**:
```
🔧 Tool: NotebookRead
📓 Reading notebook: /analysis/data-exploration.ipynb
Cell: cell-5
```
**Reasoning**: Shows notebook path and specific cell if targeted.

#### NotebookEdit
**Purpose**: Show notebook editing operations
```json
{
  "name": "NotebookEdit",
  "input": {
    "notebook_path": "/analysis/model-training.ipynb",
    "edit_mode": "insert",
    "cell_type": "code"
  }
}
```
**Display Format**:
```
🔧 Tool: NotebookEdit
📓 Editing notebook: /analysis/model-training.ipynb
Mode: insert (code cell)
```
**Reasoning**: Shows notebook, edit mode, and cell type.

## Tool Result Messages

Tool results are formatted to provide quick understanding of outcomes while preserving important details.

### File Operation Results

#### Read Results
**Pattern**: Content starting with line numbers (e.g., "1→", "  10→")
```
     1→import React from 'react';
     2→import { useState } from 'react';
     3→
     4→export function Counter() {
     5→  const [count, setCount] = useState(0);
```
**Display Format**:
```
📄 File contents:
     1→import React from 'react';
     2→import { useState } from 'react';
     3→
     4→export function Counter() {
     5→  const [count, setCount] = useState(0);
...
```
**Reasoning**: Shows first 5 lines with line numbers preserved for context.

#### Write/Edit Results
**Pattern**: "File created successfully", "has been updated", "File written successfully"
```
File created successfully at: /src/components/NewComponent.tsx
```
**Display Format**:
```
✅ File operation completed
```
**Reasoning**: Simple success confirmation without redundant details.

### Search Results

#### Grep/Glob Results
**Pattern**: "Found X files", "Found X matches"
```
Found 15 files
/src/App.tsx
/src/components/Header.tsx
/src/components/Footer.tsx
...
```
**Display Format**:
```
🔍 Search results:
Found 15 files
/src/App.tsx
/src/components/Header.tsx
/src/components/Footer.tsx
... and 12 more
```
**Reasoning**: Shows first 10 results with count of remaining to avoid overwhelming display.

#### No Results
**Pattern**: "No matches found", "No files found"
```
No matches found
```
**Display Format**:
```
❌ No matches found
```
**Reasoning**: Clear negative result indicator.

### Directory Listing Results

**Pattern**: Unix-style directory listing with "total" and permission strings
```
total 24
drwxr-xr-x  6 user  staff   192 Mar 15 10:30 .
drwxr-xr-x  8 user  staff   256 Mar 15 09:45 ..
-rw-r--r--  1 user  staff  1234 Mar 15 10:30 index.js
```
**Display Format**:
```
📁 Directory listing: 3 items
```
**Reasoning**: Shows item count instead of full listing for brevity.

### Command Execution Results

#### Package Installation
**Pattern**: "npm install", "poetry install", "pip install", "Successfully installed"
```
added 152 packages, and audited 153 packages in 12s
```
**Display Format**:
```
📦 Dependencies installed successfully
```

#### Git Operations
**Pattern**: Git commands with "commit", "branch"
```
[main 5a3f2d1] Add user authentication feature
 3 files changed, 150 insertions(+), 10 deletions(-)
```
**Display Format**:
```
🔧 Git operation completed
```

#### Docker Operations
**Pattern**: "docker" with "built", "Started", container status output
```
Successfully built 4b3f5a2d1c8e
Successfully tagged myapp:latest
```
**Display Format**:
```
🐳 Docker operation completed
```

### Error Handling

**Pattern**: "Error", "error", "ERROR" in content
```
Error: Cannot find module 'express'
    at Function.Module._resolveFilename (internal/modules/cjs/loader.js:880:15)
```
**Display Format**:
```
❌ Error: Cannot find module 'express'
```
**Reasoning**: Shows first line of error for quick identification.

### Todo Results

**Pattern**: "Todos have been modified successfully"
```
Todos have been modified successfully. Ensure that you continue to use the todo list to track your progress.
```
**Display Format**:
```
✅ Todo list updated successfully
```
**Reasoning**: Simple confirmation that todo operations succeeded.

### Generic Patterns

#### Success Messages
**Pattern**: "Successfully", "successfully", "Success"
```
Successfully compiled 15 TypeScript files
```
**Display Format**:
```
✅ Successfully compiled 15 TypeScript files
```

#### Long Results
**Pattern**: Results longer than 200 characters
```
[Very long output with multiple lines...]
```
**Display Format**:
```
📥 Tool Result (47 lines):
[First 200 characters]...
```
**Reasoning**: Shows line count and preview for large outputs.

## Adding New Tool Formats

### Step 1: Identify the Tool Pattern

1. Check tool usage data to find the tool name
2. Examine sample inputs and outputs
3. Identify unique patterns in results

### Step 2: Add Tool Use Formatting

Add a new case in the `formatMessageContent` function for tool_use messages:

```typescript
case 'YourNewTool':
  if (parsed.input?.important_param) {
    toolInfo += `\n🎯 Your description: ${parsed.input.important_param}`;
    // Add more formatting as needed
  }
  break;
```

### Step 3: Add Tool Result Formatting

Add pattern matching in the tool_result section:

```typescript
else if (content.includes('your-pattern')) {
  return '🎯 Your formatted result';
}
```

### Step 4: Choose Appropriate Icons

Use consistent emoji indicators:
- 📄 File/document operations
- 📁 Directory operations
- 🔍 Search operations
- 💻 Command execution
- 🌐 Web operations
- 📦 Package management
- 🔧 Configuration/Git
- 🐳 Container operations
- ✅ Success states
- ❌ Error states
- ⚠️ Warnings
- 📝 Task management
- 🤖 AI/Agent operations
- 📓 Notebook operations
- 📋 Planning operations

## Best Practices

### 1. Prioritize Readability
- Show essential information first
- Truncate long content with indicators
- Use visual hierarchy (indentation, spacing)

### 2. Maintain Consistency
- Use similar patterns for similar operations
- Keep icon usage consistent across tools
- Follow established truncation limits

### 3. Preserve Important Context
- Show file paths completely when possible
- Include line numbers for code references
- Display counts for collections

### 4. Handle Edge Cases
- Check for null/undefined values
- Handle empty arrays gracefully
- Provide fallbacks for missing data

### 5. Performance Considerations
- Limit displayed items (e.g., first 10 todos)
- Truncate long strings appropriately
- Avoid complex computations in formatters

### 6. User Experience
- Make tool purpose immediately clear
- Show progress/status indicators
- Highlight errors and warnings
- Group related information

### 7. Testing New Formats
1. Test with real conversation data
2. Verify all fields are handled
3. Check edge cases (empty, null, very long)
4. Ensure TypeScript types are satisfied
5. Test visual appearance in all view modes

### 8. Documentation
- Document the reasoning for format choices
- Provide examples of input/output
- Explain any truncation or summarization logic
- Update this document when adding new tools

## Maintenance

When Claude's tools are updated:
1. Monitor for new tool names in conversation data
2. Check for changed input/output formats
3. Update formatters to handle new patterns
4. Test with real conversation exports
5. Update this documentation

Remember: The goal is to make Claude's tool usage transparent and easy to follow, helping users understand what operations were performed without overwhelming them with details.
