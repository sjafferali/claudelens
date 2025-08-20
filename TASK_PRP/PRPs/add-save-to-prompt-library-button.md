# Task PRP: Add Save to Prompt Library Button

## Context

### Task Overview
Add a button next to the copy button on the message list that allows users to save a prompt to the prompt library. This button should only appear on user messages.

### Key Files
- **Message List Component**: `frontend/src/components/MessageList.tsx`
- **Prompt API**: `frontend/src/api/prompts.ts`
- **API Types**: `frontend/src/api/types.ts`
- **Lucide Icons**: Already imported in MessageList

### Current Patterns

#### Copy Button Pattern (MessageList.tsx:615-630)
```tsx
<button
  onClick={() => handleCopyToClipboard(message.content, `message-${message._id}`)}
  className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-all duration-200"
  title="Copy message"
>
  {copiedId === `message-${message._id}` ? (
    <Check className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
  ) : (
    <Copy className="h-4 w-4 text-slate-500 dark:text-slate-400" />
  )}
</button>
```

#### API Integration Pattern
- Uses `promptsApi.createPrompt()` from `frontend/src/api/prompts.ts`
- Requires: `name`, `content`, optional: `description`, `tags`, `folder_id`

### Gotchas
- **User Messages Only**: Must check `message.type === 'user'`
- **Toast Notifications**: Use `react-hot-toast` for feedback (already imported)
- **State Management**: Need to track saving state per message
- **Icon Import**: Need to add `BookmarkPlus` from lucide-react

## Task Breakdown

### 1. UPDATE frontend/src/components/MessageList.tsx - Add imports
**Lines**: 3-18
**Operation**: Add BookmarkPlus icon import
```tsx
import {
  User,
  Bot,
  Terminal,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Wrench,
  Copy,
  Check,
  Clock,
  Coins,
  Hash,
  Zap,
  Share2,
  BookmarkPlus,  // Add this
} from 'lucide-react';
```
**Validate**: `npm run type-check`
**Rollback**: Remove BookmarkPlus import

### 2. UPDATE frontend/src/components/MessageList.tsx - Import prompt API
**Lines**: After line 31
**Operation**: Add promptsApi import
```tsx
import { promptsApi } from '@/api/prompts';
```
**Validate**: `npm run type-check`
**Rollback**: Remove import

### 3. UPDATE frontend/src/components/MessageList.tsx - Add saving state
**Lines**: After line 53
**Operation**: Add state for tracking saves
```tsx
const [savingIds, setSavingIds] = useState<Set<string>>(new Set());
const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
```
**Validate**: Component renders without errors
**Rollback**: Remove state declarations

### 4. UPDATE frontend/src/components/MessageList.tsx - Add save handler
**Lines**: After handleShareMessage function (around line 116)
**Operation**: Add save to prompt library handler
```tsx
const handleSaveToPromptLibrary = async (message: Message) => {
  const messageId = message._id;

  // Start saving
  setSavingIds(prev => new Set(prev).add(messageId));

  try {
    // Generate a name from the first line or first 50 chars
    const firstLine = message.content.split('\n')[0];
    const promptName = firstLine.length > 50
      ? firstLine.substring(0, 50) + '...'
      : firstLine;

    await promptsApi.createPrompt({
      name: promptName || 'Saved Prompt',
      content: message.content,
      description: `Saved from session on ${format(new Date(message.timestamp), 'MMM d, yyyy')}`,
      tags: ['saved-from-session'],
    });

    // Mark as saved
    setSavedIds(prev => new Set(prev).add(messageId));
    toast.success('Prompt saved to library!', {
      duration: 3000,
      icon: '📚',
    });

    // Clear saved indicator after 3 seconds
    setTimeout(() => {
      setSavedIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(messageId);
        return newSet;
      });
    }, 3000);
  } catch (error) {
    toast.error('Failed to save prompt to library');
    console.error('Error saving prompt:', error);
  } finally {
    setSavingIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(messageId);
      return newSet;
    });
  }
};
```
**Validate**: Function compiles without errors
**Rollback**: Remove function

### 5. UPDATE frontend/src/components/MessageList.tsx - Add button to header section
**Lines**: 615-631 (After copy button in header section)
**Operation**: Add save to prompt library button for user messages only
```tsx
{message.type === 'user' && (
  <button
    onClick={() => handleSaveToPromptLibrary(message)}
    disabled={savingIds.has(message._id)}
    className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
    title="Save to prompt library"
  >
    {savedIds.has(message._id) ? (
      <Check className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
    ) : savingIds.has(message._id) ? (
      <div className="h-4 w-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
    ) : (
      <BookmarkPlus className="h-4 w-4 text-slate-500 dark:text-slate-400" />
    )}
  </button>
)}
```
**Validate**: Button renders only for user messages
**Rollback**: Remove button code

