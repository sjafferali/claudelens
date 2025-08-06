"""WebSocket event schemas."""
from datetime import datetime
from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field


class StatType(str, Enum):
    """Statistic types for real-time updates."""

    MESSAGES = "messages"
    TOOLS = "tools"
    TOKENS = "tokens"
    COST = "cost"


class AnimationType(str, Enum):
    """Animation types for stat updates."""

    INCREMENT = "increment"
    NONE = "none"


class StatUpdate(BaseModel):
    """Stat update data."""

    new_value: int = Field(..., description="New value for the statistic")
    formatted_value: str = Field(
        ..., description="Formatted display value (e.g., '262', '18', '45K', '$0.45')"
    )
    delta: int = Field(..., description="Change since last update")
    animation: AnimationType = Field(..., description="Animation type to use")


class StatUpdateEvent(BaseModel):
    """WebSocket event for stat updates."""

    type: Literal["stat_update"] = "stat_update"
    stat_type: StatType = Field(..., description="Type of statistic being updated")
    session_id: str = Field(..., description="Session ID the update relates to")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )
    update: StatUpdate = Field(..., description="Update data")


class MessagePreview(BaseModel):
    """Preview data for a new message."""

    uuid: str = Field(..., description="Message UUID")
    author: str = Field(..., description="Message author (user/assistant)")
    timestamp: datetime = Field(..., description="Message timestamp")
    preview: str = Field(..., description="Message preview text")
    tool_used: str | None = Field(None, description="Tool used in this message")


class NewMessageEvent(BaseModel):
    """WebSocket event for new messages."""

    type: Literal["new_message"] = "new_message"
    session_id: str = Field(..., description="Session ID the message belongs to")
    message: MessagePreview = Field(..., description="Message preview data")


class ConnectionEvent(BaseModel):
    """WebSocket connection status event."""

    type: Literal["connection"] = "connection"
    status: Literal["connected", "disconnected", "error"] = Field(
        ..., description="Connection status"
    )
    message: str | None = Field(None, description="Optional status message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )


class PingEvent(BaseModel):
    """WebSocket ping event."""

    type: Literal["ping"] = "ping"
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Ping timestamp"
    )


class PongEvent(BaseModel):
    """WebSocket pong response event."""

    type: Literal["pong"] = "pong"
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Pong timestamp"
    )


class DeletionProgressEvent(BaseModel):
    """WebSocket event for project deletion progress."""

    type: Literal["deletion_progress"] = "deletion_progress"
    project_id: str = Field(..., description="Project ID being deleted")
    stage: str = Field(..., description="Current deletion stage")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    message: str = Field(..., description="Progress message")
    completed: bool = Field(False, description="Whether deletion is complete")
    error: str | None = Field(None, description="Error message if deletion failed")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )


# Union type for all WebSocket events
WebSocketEvent = Union[
    StatUpdateEvent,
    NewMessageEvent,
    ConnectionEvent,
    PingEvent,
    PongEvent,
    DeletionProgressEvent,
]


class LiveSessionStats(BaseModel):
    """Live session statistics response."""

    session_id: str = Field(..., description="Session ID")
    message_count: int = Field(..., description="Current message count")
    tool_usage_count: int = Field(..., description="Current tool usage count")
    token_count: int = Field(..., description="Current token count")
    cost: float = Field(..., description="Current cost")
    last_activity: datetime | None = Field(None, description="Last activity timestamp")
    is_active: bool = Field(..., description="Whether the session is currently active")


class LiveStatsResponse(BaseModel):
    """Live statistics response."""

    total_messages: int = Field(..., description="Total message count")
    total_tools: int = Field(..., description="Total tool usage count")
    total_tokens: int = Field(..., description="Total token count")
    total_cost: float = Field(..., description="Total cost")
    active_sessions: int = Field(..., description="Number of active sessions")
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
