# Task: Implement Pagination for Long Conversation Threads

## Application Overview

ClaudeLens is a web application designed to analyze and visualize Claude AI conversation sessions. The application consists of:

- **Backend**: FastAPI (Python) with MongoDB for data storage
- **Frontend**: React with TypeScript, Tailwind CSS, and Vite
- **Purpose**: Track, analyze, and browse Claude AI conversations organized by projects

The app stores and displays Claude AI conversations, which can contain hundreds or thousands of messages in a single session. Each message includes content, timestamps, token counts, costs, and metadata.

## Current State

### Session Detail Page (`/sessions/{sessionId}`)
Currently displays:
- Session summary and metadata in the header
- Session details in a sidebar (ID, timestamps, models used)
- **All messages** loaded at once in the MessageList component
- No pagination - potential performance issues with long conversations

### Message Display
The `MessageList` component (`/frontend/src/components/MessageList.tsx`) shows:
- Role-based formatting (User, Assistant, System, Tool Use/Result)
- Timestamps, token counts, and costs
- Syntax highlighting for code blocks
- Different background colors for message types

### Backend API
The backend already supports message pagination:

```
GET /api/v1/sessions/{session_id}/messages
Query Parameters:
- skip: Number of messages to skip (default: 0)
- limit: Number of messages to return (default: 50, max: 200)

Returns:
{
  "session": { ...session details },
  "messages": [ ...array of messages ],
  "skip": 0,
  "limit": 50
}
```

## Task Requirements

### 1. Virtual Scrolling Implementation
For sessions with hundreds of messages, implement virtual scrolling:
- Use **@tanstack/react-virtual** for efficient rendering
- Only render visible messages + buffer
- Smooth scrolling performance even with 1000+ messages
- Maintain scroll position when navigating away and back

### 2. Load More Pagination
As an alternative or complement to virtual scrolling:
- Initial load: 50 most recent messages
- "Load Earlier Messages" button at the top
- "Load More Messages" button at the bottom (if applicable)
- Loading states while fetching
- Smooth insertion animation for new messages

### 3. Message Navigation Features
Add navigation aids for long conversations:
- **Jump to Bottom/Top** floating buttons
  - Show "Jump to Bottom" when scrolled up
  - Show "Jump to Top" when scrolled down
  - Smooth scroll animation

- **Message Timeline Indicator**
  - Slim timeline on the right side
  - Shows relative position in conversation
  - Click to jump to position
  - Highlight sections with different message types

- **Search Within Conversation**
  - Ctrl/Cmd + F to open search
  - Highlight matching text
  - Next/Previous match navigation
  - Show match count "1 of 5 matches"

### 4. Performance Optimizations
- **Message Rendering**
  - Memoize message components with React.memo
  - Lazy load images and large content blocks
  - Debounce scroll events

- **Data Management**
  - Cache loaded messages in React Query
  - Prefetch next batch while user approaches end
  - Only keep necessary messages in memory

### 5. Progressive Loading Indicators
- **Skeleton Messages** while loading
- **Progress Bar** showing loaded vs total messages
- **Message Counter**: "Showing 50-100 of 523 messages"
- **Estimated Reading Time** based on message count

### 6. Keyboard Shortcuts
Implement productivity shortcuts:
- `J/K` - Navigate to previous/next message
- `G G` - Go to top (Vim style)
- `Shift + G` - Go to bottom
- `Space/Shift+Space` - Page down/up
- `/` - Focus search
- `Esc` - Close search

Display shortcut guide with `?` key.

## Implementation Details

### Technologies to Use
- **@tanstack/react-virtual** for virtual scrolling
- **react-intersection-observer** for infinite scroll triggers
- **react-hotkeys-hook** for keyboard shortcuts
- **fuse.js** for client-side search functionality
- **framer-motion** for smooth animations
- Existing: React Query, TypeScript, Tailwind CSS

