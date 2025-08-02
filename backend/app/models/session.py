"""Session model."""
from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class SessionInDB(BaseModel):
    """Session as stored in database."""

    id: ObjectId = Field(alias="_id")
    sessionId: str
    projectId: ObjectId
    startedAt: datetime
    endedAt: datetime
    messageCount: int = 0
    totalCost: float = 0.0
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
