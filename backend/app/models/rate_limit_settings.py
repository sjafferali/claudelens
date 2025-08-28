"""Rate limit settings model."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RateLimitSettings(BaseModel):
    """Rate limit settings stored in database."""

    # General HTTP rate limits
    http_rate_limit_enabled: bool = Field(
        True, description="Enable HTTP rate limiting for all API endpoints"
    )
    http_calls_per_minute: int = Field(
        500, ge=0, description="Max HTTP requests per minute per client (0 = unlimited)"
    )
    http_rate_limit_window_seconds: int = Field(
        60, ge=1, le=3600, description="HTTP rate limit window in seconds"
    )

    # CLI/Ingestion specific limits
    ingest_enabled: bool = Field(True, description="Enable ingestion from CLI")
    ingest_rate_limit_per_hour: int = Field(
        1000, ge=0, description="Max ingestion batches per hour (0 = unlimited)"
    )
    ingest_max_batch_size: int = Field(
        1000, ge=1, le=10000, description="Max messages per ingestion batch"
    )
    ingest_max_file_size_mb: int = Field(
        50, ge=1, le=500, description="Max size per JSONL file in MB"
    )

    # AI/LLM rate limits
    ai_rate_limit_enabled: bool = Field(
        True, description="Enable rate limiting for AI features"
    )
    ai_rate_limit_per_minute: int = Field(
        10, ge=0, description="Max AI requests per minute per user (0 = unlimited)"
    )
    ai_max_tokens: int = Field(
        2000, ge=100, le=32000, description="Max tokens per AI request"
    )

    # Export/Import limits
    export_limit_per_hour: int = Field(
        10, ge=0, description="Export operations per hour (0 = unlimited)"
    )
    import_limit_per_hour: int = Field(
        5, ge=0, description="Import operations per hour (0 = unlimited)"
    )

    # Backup/Restore limits
    backup_limit_per_hour: int = Field(
        10, ge=0, description="Backup operations per hour (0 = unlimited)"
    )
    restore_limit_per_hour: int = Field(
        5, ge=0, description="Restore operations per hour (0 = unlimited)"
    )

    # File size limits
    max_upload_size_mb: int = Field(
        100, ge=0, description="Max upload size in MB (0 = unlimited)"
    )
    max_export_size_mb: int = Field(
        500, ge=0, description="Max export size in MB (0 = unlimited)"
    )
    max_backup_size_gb: int = Field(
        100, ge=0, description="Max backup size in GB (0 = unlimited)"
    )

    # Pagination limits
    max_page_size: int = Field(
        100, ge=10, le=10000, description="Maximum items per page in API responses"
    )
    default_page_size: int = Field(
        20, ge=10, le=100, description="Default items per page in API responses"
    )

    # WebSocket limits
    websocket_enabled: bool = Field(True, description="Enable WebSocket connections")
    websocket_max_connections_per_user: int = Field(
        5, ge=1, le=50, description="Max concurrent WebSocket connections per user"
    )
    websocket_message_rate_per_second: int = Field(
        10, ge=1, le=100, description="Max WebSocket messages per second per connection"
    )

    # Search limits
    search_rate_limit_per_minute: int = Field(
        60, ge=0, description="Max search requests per minute (0 = unlimited)"
    )
    search_max_results: int = Field(
        1000, ge=10, le=10000, description="Max search results returned"
    )

    # Analytics limits
    analytics_rate_limit_per_minute: int = Field(
        30, ge=0, description="Max analytics queries per minute (0 = unlimited)"
    )
    analytics_max_date_range_days: int = Field(
        365, ge=1, le=3650, description="Max date range for analytics queries in days"
    )

    # Rate limit window for operations (export, import, backup, restore)
    rate_limit_window_hours: int = Field(
        1, ge=1, le=24, description="Rate limit window in hours for operations"
    )

    # Enable/disable rate limiting globally
    rate_limiting_enabled: bool = Field(
        True, description="Enable all rate limiting features"
    )

    # Metadata
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = Field(
        None, description="User who last updated settings"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "export_limit_per_hour": 10,
                "import_limit_per_hour": 5,
                "backup_limit_per_hour": 10,
                "restore_limit_per_hour": 5,
                "max_upload_size_mb": 100,
                "max_export_size_mb": 500,
                "max_backup_size_gb": 100,
                "max_page_size": 100,
                "default_page_size": 20,
                "rate_limit_window_hours": 1,
                "rate_limiting_enabled": True,
            }
        }
    )
