"""Tests for the debug version of ingestion service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from bson import Decimal128, ObjectId

from app.schemas.ingest import IngestStats, MessageIngest
from app.services.ingest_debug import IngestServiceDebug


class TestIngestServiceDebugInit:
    """Test IngestServiceDebug initialization."""

    def test_service_initialization(self):
        """Test service initializes with proper attributes."""
        db = Mock()
        service = IngestServiceDebug(db)

        assert service.db == db
        assert isinstance(service._project_cache, dict)
        assert isinstance(service._session_cache, dict)
        assert len(service._project_cache) == 0
        assert len(service._session_cache) == 0


class TestIngestServiceDebugMessageProcessing:
    """Test message processing functionality."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        db = Mock()
        return IngestServiceDebug(db)

    @pytest.fixture
    def sample_message(self):
        """Create sample message."""
        return MessageIngest(
            uuid="test-uuid-123",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="test-session",
            message={"content": "Hello test"},
            cwd="/test/project",
        )

    def test_hash_message_consistency(self, service, sample_message):
        """Test message hashing produces consistent results."""
        hash1 = service._hash_message(sample_message)
        hash2 = service._hash_message(sample_message)

        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hex digest

    def test_hash_message_different_for_different_messages(self, service):
        """Test different messages produce different hashes."""
        msg1 = MessageIngest(
            uuid="uuid-1",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="session-1",
            message={"content": "Message 1"},
        )
        msg2 = MessageIngest(
            uuid="uuid-2",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="session-1",
            message={"content": "Message 2"},
        )

        hash1 = service._hash_message(msg1)
        hash2 = service._hash_message(msg2)

        assert hash1 != hash2


