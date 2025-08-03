# Git Branch Analytics Implementation

## Context
ClaudeLens tracks the git branch (`gitBranch` field) for each message, enabling analysis of AI usage patterns across different development branches.

## Feature Description
Implement analytics showing how Claude usage varies across git branches, helping teams understand resource allocation in their development workflow.

## Requirements

### Backend Implementation
1. Create endpoint: `GET /api/v1/analytics/git-branches`
2. Query parameters:
   - `time_range`: TimeRange enum
   - `project_id`: Optional project filter
   - `include_pattern`: Regex pattern for branch inclusion
   - `exclude_pattern`: Regex pattern for branch exclusion

3. Database aggregation:
   ```python
   # Group messages by gitBranch
   # Calculate per branch:
   #   - Total cost
   #   - Message count
   #   - Active days
   #   - Unique sessions
   #   - Most common operations
   # Identify branch lifecycle patterns
   # Compare feature vs main branch usage
   ```

4. Response schema:
   ```typescript
   {
     branches: [{
       name: string,
       type: 'main' | 'feature' | 'hotfix' | 'release' | 'other',
       metrics: {
         cost: number,
         messages: number,
         sessions: number,
         avg_session_cost: number,
         first_activity: string,
         last_activity: string,
         active_days: number
       },
       top_operations: [{
         operation: string,
         count: number
       }],
       cost_trend: number  // % change from previous period
     }],
     branch_comparisons: {
       main_vs_feature_cost_ratio: number,
       avg_feature_branch_lifetime_days: number,
       most_expensive_branch_type: string
     }
   }
   ```

### Frontend Implementation
1. Create components:
   - `BranchActivityChart.tsx` - Grouped bar chart
   - `BranchLifecycle.tsx` - Timeline visualization
   - `BranchComparison.tsx` - Comparison matrix

2. Features:
   - Grouped bar chart comparing branches
   - Timeline showing branch activity over time
   - Sunburst chart for branch hierarchy
   - Filter by branch patterns
   - Branch type auto-detection

### UI/UX Requirements
- Color-code branches by type (main, feature, etc.)
- Interactive branch selection
- Show branch merge indicators
- Cost allocation pie chart
- Export branch usage report

## Technical Considerations
- Handle null/missing gitBranch values
- Normalize branch names (strip remote prefix)
- Detect branch types from naming patterns
- Handle deleted/merged branches
- Privacy: Option to hash branch names

## Success Criteria
- Accurate branch type classification
- Clear visualization of resource allocation
- Help teams identify expensive branch patterns
- Support for repos with 1000+ branches
