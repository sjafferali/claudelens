"""Session schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.schemas.message import Message


class SessionBase(BaseModel):
    """Base session schema."""
    session_id: str = Field(alias="sessionId")
    project_id: str = Field(alias="projectId")
    summary: str | None = None
    started_at: datetime = Field(alias="startedAt")
    ended_at: datetime | None = Field(None, alias="endedAt")


class SessionCreate(SessionBase):
    """Schema for creating a session."""


class Session(SessionBase):
    """Session response schema."""
    id: str = Field(alias="_id")
    message_count: int = Field(0, alias="messageCount")
    total_cost: float | None = Field(None, alias="totalCost")
    
    model_config = ConfigDict(populate_by_name=True)
    
    @field_serializer('started_at', 'ended_at')
    def serialize_datetime(self, dt: datetime | None) -> str | None:
        return dt.isoformat() if dt else None


class SessionDetail(Session):
    """Detailed session with additional information."""
    models_used: list[str] = []
    first_message: str | None = None
    last_message: str | None = None
    messages: list[Message] | None = None  # Only included if requested


class SessionWithMessages(BaseModel):
    """Session with paginated messages."""
    session: Session
    messages: list[Message]
    skip: int
    limit: int