class TestIngestServiceDebugMessageToDoc:
    """Test message to document conversion."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        db = Mock()
        return IngestServiceDebug(db)

    def test_message_to_doc_basic_user_message(self, service):
        """Test conversion of basic user message."""
        message = MessageIngest(
            uuid="test-uuid",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="test-session",
            message={"content": "Hello world"},
            cwd="/test/path",
        )

        doc = service._message_to_doc(message, "test-session")

        assert doc["uuid"] == "test-uuid"
        assert doc["sessionId"] == "test-session"
        assert doc["type"] == "user"
        assert doc["content"] == "Hello world"
        assert doc["cwd"] == "/test/path"
        assert "contentHash" in doc
        assert "createdAt" in doc
        assert isinstance(doc["_id"], ObjectId)

    def test_message_to_doc_assistant_message_with_thinking(self, service):
        """Test conversion of assistant message with thinking."""
        message = MessageIngest(
            uuid="asst-uuid",
            type="assistant",
            timestamp=datetime.now(UTC),
            sessionId="test-session",
            message={
                "content": [
                    {"type": "thinking", "thinking": "Let me think about this"},
                    {"type": "text", "text": "Here's my response"},
                    {"type": "tool_use", "name": "search", "input": {}},
                ]
            },
        )

        doc = service._message_to_doc(message, "test-session")

        assert doc["type"] == "assistant"
        assert "thinking" in doc
        assert doc["thinking"] == "Let me think about this"
        assert "[Thinking]" in doc["content"]
        assert "Here's my response" in doc["content"]
        assert "[Using tool: search]" in doc["content"]

    def test_message_to_doc_user_message_with_tool_result(self, service):
        """Test conversion of user message with tool result."""
        message = MessageIngest(
            uuid="user-uuid",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="test-session",
            message={
                "content": [
                    {"type": "text", "text": "Here's the command"},
                    {"type": "tool_result", "content": "Command output"},
                ]
            },
        )

        doc = service._message_to_doc(message, "test-session")

        assert "Here's the command" in doc["content"]
        assert "[Tool Result: Command output]" in doc["content"]

    def test_message_to_doc_summary_message(self, service):
        """Test conversion of summary message."""
        message = MessageIngest(
            uuid="summary-uuid",
            type="summary",
            timestamp=datetime.now(UTC),
            sessionId="test-session",
            message={"summary": "Session summary content"},
        )

        doc = service._message_to_doc(message, "test-session")

        assert doc["type"] == "summary"
        assert doc["content"] == "Session summary content"

    def test_message_to_doc_with_optional_fields(self, service):
        """Test conversion with optional fields."""
        message = MessageIngest(
            uuid="test-uuid",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="test-session",
            message={"content": "Test"},
            costUsd=0.05,
            model="claude-3-sonnet",
            durationMs=1500,
            gitBranch="feature/test",
        )

        doc = service._message_to_doc(message, "test-session")

        assert isinstance(doc["costUsd"], Decimal128)
        assert doc["model"] == "claude-3-sonnet"
        assert doc["durationMs"] == 1500
        assert doc["gitBranch"] == "feature/test"

    def test_message_to_doc_string_message(self, service):
        """Test conversion when message is a string."""
        message = MessageIngest(
            uuid="test-uuid",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="test-session",
            message={"content": "Simple string message"},
        )

        doc = service._message_to_doc(message, "test-session")

        assert doc["content"] == "Simple string message"


class TestIngestServiceDebugSessionManagement:
    """Test session management functionality."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        db = Mock()
        return IngestServiceDebug(db)

    @pytest.fixture
    def sample_message(self):
        """Create sample message."""
        return MessageIngest(
            uuid="test-uuid",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="test-session",
            message={"content": "Test"},
            cwd="/test/project",
        )

    @pytest.mark.asyncio
    async def test_ensure_session_cached(self, service, sample_message):
        """Test session retrieval from cache."""
        session_id = "cached-session"
        service._session_cache[session_id] = ObjectId()

        result = await service._ensure_session(session_id, sample_message)

        assert result is None

    @pytest.mark.asyncio
    async def test_ensure_session_from_database(self, service, sample_message):
        """Test session retrieval from database."""
        session_id = "db-session"
        existing_session = {"_id": ObjectId(), "sessionId": session_id}

        service.db.sessions.find_one = AsyncMock(return_value=existing_session)

        result = await service._ensure_session(session_id, sample_message)

        assert result is None
        assert session_id in service._session_cache
        assert service._session_cache[session_id] == existing_session["_id"]

    @pytest.mark.asyncio
    async def test_ensure_session_create_new(self, service, sample_message):
        """Test creating new session."""
        session_id = "new-session"
        project_id = ObjectId()

        service.db.sessions.find_one = AsyncMock(return_value=None)
        service.db.sessions.insert_one = AsyncMock()
        service._ensure_project = AsyncMock(return_value=project_id)

        result = await service._ensure_session(session_id, sample_message)

        assert isinstance(result, ObjectId)
        assert session_id in service._session_cache
        service.db.sessions.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_project_cached(self, service):
        """Test project retrieval from cache."""
        project_path = "/cached/project"
        project_id = ObjectId()
        service._project_cache[project_path] = project_id

        result = await service._ensure_project(project_path, "Test Project")

        assert result == project_id

    @pytest.mark.asyncio
    async def test_ensure_project_from_database(self, service):
        """Test project retrieval from database."""
        project_path = "/db/project"
        project_id = ObjectId()
        existing_project = {"_id": project_id, "path": project_path}

        service.db.projects.find_one = AsyncMock(return_value=existing_project)

        result = await service._ensure_project(project_path, "DB Project")

        assert result == project_id
        assert project_path in service._project_cache

    @pytest.mark.asyncio
    async def test_ensure_project_create_new(self, service):
        """Test creating new project."""
        project_path = "/new/project"
        project_name = "New Project"

        service.db.projects.find_one = AsyncMock(return_value=None)
        service.db.projects.insert_one = AsyncMock()

        result = await service._ensure_project(project_path, project_name)

        assert isinstance(result, ObjectId)
        assert project_path in service._project_cache
        service.db.projects.insert_one.assert_called_once()


