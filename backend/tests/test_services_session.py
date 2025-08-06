"""Tests for the session service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import Decimal128, ObjectId

from app.services.session import SessionService


async def async_iter(items):
    """Helper to create async iterator from list."""
    for item in items:
        yield item


@pytest.fixture
def mock_db():
    """Create a mock database."""
    db = MagicMock()
    db.sessions = MagicMock()
    db.messages = MagicMock()
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
        # Setup
        mock_db.sessions.count_documents = AsyncMock(return_value=0)
        mock_db.sessions.find.return_value.sort.return_value.skip.return_value.limit.return_value.__aiter__ = lambda self: async_iter(
            []
        )

        # Execute
        sessions, total = await session_service.list_sessions(
            {}, 0, 10, "started_at", "desc"
        )

        # Assert
        assert sessions == []
        assert total == 0
        mock_db.sessions.count_documents.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_list_sessions_with_data(self, session_service, mock_db):
        """Test listing sessions with data."""
        # Setup
        mock_data = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "sessionId": "session-123",
                "projectId": ObjectId("507f1f77bcf86cd799439012"),
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

        # Execute
        sessions, total = await session_service.list_sessions(
            {}, 0, 10, "started_at", "desc"
        )

        # Assert
        assert len(sessions) == 1
        assert total == 1
        assert sessions[0].session_id == "session-123"
        assert sessions[0].total_cost == 0.025
        assert sessions[0].message_count == 5

    @pytest.mark.asyncio
    async def test_list_sessions_sort_mapping(self, session_service, mock_db):
        """Test that sort field mapping works correctly."""
        # Setup
        mock_db.sessions.count_documents = AsyncMock(return_value=0)
        mock_cursor = MagicMock()
        mock_db.sessions.find.return_value = mock_cursor
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter([])
        )

        # Test different sort fields
        sort_tests = [
            ("started_at", "startedAt"),
            ("ended_at", "endedAt"),
            ("message_count", "messageCount"),
            ("total_cost", "totalCost"),
            ("unknown_field", "unknown_field"),  # Should pass through unchanged
        ]

        for input_field, expected_field in sort_tests:
            await session_service.list_sessions({}, 0, 10, input_field, "asc")
            mock_cursor.sort.assert_called_with(expected_field, 1)

    @pytest.mark.asyncio
    async def test_get_session_by_object_id(self, session_service, mock_db):
        """Test getting a session by MongoDB ObjectId."""
        # Setup
        session_id = "507f1f77bcf86cd799439011"
        session_data = {
            "_id": ObjectId(session_id),
            "sessionId": "session-123",
            "projectId": ObjectId("507f1f77bcf86cd799439012"),
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

        mock_db.sessions.find_one = AsyncMock(return_value=session_data)
        mock_db.messages.distinct = AsyncMock(return_value=["gpt-4", "gpt-3.5-turbo"])
        mock_db.messages.find_one = AsyncMock(
            side_effect=[
                {
                    "content": "First message content that is quite long and should be truncated"
                },
                {"content": "Last message content"},
            ]
        )

        # Execute
        session = await session_service.get_session(session_id)

        # Assert
        assert session is not None
        assert session.session_id == "session-123"
        assert session.total_cost == 0.025
        assert session.models_used == ["gpt-4", "gpt-3.5-turbo"]
        assert len(session.first_message) <= 100

    @pytest.mark.asyncio
    async def test_get_session_by_session_id(self, session_service, mock_db):
        """Test getting a session by sessionId field when input is not a valid ObjectId."""
        # Setup
        session_data = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "sessionId": "session-123",
            "projectId": ObjectId("507f1f77bcf86cd799439012"),
            "summary": "Test session",
            "startedAt": datetime.now(UTC),
            "messageCount": 0,
            "totalCost": None,
        }

        # Mock find_one to return the session when searching by sessionId
        async def mock_find_one(query):
            if "sessionId" in query and query["sessionId"] == "session-123":
                return session_data
            return None

        mock_db.sessions.find_one = AsyncMock(side_effect=mock_find_one)
        mock_db.messages.distinct = AsyncMock(return_value=[])
        mock_db.messages.find_one = AsyncMock(return_value=None)

        # Execute - using a non-ObjectId string
        session = await session_service.get_session("session-123")

        # Assert
        assert session is not None
        assert session.session_id == "session-123"
        assert session.models_used == []
        assert session.first_message is None
        assert session.last_message is None

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_service, mock_db):
        """Test getting a non-existent session."""
        mock_db.sessions.find_one = AsyncMock(return_value=None)

        session = await session_service.get_session("non-existent")
        assert session is None

    @pytest.mark.asyncio
    async def test_get_session_with_messages(self, session_service, mock_db):
        """Test getting a session with messages included."""
        # Setup
        session_data = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "sessionId": "session-123",
            "projectId": ObjectId("507f1f77bcf86cd799439012"),
            "summary": "Test session",
            "startedAt": datetime.now(UTC),
            "messageCount": 2,
        }

        message_data = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439013"),
                "uuid": "msg-1",
                "type": "user",
                "sessionId": "session-123",
                "content": "Hello",
                "timestamp": datetime.now(UTC),
                "createdAt": datetime.now(UTC),
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439014"),
                "uuid": "msg-2",
                "type": "assistant",
                "sessionId": "session-123",
                "content": "Hi there!",
                "timestamp": datetime.now(UTC),
                "createdAt": datetime.now(UTC),
                "costUsd": Decimal128("0.001"),
                "usage": {"input_tokens": 10, "output_tokens": 5},
            },
        ]

        mock_db.sessions.find_one = AsyncMock(return_value=session_data)
        mock_db.messages.distinct = AsyncMock(return_value=["gpt-4"])
        mock_db.messages.find_one = AsyncMock(
            side_effect=[
                message_data[0],
                message_data[1],
            ]
        )

        # Mock for get_session_messages
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter(message_data)
        )
        mock_db.messages.find.return_value = mock_cursor

        # Execute
        session = await session_service.get_session(
            "507f1f77bcf86cd799439011", include_messages=True
        )

        # Assert
        assert session is not None
        assert session.messages is not None
        assert len(session.messages) == 2
        assert session.messages[0].content == "Hello"
        assert session.messages[1].cost_usd == 0.001

    @pytest.mark.asyncio
    async def test_get_session_messages(self, session_service, mock_db):
        """Test getting messages for a session."""
        # Setup session lookup
        session_data = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "sessionId": "session-123",
        }
        mock_db.sessions.find_one = AsyncMock(return_value=session_data)

        # Setup messages
        message_data = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439013"),
                "uuid": "msg-1",
                "type": "user",
                "sessionId": "session-123",
                "message": {"content": "Hello from message field"},
                "timestamp": datetime.now(UTC),
                "createdAt": datetime.now(UTC),
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439014"),
                "uuid": "msg-2",
                "type": "assistant",
                "sessionId": "session-123",
                "content": "Direct content field",
                "timestamp": datetime.now(UTC),
                "createdAt": datetime.now(UTC),
                "costUsd": 0.001,  # Test non-Decimal128 cost
                "usage": {"input_tokens": 10, "output_tokens": 5},
            },
        ]

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter(message_data)
        )
        mock_db.messages.find.return_value = mock_cursor

        # Execute
        messages = await session_service.get_session_messages(
            "507f1f77bcf86cd799439011", skip=0, limit=10
        )

        # Assert
        assert len(messages) == 2
        assert messages[0].content == "Hello from message field"  # From message.content
        assert messages[1].content == "Direct content field"  # From direct content
        assert messages[1].cost_usd == 0.001
        assert messages[1].inputTokens == 10
        assert messages[1].outputTokens == 5

    @pytest.mark.asyncio
    async def test_generate_summary_with_user_message(self, session_service, mock_db):
        """Test generating summary from user message."""
        # Setup
        session_id = "507f1f77bcf86cd799439011"
        mock_db.sessions.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(session_id),
                "sessionId": "session-123",
            }
        )

        messages = [
            {
                "type": "user",
                "content": "How can I implement a binary search tree in Python?",
                "timestamp": datetime.now(UTC),
            },
            {
                "type": "assistant",
                "content": "I'll help you implement a binary search tree...",
                "timestamp": datetime.now(UTC),
            },
        ]

        mock_db.messages.find.return_value.sort.return_value.to_list = AsyncMock(
            return_value=messages
        )
        mock_db.sessions.update_one = AsyncMock()

        # Execute
        summary = await session_service.generate_summary(session_id)

        # Assert
        assert summary == "How can I implement a binary search tree in Python?"
        mock_db.sessions.update_one.assert_called_once()
        update_call = mock_db.sessions.update_one.call_args
        assert "$set" in update_call[0][1]
        assert update_call[0][1]["$set"]["summary"] == summary

    @pytest.mark.asyncio
    async def test_generate_summary_long_content(self, session_service, mock_db):
        """Test generating summary from long content."""
        # Setup
        session_id = "507f1f77bcf86cd799439011"
        mock_db.sessions.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(session_id),
                "sessionId": "session-123",
            }
        )

        long_content = "This is a very long question that goes on and on " * 10
        messages = [
            {
                "type": "user",
                "content": long_content,
                "timestamp": datetime.now(UTC),
            },
        ]

        mock_db.messages.find.return_value.sort.return_value.to_list = AsyncMock(
            return_value=messages
        )
        mock_db.sessions.update_one = AsyncMock()

        # Execute
        summary = await session_service.generate_summary(session_id)

        # Assert
        assert len(summary) == 100  # Should be truncated to 97 + "..."
        assert summary.endswith("...")

    @pytest.mark.asyncio
    async def test_generate_summary_with_code_blocks(self, session_service, mock_db):
        """Test generating summary that removes code blocks."""
        # Setup
        session_id = "507f1f77bcf86cd799439011"
        mock_db.sessions.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(session_id),
                "sessionId": "session-123",
            }
        )

        messages = [
            {
                "type": "user",
                "content": "Fix this code: ```python\ndef broken():\n    pass\n``` please help",
                "timestamp": datetime.now(UTC),
            },
        ]

        mock_db.messages.find.return_value.sort.return_value.to_list = AsyncMock(
            return_value=messages
        )
        mock_db.sessions.update_one = AsyncMock()

        # Execute
        summary = await session_service.generate_summary(session_id)

        # Assert
        assert "```" not in summary
        assert "Fix this code:" in summary

    @pytest.mark.asyncio
    async def test_generate_summary_no_user_messages(self, session_service, mock_db):
        """Test generating summary when no user messages exist."""
        # Setup
        session_id = "507f1f77bcf86cd799439011"
        mock_db.sessions.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(session_id),
                "sessionId": "session-123",
            }
        )

        messages = [
            {
                "type": "assistant",
                "content": "Working on implementing the feature...",
                "timestamp": datetime.now(UTC),
            },
            {
                "type": "assistant",
                "content": "Created the implementation",
                "timestamp": datetime.now(UTC),
            },
        ]

        mock_db.messages.find.return_value.sort.return_value.to_list = AsyncMock(
            return_value=messages
        )
        mock_db.sessions.update_one = AsyncMock()

        # Execute
        summary = await session_service.generate_summary(session_id)

        # Assert
        assert summary == "Implementation task"

    @pytest.mark.asyncio
    async def test_generate_summary_empty_conversation(self, session_service, mock_db):
        """Test generating summary for empty conversation."""
        # Setup
        session_id = "507f1f77bcf86cd799439011"
        mock_db.sessions.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(session_id),
                "sessionId": "session-123",
            }
        )

        mock_db.messages.find.return_value.sort.return_value.to_list = AsyncMock(
            return_value=[]
        )
        mock_db.sessions.update_one = AsyncMock()

        # Execute
        summary = await session_service.generate_summary(session_id)

        # Assert
        assert summary == "Empty conversation"

    @pytest.mark.asyncio
    async def test_generate_summary_invalid_session_id(self, session_service, mock_db):
        """Test generating summary with invalid session ID."""
        mock_db.sessions.find_one = AsyncMock(return_value=None)

        summary = await session_service.generate_summary("invalid-id")
        assert summary is None

    @pytest.mark.asyncio
    async def test_get_message_thread(self, session_service, mock_db):
        """Test getting a message thread with ancestors and descendants."""
        # Setup
        session_id = "507f1f77bcf86cd799439011"
        mock_db.sessions.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(session_id),
                "sessionId": "session-123",
            }
        )

        # Target message
        target_msg = {
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "uuid": "msg-2",
            "type": "user",
            "sessionId": "session-123",
            "content": "Target message",
            "timestamp": datetime.now(UTC),
            "createdAt": datetime.now(UTC),
            "parentUuid": "msg-1",
        }

        # Parent message
        parent_msg = {
            "_id": ObjectId("507f1f77bcf86cd799439012"),
            "uuid": "msg-1",
            "type": "assistant",
            "sessionId": "session-123",
            "content": "Parent message",
            "timestamp": datetime.now(UTC),
            "createdAt": datetime.now(UTC),
        }

        # Setup find_one calls
        mock_db.messages.find_one = AsyncMock(
            side_effect=[
                target_msg,  # First call finds target
                parent_msg,  # Second call finds parent
                None,  # Third call finds no more ancestors
            ]
        )

        # Mock descendants (empty for simplicity)
        mock_db.messages.find.return_value.sort.return_value.__aiter__ = (
            lambda self: async_iter([])
        )

        # Execute
        thread = await session_service.get_message_thread(session_id, "msg-2", depth=2)

        # Assert
        assert thread is not None
        assert thread["target"].uuid == "msg-2"
        assert len(thread["ancestors"]) == 1
        assert thread["ancestors"][0].uuid == "msg-1"

    @pytest.mark.asyncio
    async def test_decimal128_conversion(self, session_service, mock_db):
        """Test that Decimal128 values are properly converted to float."""
        # Setup
        session_data = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "sessionId": "session-123",
            "projectId": ObjectId("507f1f77bcf86cd799439012"),
            "summary": "Test session",
            "startedAt": datetime.now(UTC),
            "totalCost": Decimal128("123.456789"),
        }

        mock_db.sessions.count_documents = AsyncMock(return_value=1)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter([session_data])
        )
        mock_db.sessions.find.return_value = mock_cursor

        # Execute
        sessions, _ = await session_service.list_sessions(
            {}, 0, 10, "started_at", "desc"
        )

        # Assert
        assert sessions[0].total_cost == 123.456789
        assert isinstance(sessions[0].total_cost, float)

    @pytest.mark.asyncio
    async def test_list_sessions_with_project_filter(self, session_service, mock_db):
        """Test listing sessions filtered by project ID."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439012")
        filter_dict = {"projectId": project_id}

        session_data = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "sessionId": "session-123",
            "projectId": project_id,
            "summary": "Project session",
            "startedAt": datetime.now(UTC),
            "messageCount": 3,
            "totalCost": Decimal128("0.015"),
        }

        mock_db.sessions.count_documents = AsyncMock(return_value=1)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter([session_data])
        )
        mock_db.sessions.find.return_value = mock_cursor

        # Execute
        sessions, total = await session_service.list_sessions(
            filter_dict, 0, 10, "started_at", "desc"
        )

        # Assert
        assert len(sessions) == 1
        assert total == 1
        assert sessions[0].project_id == str(project_id)
        mock_db.sessions.find.assert_called_once_with(filter_dict)

    @pytest.mark.asyncio
    async def test_list_sessions_with_date_range_filter(self, session_service, mock_db):
        """Test listing sessions filtered by date range."""
        # Setup
        start_date = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date = datetime.now(UTC)
        filter_dict = {"startedAt": {"$gte": start_date, "$lte": end_date}}

        mock_db.sessions.count_documents = AsyncMock(return_value=2)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter([])
        )
        mock_db.sessions.find.return_value = mock_cursor

        # Execute
        sessions, total = await session_service.list_sessions(
            filter_dict, 0, 10, "started_at", "desc"
        )

        # Assert
        assert sessions == []
        assert total == 2
        mock_db.sessions.find.assert_called_once_with(filter_dict)

    @pytest.mark.asyncio
    async def test_list_sessions_with_multiple_filters(self, session_service, mock_db):
        """Test listing sessions with multiple filter criteria."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439012")
        filter_dict = {
            "projectId": project_id,
            "messageCount": {"$gte": 5},
            "totalCost": {"$exists": True, "$ne": None},
        }

        mock_db.sessions.count_documents = AsyncMock(return_value=0)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter([])
        )
        mock_db.sessions.find.return_value = mock_cursor

        # Execute
        sessions, total = await session_service.list_sessions(
            filter_dict, 0, 10, "total_cost", "desc"
        )

        # Assert
        assert sessions == []
        assert total == 0
        mock_db.sessions.find.assert_called_once_with(filter_dict)

    @pytest.mark.asyncio
    async def test_list_sessions_pagination_edge_cases(self, session_service, mock_db):
        """Test pagination edge cases."""
        # Setup - create 15 sessions
        sessions_data = []
        for i in range(15):
            sessions_data.append(
                {
                    "_id": ObjectId(f"507f1f77bcf86cd7994390{i:02d}"),
                    "sessionId": f"session-{i}",
                    "projectId": ObjectId("507f1f77bcf86cd799439012"),
                    "summary": f"Session {i}",
                    "startedAt": datetime.now(UTC),
                    "messageCount": i,
                }
            )

        # Test case 1: Skip beyond total count
        mock_db.sessions.count_documents = AsyncMock(return_value=15)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter([])
        )
        mock_db.sessions.find.return_value = mock_cursor

        sessions, total = await session_service.list_sessions(
            {}, 20, 10, "started_at", "desc"
        )
        assert sessions == []
        assert total == 15

        # Test case 2: Limit 0 (should return empty list)
        sessions, total = await session_service.list_sessions(
            {}, 0, 0, "started_at", "desc"
        )
        assert sessions == []
        assert total == 15

    @pytest.mark.asyncio
    async def test_get_message_thread_with_complex_hierarchy(
        self, session_service, mock_db
    ):
        """Test getting message thread with complex parent-child relationships."""
        # Setup
        session_id = "507f1f77bcf86cd799439011"
        mock_db.sessions.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(session_id),
                "sessionId": "session-123",
            }
        )

        # Create a hierarchy: root -> msg1 -> msg2 (target) -> msg3 -> msg4
        messages = {
            "root": {
                "_id": ObjectId("507f1f77bcf86cd799439010"),
                "uuid": "root",
                "type": "user",
                "sessionId": "session-123",
                "content": "Root message",
                "timestamp": datetime.now(UTC),
                "createdAt": datetime.now(UTC),
            },
            "msg-1": {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "uuid": "msg-1",
                "type": "assistant",
                "sessionId": "session-123",
                "content": "Message 1",
                "timestamp": datetime.now(UTC),
                "createdAt": datetime.now(UTC),
                "parentUuid": "root",
            },
            "msg-2": {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "uuid": "msg-2",
                "type": "user",
                "sessionId": "session-123",
                "content": "Message 2 (target)",
                "timestamp": datetime.now(UTC),
                "createdAt": datetime.now(UTC),
                "parentUuid": "msg-1",
            },
            "msg-3": {
                "_id": ObjectId("507f1f77bcf86cd799439013"),
                "uuid": "msg-3",
                "type": "assistant",
                "sessionId": "session-123",
                "content": "Message 3",
                "timestamp": datetime.now(UTC),
                "createdAt": datetime.now(UTC),
                "parentUuid": "msg-2",
            },
            "msg-4": {
                "_id": ObjectId("507f1f77bcf86cd799439014"),
                "uuid": "msg-4",
                "type": "user",
                "sessionId": "session-123",
                "content": "Message 4",
                "timestamp": datetime.now(UTC),
                "createdAt": datetime.now(UTC),
                "parentUuid": "msg-3",
            },
        }

        # Mock find_one to return appropriate messages
        async def mock_find_one(query):
            if "uuid" in query:
                return messages.get(query["uuid"])
            return None

        mock_db.messages.find_one = AsyncMock(side_effect=mock_find_one)

        # Mock find for descendants
        def mock_find_descendants(query):
            if query.get("parentUuid") == "msg-2":
                return [messages["msg-3"]]
            elif query.get("parentUuid") == "msg-3":
                return [messages["msg-4"]]
            return []

        # Setup find to handle different queries
        def mock_find(query):
            cursor = MagicMock()
            cursor.sort.return_value.__aiter__ = lambda self: async_iter(
                mock_find_descendants(query)
            )
            return cursor

        mock_db.messages.find = MagicMock(side_effect=mock_find)

        # Execute with depth=2
        thread = await session_service.get_message_thread(session_id, "msg-2", depth=2)

        # Assert
        assert thread is not None
        assert thread["target"].uuid == "msg-2"
        assert len(thread["ancestors"]) == 2  # Should get msg-1 and root
        assert thread["ancestors"][0].uuid == "root"
        assert thread["ancestors"][1].uuid == "msg-1"
        # Note: descendants testing is limited by mock complexity

    @pytest.mark.asyncio
    async def test_get_session_with_missing_optional_fields(
        self, session_service, mock_db
    ):
        """Test getting session when optional fields are missing."""
        # Setup - minimal session data
        session_data = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "sessionId": "session-123",
            "projectId": ObjectId("507f1f77bcf86cd799439012"),
            "startedAt": datetime.now(UTC),
            # Missing: summary, endedAt, messageCount, totalCost, etc.
        }

        mock_db.sessions.find_one = AsyncMock(return_value=session_data)
        mock_db.messages.distinct = AsyncMock(return_value=[])
        mock_db.messages.find_one = AsyncMock(return_value=None)

        # Execute
        session = await session_service.get_session("507f1f77bcf86cd799439011")

        # Assert
        assert session is not None
        assert session.session_id == "session-123"
        assert session.summary is None
        assert session.ended_at is None
        assert session.message_count == 0
        assert session.total_cost is None
        assert session.tools_used == 0
        assert session.total_tokens == 0

    @pytest.mark.asyncio
    async def test_list_sessions_sort_order_directions(self, session_service, mock_db):
        """Test both ascending and descending sort orders."""
        # Setup
        mock_db.sessions.count_documents = AsyncMock(return_value=0)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter([])
        )
        mock_db.sessions.find.return_value = mock_cursor

        # Test ascending
        await session_service.list_sessions({}, 0, 10, "message_count", "asc")
        mock_cursor.sort.assert_called_with("messageCount", 1)

        # Test descending
        await session_service.list_sessions({}, 0, 10, "message_count", "desc")
        mock_cursor.sort.assert_called_with("messageCount", -1)

        # Test default (not desc) should be ascending
        await session_service.list_sessions({}, 0, 10, "message_count", "random")
        mock_cursor.sort.assert_called_with("messageCount", 1)

    @pytest.mark.asyncio
    async def test_generate_summary_with_special_characters(
        self, session_service, mock_db
    ):
        """Test generating summary with special characters and edge cases."""
        # Setup
        session_id = "507f1f77bcf86cd799439011"
        mock_db.sessions.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(session_id),
                "sessionId": "session-123",
            }
        )

        # Test with special characters and emojis
        messages = [
            {
                "type": "user",
                "content": "How can I handle 🚀 emojis and <special> characters & symbols?",
                "timestamp": datetime.now(UTC),
            },
        ]

        mock_db.messages.find.return_value.sort.return_value.to_list = AsyncMock(
            return_value=messages
        )
        mock_db.sessions.update_one = AsyncMock()

        # Execute
        summary = await session_service.generate_summary(session_id)

        # Assert
        assert (
            summary == "How can I handle 🚀 emojis and <special> characters & symbols?"
        )
        assert "```" not in summary

    @pytest.mark.asyncio
    async def test_get_session_messages_with_nested_message_content(
        self, session_service, mock_db
    ):
        """Test extracting content from nested message structure."""
        # Setup
        session_data = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "sessionId": "session-123",
        }
        mock_db.sessions.find_one = AsyncMock(return_value=session_data)

        # Messages with different content structures
        message_data = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439013"),
                "uuid": "msg-1",
                "type": "user",
                "sessionId": "session-123",
                "message": {"content": "Content from message.content", "extra": "data"},
                "timestamp": datetime.now(UTC),
                "createdAt": datetime.now(UTC),
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439014"),
                "uuid": "msg-2",
                "type": "assistant",
                "sessionId": "session-123",
                "content": "Direct content",
                "message": {"content": "Should use direct content, not this"},
                "timestamp": datetime.now(UTC),
                "createdAt": datetime.now(UTC),
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439015"),
                "uuid": "msg-3",
                "type": "assistant",
                "sessionId": "session-123",
                # No content at all
                "timestamp": datetime.now(UTC),
                "createdAt": datetime.now(UTC),
            },
        ]

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter(message_data)
        )
        mock_db.messages.find.return_value = mock_cursor

        # Execute
        messages = await session_service.get_session_messages(
            "507f1f77bcf86cd799439011", skip=0, limit=10
        )

        # Assert
        assert len(messages) == 3
        assert messages[0].content == "Content from message.content"
        assert messages[1].content == "Direct content"
        assert messages[2].content is None

    @pytest.mark.asyncio
    async def test_generate_summary_updates_session(self, session_service, mock_db):
        """Test that generate_summary properly updates the session in the database."""
        # Setup
        session_id = "507f1f77bcf86cd799439011"
        mock_db.sessions.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(session_id),
                "sessionId": "session-123",
            }
        )

        messages = [
            {
                "type": "user",
                "content": "Update the login form",
                "timestamp": datetime.now(UTC),
            },
        ]

        mock_db.messages.find.return_value.sort.return_value.to_list = AsyncMock(
            return_value=messages
        )
        mock_db.sessions.update_one = AsyncMock()

        # Execute
        summary = await session_service.generate_summary(session_id)

        # Assert summary was generated correctly
        assert summary == "Update the login form"

        # Assert session was updated with summary and updatedAt
        mock_db.sessions.update_one.assert_called_once()
        update_call = mock_db.sessions.update_one.call_args
        assert update_call[0][0] == {"_id": ObjectId(session_id)}
        assert "$set" in update_call[0][1]
        assert update_call[0][1]["$set"]["summary"] == summary
        assert "updatedAt" in update_call[0][1]["$set"]
        assert isinstance(update_call[0][1]["$set"]["updatedAt"], datetime)

    @pytest.mark.asyncio
    async def test_session_cleanup_on_project_deletion(self, session_service, mock_db):
        """Test that sessions can be properly cleaned up when a project is deleted."""
        # This test simulates the cleanup that happens in project service
        project_id = ObjectId("507f1f77bcf86cd799439012")

        # Setup sessions for the project
        sessions_data = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "sessionId": "session-1",
                "projectId": project_id,
                "summary": "Session 1",
                "startedAt": datetime.now(UTC),
                "messageCount": 5,
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439013"),
                "sessionId": "session-2",
                "projectId": project_id,
                "summary": "Session 2",
                "startedAt": datetime.now(UTC),
                "messageCount": 3,
            },
        ]

        # First verify sessions exist
        mock_db.sessions.count_documents = AsyncMock(return_value=2)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter(sessions_data)
        )
        mock_db.sessions.find.return_value = mock_cursor

        sessions, total = await session_service.list_sessions(
            {"projectId": project_id}, 0, 10, "started_at", "desc"
        )
        assert total == 2
        assert len(sessions) == 2

        # Simulate project deletion cleanup
        mock_db.sessions.delete_many = AsyncMock(
            return_value=MagicMock(deleted_count=2)
        )
        result = await mock_db.sessions.delete_many({"projectId": project_id})

        # Verify deletion was called correctly
        mock_db.sessions.delete_many.assert_called_once_with({"projectId": project_id})
        assert result.deleted_count == 2

    @pytest.mark.asyncio
    async def test_get_session_handles_concurrent_updates(
        self, session_service, mock_db
    ):
        """Test that get_session handles sessions that might be updated concurrently."""
        # Setup - session with cost being updated
        session_id = "507f1f77bcf86cd799439011"

        # Initial state
        initial_session = {
            "_id": ObjectId(session_id),
            "sessionId": "session-123",
            "projectId": ObjectId("507f1f77bcf86cd799439012"),
            "summary": "Session being updated",
            "startedAt": datetime.now(UTC),
            "messageCount": 5,
            "totalCost": Decimal128("0.10"),
        }

        # Updated state (simulating concurrent update)
        updated_session = initial_session.copy()
        updated_session["totalCost"] = Decimal128("0.15")
        updated_session["messageCount"] = 6

        # First call returns initial, second call returns updated
        mock_db.sessions.find_one = AsyncMock(
            side_effect=[initial_session, updated_session]
        )
        mock_db.messages.distinct = AsyncMock(return_value=["gpt-4"])
        mock_db.messages.find_one = AsyncMock(return_value=None)

        # Get session twice
        session1 = await session_service.get_session(session_id)
        session2 = await session_service.get_session(session_id)

        # Assert values changed between calls
        assert session1.total_cost == 0.10
        assert session1.message_count == 5
        assert session2.total_cost == 0.15
        assert session2.message_count == 6

    @pytest.mark.asyncio
    async def test_list_sessions_handles_empty_fields_gracefully(
        self, session_service, mock_db
    ):
        """Test that list_sessions handles sessions with empty or missing fields gracefully."""
        # Setup - sessions with various missing/empty fields
        sessions_data = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "sessionId": "session-1",
                "projectId": ObjectId("507f1f77bcf86cd799439012"),
                "startedAt": datetime.now(UTC),
                # Missing: summary, endedAt, messageCount, totalCost, etc.
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439013"),
                "sessionId": "session-2",
                "projectId": ObjectId("507f1f77bcf86cd799439012"),
                "summary": "",  # Empty summary
                "startedAt": datetime.now(UTC),
                "messageCount": 0,
                "totalCost": None,  # Null cost
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439014"),
                "sessionId": "session-3",
                "projectId": ObjectId("507f1f77bcf86cd799439012"),
                "summary": None,  # Null summary
                "startedAt": datetime.now(UTC),
                "endedAt": None,  # Null end time
                "totalCost": Decimal128("0"),  # Zero cost
            },
        ]

        mock_db.sessions.count_documents = AsyncMock(return_value=3)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter(sessions_data)
        )
        mock_db.sessions.find.return_value = mock_cursor

        # Execute
        sessions, total = await session_service.list_sessions(
            {}, 0, 10, "started_at", "desc"
        )

        # Assert all sessions were processed successfully
        assert total == 3
        assert len(sessions) == 3

        # Check default values were applied
        assert sessions[0].summary is None
        assert sessions[0].message_count == 0
        assert sessions[0].total_cost is None

        assert sessions[1].summary == ""
        assert sessions[1].message_count == 0
        assert sessions[1].total_cost is None

        assert sessions[2].summary is None
        assert sessions[2].ended_at is None
        assert sessions[2].total_cost == 0.0

    @pytest.mark.asyncio
    async def test_get_message_thread_orphaned_messages(self, session_service, mock_db):
        """Test get_message_thread handles orphaned messages (missing parents)."""
        # Setup
        session_id = "507f1f77bcf86cd799439011"
        mock_db.sessions.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(session_id),
                "sessionId": "session-123",
            }
        )

        # Target message with parent that doesn't exist
        target_msg = {
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "uuid": "orphaned-msg",
            "type": "user",
            "sessionId": "session-123",
            "content": "Orphaned message",
            "timestamp": datetime.now(UTC),
            "createdAt": datetime.now(UTC),
            "parentUuid": "non-existent-parent",
        }

        # Mock find_one to return target but no parent
        async def mock_find_one(query):
            if query.get("uuid") == "orphaned-msg":
                return target_msg
            return None  # Parent doesn't exist

        mock_db.messages.find_one = AsyncMock(side_effect=mock_find_one)
        mock_db.messages.find.return_value.sort.return_value.__aiter__ = (
            lambda self: async_iter([])
        )

        # Execute
        thread = await session_service.get_message_thread(
            session_id, "orphaned-msg", depth=5
        )

        # Assert thread was still created successfully
        assert thread is not None
        assert thread["target"].uuid == "orphaned-msg"
        assert len(thread["ancestors"]) == 0  # No ancestors found
        assert len(thread["descendants"]) == 0
