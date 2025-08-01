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