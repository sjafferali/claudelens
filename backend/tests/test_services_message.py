"""Tests for the message service."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import Decimal128, ObjectId

from app.services.message import MessageService


async def async_iter(items):
    """Helper to create async iterator from list."""
    for item in items:
        yield item


@pytest.fixture
def mock_db():
    """Create a mock database."""
    db = MagicMock()
    db.messages = MagicMock()
    db.sessions = MagicMock()
    return db


@pytest.fixture
def message_service(mock_db):
    """Create a message service with mock database."""
    return MessageService(mock_db)


class TestMessageService:
    """Test cases for MessageService."""

    @pytest.mark.asyncio
    async def test_list_messages_empty(self, message_service, mock_db):
        """Test listing messages when none exist."""
        # Setup
        mock_db.messages.count_documents = AsyncMock(return_value=0)
        mock_db.messages.find.return_value.sort.return_value.skip.return_value.limit.return_value.__aiter__ = lambda self: async_iter(
            []
        )

        # Execute
        messages, total = await message_service.list_messages({}, 0, 10, "desc")

        # Assert
        assert messages == []
        assert total == 0
        mock_db.messages.count_documents.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_list_messages_with_data(self, message_service, mock_db):
        """Test listing messages with data."""
        # Setup
        mock_data = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "uuid": "msg-123",
                "type": "user",
                "sessionId": "session-123",
                "content": "Hello, Claude!",
                "timestamp": datetime.now(UTC),
                "createdAt": datetime.now(UTC),
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "uuid": "msg-124",
                "type": "assistant",
                "sessionId": "session-123",
                "content": "Hello! How can I help you?",
                "timestamp": datetime.now(UTC),
                "createdAt": datetime.now(UTC),
                "model": "claude-3-opus",
            },
        ]

        mock_db.messages.count_documents = AsyncMock(return_value=2)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter(mock_data)
        )
        mock_db.messages.find.return_value = mock_cursor

        # Execute
        messages, total = await message_service.list_messages({}, 0, 10, "desc")

        # Assert
        assert len(messages) == 2
        assert total == 2
        assert messages[0].uuid == "msg-123"
        assert messages[0].content == "Hello, Claude!"
        assert messages[1].model == "claude-3-opus"

    @pytest.mark.asyncio
    async def test_list_messages_with_filter(self, message_service, mock_db):
        """Test listing messages with filter."""
        # Setup
        filter_dict = {"sessionId": "session-123", "type": "user"}
        mock_db.messages.count_documents = AsyncMock(return_value=1)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter([])
        )
        mock_db.messages.find.return_value = mock_cursor

        # Execute
        messages, total = await message_service.list_messages(filter_dict, 0, 10, "asc")

        # Assert
        mock_db.messages.find.assert_called_once_with(filter_dict)
        mock_cursor.sort.assert_called_once_with("timestamp", 1)  # asc = 1

    @pytest.mark.asyncio
    async def test_get_message_valid_id(self, message_service, mock_db):
        """Test getting a message by valid ID."""
        # Setup
        message_id = "507f1f77bcf86cd799439011"
        message_data = {
            "_id": ObjectId(message_id),
            "uuid": "msg-123",
            "type": "user",
            "sessionId": "session-123",
            "content": "Test message",
            "timestamp": datetime.now(UTC),
            "createdAt": datetime.now(UTC),
            "costUsd": Decimal128("0.001"),
            "usage": {"input_tokens": 10, "output_tokens": 20},
        }

        mock_db.messages.find_one = AsyncMock(return_value=message_data)

        # Execute
        message = await message_service.get_message(message_id)

        # Assert
        assert message is not None
        assert message.uuid == "msg-123"
        assert message.cost_usd == 0.001
        assert message.usage == {"input_tokens": 10, "output_tokens": 20}

    @pytest.mark.asyncio
    async def test_get_message_invalid_id(self, message_service, mock_db):
        """Test getting a message with invalid ID."""
        # Execute
        message = await message_service.get_message("invalid-id")

        # Assert
        assert message is None
        mock_db.messages.find_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_message_not_found(self, message_service, mock_db):
        """Test getting a non-existent message."""
        # Setup
        mock_db.messages.find_one = AsyncMock(return_value=None)

        # Execute
        message = await message_service.get_message("507f1f77bcf86cd799439011")

        # Assert
        assert message is None

    @pytest.mark.asyncio
    async def test_get_message_by_uuid(self, message_service, mock_db):
        """Test getting a message by UUID."""
        # Setup
        message_data = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "uuid": "msg-123",
            "type": "user",
            "sessionId": "session-123",
            "content": "Test message",
            "timestamp": datetime.now(UTC),
            "createdAt": datetime.now(UTC),
        }

        mock_db.messages.find_one = AsyncMock(return_value=message_data)

        # Execute
        message = await message_service.get_message_by_uuid("msg-123")

        # Assert
        assert message is not None
        assert message.uuid == "msg-123"
        mock_db.messages.find_one.assert_called_once_with({"uuid": "msg-123"})

    @pytest.mark.asyncio
    async def test_get_message_context(self, message_service, mock_db):
        """Test getting message with context."""
        # Setup
        message_id = "507f1f77bcf86cd799439011"
        target_timestamp = datetime.now(UTC)

        target_message = {
            "_id": ObjectId(message_id),
            "uuid": "msg-2",
            "type": "user",
            "sessionId": "session-123",
            "content": "Target message",
            "timestamp": target_timestamp,
            "createdAt": target_timestamp,
        }

        before_messages = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439010"),
                "uuid": "msg-1",
                "type": "assistant",
                "sessionId": "session-123",
                "content": "Before message",
                "timestamp": target_timestamp,
                "createdAt": target_timestamp,
            }
        ]

        after_messages = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "uuid": "msg-3",
                "type": "assistant",
                "sessionId": "session-123",
                "content": "After message",
                "timestamp": target_timestamp,
                "createdAt": target_timestamp,
            }
        ]

        mock_db.messages.find_one = AsyncMock(return_value=target_message)

        # Mock before cursor
        before_cursor = MagicMock()
        before_cursor.sort.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter(before_messages)
        )

        # Mock after cursor
        after_cursor = MagicMock()
        after_cursor.sort.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter(after_messages)
        )

        # Set up find to return appropriate cursor
        def mock_find(query):
            if "$lt" in query.get("timestamp", {}):
                return before_cursor
            elif "$gt" in query.get("timestamp", {}):
                return after_cursor
            return MagicMock()

        mock_db.messages.find = MagicMock(side_effect=mock_find)

        # Execute
        context = await message_service.get_message_context(
            message_id, before=2, after=2
        )

        # Assert
        assert context is not None
        assert context["target"].uuid == "msg-2"
        assert len(context["before"]) == 1
        assert len(context["after"]) == 1
        assert context["before"][0].uuid == "msg-1"
        assert context["after"][0].uuid == "msg-3"
        assert context["session_id"] == "session-123"

    @pytest.mark.asyncio
    async def test_get_message_context_invalid_id(self, message_service, mock_db):
        """Test getting message context with invalid ID."""
        # Execute
        context = await message_service.get_message_context("invalid-id", 2, 2)

        # Assert
        assert context is None

    @pytest.mark.asyncio
    async def test_doc_to_message_detail_with_metadata_usage(self, message_service):
        """Test converting document with usage in metadata."""
        # Setup
        doc = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "uuid": "msg-123",
            "type": "assistant",
            "sessionId": "session-123",
            "content": "Response",
            "timestamp": datetime.now(UTC),
            "metadata": {"usage": {"input_tokens": 15, "output_tokens": 25}},
            "costUsd": Decimal128("0.002"),
        }

        # Execute
        message = message_service._doc_to_message_detail(doc)

        # Assert
        assert message.usage == {"input_tokens": 15, "output_tokens": 25}
        assert message.cost_usd == 0.002

    @pytest.mark.asyncio
    async def test_doc_to_message_detail_with_non_decimal_cost(self, message_service):
        """Test converting document with regular float cost."""
        # Setup
        doc = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "uuid": "msg-123",
            "type": "assistant",
            "sessionId": "session-123",
            "content": "Response",
            "timestamp": datetime.now(UTC),
            "costUsd": 0.003,
        }

        # Execute
        message = message_service._doc_to_message_detail(doc)

        # Assert
        assert message.cost_usd == 0.003

    @pytest.mark.asyncio
    async def test_update_message_cost_success(self, message_service, mock_db):
        """Test successfully updating message cost."""
        # Setup
        message_id = "507f1f77bcf86cd799439011"
        mock_result = MagicMock(modified_count=1)
        mock_db.messages.update_one = AsyncMock(return_value=mock_result)

        # Execute
        success = await message_service.update_message_cost(message_id, 0.005)

        # Assert
        assert success is True
        mock_db.messages.update_one.assert_called_once()
        update_call = mock_db.messages.update_one.call_args
        assert update_call[0][0] == {"_id": ObjectId(message_id)}
        assert "$set" in update_call[0][1]
        assert "costUsd" in update_call[0][1]["$set"]

    @pytest.mark.asyncio
    async def test_update_message_cost_not_found(self, message_service, mock_db):
        """Test updating cost for non-existent message."""
        # Setup
        mock_result = MagicMock(modified_count=0)
        mock_db.messages.update_one = AsyncMock(return_value=mock_result)

        # Execute
        success = await message_service.update_message_cost(
            "507f1f77bcf86cd799439011", 0.005
        )

        # Assert
        assert success is False

    @pytest.mark.asyncio
    async def test_update_message_cost_exception(self, message_service, mock_db):
        """Test handling exception when updating cost."""
        # Setup
        mock_db.messages.update_one = AsyncMock(side_effect=Exception("DB error"))

        # Execute
        success = await message_service.update_message_cost(
            "507f1f77bcf86cd799439011", 0.005
        )

        # Assert
        assert success is False

    @pytest.mark.asyncio
    async def test_batch_update_costs(self, message_service, mock_db):
        """Test batch updating message costs."""
        # Setup
        cost_updates = {
            "msg-1": 0.001,
            "msg-2": 0.002,
            "msg-3": 0.003,
        }

        # Mock successful updates
        mock_db.messages.update_one = AsyncMock(
            return_value=MagicMock(modified_count=1)
        )

        # Mock finding session IDs
        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = lambda self: async_iter(
            [
                {"sessionId": "session-123"},
                {"sessionId": "session-123"},
                {"sessionId": "session-456"},
            ]
        )
        mock_db.messages.find.return_value = mock_cursor

        # Mock aggregation for total cost
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(
            return_value=[{"_id": None, "totalCost": Decimal128("0.006")}]
        )
        mock_db.sessions.update_one = AsyncMock()

        # Execute
        updated_count = await message_service.batch_update_costs(cost_updates)

        # Assert
        assert updated_count == 3
        assert mock_db.messages.update_one.call_count == 3
        # Should update 2 unique sessions
        assert mock_db.sessions.update_one.call_count == 2

    @pytest.mark.asyncio
    async def test_batch_update_costs_partial_success(self, message_service, mock_db):
        """Test batch update with some failures."""
        # Setup
        cost_updates = {
            "msg-1": 0.001,
            "msg-2": 0.002,
        }

        # Mock mixed results
        mock_db.messages.update_one = AsyncMock(
            side_effect=[
                MagicMock(modified_count=1),
                MagicMock(modified_count=0),
            ]
        )

        # Mock empty session list
        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = lambda self: async_iter([])
        mock_db.messages.find.return_value = mock_cursor

        # Execute
        updated_count = await message_service.batch_update_costs(cost_updates)

        # Assert
        assert updated_count == 1

    @pytest.mark.asyncio
    async def test_update_session_total_cost(self, message_service, mock_db):
        """Test updating session total cost."""
        # Setup
        session_id = "session-123"

        # Mock aggregation result
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(
            return_value=[{"_id": None, "totalCost": Decimal128("0.123")}]
        )
        mock_db.sessions.update_one = AsyncMock()

        # Execute
        await message_service._update_session_total_cost(session_id)

        # Assert
        mock_db.sessions.update_one.assert_called_once()
        update_call = mock_db.sessions.update_one.call_args
        assert update_call[0][0] == {"sessionId": session_id}
        assert "$set" in update_call[0][1]
        assert "totalCost" in update_call[0][1]["$set"]

    @pytest.mark.asyncio
    async def test_update_session_total_cost_no_messages(
        self, message_service, mock_db
    ):
        """Test updating session total cost when no messages exist."""
        # Setup
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(return_value=[])
        mock_db.sessions.update_one = AsyncMock()

        # Execute
        await message_service._update_session_total_cost("session-123")

        # Assert
        mock_db.sessions.update_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_messages_with_parent_uuid(self, message_service, mock_db):
        """Test listing messages that have parent UUIDs."""
        # Setup
        mock_data = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "uuid": "msg-123",
                "type": "user",
                "sessionId": "session-123",
                "content": "Hello",
                "timestamp": datetime.now(UTC),
                "parentUuid": "msg-122",
            },
        ]

        mock_db.messages.count_documents = AsyncMock(return_value=1)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter(mock_data)
        )
        mock_db.messages.find.return_value = mock_cursor

        # Execute
        messages, _ = await message_service.list_messages({}, 0, 10, "desc")

        # Assert
        assert messages[0].parent_uuid == "msg-122"

    @pytest.mark.asyncio
    async def test_doc_to_message_detail_with_attachments(self, message_service):
        """Test converting document with attachments and tool use."""
        # Setup
        doc = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "uuid": "msg-123",
            "type": "user",
            "sessionId": "session-123",
            "content": "Analyze this image",
            "timestamp": datetime.now(UTC),
            "attachments": [{"type": "image", "url": "http://example.com/image.png"}],
            "toolUse": [{"tool": "vision", "params": {}}],
            "contentHash": "abc123",
        }

        # Execute
        message = message_service._doc_to_message_detail(doc)

        # Assert
        assert message.attachments == [
            {"type": "image", "url": "http://example.com/image.png"}
        ]
        assert message.tool_use == [{"tool": "vision", "params": {}}]
        assert message.content_hash == "abc123"
