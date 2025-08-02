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
