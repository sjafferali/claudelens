# Task 10: Backend Query APIs Implementation

## Status
**Status:** TODO  
**Priority:** High  
**Estimated Time:** 4 hours

## Purpose
Implement the query API endpoints for retrieving projects, sessions, and messages. These endpoints power the frontend's browsing and viewing capabilities with efficient pagination, filtering, and data retrieval.

## Current State
- API structure exists
- Database models defined
- No query endpoints implemented
- No pagination utilities

## Target State
- Complete CRUD endpoints for projects, sessions, and messages
- Efficient pagination with cursor support
- Filtering and sorting capabilities
- Optimized queries with proper projections
- Thread reconstruction for conversations
- Response caching for common queries

## Implementation Details

### 1. Projects API Endpoints

**`backend/app/api/api_v1/endpoints/projects.py`:**
```python
"""Projects API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.api.dependencies import CommonDeps
from app.schemas.project import Project, ProjectCreate, ProjectUpdate, ProjectWithStats
from app.schemas.common import PaginatedResponse
from app.services.project import ProjectService
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ProjectWithStats])
async def list_projects(
    db: CommonDeps,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search in project names"),
    sort_by: str = Query("updated_at", regex="^(name|created_at|updated_at|message_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
) -> PaginatedResponse[ProjectWithStats]:
    """List all projects with pagination and filtering.
    
    Returns projects with their statistics including message and session counts.
    """
    service = ProjectService(db)
    
    # Build filter
    filter_dict = {}
    if search:
        filter_dict["$text"] = {"$search": search}
    
    # Get projects
    projects, total = await service.list_projects(
        filter_dict=filter_dict,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return PaginatedResponse(
        items=projects,
        total=total,
        skip=skip,
        limit=limit,
        has_more=skip + limit < total
    )


@router.get("/{project_id}", response_model=ProjectWithStats)
async def get_project(
    project_id: str,
    db: CommonDeps
) -> ProjectWithStats:
    """Get a specific project by ID.
    
    Returns the project with detailed statistics.
    """
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    service = ProjectService(db)
    project = await service.get_project(ObjectId(project_id))
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    return project


@router.post("/", response_model=Project, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: CommonDeps
) -> Project:
    """Create a new project.
    
    Projects are usually created automatically during ingestion,
    but this endpoint allows manual creation.
    """
    service = ProjectService(db)
    
    # Check if project with same path exists
    existing = await service.get_project_by_path(project.path)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Project with path '{project.path}' already exists"
        )
    
    created = await service.create_project(project)
    return created


@router.patch("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    update: ProjectUpdate,
    db: CommonDeps
) -> Project:
    """Update a project's metadata."""
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    service = ProjectService(db)
    updated = await service.update_project(ObjectId(project_id), update)
    
    if not updated:
        raise NotFoundError("Project", project_id)
    
    return updated


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    db: CommonDeps,
    cascade: bool = Query(False, description="Delete all associated data")
):
    """Delete a project.
    
    If cascade=true, also deletes all sessions and messages.
    Otherwise, only deletes the project metadata.
    """
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    service = ProjectService(db)
    deleted = await service.delete_project(ObjectId(project_id), cascade=cascade)
    
    if not deleted:
        raise NotFoundError("Project", project_id)


@router.get("/{project_id}/stats")
async def get_project_stats(
    project_id: str,
    db: CommonDeps
) -> dict:
    """Get detailed statistics for a project.
    
    Returns message counts by type, cost breakdown, and activity timeline.
    """
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    service = ProjectService(db)
    stats = await service.get_project_statistics(ObjectId(project_id))
    
    if not stats:
        raise NotFoundError("Project", project_id)
    
    return stats
```

### 2. Sessions API Endpoints

