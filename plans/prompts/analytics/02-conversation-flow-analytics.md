# Conversation Flow Analytics Implementation

## Status: ✅ COMPLETED

### Implementation Summary:
- Backend endpoint created: `GET /api/v1/analytics/conversation-flow` with tree building from parentUuid
- Frontend component created: `ConversationFlowVisualization.tsx` using React Flow
- Interactive tree visualization with zoom, pan, search, and export capabilities
- Full support for sidechain conversations with visual distinction (dashed borders)
- Metrics calculation: max depth, branch count, sidechain percentage, avg branch length
- Color-coded nodes: blue for user, green for assistant messages
- Integrated into Analytics page with session selector dropdown

## Context
ClaudeLens tracks Claude AI conversations with parent-child relationships via `parentUuid` field and sidechain conversations via `isSidechain` flag. This enables visualization of complex conversation patterns.

## Feature Description
Implement a conversation flow visualization that shows how conversations branch, merge, and evolve, helping users understand their interaction patterns with Claude.

## Requirements

### Backend Implementation
1. Create endpoint: `GET /api/v1/analytics/conversation-flow`
2. Query parameters:
   - `session_id`: Required - analyze specific session
   - `include_sidechains`: boolean - include/exclude sidechain messages

3. Database queries:
   ```python
   # Build conversation tree using parentUuid relationships
   # Calculate metrics per branch:
   #   - Branch depth
   #   - Message count per branch
   #   - Cost per branch
   #   - Time spent per branch
   # Identify conversation patterns (linear, branching, iterative)
   ```

4. Response schema:
   ```typescript
   {
     nodes: [{
       id: string,
       parent_id: string | null,
       type: 'user' | 'assistant',
       is_sidechain: boolean,
       cost: number,
       duration_ms: number,
       tool_count: number,
       summary: string
     }],
     edges: [{
       source: string,
       target: string,
       type: 'main' | 'sidechain'
     }],
     metrics: {
       max_depth: number,
       branch_count: number,
       sidechain_percentage: number,
       avg_branch_length: number
     }
   }
   ```

### Frontend Implementation
1. Create component: `ConversationFlowVisualization.tsx`
2. Use D3.js or React Flow for interactive tree/graph visualization
3. Features:
   - Interactive node expansion/collapse
   - Color-coding by message type
   - Path highlighting on hover
   - Zoom and pan controls
   - Export as PNG/SVG

### UI/UX Requirements
- Different visual styles for main vs sidechain conversations
- Node size based on cost or complexity
- Animated transitions when exploring the tree
- Mini-map for large conversations
- Search/filter nodes by content

## Technical Considerations
- Efficient tree traversal for large conversations
- Handle circular references gracefully
- Optimize rendering for conversations with 1000+ messages
- Progressive loading for better performance

## Success Criteria
- Smooth interaction with conversations up to 5000 messages
- Clear visual distinction between conversation types
- Intuitive navigation that helps users understand conversation structure