class TestIngestServiceDebugGetExistingHashes:
    """Test getting existing message hashes."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        db = Mock()
        return IngestServiceDebug(db)

    @pytest.mark.asyncio
    async def test_get_existing_hashes_empty(self, service):
        """Test getting hashes when no messages exist."""

        async def mock_cursor():
            return
            yield  # Make this an async generator

        service.db.messages.find = Mock(return_value=mock_cursor())

        result = await service._get_existing_hashes("test-session")

        assert result == set()

    @pytest.mark.asyncio
    async def test_get_existing_hashes_with_data(self, service):
        """Test getting hashes with existing messages."""
        mock_docs = [
            {"contentHash": "hash1"},
            {"contentHash": "hash2"},
            {"_id": ObjectId()},  # Doc without hash
        ]

        async def mock_cursor():
            for doc in mock_docs:
                yield doc

        service.db.messages.find = Mock(return_value=mock_cursor())

        result = await service._get_existing_hashes("test-session")

        assert result == {"hash1", "hash2"}


class TestIngestServiceDebugUpdateSessionStats:
    """Test session statistics updates."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        db = Mock()
        return IngestServiceDebug(db)

    @pytest.mark.asyncio
    async def test_update_session_stats_success(self, service):
        """Test successful session stats update."""
        session_id = "test-session"
        mock_stats = [
            {
                "_id": None,
                "messageCount": 5,
                "totalCost": 0.25,
                "startTime": datetime.now(UTC),
                "endTime": datetime.now(UTC),
            }
        ]

        service.db.messages.aggregate = Mock()
        service.db.messages.aggregate.return_value.to_list = AsyncMock(
            return_value=mock_stats
        )
        service.db.sessions.update_one = AsyncMock()

        await service._update_session_stats(session_id)

        service.db.sessions.update_one.assert_called_once()
        update_call = service.db.sessions.update_one.call_args
        assert update_call[0][0] == {"sessionId": session_id}
        assert "messageCount" in update_call[0][1]["$set"]

    @pytest.mark.asyncio
    async def test_update_session_stats_no_results(self, service):
        """Test session stats update with no aggregation results."""
        session_id = "empty-session"

        service.db.messages.aggregate = Mock()
        service.db.messages.aggregate.return_value.to_list = AsyncMock(return_value=[])
        service.db.sessions.update_one = AsyncMock()

        await service._update_session_stats(session_id)

        service.db.sessions.update_one.assert_not_called()


