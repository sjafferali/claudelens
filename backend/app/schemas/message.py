"""Message schemas."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.project import PyObjectId


class MessageBase(BaseModel):
    """Base message schema."""
    uuid: str
    type: str  # user, assistant, summary
    session_id: str
    content: Optional[str] = None
    timestamp: datetime
    model: Optional[str] = None
    parent_uuid: Optional[str] = None


class MessageCreate(MessageBase):
    """Schema for creating a message."""
    project_path: Optional[str] = None  # Used to identify project
    usage: Optional[Dict[str, Any]] = None
    cost_usd: Optional[float] = None
    tool_use: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class Message(MessageBase):
    """Message response schema."""
    id: str = Field(alias="_id")
    created_at: datetime
    
    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class MessageDetail(Message):
    """Detailed message with all fields."""
    usage: Optional[Dict[str, Any]] = None
    cost_usd: Optional[float] = None
    tool_use: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    content_hash: Optional[str] = None