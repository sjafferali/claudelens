"""Session schemas."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.project import PyObjectId
from app.schemas.message import Message


class SessionBase(BaseModel):
    """Base session schema."""
    session_id: str
    project_id: str
    summary: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None


class SessionCreate(SessionBase):
    """Schema for creating a session."""
    pass


class Session(SessionBase):
    """Session response schema."""
    id: str = Field(alias="_id")
    message_count: int = 0
    total_cost: Optional[float] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class SessionDetail(Session):
    """Detailed session with additional information."""
    models_used: List[str] = []
    first_message: Optional[str] = None
    last_message: Optional[str] = None
    messages: Optional[List[Message]] = None  # Only included if requested


class SessionWithMessages(BaseModel):
    """Session with paginated messages."""
    session: Session
    messages: List[Message]
    skip: int
    limit: int