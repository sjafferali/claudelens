"""Session model."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId


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
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True