"""Rate limit usage history models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RateLimitType(str, Enum):
    """Types of rate limits being tracked."""

    HTTP = "http"
    INGESTION = "ingestion"
    AI = "ai"
    EXPORT = "export"
    IMPORT = "import"
    BACKUP = "backup"
    RESTORE = "restore"
    SEARCH = "search"
    ANALYTICS = "analytics"
    WEBSOCKET = "websocket"


class UsageInterval(str, Enum):
    """Time intervals for aggregation."""

    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class RateLimitUsageRecord(BaseModel):
    """Individual rate limit usage record."""

    user_id: str = Field(..., description="User ID")
    limit_type: RateLimitType = Field(..., description="Type of rate limit")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Usage metrics
    requests_made: int = Field(0, ge=0, description="Number of requests made")
    requests_allowed: int = Field(0, ge=0, description="Number of requests allowed")
    requests_blocked: int = Field(0, ge=0, description="Number of requests blocked")

    # Limit information at time of record
    limit_value: int = Field(..., description="Rate limit value at this time")
    limit_window: int = Field(..., description="Rate limit window in seconds")

    # Additional metrics
    peak_usage_rate: float = Field(
        0.0, ge=0.0, description="Peak usage rate as percentage"
    )
    average_response_time_ms: Optional[float] = Field(
        None, description="Average response time in milliseconds"
    )

    # Data transferred (for relevant operations)
    bytes_transferred: Optional[int] = Field(
        None, description="Total bytes transferred"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user123",
                "limit_type": "http",
                "timestamp": "2024-01-01T00:00:00Z",
                "requests_made": 450,
                "requests_allowed": 450,
                "requests_blocked": 0,
                "limit_value": 500,
                "limit_window": 60,
                "peak_usage_rate": 90.0,
                "average_response_time_ms": 125.5,
                "bytes_transferred": None,
            }
        }
    )


class RateLimitUsageAggregation(BaseModel):
    """Aggregated rate limit usage data."""

    user_id: str = Field(..., description="User ID")
    limit_type: RateLimitType = Field(..., description="Type of rate limit")
    interval: UsageInterval = Field(..., description="Aggregation interval")
    period_start: datetime = Field(..., description="Start of the period")
    period_end: datetime = Field(..., description="End of the period")

    # Aggregated metrics
    total_requests: int = Field(0, ge=0, description="Total requests in period")
    total_allowed: int = Field(0, ge=0, description="Total allowed requests")
    total_blocked: int = Field(0, ge=0, description="Total blocked requests")

    # Statistics
    peak_usage_rate: float = Field(0.0, ge=0.0, description="Peak usage rate in period")
    average_usage_rate: float = Field(0.0, ge=0.0, description="Average usage rate")
    violation_count: int = Field(0, ge=0, description="Number of rate limit violations")

    # Performance metrics
    avg_response_time_ms: Optional[float] = Field(
        None, description="Average response time"
    )
    p95_response_time_ms: Optional[float] = Field(
        None, description="95th percentile response time"
    )
    p99_response_time_ms: Optional[float] = Field(
        None, description="99th percentile response time"
    )

    # Data volume (for relevant operations)
    total_bytes_transferred: Optional[int] = Field(
        None, description="Total bytes transferred"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user123",
                "limit_type": "http",
                "interval": "hour",
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-01T01:00:00Z",
                "total_requests": 4500,
                "total_allowed": 4480,
                "total_blocked": 20,
                "peak_usage_rate": 95.0,
                "average_usage_rate": 75.0,
                "violation_count": 2,
                "avg_response_time_ms": 125.5,
                "p95_response_time_ms": 250.0,
                "p99_response_time_ms": 500.0,
                "total_bytes_transferred": 10485760,
            }
        }
    )


class UserUsageSnapshot(BaseModel):
    """Current usage snapshot for a user across all rate limits."""

    user_id: str = Field(..., description="User ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Current usage by type
    http_usage: dict = Field(default_factory=dict, description="Current HTTP usage")
    ingestion_usage: dict = Field(
        default_factory=dict, description="Current ingestion usage"
    )
    ai_usage: dict = Field(default_factory=dict, description="Current AI usage")
    export_usage: dict = Field(default_factory=dict, description="Current export usage")
    import_usage: dict = Field(default_factory=dict, description="Current import usage")
    backup_usage: dict = Field(default_factory=dict, description="Current backup usage")
    restore_usage: dict = Field(
        default_factory=dict, description="Current restore usage"
    )
    search_usage: dict = Field(default_factory=dict, description="Current search usage")
    analytics_usage: dict = Field(
        default_factory=dict, description="Current analytics usage"
    )
    websocket_usage: dict = Field(
        default_factory=dict, description="Current WebSocket usage"
    )

    # Summary statistics
    total_requests_today: int = Field(0, description="Total requests today")
    total_blocked_today: int = Field(0, description="Total blocked requests today")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user123",
                "timestamp": "2024-01-01T12:00:00Z",
                "http_usage": {
                    "current": 250,
                    "limit": 500,
                    "remaining": 250,
                    "reset_in_seconds": 30,
                    "percentage_used": 50.0,
                },
                "total_requests_today": 5000,
                "total_blocked_today": 10,
            }
        }
    )
