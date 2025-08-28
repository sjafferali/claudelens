"""Fixed tests for the message service with hierarchical ownership."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from app.services.message import MessageService


async def async_iter(items):
    """Helper to create async iterator from list."""
    for item in items:
        yield item


def setup_hierarchical_mocks(mock_db, user_id, project_ids=None, session_ids=None):
    """Setup mocks for hierarchical ownership queries."""
    if project_ids is None:
        project_ids = [ObjectId()]
    if session_ids is None:
        session_ids = ["session-123"]

    # Mock projects.find for user
    mock_db.projects.find.return_value.to_list = AsyncMock(
        return_value=[{"_id": pid} for pid in project_ids]
    )

    # Mock sessions.find for projects
    mock_db.sessions.find.return_value.to_list = AsyncMock(
        return_value=[{"sessionId": sid} for sid in session_ids]
    )

    return project_ids, session_ids


@pytest.fixture
def mock_db():
    """Create a mock database."""
    db = MagicMock()
    db.messages = MagicMock()
    db.sessions = MagicMock()
    db.projects = MagicMock()
    return db


@pytest.fixture
def message_service(mock_db):
    """Create a message service with mock database and mocked rolling service."""
    # Create a mock rolling service
    mock_rolling = MagicMock()

    # Set default mock behaviors
    mock_rolling.find_messages = AsyncMock(return_value=([], 0))
    mock_rolling.find_one = AsyncMock(return_value=None)
    mock_rolling.update_one = AsyncMock(return_value=True)
    mock_rolling.aggregate_across_collections = AsyncMock(return_value=[])
    mock_rolling.count_documents = AsyncMock(return_value=0)

    # Patch the RollingMessageService import in message.py
    with patch("app.services.message.RollingMessageService", return_value=mock_rolling):
        # Create service (this will use the mocked RollingMessageService)
        service = MessageService(mock_db)

        # Ensure rolling_service is our mock
        service.rolling_service = mock_rolling

        return service


class TestMessageService:
    """Test cases for MessageService."""

    @pytest.mark.asyncio
    async def test_list_messages_empty(self, message_service, mock_db):
        """Test listing messages when none exist."""
        user_id = str(ObjectId())
        setup_hierarchical_mocks(mock_db, user_id, [], [])

        message_service.rolling_service.count_documents = AsyncMock(return_value=0)
        mock_db.messages.find.return_value.sort.return_value.skip.return_value.limit.return_value.__aiter__ = lambda self: async_iter(
            []
        )

        messages, total = await message_service.list_messages(
            user_id, {}, 0, 10, "desc"
        )

        assert messages == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_list_messages_with_data(self, message_service, mock_db):
        """Test listing messages with data."""
        user_id = str(ObjectId())
        project_ids, session_ids = setup_hierarchical_mocks(mock_db, user_id)

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

        # Mock rolling service methods
        message_service.rolling_service.find_messages = AsyncMock(
            return_value=(mock_data, 2)
        )

        messages, total = await message_service.list_messages(
            user_id, {}, 0, 10, "desc"
        )

        assert len(messages) == 2
        assert total == 2
        assert messages[0].uuid == "msg-123"
        assert messages[1].uuid == "msg-124"

    @pytest.mark.asyncio
    async def test_get_message_valid_id(self, message_service, mock_db):
        """Test getting a message by valid ID."""
        user_id = str(ObjectId())
        message_id = str(ObjectId())
        session_id = "session-123"
        project_id = ObjectId()

        # Mock message
        mock_message = {
            "_id": ObjectId(message_id),
            "uuid": "msg-123",
            "type": "user",
            "sessionId": session_id,
            "content": "Test message",
            "timestamp": datetime.now(UTC),
        }

        # Mock rolling service methods
        message_service.rolling_service.find_one = AsyncMock(return_value=mock_message)

        # Mock hierarchical ownership check
        mock_db.sessions.find_one = AsyncMock(
            return_value={"sessionId": session_id, "projectId": project_id}
        )
        mock_db.projects.find_one = AsyncMock(
            return_value={"_id": project_id, "user_id": ObjectId(user_id)}
        )

        result = await message_service.get_message(user_id, message_id)

        assert result is not None
        assert result.uuid == "msg-123"

    @pytest.mark.asyncio
    async def test_get_message_by_uuid(self, message_service, mock_db):
        """Test getting a message by UUID."""
        user_id = str(ObjectId())
        uuid = "msg-123"
        session_id = "session-123"
        project_id = ObjectId()

        # Mock message
        mock_message = {
            "_id": ObjectId(),
            "uuid": uuid,
            "type": "user",
            "sessionId": session_id,
            "content": "Test message",
            "timestamp": datetime.now(UTC),
        }

        # Mock rolling service methods
        message_service.rolling_service.find_one = AsyncMock(return_value=mock_message)

        # Mock hierarchical ownership check
        mock_db.sessions.find_one = AsyncMock(
            return_value={"sessionId": session_id, "projectId": project_id}
        )
        mock_db.projects.find_one = AsyncMock(
            return_value={"_id": project_id, "user_id": ObjectId(user_id)}
        )

        result = await message_service.get_message_by_uuid(user_id, uuid)

        assert result is not None
        assert result.uuid == uuid

    @pytest.mark.asyncio
    async def test_list_messages_with_filter(self, message_service, mock_db):
        """Test listing messages with various filters."""
        user_id = str(ObjectId())
        setup_hierarchical_mocks(mock_db, user_id)

        mock_data = [
            {
                "_id": ObjectId(),
                "uuid": "msg-filtered",
                "type": "user",
                "sessionId": "session-123",
                "content": "Filtered message",
                "timestamp": datetime.now(UTC),
            }
        ]

        # Mock rolling service methods
        message_service.rolling_service.find_messages = AsyncMock(
            return_value=(mock_data, 1)
        )

        # Test with type filter
        messages, total = await message_service.list_messages(
            user_id, {"type": "user"}, 0, 10, "asc"
        )

        assert len(messages) == 1
        assert total == 1
        assert messages[0].type == "user"

    @pytest.mark.asyncio
    async def test_list_messages_with_pagination(self, message_service, mock_db):
        """Test message pagination."""
        user_id = str(ObjectId())
        setup_hierarchical_mocks(mock_db, user_id)

        mock_data = [
            {
                "_id": ObjectId(),
                "uuid": f"msg-{i}",
                "type": "user",
                "sessionId": "session-123",
                "content": f"Message {i}",
                "timestamp": datetime.now(UTC),
            }
            for i in range(10)
        ]

        # Mock rolling service methods
        message_service.rolling_service.find_messages = AsyncMock(
            return_value=(mock_data, 100)
        )

        messages, total = await message_service.list_messages(
            user_id, {}, skip=20, limit=10, sort_order="asc"
        )

        assert len(messages) == 10
        assert total == 100
