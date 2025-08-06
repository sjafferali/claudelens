# ClaudeLens UI Redesign - Build Checklist

## Overview
This checklist breaks down the conversation flow visualization improvements into actionable user stories and atomic tasks. Each story delivers specific user value and can be implemented independently.

---

## 🎯 Phase 1: Foundation (Quick Wins)

### User Story 1: See When Messages Have Alternative Versions
*As a user, I want to know when a message has alternative responses so I can explore different options Claude provided.*

**Tasks:**
- [x] Add `branchCount` calculation to message processing logic
- [x] Create `BranchIndicator` component showing "X versions available"
- [x] Add branch count badge to message headers in `MessageList.tsx`
- [x] Style branch indicator with amber color scheme
- [x] Add hover tooltip showing "Click to see alternatives"
- [x] Write unit tests for branch detection logic
- [x] Update message type definitions to include branch metadata

### User Story 2: Navigate Between Alternative Responses
*As a user, I want to switch between different versions of Claude's responses so I can find the best answer.*

**Tasks:**
- [x] Create `BranchSelector` component with prev/next navigation
- [x] Add "Branch X of Y" display counter
- [x] Implement `onSelectBranch` handler in `SessionDetail.tsx`
- [x] Add keyboard shortcuts (Alt+←/→) for branch navigation
- [x] Store active branch UUID in component state
- [x] Update URL params to include branch selection
- [x] Add smooth transition animation between branches
- [x] Highlight currently selected branch in UI
- [x] Write tests for branch navigation logic

### User Story 3: Jump to Parent and Child Messages
*As a user, I want to quickly navigate to related messages so I can follow the conversation flow.*

**Tasks:**
- [x] Add "Jump to parent" button to message headers
- [x] Add "View replies" button for messages with children
- [x] Implement smooth scroll to message on click
- [x] Add message ID to DOM elements for scroll targeting
- [x] Create `useMessageNavigation` hook
- [x] Add visual indicator for navigation target
- [x] Implement breadcrumb trail showing message path
- [x] Write tests for navigation functions

### 🔍 QA Checkpoint: Phase 1 Verification
*Verify that all Phase 1 features are working correctly before proceeding to Phase 2.*

**QA Tasks:**
- [x] **Functional Testing with Playwright:**
  - Navigate to a session with branched messages (3+ alternatives)
  - Verify branch count badges appear on all messages with alternatives
  - Test branch navigation using prev/next buttons
  - Confirm "Branch X of Y" counter updates correctly
  - Test keyboard shortcuts (Alt+←/→) for branch navigation
  - Verify parent/child navigation buttons work
  - Confirm smooth scrolling to target messages
  - Check breadcrumb trail displays correct path

