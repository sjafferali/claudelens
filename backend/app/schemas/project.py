"""Project schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ProjectBase(BaseModel):
    """Base project schema."""

    name: str
    path: str
    description: str | None = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: str | None = None
    description: str | None = None


class Project(ProjectBase):
    """Project response schema."""

    id: str = Field(alias="_id")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()


class ProjectStats(BaseModel):
    """Project statistics."""

    session_count: int = 0
    message_count: int = 0


class ProjectWithStats(Project):
    """Project with statistics."""

    stats: ProjectStats
