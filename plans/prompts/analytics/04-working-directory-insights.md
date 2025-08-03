# Working Directory Insights Implementation

## Context
ClaudeLens tracks the working directory (`cwd` field) for each message, enabling analysis of which projects and directories consume the most AI resources.

## Feature Description
Implement a treemap visualization and analytics dashboard showing resource usage (costs, messages, tokens) broken down by directory hierarchy.

## Requirements

### Backend Implementation
1. Create endpoint: `GET /api/v1/analytics/directory-usage`
2. Query parameters:
   - `time_range`: TimeRange enum
   - `depth`: Maximum directory depth to analyze (default: 3)
   - `min_cost`: Minimum cost threshold to include directory

3. Database aggregation:
   ```python
   # Parse cwd paths into hierarchical structure
   # Aggregate metrics per directory:
   #   - Total cost
   #   - Message count
   #   - Unique sessions
   #   - Average session duration
   #   - Most used tools
   # Build tree structure with accumulated metrics
   ```

4. Response schema:
   ```typescript
   {
     root: {
       path: string,
       name: string,
       metrics: {
         cost: number,
         messages: number,
         sessions: number,
         avg_cost_per_session: number,
         last_active: string
       },
       children: DirectoryNode[],
       percentage_of_total: number
     },
     total_metrics: {
       total_cost: number,
       total_messages: number,
       unique_directories: number
     }
   }
   ```

### Frontend Implementation
1. Create components:
   - `DirectoryTreemap.tsx` - Interactive treemap visualization
   - `DirectoryExplorer.tsx` - File explorer style view
   - `DirectoryMetrics.tsx` - Detailed metrics panel

2. Features:
   - Zoomable treemap using D3.js or Recharts
   - Click to drill down into subdirectories
   - Breadcrumb navigation
   - Size by: cost, messages, or sessions toggle
   - Color by: activity recency or cost intensity

### UI/UX Requirements
- Gradient coloring based on cost intensity
- Hover tooltips with detailed metrics
- Search functionality for directory paths
- Export directory usage report
- Responsive layout for various screen sizes

## Technical Considerations
- Handle deep directory structures efficiently
- Normalize paths across different OS (Windows/Unix)
- Cache directory tree calculations
- Handle missing or null cwd values
- Privacy: Option to anonymize directory names

## Success Criteria
- Visualize up to 10,000 unique directories smoothly
- Intuitive navigation through directory hierarchy
- Clear identification of resource-heavy directories
- Help users optimize their project structure for cost efficiency
