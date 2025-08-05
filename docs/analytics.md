# ClaudeLens Analytics Documentation

This document provides a comprehensive overview of all analytics visualizations and metrics available in ClaudeLens, including their purpose, logic, and usefulness.

## Overview

ClaudeLens provides deep insights into Claude usage patterns through multiple analytics dimensions:
- **Usage Metrics**: Sessions, messages, costs, and model usage
- **Performance Analytics**: Response times and token usage patterns
- **Structural Analytics**: Conversation flow, depth, and branching patterns
- **Resource Analytics**: Git branch usage, directory insights, and tool usage
- **Real-time Monitoring**: Live session statistics with WebSocket updates

## Analytics Components

### 1. Summary Cards

**Purpose**: Provide at-a-glance overview of key metrics
**Location**: Top of analytics page

#### Overall Metrics (No session filter)
- **Total Sessions**: Count of all Claude sessions
- **Total Messages**: Sum of all messages across sessions
- **Total Cost**: Cumulative cost in USD
- **Most Used Model**: Model with highest message count

#### Session-specific Metrics (When session is selected)
- **Session Messages**: Message count for selected session
- **Session Cost**: Total cost for selected session
- **Tool Calls**: Number of tool invocations
- **Token Usage**: Total tokens consumed with cache hit rate

**Logic**: Aggregates data from MongoDB messages collection with time range filtering
**Usefulness**: ⭐⭐⭐⭐⭐ Essential for quick status checks and budget monitoring

### 2. Cost Over Time Chart

**Purpose**: Track spending patterns and identify cost spikes
**Type**: Line chart with daily/hourly granularity
**Metrics**:
- Cost per time period
- Message count correlation
- Trend visualization

**Logic**: Groups messages by timestamp, sums costs, and plots time series
**Usefulness**: ⭐⭐⭐⭐⭐ Critical for budget management and usage trend analysis

### 3. Model Usage Distribution

**Purpose**: Understand model preference and cost distribution
**Type**: Pie chart
**Metrics**:
- Message count per model
- Cost per model
- Percentage breakdown

**Logic**: Aggregates messages by model field, calculates proportions
**Usefulness**: ⭐⭐⭐⭐ Helps optimize model selection for cost/performance balance

### 4. Activity Heatmap

**Purpose**: Identify peak usage times and patterns
**Type**: 2D heatmap (day of week × hour of day)
**Metrics**:
- Message intensity by time slot
- Usage patterns visualization
- Timezone-aware display

**Logic**: Groups messages by day_of_week and hour, normalizes by max count
**Usefulness**: ⭐⭐⭐⭐ Valuable for understanding work patterns and scheduling

### 5. Conversation Flow Visualization

**Purpose**: Visualize conversation structure and branching
**Type**: Interactive node graph with React Flow
**Features**:
- User/Assistant message nodes
- Main flow vs sidechain distinction
- Cost, duration, and tool usage per node
- Search and filter capabilities
- Export to PNG

**Metrics**:
- Max depth
- Branch count
- Sidechain percentage
- Average branch length

**Logic**: Constructs tree from parent_id relationships, layouts with custom algorithm
**Usefulness**: ⭐⭐⭐⭐⭐ Excellent for understanding conversation complexity and optimization opportunities

### 6. Response Time Analytics

**Purpose**: Monitor and optimize Claude's response performance
**Type**: Multi-line chart with percentile bands
**Views**: By hour, day, model, or tool count
**Metrics**:
- Average response time
- P50, P90, P95, P99 percentiles
- Performance zones (fast <2s, normal 2-10s, slow >10s)

**Logic**: Calculates duration_ms statistics with percentile aggregation
**Usefulness**: ⭐⭐⭐⭐⭐ Critical for performance monitoring and SLA tracking

### 7. Token Usage Analytics

**Purpose**: Understand token consumption patterns
**Type**: Line chart with percentile visualization
**Metrics**:
- Average token usage over time
- P50, P90 percentiles
- Token efficiency metrics
- Cache hit rates

**Logic**: Aggregates input/output/cache tokens with time-based grouping
**Usefulness**: ⭐⭐⭐⭐ Important for cost optimization and capacity planning

### 8. Performance Factors Analysis

**Purpose**: Identify factors affecting response time and token usage
**Type**: Correlation matrix and factor analysis
**Factors Analyzed**:
- Model type impact
- Tool usage correlation
- Message length influence
- Time of day effects
- Conversation depth impact

**Logic**: Statistical correlation analysis between metrics
**Usefulness**: ⭐⭐⭐⭐ Valuable for understanding performance drivers

### 9. Session Depth Analytics

**Purpose**: Analyze conversation complexity patterns
**Components**:

#### Depth Histogram
- Distribution of sessions by maximum depth
- Average cost and messages per depth level
- Color gradient visualization

#### Depth Correlation
- Correlation between depth and cost/messages
- Identifies optimal conversation depth

