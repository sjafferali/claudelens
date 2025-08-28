"""Analytics API endpoints."""

from typing import Any

from fastapi import HTTPException, Query

from app.api.dependencies import AuthDeps, CommonDeps
from app.core.custom_router import APIRouter
from app.schemas.analytics import (
    ActivityHeatmap,
    AnalyticsSummary,
    BenchmarkEntityType,
    BenchmarkResponse,
    ConversationFlowAnalytics,
    CostAnalytics,
    CostBreakdownResponse,
    CostPrediction,
    CostSummary,
    CreateBenchmarkRequest,
    DirectoryUsageResponse,
    ErrorDetailsResponse,
    GitBranchAnalyticsResponse,
    ModelUsageStats,
    NormalizationMethod,
    SessionDepthAnalytics,
    SessionHealth,
    SuccessRateMetrics,
    TimeRange,
    TokenAnalytics,
    TokenEfficiencyDetailed,
    TokenEfficiencySummary,
    TokenUsageStats,
    ToolUsageDetailed,
    ToolUsageSummary,
    TopicExtractionResponse,
    TopicSuggestionResponse,
)
from app.services.analytics import AnalyticsService

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    db: CommonDeps,
    user_id: AuthDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
) -> AnalyticsSummary:
    """Get overall analytics summary.

    Returns high-level metrics including total messages, costs,
    active projects, and usage trends.
    """
    service = AnalyticsService(db, user_id=user_id)
    return await service.get_summary(time_range)


@router.get("/activity/heatmap", response_model=ActivityHeatmap)
async def get_activity_heatmap(
    db: CommonDeps,
    user_id: AuthDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    timezone: str = Query("UTC", description="Timezone for aggregation"),
) -> ActivityHeatmap:
    """Get activity heatmap data.

    Returns message counts aggregated by hour and day of week,
    useful for visualizing usage patterns.
    """
    service = AnalyticsService(db, user_id=user_id)
    return await service.get_activity_heatmap(time_range, timezone)


@router.get("/costs", response_model=CostAnalytics)
async def get_cost_analytics(
    db: CommonDeps,
    user_id: AuthDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    group_by: str = Query("day", pattern="^(hour|day|week|month)$"),
    project_id: str | None = Query(None),
) -> CostAnalytics:
    """Get cost analytics over time.

    Returns cost data grouped by the specified time period,
    optionally filtered by project.
    """
    service = AnalyticsService(db, user_id=user_id)
    return await service.get_cost_analytics(time_range, group_by, project_id)


@router.get("/models/usage", response_model=ModelUsageStats)
async def get_model_usage(
    db: CommonDeps,
    user_id: AuthDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    project_id: str | None = Query(None),
) -> ModelUsageStats:
    """Get model usage statistics.

    Returns usage data for each Claude model including message counts,
    costs, and average response times.
    """
    service = AnalyticsService(db, user_id=user_id)
    return await service.get_model_usage(time_range, project_id)


@router.get("/tokens", response_model=TokenUsageStats)
async def get_token_usage(
    db: CommonDeps,
    user_id: AuthDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    group_by: str = Query("day", pattern="^(hour|day|week|month)$"),
) -> TokenUsageStats:
    """Get token usage statistics.

    Returns input and output token counts over time.
    """
    service = AnalyticsService(db, user_id=user_id)
    return await service.get_token_usage(time_range, group_by)


