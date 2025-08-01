"""Message model."""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId


class MessageInDB(BaseModel):
    """Message as stored in database."""
    
    id: ObjectId = Field(alias="_id")
    uuid: str
    sessionId: str
    type: str
    timestamp: datetime
    
    parentUuid: Optional[str] = None
    message: Optional[Dict[str, Any]] = None
    userType: Optional[str] = None
    cwd: Optional[str] = None
    version: Optional[str] = None
    gitBranch: Optional[str] = None
    isSidechain: bool = False
    
    # Assistant-specific
    model: Optional[str] = None
    costUsd: Optional[float] = None
    durationMs: Optional[int] = None
    requestId: Optional[str] = None
    
    # User-specific
    toolUseResult: Optional[Dict[str, Any]] = None
    
    # Summary fields
    summary: Optional[str] = None
    leafUuid: Optional[str] = None
    
    # Metadata
    contentHash: str
    metadata: Optional[Dict[str, Any]] = None
    createdAt: datetime
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True