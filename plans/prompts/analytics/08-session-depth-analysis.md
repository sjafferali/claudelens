# Session Depth Analysis Implementation

## Status: ✅ COMPLETED

### Implementation Summary:
- Backend endpoint created: `GET /api/v1/analytics/session-depth` with tree traversal algorithms
- Frontend components created: `DepthHistogram.tsx`, `DepthCorrelation.tsx`, `ConversationPatterns.tsx`, `DepthOptimizer.tsx`
- Recursive depth calculation from parentUuid relationships with cycle detection
- Depth metrics: max depth, average, distribution, branching factor
- Correlation analysis: depth vs cost/duration/success with Pearson coefficients
- Pattern identification: shallow-wide, deep-narrow, balanced, linear patterns
- Optimization recommendations with actionable tips and best practices

## Context
ClaudeLens tracks message relationships through `parentUuid`, enabling analysis of conversation complexity and depth patterns.

## Feature Description
Implement session depth analytics to understand conversation complexity, iteration patterns, and optimal conversation structures.

## Requirements

### Backend Implementation
1. Create endpoint: `GET /api/v1/analytics/session-depth`
2. Query parameters:
   - `time_range`: TimeRange enum
   - `project_id`: Optional project filter
   - `min_depth`: Minimum depth to include
   - `include_sidechains`: Include sidechain depth

3. Database aggregation:
   ```python
   # Build conversation trees for each session
   # Calculate depth metrics:
   #   - Maximum depth per session
   #   - Average depth
   #   - Depth distribution
   #   - Branching factor
   # Correlate depth with:
   #   - Session cost
   #   - Success outcomes
   #   - Task complexity
   # Identify optimal depth patterns
   ```

4. Response schema:
   ```typescript
   {
     depth_distribution: [{
       depth: number,
       session_count: number,
       avg_cost: number,
       avg_messages: number,
       percentage: number
     }],
     depth_correlations: {
       depth_vs_cost: number,
       depth_vs_duration: number,
       depth_vs_success: number
     },
     patterns: [{
       pattern_name: string,  // "shallow-wide", "deep-narrow", etc.
       frequency: number,
       avg_cost: number,
       typical_use_case: string
     }],
     recommendations: {
       optimal_depth_range: [number, number],
       warning_threshold: number,
       tips: string[]
     }
   }
   ```

### Frontend Implementation
1. Create components:
   - `DepthHistogram.tsx` - Distribution visualization
   - `DepthCorrelation.tsx` - Correlation scatter plots
   - `ConversationPatterns.tsx` - Pattern identification
   - `DepthOptimizer.tsx` - Optimization suggestions

2. Visualizations:
   - Histogram showing depth distribution
   - Scatter plots for correlations
   - Tree diagram examples of patterns
   - Heat map of depth vs outcomes

### UI/UX Requirements
- Color gradient for depth levels
- Interactive filtering by depth range
- Pattern recognition highlights
- Animated tree exploration
- Export depth analysis report

## Technical Considerations
- Efficient tree traversal algorithms
- Handle circular references
- Memory optimization for deep trees
- Real-time depth tracking
- Cache depth calculations

## Success Criteria
- Analyze sessions with up to 1000 messages efficiently
- Identify clear patterns in conversation depth
- Provide actionable insights for conversation optimization
- Demonstrate correlation between depth and outcomes
