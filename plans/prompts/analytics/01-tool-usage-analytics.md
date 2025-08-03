# Tool Usage Analytics Implementation

## Context
ClaudeLens is a full-stack application for tracking and analyzing Claude AI conversations. It consists of:
- **Backend**: FastAPI (Python) with MongoDB for data storage
- **Frontend**: React with TypeScript, using Recharts for visualizations
- **Data Model**: Messages contain tool usage information in `message.tool_calls` field

## Feature Description
Implement comprehensive tool usage analytics that tracks which Claude tools (Bash, Read, Edit, Write, Grep, etc.) are used most frequently across sessions and projects.

## Requirements

### Backend Implementation
1. Create a new endpoint: `GET /api/v1/analytics/tools/usage`
2. Query parameters:
   - `time_range`: TimeRange enum (LAST_24_HOURS, LAST_7_DAYS, etc.)
   - `project_id`: Optional filter by project
   - `group_by`: 'tool' | 'project' | 'session'

3. Database aggregation pipeline:
   ```python
   # Extract tool names from message.tool_calls
   # Group by tool name
   # Count occurrences
   # Calculate percentage of total
   # Include success/failure rates if available
   ```

4. Response schema:
   ```typescript
   {
     tools: [{
       name: string,
       count: number,
       percentage: number,
       avg_duration_ms: number,
       success_rate: number
     }],
     total_tool_calls: number,
     time_range: string
   }
   ```

### Frontend Implementation
1. Create a new component: `ToolUsageChart.tsx`
2. Use Recharts horizontal bar chart
3. Features:
   - Sort by usage frequency
   - Show tool icons if available
   - Click to drill down into time-series view
   - Export data as CSV
   - Responsive design

### UI/UX Requirements
- Color-code tools by category (file operations, search, execution, etc.)
- Show tooltips with detailed stats on hover
- Add animation on data load
- Include a toggle for absolute vs percentage view

## Technical Considerations
- Cache aggregation results for performance
- Handle cases where tool_calls field is null/undefined
- Support real-time updates via WebSocket (optional)

## Success Criteria
- Page load time < 2 seconds
- Accurate tool counting across all message types
- Intuitive visualization that helps users understand their tool usage patterns
