"""Prompt schemas for API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


# Base schemas
class PromptVersionBase(BaseModel):
    """Base schema for prompt version."""

    version: str
    content: str
    variables: list[str]
    change_log: str


class FolderBase(BaseModel):
    """Base schema for folder."""

    name: str
    parent_id: Optional[str] = None


class PromptBase(BaseModel):
    """Base prompt schema."""

    name: str
    description: Optional[str] = None
    content: str
    tags: list[str] = []
    folder_id: Optional[str] = None
    visibility: str = "private"


# Create schemas
class FolderCreate(FolderBase):
    """Schema for creating a folder."""


class PromptCreate(PromptBase):
    """Schema for creating a prompt."""


# Update schemas
class FolderUpdate(BaseModel):
    """Schema for updating a folder."""

    name: Optional[str] = None
    parent_id: Optional[str] = None


class PromptUpdate(BaseModel):
    """Schema for updating a prompt."""

    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[list[str]] = None
    folder_id: Optional[str] = None
    visibility: Optional[str] = None
    is_starred: Optional[bool] = None


# Response schemas
class PromptVersion(PromptVersionBase):
    """Prompt version response schema."""

    created_at: datetime = Field(alias="createdAt")
    created_by: str = Field(alias="createdBy")

    model_config = ConfigDict(populate_by_name=True)

    @field_serializer("created_at")
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()


class Folder(FolderBase):
    """Folder response schema."""

    id: str = Field(alias="_id")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    created_by: str = Field(alias="createdBy")
    prompt_count: int = 0  # Added for UI display

    model_config = ConfigDict(populate_by_name=True)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()


class Prompt(PromptBase):
    """Prompt response schema."""

    id: str = Field(alias="_id")
    variables: list[str] = []
    version: str = "1.0.0"
    use_count: int = Field(0, alias="useCount")
    is_starred: bool = Field(False, alias="isStarred")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    created_by: str = Field(alias="createdBy")

    model_config = ConfigDict(populate_by_name=True)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()


class PromptDetail(Prompt):
    """Detailed prompt response schema with all fields."""

    versions: list[PromptVersion] = []
    shared_with: list[str] = Field(default=[], alias="sharedWith")
    public_url: Optional[str] = Field(None, alias="publicUrl")
    last_used_at: Optional[datetime] = Field(None, alias="lastUsedAt")
    avg_response_time: Optional[float] = Field(None, alias="avgResponseTime")
    success_rate: Optional[float] = Field(None, alias="successRate")

    @field_serializer("last_used_at")
    def serialize_last_used(self, dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat() if dt else None


# Request/Response models for special operations
class PromptShareRequest(BaseModel):
    """Request schema for sharing a prompt."""

    user_ids: list[str]
    visibility: str = "team"  # team or public


class PromptTestRequest(BaseModel):
    """Request schema for testing a prompt."""

    variables: dict[str, str]


class PromptTestResponse(BaseModel):
    """Response schema for prompt test."""

    result: str
    variables_used: dict[str, str]
    execution_time_ms: float


class PromptExportRequest(BaseModel):
    """Request schema for exporting prompts."""

    format: str = "json"  # json, csv, markdown
    prompt_ids: Optional[list[str]] = None  # None means all
    include_versions: bool = False


class PromptImportRequest(BaseModel):
    """Request schema for importing prompts."""

    format: str = "json"  # json, csv, markdown
    content: str
    folder_id: Optional[str] = None
