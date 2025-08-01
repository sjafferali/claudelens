# Task 09: Backend Ingestion API Implementation

## Status
**Status:** TODO  
**Priority:** High  
**Estimated Time:** 3 hours

## Purpose
Implement the ingestion API endpoints that receive conversation data from the CLI tool. This includes batch message processing, deduplication, and efficient storage in MongoDB.

## Current State
- API structure exists
- Database models defined
- No ingestion endpoints
- No message processing logic

## Target State
- Ingestion endpoints accepting batch messages
- Message validation and normalization
- Deduplication to prevent duplicates
- Efficient batch insertion into MongoDB
- Project auto-creation from messages
- Response with ingestion statistics

## Implementation Details

### 1. Ingestion Router

**`backend/app/api/api_v1/endpoints/ingest.py`:**
```python
"""Ingestion API endpoints."""
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from datetime import datetime

from app.api.dependencies import CommonDeps, AuthDeps
from app.schemas.ingest import (
    BatchIngestRequest,
    BatchIngestResponse,
    IngestStats,
    MessageIngest
)
from app.services.ingest import IngestService
from app.core.exceptions import ValidationError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/batch", response_model=BatchIngestResponse)
async def ingest_batch(
    request: BatchIngestRequest,
    background_tasks: BackgroundTasks,
    db: CommonDeps,
    api_key: AuthDeps
) -> BatchIngestResponse:
    """Ingest a batch of messages.
    
    Accepts up to 1000 messages per request. Messages are validated,
    deduplicated, and stored in the database. Returns statistics about
    the ingestion process.
    """
    # Validate batch size
    if len(request.messages) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Batch size exceeds maximum of 1000 messages"
        )
    
    if not request.messages:
        raise HTTPException(
            status_code=400,
            detail="No messages provided"
        )
    
    # Initialize service
    ingest_service = IngestService(db)
    
    try:
        # Process messages
        stats = await ingest_service.ingest_messages(request.messages)
        
        # Schedule background tasks
        if stats.projects_created:
            background_tasks.add_task(
                update_project_metadata,
                db,
                stats.projects_created
            )
        
        return BatchIngestResponse(
            success=True,
            stats=stats,
            message="Batch ingestion completed successfully"
        )
        
    except ValidationError as e:
        logger.error(f"Validation error during ingestion: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error during batch ingestion: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to process batch"
        )


@router.post("/message", response_model=BatchIngestResponse)
async def ingest_single(
    message: MessageIngest,
    db: CommonDeps,
    api_key: AuthDeps
) -> BatchIngestResponse:
    """Ingest a single message.
    
    Convenience endpoint for ingesting individual messages.
    """
    return await ingest_batch(
        BatchIngestRequest(messages=[message]),
        BackgroundTasks(),
        db,
        api_key
    )


@router.get("/status")
async def ingestion_status(
    db: CommonDeps,
    api_key: AuthDeps
) -> Dict[str, Any]:
    """Get ingestion system status.
    
    Returns current ingestion statistics and system health.
    """
    # Get collection stats
    messages_count = await db.messages.estimated_document_count()
    sessions_count = await db.sessions.estimated_document_count()
    projects_count = await db.projects.estimated_document_count()
    
    # Get recent ingestion stats
    recent_ingests = await db.ingestion_logs.find(
        {},
        limit=10,
        sort=[("timestamp", -1)]
    ).to_list(10)
    
    return {
        "status": "operational",
        "statistics": {
            "total_messages": messages_count,
            "total_sessions": sessions_count,
            "total_projects": projects_count
        },
        "recent_ingestions": [
            {
                "timestamp": log["timestamp"],
                "messages_processed": log["messages_processed"],
                "duration_ms": log["duration_ms"]
            }
            for log in recent_ingests
        ]
    }


async def update_project_metadata(db: AsyncIOMotorDatabase, project_ids: List[str]):
    """Background task to update project metadata."""
    try:
        for project_id in project_ids:
            # Count messages and sessions
            pipeline = [
                {"$match": {"projectId": project_id}},
                {"$group": {
                    "_id": None,
                    "message_count": {"$sum": 1},
                    "session_count": {"$addToSet": "$sessionId"}
                }}
            ]
            
            result = await db.messages.aggregate(pipeline).to_list(1)
            if result:
                stats = result[0]
                await db.projects.update_one(
                    {"_id": project_id},
                    {
                        "$set": {
                            "stats.message_count": stats["message_count"],
                            "stats.session_count": len(stats["session_count"]),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
    except Exception as e:
        logger.error(f"Error updating project metadata: {e}")
```

### 2. Ingestion Schemas

**`backend/app/schemas/ingest.py`:**
```python
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
```

### 3. Ingestion Service

