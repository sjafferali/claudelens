# Response Time Analytics Implementation

## Context
ClaudeLens tracks response duration in the `durationMs` field for assistant messages, enabling performance analysis and optimization insights.

## Feature Description
Implement comprehensive response time analytics with percentile tracking, performance trends, and factors affecting response times.

## Requirements

### Backend Implementation
1. Create endpoints:
   - `GET /api/v1/analytics/response-times`
   - `GET /api/v1/analytics/performance-factors`

2. Query parameters:
   - `time_range`: TimeRange enum
   - `percentiles`: Array of percentiles to calculate (default: [50, 90, 95, 99])
   - `group_by`: 'hour' | 'day' | 'model' | 'tool_count'

3. Database aggregation:
   ```python
   # Calculate response time percentiles
   # Analyze factors affecting response time:
   #   - Message length
   #   - Tool usage count
   #   - Time of day
   #   - Model type
   #   - Conversation depth
   # Identify performance outliers
   # Track performance trends
   ```

4. Response schemas:
   ```typescript
   // Response times
   {
     percentiles: {
       p50: number,
       p90: number,
       p95: number,
       p99: number
     },
     time_series: [{
       timestamp: string,
       avg_duration_ms: number,
       p50: number,
       p90: number,
       message_count: number
     }],
     distribution: [{
       bucket: string,  // "0-1s", "1-5s", etc.
       count: number,
       percentage: number
     }]
   }

   // Performance factors
   {
     correlations: [{
       factor: string,
       correlation_strength: number,
       impact_ms: number,
       sample_size: number
     }],
     recommendations: string[]
   }
   ```

### Frontend Implementation
1. Create components:
   - `ResponseTimeChart.tsx` - Main performance chart
   - `PercentileRibbon.tsx` - Percentile visualization
   - `PerformanceFactors.tsx` - Factor analysis display

2. Visualizations:
   - Line chart with percentile bands (p50, p90, p99)
   - Histogram showing response time distribution
   - Scatter plot correlating factors with response time
   - Performance score gauge

### UI/UX Requirements
- Color-coded performance zones (fast/normal/slow)
- Animated transitions between time ranges
- Highlight outliers and anomalies
- Comparative view (this period vs last period)
- Performance tips based on data

## Technical Considerations
- Efficient percentile calculation for large datasets
- Handle missing durationMs values
- Account for network latency vs processing time
- Real-time performance monitoring option
- Cache percentile calculations

## Success Criteria
- Accurate percentile calculations within 100ms
- Clear visualization of performance trends
- Actionable insights for performance improvement
- Support for analyzing millions of messages
