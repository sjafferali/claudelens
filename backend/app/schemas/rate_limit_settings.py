"""Rate limit settings schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RateLimitSettingsUpdate(BaseModel):
    """Request to update rate limit settings."""

    # Export/Import limits
    export_limit_per_hour: Optional[int] = Field(
        None, ge=0, description="Export rate limit per hour (0 = unlimited)"
    )
    import_limit_per_hour: Optional[int] = Field(
        None, ge=0, description="Import rate limit per hour (0 = unlimited)"
    )

    # Backup/Restore limits
    backup_limit_per_hour: Optional[int] = Field(
        None, ge=0, description="Backup rate limit per hour (0 = unlimited)"
    )
    restore_limit_per_hour: Optional[int] = Field(
        None, ge=0, description="Restore rate limit per hour (0 = unlimited)"
    )

    # File size limits
    max_upload_size_mb: Optional[int] = Field(
        None, ge=0, description="Max upload size in MB (0 = unlimited)"
    )
    max_export_size_mb: Optional[int] = Field(
        None, ge=0, description="Max export size in MB (0 = unlimited)"
    )
    max_backup_size_gb: Optional[int] = Field(
        None, ge=0, description="Max backup size in GB (0 = unlimited)"
    )

    # Pagination limits
    max_page_size: Optional[int] = Field(
        None, ge=10, le=10000, description="Maximum items per page"
    )
    default_page_size: Optional[int] = Field(
        None, ge=10, le=100, description="Default items per page"
    )

    # Rate limit window
    rate_limit_window_hours: Optional[int] = Field(
        None, ge=1, le=24, description="Rate limit window in hours"
    )

    # Enable/disable rate limiting
    rate_limiting_enabled: Optional[bool] = Field(
        None, description="Enable rate limiting"
    )


class RateLimitSettingsResponse(BaseModel):
    """Rate limit settings response."""

    # Export/Import limits
    export_limit_per_hour: int
    import_limit_per_hour: int

    # Backup/Restore limits
    backup_limit_per_hour: int
    restore_limit_per_hour: int

    # File size limits
    max_upload_size_mb: int
    max_export_size_mb: int
    max_backup_size_gb: int

    # Pagination limits
    max_page_size: int
    default_page_size: int

    # Rate limit window
    rate_limit_window_hours: int

    # Enable/disable rate limiting
    rate_limiting_enabled: bool

    # Metadata
    updated_at: datetime
    updated_by: Optional[str]

    # Current usage info (helpful for UI)
    current_usage: Optional[dict] = Field(None, description="Current rate limit usage")
