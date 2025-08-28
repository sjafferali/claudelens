"""Rate limit settings model."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RateLimitSettings(BaseModel):
    """Rate limit settings stored in database."""

    # Export/Import limits
    export_limit_per_hour: int = Field(
        10, ge=0, description="Export rate limit per hour (0 = unlimited)"
    )
    import_limit_per_hour: int = Field(
        5, ge=0, description="Import rate limit per hour (0 = unlimited)"
    )

    # Backup/Restore limits
    backup_limit_per_hour: int = Field(
        10, ge=0, description="Backup rate limit per hour (0 = unlimited)"
    )
    restore_limit_per_hour: int = Field(
        5, ge=0, description="Restore rate limit per hour (0 = unlimited)"
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
        100, ge=10, le=10000, description="Maximum items per page"
    )
    default_page_size: int = Field(
        20, ge=10, le=100, description="Default items per page"
    )

    # Rate limit window
    rate_limit_window_hours: int = Field(
        1, ge=1, le=24, description="Rate limit window in hours"
    )

    # Enable/disable rate limiting
    rate_limiting_enabled: bool = Field(True, description="Enable rate limiting")

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
