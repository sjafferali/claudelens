# Import/Export Data Format Specifications

## Overview
This document defines the data formats supported by ClaudeLens for importing and exporting conversation data. These specifications ensure data portability and compatibility across different versions and instances of the application.

## Supported Formats

### 1. JSON Format (Recommended)
**File Extension:** `.json`
**MIME Type:** `application/json`
**Use Case:** Complete data export with full metadata preservation

#### Structure
```json
{
  "version": "1.0.0",
  "export_date": "2024-01-31T14:23:00Z",
  "metadata": {
    "total_conversations": 156,
    "total_messages": 3842,
    "total_cost_usd": 45.67,
    "date_range": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-31T23:59:59Z"
    }
  },
  "conversations": [
    {
      "id": "conv_abc123def456",
      "external_id": "chat-123456",
      "title": "React Component Optimization",
      "summary": "Discussion about optimizing React components using memo, useMemo, and useCallback hooks",
      "project_id": "proj_789xyz",
      "project_name": "Personal Website",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T12:45:00Z",
      "duration_seconds": 8100,
      "model": "claude-3-opus",
      "cost_usd": 2.45,
      "message_count": 42,
      "tags": ["react", "optimization", "performance"],
      "metadata": {
        "browser": "Chrome",
        "platform": "Web",
        "user_agent": "Mozilla/5.0...",
        "custom_fields": {}
      },
      "messages": [
        {
          "id": "msg_001",
          "type": "user",
          "content": "How can I optimize my React component that's re-rendering too often?",
          "timestamp": "2024-01-15T10:30:00Z",
          "tokens": {
            "input": 15,
            "output": 0
          },
          "cost_usd": 0.0003
        },
        {
          "id": "msg_002",
          "type": "assistant",
          "content": "There are several ways to optimize React components...",
          "timestamp": "2024-01-15T10:30:15Z",
          "tokens": {
            "input": 15,
            "output": 450
          },
          "cost_usd": 0.0135,
          "model": "claude-3-opus"
        },
        {
          "id": "msg_003",
          "type": "tool_use",
          "tool_name": "code_interpreter",
          "tool_input": {
            "code": "const MemoizedComponent = React.memo(MyComponent);"
          },
          "timestamp": "2024-01-15T10:31:00Z"
        },
        {
          "id": "msg_004",
          "type": "tool_result",
          "tool_name": "code_interpreter",
          "content": "Code executed successfully",
          "timestamp": "2024-01-15T10:31:02Z"
        }
      ],
      "branches": [],
      "parent_conversation_id": null
    }
  ]
}
```

### 2. CSV Format
**File Extension:** `.csv`
**MIME Type:** `text/csv`
**Use Case:** Spreadsheet analysis, basic data export

#### Structure
```csv
conversation_id,title,project_name,model,message_count,cost_usd,created_at,summary
conv_abc123,React Component Optimization,Personal Website,claude-3-opus,42,2.45,2024-01-15T10:30:00Z,"Discussion about optimizing React components"
conv_def456,API Design Discussion,Mobile App,claude-3-sonnet,28,1.89,2024-01-14T09:15:00Z,"RESTful API design patterns and best practices"
```

#### Messages CSV (separate file)
```csv
conversation_id,message_id,type,role,content,timestamp,tokens_input,tokens_output,cost_usd
conv_abc123,msg_001,user,user,"How can I optimize my React component?",2024-01-15T10:30:00Z,15,0,0.0003
conv_abc123,msg_002,assistant,assistant,"There are several ways to optimize...",2024-01-15T10:30:15Z,15,450,0.0135
```

### 3. Markdown Format
**File Extension:** `.md`
**MIME Type:** `text/markdown`
**Use Case:** Human-readable export, documentation, sharing

#### Structure
```markdown
# ClaudeLens Export - 2024-01-31

## Metadata
- **Total Conversations:** 156
- **Total Messages:** 3,842
- **Total Cost:** $45.67
- **Date Range:** 2024-01-01 to 2024-01-31

---

## Conversations

### 1. React Component Optimization
- **ID:** conv_abc123def456
- **Project:** Personal Website
- **Model:** claude-3-opus
- **Date:** 2024-01-15
- **Messages:** 42
- **Cost:** $2.45
- **Tags:** react, optimization, performance

#### Summary
Discussion about optimizing React components using memo, useMemo, and useCallback hooks

#### Messages

**User** (10:30:00):
> How can I optimize my React component that's re-rendering too often?

**Assistant** (10:30:15):
> There are several ways to optimize React components...
>
> 1. Use React.memo for functional components
> 2. Implement useMemo for expensive calculations
> 3. Use useCallback for function props

**Tool Use** (10:31:00):
```javascript
const MemoizedComponent = React.memo(MyComponent);
```

---
```

### 4. PDF Format (Export Only)
**File Extension:** `.pdf`
**MIME Type:** `application/pdf`
**Use Case:** Print-ready documents, archival, sharing with non-technical users