**`backend/app/services/ingest.py`:**
```python
"""Ingestion service for processing messages."""
import asyncio
from typing import List, Dict, Any, Set, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import hashlib
import json
import logging

from app.schemas.ingest import MessageIngest, IngestStats
from app.models.message import MessageInDB
from app.models.session import SessionInDB
from app.models.project import ProjectInDB

logger = logging.getLogger(__name__)


class IngestService:
    """Service for ingesting Claude messages."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._project_cache: Dict[str, ObjectId] = {}
        self._session_cache: Dict[str, ObjectId] = {}
    
    async def ingest_messages(self, messages: List[MessageIngest]) -> IngestStats:
        """Ingest a batch of messages."""
        start_time = datetime.utcnow()
        stats = IngestStats(messages_received=len(messages))
        
        # Group messages by session
        sessions_map: Dict[str, List[MessageIngest]] = {}
        for message in messages:
            session_id = message.sessionId
            if session_id not in sessions_map:
                sessions_map[session_id] = []
            sessions_map[session_id].append(message)
        
        # Process each session
        tasks = []
        for session_id, session_messages in sessions_map.items():
            task = self._process_session_messages(session_id, session_messages, stats)
            tasks.append(task)
        
        # Run all sessions in parallel
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        stats.duration_ms = int(duration)
        
        # Log ingestion
        await self._log_ingestion(stats)
        
        return stats
    
    async def _process_session_messages(
        self,
        session_id: str,
        messages: List[MessageIngest],
        stats: IngestStats
    ):
        """Process messages for a single session."""
        try:
            # Ensure session exists
            session_obj_id = await self._ensure_session(session_id, messages[0])
            if session_obj_id:
                stats.sessions_created += 1
            else:
                stats.sessions_updated += 1
            
            # Get existing message hashes for deduplication
            existing_hashes = await self._get_existing_hashes(session_id)
            
            # Process each message
            new_messages = []
            for message in messages:
                # Generate hash for deduplication
                message_hash = self._hash_message(message)
                
                if message_hash in existing_hashes:
                    stats.messages_skipped += 1
                    continue
                
                # Convert to database model
                try:
                    message_doc = self._message_to_doc(message, session_id)
                    new_messages.append(message_doc)
                    existing_hashes.add(message_hash)
                except Exception as e:
                    logger.error(f"Error processing message {message.uuid}: {e}")
                    stats.messages_failed += 1
            
            # Bulk insert new messages
            if new_messages:
                result = await self.db.messages.insert_many(new_messages)
                stats.messages_processed += len(result.inserted_ids)
                
                # Update session statistics
                await self._update_session_stats(session_id)
            
        except Exception as e:
            logger.error(f"Error processing session {session_id}: {e}")
            stats.messages_failed += len(messages)
    
    async def _ensure_session(
        self,
        session_id: str,
        first_message: MessageIngest
    ) -> Optional[ObjectId]:
        """Ensure session exists, create if needed."""
        # Check cache first
        if session_id in self._session_cache:
            return None
        
        # Check database
        existing = await self.db.sessions.find_one({"sessionId": session_id})
        if existing:
            self._session_cache[session_id] = existing["_id"]
            return None
        
        # Extract project info from path
        project_path = None
        project_name = "Unknown Project"
        
        if first_message.cwd:
            # Extract project from Claude path format
            # e.g., /Users/user/projects/my-project -> my-project
            parts = first_message.cwd.split('/')
            if 'projects' in parts:
                idx = parts.index('projects')
                if idx + 1 < len(parts):
                    project_name = parts[idx + 1]
                    project_path = '/'.join(parts[:idx + 2])
        
        # Ensure project exists
        project_id = await self._ensure_project(project_path or first_message.cwd, project_name)
        
        # Create session
        session_doc = {
            "_id": ObjectId(),
            "sessionId": session_id,
            "projectId": project_id,
            "startedAt": first_message.timestamp,
            "endedAt": first_message.timestamp,
            "messageCount": 0,
            "totalCost": 0.0,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        await self.db.sessions.insert_one(session_doc)
        self._session_cache[session_id] = session_doc["_id"]
        
        return session_doc["_id"]
    
    async def _ensure_project(self, project_path: str, project_name: str) -> ObjectId:
        """Ensure project exists, create if needed."""
        # Check cache first
        if project_path in self._project_cache:
            return self._project_cache[project_path]
        
        # Check database
        existing = await self.db.projects.find_one({"path": project_path})
        if existing:
            self._project_cache[project_path] = existing["_id"]
            return existing["_id"]
        
        # Create project
        project_doc = {
            "_id": ObjectId(),
            "name": project_name,
            "path": project_path,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
            "stats": {
                "message_count": 0,
                "session_count": 0
            }
        }
        
        await self.db.projects.insert_one(project_doc)
        self._project_cache[project_path] = project_doc["_id"]
        
        return project_doc["_id"]
    
    async def _get_existing_hashes(self, session_id: str) -> Set[str]:
        """Get existing message hashes for a session."""
        cursor = self.db.messages.find(
            {"sessionId": session_id},
            {"contentHash": 1}
        )
        
        hashes = set()
        async for doc in cursor:
            if "contentHash" in doc:
                hashes.add(doc["contentHash"])
        
        return hashes
    
    def _hash_message(self, message: MessageIngest) -> str:
        """Generate hash for message deduplication."""
        # Create deterministic string representation
        hash_data = {
            "uuid": message.uuid,
            "type": message.type,
            "timestamp": message.timestamp.isoformat(),
            "content": message.message
        }
        
        content = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _message_to_doc(self, message: MessageIngest, session_id: str) -> dict:
        """Convert message to database document."""
        doc = {
            "_id": ObjectId(),
            "uuid": message.uuid,
            "sessionId": session_id,
            "type": message.type,
            "timestamp": message.timestamp,
            "parentUuid": message.parentUuid,
            "contentHash": self._hash_message(message),
            "createdAt": datetime.utcnow()
        }
        
        # Add message content
        if message.message:
            doc["message"] = message.message
        
        # Add optional fields
        optional_fields = [
            "userType", "cwd", "model", "costUsd", "durationMs"
        ]
        for field in optional_fields:
            value = getattr(message, field, None)
            if value is not None:
                doc[field] = value
        
        # Add any extra fields
        if message.extra_fields:
            doc["metadata"] = message.extra_fields
        
        return doc
    
    async def _update_session_stats(self, session_id: str):
        """Update session statistics."""
        # Aggregate statistics
        pipeline = [
            {"$match": {"sessionId": session_id}},
            {"$group": {
                "_id": None,
                "messageCount": {"$sum": 1},
                "totalCost": {"$sum": {"$ifNull": ["$costUsd", 0]}},
                "startTime": {"$min": "$timestamp"},
                "endTime": {"$max": "$timestamp"}
            }}
        ]
        
        result = await self.db.messages.aggregate(pipeline).to_list(1)
        
        if result:
            stats = result[0]
            await self.db.sessions.update_one(
                {"sessionId": session_id},
                {
                    "$set": {
                        "messageCount": stats["messageCount"],
                        "totalCost": stats["totalCost"],
                        "startedAt": stats["startTime"],
                        "endedAt": stats["endTime"],
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
    
    async def _log_ingestion(self, stats: IngestStats):
        """Log ingestion statistics."""
        log_entry = {
            "timestamp": datetime.utcnow(),
            "messages_processed": stats.messages_processed,
            "messages_skipped": stats.messages_skipped,
            "messages_failed": stats.messages_failed,
            "duration_ms": stats.duration_ms
        }
        
        await self.db.ingestion_logs.insert_one(log_entry)
```