@router.get("/projects/comparison")
async def compare_projects(
    db: CommonDeps,
    user_id: AuthDeps,
    project_ids: list[str] = Query(..., description="Project IDs to compare"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
) -> dict[str, Any]:
    """Compare analytics across multiple projects.

    Returns comparative metrics for the specified projects.
    """
    if len(project_ids) < 2 or len(project_ids) > 10:
        raise HTTPException(
            status_code=400, detail="Please provide between 2 and 10 project IDs"
        )

    service = AnalyticsService(db, user_id=user_id)
    return await service.compare_projects(project_ids, time_range)


@router.get("/trends")
async def get_usage_trends(
    db: CommonDeps,
    user_id: AuthDeps,
    time_range: TimeRange = Query(TimeRange.LAST_90_DAYS),
    metric: str = Query("messages", pattern="^(messages|costs|sessions)$"),
) -> dict[str, Any]:
    """Get usage trends over time.

    Analyzes trends and provides insights on usage patterns.
    """
    service = AnalyticsService(db, user_id=user_id)
    return await service.analyze_trends(time_range, metric)


@router.get("/tools/summary", response_model=ToolUsageSummary)
async def get_tool_usage_summary(
    db: CommonDeps,
    user_id: AuthDeps,
    session_id: str | None = Query(None),
    project_id: str | None = Query(None),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
) -> ToolUsageSummary:
    """Get tool usage summary for stat card display.

    Returns total tool calls, unique tools count, and most used tool.
    """
    service = AnalyticsService(db, user_id=user_id)
    return await service.get_tool_usage_summary(session_id, project_id, time_range)


@router.get("/tools/detailed", response_model=ToolUsageDetailed)
async def get_tool_usage_detailed(
    db: CommonDeps,
    user_id: AuthDeps,
    session_id: str | None = Query(None),
    project_id: str | None = Query(None),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
) -> ToolUsageDetailed:
    """Get detailed tool usage analytics for details panel.

    Returns individual tools with counts, percentages, categories, and last used timestamps.
    """
    service = AnalyticsService(db, user_id=user_id)
    return await service.get_tool_usage_detailed(session_id, project_id, time_range)


@router.get("/conversation-flow", response_model=ConversationFlowAnalytics)
async def get_conversation_flow(
    db: CommonDeps,
    user_id: AuthDeps,
    session_id: str = Query(..., description="Session ID to analyze"),
    include_sidechains: bool = Query(
        True, description="Include sidechain conversations"
    ),
) -> ConversationFlowAnalytics:
    """Get conversation flow analytics for visualization.

    Returns conversation tree structure with nodes, edges, and metrics
    for interactive flow visualization.
    """
    service = AnalyticsService(db)
    return await service.get_conversation_flow(session_id, include_sidechains)


@router.get("/session/health", response_model=SessionHealth)
async def get_session_health(
    db: CommonDeps,
    user_id: AuthDeps,
    session_id: str | None = Query(None, description="Filter by specific session"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
) -> SessionHealth:
    """Get session health metrics for stat card display.

    Returns success rate, total operations, error count, and health status
    based on tool execution results.
    """
    service = AnalyticsService(db)
    return await service.get_session_health(session_id, time_range)


@router.get("/errors/detailed", response_model=ErrorDetailsResponse)
async def get_detailed_errors(
    db: CommonDeps,
    user_id: AuthDeps,
    session_id: str | None = Query(None, description="Filter by specific session"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    error_severity: str
    | None = Query(
        None,
        pattern="^(critical|warning|info)$",
        description="Filter by error severity",
    ),
) -> ErrorDetailsResponse:
    """Get detailed error analytics for details panel.

    Returns individual errors with timestamps, tools, types, severity levels,
    and summary statistics grouped by type and tool.
    """
    service = AnalyticsService(db)
    return await service.get_detailed_errors(session_id, time_range, error_severity)


@router.get("/success-rate", response_model=SuccessRateMetrics)
async def get_success_rate(
    db: CommonDeps,
    user_id: AuthDeps,
    session_id: str | None = Query(None, description="Filter by specific session"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
) -> SuccessRateMetrics:
    """Get success rate metrics.

    Returns overall success rate percentages and operation counts
    based on tool execution results analysis.
    """
    service = AnalyticsService(db)
    return await service.get_success_rate(session_id, time_range)


@router.get("/directory-usage", response_model=DirectoryUsageResponse)
async def get_directory_usage(
    db: CommonDeps,
    user_id: AuthDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    depth: int = Query(
        3, ge=1, le=10, description="Maximum directory depth to analyze"
    ),
    min_cost: float = Query(
        0.0, ge=0.0, description="Minimum cost threshold to include directory"
    ),
) -> DirectoryUsageResponse:
    """Get directory usage analytics with hierarchical tree structure.

    Returns resource usage (costs, messages, sessions) broken down by directory hierarchy,
    useful for identifying which projects and directories consume the most AI resources.
    """
    service = AnalyticsService(db)
    return await service.get_directory_usage(time_range, depth, min_cost)


@router.get("/token-analytics", response_model=TokenAnalytics)
async def get_token_analytics(
    db: CommonDeps,
    user_id: AuthDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    percentiles: list[int]
    | None = Query(
        None, description="Percentiles to calculate (default: [50, 90, 95, 99])"
    ),
    group_by: str = Query(
        "hour", pattern="^(hour|day|model)$", description="Grouping method"
    ),
) -> TokenAnalytics:
    """Get token usage analytics with percentiles and distribution.

    Returns token usage percentiles, time series data, and distribution buckets
    for analyzing token consumption patterns and efficiency.
    """
    if percentiles is None:
        percentiles = [50, 90, 95, 99]

    service = AnalyticsService(db)
    return await service.get_token_analytics(time_range, percentiles, group_by)


@router.get("/git-branches", response_model=GitBranchAnalyticsResponse)
async def get_git_branch_analytics(
    db: CommonDeps,
    user_id: AuthDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    project_id: str | None = Query(None, description="Filter by project ID"),
    include_pattern: str
    | None = Query(None, description="Regex pattern for branch inclusion"),
    exclude_pattern: str
    | None = Query(None, description="Regex pattern for branch exclusion"),
) -> GitBranchAnalyticsResponse:
    """Get git branch analytics.

    Returns analytics showing how Claude usage varies across git branches,
    helping teams understand resource allocation in their development workflow.
    """
    service = AnalyticsService(db)
    return await service.get_git_branch_analytics(
        time_range, project_id, include_pattern, exclude_pattern
    )


@router.get("/tokens/summary", response_model=TokenEfficiencySummary)
async def get_token_efficiency_summary(
    db: CommonDeps,
    user_id: AuthDeps,
    session_id: str | None = Query(None, description="Filter by specific session"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    include_cache_metrics: bool = Query(
        True, description="Include cache token metrics"
    ),
) -> TokenEfficiencySummary:
    """Get token efficiency summary for stat card display.

    Returns total token count with smart formatting, cost estimate,
    and trend information for display in the stat grid.
    """
    service = AnalyticsService(db)
    return await service.get_token_efficiency_summary(
        session_id, time_range, include_cache_metrics
    )


@router.get("/tokens/detailed", response_model=TokenEfficiencyDetailed)
async def get_token_efficiency_detailed(
    db: CommonDeps,
    user_id: AuthDeps,
    session_id: str | None = Query(None, description="Filter by specific session"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    include_cache_metrics: bool = Query(
        True, description="Include cache token metrics"
    ),
) -> TokenEfficiencyDetailed:
    """Get detailed token efficiency analytics for details panel.

    Returns comprehensive token breakdown by type (input, output, cache),
    efficiency metrics, and formatted values for visualization.
    """
    service = AnalyticsService(db)
    return await service.get_token_efficiency_detailed(
        session_id, time_range, include_cache_metrics
    )


@router.get("/session-depth", response_model=SessionDepthAnalytics)
async def get_session_depth_analytics(
    db: CommonDeps,
    user_id: AuthDeps,
    time_range: TimeRange = Query(
        TimeRange.LAST_30_DAYS, description="Time range for analysis"
    ),
    project_id: str | None = Query(None, description="Filter by project ID"),
    min_depth: int = Query(0, ge=0, description="Minimum depth to include in analysis"),
    include_sidechains: bool = Query(
        True, description="Include sidechain depth in analysis"
    ),
) -> SessionDepthAnalytics:
    """Get session depth analytics.

    Analyzes conversation complexity through depth patterns, identifying
    optimal conversation structures and providing optimization recommendations.

    Returns depth distribution, correlations with cost/duration/success,
    conversation patterns, and actionable insights for improving conversation efficiency.
    """
    service = AnalyticsService(db)
    return await service.get_session_depth_analytics(
        time_range, project_id, min_depth, include_sidechains
    )


# Cost Prediction Dashboard Endpoints


@router.get("/cost/summary", response_model=CostSummary)
async def get_cost_summary(
    db: CommonDeps,
    user_id: AuthDeps,
    session_id: str | None = Query(None, description="Filter by specific session"),
    project_id: str | None = Query(None, description="Filter by project"),
    time_range: TimeRange = Query(
        TimeRange.LAST_30_DAYS, description="Time range for analysis"
    ),
) -> CostSummary:
    """Get cost summary for stat card display.

    Returns total cost with formatted display string, currency, trend information,
    and time period for display in the cost stat card.
    """
    service = AnalyticsService(db)
    return await service.get_cost_summary(session_id, project_id, time_range)


@router.get("/cost/breakdown", response_model=CostBreakdownResponse)
async def get_cost_breakdown(
    db: CommonDeps,
    user_id: AuthDeps,
    session_id: str | None = Query(None, description="Filter by specific session"),
    project_id: str | None = Query(None, description="Filter by project"),
    time_range: TimeRange = Query(
        TimeRange.LAST_30_DAYS, description="Time range for analysis"
    ),
) -> CostBreakdownResponse:
    """Get detailed cost breakdown for analytics panels.

    Returns cost breakdown by model and time, along with efficiency metrics
    like average cost per message, most expensive model, and cost efficiency score.
    """
    service = AnalyticsService(db)
    return await service.get_cost_breakdown(session_id, project_id, time_range)


@router.get("/cost/prediction", response_model=CostPrediction)
async def get_cost_prediction(
    db: CommonDeps,
    user_id: AuthDeps,
    session_id: str | None = Query(None, description="Filter by specific session"),
    project_id: str | None = Query(None, description="Filter by project"),
    prediction_days: int = Query(
        7, ge=1, le=365, description="Number of days to predict (7, 14, 30)"
    ),
) -> CostPrediction:
    """Get cost forecasting predictions.

    Returns cost predictions for the specified number of days based on historical data,
    including confidence intervals and model accuracy metrics.
    """
    service = AnalyticsService(db)
    return await service.get_cost_prediction(session_id, project_id, prediction_days)


# Topic Extraction and Classification Endpoints


@router.get("/topics/extract", response_model=TopicExtractionResponse)
async def extract_session_topics(
    db: CommonDeps,
    user_id: AuthDeps,
    session_id: str = Query(..., description="Session ID to extract topics from"),
    confidence_threshold: float = Query(
        0.3, ge=0.0, le=1.0, description="Minimum confidence threshold for topics"
    ),
) -> TopicExtractionResponse:
    """Extract topics from a session's messages and tool usage.

    Analyzes message content, file extensions, tool usage patterns, and framework mentions
    to automatically classify session topics across predefined categories:
    - Web Development, API Integration, Data Visualization, Machine Learning,
    - Database Operations, DevOps/Deployment, Testing/QA, Documentation

    Returns extracted topics with confidence scores and suggested related topics.
    """
    service = AnalyticsService(db)
    return await service.extract_session_topics(session_id, confidence_threshold)


@router.get("/topics/suggest", response_model=TopicSuggestionResponse)
async def get_topic_suggestions(
    db: CommonDeps,
    user_id: AuthDeps,
    time_range: TimeRange = Query(
        TimeRange.LAST_30_DAYS, description="Time range for topic analysis"
    ),
) -> TopicSuggestionResponse:
    """Get popular topics and topic combinations across sessions.

    Returns trending topics, topic frequency statistics, and common topic combinations
    to help users understand usage patterns and discover related topics.
    """
    service = AnalyticsService(db)
    return await service.get_topic_suggestions(time_range)


# Performance Benchmarking Endpoints


@router.get("/benchmarks", response_model=BenchmarkResponse)
async def get_benchmarks(
    db: CommonDeps,
    user_id: AuthDeps,
    entity_type: BenchmarkEntityType = Query(
        ..., description="Type of entities to benchmark"
    ),
    entity_ids: list[str] = Query(
        ..., description="Entity IDs to compare (2-20 items)"
    ),
    time_range: TimeRange = Query(
        TimeRange.LAST_30_DAYS, description="Time range for analysis"
    ),
    normalization_method: NormalizationMethod = Query(
        NormalizationMethod.Z_SCORE, description="Normalization method"
    ),
    include_percentile_ranks: bool = Query(
        True, description="Include percentile rankings"
    ),
) -> BenchmarkResponse:
    """Get performance benchmarks for specified entities.

    Compares performance across multiple entities (projects, teams, or time periods)
    using multi-dimensional analysis including cost efficiency, speed, quality,
    productivity, and complexity handling metrics.

    Returns normalized scores, percentile rankings, comparison matrix, and insights.
    """
    if len(entity_ids) < 2 or len(entity_ids) > 20:
        raise HTTPException(
            status_code=400,
            detail="Please provide between 2 and 20 entity IDs for comparison",
        )

    service = AnalyticsService(db)
    return await service.get_benchmarks(
        entity_type,
        entity_ids=entity_ids,
        time_range=time_range,
        normalization_method=normalization_method,
        include_percentile_ranks=include_percentile_ranks,
    )


@router.post("/create-benchmark", response_model=BenchmarkResponse)
async def create_benchmark(
    db: CommonDeps,
    user_id: AuthDeps,
    request: CreateBenchmarkRequest,
) -> BenchmarkResponse:
    """Create a new benchmark analysis.

    Alternative endpoint that accepts a POST request body for creating benchmarks.
    Useful for complex benchmark configurations or when entity IDs list is large.
    """
    service = AnalyticsService(db)
    return await service.get_benchmarks(
        request.entity_type,
        entity_ids=request.entity_ids,
        time_range=request.time_range,
        normalization_method=request.normalization_method,
        include_percentile_ranks=request.include_percentile_ranks,
    )


@router.get("/benchmark-comparison", response_model=BenchmarkResponse)
async def get_benchmark_comparison(
    db: CommonDeps,
    user_id: AuthDeps,
    primary_entity_id: str = Query(
        ..., description="Primary entity to compare against"
    ),
    comparison_entity_ids: list[str] = Query(
        ..., description="Entities to compare with"
    ),
    entity_type: BenchmarkEntityType = Query(..., description="Type of entities"),
    time_range: TimeRange = Query(
        TimeRange.LAST_30_DAYS, description="Time range for analysis"
    ),
    metrics_to_compare: list[str]
    | None = Query(None, description="Specific metrics to compare"),
) -> BenchmarkResponse:
    """Get focused benchmark comparison against a primary entity.

    Compares one primary entity against multiple comparison entities,
    with optional filtering to specific metrics for targeted analysis.
    """
    if len(comparison_entity_ids) < 1 or len(comparison_entity_ids) > 10:
        raise HTTPException(
            status_code=400,
            detail="Please provide between 1 and 10 comparison entity IDs",
        )

    service = AnalyticsService(db)

    return await service.get_benchmark_comparison(
        primary_entity_id,
        comparison_entity_ids=comparison_entity_ids,
        entity_type=entity_type,
        time_range=time_range,
        metrics_to_compare=metrics_to_compare,
    )