#### Conversation Patterns
- Common conversation structures
- Branch patterns analysis
- Sidechain usage patterns

#### Depth Optimizer
- Recommendations for optimal depth
- Cost/benefit analysis
- Suggested depth limits

**Logic**: Analyzes message chains to calculate depths and patterns
**Usefulness**: ⭐⭐⭐⭐ Helps optimize conversation structure for efficiency

### 10. Git Branch Analytics

**Purpose**: Track Claude usage across development branches
**Components**:

#### Branch Activity Chart
- Bar chart of usage by branch
- Filterable by cost/messages/sessions
- Branch type categorization (main, feature, hotfix, release)
- Pattern-based filtering

#### Branch Lifecycle
- Average branch lifetime
- Activity timeline
- Cost accumulation over time

#### Branch Comparison
- Main vs feature branch ratio
- Most expensive branch type
- Cross-branch metrics comparison

**Logic**: Extracts git branch from session metadata, categorizes by naming patterns
**Usefulness**: ⭐⭐⭐⭐⭐ Essential for development teams tracking AI costs by feature

### 11. Directory Usage Insights

**Purpose**: Analyze AI resource usage by project structure
**Views**: Treemap or Explorer
**Metrics**: Cost, messages, or sessions by directory
**Features**:
- Interactive drill-down navigation
- Breadcrumb trail
- Percentage of total calculations
- Depth control (1-5 levels)

**Logic**: Aggregates messages by working directory path hierarchy
**Usefulness**: ⭐⭐⭐⭐ Excellent for identifying high-cost areas of codebase

### 12. Real-time Activity Monitor

**Purpose**: Live monitoring of active Claude sessions
**Type**: WebSocket-connected stat cards
**Metrics**:
- Messages (real-time count)
- Tools Used (live updates)
- Tokens (animated increments)
- Cost (live accumulation)

**Features**:
- Connection status indicator
- Smooth animations for updates
- Session-specific monitoring
- Automatic reconnection

**Logic**: WebSocket connection to backend for push updates
**Usefulness**: ⭐⭐⭐⭐⭐ Perfect for monitoring ongoing sessions and demos

### 13. Tool Usage Analytics

**Purpose**: Understand which tools Claude uses most
**Type**: Ranked list with percentages
**Metrics**:
- Tool call frequency
- Tool categories
- Usage percentage
- Session-specific filtering

**Logic**: Parses tool_use blocks from messages, aggregates by tool name
**Usefulness**: ⭐⭐⭐⭐ Helps understand Claude's problem-solving patterns

## Evaluation of Analytics Logic

### Strengths
1. **Comprehensive Coverage**: Covers cost, performance, structure, and usage dimensions
2. **Interactive Visualizations**: Most charts support drilling down and filtering
3. **Real-time Capabilities**: WebSocket integration for live monitoring
4. **Session Filtering**: Can view overall or session-specific analytics
5. **Time Range Flexibility**: All analytics support multiple time ranges
6. **Performance Optimized**: MongoDB aggregations with proper indexing

### Areas for Improvement
1. **Predictive Analytics**: Could add cost forecasting based on trends
2. **Anomaly Detection**: Automatic alerting for unusual patterns
3. **Custom Dashboards**: User-configurable analytics views
4. **Export Capabilities**: More formats beyond PNG (CSV, PDF reports)
5. **Comparison Tools**: Side-by-side session or time period comparisons

## Implementation Details

### Data Flow
1. Messages stored in MongoDB with rich metadata
2. Analytics API endpoints use aggregation pipelines
3. Frontend fetches data with React Query hooks
4. WebSocket server publishes real-time updates
5. Recharts and React Flow for visualizations

### Performance Considerations
- Indexes on timestamp, session_id, model, cost fields
- Aggregation pipelines optimized for common queries
- Client-side caching with React Query
- Lazy loading for heavy visualizations
- WebSocket connection pooling

## Best Practices for Users

1. **Regular Monitoring**: Check cost trends weekly to avoid surprises
2. **Session Filtering**: Use session-specific views for detailed analysis
3. **Time Range Selection**: Start broad, then narrow for specific insights
4. **Pattern Recognition**: Look for recurring high-cost patterns
5. **Performance Tracking**: Monitor response times during critical work
6. **Branch Analysis**: Review feature branch costs before merging
7. **Directory Insights**: Identify and optimize high-cost code areas

## Conclusion

ClaudeLens analytics provides a comprehensive, well-designed system for understanding Claude usage. The visualizations are thoughtfully chosen for their specific insights, with clear logic behind each metric. The combination of historical analysis and real-time monitoring makes it a powerful tool for both retrospective analysis and active session management.

The analytics are particularly strong in:
- Cost tracking and optimization
- Performance monitoring
- Development workflow integration (git branches)
- Real-time session monitoring
- Conversation structure analysis

Overall rating: ⭐⭐⭐⭐⭐ - A mature, well-implemented analytics platform that covers all essential aspects of Claude usage monitoring.
