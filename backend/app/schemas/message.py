"""Message schemas."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class MessageBase(BaseModel):
    """Base message schema."""

    uuid: str
    type: str  # user, assistant, summary
    session_id: str
    content: str | None = None
    timestamp: datetime
    model: str | None = None
    parent_uuid: str | None = None


class MessageCreate(MessageBase):
    """Schema for creating a message."""

    project_path: str | None = None  # Used to identify project
    usage: dict[str, Any] | None = None
    cost_usd: float | None = None
    tool_use: list[dict[str, Any]] | None = None
    attachments: list[dict[str, Any]] | None = None


class Message(MessageBase):
    """Message response schema."""

    id: str = Field(alias="_id")
    created_at: datetime

    # Additional fields for frontend compatibility
    messageUuid: str | None = Field(default=None, alias="message_uuid")
    sessionId: str | None = Field(default=None, alias="session_id_alias")
    parentUuid: str | None = Field(default=None, alias="parent_uuid_alias")
    totalCost: float | None = None
    cost_usd: float | None = None
    inputTokens: int | None = None
    outputTokens: int | None = None
    usage: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)

    @field_serializer("timestamp", "created_at")
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()


class MessageDetail(Message):
    """Detailed message with all fields."""

    usage: dict[str, Any] | None = None
    cost_usd: float | None = None
    tool_use: list[dict[str, Any]] | None = None
    attachments: list[dict[str, Any]] | None = None
    content_hash: str | None = None
