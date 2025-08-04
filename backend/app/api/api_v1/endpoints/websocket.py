"""WebSocket endpoints for real-time updates."""
import asyncio
import logging
from typing import Any

from fastapi import Depends, HTTPException, WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_database
from app.core.custom_router import APIRouter
from app.schemas.websocket import LiveSessionStats, LiveStatsResponse
from app.services.websocket_manager import RealtimeStatsService, connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/session/{session_id}")
async def websocket_session_endpoint(
    websocket: WebSocket,
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> None:
    """WebSocket endpoint for session-specific real-time updates."""
    logger.info(f"WebSocket connection attempt for session: {session_id}")

    try:
        # Verify session exists
        sessions_collection = db.sessions
        session = await sessions_collection.find_one({"sessionId": session_id})
        if not session:
            await websocket.close(code=4004, reason="Session not found")
            return

        # Connect the WebSocket
        await connection_manager.connect(websocket, session_id)

        # Handle messages in the background
        await connection_manager.handle_websocket_messages(websocket, session_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.exception(f"WebSocket error for session {session_id}: {e}")
        await connection_manager.disconnect(websocket, session_id)


@router.websocket("/stats/{session_id}")
async def websocket_stats_endpoint(
    websocket: WebSocket,
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> None:
    """WebSocket endpoint for session stats real-time updates."""
    logger.info(f"WebSocket stats connection attempt for session: {session_id}")

    try:
        # Verify session exists
        sessions_collection = db.sessions
        session = await sessions_collection.find_one({"sessionId": session_id})
        if not session:
            await websocket.close(code=4004, reason="Session not found")
            return

        # Connect the WebSocket for stats
        await connection_manager.connect(websocket, session_id)

        # Send initial stats
        stats_service = RealtimeStatsService(db)

        # Send initial stat updates
        await asyncio.gather(
            stats_service.update_message_count(session_id),
            stats_service.update_tool_usage(session_id),
            stats_service.update_token_count(session_id),
            stats_service.update_cost(session_id),
            return_exceptions=True,
        )

        # Handle messages in the background
        await connection_manager.handle_websocket_messages(websocket, session_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket stats disconnected for session: {session_id}")
    except Exception as e:
        logger.exception(f"WebSocket stats error for session {session_id}: {e}")
        await connection_manager.disconnect(websocket, session_id)


@router.websocket("/stats")
async def websocket_global_stats_endpoint(
    websocket: WebSocket, db: AsyncIOMotorDatabase = Depends(get_database)
) -> None:
    """WebSocket endpoint for global stats real-time updates."""
    logger.info("WebSocket global stats connection attempt")

    try:
        # Connect the WebSocket for global stats
        await connection_manager.connect(websocket, None)

        # Handle messages in the background
        await connection_manager.handle_websocket_messages(websocket, None)

    except WebSocketDisconnect:
        logger.info("WebSocket global stats disconnected")
    except Exception as e:
        logger.exception(f"WebSocket global stats error: {e}")
        await connection_manager.disconnect(websocket, None)


@router.get("/session/live", response_model=LiveSessionStats)
async def get_live_session_stats(
    session_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
) -> LiveSessionStats:
    """Get current live session statistics."""
    # Verify session exists
    sessions_collection = db.sessions
    session = await sessions_collection.find_one({"sessionId": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages_collection = db.messages

    # Get message count
    message_count = await messages_collection.count_documents({"sessionId": session_id})

    # Get tool usage count
    tool_pipeline: list[dict[str, Any]] = [
        {"$match": {"sessionId": session_id}},
        {"$unwind": {"path": "$toolsUsed", "preserveNullAndEmptyArrays": True}},
        {"$match": {"toolsUsed": {"$ne": None}}},
        {"$count": "total_tools"},
    ]
    tool_result = await messages_collection.aggregate(tool_pipeline).to_list(1)
    tool_usage_count = tool_result[0]["total_tools"] if tool_result else 0

    # Get token count
    token_pipeline: list[dict[str, Any]] = [
        {"$match": {"sessionId": session_id}},
        {
            "$group": {
                "_id": None,
                "total_tokens": {
                    "$sum": {
                        "$add": [
                            {"$ifNull": ["$inputTokens", 0]},
                            {"$ifNull": ["$outputTokens", 0]},
                        ]
                    }
                },
            }
        },
    ]
    token_result = await messages_collection.aggregate(token_pipeline).to_list(1)
    token_count = token_result[0]["total_tokens"] if token_result else 0

    # Get cost
    cost_pipeline: list[dict[str, Any]] = [
        {"$match": {"sessionId": session_id}},
        {"$group": {"_id": None, "total_cost": {"$sum": {"$ifNull": ["$costUsd", 0]}}}},
    ]
    cost_result = await messages_collection.aggregate(cost_pipeline).to_list(1)
    raw_cost = cost_result[0]["total_cost"] if cost_result else 0.0
    # Convert Decimal128 to float if necessary
    if hasattr(raw_cost, "to_decimal"):
        cost = float(raw_cost.to_decimal())
    else:
        cost = float(raw_cost)

    # Get last activity
    last_message = await messages_collection.find_one(
        {"sessionId": session_id}, sort=[("timestamp", -1)]
    )
    last_activity = last_message.get("timestamp") if last_message else None

    # Determine if session is active (activity within last 5 minutes)
    is_active = False
    if last_activity:
        from datetime import datetime, timedelta

        is_active = (datetime.utcnow() - last_activity) < timedelta(minutes=5)

    return LiveSessionStats(
        session_id=session_id,
        message_count=message_count,
        tool_usage_count=tool_usage_count,
        token_count=token_count,
        cost=cost,
        last_activity=last_activity,
        is_active=is_active,
    )


@router.get("/stats/live", response_model=LiveStatsResponse)
async def get_live_global_stats(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> LiveStatsResponse:
    """Get current live global statistics."""
    messages_collection = db.messages
    sessions_collection = db.sessions

    # Get total message count
    total_messages = await messages_collection.count_documents({})

    # Get total tool usage count
    tool_pipeline: list[dict[str, Any]] = [
        {"$unwind": {"path": "$toolsUsed", "preserveNullAndEmptyArrays": True}},
        {"$match": {"toolsUsed": {"$ne": None}}},
        {"$count": "total_tools"},
    ]
    tool_result = await messages_collection.aggregate(tool_pipeline).to_list(1)
    total_tools = tool_result[0]["total_tools"] if tool_result else 0

    # Get total token count
    token_pipeline: list[dict[str, Any]] = [
        {
            "$group": {
                "_id": None,
                "total_tokens": {
                    "$sum": {
                        "$add": [
                            {"$ifNull": ["$inputTokens", 0]},
                            {"$ifNull": ["$outputTokens", 0]},
                        ]
                    }
                },
            }
        }
    ]
    token_result = await messages_collection.aggregate(token_pipeline).to_list(1)
    total_tokens = token_result[0]["total_tokens"] if token_result else 0

    # Get total cost
    cost_pipeline: list[dict[str, Any]] = [
        {"$group": {"_id": None, "total_cost": {"$sum": {"$ifNull": ["$costUsd", 0]}}}}
    ]
    cost_result = await messages_collection.aggregate(cost_pipeline).to_list(1)
    raw_total_cost = cost_result[0]["total_cost"] if cost_result else 0.0
    # Convert Decimal128 to float if necessary
    if hasattr(raw_total_cost, "to_decimal"):
        total_cost = float(raw_total_cost.to_decimal())
    else:
        total_cost = float(raw_total_cost)

    # Get active sessions count (sessions with activity in last 5 minutes)
    from datetime import datetime, timedelta

    cutoff_time = datetime.utcnow() - timedelta(minutes=5)

    active_sessions_pipeline: list[dict[str, Any]] = [
        {
            "$lookup": {
                "from": "messages",
                "localField": "sessionId",
                "foreignField": "sessionId",
                "as": "messages",
            }
        },
        {"$match": {"messages.timestamp": {"$gte": cutoff_time}}},
        {"$count": "active_sessions"},
    ]

    active_result = await sessions_collection.aggregate(
        active_sessions_pipeline
    ).to_list(1)
    active_sessions = active_result[0]["active_sessions"] if active_result else 0

    return LiveStatsResponse(
        total_messages=total_messages,
        total_tools=total_tools,
        total_tokens=total_tokens,
        total_cost=total_cost,
        active_sessions=active_sessions,
    )


@router.get("/connections")
async def get_connection_stats() -> dict:
    """Get WebSocket connection statistics (for debugging)."""
    return connection_manager.get_connection_stats()
