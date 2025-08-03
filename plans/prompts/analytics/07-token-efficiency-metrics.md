# Token Efficiency Metrics Implementation

## Context
ClaudeLens can extract token usage from message metadata, including input/output tokens and cache utilization. This enables efficiency analysis and optimization.

## Feature Description
Implement token efficiency analytics showing token usage patterns, cache hit rates, and efficiency scores to help users optimize their Claude interactions.

## Requirements

### Backend Implementation
1. Create endpoints:
   - `GET /api/v1/analytics/token-efficiency`
   - `GET /api/v1/analytics/cache-performance`

2. Query parameters:
   - `time_range`: TimeRange enum
   - `group_by`: 'session' | 'project' | 'model'
   - `efficiency_metric`: 'tokens_per_task' | 'cache_hit_rate' | 'reuse_rate'

3. Database aggregation:
   ```python
   # Extract token counts from metadata
   # Calculate efficiency metrics:
   #   - Tokens per completed task
   #   - Cache hit rate (cache_read / total)
   #   - Token reuse efficiency
   #   - Input/output token ratio
   # Identify optimization opportunities
   # Track efficiency trends over time
   ```

4. Response schemas:
   ```typescript
   // Token efficiency
   {
     efficiency_scores: {
       overall: number,  // 0-100 score
       tokens_per_task: number,
       cache_hit_rate: number,
       input_output_ratio: number,
       context_reuse_rate: number
     },
     breakdowns: [{
       category: string,
       input_tokens: number,
       output_tokens: number,
       cache_creation_tokens: number,
       cache_read_tokens: number,
       total_tokens: number,
       efficiency_score: number
     }],
     optimization_suggestions: [{
       type: string,
       potential_savings: number,
       description: string,
       impact: 'high' | 'medium' | 'low'
     }]
   }

   // Cache performance
   {
     cache_metrics: {
       total_cache_hits: number,
       total_cache_misses: number,
       hit_rate: number,
       tokens_saved: number,
       cost_saved: number
     },
     time_series: [{
       timestamp: string,
       hit_rate: number,
       tokens_saved: number
     }]
   }
   ```

### Frontend Implementation
1. Create components:
   - `TokenEfficiencyGauge.tsx` - Efficiency score gauges
   - `TokenBreakdownChart.tsx` - Token type distribution
   - `CachePerformance.tsx` - Cache hit visualization
   - `OptimizationTips.tsx` - Actionable recommendations

2. Visualizations:
   - Gauge charts for efficiency scores
   - Stacked bar chart for token breakdown
   - Line chart for cache hit rate trends
   - Savings calculator showing potential optimizations

### UI/UX Requirements
- Traffic light coloring for efficiency scores
- Animated gauge needles
- Hover details on token breakdowns
- Before/after optimization preview
- Export efficiency report

## Technical Considerations
- Handle various token metadata formats
- Calculate meaningful efficiency scores
- Account for different task complexities
- Provide context-aware suggestions
- Cache efficiency calculations

## Success Criteria
- Accurate token counting and categorization
- Meaningful efficiency scores that drive action
- Clear optimization recommendations
- Measurable improvement in token usage after implementing suggestions
