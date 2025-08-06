# ClaudeLens UI Redesign - Continuation Prompt

## Instructions for Agent

You are tasked with implementing the next uncompleted user story from the ClaudeLens UI redesign project. This project enhances the visualization of conversation relationships, branches, and sidechains in Claude conversation histories.

## Your Task

1. **Find the next task**: Open `/plans/uiredesign/build-checklist.md` and locate the FIRST unchecked task `[ ]` that is NOT a QA checkpoint
2. **Implement the task**: Complete the implementation following the specifications
3. **Update progress**: Mark the task as complete `[x]` in the checklist as you finish it
4. **Continue or QA**:
   - If this completes a user story, move to the next one
   - If you encounter a QA checkpoint, perform the QA tasks
   - Stop after completing one full user story OR one QA checkpoint

## Project Context

### Application Overview
ClaudeLens is a web application that archives and visualizes Claude AI conversations. It consists of:
- **Frontend**: React/TypeScript application in `/frontend`
- **Backend**: FastAPI Python application in `/backend`
- **Database**: MongoDB storing conversation data

### Current UI Limitation
The application currently displays conversations in a linear timeline, hiding the rich relationship data available in Claude's message structure.

### Key Concepts You Need to Know

**Message Types:**
- `user`: User messages to Claude
- `assistant`: Claude's responses
- `tool_use`: Tool operations (file reading, web searches)
- `tool_result`: Results from tool operations
- `summary`: Session metadata

**Conversation Patterns:**
1. **Linear Flow**: Standard back-and-forth (99% of conversations)
2. **Branching**: Multiple responses from same parent (regenerated responses)
3. **Sidechains**: Parallel operations marked with `isSidechain: true`
4. **Forking**: New sessions from existing messages (future feature)

**Key Data Fields:**
- `uuid`: Unique message identifier
- `parentUuid`: Links to parent message
- `sessionId`: Groups messages into conversations
- `isSidechain`: Boolean for auxiliary operations

### File Locations

**Frontend Components:**
- `/frontend/src/components/MessageList.tsx` - Main message display component
- `/frontend/src/pages/SessionDetail.tsx` - Session view page
- `/frontend/src/api/types.ts` - TypeScript type definitions
- `/frontend/src/api/sessions.ts` - API client for sessions

**Backend:**
- `/backend/app/models/message.py` - Message data model
- `/backend/app/models/session.py` - Session data model
- `/backend/app/api/v1/endpoints/sessions.py` - Session API endpoints

**Documentation:**
- `/docs/message-handling-types.md` - Detailed message type documentation
- `/plans/uiredesign/ui_improvement_proposal.md` - Full proposal with mockups
- `/plans/uiredesign/conversation_ui_mockup.html` - Visual mockup of improvements
- `/plans/uiredesign/build-checklist.md` - Implementation checklist (UPDATE THIS)

### Design Specifications

**Color Schemes:**
- User messages: Blue theme (`bg-blue-500`, `border-blue-300`)
- Assistant messages: Emerald theme (`bg-emerald-500`, `border-emerald-300`)
- Sidechains: Purple/violet theme (`bg-purple-500`, `border-purple-300`)
- Branches: Amber/yellow indicators (`bg-amber-500`)

**UI Components to Create:**
- `BranchIndicator`: Shows "X versions available"
- `BranchSelector`: Navigate between alternatives
- `ConversationTree`: Interactive tree visualization
- `SidechainPanel`: Sidebar for auxiliary operations
- `ConversationMiniMap`: Overview navigation

## Implementation Guidelines

1. **Component Structure**: Create new components in `/frontend/src/components/`
2. **Styling**: Use Tailwind CSS classes matching existing patterns
3. **State Management**: Use React hooks and component state
4. **Type Safety**: Define TypeScript interfaces for all props and data
5. **Testing**: Write tests alongside implementation
6. **Performance**: Consider large conversations (1000+ messages)

## QA Checkpoint Instructions

When you encounter a QA checkpoint task:

1. **Verify Functionality**:
   - Use the Playwright MCP server to test UI changes
   - Navigate to `http://localhost:3000` (or the running frontend URL)
   - Verify all features from the completed phase work as specified
   - Test with both simple and complex conversations

2. **Run Code Quality Checks**:
   ```bash
   # Frontend
   cd frontend
   npm run lint
   npm run format:check
   npm run type-check
   npm test

   # Backend (if modified)
   cd backend
   poetry run ruff check
   poetry run ruff format --check
   poetry run pytest
   ```

3. **Update Checklist Based on Results**:
   - If all checks pass: Mark QA checkpoint as complete `[x]`
   - If issues found:
     - Mark QA checkpoint with `[FAILED - <reason>]`
     - Change the previous task(s) that failed from `[x]` to `[REWORK - <issue>]`
     - Document specific issues found
     - The next agent will fix these before proceeding

## Working Process

1. Read the checklist to find your task
2. Review relevant existing code
3. Implement the feature/task
4. Test your implementation
5. Update the checklist with your progress
6. If at a QA checkpoint, perform verification
7. Commit your changes with a descriptive message

## Example Checklist Updates

```markdown
# Before
- [ ] Add branch count badge to message headers
- [ ] QA Checkpoint: Verify Phase 1 Implementation

# After successful implementation
- [x] Add branch count badge to message headers
- [ ] QA Checkpoint: Verify Phase 1 Implementation

# After failed QA
- [REWORK - Badge not showing for messages with 3+ branches] Add branch count badge to message headers
- [FAILED - Branch badges missing for some messages, lint errors in BranchIndicator.tsx] QA Checkpoint: Verify Phase 1 Implementation
```

## Important Notes

- Focus on one user story at a time
- Update the checklist immediately after completing each task
- If blocked, document the blocker in the checklist and move to the next task
- Maintain backward compatibility with existing features
- Follow existing code patterns and conventions
- Test with the sample data available in the MongoDB database

## Stop Conditions

Stop work and update the checklist when:
1. You complete a full user story (all tasks checked)
2. You complete a QA checkpoint (either passed or failed)
3. You encounter a blocking issue that prevents progress

Remember: The goal is incremental progress. Complete one user story well rather than rushing through multiple stories.
