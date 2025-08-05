"""Tests for WebSocket manager service."""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket, WebSocketDisconnect

from app.schemas.websocket import (
    AnimationType,
    MessagePreview,
    StatType,
)
from app.services.websocket_manager import (
    ConnectionManager,
    RealtimeStatsService,
)


class TestConnectionManager:
    """Test WebSocket connection manager."""

    @pytest.fixture
    def manager(self):
        """Create a fresh connection manager for each test."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        websocket = MagicMock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_connect_session_websocket(self, manager, mock_websocket):
        """Test connecting a session-specific WebSocket."""
        session_id = "test-session-123"

        await manager.connect(mock_websocket, session_id)

        # Verify websocket was accepted
        mock_websocket.accept.assert_called_once()

        # Verify connection was added to appropriate groups
        assert mock_websocket in manager.active_connections
        assert session_id in manager.session_connections
        assert mock_websocket in manager.session_connections[session_id]
        assert mock_websocket not in manager.stats_connections

        # Verify connection event was sent
        mock_websocket.send_text.assert_called_once()
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data["type"] == "connection"
        assert sent_data["status"] == "connected"

    @pytest.mark.asyncio
    async def test_connect_stats_websocket(self, manager, mock_websocket):
        """Test connecting a global stats WebSocket."""
        await manager.connect(mock_websocket, session_id=None)

        # Verify websocket was accepted
        mock_websocket.accept.assert_called_once()

        # Verify connection was added to appropriate groups
        assert mock_websocket in manager.active_connections
        assert mock_websocket in manager.stats_connections
        assert len(manager.session_connections) == 0

        # Verify connection event was sent
        mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_session_websocket(self, manager, mock_websocket):
        """Test disconnecting a session-specific WebSocket."""
        session_id = "test-session-123"

        # First connect
        await manager.connect(mock_websocket, session_id)
        assert mock_websocket in manager.session_connections[session_id]

        # Then disconnect
        await manager.disconnect(mock_websocket, session_id)

        # Verify connection was removed
        assert session_id not in manager.session_connections
        assert mock_websocket not in manager.stats_connections

    @pytest.mark.asyncio
    async def test_disconnect_stats_websocket(self, manager, mock_websocket):
        """Test disconnecting a global stats WebSocket."""
        # First connect
        await manager.connect(mock_websocket, session_id=None)
        assert mock_websocket in manager.stats_connections

        # Then disconnect
        await manager.disconnect(mock_websocket, session_id=None)

        # Verify connection was removed
        assert mock_websocket not in manager.stats_connections

    @pytest.mark.asyncio
    async def test_disconnect_multiple_session_connections(self, manager):
        """Test that session group is kept when other connections remain."""
        session_id = "test-session-123"
        websocket1 = MagicMock(spec=WebSocket)
        websocket1.accept = AsyncMock()
        websocket1.send_text = AsyncMock()

        websocket2 = MagicMock(spec=WebSocket)
        websocket2.accept = AsyncMock()
        websocket2.send_text = AsyncMock()

        # Connect two websockets to same session
        await manager.connect(websocket1, session_id)
        await manager.connect(websocket2, session_id)

        assert len(manager.session_connections[session_id]) == 2

        # Disconnect one
        await manager.disconnect(websocket1, session_id)

        # Session group should still exist with remaining connection
        assert session_id in manager.session_connections
        assert len(manager.session_connections[session_id]) == 1
        assert websocket2 in manager.session_connections[session_id]

        # Disconnect the last one
        await manager.disconnect(websocket2, session_id)

        # Now session group should be removed
        assert session_id not in manager.session_connections

    @pytest.mark.asyncio
    async def test_broadcast_stat_update_session_connections(self, manager):
        """Test broadcasting stat updates to session connections."""
        session_id = "test-session-123"
        websocket1 = MagicMock(spec=WebSocket)
        websocket1.accept = AsyncMock()
        websocket1.send_text = AsyncMock()

        websocket2 = MagicMock(spec=WebSocket)
        websocket2.accept = AsyncMock()
        websocket2.send_text = AsyncMock()

        # Connect websockets
        await manager.connect(websocket1, session_id)
        await manager.connect(websocket2, session_id=None)  # Stats connection

        # Broadcast stat update
        await manager.broadcast_stat_update(
            stat_type=StatType.MESSAGES,
            session_id=session_id,
            new_value=42,
            formatted_value="42",
            delta=1,
            animation=AnimationType.INCREMENT,
        )

        # Both connections should receive the update
        assert websocket1.send_text.call_count == 2  # Connection event + stat update
        assert websocket2.send_text.call_count == 2  # Connection event + stat update

        # Check the stat update message
        stat_calls = [
            call
            for call in websocket1.send_text.call_args_list
            if "stat_update" in str(call)
        ]
        assert len(stat_calls) == 1

        sent_data = json.loads(stat_calls[0][0][0])
        assert sent_data["type"] == "stat_update"
        assert sent_data["stat_type"] == "messages"
        assert sent_data["session_id"] == session_id
        assert sent_data["update"]["new_value"] == 42

    @pytest.mark.asyncio
    async def test_broadcast_new_message(self, manager):
        """Test broadcasting new message events."""
        session_id = "test-session-123"
        websocket = MagicMock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()

        # Connect websocket to session
        await manager.connect(websocket, session_id)

        # Create message preview
        message_preview = MessagePreview(
            uuid="msg-123",
            author="user",
            timestamp=datetime.utcnow(),
            preview="Hello world",
            tool_used="bash",
        )

        # Broadcast new message
        await manager.broadcast_new_message(session_id, message_preview)

        # Verify message was sent
        assert websocket.send_text.call_count == 2  # Connection event + new message

        # Check the new message event
        new_msg_calls = [
            call
            for call in websocket.send_text.call_args_list
            if "new_message" in str(call)
        ]
        assert len(new_msg_calls) == 1

        sent_data = json.loads(new_msg_calls[0][0][0])
        assert sent_data["type"] == "new_message"
        assert sent_data["session_id"] == session_id
        assert sent_data["message"]["uuid"] == "msg-123"
        assert sent_data["message"]["author"] == "user"

    @pytest.mark.asyncio
    async def test_handle_websocket_ping_pong(self, manager, mock_websocket):
        """Test WebSocket ping/pong handling."""
        session_id = "test-session-123"

        # Mock receiving a ping message
        mock_websocket.receive_text = AsyncMock(
            side_effect=[
                json.dumps({"type": "ping"}),
                WebSocketDisconnect(),  # Disconnect after ping
            ]
        )

        # Handle WebSocket messages
        await manager.handle_websocket_messages(mock_websocket, session_id)

        # Verify pong was sent (should have at least one send_text call for pong)
        assert mock_websocket.send_text.call_count >= 1

        # Check if any call contains pong
        pong_calls = [
            call
            for call in mock_websocket.send_text.call_args_list
            if "pong" in str(call)
        ]
        assert len(pong_calls) >= 1

    @pytest.mark.asyncio
    async def test_handle_websocket_invalid_json(self, manager, mock_websocket):
        """Test handling of invalid JSON in WebSocket messages."""
        session_id = "test-session-123"

        # Mock receiving invalid JSON
        mock_websocket.receive_text = AsyncMock(
            side_effect=["invalid json {", WebSocketDisconnect()]
        )

        # Should not raise exception
        await manager.handle_websocket_messages(mock_websocket, session_id)

    @pytest.mark.asyncio
    async def test_handle_websocket_disconnect(self, manager, mock_websocket):
        """Test WebSocket disconnect handling."""
        session_id = "test-session-123"

        # First connect
        await manager.connect(mock_websocket, session_id)
        assert mock_websocket in manager.session_connections[session_id]

        # Mock disconnect during message handling
        mock_websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect())

        # Handle messages should handle disconnect gracefully
        await manager.handle_websocket_messages(mock_websocket, session_id)

        # Connection should be cleaned up
        assert session_id not in manager.session_connections

    @pytest.mark.asyncio
    async def test_send_to_websocket_failure_cleanup(self, manager, mock_websocket):
        """Test that failed WebSocket sends clean up connections."""
        session_id = "test-session-123"

        # Connect websocket
        await manager.connect(mock_websocket, session_id)
        await manager.connect(mock_websocket, session_id=None)  # Also add to stats

        # Make send_text fail
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Connection failed"))

        # Try to send a stat update
        await manager.broadcast_stat_update(
            stat_type=StatType.MESSAGES,
            session_id=session_id,
            new_value=42,
            formatted_value="42",
            delta=1,
        )

        # Connection should be cleaned up from both groups
        assert mock_websocket not in manager.stats_connections
        if session_id in manager.session_connections:
            assert mock_websocket not in manager.session_connections[session_id]

    def test_get_connection_stats(self, manager):
        """Test getting connection statistics."""
        # Initially should be empty
        stats = manager.get_connection_stats()
        assert stats["total_connections"] == 0
        assert stats["stats_connections"] == 0
        assert stats["session_connections"] == {}

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, manager):
        """Test handling multiple concurrent connections."""
        websockets = []
        session_ids = []

        # Create multiple websockets and connect them concurrently
        for i in range(5):
            websocket = MagicMock(spec=WebSocket)
            websocket.accept = AsyncMock()
            websocket.send_text = AsyncMock()
            websockets.append(websocket)

            session_id = f"session-{i}"
            session_ids.append(session_id)

        # Connect all concurrently
        tasks = [manager.connect(ws, sid) for ws, sid in zip(websockets, session_ids)]
        await asyncio.gather(*tasks)

        # Verify all connections are tracked
        assert len(manager.session_connections) == 5
        for i, session_id in enumerate(session_ids):
            assert session_id in manager.session_connections
            assert websockets[i] in manager.session_connections[session_id]

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_connections(self, manager):
        """Test broadcasting to empty connection sets."""
        # Should not raise exception when no connections exist
        await manager.broadcast_stat_update(
            stat_type=StatType.MESSAGES,
            session_id="nonexistent-session",
            new_value=42,
            formatted_value="42",
            delta=1,
        )

        await manager.broadcast_new_message(
            "nonexistent-session",
            MessagePreview(
                uuid="test", author="user", timestamp=datetime.utcnow(), preview="test"
            ),
        )


class TestRealtimeStatsService:
    """Test RealtimeStatsService for message broadcasting."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.messages = MagicMock()
        return db

    @pytest.fixture
    def stats_service(self, mock_db):
        """Create RealtimeStatsService with mock database."""
        return RealtimeStatsService(mock_db)

    @pytest.fixture
    def mock_connection_manager(self):
        """Mock the global connection manager."""
        with patch("app.services.websocket_manager.connection_manager") as mock_manager:
            mock_manager.broadcast_stat_update = AsyncMock()
            mock_manager.broadcast_new_message = AsyncMock()
            yield mock_manager

    @pytest.mark.asyncio
    async def test_update_message_count(
        self, stats_service, mock_db, mock_connection_manager
    ):
        """Test updating message count."""
        session_id = "test-session-123"

        # Mock database count
        mock_db.messages.count_documents = AsyncMock(return_value=42)

        await stats_service.update_message_count(session_id)

        # Verify database was queried
        mock_db.messages.count_documents.assert_called_once_with(
            {"sessionId": session_id}
        )

        # Verify broadcast was called
        mock_connection_manager.broadcast_stat_update.assert_called_once()
        call_args = mock_connection_manager.broadcast_stat_update.call_args
        assert call_args[1]["stat_type"] == StatType.MESSAGES
        assert call_args[1]["session_id"] == session_id
        assert call_args[1]["new_value"] == 42
        assert call_args[1]["formatted_value"] == "42"
        assert call_args[1]["delta"] == 1

    @pytest.mark.asyncio
    async def test_update_message_count_large_number(
        self, stats_service, mock_db, mock_connection_manager
    ):
        """Test updating message count with large numbers."""
        session_id = "test-session-123"

        # Mock large count
        mock_db.messages.count_documents = AsyncMock(return_value=1500)

        await stats_service.update_message_count(session_id)

        # Verify formatting for large numbers
        call_args = mock_connection_manager.broadcast_stat_update.call_args
        assert call_args[1]["new_value"] == 1500
        assert call_args[1]["formatted_value"] == "1K"

    @pytest.mark.asyncio
    async def test_update_tool_usage(
        self, stats_service, mock_db, mock_connection_manager
    ):
        """Test updating tool usage count."""
        session_id = "test-session-123"

        # Mock aggregation result
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[{"total_tools": 15}])
        mock_db.messages.aggregate.return_value = mock_aggregate

        await stats_service.update_tool_usage(session_id)

        # Verify aggregation was called
        mock_db.messages.aggregate.assert_called_once()

        # Verify broadcast was called
        mock_connection_manager.broadcast_stat_update.assert_called_once()
        call_args = mock_connection_manager.broadcast_stat_update.call_args
        assert call_args[1]["stat_type"] == StatType.TOOLS
        assert call_args[1]["new_value"] == 15
        assert call_args[1]["formatted_value"] == "15"

    @pytest.mark.asyncio
    async def test_update_tool_usage_no_results(
        self, stats_service, mock_db, mock_connection_manager
    ):
        """Test updating tool usage with no results."""
        session_id = "test-session-123"

        # Mock empty aggregation result
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[])
        mock_db.messages.aggregate.return_value = mock_aggregate

        await stats_service.update_tool_usage(session_id)

        # Should broadcast 0 count
        call_args = mock_connection_manager.broadcast_stat_update.call_args
        assert call_args[1]["new_value"] == 0
        assert call_args[1]["formatted_value"] == "0"

    @pytest.mark.asyncio
    async def test_update_token_count(
        self, stats_service, mock_db, mock_connection_manager
    ):
        """Test updating token count."""
        session_id = "test-session-123"

        # Mock aggregation result
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[{"total_tokens": 5000}])
        mock_db.messages.aggregate.return_value = mock_aggregate

        await stats_service.update_token_count(session_id)

        # Verify broadcast was called
        call_args = mock_connection_manager.broadcast_stat_update.call_args
        assert call_args[1]["stat_type"] == StatType.TOKENS
        assert call_args[1]["new_value"] == 5000
        assert call_args[1]["formatted_value"] == "5K"  # 5000 should format as 5K

    @pytest.mark.asyncio
    async def test_update_token_count_millions(
        self, stats_service, mock_db, mock_connection_manager
    ):
        """Test updating token count with millions."""
        session_id = "test-session-123"

        # Mock large token count
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[{"total_tokens": 2500000}])
        mock_db.messages.aggregate.return_value = mock_aggregate

        await stats_service.update_token_count(session_id)

        # Verify formatting for millions
        call_args = mock_connection_manager.broadcast_stat_update.call_args
        assert call_args[1]["new_value"] == 2500000
        assert call_args[1]["formatted_value"] == "2M"

    @pytest.mark.asyncio
    async def test_update_cost(self, stats_service, mock_db, mock_connection_manager):
        """Test updating cost."""
        session_id = "test-session-123"

        # Mock aggregation result
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[{"total_cost": 12.34}])
        mock_db.messages.aggregate.return_value = mock_aggregate

        await stats_service.update_cost(session_id)

        # Verify broadcast was called
        call_args = mock_connection_manager.broadcast_stat_update.call_args
        assert call_args[1]["stat_type"] == StatType.COST
        assert call_args[1]["new_value"] == 1234  # 12.34 * 100 = 1234 cents
        assert call_args[1]["formatted_value"] == "$12.34"

    @pytest.mark.asyncio
    async def test_update_cost_decimal128(
        self, stats_service, mock_db, mock_connection_manager
    ):
        """Test updating cost with Decimal128 format."""
        session_id = "test-session-123"

        # Mock Decimal128 object
        decimal_mock = MagicMock()
        decimal_mock.to_decimal.return_value = 5.67

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[{"total_cost": decimal_mock}])
        mock_db.messages.aggregate.return_value = mock_aggregate

        await stats_service.update_cost(session_id)

        # Verify Decimal128 was handled correctly
        call_args = mock_connection_manager.broadcast_stat_update.call_args
        assert call_args[1]["new_value"] == 567  # 5.67 * 100 = 567 cents
        assert call_args[1]["formatted_value"] == "$5.67"

    @pytest.mark.asyncio
    async def test_broadcast_new_message(self, stats_service, mock_connection_manager):
        """Test broadcasting new message."""
        session_id = "test-session-123"
        message_data = {
            "uuid": "msg-456",
            "author": "assistant",
            "timestamp": datetime.utcnow(),
            "text": "This is a very long message that should definitely be truncated because it clearly exceeds the 100 character preview limit that is set in the WebSocket manager service for message previews",
            "toolsUsed": [{"name": "bash"}],
        }

        # Mock the update_message_count method
        with patch.object(
            stats_service, "update_message_count", new=AsyncMock()
        ) as mock_update:
            await stats_service.broadcast_new_message(session_id, message_data)

        # Verify new message was broadcast
        mock_connection_manager.broadcast_new_message.assert_called_once()
        call_args = mock_connection_manager.broadcast_new_message.call_args
        assert call_args[0][0] == session_id

        # Verify message preview
        preview = call_args[0][1]
        assert preview.uuid == "msg-456"
        assert preview.author == "assistant"
        assert preview.tool_used == "bash"
        assert "..." in preview.preview  # Should be truncated

        # Verify message count was updated
        mock_update.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_broadcast_new_message_short_text(
        self, stats_service, mock_connection_manager
    ):
        """Test broadcasting new message with short text."""
        session_id = "test-session-123"
        message_data = {
            "uuid": "msg-789",
            "author": "user",
            "timestamp": datetime.utcnow(),
            "text": "Short message",
            "toolsUsed": [],
        }

        with patch.object(stats_service, "update_message_count", new=AsyncMock()):
            await stats_service.broadcast_new_message(session_id, message_data)

        # Verify preview is not truncated
        call_args = mock_connection_manager.broadcast_new_message.call_args
        preview = call_args[0][1]
        assert preview.preview == "Short message"
        assert "..." not in preview.preview
        assert preview.tool_used is None  # No tools used

    @pytest.mark.asyncio
    async def test_broadcast_new_message_no_tools(
        self, stats_service, mock_connection_manager
    ):
        """Test broadcasting new message with no tools."""
        session_id = "test-session-123"
        message_data = {
            "uuid": "msg-999",
            "author": "user",
            "timestamp": datetime.utcnow(),
            "text": "Message without tools",
        }

        with patch.object(stats_service, "update_message_count", new=AsyncMock()):
            await stats_service.broadcast_new_message(session_id, message_data)

        call_args = mock_connection_manager.broadcast_new_message.call_args
        preview = call_args[0][1]
        assert preview.tool_used is None

    @pytest.mark.asyncio
    async def test_stats_service_error_handling(
        self, stats_service, mock_db, mock_connection_manager
    ):
        """Test error handling in stats service methods."""
        session_id = "test-session-123"

        # Make database operations fail
        mock_db.messages.count_documents = AsyncMock(side_effect=Exception("DB Error"))

        # Should not raise exception
        await stats_service.update_message_count(session_id)

        # Broadcast should not have been called due to error
        mock_connection_manager.broadcast_stat_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_aggregation_pipeline_structure(
        self, stats_service, mock_db, mock_connection_manager
    ):
        """Test that aggregation pipelines are structured correctly."""
        session_id = "test-session-123"

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[{"total_tools": 5}])
        mock_db.messages.aggregate.return_value = mock_aggregate

        await stats_service.update_tool_usage(session_id)

        # Verify aggregation pipeline was called correctly
        call_args = mock_db.messages.aggregate.call_args[0][0]

        # Check pipeline structure
        assert len(call_args) >= 3  # Should have match, unwind, match, count stages
        assert call_args[0]["$match"]["sessionId"] == session_id
        assert "$unwind" in call_args[1]
        assert "$count" in call_args[-1]
