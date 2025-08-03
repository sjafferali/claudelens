# Error and Success Rate Tracking Implementation

## Context
ClaudeLens captures tool execution results in the `toolUseResult` field, allowing tracking of success and failure patterns across different tools and contexts.

## Feature Description
Implement comprehensive error tracking and success rate analytics to help users identify problematic patterns and improve their Claude interactions.

## Requirements

### Backend Implementation
1. Create endpoints:
   - `GET /api/v1/analytics/error-rates`
   - `GET /api/v1/analytics/error-patterns`

2. Query parameters:
   - `time_range`: TimeRange enum
   - `group_by`: 'tool' | 'project' | 'hour' | 'day'
   - `error_type`: Optional filter by error category

3. Database aggregation:
   ```python
   # Parse toolUseResult for error indicators
   # Categorize errors (syntax, permission, network, timeout, etc.)
   # Calculate success/failure rates per tool
   # Identify error patterns and correlations
   # Track error frequency over time
   ```

4. Response schemas:
   ```typescript
   // Error rates
   {
     metrics: [{
       group: string,
       total_executions: number,
       success_count: number,
       error_count: number,
       success_rate: number,
       common_errors: [{
         type: string,
         count: number,
         example: string
       }]
     }],
     time_series: [{
       timestamp: string,
       success_rate: number,
       error_count: number
     }]
   }

   // Error patterns
   {
     patterns: [{
       pattern_type: string,
       frequency: number,
       affected_tools: string[],
       correlation_factors: {
         time_of_day?: string,
         file_size?: string,
         directory?: string
       },
       suggested_fix: string
     }]
   }
   ```

### Frontend Implementation
1. Create components:
   - `ErrorRateDashboard.tsx` - Main dashboard
   - `ErrorTimeline.tsx` - Time-series visualization
   - `ErrorPatternAnalyzer.tsx` - Pattern detection UI

2. Visualizations:
   - Stacked area chart for success/error rates over time
   - Heat map showing error concentration by tool and time
   - Error type distribution pie chart
   - Alert cards for critical error patterns

### UI/UX Requirements
- Red/green color coding for error/success
- Expandable error details with stack traces
- Quick filters for common error types
- Export error logs functionality
- Real-time error notifications (optional)

## Technical Considerations
- Efficient error parsing from varied toolUseResult formats
- Handle missing or malformed error data
- Privacy: Sanitize sensitive information from error messages
- Set up error alerting thresholds

## Success Criteria
- Accurately categorize 95% of errors
- Identify recurring error patterns
- Provide actionable insights for error reduction
- Sub-second query performance for error analytics
