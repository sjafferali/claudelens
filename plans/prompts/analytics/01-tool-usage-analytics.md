# Tool Usage Analytics Implementation

## Context
ClaudeLens is a full-stack application for tracking and analyzing Claude AI conversations with a modern UI featuring stat cards and details panels:
- **Backend**: FastAPI (Python) with MongoDB for data storage
- **Frontend**: React with TypeScript, CSS variables for theming
- **UI Design**: Dark/light theme with stat cards, details panel, and tag-based displays
- **Data Model**: Messages contain tool usage information in `message.tool_calls` field

## Feature Description
Implement tool usage analytics that integrates with the new UI design, displaying tool usage in both the "Tools Used" stat card and the detailed "Tools Used" section in the right panel.

## Requirements

### Backend Implementation
1. Create endpoints:
   - `GET /api/v1/analytics/tools/summary` - For stat card display
   - `GET /api/v1/analytics/tools/detailed` - For detailed panel view

2. Query parameters:
   - `session_id`: Filter by specific session
   - `project_id`: Optional filter by project
   - `time_range`: TimeRange enum (LAST_24_HOURS, LAST_7_DAYS, etc.)

3. Database aggregation pipeline:
   ```python
   # Extract tool names from message.tool_calls
   # Group by tool name
   # Count occurrences
   # Calculate usage frequency
   # Sort by usage count
   ```

4. Response schemas:
   ```typescript
   // Summary for stat card
   {
     total_tool_calls: number,
     unique_tools: number,
     most_used_tool: string
   }

   // Detailed for panel
   {
     tools: [{
       name: string,
       count: number,
       percentage: number,
       category: 'file' | 'search' | 'execution' | 'other',
       last_used: string
     }],
     total_calls: number,
     session_id: string
   }
   ```

### Frontend Implementation

1. **Stat Card Component**: `ToolUsageStatCard.tsx`
   ```typescript
   // Displays in the 2x2 stat grid
   // Shows total number of tools used
   // Styled with:
   // - stat-value class (24px font, var(--accent-primary))
   // - stat-label class (12px font, var(--text-muted))
   ```

2. **Details Panel Component**: `ToolUsageDetails.tsx`
   ```typescript
   // Displays in the right sidebar details panel
   // Shows tools as tags with usage counts
   // Uses tag class styling:
   // - padding: 4px 12px
   // - background: var(--bg-tertiary)
   // - border: 1px solid var(--border-primary)
   // - border-radius: 16px
   ```

3. **Tag Display Format**:
   ```html
   <div class="tags">
     <span class="tag">todoWrite × 12</span>
     <span class="tag">fileWrite × 4</span>
     <span class="tag">codeAnalysis × 2</span>
   </div>
   ```

### UI/UX Requirements
- **Stat Card**: Display total tools used as primary metric
- **Details Panel**: Show individual tools as tags with counts
- **Color Coding**: Use consistent tag styling from the mockup
- **Hover Effects**: Show detailed stats in tooltip
- **Theme Support**: Use CSS variables for all colors
- **Animation**: Fade-in animation when data loads

### Integration Points
1. **Session Detail Page**: Both stat card and details panel
2. **Analytics Dashboard**: Aggregate view across sessions
3. **Real-time Updates**: Update counts as new tools are used

## Technical Considerations
- Use MongoDB aggregation for efficient counting
- Cache results with 5-minute TTL
- Handle missing tool_calls gracefully
- Support both dark and light themes via CSS variables

## Success Criteria
- Stat card loads instantly (< 100ms)
- Details panel updates smoothly
- Accurate tool counting across all message types
- Seamless theme switching support
- Tags display consistently with mockup design