#### Features
- Formatted conversation layout
- Syntax highlighting for code blocks
- Table of contents for navigation
- Page numbers and headers
- Embedded metadata

## Import Specifications

### Field Mapping Rules

#### Required Fields
- `conversation_id` or `id` - Unique identifier
- `messages` - Array of message objects
- `created_at` or `timestamp` - Creation timestamp

#### Optional Fields
- `title` - Conversation title (auto-generated if missing)
- `summary` - Brief description
- `project_id` - Associated project
- `model` - AI model used
- `cost_usd` - Total cost
- `tags` - Array of tags
- `metadata` - Additional custom data

### Validation Rules

1. **ID Validation**
   - Must be unique within the import
   - Can be any string format
   - Will be mapped to internal UUID if needed

2. **Timestamp Validation**
   - ISO 8601 format preferred
   - Unix timestamps accepted
   - Relative dates parsed (e.g., "2 days ago")

3. **Message Type Validation**
   - Accepted types: `user`, `assistant`, `system`, `tool_use`, `tool_result`
   - Unknown types mapped to `system`

4. **Cost Validation**
   - Numeric values only
   - Negative values rejected
   - Missing costs calculated from token counts if available

### Conflict Resolution Strategies

#### 1. Skip Strategy
- Ignores duplicate conversations
- Preserves existing data
- Logs skipped items

#### 2. Replace Strategy
- Overwrites existing conversations
- Updates all fields
- Preserves conversation ID

#### 3. Merge Strategy
- Combines messages from both versions
- Deduplicates based on message content and timestamp
- Updates metadata to latest values
- Preserves conversation history

### Size Limitations

| Format | Max File Size | Max Conversations | Max Messages per Conversation |
|--------|--------------|-------------------|-------------------------------|
| JSON   | 100 MB       | 10,000           | 10,000                       |
| CSV    | 50 MB        | 5,000            | 1,000                        |
| Markdown| 25 MB       | 1,000            | 500                          |

## Export Options

### Filtering Options
- **Date Range:** Start and end date
- **Projects:** Single or multiple project selection
- **Models:** Filter by AI model
- **Cost Range:** Min and max cost
- **Tags:** Include/exclude specific tags
- **Message Types:** Filter message types

### Compression
- Large exports automatically compressed as `.zip`
- Maintains original file structure
- Includes manifest file with export metadata

## API Integration

### Export Endpoint
```
POST /api/v1/export
{
  "format": "json",
  "filters": {
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    },
    "projects": ["proj_789xyz"],
    "include_messages": true
  },
  "options": {
    "compress": true,
    "split_files": false
  }
}
```

### Import Endpoint
```
POST /api/v1/import
Content-Type: multipart/form-data

{
  "file": <file>,
  "options": {
    "conflict_strategy": "merge",
    "validate_only": false,
    "map_fields": {
      "conversation_id": "id",
      "created_at": "timestamp"
    }
  }
}
```

## Data Privacy & Security

### Encryption
- Exports can be encrypted with user-provided password
- AES-256 encryption for sensitive data
- Password-protected ZIP files

### Data Sanitization
- Personal information can be redacted
- API keys and tokens automatically removed
- Option to anonymize user messages

### Audit Trail
- All exports logged with user, timestamp, and filters
- Import operations tracked with source and changes
- Retention policy for export files (30 days default)

## Version Compatibility

### Forward Compatibility
- Newer versions can read older formats
- Unknown fields preserved but ignored
- Graceful degradation for missing features

### Backward Compatibility
- Export version included in metadata
- Option to export in legacy formats
- Migration tools for format updates

## Best Practices

### For Exporting
1. Use JSON for complete data preservation
2. Include date ranges to limit file size
3. Compress large exports
4. Verify export completed before download
5. Store exports securely

### For Importing
1. Validate file format before upload
2. Review conflict resolution options
3. Test with small dataset first
4. Backup existing data before large imports
5. Monitor import progress for errors

## Error Handling

### Common Export Errors
- `EXPORT_TOO_LARGE`: File exceeds size limit
- `INVALID_FILTERS`: Malformed filter parameters
- `EXPORT_TIMEOUT`: Operation took too long
- `INSUFFICIENT_PERMISSIONS`: User lacks export rights

### Common Import Errors
- `INVALID_FORMAT`: File format not recognized
- `VALIDATION_FAILED`: Data doesn't meet requirements
- `DUPLICATE_IDS`: Conflicting conversation IDs
- `QUOTA_EXCEEDED`: Import exceeds user limits

## Future Enhancements

### Planned Features
1. **Incremental Exports:** Only export changes since last export
2. **Scheduled Exports:** Automatic periodic exports
3. **Template System:** Custom export templates
4. **Streaming Exports:** Real-time data streaming for large datasets
5. **Format Conversion:** Convert between formats post-export
6. **External Storage:** Direct export to cloud storage services

### Format Extensions
1. **JSONL:** Line-delimited JSON for streaming
2. **Parquet:** Columnar format for analytics
3. **XML:** Legacy system compatibility
4. **SQLite:** Portable database format
