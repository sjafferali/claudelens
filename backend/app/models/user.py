"""User model with API key management."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class APIKey(BaseModel):
    """API Key associated with a user."""

    key_hash: str
    name: str
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    active: bool = True


class UserInDB(BaseModel):
    """User as stored in database."""

    id: ObjectId = Field(alias="_id")
    email: str
    username: str
    password_hash: Optional[str] = None  # For password authentication
    role: UserRole = UserRole.USER
    api_keys: List[APIKey] = []
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    # Usage statistics (denormalized for performance)
    project_count: int = 0
    session_count: int = 0
    message_count: int = 0
    total_disk_usage: int = 0  # in bytes

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class UserCreate(BaseModel):
    """User creation model."""

    email: str
    username: str
    password: Optional[str] = None  # Optional password for UI users
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    """User update model."""

    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None  # For password changes
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response model for API."""

    id: str
    email: str
    username: str
    role: UserRole
    created_at: datetime
    updated_at: datetime
    project_count: int
    session_count: int
    message_count: int
    total_disk_usage: int
    api_key_count: int

    model_config = ConfigDict(from_attributes=True)