class TestIngestServiceDebugLogIngestion:
    """Test ingestion logging."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        db = Mock()
        return IngestServiceDebug(db)

    @pytest.mark.asyncio
    async def test_log_ingestion(self, service):
        """Test ingestion logging."""
        stats = IngestStats(
            messages_received=10,
            messages_processed=8,
            messages_skipped=1,
            messages_updated=0,
            messages_failed=1,
            sessions_created=1,
            sessions_updated=0,
            todos_processed=0,
            config_updated=False,
            duration_ms=1500,
        )

        service.db.ingestion_logs.insert_one = AsyncMock()

        await service._log_ingestion(stats)

        service.db.ingestion_logs.insert_one.assert_called_once()
        log_call = service.db.ingestion_logs.insert_one.call_args[0][0]
        assert log_call["messages_processed"] == 8
        assert log_call["messages_skipped"] == 1
        assert log_call["messages_failed"] == 1
        assert log_call["duration_ms"] == 1500


class TestIngestServiceDebugProcessSessionMessages:
    """Test session message processing."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        db = Mock()
        service = IngestServiceDebug(db)
        service._ensure_session = AsyncMock()
        service._get_existing_hashes = AsyncMock(return_value=set())
        service._update_session_stats = AsyncMock()
        return service

    @pytest.fixture
    def sample_messages(self):
        """Create sample messages."""
        return [
            MessageIngest(
                uuid="msg-1",
                type="user",
                timestamp=datetime.now(UTC),
                sessionId="test-session",
                message={"content": "Message 1"},
            ),
            MessageIngest(
                uuid="msg-2",
                type="assistant",
                timestamp=datetime.now(UTC),
                sessionId="test-session",
                message={"content": [{"type": "text", "text": "Response 1"}]},
            ),
        ]

    @pytest.mark.asyncio
    async def test_process_session_messages_new_session(self, service, sample_messages):
        """Test processing messages for new session."""
        session_id = "new-session"
        stats = IngestStats()

        service._ensure_session.return_value = ObjectId()
        service.db.messages.insert_many = AsyncMock()
        service.db.messages.insert_many.return_value.inserted_ids = [
            ObjectId(),
            ObjectId(),
        ]

        await service._process_session_messages(session_id, sample_messages, stats)

        assert stats.sessions_created == 1
        assert stats.sessions_updated == 0
        service.db.messages.insert_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_session_messages_existing_session(
        self, service, sample_messages
    ):
        """Test processing messages for existing session."""
        session_id = "existing-session"
        stats = IngestStats()

        service._ensure_session.return_value = None
        service.db.messages.insert_many = AsyncMock()
        service.db.messages.insert_many.return_value.inserted_ids = [
            ObjectId(),
            ObjectId(),
        ]

        await service._process_session_messages(session_id, sample_messages, stats)

        assert stats.sessions_created == 0
        assert stats.sessions_updated == 1

    @pytest.mark.asyncio
    async def test_process_session_messages_with_duplicates(
        self, service, sample_messages
    ):
        """Test processing messages with duplicate detection."""
        session_id = "test-session"
        stats = IngestStats()

        # Mock duplicate hash for first message
        duplicate_hash = service._hash_message(sample_messages[0])
        service._get_existing_hashes.return_value = {duplicate_hash}
        service._ensure_session.return_value = None
        service.db.messages.insert_many = AsyncMock()
        service.db.messages.insert_many.return_value.inserted_ids = [ObjectId()]

        await service._process_session_messages(session_id, sample_messages, stats)

        assert stats.messages_skipped == 1
        service.db.messages.insert_many.assert_called_once()
        # Should only insert one message (second one, first was duplicate)
        assert len(service.db.messages.insert_many.call_args[0][0]) == 1

    @pytest.mark.asyncio
    async def test_process_session_messages_insert_failure(
        self, service, sample_messages
    ):
        """Test handling of MongoDB insert failure."""
        session_id = "test-session"
        stats = IngestStats()

        service._ensure_session.return_value = None
        service.db.messages.insert_many = AsyncMock(
            side_effect=Exception("Insert failed")
        )

        await service._process_session_messages(session_id, sample_messages, stats)

        assert stats.messages_failed == len(sample_messages)
        assert stats.messages_processed == 0