**`backend/app/api/api_v1/endpoints/sessions.py`:**
```python
"""Sessions API endpoints."""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.api.dependencies import CommonDeps
from app.schemas.session import Session, SessionDetail, SessionWithMessages
from app.schemas.common import PaginatedResponse
from app.services.session import SessionService
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[Session])
async def list_sessions(
    db: CommonDeps,
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search in session summaries"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    sort_by: str = Query("started_at", regex="^(started_at|ended_at|message_count|total_cost)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
) -> PaginatedResponse[Session]:
    """List sessions with pagination and filtering."""
    service = SessionService(db)
    
    # Build filter
    filter_dict = {}
    if project_id:
        if not ObjectId.is_valid(project_id):
            raise HTTPException(status_code=400, detail="Invalid project ID")
        filter_dict["projectId"] = ObjectId(project_id)
    
    if search:
        filter_dict["$text"] = {"$search": search}
    
    if start_date:
        filter_dict["startedAt"] = {"$gte": start_date}
    
    if end_date:
        if "startedAt" in filter_dict:
            filter_dict["startedAt"]["$lte"] = end_date
        else:
            filter_dict["startedAt"] = {"$lte": end_date}
    
    # Get sessions
    sessions, total = await service.list_sessions(
        filter_dict=filter_dict,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return PaginatedResponse(
        items=sessions,
        total=total,
        skip=skip,
        limit=limit,
        has_more=skip + limit < total
    )


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: str,
    db: CommonDeps,
    include_messages: bool = Query(False, description="Include first 10 messages")
) -> SessionDetail:
    """Get a specific session by ID."""
    service = SessionService(db)
    session = await service.get_session(session_id, include_messages=include_messages)
    
    if not session:
        raise NotFoundError("Session", session_id)
    
    return session


@router.get("/{session_id}/messages", response_model=SessionWithMessages)
async def get_session_messages(
    session_id: str,
    db: CommonDeps,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
) -> SessionWithMessages:
    """Get all messages for a session.
    
    Returns messages in chronological order with pagination.
    """
    service = SessionService(db)
    
    # Get session
    session = await service.get_session(session_id)
    if not session:
        raise NotFoundError("Session", session_id)
    
    # Get messages
    messages = await service.get_session_messages(
        session_id,
        skip=skip,
        limit=limit
    )
    
    return SessionWithMessages(
        session=session,
        messages=messages,
        skip=skip,
        limit=limit
    )


@router.get("/{session_id}/thread/{message_uuid}")
async def get_message_thread(
    session_id: str,
    message_uuid: str,
    db: CommonDeps,
    depth: int = Query(10, ge=1, le=100, description="Maximum thread depth")
) -> dict:
    """Get the conversation thread for a specific message.
    
    Returns the message and its parent/child messages up to the specified depth.
    """
    service = SessionService(db)
    thread = await service.get_message_thread(session_id, message_uuid, depth)
    
    if not thread:
        raise NotFoundError("Message thread", f"{session_id}/{message_uuid}")
    
    return thread


@router.post("/{session_id}/generate-summary")
async def generate_session_summary(
    session_id: str,
    db: CommonDeps
) -> dict:
    """Generate or regenerate a summary for a session.
    
    Uses the first and last few messages to create a concise summary.
    """
    service = SessionService(db)
    summary = await service.generate_summary(session_id)
    
    if not summary:
        raise NotFoundError("Session", session_id)
    
    return {"session_id": session_id, "summary": summary}
```

### 3. Messages API Endpoints

