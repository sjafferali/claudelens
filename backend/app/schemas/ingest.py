"""Ingestion schemas."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageIngest(BaseModel):
    """Schema for ingesting a message from Claude."""

    uuid: str = Field(..., description="Unique message identifier")
    type: str = Field(..., description="Message type (user, assistant, summary)")
    sessionId: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(..., description="Message timestamp")

    parentUuid: str | None = Field(None, description="Parent message UUID")
    message: dict[str, Any] | None = Field(None, description="Message content")
    userType: str | None = Field(None, description="User type (external, internal)")
    cwd: str | None = Field(None, description="Working directory")
    version: str | None = Field(None, description="Claude version")
    gitBranch: str | None = Field(None, description="Git branch if applicable")
    isSidechain: bool = Field(False, description="Whether message is in sidechain")

    # Assistant-specific fields
    model: str | None = Field(None, description="Model used")
    costUsd: float | None = Field(None, description="Cost in USD")
    durationMs: int | None = Field(None, description="Duration in milliseconds")
    requestId: str | None = Field(None, description="API request ID")

    # User-specific fields
    toolUseResult: dict[str, Any] | None = Field(
        None, description="Tool execution results"
    )

    # Summary fields
    summary: str | None = Field(None, description="Conversation summary")
    leafUuid: str | None = Field(None, description="Leaf UUID for summaries")

    # Additional fields stored as-is
    extra_fields: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: Any) -> datetime:
        """Parse timestamp from string if needed."""
        if isinstance(v, str):
            # Handle 'Z' suffix
            if v.endswith("Z"):
                v = v[:-1] + "+00:00"
            return datetime.fromisoformat(v)
        if isinstance(v, datetime):
            return v
        raise ValueError(f"Invalid timestamp value: {v}")

    def __init__(self, **data: Any) -> None:
        """Custom init to handle extra fields."""
        # Extract known fields
        known_fields = set(self.__fields__.keys())
        known_data = {k: v for k, v in data.items() if k in known_fields}
        extra_data = {k: v for k, v in data.items() if k not in known_fields}

        # Initialize with known fields
        super().__init__(**known_data)

        # Store extra fields
        self.extra_fields = extra_data


class TodoIngest(BaseModel):
    """Schema for ingesting todo lists."""

    sessionId: str = Field(..., description="Session ID the todos belong to")
    filename: str = Field(..., description="Original filename")
    todos: list[dict[str, Any]] = Field(..., description="Todo items")
    todoCount: int = Field(..., description="Number of todo items")


class ConfigIngest(BaseModel):
    """Schema for ingesting configuration data."""

    config: dict[str, Any] | None = Field(None, description="config.json contents")
    settings: dict[str, Any] | None = Field(None, description="settings.json contents")
    userId: str | None = Field(None, description="User ID from config")


class BatchIngestRequest(BaseModel):
    """Request for batch message ingestion."""

    messages: list[MessageIngest] = Field(
        default_factory=list, description="List of messages to ingest", max_length=1000
    )
    todos: list[TodoIngest] = Field(
        default_factory=list, description="List of todo files to ingest"
    )
    config: ConfigIngest | None = Field(
        None, description="Configuration data to ingest"
    )


class IngestStats(BaseModel):
    """Statistics from ingestion process."""

    messages_received: int = Field(0, description="Total messages received")
    messages_processed: int = Field(0, description="Messages successfully processed")
    messages_skipped: int = Field(0, description="Messages skipped (duplicates)")
    messages_failed: int = Field(0, description="Messages that failed processing")

    sessions_created: int = Field(0, description="New sessions created")
    sessions_updated: int = Field(0, description="Existing sessions updated")

    todos_processed: int = Field(0, description="Todo files processed")
    config_updated: bool = Field(False, description="Config data updated")

    projects_created: list[str] = Field(
        default_factory=list, description="IDs of newly created projects"
    )

    duration_ms: int = Field(0, description="Processing duration in milliseconds")


class BatchIngestResponse(BaseModel):
    """Response from batch ingestion."""

    success: bool
    stats: IngestStats
    message: str
    errors: list[dict[str, Any]] | None = None
