# Message Linking Documentation

## Overview

ClaudeLens supports direct linking to specific messages within conversations. This feature allows users to:
- Share links to specific points in conversations
- Bookmark important messages
- Navigate directly to message branches
- Reference exact conversation moments

## URL Format

Message links follow this format:
```
/sessions/{sessionId}?messageId={messageId}&branchIndex={branchIndex}
```

### Parameters

- **sessionId** (required): The unique identifier for the conversation session
- **messageId** (required): The UUID of the specific message to link to
- **branchIndex** (optional): The branch number when linking to alternative responses (1-based)

### Examples

Basic message link:
```
/sessions/65f1234567890abcdef12345?messageId=msg_67890abcdef12345
```

Link to specific branch (Branch 2 of 3):
```
/sessions/65f1234567890abcdef12345?messageId=msg_67890abcdef12345&branchIndex=2
```

## How to Share Messages

### 1. Using the Share Button

Each message displays a share icon (🔗) next to the timestamp when you hover over the message. Click the share icon to:
- Copy the message link to your clipboard
- Show a confirmation toast with message preview

### 2. Using Keyboard Shortcuts

- **Cmd/Ctrl + Shift + L**: Copy link to the currently selected message
- If no message is selected, copies link to the first visible message

### 3. Programmatic Usage

Use the utility functions in `/src/utils/message-linking.ts`:

```typescript
import { generateMessageLink, copyMessageLink } from '@/utils/message-linking';

// Generate a link
const link = generateMessageLink(message, sessionId, {
  branchIndex: 2,
  includeTimestamp: true
});

// Copy to clipboard with user feedback
const success = await copyMessageLink(message, sessionId, {
  branchIndex: message.branchIndex
});
```

## Link Behavior

### Navigation
- Links automatically scroll to and highlight the target message
- If the message is in a collapsed branch, the branch is expanded
- Invalid messageId parameters show an error message

### Branch Handling
- Links to branched messages will show the specified branch
- If branchIndex is omitted, shows the first branch (branchIndex=1)
- Invalid branch indexes fall back to the first available branch

### Deep Linking Support
- All message types are supported: user, assistant, tool_use, tool_result
- Tool operation messages are linkable individually
- Sidechain messages can be directly linked

## Message Types and Linking

### User Messages
- Link format shows "User: [first 50 characters]..."
- Useful for referencing specific questions or requests

### Assistant Messages
- Link format shows "Assistant: [first 50 characters]..."
- Includes branch information if message has alternatives

### Tool Operations
- Tool Use: Shows "Tool Use: [tool_name]..."
- Tool Result: Shows "Tool Result: [preview]..."
- Links directly to the tool operation in the timeline

### System Messages
- Link format shows "Message: [preview]..."
- Includes any system-generated content

## Browser Compatibility

Message linking works across all modern browsers:
- **Chrome/Chromium**: Full support including clipboard API
- **Firefox**: Full support including clipboard API
- **Safari**: Full support including clipboard API
- **Edge**: Full support including clipboard API

### Fallback Behavior
- If modern clipboard API fails, uses legacy `document.execCommand('copy')`
- Shows appropriate error messages if copying fails entirely

## Privacy and Security

### URL Structure
- Message links contain no sensitive information
- UUIDs are cryptographically random and not guessable
- Session access controls apply to all linked messages

### Sharing Considerations
- Links only work for users with access to the session
- Consider privacy before sharing links containing sensitive conversations
- Links include conversation context - share appropriately

## Troubleshooting

### "Session ID not available"
- Occurs when trying to share from a page without session context
- Navigate to a specific session page before sharing

### "Failed to copy message link"
- Browser may block clipboard access
- Try using the manual copy option or refresh the page

### Message not found
- The linked message may have been deleted
- Session may not be accessible to the current user
- Check that the messageId parameter is correct

### Branch not available
- Requested branchIndex may not exist for this message
- System will fall back to the first available branch

## Implementation Details

### URL Parameter Parsing
The application uses `URLSearchParams` to parse message link parameters:

```typescript
const messageId = searchParams.get('messageId');
const branchIndex = searchParams.get('branchIndex') ?
  parseInt(searchParams.get('branchIndex')!, 10) : undefined;
```

### Message Resolution
Messages are located using multiple ID formats for compatibility:
- `uuid` field (primary)
- `messageUuid` field (fallback)
- `_id` field (database ID fallback)

### Toast Notifications
Link copying shows user-friendly feedback:
- Success: "Message link copied! {preview}" with 🔗 icon
- Error: "Failed to copy message link"
- Duration: 3 seconds for success messages
