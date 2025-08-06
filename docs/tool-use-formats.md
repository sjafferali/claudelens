# Tool Use Formatting Documentation

This document describes how ClaudeLens formats and displays tool usage in conversations. It covers the component architecture, all supported tools, their display formats, examples, and best practices for adding new tool formats.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tool Use Messages](#tool-use-messages)
4. [Tool Result Messages](#tool-result-messages)
5. [Component Implementation](#component-implementation)
6. [Adding New Tool Formats](#adding-new-tool-formats)
7. [Best Practices](#best-practices)

## Overview

ClaudeLens uses a component-based architecture to display tool usage in conversations. The system handles two types of tool-related messages:

- **Tool Use Messages**: When Claude calls a tool (type: `tool_use`)
- **Tool Result Messages**: When a tool returns results (type: `tool_result`)

Each tool is formatted using specialized components that provide:
- Clear, human-readable formatting
- Tool-specific visual treatments
- Collapsed/expanded states with meaningful previews
- Consistent color coding and iconography

## Architecture

The tool display system consists of three main components:

### 1. ToolDisplay Component (`/components/ToolDisplay.tsx`)
Handles the display of tool invocations with:
- Tool-specific formatters for each tool type
- Color-coded categories (file operations, search, commands, web, tasks, notebooks)
- Consistent iconography
- Collapsed and expanded view states

### 2. ToolResultDisplay Component (`/components/ToolResultDisplay.tsx`)
Handles the display of tool results with:
- Intelligent result type detection
- Specialized formatting for different result patterns
- Syntax highlighting for code
- Collapsible views for long output

### 3. SessionDetail Integration
Combines tool use and result messages into paired displays:
- Groups consecutive tool_use and tool_result messages
- Provides unified expand/collapse controls
- Maintains cost and timing information

## Tool Message Extraction and Storage

### How Tool Messages Are Created

When Claude uses a tool, the original assistant message contains a `tool_use` content block. During the ingest process, ClaudeLens:

1. **Identifies tool_use blocks** in assistant message content arrays
2. **Extracts each tool operation** as a separate message
3. **Creates tool_result messages** for the responses
4. **Sets parent relationships** to maintain hierarchy

### Extraction Pattern

**Original Assistant Message:**
```json
{
  "type": "assistant",
  "uuid": "assistant-msg-123",
  "message": {
    "content": [
      {
        "type": "tool_use",
        "id": "tool-call-001",
        "name": "Read",
        "input": {"file_path": "/path/to/file.txt"}
      }
    ]
  }
}
```

**Extracted Messages:**
```json
// 1. Modified assistant message
{
  "type": "assistant",
  "uuid": "assistant-msg-123",
  "content": "📄 Reading file: /path/to/file.txt"
}

// 2. Extracted tool_use message
{
  "type": "tool_use",
  "uuid": "assistant-msg-123_tool_0",
  "parentUuid": "assistant-msg-123",
  "content": "{\"type\":\"tool_use\",\"name\":\"Read\",\"input\":{...}}",
  "isSidechain": true
}

// 3. Extracted tool_result message
{
  "type": "tool_result",
  "uuid": "assistant-msg-123_result_0",
  "parentUuid": "assistant-msg-123_tool_0",
  "content": "File contents here...",
  "isSidechain": true
}
```

## Tool Use Messages

Tool use messages are displayed using the `ToolDisplay` component, which provides specialized formatting for each tool type. The component uses color-coded categories and tool-specific icons to enhance readability.

### Tool Categories

Tools are organized into six categories, each with distinct visual treatment:

| Category | Color Theme | Tools | Icon Type |
|----------|------------|-------|-----------|
| File Operations | Blue | Read, Write, Edit, MultiEdit | 📄 FileText, ✏️ Edit |
| Search Operations | Purple | LS, Glob, Grep | 🔍 Search, 📁 Folder |
| Command Execution | Gray | Bash | 💻 Terminal |
| Web Operations | Green | WebSearch, WebFetch | 🌐 Globe |
| Task Management | Amber | TodoWrite, Task, ExitPlanMode | ✅ CheckSquare, 🤖 Bot |
| Notebook Operations | Indigo | NotebookRead, NotebookEdit | 📓 BookOpen |

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
**Collapsed Display**:
```
Reading: /src/app.js (lines 100-150)
```

**Expanded Display**:
```
File: /src/app.js
Range: Lines 100 to 150
```

**Implementation**: The component shows file path and optional line range. In collapsed state, it provides a one-line summary. In expanded state, it shows structured parameter details.

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
**Collapsed Display**:
```
Writing to: /src/new-component.tsx (45 lines)
```

**Expanded Display**:
```
File: /src/new-component.tsx
Content: 45 lines
[First 5 lines of content preview if ≤ 5 lines total]
```

**Implementation**: Shows target file and line count. Expanded view includes content preview for small files.

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
**Collapsed Display**:
```
Editing: /src/config.js
```

**Expanded Display**:
```
File: /src/config.js
⚠️ Replacing all occurrences
```

**Implementation**: Shows file path, with warning indicator for global replacements.

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
**Collapsed Display**:
```
Editing: /src/utils.js (2 changes)
```

**Expanded Display**:
```
File: /src/utils.js
Changes: 2 edits
```

**Implementation**: Shows file and edit count. The component handles both single and multiple edits.

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
**Collapsed Display**:
```
Listing: /src/components
```

**Expanded Display**:
```
Directory: /src/components
Ignoring: *.test.js, *.spec.js
```

**Implementation**: Shows directory path, with ignored patterns listed in expanded view.

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
**Collapsed Display**:
```
Pattern: **/*.tsx in /src
```

**Expanded Display**:
```
Pattern: **/*.tsx
In: /src
```

**Implementation**: Combines pattern and path in collapsed view for compact display.

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
**Collapsed Display**:
```
Searching for: "useState" in /src
```

**Expanded Display**:
```
Pattern: useState
Location: /src
File pattern: *.tsx
File type: tsx
```

**Implementation**: Shows search pattern and location. Expanded view includes all search parameters.

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
**Collapsed Display**:
```
Install backend dependencies
```
(or command preview if no description)

**Expanded Display**:
```
Description: Install backend dependencies
$ npm install express mongoose cors
Timeout: 30000ms
```

**Implementation**: Prioritizes description in collapsed view. Shows full command with terminal prompt in expanded view.

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
**Collapsed Display**:
```
Searching: "React 18 concurrent features"
```

**Expanded Display**:
```
Query: "React 18 concurrent features"
Domains: reactjs.org, developer.mozilla.org
```

**Implementation**: Shows query in collapsed view, domain restrictions in expanded view.

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
**Collapsed Display**:
```
Fetching: https://api.github.com/repos/facebook/react
```

**Expanded Display**:
```
URL: https://api.github.com/repos/facebook/react
Purpose: Extract the current star count and latest release version
```

**Implementation**: URL is clickable link in expanded view. Full prompt shown without truncation.

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
**Collapsed Display**:
```
3 tasks: 1 pending, 1 in progress, 1 completed
```

**Expanded Display**:
```
⏳ Pending: 1 | 🔄 In Progress: 1 | ✅ Completed: 1

Tasks:
1. 🔄 🔴 Implement user authentication
2. ⏳ 🟡 Add unit tests for auth module
3. ✅ 🟢 Update documentation
[...and X more tasks]
```

**Implementation**: Collapsed view shows summary counts. Expanded view shows up to 10 tasks with status/priority indicators. Status icons: ⏳ pending, 🔄 in_progress, ✅ completed. Priority colors: 🔴 high, 🟡 medium, 🟢 low.

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
**Collapsed Display**:
```
Agent task: Research React performance optimization techniques
```

**Expanded Display**:
```
Description: Research React performance optimization techniques
Agent type: general-purpose
```

**Implementation**: Shows task description in both views, agent type only in expanded.

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
**Collapsed Display**:
```
Exiting plan mode
```

**Expanded Display**:
```
Exiting plan mode (4 line plan)
```

**Implementation**: Simple collapsed view, line count shown in expanded view.

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
**Collapsed Display**:
```
Reading notebook: /analysis/data-exploration.ipynb
```

**Expanded Display**:
```
Notebook: /analysis/data-exploration.ipynb
Cell: cell-5
```

**Implementation**: Shows notebook path, cell ID only in expanded view.

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
**Collapsed Display**:
```
Editing notebook: /analysis/model-training.ipynb
```

**Expanded Display**:
```
Notebook: /analysis/model-training.ipynb
Mode: insert - code cell
```

**Implementation**: Shows notebook path, edit details only in expanded view.

## Tool Result Messages

Tool results are displayed using the `ToolResultDisplay` component, which automatically detects result types and applies appropriate formatting. The component uses pattern matching to identify result types and provides specialized displays for each.

### Result Type Detection

The component detects the following result types:
- `todo_success`: TodoWrite confirmations
- `file_contents`: File contents with line numbers
- `file_operation`: File creation/update confirmations
- `search_results`: Grep/Glob search results
- `no_results`: Empty search results
- `directory_listing`: LS command output
- `package_install`: npm/pip/poetry installations
- `git_operation`: Git command results
- `docker_operation`: Docker command results
- `error`: Error messages
- `success`: Generic success messages
- `web_content`: HTML content
- `notebook_operation`: Notebook operations
- `long_output`: Results > 500 chars or > 20 lines
- `generic`: Fallback for unrecognized patterns

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
**Collapsed Display**:
```
[📄 File Contents icon] File Contents
5 lines shown of X total
```

**Expanded Display**:
```
[📄 File Contents header with line count]
     1→import React from 'react';
     2→import { useState } from 'react';
     3→
     4→export function Counter() {
     5→  const [count, setCount] = useState(0);
[Shows up to 50 lines in expanded view]
... X more lines
```

**Implementation**: Preserves line numbers, shows 5 lines collapsed, 50 expanded.

#### Write/Edit Results
**Pattern**: "File created successfully", "has been updated", "File written successfully"
```
File created successfully at: /src/components/NewComponent.tsx
```
**Display Format**:
```
[✅ CheckCircle icon] File operation completed
/src/components/NewComponent.tsx (if path detected)
```

**Implementation**: Green success indicator with optional file path extraction.

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
**Collapsed Display**:
```
[🔍 Search icon] Search Results: 15 files
```

**Expanded Display**:
```
[🔍 Search header] Search Results: 15 files
/src/App.tsx
/src/components/Header.tsx
/src/components/Footer.tsx
[Shows up to 20 results]
... and 12 more
```

**Implementation**: Purple-themed search results, shows 5 items collapsed, 20 expanded.

#### No Results
**Pattern**: "No matches found", "No files found"
```
No matches found
```
**Display Format**:
```
[⚠️ AlertCircle icon] No matches found
```

**Implementation**: Gray alert indicator for empty results.

### Directory Listing Results

**Pattern**: Unix-style directory listing with "total" and permission strings
```
total 24
drwxr-xr-x  6 user  staff   192 Mar 15 10:30 .
drwxr-xr-x  8 user  staff   256 Mar 15 09:45 ..
-rw-r--r--  1 user  staff  1234 Mar 15 10:30 index.js
```
**Collapsed Display**:
```
[📁 FolderOpen icon] Directory listing: 3 items
```

**Expanded Display**:
```
[📁 Directory header] 3 items
[First 10 items with permissions]
... X more items
```

**Implementation**: Blue-themed directory display, shows item count and preview.

### Command Execution Results

#### Package Installation
**Pattern**: "npm install", "poetry install", "pip install", "Successfully installed"
```
added 152 packages, and audited 153 packages in 12s
```
**Display Format**:
```
[📦 Package icon] Dependencies installed successfully
(152 packages) if count detected
```

**Implementation**: Green success with package count extraction.

#### Git Operations
**Pattern**: Git commands with "commit", "branch"
```
[main 5a3f2d1] Add user authentication feature
 3 files changed, 150 insertions(+), 10 deletions(-)
```
**Display Format**:
```
[GitBranch icon] Git operation completed
[main 5a3f2d1] Add user authentication feature
```

**Implementation**: Blue-themed with first line of git output.

#### Docker Operations
**Pattern**: "docker" with "built", "Started", container status output
```
Successfully built 4b3f5a2d1c8e
Successfully tagged myapp:latest
```
**Display Format**:
```
[🐳 Container icon] Docker operation completed
Successfully built 4b3f5a2d1c8e
```

**Implementation**: Blue-themed with operation details.

### Error Handling

**Pattern**: "Error", "error", "ERROR" in content
```
Error: Cannot find module 'express'
    at Function.Module._resolveFilename (internal/modules/cjs/loader.js:880:15)
```
**Collapsed Display**:
```
[❌ XCircle icon] Error: Cannot find module 'express'
```

**Expanded Display**:
```
[❌ Error header]
Error: Cannot find module 'express'
    at Function.Module._resolveFilename (internal/modules/cjs/loader.js:880:15)
[Full stack trace]
```

**Implementation**: Red error theme with expandable stack trace.

### Todo Results

**Pattern**: "Todos have been modified successfully"
```
Todos have been modified successfully. Ensure that you continue to use the todo list to track your progress.
```
**Display Format**:
```
[✅ CheckCircle icon] Todo list updated successfully
```

**Implementation**: Green success indicator for todo operations.

### Generic Patterns

#### Success Messages
**Pattern**: "Successfully", "successfully", "Success"
```
Successfully compiled 15 TypeScript files
```
**Display Format**:
```
[✅ CheckCircle icon] Successfully compiled 15 TypeScript files
```

**Implementation**: Extracts and preserves success message details.

#### Long Results
**Pattern**: Results longer than 200 characters
```
[Very long output with multiple lines...]
```
**Collapsed Display**:
```
[📄 FileText icon] Output
47 lines
```

**Expanded Display**:
```
[Output header with line count]
[First 1000 characters]
... X more characters
```

**Implementation**: Shows 200 chars collapsed, 1000 expanded.

## Component Implementation

### ToolDisplay Component Structure

```typescript
// Tool categories with visual themes
const toolCategories = {
  file: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700' },
  search: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700' },
  command: { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-700' },
  web: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700' },
  task: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700' },
  notebook: { bg: 'bg-indigo-50', border: 'border-indigo-200', text: 'text-indigo-700' }
};

// Tool-specific formatters
function TodoWriteDisplay({ input, isCollapsed }) {
  // Shows task statistics and individual tasks
}

function ReadDisplay({ input, isCollapsed }) {
  // Shows file path and line range
}

// ... other tool-specific displays
```

### ToolResultDisplay Component Structure

```typescript
// Result type detection
function detectResultType(content: string): ResultType {
  if (content.includes('Todos have been modified successfully')) {
    return 'todo_success';
  }
  if (/^\s*\d+[→|->]/.test(content)) {
    return 'file_contents';
  }
  // ... other patterns
}

// Result-specific renderers
function FileContentsResult({ content, isCollapsed }) {
  // Syntax-highlighted code display
}

function SearchResultsDisplay({ content, isCollapsed }) {
  // Formatted search results with counts
}

// ... other result displays
```

### Integration in SessionDetail

```typescript
// Parse tool information
let toolName = 'Unknown Tool';
let toolInput = {};
try {
  const parsed = JSON.parse(toolUseMessage.content);
  toolName = parsed.name || 'Unknown Tool';
  toolInput = parsed.input || {};
} catch {
  // Fallback to raw content
}

// Render tool pair
<div className="space-y-2">
  <ToolDisplay
    toolName={toolName}
    toolInput={toolInput}
    isCollapsed={!isPairExpanded}
  />
  <ToolResultDisplay
    content={toolResultMessage.content}
    toolName={toolName}
    isCollapsed={!isPairExpanded}
  />
</div>
```

## Adding New Tool Formats

### Step 1: Identify the Tool

1. Check tool usage data to find the tool name
2. Examine sample inputs and outputs
3. Identify unique patterns in results
4. Determine appropriate category (file/search/command/web/task/notebook)

### Step 2: Add Tool Display

1. Add the tool to the category mapping in `getToolCategory()`
2. Add an icon mapping in `toolIcons`
3. Create a tool-specific display component:

```typescript
function YourToolDisplay({ input, isCollapsed }: { input: any; isCollapsed: boolean }) {
  if (isCollapsed) {
    return <div className="text-sm text-gray-600">
      {/* Concise one-line summary */}
    </div>;
  }

  return (
    <div className="space-y-2 text-sm">
      {/* Detailed parameter display */}
    </div>
  );
}
```

4. Add case in `renderToolContent()`:

```typescript
case 'YourTool':
  return <YourToolDisplay input={toolInput} isCollapsed={isCollapsed} />;
```

### Step 3: Add Result Display

1. Add pattern detection in `detectResultType()`:

```typescript
if (content.includes('your-pattern')) {
  return 'your_result_type';
}
```

2. Create result display component:

```typescript
function YourResultDisplay({ content, isCollapsed }) {
  // Format and display the result
}
```

3. Add case in `renderResult()`:

```typescript
case 'your_result_type':
  return <YourResultDisplay content={content} isCollapsed={isCollapsed} />;
```

### Step 4: Choose Visual Elements

Choose appropriate icons from lucide-react:
- `FileText`, `Edit`, `FileCode` - File operations
- `Folder`, `FolderOpen` - Directory operations
- `Search` - Search operations
- `Terminal` - Command execution
- `Globe` - Web operations
- `Package` - Package management
- `GitBranch` - Git operations
- `Container` - Docker operations
- `CheckCircle` - Success states
- `XCircle` - Error states
- `AlertCircle` - Warnings
- `CheckSquare` - Task management
- `Bot` - AI/Agent operations
- `BookOpen` - Notebook operations
- `ClipboardList` - Planning operations

## Best Practices

### 1. Component Design Principles

#### Collapsed vs Expanded States
- **Collapsed**: One-line summary with key information
- **Expanded**: Full parameter details with structured layout
- Use consistent spacing and typography

#### Color Coding
- Each tool category has a distinct color theme
- Use lighter backgrounds with darker borders
- Ensure sufficient contrast for accessibility

#### Progressive Disclosure
- Show most important info in collapsed state
- Hide verbose details until expanded
- Limit list displays (10 todos, 20 search results)

### 2. Result Display Guidelines

#### Pattern Detection
- Test patterns with real data
- Order patterns from most specific to most generic
- Include fallback for unrecognized formats

#### Content Formatting
- Preserve line numbers for code
- Show item counts for collections
- Extract key information (file paths, error messages)

#### Visual Indicators
- Use icons to reinforce result type
- Color-code success/error/warning states
- Include metadata (line counts, file sizes)

### 3. Implementation Best Practices

#### Type Safety
```typescript
interface ToolDisplayProps {
  toolName: string;
  toolInput: any; // Consider specific types per tool
  isCollapsed?: boolean;
}
```

#### Error Handling
```typescript
try {
  const parsed = JSON.parse(toolUseMessage.content);
  // Handle parsed data
} catch {
  // Graceful fallback
}
```

#### Performance
- Limit rendered items in lists
- Use React.memo for expensive components
- Lazy load syntax highlighting

### 4. Accessibility Considerations

- Ensure color is not the only differentiator
- Provide text alternatives for icons
- Support keyboard navigation
- Test with screen readers

### 5. Testing Checklist

1. **Visual Testing**
   - All view states (collapsed/expanded)
   - Light and dark themes
   - Different screen sizes

2. **Data Testing**
   - Empty states
   - Very long content
   - Special characters
   - Unicode content

3. **Integration Testing**
   - Tool pairs display correctly
   - Costs and timestamps preserved
   - Expand/collapse interactions

### 6. Documentation Standards

When documenting new tools:
- Provide real JSON examples
- Show both collapsed and expanded displays
- Explain design decisions
- Include edge cases

## Maintenance

When Claude's tools are updated:
1. Monitor for new tool names in conversation data
2. Check for changed input/output formats
3. Update formatters to handle new patterns
4. Test with real conversation exports
5. Update this documentation

### Component Architecture Summary

The new component-based architecture provides:

1. **Separation of Concerns**: Tool display logic is separated from result display logic
2. **Reusability**: Components can be used in different contexts
3. **Maintainability**: Adding new tools requires minimal changes
4. **Consistency**: All tools follow the same visual patterns
5. **Performance**: Collapsed states reduce initial render cost
6. **Accessibility**: Semantic HTML and ARIA labels throughout

Remember: The goal is to make Claude's tool usage transparent and easy to follow, helping users understand what operations were performed without overwhelming them with details. The component architecture ensures consistency while allowing flexibility for tool-specific formatting needs.

## Tool Extraction Patterns

### Complete Tool Input Specifications

This section documents the exact input format for each tool as they appear in Claude's messages and how they are extracted during the ingest process.

#### File Operations

**Read Tool:**
- **Input Format:**
  ```json
  {
    "name": "Read",
    "input": {
      "file_path": "/path/to/file.txt",
      "offset": 0,      // Optional: line to start from
      "limit": 100      // Optional: number of lines
    }
  }
  ```
- **Extraction**: Creates tool_use message with UUID pattern `{assistant_uuid}_tool_{index}`
- **Display Summary**: "📄 Reading file: {file_path}"

**Write Tool:**
- **Input Format:**
  ```json
  {
    "name": "Write",
    "input": {
      "file_path": "/path/to/file.txt",
      "content": "File content..."
    }
  }
  ```
- **Extraction**: Creates tool_use message with full content preserved
- **Display Summary**: "✏️ Writing to file: {file_path}"

**Edit Tool:**
- **Input Format:**
  ```json
  {
    "name": "Edit",
    "input": {
      "file_path": "/path/to/file.txt",
      "old_string": "original",
      "new_string": "replacement",
      "replace_all": false
    }
  }
  ```
- **Extraction**: Preserves edit details for undo/redo capability
- **Display Summary**: "✏️ Editing file: {file_path}"

#### Search Operations

**Grep Tool:**
- **Input Format:**
  ```json
  {
    "name": "Grep",
    "input": {
      "pattern": "TODO|FIXME",
      "path": "/src",
      "glob": "*.js",
      "output_mode": "content",
      "-i": true,
      "-n": true
    }
  }
  ```
- **Extraction**: Maintains all grep flags and options
- **Display Summary**: "🔍 Searching for: {pattern}"

**Bash Tool:**
- **Input Format:**
  ```json
  {
    "name": "Bash",
    "input": {
      "command": "npm test",
      "description": "Run tests",
      "timeout": 30000
    }
  }
  ```
- **Extraction**: Preserves command and timeout settings
- **Display Summary**: "💻 Running command: {command}"

### Parent-Child Relationships

When extracting tool messages, the following parent-child relationships are established:

1. **Assistant → Tool Use**: Tool use messages become children of the assistant message containing them
2. **Tool Use → Tool Result**: Tool result messages become children of their corresponding tool use
3. **UUID Pattern**:
   - Assistant: `original-uuid`
   - Tool Use: `original-uuid_tool_0`, `original-uuid_tool_1`, etc.
   - Tool Result: `original-uuid_result_0`, `original-uuid_result_1`, etc.

### Sidechain Marking

All extracted tool messages are marked with `"isSidechain": true` to:
- Group them in the sidechain panel
- Keep the main conversation flow clean
- Allow filtering of auxiliary operations