- [x] **Visual Verification:**
  - Branch indicators use amber color scheme (#fbbf24)
  - Hover tooltips display correctly
  - Selected branch is visually highlighted
  - Navigation animations are smooth
  - All UI elements are properly aligned

- [x] **Edge Cases:**
  - Test with conversations having 0, 1, and 5+ branches
  - Verify behavior with deeply nested messages (10+ levels)
  - Test with sessions containing no messages
  - Verify navigation at conversation boundaries

- [x] **Code Quality Checks:**
  ```bash
  cd frontend
  npm run lint         # Should pass with 0 errors
  npm run format:check # Should pass with 0 issues
  npm run type-check   # Should pass with 0 type errors
  npm test            # All tests should pass
  ```

- [x] **Performance Verification:**
  - Test with large conversation (500+ messages)
  - Branch navigation should respond in <100ms
  - No memory leaks during repeated navigation
  - React DevTools shows no unnecessary re-renders

**QA Result: ✅ PASSED - All Phase 1 features verified and working correctly**
- Branch detection and navigation fully functional
- Visual design matches specifications
- All code quality checks pass
- Performance meets requirements
- Ready to proceed to Phase 2

---

## 🌳 Phase 2: Visualization (Core Features)

### User Story 4: View Conversation as Interactive Tree
*As a user, I want to see my conversation as a visual tree so I can understand the overall structure and relationships.*

**Tasks:**
- [x] Install React Flow dependency
- [REWORK - TypeScript errors with Message type properties] Create `ConversationTree` component
- [REWORK - TypeScript errors with Message type properties] Implement tree layout algorithm for message positioning
- [REWORK - TypeScript errors with Message type properties] Create custom `MessageNode` component
- [x] Add node color coding by message type
- [x] Implement edge rendering with proper styling
- [x] Add zoom and pan controls
- [x] Create node click handler for message selection
- [x] Add animation for active message highlighting
- [x] Implement tree view toggle button in UI
- [x] Add loading state for tree rendering
- [x] Optimize performance for large conversations
- [REWORK - TypeScript errors in test file] Write tests for tree generation logic

### User Story 5: See Sidechains Separately
*As a user, I want to see tool operations and sidechains in a dedicated panel so the main conversation stays clear.*

**Tasks:**
- [x] Create `SidechainPanel` component
- [x] Add collapsible sidebar layout to `SessionDetail`
- [x] Filter messages by `isSidechain` property
- [x] Group sidechains by parent message
- [x] Add toggle button to show/hide sidechain panel
- [x] Create sidechain message cards with compact view
- [x] Add linking lines to parent messages
- [x] Implement sidechain type categorization
- [x] Add sidechain count badge to main messages
- [x] Style with purple/violet color scheme
- [x] Write tests for sidechain filtering

### User Story 6: Navigate with Conversation Mini-Map
*As a user, I want a mini-map overview so I can quickly understand conversation complexity and jump to different sections.*

**Tasks:**
- [REWORK - ResizeObserver not defined error in tests] Create `ConversationMiniMap` component
- [x] Generate thumbnail representation of conversation structure
- [x] Add viewport indicator showing current position
- [x] Implement click-to-navigate on mini-map
- [x] Calculate complexity metrics (branches, depth)
- [x] Add color coding for message types
- [x] Position mini-map as floating overlay
- [x] Add show/hide toggle for mini-map
- [x] Highlight active message in mini-map
- [REWORK - Test failures with ResizeObserver] Write tests for mini-map generation

### User Story 7: Understand My Current Location
*As a user, I want breadcrumb navigation so I always know where I am in the conversation hierarchy.*

**Tasks:**
- [x] Create `ConversationBreadcrumbs` component
- [x] Build path from root to current message
- [x] Add clickable breadcrumb items
- [x] Show branch information in breadcrumbs
- [x] Truncate long paths with ellipsis
- [x] Add hover tooltips for truncated items
- [x] Style breadcrumbs to match UI theme
- [x] Update breadcrumbs on message navigation
- [x] Write tests for path building logic

### 🔍 QA Checkpoint: Phase 2 Verification
*Verify that all Phase 2 visualization features are working correctly before proceeding to Phase 3.*

**QA Tasks:**
- [FAILED - TypeScript errors and test failures] **Tree View Testing with Playwright:**
  - Toggle to tree view mode successfully
  - Verify all messages appear as nodes in correct hierarchy
  - Test node clicking navigates to message
  - Verify zoom and pan controls work
  - Check node colors match message types (blue=user, emerald=assistant, purple=tool)
  - Verify sidechain messages show with dashed edges
  - Test mini-map displays and allows navigation
  - Confirm active message is highlighted in tree

- [ ] **Sidechain Panel Testing:**
  - Verify panel opens/closes with toggle button
  - Confirm sidechains are correctly filtered from main flow
  - Test that sidechains group by parent message
  - Verify linking lines connect to parent messages
  - Check purple/violet color scheme is applied
  - Confirm sidechain count badges appear on main messages

- [ ] **Mini-Map Functionality:**
  - Mini-map shows accurate conversation structure
  - Click-to-navigate works correctly
  - Viewport indicator shows current position
  - Complexity metrics display correctly
  - Toggle show/hide works

- [ ] **Breadcrumb Navigation:**
  - Breadcrumbs show correct path from root
  - Clicking breadcrumb items navigates correctly
  - Branch information displays in breadcrumbs
  - Long paths truncate with ellipsis
  - Hover tooltips show full path

- [ ] **Performance Testing:**
  - Tree view renders within 500ms for 100+ messages
  - Smooth animations at 60fps
  - No lag when panning/zooming tree
  - Memory usage stable during navigation
  - React Flow handles 500+ nodes efficiently

- [FAILED - TypeScript errors in ConversationTree and test failures] **Code Quality Checks:**
  ```bash
  cd frontend
  npm run lint         # ✓ Passed with 0 errors
  npm run format:check # ✓ Passed with 0 issues
  npm run type-check   # ✗ Failed - 71 TypeScript errors
  npm test            # ✗ Failed - 10 test failures
  ```

**QA Result: ❌ FAILED - TypeScript errors and test failures**
- npm run lint: ✅ Passed
- npm run format:check: ✅ Passed
- npm run type-check: ❌ 71 TypeScript errors in ConversationTree, MessageNode, tree-layout
- npm test: ❌ 10 test failures in ConversationMiniMap tests
- Issues need to be fixed before proceeding to Phase 3

**If any checks fail:** Mark this checkpoint as `[FAILED - <details>]` and mark the specific failing task(s) above as `[REWORK - <issue>]`

---

## 🔀 Phase 3: Advanced Features

### User Story 8: Compare Different Branches Side-by-Side
*As a user, I want to compare alternative responses side-by-side so I can evaluate which approach worked better.*

**Tasks:**
- [ ] Create `BranchComparison` view component
- [ ] Implement split-pane layout
- [ ] Add branch selection dropdowns
- [ ] Create synchronized scrolling between panes
- [ ] Highlight differences between branches
- [ ] Add metrics comparison (cost, tokens, time)
- [ ] Implement "Select this branch" action
- [ ] Add export comparison feature
- [ ] Style with clear visual separation
- [ ] Write tests for comparison logic

### User Story 9: Fork Conversation to New Session
*As a user, I want to fork a conversation at any point so I can explore a different direction without losing my original work.*

**Tasks:**
- [ ] Add "Fork from here" button to messages
- [ ] Create fork confirmation dialog
- [ ] Implement API endpoint for session forking
- [ ] Generate new session with fork metadata
- [ ] Copy conversation history up to fork point
- [ ] Add fork indicator in original session
- [ ] Create "View forks" panel
- [ ] Navigate to new forked session
- [ ] Track fork relationships in database
- [ ] Write tests for forking logic

### User Story 10: Merge Insights from Multiple Branches
*As a user, I want to merge the best parts of different conversation branches so I can create an optimal solution.*

**Tasks:**
- [ ] Create `BranchMerge` dialog component
- [ ] Add branch multi-selection interface
- [ ] Implement merge strategy selector (sequential/intelligent/cherry-pick)
- [ ] Create message selection checklist for cherry-pick
- [ ] Add merge preview panel
- [ ] Implement AI-powered intelligent merge
- [ ] Generate merge summary message
- [ ] Create new branch with merged content
- [ ] Add merge history tracking
- [ ] Implement conflict resolution UI
- [ ] Write comprehensive merge tests

### 🔍 QA Checkpoint: Phase 3 Verification
*Verify that all Phase 3 advanced features are working correctly.*

**QA Tasks:**
- [ ] **Branch Comparison Testing with Playwright:**
  - Open comparison view with 2+ branches
  - Verify split-pane layout displays correctly
  - Test branch selection dropdowns work
  - Confirm synchronized scrolling between panes
  - Check differences are highlighted
  - Verify metrics comparison (cost, tokens) displays
  - Test "Select this branch" action works
  - Verify export comparison feature

- [ ] **Fork Functionality Testing:**
  - "Fork from here" button appears on messages
  - Fork confirmation dialog displays
  - New session is created with correct metadata
  - Conversation history copied up to fork point
  - Fork indicator shows in original session
  - "View forks" panel displays forked sessions
  - Navigation to forked session works
  - Fork relationships tracked in database

- [ ] **Merge Operations Testing:**
  - Branch merge dialog opens correctly
  - Multi-selection of branches works
  - All merge strategies available (sequential/intelligent/cherry-pick)
  - Cherry-pick allows individual message selection
  - Merge preview shows expected result
  - AI-powered merge produces coherent result
  - Merge summary message generated
  - New merged branch created successfully
  - Merge history is tracked
  - Conflict resolution UI works for conflicting merges

- [ ] **Integration Testing:**
  - Fork → Edit → Merge workflow completes
  - Compare → Select → Continue workflow works
  - All advanced features work with Phase 1 & 2 features
  - No regression in existing functionality

- [ ] **Backend Verification:**
  ```bash
  cd backend
  poetry run pytest tests/  # All tests pass
  poetry run ruff check     # No linting errors
  poetry run ruff format --check  # Formatting correct
  ```

- [ ] **Performance & Edge Cases:**
  - Fork operation completes in <2 seconds
  - Merge handles 10+ branches without error
  - Comparison view handles long conversations (1000+ messages)
  - Database properly indexes fork relationships
  - No memory leaks during complex operations

**If any checks fail:** Mark this checkpoint as `[FAILED - <details>]` and mark the specific failing task(s) above as `[REWORK - <issue>]`

---

## 🎨 UI Polish & Performance

### User Story 11: Experience Smooth Interactions
*As a user, I want the UI to be responsive and smooth so I can navigate complex conversations effortlessly.*

**Tasks:**
- [ ] Add loading skeletons for async operations
- [ ] Implement virtual scrolling for long conversations
- [ ] Add transition animations between views
- [ ] Optimize React re-renders with memo/callbacks
- [ ] Implement progressive tree rendering
- [ ] Add error boundaries for graceful failures
- [ ] Cache processed conversation structures
- [ ] Implement undo/redo for navigation
- [ ] Add keyboard shortcut overlay
- [ ] Performance test with large conversations (1000+ messages)

### User Story 12: Understand Visual Indicators
*As a user, I want clear visual legends and help text so I understand what all the indicators mean.*

**Tasks:**
- [ ] Create `Legend` component for tree view
- [ ] Add tooltips to all interactive elements
- [ ] Create onboarding tour for new features
- [ ] Add help panel with feature documentation
- [ ] Implement color blind friendly palette option
- [ ] Add icon legend for message types
- [ ] Create keyboard shortcut reference
- [ ] Add feature discovery hints
- [ ] Write user-facing documentation

---

## 📊 Backend Support Tasks

### API Enhancements
- [ ] Add endpoint for branch statistics
- [ ] Create endpoint for fork operations
- [ ] Add sidechain aggregation endpoint
- [ ] Implement conversation complexity scoring
- [ ] Add branch path calculation
- [ ] Create merge operation endpoint
- [ ] Optimize message relationship queries
- [ ] Add caching for tree structures

### Database Updates
- [ ] Add indexes for parentUuid queries
- [ ] Create fork relationship table
- [ ] Add merge history tracking
- [ ] Optimize branch detection queries
- [ ] Add conversation complexity metrics
- [ ] Create materialized views for trees

---

## 🧪 Testing Requirements

### Unit Tests
- [ ] Branch detection logic
- [ ] Tree generation algorithm
- [ ] Navigation path building
- [ ] Sidechain filtering
- [ ] Merge conflict resolution
- [ ] Fork relationship tracking

### Integration Tests
- [ ] Branch navigation flow
- [ ] Tree view interactions
- [ ] Sidechain panel updates
- [ ] Fork creation process
- [ ] Merge operation workflow

### E2E Tests
- [ ] Complete branch exploration flow
- [ ] Tree view with large conversations
- [ ] Fork and continue workflow
- [ ] Branch comparison workflow

---

## 📝 Documentation Tasks

- [ ] Update user guide with new features
- [ ] Create video tutorials for complex features
- [ ] Document keyboard shortcuts
- [ ] Write API documentation for new endpoints
- [ ] Create troubleshooting guide
- [ ] Document performance considerations

---

## 🚀 Release Checklist

### Before Each Release
- [ ] All tests passing
- [ ] Performance benchmarks met
- [ ] Accessibility audit passed
- [ ] Documentation updated
- [ ] Feature flags configured
- [ ] Rollback plan prepared

---

## Success Metrics

Track these metrics to measure feature success:
- Time to find specific messages (should decrease)
- Usage of branch navigation features
- User engagement with tree view
- Support tickets about "lost" messages (should decrease)
- Performance metrics (render time, memory usage)
- User satisfaction scores

---

## Workflow Process

### For Implementation Agents
1. Find the first unchecked `[ ]` task that is NOT a QA checkpoint
2. Implement the task according to specifications
3. Mark completed tasks with `[x]`
4. Continue until reaching a QA checkpoint or completing a user story
5. Run basic tests to verify your implementation works

### For QA Checkpoints
1. When encountering a QA checkpoint, perform ALL verification tasks
2. Use Playwright MCP to test UI functionality
3. Run all linting, formatting, and test commands
4. If all checks pass: Mark checkpoint as `[x]`
5. If any check fails:
   - Mark checkpoint as `[FAILED - <specific issues>]`
   - Mark failing tasks as `[REWORK - <what needs fixing>]`
   - Document issues clearly for the next agent

### Task Status Markers
- `[ ]` - Not started
- `[x]` - Completed successfully
- `[REWORK - <issue>]` - Needs to be redone due to QA failure
- `[FAILED - <reason>]` - QA checkpoint failed, see details
- `[BLOCKED - <reason>]` - Cannot proceed due to external dependency

### Continuous Process
Agents should use `/plans/uiredesign/continue-prompt.md` to understand the full context and continue work. The process is:
1. Agent implements tasks → 2. QA verification → 3. Fix any issues → 4. Repeat

## Notes

- Start with Phase 1 for immediate user value
- Each user story can be released independently
- Prioritize based on user feedback
- Consider feature flags for gradual rollout
- Monitor performance impact of visualization features
- QA checkpoints ensure quality before moving to next phase
