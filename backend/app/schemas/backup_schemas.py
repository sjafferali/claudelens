"""Backup and restore schemas for request/response validation."""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BackupType(str, Enum):
    """Backup type enumeration."""

    FULL = "full"
    SELECTIVE = "selective"


class BackupStatus(str, Enum):
    """Backup status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"
    DELETING = "deleting"


class RestoreMode(str, Enum):
    """Restore mode enumeration."""

    FULL = "full"
    SELECTIVE = "selective"
    MERGE = "merge"


class ConflictResolution(str, Enum):
    """Conflict resolution strategy enumeration."""

    SKIP = "skip"
    OVERWRITE = "overwrite"
    RENAME = "rename"
    MERGE = "merge"


class JobStatus(str, Enum):
    """Job status enumeration."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackupFilters(BaseModel):
    """Filters for selective backup."""

    projects: Optional[List[str]] = None
    sessions: Optional[List[str]] = None
    date_range: Optional[Dict[str, datetime]] = None
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    min_message_count: Optional[int] = Field(None, ge=1, le=10000)
    max_message_count: Optional[int] = Field(None, ge=1, le=10000)

    @field_validator("date_range")
    @classmethod
    def validate_date_range(
        cls, v: Optional[Dict[str, datetime]]
    ) -> Optional[Dict[str, datetime]]:
        if v and "start" in v and "end" in v:
            if v["start"] >= v["end"]:
                raise ValueError("start date must be before end date")
        return v


class BackupOptions(BaseModel):
    """Options for backup creation."""

    compress: bool = True
    compression_level: int = Field(default=3, ge=1, le=9)
    encrypt: bool = False
    include_metadata: bool = True
    include_analytics: bool = False
    split_size_mb: Optional[int] = Field(None, ge=100, le=5000)


class CreateBackupRequest(BaseModel):
    """Request to create a backup."""

    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    type: BackupType
    filters: Optional[BackupFilters] = None
    options: Optional[BackupOptions] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", v):
            raise ValueError(
                "Name must be alphanumeric with spaces, dashes, or underscores"
            )
        return v

    @model_validator(mode="after")
    def validate_filters_for_selective(self) -> "CreateBackupRequest":
        """Validate that selective backups have filters."""
        if self.type == BackupType.SELECTIVE and not self.filters:
            raise ValueError("Filters are required for selective backup type")
        return self


class CreateBackupResponse(BaseModel):
    """Response for backup creation."""

    job_id: str
    backup_id: str
    status: JobStatus
    created_at: datetime
    estimated_size_bytes: Optional[int] = None
    estimated_duration_seconds: Optional[int] = None
    message: str


class BackupContents(BaseModel):
    """Backup contents summary."""

    projects_count: int = 0
    sessions_count: int = 0
    messages_count: int = 0
    prompts_count: int = 0
    ai_settings_count: int = 0
    total_documents: int = 0
    date_range: Optional[Dict[str, datetime]] = None


class BackupMetadataResponse(BaseModel):
    """Backup metadata response."""

    id: str = Field(alias="_id")
    name: str
    description: Optional[str] = None
    filename: str
    filepath: str
    created_at: datetime
    created_by: Optional[str] = None
    size_bytes: int
    compressed_size_bytes: Optional[int] = None
    type: BackupType
    status: BackupStatus
    filters: Optional[BackupFilters] = None
    contents: BackupContents
    checksum: str
    version: str
    download_url: Optional[str] = None
    can_restore: bool = True
    error_message: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class BackupDetailResponse(BackupMetadataResponse):
    """Detailed backup information response."""

    storage_location: str
    encryption: Optional[Dict[str, Any]] = None
    compression: Optional[Dict[str, Any]] = None
    restore_history: List[Dict[str, Any]] = Field(default_factory=list)
    validation_status: Optional[Dict[str, Any]] = None


class PagedBackupsResponse(BaseModel):
    """Paginated backups response."""

    items: List[BackupMetadataResponse]
    pagination: Dict[str, Any]
    summary: Dict[str, Any]

    model_config = ConfigDict(populate_by_name=True)


class CreateRestoreRequest(BaseModel):
    """Request to restore from backup."""

    backup_id: str
    mode: RestoreMode
    target: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None
    selections: Optional[Dict[str, Any]] = None
    conflict_resolution: ConflictResolution = ConflictResolution.SKIP


class CreateRestoreResponse(BaseModel):
    """Response for restore creation."""

    job_id: str
    status: JobStatus
    created_at: datetime
    backup_id: str
    mode: RestoreMode
    estimated_duration_seconds: Optional[int] = None
    message: str


class RestoreProgressResponse(BaseModel):
    """Restore progress response."""

    job_id: str
    status: JobStatus
    progress: Dict[str, Any]
    statistics: Dict[str, Any]
    errors: List[Dict[str, Any]]
    completed_at: Optional[datetime] = None


class PreviewBackupResponse(BaseModel):
    """Preview backup contents response."""

    backup_id: str
    name: str
    created_at: datetime
    type: BackupType
    contents: BackupContents
    filters: Optional[BackupFilters] = None
    size_bytes: int
    compressed_size_bytes: Optional[int] = None
    preview_data: Dict[str, Any]
    can_restore: bool
    warnings: List[str] = Field(default_factory=list)


class BackupScheduleRequest(BaseModel):
    """Request to schedule automatic backups."""

    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    schedule: str  # Cron expression
    type: BackupType
    filters: Optional[BackupFilters] = None
    options: Optional[BackupOptions] = None
    retention_days: int = Field(default=30, ge=1, le=365)
    enabled: bool = True

    @field_validator("schedule")
    @classmethod
    def validate_cron_expression(cls, v: str) -> str:
        # Basic cron validation (can be enhanced)
        parts = v.split()
        if len(parts) != 5:
            raise ValueError("Invalid cron expression format")
        return v


class BackupScheduleResponse(BaseModel):
    """Backup schedule response."""

    schedule_id: str
    name: str
    description: Optional[str] = None
    schedule: str
    type: BackupType
    filters: Optional[BackupFilters] = None
    options: Optional[BackupOptions] = None
    retention_days: int
    enabled: bool
    created_at: datetime
    next_run: datetime
    last_run: Optional[datetime] = None
    last_status: Optional[str] = None
