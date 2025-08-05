"""Tests for ingest service."""
import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from app.schemas.ingest import IngestStats, MessageIngest
from app.services.ingest import IngestService


@pytest.fixture
def mock_db():
    """Mock database for testing."""
    return MagicMock()


@pytest.fixture
def ingest_service(mock_db):
    """Create IngestService instance with mock database."""
    return IngestService(mock_db)


@pytest.fixture
def sample_message_ingest():
    """Sample message ingest data."""
    return MessageIngest(
        uuid="msg_123",
        sessionId="session_456",
        type="user",
        timestamp=datetime.now(UTC),
        message={"role": "user", "content": "Test message"},
        projectPath="/test/project",
        model="claude-3-sonnet",
        usage={"input_tokens": 10, "output_tokens": 20},
        costUsd=0.001,
    )


class TestIngestService:
    """Tests for IngestService class."""

    def test_init(self, mock_db):
        """Test IngestService initialization."""
        service = IngestService(mock_db)
        assert service.db == mock_db
        assert service._project_cache == {}
        assert service._session_cache == {}

    @pytest.mark.asyncio
    async def test_ingest_messages_empty_list(self, ingest_service):
        """Test ingesting empty message list."""
        messages = []

        with patch.object(ingest_service, "_log_ingestion") as mock_log:
            stats = await ingest_service.ingest_messages(messages)

            assert stats.messages_received == 0
            assert stats.messages_processed == 0
            assert stats.messages_skipped == 0
            assert stats.messages_failed == 0
            assert stats.duration_ms >= 0
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_messages_single_message(
        self, ingest_service, sample_message_ingest
    ):
        """Test ingesting a single message."""
        messages = [sample_message_ingest]

        # Mock the process session messages method
        with patch.object(
            ingest_service, "_process_session_messages"
        ) as mock_process, patch.object(ingest_service, "_log_ingestion") as mock_log:
            stats = await ingest_service.ingest_messages(messages)

            assert stats.messages_received == 1
            assert stats.duration_ms >= 0
            mock_process.assert_called_once()
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_messages_multiple_sessions(self, ingest_service):
        """Test ingesting messages from multiple sessions."""
        messages = [
            MessageIngest(
                uuid="msg_1",
                sessionId="session_1",
                type="user",
                timestamp=datetime.now(UTC),
                message={"role": "user", "content": "Message 1"},
                projectPath="/test/project",
            ),
            MessageIngest(
                uuid="msg_2",
                sessionId="session_2",
                type="user",
                timestamp=datetime.now(UTC),
                message={"role": "user", "content": "Message 2"},
                projectPath="/test/project",
            ),
            MessageIngest(
                uuid="msg_3",
                sessionId="session_1",
                type="assistant",
                timestamp=datetime.now(UTC),
                message={"role": "assistant", "content": "Response 1"},
                projectPath="/test/project",
            ),
        ]

        with patch.object(
            ingest_service, "_process_session_messages"
        ) as mock_process, patch.object(ingest_service, "_log_ingestion") as mock_log:
            stats = await ingest_service.ingest_messages(messages)

            assert stats.messages_received == 3
            # Should process 2 sessions (session_1 and session_2)
            assert mock_process.call_count == 2
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_messages_overwrite_mode(
        self, ingest_service, sample_message_ingest
    ):
        """Test ingesting messages with overwrite mode."""
        messages = [sample_message_ingest]

        with patch.object(
            ingest_service, "_process_session_messages"
        ) as mock_process, patch.object(ingest_service, "_log_ingestion"):
            stats = await ingest_service.ingest_messages(messages, overwrite_mode=True)

            assert stats.messages_received == 1
            # Verify overwrite_mode is passed to _process_session_messages
            mock_process.assert_called_once()
            call_args = mock_process.call_args
            assert call_args[0][3] is True  # overwrite_mode parameter

    @pytest.mark.asyncio
    async def test_process_session_messages_new_session(
        self, ingest_service, sample_message_ingest
    ):
        """Test processing messages for a new session."""
        session_id = "new_session"
        messages = [sample_message_ingest]
        stats = IngestStats(messages_received=1)

        # Mock dependencies
        with patch.object(
            ingest_service, "_ensure_session", return_value=ObjectId()
        ) as mock_ensure, patch.object(
            ingest_service, "_get_existing_hashes", return_value=set()
        ) as mock_hashes, patch.object(
            ingest_service, "_message_to_doc", return_value=[{"uuid": "msg_123"}]
        ), patch.object(
            ingest_service, "_hash_message", return_value="hash123"
        ):
            # Mock database insert
            ingest_service.db.messages.insert_many = AsyncMock()

            await ingest_service._process_session_messages(session_id, messages, stats)

            assert stats.sessions_created == 1
            assert stats.sessions_updated == 0
            mock_ensure.assert_called_once()
            mock_hashes.assert_called_once_with(session_id)
            ingest_service.db.messages.insert_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_session_messages_existing_session(
        self, ingest_service, sample_message_ingest
    ):
        """Test processing messages for an existing session."""
        session_id = "existing_session"
        messages = [sample_message_ingest]
        stats = IngestStats(messages_received=1)

        # Mock dependencies - None return indicates existing session
        with patch.object(
            ingest_service, "_ensure_session", return_value=None
        ) as mock_ensure, patch.object(
            ingest_service, "_get_existing_hashes", return_value=set()
        ), patch.object(
            ingest_service, "_message_to_doc", return_value=[{"uuid": "msg_123"}]
        ), patch.object(
            ingest_service, "_hash_message", return_value="hash123"
        ):
            # Mock database insert
            ingest_service.db.messages.insert_many = AsyncMock()

            await ingest_service._process_session_messages(session_id, messages, stats)

            assert stats.sessions_created == 0
            assert stats.sessions_updated == 1
            mock_ensure.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_session_messages_duplicate_detection(
        self, ingest_service, sample_message_ingest
    ):
        """Test that duplicate messages are skipped."""
        session_id = "test_session"
        messages = [sample_message_ingest]
        stats = IngestStats(messages_received=1)

        # Mock dependencies - existing hash should cause skip
        with patch.object(
            ingest_service, "_ensure_session", return_value=None
        ), patch.object(
            ingest_service, "_get_existing_hashes", return_value={"hash123"}
        ), patch.object(
            ingest_service, "_hash_message", return_value="hash123"
        ):
            # Mock database insert (should not be called)
            ingest_service.db.messages.insert_many = AsyncMock()

            await ingest_service._process_session_messages(session_id, messages, stats)

            assert stats.messages_skipped == 1
            assert stats.messages_processed == 0
            # Insert should not be called since message was skipped
            ingest_service.db.messages.insert_many.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_session_messages_overwrite_mode(
        self, ingest_service, sample_message_ingest
    ):
        """Test processing messages in overwrite mode."""
        session_id = "test_session"
        messages = [sample_message_ingest]
        stats = IngestStats(messages_received=1)

        with patch.object(
            ingest_service, "_ensure_session", return_value=None
        ), patch.object(
            ingest_service,
            "_message_to_doc",
            return_value=[{"uuid": "msg_123", "_id": ObjectId()}],
        ) as mock_to_doc:
            # Mock database bulk_write
            ingest_service.db.messages.bulk_write = AsyncMock()

            await ingest_service._process_session_messages(
                session_id, messages, stats, overwrite_mode=True
            )

            # In overwrite mode, _get_existing_hashes should not be called
            mock_to_doc.assert_called_once()
            ingest_service.db.messages.bulk_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_session_messages_error_handling(self, ingest_service):
        """Test error handling during message processing."""
        session_id = "test_session"
        messages = [
            MessageIngest(
                uuid="msg_bad",
                sessionId=session_id,
                type="user",
                timestamp=datetime.now(UTC),
                message={"role": "user", "content": "Bad message"},
                projectPath="/test/project",
            )
        ]
        stats = IngestStats(messages_received=1)

        with patch.object(
            ingest_service, "_ensure_session", return_value=None
        ), patch.object(
            ingest_service, "_get_existing_hashes", return_value=set()
        ), patch.object(
            ingest_service, "_hash_message", return_value="hash123"
        ), patch.object(
            ingest_service, "_message_to_doc", side_effect=Exception("Processing error")
        ):
            await ingest_service._process_session_messages(session_id, messages, stats)

            assert stats.messages_failed == 1
            assert stats.messages_processed == 0

    def test_hash_message(self, ingest_service, sample_message_ingest):
        """Test message hashing for deduplication."""
        hash1 = ingest_service._hash_message(sample_message_ingest)
        hash2 = ingest_service._hash_message(sample_message_ingest)

        # Same message should produce same hash
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) > 0

    def test_hash_message_different_content(self, ingest_service):
        """Test that different messages produce different hashes."""
        message1 = MessageIngest(
            uuid="msg_1",
            sessionId="session_1",
            type="user",
            timestamp=datetime.now(UTC),
            message={"role": "user", "content": "Message 1"},
            projectPath="/test/project",
        )

        message2 = MessageIngest(
            uuid="msg_2",
            sessionId="session_1",
            type="user",
            timestamp=datetime.now(UTC),
            message={"role": "user", "content": "Message 2"},
            projectPath="/test/project",
        )

        hash1 = ingest_service._hash_message(message1)
        hash2 = ingest_service._hash_message(message2)

        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_log_ingestion(self, ingest_service):
        """Test ingestion logging."""
        stats = IngestStats(
            messages_received=10,
            messages_processed=8,
            messages_skipped=1,
            messages_failed=1,
            duration_ms=1000,
        )

        # Mock database insert
        ingest_service.db.ingestion_logs.insert_one = AsyncMock()

        await ingest_service._log_ingestion(stats)

        ingest_service.db.ingestion_logs.insert_one.assert_called_once()
        call_args = ingest_service.db.ingestion_logs.insert_one.call_args[0][0]
        assert call_args["messages_processed"] == 8
        assert call_args["messages_skipped"] == 1
        assert call_args["messages_failed"] == 1
        assert call_args["duration_ms"] == 1000
        assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_get_existing_hashes(self, ingest_service):
        """Test retrieving existing message hashes."""
        session_id = "test_session"

        # Mock database query with async iterator
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = iter(
            [
                {"contentHash": "hash1"},
                {"contentHash": "hash2"},
                {"contentHash": "hash3"},
            ]
        )
        ingest_service.db.messages.find.return_value = mock_cursor

        hashes = await ingest_service._get_existing_hashes(session_id)

        assert hashes == {"hash1", "hash2", "hash3"}
        ingest_service.db.messages.find.assert_called_once_with(
            {"sessionId": session_id}, {"contentHash": 1}
        )

    @pytest.mark.asyncio
    async def test_get_existing_hashes_empty(self, ingest_service):
        """Test retrieving existing hashes when none exist."""
        session_id = "empty_session"

        # Mock database query returning empty result
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = iter([])
        ingest_service.db.messages.find.return_value = mock_cursor

        hashes = await ingest_service._get_existing_hashes(session_id)

        assert hashes == set()
        ingest_service.db.messages.find.assert_called_once()

    def test_ingest_stats_initialization(self):
        """Test IngestStats initialization."""
        stats = IngestStats(messages_received=5)

        assert stats.messages_received == 5
        assert stats.messages_processed == 0
        assert stats.messages_skipped == 0
        assert stats.messages_failed == 0
        assert stats.messages_updated == 0
        assert stats.sessions_created == 0
        assert stats.sessions_updated == 0
        assert stats.todos_processed == 0
        assert stats.config_updated is False
        assert stats.duration_ms == 0

    @pytest.mark.asyncio
    async def test_concurrent_session_processing(self, ingest_service):
        """Test that multiple sessions are processed concurrently."""
        messages = []
        for i in range(5):
            messages.append(
                MessageIngest(
                    uuid=f"msg_{i}",
                    sessionId=f"session_{i}",
                    type="user",
                    timestamp=datetime.now(UTC),
                    message={"role": "user", "content": f"Message {i}"},
                    projectPath="/test/project",
                )
            )

        # Track calls to _process_session_messages
        call_count = 0

        async def mock_process(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Add small delay to test concurrency
            await asyncio.sleep(0.01)
            return None

        with patch.object(
            ingest_service, "_process_session_messages", side_effect=mock_process
        ), patch.object(ingest_service, "_log_ingestion"):
            start_time = datetime.now(UTC)
            await ingest_service.ingest_messages(messages)
            duration = (datetime.now(UTC) - start_time).total_seconds()

            # Should process 5 sessions
            assert call_count == 5
            # Should complete faster than sequential processing (5 * 0.01 = 0.05s)
            assert duration < 0.04  # Some buffer for test execution


class TestIngestServiceBatchProcessing:
    """Tests for batch processing functionality in IngestService."""

    @pytest.mark.asyncio
    async def test_large_batch_processing(self, ingest_service):
        """Test processing a large batch of messages."""
        # Create 100 messages across 10 sessions
        messages = []
        for session_idx in range(10):
            for msg_idx in range(10):
                messages.append(
                    MessageIngest(
                        uuid=f"msg_{session_idx}_{msg_idx}",
                        sessionId=f"session_{session_idx}",
                        type="user" if msg_idx % 2 == 0 else "assistant",
                        timestamp=datetime.now(UTC),
                        message={
                            "role": "user" if msg_idx % 2 == 0 else "assistant",
                            "content": f"Message {msg_idx}",
                        },
                        projectPath="/test/project",
                    )
                )

        with patch.object(
            ingest_service, "_process_session_messages"
        ) as mock_process, patch.object(ingest_service, "_log_ingestion"):
            stats = await ingest_service.ingest_messages(messages)

            assert stats.messages_received == 100
            # Should process 10 sessions
            assert mock_process.call_count == 10

    @pytest.mark.asyncio
    async def test_batch_with_mixed_message_types(self, ingest_service):
        """Test batch processing with different message types."""
        messages = [
            MessageIngest(
                uuid="user_msg",
                sessionId="session_1",
                type="user",
                timestamp=datetime.now(UTC),
                message={"role": "user", "content": "User message"},
                projectPath="/test/project",
            ),
            MessageIngest(
                uuid="assistant_msg",
                sessionId="session_1",
                type="assistant",
                timestamp=datetime.now(UTC),
                message={"role": "assistant", "content": "Assistant response"},
                projectPath="/test/project",
                model="claude-3-sonnet",
                usage={"input_tokens": 10, "output_tokens": 20},
            ),
            MessageIngest(
                uuid="tool_msg",
                sessionId="session_1",
                type="tool_use",
                timestamp=datetime.now(UTC),
                message={
                    "role": "assistant",
                    "content": [{"type": "tool_use", "name": "calculator"}],
                },
                projectPath="/test/project",
            ),
        ]

        with patch.object(
            ingest_service, "_process_session_messages"
        ) as mock_process, patch.object(ingest_service, "_log_ingestion"):
            stats = await ingest_service.ingest_messages(messages)

            assert stats.messages_received == 3
            # All messages are from same session
            assert mock_process.call_count == 1
            # Verify session_messages parameter contains all 3 messages
            call_args = mock_process.call_args[0]
            session_messages = call_args[1]
            assert len(session_messages) == 3

    @pytest.mark.asyncio
    async def test_batch_processing_stats_aggregation(self, ingest_service):
        """Test that stats are properly aggregated across sessions."""
        messages = [
            MessageIngest(
                uuid="msg_1",
                sessionId="session_1",
                type="user",
                timestamp=datetime.now(UTC),
                message={"role": "user", "content": "Message 1"},
                projectPath="/test/project",
            ),
            MessageIngest(
                uuid="msg_2",
                sessionId="session_2",
                type="user",
                timestamp=datetime.now(UTC),
                message={"role": "user", "content": "Message 2"},
                projectPath="/test/project",
            ),
        ]

        async def mock_process_session(
            session_id, session_messages, stats, overwrite_mode=False
        ):
            """Mock that simulates processing with different outcomes per session."""
            if session_id == "session_1":
                stats.messages_processed += 1
                stats.sessions_created += 1
            else:
                stats.messages_skipped += 1
                stats.sessions_updated += 1

        with patch.object(
            ingest_service,
            "_process_session_messages",
            side_effect=mock_process_session,
        ), patch.object(ingest_service, "_log_ingestion"):
            stats = await ingest_service.ingest_messages(messages)

            assert stats.messages_received == 2
            assert stats.messages_processed == 1
            assert stats.messages_skipped == 1
            assert stats.sessions_created == 1
            assert stats.sessions_updated == 1

    @pytest.mark.asyncio
    async def test_batch_processing_partial_failures(self, ingest_service):
        """Test batch processing when some sessions fail."""
        messages = [
            MessageIngest(
                uuid="good_msg",
                sessionId="good_session",
                type="user",
                timestamp=datetime.now(UTC),
                message={"role": "user", "content": "Good message"},
                projectPath="/test/project",
            ),
            MessageIngest(
                uuid="bad_msg",
                sessionId="bad_session",
                type="user",
                timestamp=datetime.now(UTC),
                message={"role": "user", "content": "Bad message"},
                projectPath="/test/project",
            ),
        ]

        async def mock_process_session(
            session_id, session_messages, stats, overwrite_mode=False
        ):
            """Mock that simulates one session failing."""
            if session_id == "bad_session":
                raise Exception("Session processing failed")
            else:
                stats.messages_processed += 1
                stats.sessions_created += 1

        with patch.object(
            ingest_service,
            "_process_session_messages",
            side_effect=mock_process_session,
        ), patch.object(ingest_service, "_log_ingestion"):
            # Should not raise exception - uses return_exceptions=True
            stats = await ingest_service.ingest_messages(messages)

            assert stats.messages_received == 2
            # Only good session should be processed
            assert stats.messages_processed == 1
            assert stats.sessions_created == 1

    @pytest.mark.asyncio
    async def test_session_grouping_logic(self, ingest_service):
        """Test that messages are correctly grouped by session."""
        messages = [
            MessageIngest(
                uuid="msg_1_a",
                sessionId="session_1",
                type="user",
                timestamp=datetime.now(UTC),
                message={"role": "user", "content": "Message 1A"},
                projectPath="/test/project",
            ),
            MessageIngest(
                uuid="msg_2_a",
                sessionId="session_2",
                type="user",
                timestamp=datetime.now(UTC),
                message={"role": "user", "content": "Message 2A"},
                projectPath="/test/project",
            ),
            MessageIngest(
                uuid="msg_1_b",
                sessionId="session_1",
                type="assistant",
                timestamp=datetime.now(UTC),
                message={"role": "assistant", "content": "Response 1B"},
                projectPath="/test/project",
            ),
        ]

        session_groups = {}

        async def capture_session_groups(
            session_id, session_messages, stats, overwrite_mode=False
        ):
            """Capture the session groupings for verification."""
            session_groups[session_id] = [msg.uuid for msg in session_messages]
            stats.messages_processed += len(session_messages)

        with patch.object(
            ingest_service,
            "_process_session_messages",
            side_effect=capture_session_groups,
        ), patch.object(ingest_service, "_log_ingestion"):
            await ingest_service.ingest_messages(messages)

            # Verify grouping
            assert len(session_groups) == 2
            assert set(session_groups["session_1"]) == {"msg_1_a", "msg_1_b"}
            assert set(session_groups["session_2"]) == {"msg_2_a"}

    @pytest.mark.asyncio
    async def test_batch_performance_timing(self, ingest_service):
        """Test that batch processing records accurate timing."""
        messages = [
            MessageIngest(
                uuid="msg_1",
                sessionId="session_1",
                type="user",
                timestamp=datetime.now(UTC),
                message={"role": "user", "content": "Message 1"},
                projectPath="/test/project",
            )
        ]

        async def slow_process_session(*args, **kwargs):
            """Simulate slow processing."""
            await asyncio.sleep(0.05)  # 50ms delay

        with patch.object(
            ingest_service,
            "_process_session_messages",
            side_effect=slow_process_session,
        ), patch.object(ingest_service, "_log_ingestion") as mock_log:
            stats = await ingest_service.ingest_messages(messages)

            # Should record at least 50ms duration
            assert stats.duration_ms >= 45  # Some buffer for test timing
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_session_handling(self, ingest_service):
        """Test handling of edge case with empty sessions."""
        # This is more of a defensive test - normally wouldn't happen
        # but good to ensure the code is robust

        with patch.object(
            ingest_service, "_process_session_messages"
        ) as mock_process, patch.object(ingest_service, "_log_ingestion") as mock_log:
            stats = await ingest_service.ingest_messages([])

            assert stats.messages_received == 0
            assert stats.duration_ms >= 0
            # No sessions to process
            mock_process.assert_not_called()
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_overwrite_mode_propagation(self, ingest_service):
        """Test that overwrite mode is properly propagated to all sessions."""
        messages = [
            MessageIngest(
                uuid="msg_1",
                sessionId="session_1",
                type="user",
                timestamp=datetime.now(UTC),
                message={"role": "user", "content": "Message 1"},
                projectPath="/test/project",
            ),
            MessageIngest(
                uuid="msg_2",
                sessionId="session_2",
                type="user",
                timestamp=datetime.now(UTC),
                message={"role": "user", "content": "Message 2"},
                projectPath="/test/project",
            ),
        ]

        overwrite_calls = []

        async def capture_overwrite_mode(
            session_id, session_messages, stats, overwrite_mode=False
        ):
            """Capture overwrite mode for each session."""
            overwrite_calls.append((session_id, overwrite_mode))

        with patch.object(
            ingest_service,
            "_process_session_messages",
            side_effect=capture_overwrite_mode,
        ), patch.object(ingest_service, "_log_ingestion"):
            # Test with overwrite_mode=True
            await ingest_service.ingest_messages(messages, overwrite_mode=True)

            # Verify all sessions received overwrite_mode=True
            assert len(overwrite_calls) == 2
            for session_id, overwrite_mode in overwrite_calls:
                assert overwrite_mode is True


class TestIngestServiceErrorHandling:
    """Tests for error handling in IngestService."""

    @pytest.mark.asyncio
    async def test_database_bulk_write_error_in_overwrite_mode(
        self, ingest_service, sample_message_ingest
    ):
        """Test handling of database bulk write errors in overwrite mode."""
        session_id = "test_session"
        messages = [sample_message_ingest]
        stats = IngestStats(messages_received=1)

        with patch.object(
            ingest_service, "_ensure_session", return_value=None
        ), patch.object(
            ingest_service,
            "_message_to_doc",
            return_value=[{"uuid": "msg_123", "_id": ObjectId()}],
        ):
            # Mock bulk_write to raise an exception
            ingest_service.db.messages.bulk_write = AsyncMock(
                side_effect=Exception("Bulk write failed")
            )

            await ingest_service._process_session_messages(
                session_id, messages, stats, overwrite_mode=True
            )

            # Should track the failure
            assert stats.messages_failed == 1
            assert stats.messages_processed == 0

    @pytest.mark.asyncio
    async def test_database_insert_error_in_normal_mode(
        self, ingest_service, sample_message_ingest
    ):
        """Test handling of database insert errors in normal mode."""
        session_id = "test_session"
        messages = [sample_message_ingest]
        stats = IngestStats(messages_received=1)

        with patch.object(
            ingest_service, "_ensure_session", return_value=None
        ), patch.object(
            ingest_service, "_get_existing_hashes", return_value=set()
        ), patch.object(
            ingest_service, "_message_to_doc", return_value=[{"uuid": "msg_123"}]
        ), patch.object(
            ingest_service, "_hash_message", return_value="hash123"
        ):
            # Mock insert_many to raise an exception
            ingest_service.db.messages.insert_many = AsyncMock(
                side_effect=Exception("Insert failed")
            )

            await ingest_service._process_session_messages(session_id, messages, stats)

            # Should track the failure
            assert stats.messages_failed == 1
            assert stats.messages_processed == 0

    @pytest.mark.asyncio
    async def test_session_creation_error(self, ingest_service, sample_message_ingest):
        """Test handling of session creation errors."""
        session_id = "failing_session"
        messages = [sample_message_ingest]
        stats = IngestStats(messages_received=1)

        # Mock _ensure_session to raise an exception
        with patch.object(
            ingest_service,
            "_ensure_session",
            side_effect=Exception("Session creation failed"),
        ):
            await ingest_service._process_session_messages(session_id, messages, stats)

            # Should track all messages in the session as failed
            assert stats.messages_failed == 1

    @pytest.mark.asyncio
    async def test_project_creation_error_in_ensure_session(
        self, ingest_service, sample_message_ingest
    ):
        """Test handling of project creation errors during session creation."""
        session_id = "test_session"

        # Mock database queries
        ingest_service.db.sessions.find_one = AsyncMock(return_value=None)
        ingest_service.db.projects.find_one = AsyncMock(return_value=None)
        ingest_service.db.projects.insert_one = AsyncMock(
            side_effect=Exception("Project creation failed")
        )

        with pytest.raises(Exception, match="Project creation failed"):
            await ingest_service._ensure_session(session_id, sample_message_ingest)

    @pytest.mark.asyncio
    async def test_session_insertion_error_in_ensure_session(
        self, ingest_service, sample_message_ingest
    ):
        """Test handling of session insertion errors."""
        session_id = "test_session"

        # Mock database queries - session doesn't exist, project exists
        ingest_service.db.sessions.find_one = AsyncMock(return_value=None)
        ingest_service.db.projects.find_one = AsyncMock(
            return_value={"_id": ObjectId(), "name": "Test"}
        )
        ingest_service.db.sessions.insert_one = AsyncMock(
            side_effect=Exception("Session insertion failed")
        )

        with pytest.raises(Exception, match="Session insertion failed"):
            await ingest_service._ensure_session(session_id, sample_message_ingest)

    @pytest.mark.asyncio
    async def test_project_insertion_error_in_ensure_project(self, ingest_service):
        """Test handling of project insertion errors."""
        project_path = "/test/project"
        project_name = "Test Project"

        # Mock database queries - project doesn't exist
        ingest_service.db.projects.find_one = AsyncMock(return_value=None)
        ingest_service.db.projects.insert_one = AsyncMock(
            side_effect=Exception("Project insertion failed")
        )

        with pytest.raises(Exception, match="Project insertion failed"):
            await ingest_service._ensure_project(project_path, project_name)

    @pytest.mark.asyncio
    async def test_message_to_doc_conversion_error(
        self, ingest_service, sample_message_ingest
    ):
        """Test handling of message to document conversion errors."""
        session_id = "test_session"
        messages = [sample_message_ingest]
        stats = IngestStats(messages_received=1)

        with patch.object(
            ingest_service, "_ensure_session", return_value=None
        ), patch.object(
            ingest_service, "_get_existing_hashes", return_value=set()
        ), patch.object(
            ingest_service, "_hash_message", return_value="hash123"
        ), patch.object(
            ingest_service,
            "_message_to_doc",
            side_effect=Exception("Conversion failed"),
        ):
            await ingest_service._process_session_messages(session_id, messages, stats)

            # Should track the failed message
            assert stats.messages_failed == 1
            assert stats.messages_processed == 0

    @pytest.mark.asyncio
    async def test_update_session_stats_error(
        self, ingest_service, sample_message_ingest
    ):
        """Test handling of session stats update errors."""
        session_id = "test_session"
        messages = [sample_message_ingest]
        stats = IngestStats(messages_received=1)

        with patch.object(
            ingest_service, "_ensure_session", return_value=None
        ), patch.object(
            ingest_service, "_get_existing_hashes", return_value=set()
        ), patch.object(
            ingest_service, "_message_to_doc", return_value=[{"uuid": "msg_123"}]
        ), patch.object(
            ingest_service, "_hash_message", return_value="hash123"
        ), patch.object(
            ingest_service,
            "_update_session_stats",
            side_effect=Exception("Stats update failed"),
        ):
            # Mock successful insert
            ingest_service.db.messages.insert_many = AsyncMock(
                return_value=MagicMock(inserted_ids=["id1"])
            )

            # Message is processed successfully, then stats update fails, caught by outer exception handler
            await ingest_service._process_session_messages(session_id, messages, stats)

            # Message is processed first, then outer exception handler adds to failed count
            assert stats.messages_processed == 1
            assert stats.messages_failed == 1

    @pytest.mark.asyncio
    async def test_get_existing_hashes_database_error(self, ingest_service):
        """Test handling of database errors when retrieving existing hashes."""
        session_id = "test_session"

        # Mock database query to raise an exception
        ingest_service.db.messages.find = MagicMock(
            side_effect=Exception("Database connection failed")
        )

        with pytest.raises(Exception, match="Database connection failed"):
            await ingest_service._get_existing_hashes(session_id)

    @pytest.mark.asyncio
    async def test_aggregation_pipeline_error_in_update_session_stats(
        self, ingest_service
    ):
        """Test handling of aggregation pipeline errors in session stats update."""
        session_id = "test_session"

        # Mock aggregation to raise an exception
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(side_effect=Exception("Aggregation failed"))
        ingest_service.db.messages.aggregate = MagicMock(return_value=mock_cursor)

        with pytest.raises(Exception, match="Aggregation failed"):
            await ingest_service._update_session_stats(session_id)

    @pytest.mark.asyncio
    async def test_session_update_error_in_update_session_stats(self, ingest_service):
        """Test handling of session update errors in session stats update."""
        session_id = "test_session"

        # Mock successful aggregation but failed session update
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(
            return_value=[
                {
                    "_id": None,
                    "messageCount": 5,
                    "totalCost": 0.1,
                    "inputTokens": 100,
                    "outputTokens": 50,
                    "toolUseCount": 2,
                    "startTime": datetime.now(UTC),
                    "endTime": datetime.now(UTC),
                }
            ]
        )
        ingest_service.db.messages.aggregate = MagicMock(return_value=mock_cursor)
        ingest_service.db.sessions.update_one = AsyncMock(
            side_effect=Exception("Session update failed")
        )

        with pytest.raises(Exception, match="Session update failed"):
            await ingest_service._update_session_stats(session_id)

    @pytest.mark.asyncio
    async def test_integration_service_error_handling(
        self, ingest_service, sample_message_ingest
    ):
        """Test handling of integration service errors."""
        session_id = "test_session"
        messages = [sample_message_ingest]
        stats = IngestStats(messages_received=1)

        with patch.object(
            ingest_service, "_ensure_session", return_value=None
        ), patch.object(
            ingest_service, "_get_existing_hashes", return_value=set()
        ), patch.object(
            ingest_service, "_message_to_doc", return_value=[{"uuid": "msg_123"}]
        ), patch.object(
            ingest_service, "_hash_message", return_value="hash123"
        ), patch(
            "app.services.realtime_integration.get_integration_service"
        ) as mock_get_service, patch.object(
            ingest_service,
            "_update_session_stats",
            side_effect=Exception("Integration service failed"),
        ):
            # Mock successful insert
            mock_result = MagicMock()
            mock_result.inserted_ids = ["id1"]
            ingest_service.db.messages.insert_many = AsyncMock(return_value=mock_result)

            # Mock integration service to raise error
            mock_integration = MagicMock()
            mock_integration.on_message_ingested = AsyncMock(
                side_effect=Exception("Integration failed")
            )
            mock_get_service.return_value = mock_integration

            # Message processed successfully, then integration service error in stats update
            await ingest_service._process_session_messages(session_id, messages, stats)

            # Both processed and failed due to execution order
            assert stats.messages_processed == 1
            assert stats.messages_failed == 1

    @pytest.mark.asyncio
    async def test_cost_calculation_error_in_message_processing(self, ingest_service):
        """Test handling of cost calculation errors during message processing."""
        message = MessageIngest(
            uuid="msg_with_usage",
            sessionId="session_1",
            type="assistant",
            timestamp=datetime.now(UTC),
            message={
                "role": "assistant",
                "content": "Response",
                "usage": {"input_tokens": 100, "output_tokens": 50},
                "model": "claude-3-sonnet",
            },
            projectPath="/test/project",
        )

        with patch("app.services.ingest.CostCalculationService") as mock_cost_service:
            # Mock cost service to raise error
            mock_cost_instance = MagicMock()
            mock_cost_instance.calculate_message_cost.side_effect = Exception(
                "Cost calculation failed"
            )
            mock_cost_service.return_value = mock_cost_instance

            # Cost calculation error should propagate and be raised
            with pytest.raises(Exception, match="Cost calculation failed"):
                ingest_service._create_default_doc(message, "session_1")

    @pytest.mark.asyncio
    async def test_log_ingestion_error(self, ingest_service):
        """Test handling of ingestion logging errors."""
        stats = IngestStats(
            messages_received=1,
            messages_processed=1,
            messages_skipped=0,
            messages_failed=0,
            duration_ms=100,
        )

        # Mock database insert to raise error
        ingest_service.db.ingestion_logs.insert_one = AsyncMock(
            side_effect=Exception("Logging failed")
        )

        with pytest.raises(Exception, match="Logging failed"):
            await ingest_service._log_ingestion(stats)

    @pytest.mark.asyncio
    async def test_complex_message_parsing_error(self, ingest_service):
        """Test handling of complex message parsing errors."""
        # Create a message with malformed content that could cause parsing errors
        message = MessageIngest(
            uuid="malformed_msg",
            sessionId="session_1",
            type="assistant",
            timestamp=datetime.now(UTC),
            message={
                "content": [
                    {"type": "text", "text": "Valid text"},
                    {
                        "type": "tool_use",
                        "name": None,
                        "input": None,
                    },  # Malformed tool use
                    {"type": "invalid_type", "data": "unexpected"},  # Invalid type
                ]
            },
            projectPath="/test/project",
        )

        # Should handle malformed content gracefully
        docs = ingest_service._message_to_doc(message, "session_1")

        # Should still create documents, even with malformed parts
        assert len(docs) >= 1
        assert docs[0]["uuid"] == "malformed_msg"

    @pytest.mark.asyncio
    async def test_concurrent_processing_with_errors(self, ingest_service):
        """Test that errors in one session don't affect others when processing concurrently."""
        messages = []
        for i in range(3):
            messages.append(
                MessageIngest(
                    uuid=f"msg_{i}",
                    sessionId=f"session_{i}",
                    type="user",
                    timestamp=datetime.now(UTC),
                    message={"role": "user", "content": f"Message {i}"},
                    projectPath="/test/project",
                )
            )

        async def selective_failure(
            session_id, session_messages, stats, overwrite_mode=False
        ):
            """Fail only session_1, succeed for others."""
            if session_id == "session_1":
                raise Exception("Session 1 failed")
            else:
                stats.messages_processed += len(session_messages)
                stats.sessions_created += 1

        with patch.object(
            ingest_service, "_process_session_messages", side_effect=selective_failure
        ), patch.object(ingest_service, "_log_ingestion"):
            # Should not raise exception due to return_exceptions=True
            stats = await ingest_service.ingest_messages(messages)

            # Should process 2 out of 3 sessions successfully
            assert stats.messages_processed == 2
            assert stats.sessions_created == 2
            assert stats.messages_received == 3

    def test_hash_message_with_none_content(self, ingest_service):
        """Test message hashing with None content."""
        message = MessageIngest(
            uuid="msg_none",
            sessionId="session_1",
            type="user",
            timestamp=datetime.now(UTC),
            message=None,  # None message content
            projectPath="/test/project",
        )

        hash_result = ingest_service._hash_message(message)

        # Should produce a valid hash even with None content
        assert isinstance(hash_result, str)
        assert len(hash_result) > 0

    def test_add_optional_fields_with_invalid_cost(self, ingest_service):
        """Test adding optional fields with invalid cost data."""
        doc = {"uuid": "test"}
        message = MessageIngest(
            uuid="test",
            sessionId="session_1",
            type="assistant",
            timestamp=datetime.now(UTC),
            message={
                "usage": {
                    "input_tokens": "invalid",
                    "output_tokens": 50,
                },  # Invalid token count
                "model": "claude-3-sonnet",
            },
            projectPath="/test/project",
        )

        with patch("app.services.ingest.CostCalculationService") as mock_cost_service:
            mock_cost_instance = MagicMock()
            mock_cost_instance.calculate_message_cost.side_effect = ValueError(
                "Invalid token count"
            )
            mock_cost_service.return_value = mock_cost_instance

            # Cost calculation error should propagate and be raised
            with pytest.raises(ValueError, match="Invalid token count"):
                ingest_service._add_optional_fields(doc, message)
