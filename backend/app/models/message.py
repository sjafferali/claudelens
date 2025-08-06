"""Message model."""

from datetime import datetime
from typing import Any

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class MessageInDB(BaseModel):
    """Message as stored in database."""

    id: ObjectId = Field(alias="_id")
    uuid: str
    sessionId: str
    type: str
    timestamp: datetime

    parentUuid: str | None = None
    message: dict[str, Any] | None = None
    userType: str | None = None
    cwd: str | None = None
    version: str | None = None
    gitBranch: str | None = None
    isSidechain: bool = False

    # Assistant-specific
    model: str | None = None
    costUsd: float | None = None
    durationMs: int | None = None
    requestId: str | None = None

    # User-specific
    toolUseResult: dict[str, Any] | None = None

    # Summary fields
    summary: str | None = None
    leafUuid: str | None = None

    # Metadata
    contentHash: str
    metadata: dict[str, Any] | None = None
    createdAt: datetime

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
