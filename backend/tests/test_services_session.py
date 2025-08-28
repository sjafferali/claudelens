"""Fixed tests for the session service with hierarchical ownership."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import Decimal128, ObjectId

from app.services.session import SessionService


async def async_iter(items):
    """Helper to create async iterator from list."""
    for item in items:
        yield item


def setup_project_mocks(mock_db, user_id, project_ids=None):
    """Setup mocks for hierarchical ownership queries."""
    if project_ids is None:
        project_ids = [ObjectId()]

    # Mock projects.find for user
    mock_db.projects.find.return_value.to_list = AsyncMock(
        return_value=[{"_id": pid} for pid in project_ids]
    )

    return project_ids


@pytest.fixture
def mock_db():
    """Create a mock database."""
    db = MagicMock()
    db.sessions = MagicMock()
    db.messages = MagicMock()
    db.projects = MagicMock()

    # Set default AsyncMocks for common async methods
    db.sessions.find_one = AsyncMock()
    db.sessions.count_documents = AsyncMock()
    db.projects.find_one = AsyncMock()
    db.projects.find = MagicMock()
    db.projects.find.return_value.to_list = AsyncMock()
    db.messages.find_one = AsyncMock()
    db.messages.count_documents = AsyncMock()
    db.messages.distinct = AsyncMock()

    return db


@pytest.fixture
def session_service(mock_db):
    """Create a session service with mock database."""
    return SessionService(mock_db)


class TestSessionService:
    """Test cases for SessionService."""

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, session_service, mock_db):
        """Test listing sessions when none exist."""
        user_id = str(ObjectId())
        setup_project_mocks(mock_db, user_id, [])

        mock_db.sessions.count_documents = AsyncMock(return_value=0)
        mock_db.sessions.find.return_value.sort.return_value.skip.return_value.limit.return_value.__aiter__ = lambda self: async_iter(
            []
        )

        sessions, total = await session_service.list_sessions(
            user_id, {}, 0, 10, "started_at", "desc"
        )

        assert sessions == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_list_sessions_with_data(self, session_service, mock_db):
        """Test listing sessions with data."""
        user_id = str(ObjectId())
        project_id = ObjectId()
        setup_project_mocks(mock_db, user_id, [project_id])

        mock_data = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "sessionId": "session-123",
                "projectId": project_id,
                "summary": "Test session",
                "startedAt": datetime.now(UTC),
                "endedAt": datetime.now(UTC),
                "messageCount": 5,
                "totalCost": Decimal128("0.025"),
                "toolsUsed": 3,
                "totalTokens": 1000,
                "inputTokens": 600,
                "outputTokens": 400,
            }
        ]

        mock_db.sessions.count_documents = AsyncMock(return_value=1)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter(mock_data)
        )
        mock_db.sessions.find.return_value = mock_cursor

        sessions, total = await session_service.list_sessions(
            user_id, {}, 0, 10, "started_at", "desc"
        )

        assert len(sessions) == 1
        assert total == 1
        assert sessions[0].session_id == "session-123"

    @pytest.mark.asyncio
    async def test_get_session_by_object_id(self, session_service, mock_db):
        """Test getting a session by MongoDB ObjectId."""
        user_id = str(ObjectId())
        session_id = str(ObjectId())
        project_id = ObjectId()

        mock_session = {
            "_id": ObjectId(session_id),
            "sessionId": "session-123",
            "projectId": project_id,
            "summary": "Test session",
            "startedAt": datetime.now(UTC),
            "endedAt": datetime.now(UTC),
            "messageCount": 5,
            "totalCost": Decimal128("0.025"),
        }

        # Mock session lookup
        mock_db.sessions.find_one = AsyncMock(return_value=mock_session)

        # Mock project ownership check
        mock_db.projects.find_one = AsyncMock(
            return_value={"_id": project_id, "user_id": ObjectId(user_id)}
        )

        # Mock messages queries
        mock_db.messages.count_documents = AsyncMock(return_value=0)
        mock_db.messages.distinct = AsyncMock(return_value=["gpt-4"])
        mock_db.messages.find_one = AsyncMock(
            return_value={"content": "Test message", "cwd": "/test/dir"}
        )

        result = await session_service.get_session(
            user_id, session_id, include_messages=False
        )

        assert result is not None
        assert result.session_id == "session-123"

    @pytest.mark.asyncio
    async def test_get_session_by_session_id(self, session_service, mock_db):
        """Test getting a session by sessionId field."""
        user_id = str(ObjectId())
        session_id = "session-123"
        project_id = ObjectId()

        mock_session = {
            "_id": ObjectId(),
            "sessionId": session_id,
            "projectId": project_id,
            "summary": "Test session",
            "startedAt": datetime.now(UTC),
            "endedAt": datetime.now(UTC),
            "messageCount": 5,
            "totalCost": Decimal128("0.025"),
        }

        # Mock session lookup by sessionId
        mock_db.sessions.find_one = AsyncMock(return_value=mock_session)

        # Mock project ownership check
        mock_db.projects.find_one = AsyncMock(
            return_value={"_id": project_id, "user_id": ObjectId(user_id)}
        )

        # Mock messages distinct and find_one for extra fields
        mock_db.messages.distinct = AsyncMock(return_value=[])
        mock_db.messages.find_one = AsyncMock(return_value=None)

        result = await session_service.get_session(
            user_id, session_id, include_messages=False
        )

        # Should return None because session_id is not a valid ObjectId
        # The service tries to find by ObjectId first, fails, then finds by sessionId
        assert result is not None
        assert result.session_id == session_id

    @pytest.mark.asyncio
    async def test_get_session_with_messages(self, session_service, mock_db):
        """Test getting a session with messages included."""
        user_id = str(ObjectId())
        session_id = str(ObjectId())
        project_id = ObjectId()

        mock_session = {
            "_id": ObjectId(session_id),
            "sessionId": "session-123",
            "projectId": project_id,
            "summary": "Test session",
            "startedAt": datetime.now(UTC),
            "endedAt": datetime.now(UTC),
            "messageCount": 2,
            "totalCost": Decimal128("0.025"),
        }

        # Mock session lookup
        mock_db.sessions.find_one = AsyncMock(return_value=mock_session)

        # Mock project ownership check
        mock_db.projects.find_one = AsyncMock(
            return_value={"_id": project_id, "user_id": ObjectId(user_id)}
        )

        # Mock messages distinct and find_one for extra fields
        mock_db.messages.distinct = AsyncMock(return_value=["claude-3"])

        mock_messages = [
            {
                "_id": ObjectId(),
                "uuid": "msg-1",
                "type": "user",
                "sessionId": "session-123",
                "content": "Hello",
                "timestamp": datetime.now(UTC),
            },
            {
                "_id": ObjectId(),
                "uuid": "msg-2",
                "type": "assistant",
                "sessionId": "session-123",
                "content": "Hi there!",
                "timestamp": datetime.now(UTC),
            },
        ]

        # Mock session lookup
        mock_db.sessions.find_one = AsyncMock(return_value=mock_session)

        # Mock project ownership check
        mock_db.projects.find_one = AsyncMock(
            return_value={"_id": project_id, "user_id": ObjectId(user_id)}
        )

        # Mock messages
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter(mock_messages)
        )
        mock_db.messages.find.return_value = mock_cursor
        mock_db.messages.count_documents = AsyncMock(return_value=2)
        mock_db.messages.find_one = AsyncMock(return_value=mock_messages[0])
        mock_db.messages.distinct = AsyncMock(return_value=["claude-3"])

        result = await session_service.get_session(
            user_id, session_id, include_messages=True
        )

        assert result is not None
        assert result.session_id == "session-123"
        assert len(result.messages) == 2

    @pytest.mark.asyncio
    async def test_list_sessions_sort_mapping(self, session_service, mock_db):
        """Test that sort field mapping works correctly."""
        user_id = str(ObjectId())
        project_id = ObjectId()
        setup_project_mocks(mock_db, user_id, [project_id])

        mock_db.sessions.count_documents = AsyncMock(return_value=0)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter([])
        )
        mock_db.sessions.find.return_value = mock_cursor

        # Test different sort fields
        await session_service.list_sessions(user_id, {}, 0, 10, "started_at", "desc")
        mock_cursor.sort.assert_called_with("startedAt", -1)

        await session_service.list_sessions(user_id, {}, 0, 10, "message_count", "asc")
        mock_cursor.sort.assert_called_with("messageCount", 1)

        await session_service.list_sessions(user_id, {}, 0, 10, "total_cost", "desc")
        mock_cursor.sort.assert_called_with("totalCost", -1)

    @pytest.mark.asyncio
    async def test_decimal128_conversion(self, session_service, mock_db):
        """Test that Decimal128 values are properly converted to float."""
        user_id = str(ObjectId())
        project_id = ObjectId()
        setup_project_mocks(mock_db, user_id, [project_id])

        mock_data = [
            {
                "_id": ObjectId(),
                "sessionId": "session-123",
                "projectId": project_id,
                "startedAt": datetime.now(UTC),
                "totalCost": Decimal128("123.456"),
                "messageCount": 10,
            }
        ]

        mock_db.sessions.count_documents = AsyncMock(return_value=1)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter(mock_data)
        )
        mock_db.sessions.find.return_value = mock_cursor

        sessions, _ = await session_service.list_sessions(
            user_id, {}, 0, 10, "started_at", "desc"
        )

        assert len(sessions) == 1
        assert sessions[0].total_cost == 123.456
        assert isinstance(sessions[0].total_cost, float)
