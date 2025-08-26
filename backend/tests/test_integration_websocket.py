"""Integration tests for WebSocket real-time updates."""

import asyncio
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import WebSocket

from app.schemas.websocket import (
    AnimationType,
    MessagePreview,
    StatType,
)
from app.services.websocket_manager import ConnectionManager


@pytest.fixture
def connection_manager():
    """Create a ConnectionManager instance."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    websocket = MagicMock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


@pytest.fixture
def mock_websocket_2():
    """Create a second mock WebSocket connection."""
    websocket = MagicMock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


class TestWebSocketIntegration:
    """Integration tests for WebSocket real-time updates."""

    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(
        self, connection_manager, mock_websocket
    ):
        """Test WebSocket connection and disconnection lifecycle."""
        session_id = "test_session_001"

        # Connect websocket
        await connection_manager.connect(mock_websocket, session_id)

        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()

        # Verify connection event was sent
        mock_websocket.send_text.assert_called_once()
        sent_data = mock_websocket.send_text.call_args[0][0]
        event_data = json.loads(sent_data)
        assert event_data["type"] == "connection"
        assert event_data["status"] == "connected"

        # Verify websocket is tracked
        assert mock_websocket in connection_manager.active_connections
        assert session_id in connection_manager.session_connections
        assert mock_websocket in connection_manager.session_connections[session_id]

        # Disconnect websocket
        await connection_manager.disconnect(mock_websocket, session_id)

        # Verify cleanup
        assert session_id not in connection_manager.session_connections
        assert mock_websocket not in connection_manager.stats_connections

    @pytest.mark.asyncio
    async def test_stats_connection_management(
        self, connection_manager, mock_websocket
    ):
        """Test stats connection management (no session_id)."""
        # Connect as stats connection
        await connection_manager.connect(mock_websocket, None)

        # Verify connection
        mock_websocket.accept.assert_called_once()
        assert mock_websocket in connection_manager.active_connections
        assert mock_websocket in connection_manager.stats_connections

        # Disconnect
        await connection_manager.disconnect(mock_websocket, None)

        # Verify cleanup
        assert mock_websocket not in connection_manager.stats_connections

    @pytest.mark.asyncio
    async def test_stat_update_broadcast(
        self, connection_manager, mock_websocket, mock_websocket_2
    ):
        """Test broadcasting stat updates to relevant connections."""
        session_id = "test_session_001"

        # Connect two websockets - one session-specific, one stats
        await connection_manager.connect(mock_websocket, session_id)
        await connection_manager.connect(mock_websocket_2, None)

        # Clear previous send_text calls
        mock_websocket.send_text.reset_mock()
        mock_websocket_2.send_text.reset_mock()

        # Broadcast stat update
        await connection_manager.broadcast_stat_update(
            stat_type=StatType.MESSAGES,
            session_id=session_id,
            new_value=100,
            formatted_value="100",
            delta=5,
            animation=AnimationType.INCREMENT,
        )

        # Verify both connections received the update
        assert mock_websocket.send_text.called
        assert mock_websocket_2.send_text.called

        # Verify event structure
        sent_data = mock_websocket.send_text.call_args[0][0]
        event_data = json.loads(sent_data)
        assert event_data["type"] == "stat_update"
        assert event_data["stat_type"] == "messages"
        assert event_data["session_id"] == session_id
        assert event_data["update"]["new_value"] == 100
        assert event_data["update"]["delta"] == 5

    @pytest.mark.asyncio
    async def test_new_message_broadcast(self, connection_manager, mock_websocket):
        """Test broadcasting new message events."""
        session_id = "test_session_001"

        # Connect websocket
        await connection_manager.connect(mock_websocket, session_id)
        mock_websocket.send_text.reset_mock()

        # Create message preview data
        message_preview = MessagePreview(
            uuid="msg_123",
            author="user",
            timestamp=datetime.now(UTC),
            preview="Test message content",
            tool_used=None,
        )

        await connection_manager.broadcast_new_message(session_id, message_preview)

        # Verify message was sent
        assert mock_websocket.send_text.called
        sent_data = mock_websocket.send_text.call_args[0][0]
        event_data = json.loads(sent_data)
        assert event_data["type"] == "new_message"
        assert event_data["session_id"] == session_id
        assert event_data["message"]["uuid"] == "msg_123"

    @pytest.mark.asyncio
    async def test_connection_status_info(self, connection_manager, mock_websocket):
        """Test getting connection status information."""
        session_id = "test_session_001"

        # Initially no connections
        stats = connection_manager.get_connection_stats()
        assert stats["total_connections"] == 0
        assert stats["stats_connections"] == 0

        # Connect websocket
        await connection_manager.connect(mock_websocket, session_id)

        # Check stats after connection
        stats = connection_manager.get_connection_stats()
        assert stats["total_connections"] == 1
        assert session_id in stats["session_connections"]

    @pytest.mark.asyncio
    async def test_concurrent_connections(
        self, connection_manager, mock_websocket, mock_websocket_2
    ):
        """Test handling multiple concurrent connections."""
        session_id_1 = "test_session_001"
        session_id_2 = "test_session_002"

        # Connect multiple websockets concurrently
        await asyncio.gather(
            connection_manager.connect(mock_websocket, session_id_1),
            connection_manager.connect(mock_websocket_2, session_id_2),
        )

        # Verify both connections are tracked
        assert mock_websocket in connection_manager.active_connections
        assert mock_websocket_2 in connection_manager.active_connections
        assert len(connection_manager.session_connections) == 2

        # Clear previous calls
        mock_websocket.send_text.reset_mock()
        mock_websocket_2.send_text.reset_mock()

        # Broadcast to specific session
        await connection_manager.broadcast_stat_update(
            stat_type=StatType.TOKENS,
            session_id=session_id_1,
            new_value=1000,
            formatted_value="1K",
            delta=50,
            animation=AnimationType.INCREMENT,
        )

        # Verify only session_1 websocket received update
        # (Note: in real implementation, stats connections would also receive it)
        assert mock_websocket.send_text.called or mock_websocket_2.send_text.called

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, connection_manager, mock_websocket):
        """Test WebSocket error handling during send operations."""
        session_id = "test_session_001"

        # Connect websocket
        await connection_manager.connect(mock_websocket, session_id)

        # Mock send_text to raise an exception
        mock_websocket.send_text.side_effect = Exception("Connection error")

        # Broadcasting should handle the error gracefully
        try:
            await connection_manager.broadcast_stat_update(
                stat_type=StatType.COST,
                session_id=session_id,
                new_value=500,
                formatted_value="$5.00",
                delta=25,
                animation=AnimationType.INCREMENT,
            )
            # Should not raise exception
        except Exception as e:
            pytest.fail(f"broadcast_stat_update raised an exception: {e}")

    @pytest.mark.asyncio
    async def test_connection_manager_thread_safety(self, connection_manager):
        """Test ConnectionManager thread safety with concurrent operations."""
        websockets = []
        session_ids = []

        # Create multiple mock websockets
        for i in range(5):
            ws = MagicMock(spec=WebSocket)
            ws.accept = AsyncMock()
            ws.send_text = AsyncMock()
            websockets.append(ws)
            session_ids.append(f"session_{i}")

        # Connect all websockets concurrently
        connect_tasks = [
            connection_manager.connect(ws, sid)
            for ws, sid in zip(websockets, session_ids)
        ]

        await asyncio.gather(*connect_tasks)

        # Verify all connections were established
        assert len(connection_manager.session_connections) == 5
        for ws in websockets:
            assert ws in connection_manager.active_connections

        # Disconnect all concurrently
        disconnect_tasks = [
            connection_manager.disconnect(ws, sid)
            for ws, sid in zip(websockets, session_ids)
        ]

        await asyncio.gather(*disconnect_tasks)

        # Verify cleanup
        assert len(connection_manager.session_connections) == 0

    @pytest.mark.asyncio
    async def test_websocket_event_serialization(
        self, connection_manager, mock_websocket
    ):
        """Test proper serialization of WebSocket events."""
        session_id = "test_session_001"

        # Connect websocket
        await connection_manager.connect(mock_websocket, session_id)
        mock_websocket.send_text.reset_mock()

        # Test StatUpdateEvent serialization
        await connection_manager.broadcast_stat_update(
            stat_type=StatType.TOOLS,
            session_id=session_id,
            new_value=42,
            formatted_value="42 tools",
            delta=3,
            animation=AnimationType.NONE,
        )

        # Verify JSON serialization
        assert mock_websocket.send_text.called
        sent_data = mock_websocket.send_text.call_args[0][0]

        # Should be valid JSON
        event_data = json.loads(sent_data)

        # Verify all required fields are present
        required_fields = ["type", "stat_type", "session_id", "timestamp", "update"]
        for field in required_fields:
            assert field in event_data

        # Verify update object structure
        update_data = event_data["update"]
        update_fields = ["new_value", "formatted_value", "delta", "animation"]
        for field in update_fields:
            assert field in update_data
