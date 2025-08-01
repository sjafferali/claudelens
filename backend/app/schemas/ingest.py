"""Ingestion schemas."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class MessageIngest(BaseModel):
    """Schema for ingesting a message from Claude."""
    
    uuid: str = Field(..., description="Unique message identifier")
    type: str = Field(..., description="Message type (user, assistant, summary)")
    sessionId: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(..., description="Message timestamp")
    
    parentUuid: Optional[str] = Field(None, description="Parent message UUID")
    message: Optional[Dict[str, Any]] = Field(None, description="Message content")
    userType: Optional[str] = Field(None, description="User type (external, internal)")
    cwd: Optional[str] = Field(None, description="Working directory")
    version: Optional[str] = Field(None, description="Claude version")
    gitBranch: Optional[str] = Field(None, description="Git branch if applicable")
    isSidechain: bool = Field(False, description="Whether message is in sidechain")
    
    # Assistant-specific fields
    model: Optional[str] = Field(None, description="Model used")
    costUsd: Optional[float] = Field(None, description="Cost in USD")
    durationMs: Optional[int] = Field(None, description="Duration in milliseconds")
    requestId: Optional[str] = Field(None, description="API request ID")
    
    # User-specific fields
    toolUseResult: Optional[Dict[str, Any]] = Field(None, description="Tool execution results")
    
    # Summary fields
    summary: Optional[str] = Field(None, description="Conversation summary")
    leafUuid: Optional[str] = Field(None, description="Leaf UUID for summaries")
    
    # Additional fields stored as-is
    extra_fields: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"
    
    @validator("timestamp", pre=True)
    def parse_timestamp(cls, v):
        """Parse timestamp from string if needed."""
        if isinstance(v, str):
            # Handle 'Z' suffix
            if v.endswith('Z'):
                v = v[:-1] + '+00:00'
            return datetime.fromisoformat(v)
        return v
    
    def __init__(self, **data):
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
    todos: List[Dict[str, Any]] = Field(..., description="Todo items")
    todoCount: int = Field(..., description="Number of todo items")


class ConfigIngest(BaseModel):
    """Schema for ingesting configuration data."""
    
    config: Optional[Dict[str, Any]] = Field(None, description="config.json contents")
    settings: Optional[Dict[str, Any]] = Field(None, description="settings.json contents")
    userId: Optional[str] = Field(None, description="User ID from config")


class BatchIngestRequest(BaseModel):
    """Request for batch message ingestion."""
    
    messages: List[MessageIngest] = Field(
        default_factory=list,
        description="List of messages to ingest",
        max_items=1000
    )
    todos: List[TodoIngest] = Field(
        default_factory=list,
        description="List of todo files to ingest"
    )
    config: Optional[ConfigIngest] = Field(
        None,
        description="Configuration data to ingest"
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
    
    projects_created: List[str] = Field(
        default_factory=list,
        description="IDs of newly created projects"
    )
    
    duration_ms: int = Field(0, description="Processing duration in milliseconds")


class BatchIngestResponse(BaseModel):
    """Response from batch ingestion."""
    
    success: bool
    stats: IngestStats
    message: str
    errors: Optional[List[Dict[str, Any]]] = None