class TestIngestServiceDebugIngestMessages:
    """Test main ingest_messages method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        db = Mock()
        return IngestServiceDebug(db)

    @pytest.fixture
    def sample_messages(self):
        """Create sample messages for different sessions."""
        return [
            MessageIngest(
                uuid="msg-1",
                type="user",
                timestamp=datetime.now(UTC),
                sessionId="session-1",
                message={"content": "Message 1"},
            ),
            MessageIngest(
                uuid="msg-2",
                type="user",
                timestamp=datetime.now(UTC),
                sessionId="session-1",
                message={"content": "Message 2"},
            ),
            MessageIngest(
                uuid="msg-3",
                type="user",
                timestamp=datetime.now(UTC),
                sessionId="session-2",
                message={"content": "Message 3"},
            ),
        ]

    @pytest.mark.asyncio
    async def test_ingest_messages_success(self, service, sample_messages):
        """Test successful message ingestion."""
        service._process_session_messages = AsyncMock()
        service._log_ingestion = AsyncMock()

        result = await service.ingest_messages(sample_messages)

        assert isinstance(result, IngestStats)
        assert result.messages_received == 3
        assert result.duration_ms >= 0  # Can be 0 if very fast

        # Should process 2 sessions
        assert service._process_session_messages.call_count == 2
        service._log_ingestion.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_messages_empty_list(self, service):
        """Test ingesting empty message list."""
        service._log_ingestion = AsyncMock()

        result = await service.ingest_messages([])

        assert result.messages_received == 0
        assert result.messages_processed == 0
        service._log_ingestion.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_messages_task_exception(self, service, sample_messages):
        """Test handling of task exceptions during processing."""
        service._process_session_messages = AsyncMock(
            side_effect=Exception("Processing failed")
        )
        service._log_ingestion = AsyncMock()

        # Should not raise exception, should handle gracefully
        result = await service.ingest_messages(sample_messages)

        assert isinstance(result, IngestStats)
        service._log_ingestion.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_messages_fatal_error(self, service, sample_messages):
        """Test handling of fatal errors in ingest_messages."""
        service._process_session_messages = AsyncMock()
        service._log_ingestion = AsyncMock(side_effect=Exception("Fatal error"))

        with pytest.raises(Exception, match="Fatal error"):
            await service.ingest_messages(sample_messages)


class TestIngestServiceDebugProjectExtraction:
    """Test project information extraction."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        db = Mock()
        return IngestServiceDebug(db)

    @pytest.mark.asyncio
    async def test_project_name_extraction_from_path(self, service):
        """Test extracting project name from path."""
        message = MessageIngest(
            uuid="test-uuid",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="test-session",
            message={"content": "Test"},
            cwd="/Users/test/projects/my-awesome-project",
        )

        service.db.projects.find_one = AsyncMock(return_value=None)
        service.db.projects.insert_one = AsyncMock()

        await service._ensure_project(message.cwd, "")

        # Check that project was created with extracted name
        insert_call = service.db.projects.insert_one.call_args[0][0]
        assert insert_call["path"] == "/Users/test/projects/my-awesome-project"

    @pytest.mark.asyncio
    async def test_project_handling_empty_path(self, service):
        """Test project handling with empty/None path."""
        service.db.projects.find_one = AsyncMock(return_value=None)
        service.db.projects.insert_one = AsyncMock()

        result = await service._ensure_project("", "Empty Project")

        assert isinstance(result, ObjectId)
        service.db.projects.insert_one.assert_called_once()


class TestIngestServiceDebugEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        db = Mock()
        return IngestServiceDebug(db)

    def test_hash_message_with_complex_content(self, service):
        """Test hashing message with complex nested content."""
        message = MessageIngest(
            uuid="complex-uuid",
            type="assistant",
            timestamp=datetime.now(UTC),
            sessionId="test-session",
            message={
                "content": [
                    {"type": "thinking", "thinking": "Complex thinking"},
                    {"type": "text", "text": "Complex response"},
                    {
                        "type": "tool_use",
                        "name": "complex_tool",
                        "input": {"nested": {"data": "value"}},
                    },
                ]
            },
        )

        hash_result = service._hash_message(message)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 64

    def test_message_to_doc_with_empty_content(self, service):
        """Test message conversion when message has empty content."""
        message = MessageIngest(
            uuid="empty-msg",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="test-session",
            message={"content": ""},
        )

        doc = service._message_to_doc(message, "test-session")

        assert doc["content"] == ""
        assert doc["uuid"] == "empty-msg"

    @pytest.mark.asyncio
    async def test_ensure_session_create_failure(self, service):
        """Test session creation failure."""
        message = MessageIngest(
            uuid="test-uuid",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="fail-session",
            message={"content": "Test"},
            cwd="/test/path",
        )

        service.db.sessions.find_one = AsyncMock(return_value=None)
        service.db.sessions.insert_one = AsyncMock(
            side_effect=Exception("Insert failed")
        )
        service._ensure_project = AsyncMock(return_value=ObjectId())

        with pytest.raises(Exception, match="Insert failed"):
            await service._ensure_session("fail-session", message)

    @pytest.mark.asyncio
    async def test_ensure_project_create_failure(self, service):
        """Test project creation failure."""
        service.db.projects.find_one = AsyncMock(return_value=None)
        service.db.projects.insert_one = AsyncMock(
            side_effect=Exception("Project insert failed")
        )

        with pytest.raises(Exception, match="Project insert failed"):
            await service._ensure_project("/fail/path", "Fail Project")
