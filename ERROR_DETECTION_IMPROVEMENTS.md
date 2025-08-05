# Error Detection Improvements for ClaudeLens

## Summary of Issues Found

After analyzing the error detection system and reviewing the data, I found several issues:

### 1. False Positives (Most Critical)
- The current regex pattern `error|Error|ERROR|failed|Failed|FAILED` catches many false positives
- Examples of false positives:
  - Test outputs that contain "Testing Error Handling"
  - File contents with error-related code
  - Success messages like "No errors found"
  - Documentation mentioning error handling

### 2. Missing Tool Names
- All errors show tool as "unknown" because the tool name isn't stored in `toolUseResult`
- Tool names are in the parent `tool_use` message's `messageData.name` field
- Need to join/lookup to get the actual tool name

### 3. Limited Error Detection
- Only looks at `toolUseResult` fields
- Misses:
  - API errors (overloaded, rate limits) in assistant messages
  - Tool failures mentioned in assistant responses
  - Errors without tool results

### 4. Poor Error Classification
- Current severity is mostly "info" for everything
- No proper classification of error types
- Truncated messages without context

## Proposed Improvements

### 1. Better Error Detection Logic

```python
# Instead of simple regex, use context-aware detection:

# For tool results:
- Check explicit error fields first
- For stderr, only flag if it contains actual error indicators:
  - "error:", "fatal:", "exception", "traceback", "permission denied"
  - "not found", "no such file", "cannot", "failed to", "unable to"
- For exit codes, include context from stdout/stderr

# For API errors:
- Detect "API Error:", "overloaded_error", "rate_limit_error"
- Classify as critical severity

# For operation failures:
- Look for "Failed to", "Could not", "Unable to" in assistant messages
- Extract relevant context lines
```

### 2. Tool Name Resolution

```python
# Use MongoDB $lookup to join with parent tool_use message
{
    "$lookup": {
        "from": "messages",
        "let": {"parent_uuid": "$parentUuid"},
        "pipeline": [
            {"$match": {"$expr": {"$eq": ["$uuid", "$$parent_uuid"]}}},
            {"$project": {"messageData.name": 1}}
        ],
        "as": "tool_use_info"
    }
}
```

### 3. Improved Error Classification

| Error Type | Severity | Description |
|------------|----------|-------------|
| execution_error | critical | Explicit error field in tool result |
| stderr_error | warning | Meaningful stderr output |
| exit_code_error | warning | Non-zero exit code |
| api_overloaded | critical | Claude API overloaded |
| api_rate_limit | critical | Claude API rate limit |
| operation_failed | warning | Tool operation failure mentioned in text |

### 4. Better Context

- Include command for bash errors
- Include model for API errors
- Show first few lines of error output
- Provide session context

## Implementation Steps

1. **Update `get_detailed_errors` method** in `analytics.py`:
   - Replace simple regex with context-aware detection
   - Add $lookup for tool name resolution
   - Add separate pipelines for different error types

2. **Add new error detection pipelines**:
   - Tool execution errors (improved)
   - API errors in assistant messages
   - Operation failures in assistant messages

3. **Improve error classification**:
   - Use proper severity levels
   - Better error type categorization
   - Include more context in error messages

4. **Update the frontend** (if needed):
   - Show error severity with appropriate colors
   - Display tool names properly
   - Show better error context

## Expected Results

After implementing these improvements:
- **Fewer false positives**: Only real errors will be shown
- **Better tool identification**: Errors will show the actual tool name
- **More error coverage**: API errors and operation failures will be detected
- **Improved context**: Users will better understand what went wrong
- **Proper severity**: Critical errors will be highlighted appropriately

## Testing

The improved implementation can be tested with:
1. Sessions with actual tool errors
2. Sessions with API overload errors
3. Sessions with successful operations (should show no errors)
4. Mixed sessions with various error types