**`backend/app/api/api_v1/endpoints/messages.py`:**
```python
"""Messages API endpoints."""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import CommonDeps
from app.schemas.message import Message, MessageDetail
from app.schemas.common import PaginatedResponse
from app.services.message import MessageService
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[Message])
async def list_messages(
    db: CommonDeps,
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    type: Optional[str] = Query(None, description="Filter by message type"),
    model: Optional[str] = Query(None, description="Filter by model"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort_order: str = Query("asc", regex="^(asc|desc)$")
) -> PaginatedResponse[Message]:
    """List messages with pagination and filtering.
    
    By default, returns messages in chronological order.
    """
    service = MessageService(db)
    
    # Build filter
    filter_dict = {}
    if session_id:
        filter_dict["sessionId"] = session_id
    if type:
        filter_dict["type"] = type
    if model:
        filter_dict["model"] = model
    
    # Get messages
    messages, total = await service.list_messages(
        filter_dict=filter_dict,
        skip=skip,
        limit=limit,
        sort_order=sort_order
    )
    
    return PaginatedResponse(
        items=messages,
        total=total,
        skip=skip,
        limit=limit,
        has_more=skip + limit < total
    )


@router.get("/{message_id}", response_model=MessageDetail)
async def get_message(
    message_id: str,
    db: CommonDeps
) -> MessageDetail:
    """Get a specific message by ID."""
    service = MessageService(db)
    message = await service.get_message(message_id)
    
    if not message:
        raise NotFoundError("Message", message_id)
    
    return message


@router.get("/uuid/{uuid}", response_model=MessageDetail)
async def get_message_by_uuid(
    uuid: str,
    db: CommonDeps
) -> MessageDetail:
    """Get a message by its Claude UUID."""
    service = MessageService(db)
    message = await service.get_message_by_uuid(uuid)
    
    if not message:
        raise NotFoundError("Message with UUID", uuid)
    
    return message


@router.get("/{message_id}/context")
async def get_message_context(
    message_id: str,
    db: CommonDeps,
    before: int = Query(5, ge=0, le=50, description="Number of messages before"),
    after: int = Query(5, ge=0, le=50, description="Number of messages after")
) -> dict:
    """Get a message with surrounding context.
    
    Returns the specified message along with messages before and after it
    in the same session.
    """
    service = MessageService(db)
    context = await service.get_message_context(message_id, before, after)
    
    if not context:
        raise NotFoundError("Message", message_id)
    
    return context
```

### 4. Service Layer Implementation

