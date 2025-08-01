"""Analytics schemas."""
from typing import List, Dict, Any, Optional
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
    
    messages_trend: float = Field(..., description="Percentage change from previous period")
    cost_trend: float = Field(..., description="Percentage change from previous period")
    
    most_active_project: Optional[str] = None
    most_used_model: Optional[str] = None
    
    time_range: TimeRange
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class HeatmapCell(BaseModel):
    """Single cell in activity heatmap."""
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    hour: int = Field(..., ge=0, le=23)
    count: int = Field(..., ge=0)
    
    # Optional enrichment
    avg_cost: Optional[float] = None
    avg_response_time: Optional[float] = None


class ActivityHeatmap(BaseModel):
    """Activity heatmap data."""
    cells: List[HeatmapCell]
    total_messages: int
    time_range: TimeRange
    timezone: str
    
    # Peak activity times
    peak_hour: Optional[int] = None
    peak_day: Optional[int] = None


class CostDataPoint(BaseModel):
    """Cost data point in time series."""
    timestamp: datetime
    cost: float
    message_count: int
    
    # Breakdown by model
    cost_by_model: Optional[Dict[str, float]] = None


class CostAnalytics(BaseModel):
    """Cost analytics over time."""
    data_points: List[CostDataPoint]
    total_cost: float
    average_cost_per_message: float
    
    time_range: TimeRange
    group_by: str
    
    # Cost breakdown
    cost_by_model: Dict[str, float]
    cost_by_project: Optional[Dict[str, float]] = None


class ModelUsage(BaseModel):
    """Usage statistics for a single model."""
    model: str
    message_count: int
    total_cost: float
    avg_cost_per_message: float
    
    avg_response_time_ms: Optional[float] = None
    avg_tokens_input: Optional[float] = None
    avg_tokens_output: Optional[float] = None
    
    # Usage trend
    trend_percentage: Optional[float] = None


class ModelUsageStats(BaseModel):
    """Model usage statistics."""
    models: List[ModelUsage]
    total_models: int
    time_range: TimeRange
    
    # Most/least used
    most_used: Optional[str] = None
    least_used: Optional[str] = None


class TokenDataPoint(BaseModel):
    """Token usage data point."""
    timestamp: datetime
    input_tokens: int
    output_tokens: int
    total_tokens: int


class TokenUsageStats(BaseModel):
    """Token usage statistics."""
    data_points: List[TokenDataPoint]
    total_input_tokens: int
    total_output_tokens: int
    
    avg_input_tokens_per_message: float
    avg_output_tokens_per_message: float
    
    time_range: TimeRange
    group_by: str