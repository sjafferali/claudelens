"""Export operation schemas."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateExportRequest(BaseModel):
    """Request schema for creating a new export job."""

    format: Literal["json", "csv", "markdown", "pdf"]
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("options", mode="before")
    @classmethod
    def validate_options(cls, v: Any) -> Dict[str, Any]:
        """Validate export options."""
        if v is None:
            return {}
        if isinstance(v, dict):
            # Validate splitSizeMb if provided
            if "splitSizeMb" in v:
                split_size = v["splitSizeMb"]
                if (
                    not isinstance(split_size, (int, float))
                    or not 1 <= split_size <= 500
                ):
                    raise ValueError("splitSizeMb must be between 1 and 500")
            # Validate encryption settings
            if v.get("encryption", {}).get("enabled"):
                if not v.get("encryption", {}).get("password"):
                    raise ValueError("Password required when encryption is enabled")
                if len(v["encryption"]["password"]) < 8:
                    raise ValueError("Password must be at least 8 characters")
        return v if isinstance(v, dict) else {}

    @field_validator("filters", mode="before")
    @classmethod
    def validate_filters(cls, v: Any) -> Dict[str, Any]:
        """Validate export filters."""
        if v is None:
            return {}
        if isinstance(v, dict):
            # Validate date range if provided
            if "dateRange" in v and v["dateRange"]:
                date_range = v["dateRange"]
                if "start" in date_range and "end" in date_range:
                    try:
                        start = datetime.fromisoformat(
                            date_range["start"].replace("Z", "+00:00")
                        )
                        end = datetime.fromisoformat(
                            date_range["end"].replace("Z", "+00:00")
                        )
                        if start > end:
                            raise ValueError("Start date must be before end date")
                    except (ValueError, TypeError) as e:
                        raise ValueError(f"Invalid date format: {e}")
            # Validate cost range if provided
            if "costRange" in v and v["costRange"]:
                cost_range = v["costRange"]
                if "min" in cost_range and "max" in cost_range:
                    if cost_range["min"] > cost_range["max"]:
                        raise ValueError(
                            "Min cost must be less than or equal to max cost"
                        )
        return v if isinstance(v, dict) else {}


class CreateExportResponse(BaseModel):
    """Response schema for export job creation."""

    job_id: str = Field(alias="jobId")
    status: Literal["queued", "processing"]
    estimated_size_bytes: int = Field(alias="estimatedSizeBytes")
    estimated_duration_seconds: int = Field(alias="estimatedDurationSeconds")
    created_at: str = Field(alias="createdAt")
    expires_at: str = Field(alias="expiresAt")

    model_config = ConfigDict(populate_by_name=True)


class ExportStatusResponse(BaseModel):
    """Response schema for export job status."""

    job_id: str = Field(alias="jobId")
    status: Literal["queued", "processing", "completed", "failed", "cancelled"]
    progress: Optional[Dict[str, Any]] = None
    current_item: Optional[str] = Field(None, alias="currentItem")
    file_info: Optional[Dict[str, Any]] = Field(None, alias="fileInfo")
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(alias="createdAt")
    started_at: Optional[str] = Field(None, alias="startedAt")
    completed_at: Optional[str] = Field(None, alias="completedAt")
    expires_at: str = Field(alias="expiresAt")

    model_config = ConfigDict(populate_by_name=True)


class CancelExportResponse(BaseModel):
    """Response schema for cancelling an export job."""

    job_id: str = Field(alias="jobId")
    status: Literal["cancelled"]
    message: str

    model_config = ConfigDict(populate_by_name=True)


class ExportJobListItem(BaseModel):
    """Schema for export job list item."""

    job_id: str = Field(alias="jobId")
    status: str
    format: str
    created_at: str = Field(alias="createdAt")
    completed_at: Optional[str] = Field(None, alias="completedAt")
    file_info: Optional[Dict[str, Any]] = Field(None, alias="fileInfo")

    model_config = ConfigDict(populate_by_name=True)


class PagedExportJobsResponse(BaseModel):
    """Response schema for paginated export jobs list."""

    content: List[ExportJobListItem]
    total_elements: int = Field(alias="totalElements")
    total_pages: int = Field(alias="totalPages")
    size: int
    number: int

    model_config = ConfigDict(populate_by_name=True)


class ExportedMessage(BaseModel):
    """Schema for exported message format."""

    id: str
    type: Literal["user", "assistant", "system", "tool_use", "tool_result"]
    content: str
    timestamp: str
    tokens: Optional[Dict[str, int]] = None
    cost_usd: Optional[float] = Field(None, alias="costUsd")
    model: Optional[str] = None
    tool_name: Optional[str] = Field(None, alias="toolName")
    tool_input: Optional[Any] = Field(None, alias="toolInput")
    attachments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(populate_by_name=True)


class ConversationBranch(BaseModel):
    """Schema for conversation branch."""

    id: str
    parent_message_id: str = Field(alias="parentMessageId")
    created_at: str = Field(alias="createdAt")
    messages: List[ExportedMessage]

    model_config = ConfigDict(populate_by_name=True)


class ExportedConversation(BaseModel):
    """Schema for exported conversation format."""

    id: str
    external_id: Optional[str] = Field(None, alias="externalId")
    title: str
    summary: Optional[str] = None
    project_id: Optional[str] = Field(None, alias="projectId")
    project_name: Optional[str] = Field(None, alias="projectName")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    duration_seconds: Optional[int] = Field(None, alias="durationSeconds")
    model: str
    cost_usd: float = Field(alias="costUsd")
    message_count: int = Field(alias="messageCount")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    messages: List[ExportedMessage]
    branches: Optional[List[ConversationBranch]] = None
    parent_conversation_id: Optional[str] = Field(None, alias="parentConversationId")

    model_config = ConfigDict(populate_by_name=True)