**`backend/app/services/project.py`:**
```python
"""Project service layer."""
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectWithStats
from app.models.project import ProjectInDB


class ProjectService:
    """Service for project operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def list_projects(
        self,
        filter_dict: Dict[str, Any],
        skip: int,
        limit: int,
        sort_by: str,
        sort_order: str
    ) -> Tuple[List[ProjectWithStats], int]:
        """List projects with pagination."""
        # Count total
        total = await self.db.projects.count_documents(filter_dict)
        
        # Build sort
        sort_direction = -1 if sort_order == "desc" else 1
        
        # Special handling for nested fields
        if sort_by == "message_count":
            sort_field = "stats.message_count"
        else:
            sort_field = sort_by
        
        # Get projects
        cursor = self.db.projects.find(filter_dict).sort(
            sort_field, sort_direction
        ).skip(skip).limit(limit)
        
        projects = []
        async for doc in cursor:
            # Enrich with real-time stats
            stats = await self._get_project_stats(doc["_id"])
            doc["stats"] = stats
            projects.append(ProjectWithStats(**doc))
        
        return projects, total
    
    async def get_project(self, project_id: ObjectId) -> Optional[ProjectWithStats]:
        """Get a single project."""
        doc = await self.db.projects.find_one({"_id": project_id})
        if not doc:
            return None
        
        # Enrich with stats
        stats = await self._get_project_stats(project_id)
        doc["stats"] = stats
        
        return ProjectWithStats(**doc)
    
    async def get_project_by_path(self, path: str) -> Optional[ProjectInDB]:
        """Get project by path."""
        doc = await self.db.projects.find_one({"path": path})
        return ProjectInDB(**doc) if doc else None
    
    async def create_project(self, project: ProjectCreate) -> ProjectInDB:
        """Create a new project."""
        doc = {
            "_id": ObjectId(),
            "name": project.name,
            "path": project.path,
            "description": project.description,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        await self.db.projects.insert_one(doc)
        return ProjectInDB(**doc)
    
    async def update_project(
        self,
        project_id: ObjectId,
        update: ProjectUpdate
    ) -> Optional[ProjectInDB]:
        """Update a project."""
        update_dict = update.dict(exclude_unset=True)
        if update_dict:
            update_dict["updatedAt"] = datetime.utcnow()
            
            result = await self.db.projects.find_one_and_update(
                {"_id": project_id},
                {"$set": update_dict},
                return_document=True
            )
            
            return ProjectInDB(**result) if result else None
        
        return await self.get_project(project_id)
    
    async def delete_project(
        self,
        project_id: ObjectId,
        cascade: bool = False
    ) -> bool:
        """Delete a project."""
        if cascade:
            # Delete all associated data
            # Get all session IDs
            session_ids = await self.db.sessions.distinct(
                "sessionId",
                {"projectId": project_id}
            )
            
            # Delete messages
            await self.db.messages.delete_many(
                {"sessionId": {"$in": session_ids}}
            )
            
            # Delete sessions
            await self.db.sessions.delete_many({"projectId": project_id})
        
        # Delete project
        result = await self.db.projects.delete_one({"_id": project_id})
        return result.deleted_count > 0
    
    async def get_project_statistics(self, project_id: ObjectId) -> Optional[dict]:
        """Get detailed project statistics."""
        # Check project exists
        project = await self.db.projects.find_one({"_id": project_id})
        if not project:
            return None
        
        # Get session IDs
        session_ids = await self.db.sessions.distinct(
            "sessionId",
            {"projectId": project_id}
        )
        
        # Aggregate statistics
        pipeline = [
            {"$match": {"sessionId": {"$in": session_ids}}},
            {"$group": {
                "_id": None,
                "total_messages": {"$sum": 1},
                "user_messages": {
                    "$sum": {"$cond": [{"$eq": ["$type", "user"]}, 1, 0]}
                },
                "assistant_messages": {
                    "$sum": {"$cond": [{"$eq": ["$type", "assistant"]}, 1, 0]}
                },
                "total_cost": {"$sum": {"$ifNull": ["$costUsd", 0]}},
                "models_used": {"$addToSet": "$model"},
                "first_message": {"$min": "$timestamp"},
                "last_message": {"$max": "$timestamp"}
            }}
        ]
        
        result = await self.db.messages.aggregate(pipeline).to_list(1)
        
        if result:
            stats = result[0]
            stats["session_count"] = len(session_ids)
            stats["project_id"] = str(project_id)
            return stats
        
        return {
            "project_id": str(project_id),
            "session_count": 0,
            "total_messages": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "total_cost": 0,
            "models_used": []
        }
    
    async def _get_project_stats(self, project_id: ObjectId) -> dict:
        """Get basic project statistics."""
        # Count sessions
        session_count = await self.db.sessions.count_documents(
            {"projectId": project_id}
        )
        
        # Count messages (through sessions)
        session_ids = await self.db.sessions.distinct(
            "sessionId",
            {"projectId": project_id}
        )
        
        message_count = await self.db.messages.count_documents(
            {"sessionId": {"$in": session_ids}}
        )
        
        return {
            "session_count": session_count,
            "message_count": message_count
        }
```

### 5. Response Schemas

**`backend/app/schemas/project.py`:**
```python
"""Project schemas."""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.project import PyObjectId


class ProjectBase(BaseModel):
    """Base project schema."""
    name: str
    path: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = None
    description: Optional[str] = None


class Project(ProjectBase):
    """Project response schema."""
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ProjectStats(BaseModel):
    """Project statistics."""
    session_count: int = 0
    message_count: int = 0


class ProjectWithStats(Project):
    """Project with statistics."""
    stats: ProjectStats
```

## Required Technologies
- FastAPI for API framework
- Motor for async MongoDB operations
- Pydantic for data validation
- Redis for caching (optional)

## Success Criteria
- [ ] All CRUD endpoints implemented for projects, sessions, messages
- [ ] Pagination working with skip/limit
- [ ] Filtering by various fields functional
- [ ] Sorting in ascending/descending order
- [ ] Thread reconstruction for conversations
- [ ] Efficient queries with proper indexes
- [ ] Response times < 100ms for most queries
- [ ] Proper error handling for invalid IDs
- [ ] API documentation complete

## Notes
- Use projections to limit data transfer
- Implement cursor-based pagination for large datasets
- Cache frequently accessed data
- Use aggregation pipelines for statistics
- Ensure all queries use indexes efficiently