### 6. UPDATE frontend/src/components/MessageList.tsx - Add button to inline section
**Lines**: 644-661 (After copy button in inline section for messages without header)
**Operation**: Add save button for user messages without header
```tsx
{message.type === 'user' && (
  <button
    onClick={() => handleSaveToPromptLibrary(message)}
    disabled={savingIds.has(message._id)}
    className="absolute top-4 right-16 p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 bg-white/90 dark:bg-slate-800/90 hover:bg-slate-100 dark:hover:bg-slate-700 backdrop-blur-sm shadow-md border border-slate-200/50 dark:border-slate-600/50 disabled:opacity-50 disabled:cursor-not-allowed"
    title="Save to prompt library"
  >
    {savedIds.has(message._id) ? (
      <Check className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
    ) : savingIds.has(message._id) ? (
      <div className="h-4 w-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
    ) : (
      <BookmarkPlus className="h-4 w-4 text-slate-600 dark:text-slate-400" />
    )}
  </button>
)}
```
**Note**: Position adjusted to `right-16` to avoid overlapping with copy button at `right-4`
**Validate**: Buttons don't overlap
**Rollback**: Remove button code

### 7. TEST frontend - Manual testing
**Operation**: Start dev server and test functionality
```bash
npm run dev
```
**Test Cases**:
1. Save button appears only on user messages ✓
2. Save button shows loading state while saving ✓
3. Success toast appears after save ✓
4. Error toast appears on failure ✓
5. Button temporarily shows check mark after success ✓
6. Buttons don't overlap in both header and inline positions ✓

### 8. CREATE frontend/src/components/__tests__/MessageList.test.tsx - Add tests
**Operation**: Create test file for save functionality
```tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MessageList from '../MessageList';
import { promptsApi } from '@/api/prompts';
import toast from 'react-hot-toast';

jest.mock('@/api/prompts');
jest.mock('react-hot-toast');

describe('MessageList - Save to Prompt Library', () => {
  const mockUserMessage = {
    _id: 'msg1',
    type: 'user',
    content: 'This is a test prompt',
    timestamp: '2024-01-01T00:00:00Z',
  };

  const mockAssistantMessage = {
    _id: 'msg2',
    type: 'assistant',
    content: 'Response',
    timestamp: '2024-01-01T00:00:01Z',
  };

  it('should show save button only for user messages', () => {
    render(<MessageList messages={[mockUserMessage, mockAssistantMessage]} />);

    const saveButtons = screen.getAllByTitle('Save to prompt library');
    expect(saveButtons).toHaveLength(1);
  });

  it('should save prompt when button is clicked', async () => {
    (promptsApi.createPrompt as jest.Mock).mockResolvedValue({});

    render(<MessageList messages={[mockUserMessage]} />);

    const saveButton = screen.getByTitle('Save to prompt library');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(promptsApi.createPrompt).toHaveBeenCalledWith({
        name: 'This is a test prompt',
        content: 'This is a test prompt',
        description: expect.stringContaining('Saved from session'),
        tags: ['saved-from-session'],
      });
      expect(toast.success).toHaveBeenCalledWith('Prompt saved to library!', expect.any(Object));
    });
  });

  it('should show error toast on save failure', async () => {
    (promptsApi.createPrompt as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(<MessageList messages={[mockUserMessage]} />);

    const saveButton = screen.getByTitle('Save to prompt library');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to save prompt to library');
    });
  });
});
```
**Validate**: `npm run test:coverage`
**Rollback**: Delete test file

## Validation Strategy

### Unit Tests
```bash
npm run test -- MessageList.test.tsx
```

### Integration Tests
1. Create a new session with user messages
2. Click save button on user message
3. Navigate to Prompts page
4. Verify prompt appears in library

### Type Checking
```bash
npm run type-check
```

### Linting
```bash
npm run lint
```

## Rollback Plan

If issues occur:
1. Revert MessageList.tsx changes
2. Remove test file
3. Clear browser cache
4. Restart dev server

## Performance Considerations

- Save operations are async and don't block UI
- Loading states prevent duplicate saves
- Temporary success indicators auto-clear after 3 seconds
- No impact on message list rendering performance

## Security Considerations

- API calls use existing authentication
- No sensitive data exposed in UI
- Content sanitization handled by API

## Edge Cases Handled

1. **Long prompts**: Name truncated to 50 chars
2. **Empty content**: Falls back to "Saved Prompt" name
3. **Network errors**: Show error toast
4. **Rapid clicks**: Button disabled during save
5. **Dark mode**: Proper styling for both themes

## Success Criteria

- [x] Button appears only on user messages
- [x] Button positioned correctly next to copy button
- [x] Save functionality works with prompt API
- [x] Loading and success states implemented
- [x] Error handling with toast notifications
- [x] Tests cover main scenarios
- [x] No regression in existing functionality