### 4. Message Validation Service

**`backend/app/services/validation.py`:**
```python
"""Message validation service."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from app.core.exceptions import ValidationError


class MessageValidator:
    """Validates Claude messages."""
    
    # Valid message types
    VALID_TYPES = {"user", "assistant", "system", "tool", "summary"}
    
    # UUID pattern
    UUID_PATTERN = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    @classmethod
    def validate_message(cls, message: Dict[str, Any]) -> List[str]:
        """Validate a message and return list of errors."""
        errors = []
        
        # Required fields
        if "uuid" not in message:
            errors.append("Missing required field: uuid")
        elif not cls.UUID_PATTERN.match(str(message["uuid"])):
            errors.append("Invalid UUID format")
        
        if "type" not in message:
            errors.append("Missing required field: type")
        elif message["type"] not in cls.VALID_TYPES:
            errors.append(f"Invalid message type: {message['type']}")
        
        if "timestamp" not in message:
            errors.append("Missing required field: timestamp")
        
        if "sessionId" not in message:
            errors.append("Missing required field: sessionId")
        
        # Type-specific validation
        if message.get("type") == "assistant":
            if "message" not in message:
                errors.append("Assistant messages must have 'message' field")
        
        # Cost validation
        if "costUsd" in message:
            try:
                cost = float(message["costUsd"])
                if cost < 0 or cost > 100:  # Sanity check
                    errors.append("Cost value out of reasonable range")
            except (TypeError, ValueError):
                errors.append("Invalid cost value")
        
        return errors
    
    @classmethod
    def sanitize_message(cls, message: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize message content."""
        # Remove any potential XSS or injection attempts
        if "message" in message and isinstance(message["message"], dict):
            if "content" in message["message"]:
                # Basic sanitization - in production use a proper library
                content = str(message["message"]["content"])
                # Remove script tags
                content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
                message["message"]["content"] = content
        
        return message
```

## Required Technologies
- FastAPI
- Motor (async MongoDB driver)
- Pydantic for validation
- asyncio for concurrent processing

## Success Criteria
- [ ] Batch ingestion endpoint accepts messages, todos, and config
- [ ] Messages are validated and normalized
- [ ] All Claude message types handled (user, assistant, summary)
- [ ] Todo lists associated with correct sessions
- [ ] Configuration data stored for user preferences
- [ ] Deduplication prevents duplicate messages
- [ ] Projects and sessions auto-created as needed
- [ ] Efficient bulk insertion into MongoDB
- [ ] Proper error handling and reporting
- [ ] Background tasks update statistics
- [ ] API documentation shows all endpoints
- [ ] Performance: Can process 1000 messages in < 5 seconds

## Notes
- Use bulk operations for efficiency
- Hash messages for deduplication
- Cache project/session lookups during batch
- Validate messages but be flexible with schema
- Log all ingestion operations for debugging