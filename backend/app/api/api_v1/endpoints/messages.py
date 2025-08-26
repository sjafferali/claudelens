"""Messages API endpoints."""

from typing import List, Optional

from fastapi import Query

from app.api.dependencies import AuthDeps, CommonDeps
from app.core.custom_router import APIRouter
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse
from app.schemas.message import Message, MessageDetail
from app.services.cost_calculation import CostCalculationService
from app.services.message import MessageService

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=PaginatedResponse[Message])
async def list_messages(
    db: CommonDeps,
    user_id: AuthDeps,
    session_id: str | None = Query(None, description="Filter by session ID"),
    type: str | None = Query(None, description="Filter by message type"),
    model: str | None = Query(None, description="Filter by model"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
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
        user_id, filter_dict=filter_dict, skip=skip, limit=limit, sort_order=sort_order
    )

    return PaginatedResponse(
        items=messages,
        total=total,
        skip=skip,
        limit=limit,
        has_more=skip + limit < total,
    )


@router.get("/{message_id}", response_model=MessageDetail)
async def get_message(
    message_id: str, db: CommonDeps, user_id: AuthDeps
) -> MessageDetail:
    """Get a specific message by ID."""
    service = MessageService(db)
    message = await service.get_message(user_id, message_id)

    if not message:
        raise NotFoundError("Message", message_id)

    return message


@router.get("/uuid/{uuid}", response_model=MessageDetail)
async def get_message_by_uuid(
    uuid: str, db: CommonDeps, user_id: AuthDeps
) -> MessageDetail:
    """Get a message by its Claude UUID."""
    service = MessageService(db)
    message = await service.get_message_by_uuid(user_id, uuid)

    if not message:
        raise NotFoundError("Message with UUID", uuid)

    return message


@router.get("/{message_id}/context")
async def get_message_context(
    message_id: str,
    db: CommonDeps,
    user_id: AuthDeps,
    before: int = Query(5, ge=0, le=50, description="Number of messages before"),
    after: int = Query(5, ge=0, le=50, description="Number of messages after"),
) -> dict:
    """Get a message with surrounding context.

    Returns the specified message along with messages before and after it
    in the same session.
    """
    service = MessageService(db)
    context = await service.get_message_context(user_id, message_id, before, after)

    if not context:
        raise NotFoundError("Message", message_id)

    return context


@router.patch("/{message_id}/cost")
async def update_message_cost(
    message_id: str,
    db: CommonDeps,
    user_id: AuthDeps,
    cost_usd: float = Query(..., description="Cost in USD"),
) -> dict:
    """Update the cost for a specific message."""
    service = MessageService(db)
    success = await service.update_message_cost(user_id, message_id, cost_usd)

    if not success:
        raise NotFoundError("Message", message_id)

    return {"success": True, "message_id": message_id, "cost_usd": cost_usd}


@router.post("/batch-update-costs")
async def batch_update_costs(
    db: CommonDeps,
    user_id: AuthDeps,
    cost_updates: dict[str, float],
) -> dict:
    """Batch update costs for multiple messages.

    Expects a dictionary mapping message UUIDs to their costs in USD.
    """
    service = MessageService(db)
    updated_count = await service.batch_update_costs(user_id, cost_updates)

    return {
        "success": True,
        "updated_count": updated_count,
        "requested_count": len(cost_updates),
    }


@router.post("/calculate-costs")
async def calculate_message_costs(
    db: CommonDeps,
    user_id: AuthDeps,
    session_id: Optional[str] = None,
    message_ids: Optional[List[str]] = None,
) -> dict:
    """Calculate costs for messages and update them in the database.

    Either provide a session_id to calculate costs for all messages in that session,
    or provide a list of message_ids to calculate costs for specific messages.
    """
    if not session_id and not message_ids:
        return {
            "success": False,
            "error": "Either session_id or message_ids must be provided",
        }

    try:
        service = MessageService(db)
        cost_service = CostCalculationService()

        # Get messages to calculate costs for
        messages: List[MessageDetail] = []
        if session_id:
            # Get all message IDs first
            basic_messages, total = await service.list_messages(
                user_id,
                filter_dict={"sessionId": session_id},
                skip=0,
                limit=10000,  # Get all messages in session
                sort_order="asc",
            )
            logger.debug(
                f"Found {len(basic_messages)} messages out of {total} total for session {session_id}"
            )
            # Get detailed messages with usage data
            for msg in basic_messages:
                detailed_msg = await service.get_message(user_id, msg.id)
                if detailed_msg:
                    messages.append(detailed_msg)
        elif message_ids:
            for msg_id in message_ids:
                detailed_msg = await service.get_message(user_id, msg_id)
                if detailed_msg:
                    messages.append(detailed_msg)

        # Calculate and update costs
        cost_updates = {}
        calculated_count = 0
        skipped_count = 0

        for message in messages:
            # Skip if no usage data or already has cost
            if not message.usage:
                skipped_count += 1
                continue

            if (
                hasattr(message, "cost_usd")
                and message.cost_usd
                and message.cost_usd > 0
            ):
                skipped_count += 1
                continue

            # Skip if no model specified
            if not message.model:
                skipped_count += 1
                continue

            # Calculate cost
            cost = cost_service.calculate_message_cost(
                model=message.model,
                input_tokens=message.usage.get("input_tokens"),
                output_tokens=message.usage.get("output_tokens"),
                cache_creation_input_tokens=message.usage.get(
                    "cache_creation_input_tokens"
                ),
                cache_read_input_tokens=message.usage.get("cache_read_input_tokens"),
            )

            if cost is not None and cost > 0:
                # Use UUID if available, otherwise use ID
                msg_key = (
                    message.uuid
                    if hasattr(message, "uuid") and message.uuid
                    else str(message.id)
                )
                cost_updates[msg_key] = cost
                calculated_count += 1

        # Batch update costs in database
        updated_count = 0
        if cost_updates:
            updated_count = await service.batch_update_costs(user_id, cost_updates)

        return {
            "success": True,
            "messages_processed": len(messages),
            "messages_skipped": skipped_count,
            "costs_calculated": calculated_count,
            "costs_updated": updated_count,
            "session_id": session_id,
            "message_ids": message_ids,
        }
    except Exception as e:
        import traceback

        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
