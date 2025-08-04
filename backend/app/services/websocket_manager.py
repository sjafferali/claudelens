"""WebSocket connection manager for real-time updates."""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Set
from weakref import WeakSet

from fastapi import WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.websocket import (
    AnimationType,
    ConnectionEvent,
    MessagePreview,
    NewMessageEvent,
    PongEvent,
    StatType,
    StatUpdate,
    StatUpdateEvent,
    WebSocketEvent,
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and handles broadcasting."""

    def __init__(self) -> None:
        # Use WeakSet to automatically clean up disconnected websockets
        self.active_connections: WeakSet[WebSocket] = WeakSet()
        # Session-specific connections for targeted updates
        self.session_connections: Dict[str, Set[WebSocket]] = {}
        # Stats connections for global updates
        self.stats_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(
        self, websocket: WebSocket, session_id: str | None = None
    ) -> None:
        """Accept a WebSocket connection and add it to the appropriate groups."""
        await websocket.accept()

        async with self._lock:
            self.active_connections.add(websocket)

            if session_id:
                # Session-specific connection
                if session_id not in self.session_connections:
                    self.session_connections[session_id] = set()
                self.session_connections[session_id].add(websocket)
                logger.info(f"WebSocket connected for session {session_id}")
            else:
                # Stats connection (global)
                self.stats_connections.add(websocket)
                logger.info("WebSocket connected for global stats")

        # Send connection confirmation
        await self._send_to_websocket(
            websocket,
            ConnectionEvent(
                status="connected", message="Connected to real-time updates"
            ),
        )

    async def disconnect(
        self, websocket: WebSocket, session_id: str | None = None
    ) -> None:
        """Remove a WebSocket connection from all groups."""
        async with self._lock:
            # Remove from session connections
            if session_id and session_id in self.session_connections:
                self.session_connections[session_id].discard(websocket)
                if not self.session_connections[session_id]:
                    del self.session_connections[session_id]
                logger.info(f"WebSocket disconnected for session {session_id}")

            # Remove from stats connections
            self.stats_connections.discard(websocket)

            # active_connections is a WeakSet, so it will clean up automatically

    async def broadcast_stat_update(
        self,
        stat_type: StatType,
        session_id: str,
        new_value: int,
        formatted_value: str,
        delta: int,
        animation: AnimationType = AnimationType.INCREMENT,
    ) -> None:
        """Broadcast a stat update to relevant connections."""
        event = StatUpdateEvent(
            stat_type=stat_type,
            session_id=session_id,
            update=StatUpdate(
                new_value=new_value,
                formatted_value=formatted_value,
                delta=delta,
                animation=animation,
            ),
        )

        # Send to session-specific connections
        if session_id in self.session_connections:
            await self._broadcast_to_connections(
                self.session_connections[session_id], event
            )

        # Send to global stats connections
        await self._broadcast_to_connections(self.stats_connections, event)

    async def broadcast_new_message(
        self, session_id: str, message_data: MessagePreview
    ) -> None:
        """Broadcast a new message event to relevant connections."""
        event = NewMessageEvent(session_id=session_id, message=message_data)

        # Send to session-specific connections
        if session_id in self.session_connections:
            await self._broadcast_to_connections(
                self.session_connections[session_id], event
            )

    async def handle_websocket_messages(
        self, websocket: WebSocket, session_id: str | None = None
    ) -> None:
        """Handle incoming WebSocket messages (like ping/pong)."""
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    message_type = message.get("type")

                    if message_type == "ping":
                        # Respond to ping with pong
                        pong_event = PongEvent()
                        await self._send_to_websocket(websocket, pong_event)

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from WebSocket: {data}")

        except WebSocketDisconnect:
            await self.disconnect(websocket, session_id)
        except Exception as e:
            logger.exception(f"Error handling WebSocket messages: {e}")
            await self.disconnect(websocket, session_id)

    async def _broadcast_to_connections(
        self, connections: Set[WebSocket], event: WebSocketEvent
    ) -> None:
        """Broadcast an event to a set of connections."""
        if not connections:
            return

        # Create a copy to avoid modification during iteration
        connections_copy = set(connections)

        # Send to all connections concurrently
        tasks = [
            self._send_to_websocket(websocket, event) for websocket in connections_copy
        ]

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_to_websocket(
        self, websocket: WebSocket, event: WebSocketEvent
    ) -> None:
        """Send an event to a specific WebSocket connection."""
        try:
            # Convert Pydantic model to dict and then to JSON
            event_dict = event.model_dump(mode="json")
            # Handle datetime serialization
            for key, value in event_dict.items():
                if isinstance(value, datetime):
                    event_dict[key] = value.isoformat()
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, datetime):
                            value[sub_key] = sub_value.isoformat()

            await websocket.send_text(json.dumps(event_dict))

        except Exception as e:
            logger.warning(f"Failed to send message to WebSocket: {e}")
            # Remove the connection from all groups
            async with self._lock:
                self.stats_connections.discard(websocket)
                for session_id, session_conns in self.session_connections.items():
                    session_conns.discard(websocket)

    def get_connection_stats(self) -> dict:
        """Get statistics about active connections."""
        return {
            "total_connections": len(self.active_connections),
            "stats_connections": len(self.stats_connections),
            "session_connections": {
                session_id: len(connections)
                for session_id, connections in self.session_connections.items()
            },
        }


# Global connection manager instance
connection_manager = ConnectionManager()


class RealtimeStatsService:
    """Service for managing real-time statistics updates."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def update_message_count(self, session_id: str) -> None:
        """Update message count and broadcast the change."""
        try:
            # Get current message count from database
            messages_collection = self.db.messages
            count = await messages_collection.count_documents({"sessionId": session_id})

            # Format the count appropriately
            if count >= 1000:
                formatted_value = f"{count // 1000}K"
            else:
                formatted_value = str(count)

            await connection_manager.broadcast_stat_update(
                stat_type=StatType.MESSAGES,
                session_id=session_id,
                new_value=count,
                formatted_value=formatted_value,
                delta=1,  # Assume increment by 1
                animation=AnimationType.INCREMENT,
            )

            logger.debug(
                f"Broadcasted message count update for session {session_id}: {count}"
            )

        except Exception as e:
            logger.exception(
                f"Error updating message count for session {session_id}: {e}"
            )

    async def update_tool_usage(self, session_id: str) -> None:
        """Update tool usage count and broadcast the change."""
        try:
            # Get current tool usage count from database
            messages_collection = self.db.messages
            pipeline: list[dict[str, Any]] = [
                {"$match": {"sessionId": session_id}},
                {"$unwind": {"path": "$toolsUsed", "preserveNullAndEmptyArrays": True}},
                {"$match": {"toolsUsed": {"$ne": None}}},
                {"$count": "total_tools"},
            ]

            result = await messages_collection.aggregate(pipeline).to_list(1)
            count = result[0]["total_tools"] if result else 0

            # Format the count appropriately
            if count >= 1000:
                formatted_value = f"{count // 1000}K"
            else:
                formatted_value = str(count)

            await connection_manager.broadcast_stat_update(
                stat_type=StatType.TOOLS,
                session_id=session_id,
                new_value=count,
                formatted_value=formatted_value,
                delta=1,  # Assume increment by 1
                animation=AnimationType.INCREMENT,
            )

            logger.debug(
                f"Broadcasted tool usage update for session {session_id}: {count}"
            )

        except Exception as e:
            logger.exception(f"Error updating tool usage for session {session_id}: {e}")

    async def update_token_count(self, session_id: str) -> None:
        """Update token count and broadcast the change."""
        try:
            # Get current token count from database
            messages_collection = self.db.messages
            pipeline: list[dict[str, Any]] = [
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

            result = await messages_collection.aggregate(pipeline).to_list(1)
            count = result[0]["total_tokens"] if result else 0

            # Format the count appropriately
            if count >= 1000000:
                formatted_value = f"{count // 1000000}M"
            elif count >= 1000:
                formatted_value = f"{count // 1000}K"
            else:
                formatted_value = str(count)

            await connection_manager.broadcast_stat_update(
                stat_type=StatType.TOKENS,
                session_id=session_id,
                new_value=count,
                formatted_value=formatted_value,
                delta=100,  # Assume some increment
                animation=AnimationType.INCREMENT,
            )

            logger.debug(
                f"Broadcasted token count update for session {session_id}: {count}"
            )

        except Exception as e:
            logger.exception(
                f"Error updating token count for session {session_id}: {e}"
            )

    async def update_cost(self, session_id: str) -> None:
        """Update cost and broadcast the change."""
        try:
            # Get current cost from database
            messages_collection = self.db.messages
            pipeline: list[dict[str, Any]] = [
                {"$match": {"sessionId": session_id}},
                {
                    "$group": {
                        "_id": None,
                        "total_cost": {"$sum": {"$ifNull": ["$costUsd", 0]}},
                    }
                },
            ]

            result = await messages_collection.aggregate(pipeline).to_list(1)
            raw_cost = result[0]["total_cost"] if result else 0.0

            # Convert Decimal128 to float if necessary
            if hasattr(raw_cost, "to_decimal"):
                cost = float(raw_cost.to_decimal())
            else:
                cost = float(raw_cost)

            # Format the cost appropriately
            formatted_value = f"${cost:.2f}"

            await connection_manager.broadcast_stat_update(
                stat_type=StatType.COST,
                session_id=session_id,
                new_value=int(cost * 100),  # Convert to cents for integer value
                formatted_value=formatted_value,
                delta=1,  # Assume small increment
                animation=AnimationType.INCREMENT,
            )

            logger.debug(f"Broadcasted cost update for session {session_id}: {cost}")

        except Exception as e:
            logger.exception(f"Error updating cost for session {session_id}: {e}")

    async def broadcast_new_message(self, session_id: str, message_data: dict) -> None:
        """Broadcast a new message event."""
        try:
            # Create message preview
            preview = MessagePreview(
                uuid=message_data.get("uuid", ""),
                author=message_data.get("author", ""),
                timestamp=message_data.get("timestamp", datetime.utcnow()),
                preview=message_data.get("text", "")[:100] + "..."
                if len(message_data.get("text", "")) > 100
                else message_data.get("text", ""),
                tool_used=message_data.get("toolsUsed", [{}])[0].get("name")
                if message_data.get("toolsUsed")
                else None,
            )

            await connection_manager.broadcast_new_message(session_id, preview)

            # Also update the message count
            await self.update_message_count(session_id)

            logger.debug(f"Broadcasted new message for session {session_id}")

        except Exception as e:
            logger.exception(
                f"Error broadcasting new message for session {session_id}: {e}"
            )
