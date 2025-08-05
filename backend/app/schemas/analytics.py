"""Analytics schemas."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TimeRange(str, Enum):
    """Predefined time ranges for analytics."""

    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    LAST_YEAR = "1y"
    ALL_TIME = "all"


class AnalyticsSummary(BaseModel):
    """Overall analytics summary."""

    total_messages: int
    total_sessions: int
    total_projects: int
    total_cost: float

    messages_trend: float = Field(
        ..., description="Percentage change from previous period"
    )
    cost_trend: float = Field(..., description="Percentage change from previous period")

    most_active_project: str | None = None
    most_used_model: str | None = None

    time_range: TimeRange
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class HeatmapCell(BaseModel):
    """Single cell in activity heatmap."""

    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    hour: int = Field(..., ge=0, le=23)
    count: int = Field(..., ge=0)

    # Optional enrichment
    avg_cost: float | None = None
    avg_response_time: float | None = None


class ActivityHeatmap(BaseModel):
    """Activity heatmap data."""

    cells: list[HeatmapCell]
    total_messages: int
    time_range: TimeRange
    timezone: str

    # Peak activity times
    peak_hour: int | None = None
    peak_day: int | None = None


class CostDataPoint(BaseModel):
    """Cost data point in time series."""

    timestamp: datetime
    cost: float
    message_count: int

    # Breakdown by model
    cost_by_model: dict[str, float] | None = None


class CostAnalytics(BaseModel):
    """Cost analytics over time."""

    data_points: list[CostDataPoint]
    total_cost: float
    average_cost_per_message: float

    time_range: TimeRange
    group_by: str

    # Cost breakdown
    cost_by_model: dict[str, float]
    cost_by_project: dict[str, float] | None = None


class ModelUsage(BaseModel):
    """Usage statistics for a single model."""

    model: str
    message_count: int
    total_cost: float
    avg_cost_per_message: float

    avg_response_time_ms: float | None = None
    avg_tokens_input: float | None = None
    avg_tokens_output: float | None = None

    # Usage trend
    trend_percentage: float | None = None


class ModelUsageStats(BaseModel):
    """Model usage statistics."""

    models: list[ModelUsage]
    total_models: int
    time_range: TimeRange

    # Most/least used
    most_used: str | None = None
    least_used: str | None = None


class TokenDataPoint(BaseModel):
    """Token usage data point."""

    timestamp: datetime
    input_tokens: int
    output_tokens: int
    total_tokens: int


class TokenUsageStats(BaseModel):
    """Token usage statistics."""

    data_points: list[TokenDataPoint]
    total_input_tokens: int
    total_output_tokens: int

    avg_input_tokens_per_message: float
    avg_output_tokens_per_message: float

    time_range: TimeRange
    group_by: str


class ToolUsageSummary(BaseModel):
    """Tool usage summary for stat card."""

    total_tool_calls: int
    unique_tools: int
    most_used_tool: str | None = None


class ToolUsage(BaseModel):
    """Individual tool usage statistics."""

    name: str
    count: int
    percentage: float
    category: str = Field(
        ..., description="Tool category: file, search, execution, or other"
    )
    last_used: datetime


class ToolUsageDetailed(BaseModel):
    """Detailed tool usage analytics."""

    tools: list[ToolUsage]
    total_calls: int
    session_id: str | None = None
    time_range: TimeRange


class ConversationFlowNode(BaseModel):
    """Node in conversation flow visualization."""

    id: str = Field(..., description="Message UUID")
    parent_id: str | None = Field(None, description="Parent message UUID")
    type: str = Field(..., description="Message type: user or assistant")
    is_sidechain: bool = Field(False, description="Whether this is a sidechain message")
    cost: float = Field(0.0, description="Cost in USD for this message")
    duration_ms: int | None = Field(None, description="Response time in milliseconds")
    tool_count: int = Field(0, description="Number of tools used in this message")
    summary: str = Field("", description="Brief summary of the message content")
    timestamp: datetime = Field(..., description="Message timestamp")


class ConversationFlowEdge(BaseModel):
    """Edge in conversation flow visualization."""

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Edge type: main or sidechain")


class ConversationFlowMetrics(BaseModel):
    """Metrics for conversation flow."""

    max_depth: int = Field(0, description="Maximum conversation depth")
    branch_count: int = Field(0, description="Number of conversation branches")
    sidechain_percentage: float = Field(
        0.0, description="Percentage of messages that are sidechains"
    )
    avg_branch_length: float = Field(
        0.0, description="Average length of conversation branches"
    )
    total_nodes: int = Field(0, description="Total number of nodes in the flow")
    total_cost: float = Field(0.0, description="Total cost across all messages")
    avg_response_time_ms: float | None = Field(
        None, description="Average response time"
    )


class ConversationFlowAnalytics(BaseModel):
    """Complete conversation flow analytics response."""

    nodes: list[ConversationFlowNode]
    edges: list[ConversationFlowEdge]
    metrics: ConversationFlowMetrics
    session_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Error and Success Rate Tracking Schemas


class SessionHealth(BaseModel):
    """Session health metrics for stat card display."""

    success_rate: float = Field(
        ..., ge=0.0, le=100.0, description="Success rate percentage"
    )
    total_operations: int = Field(..., ge=0, description="Total tool operations")
    error_count: int = Field(..., ge=0, description="Number of errors")
    health_status: str = Field(
        ..., description="Health status: excellent, good, fair, or poor"
    )


class ErrorDetail(BaseModel):
    """Individual error detail."""

    timestamp: datetime = Field(..., description="When the error occurred")
    tool: str = Field(..., description="Tool that caused the error")
    error_type: str = Field(..., description="Type/category of error")
    severity: str = Field(..., description="Error severity: critical, warning, or info")
    message: str = Field(..., description="Error message")
    context: str = Field("", description="Additional context about the error")


class ErrorSummary(BaseModel):
    """Summary of errors by type and tool."""

    by_type: dict[str, int] = Field(
        default_factory=dict, description="Error counts by type"
    )
    by_tool: dict[str, int] = Field(
        default_factory=dict, description="Error counts by tool"
    )


class ErrorDetailsResponse(BaseModel):
    """Detailed errors response for panel display."""

    errors: list[ErrorDetail] = Field(
        default_factory=list, description="List of errors"
    )
    error_summary: ErrorSummary = Field(
        default_factory=ErrorSummary, description="Error summary statistics"
    )


class SuccessRateMetrics(BaseModel):
    """Success rate metrics response."""

    success_rate: float = Field(
        ..., ge=0.0, le=100.0, description="Overall success rate percentage"
    )
    total_operations: int = Field(..., ge=0, description="Total operations counted")
    successful_operations: int = Field(
        ..., ge=0, description="Number of successful operations"
    )
    failed_operations: int = Field(..., ge=0, description="Number of failed operations")
    time_range: TimeRange = Field(..., description="Time range for the metrics")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Directory Usage Analytics Schemas


class DirectoryMetrics(BaseModel):
    """Metrics for a directory."""

    cost: float = Field(..., ge=0, description="Total cost in USD")
    messages: int = Field(..., ge=0, description="Number of messages")
    sessions: int = Field(..., ge=0, description="Number of unique sessions")
    avg_cost_per_session: float = Field(
        ..., ge=0, description="Average cost per session"
    )
    last_active: datetime = Field(..., description="Last activity timestamp")


class DirectoryNode(BaseModel):
    """Node in directory tree structure."""

    path: str = Field(..., description="Full directory path")
    name: str = Field(..., description="Directory name")
    metrics: DirectoryMetrics = Field(..., description="Directory metrics")
    children: list["DirectoryNode"] = Field(
        default_factory=list, description="Child directories"
    )
    percentage_of_total: float = Field(
        ..., ge=0, le=100, description="Percentage of total cost"
    )


class DirectoryTotalMetrics(BaseModel):
    """Total metrics across all directories."""

    total_cost: float = Field(
        ..., ge=0, description="Total cost across all directories"
    )
    total_messages: int = Field(..., ge=0, description="Total messages")
    unique_directories: int = Field(
        ..., ge=0, description="Number of unique directories"
    )


class DirectoryUsageResponse(BaseModel):
    """Response for directory usage analytics."""

    root: DirectoryNode = Field(..., description="Root directory node")
    total_metrics: DirectoryTotalMetrics = Field(..., description="Total metrics")
    time_range: TimeRange = Field(..., description="Time range for the analysis")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Response Time Analytics Schemas


class ResponseTimePercentiles(BaseModel):
    """Response time percentiles."""

    p50: float = Field(..., description="50th percentile (median) response time in ms")
    p90: float = Field(..., description="90th percentile response time in ms")
    p95: float = Field(..., description="95th percentile response time in ms")
    p99: float = Field(..., description="99th percentile response time in ms")


class ResponseTimeDataPoint(BaseModel):
    """Response time data point in time series."""

    timestamp: datetime = Field(..., description="Data point timestamp")
    avg_duration_ms: float = Field(..., description="Average response time in ms")
    p50: float = Field(..., description="50th percentile response time in ms")
    p90: float = Field(..., description="90th percentile response time in ms")
    message_count: int = Field(
        ..., ge=0, description="Number of messages in this time bucket"
    )


class DistributionBucket(BaseModel):
    """Response time distribution bucket."""

    bucket: str = Field(..., description="Bucket range (e.g., '0-1s', '1-5s')")
    count: int = Field(..., ge=0, description="Number of messages in this bucket")
    percentage: float = Field(
        ..., ge=0, le=100, description="Percentage of total messages"
    )


class ResponseTimeAnalytics(BaseModel):
    """Response time analytics response."""

    percentiles: ResponseTimePercentiles = Field(
        ..., description="Overall percentiles for the time range"
    )
    time_series: list[ResponseTimeDataPoint] = Field(
        ..., description="Time series data"
    )
    distribution: list[DistributionBucket] = Field(
        ..., description="Response time distribution"
    )
    time_range: TimeRange = Field(..., description="Time range for the analysis")
    group_by: str = Field(..., description="Grouping method used")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class PerformanceCorrelation(BaseModel):
    """Performance factor correlation."""

    factor: str = Field(
        ..., description="Factor name (e.g., 'message_length', 'tool_count')"
    )
    correlation_strength: float = Field(
        ..., ge=-1, le=1, description="Pearson correlation coefficient"
    )
    impact_ms: float = Field(..., description="Average impact on response time in ms")
    sample_size: int = Field(
        ..., ge=0, description="Number of samples used for correlation"
    )


class PerformanceFactorsAnalytics(BaseModel):
    """Performance factors analysis response."""

    correlations: list[PerformanceCorrelation] = Field(
        ..., description="Factor correlations"
    )
    recommendations: list[str] = Field(
        ..., description="Performance optimization recommendations"
    )
    time_range: TimeRange = Field(..., description="Time range for the analysis")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Token Analytics Schemas


class TokenPercentiles(BaseModel):
    """Token usage percentiles."""

    p50: float = Field(..., description="50th percentile (median) token usage")
    p90: float = Field(..., description="90th percentile token usage")
    p95: float = Field(..., description="95th percentile token usage")
    p99: float = Field(..., description="99th percentile token usage")


class TokenAnalyticsDataPoint(BaseModel):
    """Token analytics data point in time series."""

    timestamp: datetime = Field(..., description="Data point timestamp")
    avg_tokens: float = Field(..., description="Average token usage")
    p50: float = Field(..., description="50th percentile token usage")
    p90: float = Field(..., description="90th percentile token usage")
    message_count: int = Field(
        ..., ge=0, description="Number of messages in this time bucket"
    )


class TokenDistributionBucket(BaseModel):
    """Token usage distribution bucket."""

    bucket: str = Field(
        ...,
        description="Bucket range (e.g., '0-1000', '1000-5000', '5000-10000', '10000+')",
    )
    count: int = Field(..., ge=0, description="Number of messages in this bucket")
    percentage: float = Field(
        ..., ge=0, le=100, description="Percentage of total messages"
    )


class TokenAnalytics(BaseModel):
    """Token usage analytics response."""

    percentiles: TokenPercentiles = Field(
        ..., description="Overall percentiles for the time range"
    )
    time_series: list[TokenAnalyticsDataPoint] = Field(
        ..., description="Time series data"
    )
    distribution: list[TokenDistributionBucket] = Field(
        ..., description="Token usage distribution"
    )
    time_range: TimeRange = Field(..., description="Time range for the analysis")
    group_by: str = Field(..., description="Grouping method used")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class TokenPerformanceCorrelation(BaseModel):
    """Token performance factor correlation."""

    factor: str = Field(
        ..., description="Factor name (e.g., 'message_length', 'tool_count')"
    )
    correlation_strength: float = Field(
        ..., ge=-1, le=1, description="Pearson correlation coefficient"
    )
    impact_tokens: float = Field(..., description="Average impact on token usage")
    sample_size: int = Field(
        ..., ge=0, description="Number of samples used for correlation"
    )


class TokenPerformanceFactorsAnalytics(BaseModel):
    """Token performance factors analysis response."""

    correlations: list[TokenPerformanceCorrelation] = Field(
        ..., description="Factor correlations"
    )
    recommendations: list[str] = Field(
        ..., description="Token usage optimization recommendations"
    )
    time_range: TimeRange = Field(..., description="Time range for the analysis")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Git Branch Analytics Schemas


class BranchType(str, Enum):
    """Branch type classification."""

    MAIN = "main"
    FEATURE = "feature"
    HOTFIX = "hotfix"
    RELEASE = "release"
    OTHER = "other"


class BranchTopOperation(BaseModel):
    """Top operation performed on a branch."""

    operation: str = Field(..., description="Operation/tool name")
    count: int = Field(..., ge=0, description="Number of times used")


class BranchMetrics(BaseModel):
    """Metrics for a git branch."""

    cost: float = Field(..., ge=0, description="Total cost in USD")
    messages: int = Field(..., ge=0, description="Number of messages")
    sessions: int = Field(..., ge=0, description="Number of unique sessions")
    avg_session_cost: float = Field(..., ge=0, description="Average cost per session")
    first_activity: datetime = Field(..., description="First activity timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    active_days: int = Field(..., ge=0, description="Number of active days")


class BranchAnalytics(BaseModel):
    """Analytics for a single git branch."""

    name: str = Field(..., description="Branch name")
    type: BranchType = Field(..., description="Detected branch type")
    metrics: BranchMetrics = Field(..., description="Branch metrics")
    top_operations: list[BranchTopOperation] = Field(
        default_factory=list, description="Most common operations"
    )
    cost_trend: float = Field(
        0.0, description="Cost trend percentage from previous period"
    )


class BranchComparison(BaseModel):
    """Branch comparison metrics."""

    main_vs_feature_cost_ratio: float = Field(
        ..., description="Ratio of main to feature branch costs"
    )
    avg_feature_branch_lifetime_days: float = Field(
        ..., ge=0, description="Average feature branch lifetime in days"
    )
    most_expensive_branch_type: BranchType = Field(
        ..., description="Branch type with highest costs"
    )


class GitBranchAnalyticsResponse(BaseModel):
    """Git branch analytics response."""

    branches: list[BranchAnalytics] = Field(..., description="Branch analytics data")
    branch_comparisons: BranchComparison = Field(
        ..., description="Branch comparison metrics"
    )
    time_range: TimeRange = Field(..., description="Time range for the analysis")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Token Efficiency Metrics Schemas


class TokenBreakdown(BaseModel):
    """Token usage breakdown by type."""

    input_tokens: int = Field(..., ge=0, description="Input tokens used")
    output_tokens: int = Field(..., ge=0, description="Output tokens generated")
    cache_creation: int = Field(0, ge=0, description="Tokens used for cache creation")
    cache_read: int = Field(0, ge=0, description="Tokens read from cache")
    total: int = Field(..., ge=0, description="Total tokens used")


class TokenEfficiencyMetrics(BaseModel):
    """Token efficiency metrics."""

    cache_hit_rate: float = Field(
        0.0, ge=0.0, le=100.0, description="Cache hit rate percentage"
    )
    input_output_ratio: float = Field(
        ..., ge=0.0, description="Ratio of input to output tokens"
    )
    avg_tokens_per_message: float = Field(
        ..., ge=0.0, description="Average tokens per message"
    )
    cost_per_token: float = Field(0.0, ge=0.0, description="Cost per token in USD")


class TokenFormattedValues(BaseModel):
    """Formatted token values for display."""

    total: str = Field(..., description="Formatted total tokens (e.g., '45K', '1.2M')")
    input: str = Field(..., description="Formatted input tokens")
    output: str = Field(..., description="Formatted output tokens")
    cache_creation: str = Field("0", description="Formatted cache creation tokens")
    cache_read: str = Field("0", description="Formatted cache read tokens")


class TokenEfficiencySummary(BaseModel):
    """Token efficiency summary for stat card display."""

    total_tokens: int = Field(..., ge=0, description="Total token count")
    formatted_total: str = Field(
        ..., description="Formatted total for display (e.g., '45K', '1.2M')"
    )
    cost_estimate: float = Field(0.0, ge=0.0, description="Estimated cost in USD")
    trend: str = Field("stable", description="Token usage trend: up, down, or stable")


class TokenEfficiencyDetailed(BaseModel):
    """Detailed token efficiency analytics."""

    token_breakdown: TokenBreakdown = Field(
        ..., description="Token usage breakdown by type"
    )
    efficiency_metrics: TokenEfficiencyMetrics = Field(
        ..., description="Efficiency calculations"
    )
    formatted_values: TokenFormattedValues = Field(
        ..., description="Formatted values for display"
    )
    session_id: str | None = Field(
        None, description="Session ID if filtered by session"
    )
    time_range: TimeRange = Field(..., description="Time range for the analysis")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Session Depth Analysis Schemas


class DepthDistribution(BaseModel):
    """Distribution of conversation depths."""

    depth: int = Field(..., ge=0, description="Conversation depth level")
    session_count: int = Field(
        ..., ge=0, description="Number of sessions at this depth"
    )
    avg_cost: float = Field(
        ..., ge=0, description="Average cost for sessions at this depth"
    )
    avg_messages: int = Field(
        ..., ge=0, description="Average message count for sessions at this depth"
    )
    percentage: float = Field(
        ..., ge=0, le=100, description="Percentage of total sessions"
    )


class DepthCorrelations(BaseModel):
    """Correlations between depth and other metrics."""

    depth_vs_cost: float = Field(
        ..., ge=-1, le=1, description="Correlation between depth and cost"
    )
    depth_vs_duration: float = Field(
        ..., ge=-1, le=1, description="Correlation between depth and session duration"
    )
    depth_vs_success: float = Field(
        ..., ge=-1, le=1, description="Correlation between depth and success rate"
    )


class ConversationPattern(BaseModel):
    """Identified conversation pattern."""

    pattern_name: str = Field(
        ..., description="Pattern name (e.g., 'shallow-wide', 'deep-narrow')"
    )
    frequency: int = Field(
        ..., ge=0, description="Number of sessions matching this pattern"
    )
    avg_cost: float = Field(
        ..., ge=0, description="Average cost for sessions with this pattern"
    )
    typical_use_case: str = Field(
        ..., description="Description of typical use case for this pattern"
    )


class DepthRecommendations(BaseModel):
    """Optimization recommendations based on depth analysis."""

    optimal_depth_range: tuple[int, int] = Field(
        ..., description="Recommended optimal depth range"
    )
    warning_threshold: int = Field(
        ..., ge=0, description="Depth threshold that indicates potential issues"
    )
    tips: list[str] = Field(
        default_factory=list, description="Actionable optimization tips"
    )


class SessionDepthAnalytics(BaseModel):
    """Complete session depth analytics response."""

    depth_distribution: list[DepthDistribution] = Field(
        ..., description="Distribution of conversation depths"
    )
    depth_correlations: DepthCorrelations = Field(
        ..., description="Correlations with other metrics"
    )
    patterns: list[ConversationPattern] = Field(
        ..., description="Identified conversation patterns"
    )
    recommendations: DepthRecommendations = Field(
        ..., description="Optimization recommendations"
    )
    time_range: TimeRange = Field(..., description="Time range for the analysis")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Cost Prediction Dashboard Schemas


class CostSummary(BaseModel):
    """Cost summary for stat card display."""

    total_cost: float = Field(..., ge=0, description="Total cost in USD")
    formatted_cost: str = Field(
        ..., description="Formatted cost string (e.g., '$0.45', '$12.30')"
    )
    currency: str = Field("USD", description="Currency code")
    trend: str = Field("stable", description="Cost trend: up, down, or stable")
    period: str = Field(..., description="Time period for the cost data")


class CostBreakdownItem(BaseModel):
    """Individual cost breakdown item."""

    model: str = Field(..., description="Model name")
    cost: float = Field(..., ge=0, description="Cost for this model")
    percentage: float = Field(..., ge=0, le=100, description="Percentage of total cost")
    message_count: int = Field(
        ..., ge=0, description="Number of messages for this model"
    )


class CostTimePoint(BaseModel):
    """Cost data point over time."""

    timestamp: datetime = Field(..., description="Timestamp for this data point")
    cost: float = Field(..., ge=0, description="Cost at this timestamp")
    cumulative: float = Field(..., ge=0, description="Cumulative cost up to this point")


class CostBreakdown(BaseModel):
    """Detailed cost breakdown."""

    by_model: list[CostBreakdownItem] = Field(
        default_factory=list, description="Cost breakdown by model"
    )
    by_time: list[CostTimePoint] = Field(
        default_factory=list, description="Cost breakdown over time"
    )


class CostMetrics(BaseModel):
    """Cost efficiency metrics."""

    avg_cost_per_message: float = Field(
        ..., ge=0, description="Average cost per message"
    )
    avg_cost_per_hour: float = Field(..., ge=0, description="Average cost per hour")
    most_expensive_model: str | None = Field(None, description="Most expensive model")


class CostBreakdownResponse(BaseModel):
    """Detailed cost breakdown response."""

    cost_breakdown: CostBreakdown = Field(..., description="Cost breakdown data")
    cost_metrics: CostMetrics = Field(..., description="Cost efficiency metrics")
    time_range: TimeRange = Field(..., description="Time range for the analysis")
    session_id: str | None = Field(
        None, description="Session ID if filtered by session"
    )
    project_id: str | None = Field(
        None, description="Project ID if filtered by project"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class CostPredictionPoint(BaseModel):
    """Single cost prediction data point."""

    date: datetime = Field(..., description="Predicted date")
    predicted_cost: float = Field(..., ge=0, description="Predicted cost for this date")
    confidence_interval: tuple[float, float] = Field(
        ..., description="Lower and upper bounds of prediction"
    )


class CostPrediction(BaseModel):
    """Cost prediction response."""

    predictions: list[CostPredictionPoint] = Field(..., description="Cost predictions")
    total_predicted: float = Field(
        ..., ge=0, description="Total predicted cost for the period"
    )
    confidence_level: float = Field(
        0.95, ge=0, le=1, description="Confidence level for predictions"
    )
    model_accuracy: float = Field(
        ..., ge=0, le=100, description="Historical accuracy of predictions"
    )
    prediction_days: int = Field(..., ge=1, description="Number of days predicted")
    session_id: str | None = Field(
        None, description="Session ID if filtered by session"
    )
    project_id: str | None = Field(
        None, description="Project ID if filtered by project"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# User Intent Classification Schemas


class TopicCategory(str, Enum):
    """Topic category classification."""

    WEB_DEVELOPMENT = "Web Development"
    API_INTEGRATION = "API Integration"
    DATA_VISUALIZATION = "Data Visualization"
    MACHINE_LEARNING = "Machine Learning"
    DATABASE_OPERATIONS = "Database Operations"
    DEVOPS_DEPLOYMENT = "DevOps/Deployment"
    TESTING_QA = "Testing/QA"
    DOCUMENTATION = "Documentation"


class ExtractedTopic(BaseModel):
    """Individual extracted topic."""

    name: str = Field(..., description="Topic name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    category: TopicCategory = Field(..., description="Topic category")
    relevance_score: float = Field(..., ge=0.0, description="Topic relevance score")
    keywords: list[str] = Field(
        default_factory=list, description="Keywords that triggered this topic"
    )


class TopicExtractionResponse(BaseModel):
    """Response for topic extraction from a session."""

    session_id: str = Field(..., description="Session ID analyzed")
    topics: list[ExtractedTopic] = Field(
        default_factory=list, description="Extracted topics"
    )
    suggested_topics: list[str] = Field(
        default_factory=list, description="Additional suggested topics"
    )
    extraction_method: str = Field(
        "keyword", description="Method used: keyword, ml, or hybrid"
    )
    confidence_threshold: float = Field(
        0.3, description="Minimum confidence threshold used"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class PopularTopic(BaseModel):
    """Popular topic aggregation."""

    name: str = Field(..., description="Topic name")
    session_count: int = Field(
        ..., ge=0, description="Number of sessions with this topic"
    )
    trend: str = Field(..., description="Trend: trending, stable, or declining")
    percentage_change: float = Field(
        0.0, description="Percentage change from previous period"
    )


class TopicCombination(BaseModel):
    """Common topic combination."""

    topics: list[str] = Field(..., description="Topics that appear together")
    frequency: int = Field(
        ..., ge=0, description="Number of sessions with this combination"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence of this combination"
    )


class TopicSuggestionResponse(BaseModel):
    """Response for topic suggestions and aggregations."""

    popular_topics: list[PopularTopic] = Field(
        default_factory=list, description="Most popular topics"
    )
    topic_combinations: list[TopicCombination] = Field(
        default_factory=list, description="Common topic combinations"
    )
    time_range: TimeRange = Field(..., description="Time range for the analysis")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Performance Benchmarking Schemas


class NormalizationMethod(str, Enum):
    """Normalization method for benchmark metrics."""

    Z_SCORE = "z_score"
    MIN_MAX = "min_max"
    PERCENTILE_RANK = "percentile_rank"


class BenchmarkEntityType(str, Enum):
    """Type of entity being benchmarked."""

    PROJECT = "project"
    TEAM = "team"
    TIME_PERIOD = "time_period"


class BenchmarkMetrics(BaseModel):
    """Benchmark performance metrics."""

    cost_efficiency: float = Field(..., description="Cost efficiency score (0-100)")
    speed_score: float = Field(..., description="Speed performance score (0-100)")
    quality_score: float = Field(
        ..., description="Quality score based on error rates (0-100)"
    )
    productivity_score: float = Field(
        ..., description="Productivity score based on tasks per session (0-100)"
    )
    complexity_handling: float = Field(
        ..., description="Complexity handling score (0-100)"
    )
    overall_score: float = Field(..., description="Overall composite score (0-100)")


class BenchmarkPercentileRanks(BaseModel):
    """Percentile ranks for benchmark metrics."""

    cost_efficiency: float = Field(
        ..., ge=0, le=100, description="Cost efficiency percentile rank"
    )
    speed: float = Field(..., ge=0, le=100, description="Speed percentile rank")
    quality: float = Field(..., ge=0, le=100, description="Quality percentile rank")
    productivity: float = Field(
        ..., ge=0, le=100, description="Productivity percentile rank"
    )


class BenchmarkEntity(BaseModel):
    """Individual benchmark entity result."""

    entity: str = Field(..., description="Entity name (project/team/period)")
    entity_type: BenchmarkEntityType = Field(..., description="Type of entity")
    metrics: BenchmarkMetrics = Field(..., description="Performance metrics")
    percentile_ranks: BenchmarkPercentileRanks = Field(
        ..., description="Percentile rankings"
    )
    strengths: list[str] = Field(default_factory=list, description="Areas of strength")
    improvement_areas: list[str] = Field(
        default_factory=list, description="Areas for improvement"
    )


class BenchmarkComparisonMatrix(BaseModel):
    """Comparison matrix for benchmarks."""

    headers: list[str] = Field(..., description="Matrix column headers (entity names)")
    data: list[list[float]] = Field(
        ..., description="Matrix data rows (metrics x entities)"
    )
    best_performer_per_metric: list[str] = Field(
        ..., description="Best performer for each metric"
    )


class BenchmarkImprovement(BaseModel):
    """Individual improvement record."""

    entity: str = Field(..., description="Entity name")
    metric: str = Field(..., description="Metric that improved")
    improvement: float = Field(..., description="Improvement amount")
    improvement_percentage: float = Field(..., description="Improvement percentage")


class BenchmarkInsights(BaseModel):
    """Benchmark insights and recommendations."""

    top_performers: list[str] = Field(..., description="Top performing entities")
    biggest_improvements: list[BenchmarkImprovement] = Field(
        ..., description="Biggest improvements"
    )
    recommendations: list[str] = Field(..., description="Performance recommendations")


class BenchmarkResponse(BaseModel):
    """Complete benchmark analysis response."""

    benchmarks: list[BenchmarkEntity] = Field(
        ..., description="Individual benchmark results"
    )
    comparison_matrix: BenchmarkComparisonMatrix = Field(
        ..., description="Comparison matrix"
    )
    insights: BenchmarkInsights = Field(..., description="Analysis insights")
    normalization_method: NormalizationMethod = Field(
        ..., description="Normalization method used"
    )
    time_range: TimeRange = Field(..., description="Time range for analysis")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class CreateBenchmarkRequest(BaseModel):
    """Request to create a new benchmark."""

    entity_type: BenchmarkEntityType = Field(
        ..., description="Type of entities to benchmark"
    )
    entity_ids: list[str] = Field(
        ..., min_length=2, max_length=20, description="Entity IDs to compare"
    )
    time_range: TimeRange = Field(
        TimeRange.LAST_30_DAYS, description="Time range for analysis"
    )
    normalization_method: NormalizationMethod = Field(
        NormalizationMethod.Z_SCORE, description="Normalization method"
    )
    include_percentile_ranks: bool = Field(
        True, description="Include percentile rankings"
    )


class BenchmarkComparisonRequest(BaseModel):
    """Request for benchmark comparison analysis."""

    primary_entity_id: str = Field(
        ..., description="Primary entity to compare against others"
    )
    comparison_entity_ids: list[str] = Field(
        ..., min_length=1, max_length=10, description="Entities to compare with"
    )
    entity_type: BenchmarkEntityType = Field(..., description="Type of entities")
    time_range: TimeRange = Field(
        TimeRange.LAST_30_DAYS, description="Time range for analysis"
    )
    metrics_to_compare: list[str] | None = Field(
        None, description="Specific metrics to compare"
    )


# Enable forward references for DirectoryNode
DirectoryNode.model_rebuild()