### Component Structure
1. Create `components/VirtualMessageList.tsx` - Virtual scrolling wrapper
2. Create `components/MessageNavigator.tsx` - Timeline and jump buttons
3. Create `components/ConversationSearch.tsx` - Search within messages
4. Create `components/KeyboardShortcuts.tsx` - Shortcut guide modal
5. Update `components/MessageList.tsx` - Integrate with virtual scrolling
6. Create `hooks/useMessagePagination.ts` - Pagination logic
7. Create `hooks/useConversationSearch.ts` - Search functionality

### UI/UX Guidelines

#### Virtual Scrolling
- Maintain at least 5 messages above/below viewport as buffer
- Preserve scroll position percentage when window resizes
- Show subtle loading placeholder for unloaded messages
- Handle dynamic height messages gracefully

#### Load More Buttons
- Sticky position at top/bottom of message container
- Disable when no more messages to load
- Show remaining message count
- Collapse when all messages are loaded

#### Navigation UI
- Floating action buttons in bottom-right corner
- Semi-transparent with backdrop blur
- Hide when user is typing
- Timeline indicator: 40px wide on desktop, hidden on mobile

#### Search Interface
- Overlay search bar at top of conversation
- Yellow highlight for current match
- Light yellow for other matches
- Maintain search state when loading more messages

### Performance Requirements
- Initial render under 100ms for 50 messages
- Smooth 60fps scrolling with 1000+ messages
- Memory usage under 100MB for large conversations
- Lazy load images and media content
- Cancel pending requests when navigating away

### State Management
- Store pagination state in component (not URL)
- Cache message batches with React Query
- Persist scroll position in session storage
- Track loaded message ranges to prevent duplicates

### Accessibility
- Announce message count to screen readers
- Keyboard navigation fully functional
- Focus management for search and shortcuts
- High contrast mode for navigation elements
- Respect prefers-reduced-motion

## Success Criteria
1. Long conversations (500+ messages) load quickly
2. Scrolling remains smooth with any message count
3. Users can efficiently navigate to any part of conversation
4. Search helps find specific content quickly
5. Memory usage remains reasonable
6. Works well on mobile devices
7. Keyboard shortcuts improve power user productivity
8. Loading states prevent confusion
9. No duplicate messages when paginating
10. Scroll position preserved on navigation

## Testing Considerations
- Test with conversations of various sizes (10, 100, 1000+ messages)
- Verify performance metrics with Chrome DevTools
- Test rapid scrolling and navigation
- Check memory leaks with long sessions
- Test search with special characters and regex
- Verify mobile touch scrolling
- Test with slow network connections
- Ensure messages load in correct order
- Test keyboard shortcuts across browsers
- Verify accessibility with screen readers

## Edge Cases to Handle
- Sessions with no messages
- Sessions with only 1-2 messages
- Very long individual messages (10,000+ characters)
- Messages with large embedded images
- Rapid pagination requests
- Network failures during pagination
- Browser back/forward with scroll position
- Window resize during virtual scrolling
- Search across paginated boundaries
- Concurrent message loading requests

## Files to Modify/Create
- `/frontend/src/components/MessageList.tsx` - Enhance with virtual scrolling
- `/frontend/src/components/VirtualMessageList.tsx` - New virtual scroll wrapper
- `/frontend/src/components/MessageNavigator.tsx` - New navigation component
- `/frontend/src/components/ConversationSearch.tsx` - New search component
- `/frontend/src/components/KeyboardShortcuts.tsx` - New shortcuts guide
- `/frontend/src/hooks/useMessagePagination.ts` - New pagination hook
- `/frontend/src/hooks/useConversationSearch.ts` - New search hook
- `/frontend/src/pages/Sessions.tsx` - Integrate pagination components
- `/frontend/src/hooks/useSessions.ts` - Update message fetching logic
- `/frontend/package.json` - Add new dependencies
