"""Project schemas."""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.project import PyObjectId


class ProjectBase(BaseModel):
    """Base project schema."""
    name: str
    path: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = None
    description: Optional[str] = None


class Project(ProjectBase):
    """Project response schema."""
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ProjectStats(BaseModel):
    """Project statistics."""
    session_count: int = 0
    message_count: int = 0


class ProjectWithStats(Project):
    """Project with statistics."""
    stats: ProjectStats