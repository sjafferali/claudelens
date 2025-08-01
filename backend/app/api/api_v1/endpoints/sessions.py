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