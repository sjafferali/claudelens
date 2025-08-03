"""Integration service for real-time updates with ingest system."""
import asyncio
import logging
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.websocket_manager import RealtimeStatsService

logger = logging.getLogger(__name__)


class RealtimeIntegrationService:
    """Service that integrates real-time updates with the ingest system."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.stats_service = RealtimeStatsService(db)

    async def on_message_ingested(self, message_data: Dict[str, Any]) -> None:
        """Called when a new message is ingested into the system."""
        try:
            session_id = message_data.get("sessionId")
            if not session_id:
                return

            # Fire off real-time updates without waiting
            # This ensures ingest performance isn't affected
            asyncio.create_task(
                self._broadcast_message_updates(session_id, message_data)
            )

        except Exception as e:
            logger.exception(f"Error in real-time integration for message ingest: {e}")

    async def _broadcast_message_updates(
        self, session_id: str, message_data: Dict[str, Any]
    ) -> None:
        """Broadcast all relevant updates for a new message."""
        try:
            # Broadcast new message event
            await self.stats_service.broadcast_new_message(session_id, message_data)

            # Update and broadcast all relevant stats
            # Run these concurrently to minimize delay
            await asyncio.gather(
                self.stats_service.update_message_count(session_id),
                self._update_tool_usage_if_applicable(session_id, message_data),
                self.stats_service.update_token_count(session_id),
                self.stats_service.update_cost(session_id),
                return_exceptions=True,
            )

        except Exception as e:
            logger.exception(
                f"Error broadcasting message updates for session {session_id}: {e}"
            )

    async def _update_tool_usage_if_applicable(
        self, session_id: str, message_data: Dict[str, Any]
    ) -> None:
        """Update tool usage if the message contains tool usage."""
        tools_used = message_data.get("toolsUsed", [])
        if tools_used:
            await self.stats_service.update_tool_usage(session_id)

    async def on_session_started(self, session_id: str) -> None:
        """Called when a new session is started."""
        try:
            # Initialize stats for the session
            await asyncio.gather(
                self.stats_service.update_message_count(session_id),
                self.stats_service.update_tool_usage(session_id),
                self.stats_service.update_token_count(session_id),
                self.stats_service.update_cost(session_id),
                return_exceptions=True,
            )

        except Exception as e:
            logger.exception(f"Error initializing stats for session {session_id}: {e}")

    async def on_session_updated(self, session_id: str) -> None:
        """Called when a session is updated."""
        try:
            # Refresh all stats for the session
            await asyncio.gather(
                self.stats_service.update_message_count(session_id),
                self.stats_service.update_tool_usage(session_id),
                self.stats_service.update_token_count(session_id),
                self.stats_service.update_cost(session_id),
                return_exceptions=True,
            )

        except Exception as e:
            logger.exception(f"Error updating stats for session {session_id}: {e}")


# Global integration service instance
_integration_service: RealtimeIntegrationService | None = None


def get_integration_service(db: AsyncIOMotorDatabase) -> RealtimeIntegrationService:
    """Get or create the global integration service instance."""
    global _integration_service
    if _integration_service is None:
        _integration_service = RealtimeIntegrationService(db)
    return _integration_service


async def initialize_realtime_integration(db: AsyncIOMotorDatabase) -> None:
    """Initialize the real-time integration service."""
    global _integration_service
    _integration_service = RealtimeIntegrationService(db)
    logger.info("Real-time integration service initialized")
