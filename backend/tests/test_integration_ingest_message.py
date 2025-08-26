"""Integration tests for ingest → message flow."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from app.schemas.ingest import MessageIngest
from app.services.ingest import IngestService
from app.services.message import MessageService


@pytest.fixture
def mock_db():
    """Create a mock database for integration testing."""
    db = MagicMock()

    # Mock collections with async methods
    db.messages = MagicMock()
    db.sessions = MagicMock()
    db.projects = MagicMock()
    db.ingestion_logs = MagicMock()

    # Make collection methods async
    for collection in [db.messages, db.sessions, db.projects, db.ingestion_logs]:
        collection.insert_one = AsyncMock()
        # Mock insert_many to return proper result
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_ids = [ObjectId(), ObjectId(), ObjectId()]
        collection.insert_many = AsyncMock(return_value=mock_insert_result)

        collection.find_one = AsyncMock(return_value=None)
        collection.find = MagicMock()
        collection.update_one = AsyncMock()
        collection.delete_many = AsyncMock()
        collection.count_documents = AsyncMock(return_value=0)

        # Mock bulk_write to return proper result
        mock_bulk_result = MagicMock()
        mock_bulk_result.inserted_count = 3
        mock_bulk_result.modified_count = 0
        collection.bulk_write = AsyncMock(return_value=mock_bulk_result)

        # Mock aggregate method
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        collection.aggregate = MagicMock(return_value=mock_cursor)

    return db


@pytest.fixture
def ingest_service(mock_db):
    """Create IngestService with mock database."""
    return IngestService(mock_db)


@pytest.fixture
def message_service(mock_db):
    """Create MessageService with mock database."""
    return MessageService(mock_db)


@pytest.fixture
def sample_messages():
    """Sample messages for integration testing."""
    now = datetime.now(UTC)
    return [
        MessageIngest(
            uuid="test_msg_001",
            sessionId="test_session_001",
            type="user",
            timestamp=now,
            message={"role": "user", "content": "Hello, Claude!"},
            projectPath="/test/integration",
            model="claude-3-sonnet",
            usage={"input_tokens": 15, "output_tokens": 0},
            costUsd=0.0015,
        ),
        MessageIngest(
            uuid="test_msg_002",
            sessionId="test_session_001",
            type="assistant",
            timestamp=now,
            message={"role": "assistant", "content": "Hello! How can I help you?"},
            projectPath="/test/integration",
            model="claude-3-sonnet",
            usage={"input_tokens": 15, "output_tokens": 25},
            costUsd=0.0025,
            parentUuid="test_msg_001",
        ),
        MessageIngest(
            uuid="test_msg_003",
            sessionId="test_session_002",
            type="user",
            timestamp=now,
            message={"role": "user", "content": "Different session message"},
            projectPath="/test/integration",
            model="claude-3-sonnet",
            usage={"input_tokens": 20, "output_tokens": 0},
            costUsd=0.002,
        ),
    ]


class TestIngestMessageIntegration:
    """Integration tests for ingest to message flow."""

    @pytest.mark.asyncio
    async def test_ingest_and_retrieve_messages(
        self, ingest_service, message_service, sample_messages, mock_db
    ):
        """Test full flow: ingest messages and retrieve them."""
        # Set up mock database responses
        mock_db.projects.find_one.return_value = None  # No existing project
        mock_db.sessions.find_one.return_value = None  # No existing session
        mock_db.messages.find_one.return_value = None  # No existing messages
        mock_db.messages.count_documents.return_value = 3

        # Mock cursor for find operation - setup different responses for different queries
        def mock_find(query_filter=None, projection=None):
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.skip.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor

            # Check if this is the hash-checking query
            if projection and "contentHash" in projection:
                # Return empty cursor for dedup checking
                async def empty_async_iter(self):
                    return
                    yield  # This never executes

                mock_cursor.__aiter__ = empty_async_iter
            else:
                # Return full messages for regular queries
                async def mock_async_iter(self):
                    for i, msg in enumerate(sample_messages):
                        yield {
                            "_id": ObjectId(),
                            "uuid": msg.uuid,
                            "type": msg.type,
                            "sessionId": msg.sessionId,
                            "content": msg.message.get("content", ""),
                            "timestamp": msg.timestamp,
                            "model": msg.model,
                            "parentUuid": getattr(msg, "parentUuid", None),
                            "createdAt": msg.timestamp,
                        }

                mock_cursor.__aiter__ = mock_async_iter

            return mock_cursor

        mock_db.messages.find.side_effect = mock_find

        # Mock external dependencies
        with (
            patch(
                "app.services.realtime_integration.get_integration_service"
            ) as mock_integration,
            patch(
                "app.services.cost_calculation.CostCalculationService"
            ) as mock_cost_service,
        ):
            mock_integration.return_value = AsyncMock()
            mock_cost_service.return_value = AsyncMock()

            # Ingest messages
            stats = await ingest_service.ingest_messages(sample_messages)

            # Verify ingest stats (depends on internal logic)
            assert stats.messages_received == 3
            assert stats.duration_ms >= 0

            # Verify database operations were called
            # In non-overwrite mode, messages use insert_many, sessions use bulk operations
            assert mock_db.messages.insert_many.called
            assert (
                mock_db.sessions.insert_one.called
            )  # Sessions are created with insert_one

            # Retrieve all messages
            messages, total = await message_service.list_messages(
                user_id="507f1f77bcf86cd799439011",
                filter_dict={"uuid": {"$regex": "^test_"}},
                skip=0,
                limit=10,
                sort_order="asc",
            )

            # Verify message retrieval worked
            assert total == 3
            assert len(messages) == 3

            # Verify messages have expected properties
            assert all(hasattr(msg, "uuid") for msg in messages)
            assert all(hasattr(msg, "type") for msg in messages)
            assert all(hasattr(msg, "session_id") for msg in messages)

    @pytest.mark.asyncio
    async def test_ingest_duplicate_messages_overwrite_mode(
        self, ingest_service, message_service, sample_messages, mock_db
    ):
        """Test ingesting duplicate messages with overwrite mode."""
        # Mock finding existing messages for overwrite scenario
        mock_db.messages.find_one.return_value = {
            "_id": ObjectId(),
            "uuid": "test_msg_001",
            "type": "user",
            "sessionId": "test_session_001",
            "content": "Original content",
        }

        with (
            patch(
                "app.services.realtime_integration.get_integration_service"
            ) as mock_integration,
            patch(
                "app.services.cost_calculation.CostCalculationService"
            ) as mock_cost_service,
        ):
            mock_integration.return_value = AsyncMock()
            mock_cost_service.return_value = AsyncMock()

            # Ingest with overwrite mode
            stats = await ingest_service.ingest_messages(
                sample_messages, overwrite_mode=True
            )

            # Verify stats show received messages
            assert stats.messages_received == 3

            # Verify bulk operations were called (indicating processing occurred)
            assert mock_db.messages.bulk_write.called

    @pytest.mark.asyncio
    async def test_ingest_session_filtering(
        self, ingest_service, message_service, sample_messages, mock_db
    ):
        """Test message retrieval filtered by session."""
        # Mock responses for session filtering
        mock_db.messages.count_documents.return_value = 2

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor

        # Mock messages for session_001 only
        async def mock_session_iter(self):
            for msg in sample_messages[:2]:  # First two messages are session_001
                yield {
                    "_id": ObjectId(),
                    "uuid": msg.uuid,
                    "type": msg.type,
                    "sessionId": msg.sessionId,
                    "content": msg.message.get("content", ""),
                    "timestamp": msg.timestamp,
                    "model": msg.model,
                    "parentUuid": getattr(msg, "parentUuid", None),
                    "createdAt": msg.timestamp,
                }

        mock_cursor.__aiter__ = mock_session_iter
        mock_db.messages.find.return_value = mock_cursor

        with (
            patch(
                "app.services.realtime_integration.get_integration_service"
            ) as mock_integration,
            patch(
                "app.services.cost_calculation.CostCalculationService"
            ) as mock_cost_service,
        ):
            mock_integration.return_value = AsyncMock()
            mock_cost_service.return_value = AsyncMock()

            # Test session filtering
            messages, total = await message_service.list_messages(
                user_id="507f1f77bcf86cd799439011",
                filter_dict={"sessionId": "test_session_001"},
                skip=0,
                limit=10,
                sort_order="asc",
            )

            # Should find 2 messages for session_001
            assert total == 2
            assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_service_integration_flow(
        self, ingest_service, message_service, sample_messages, mock_db
    ):
        """Test the complete service integration flow."""
        with (
            patch(
                "app.services.realtime_integration.get_integration_service"
            ) as mock_integration,
            patch(
                "app.services.cost_calculation.CostCalculationService"
            ) as mock_cost_service,
        ):
            mock_integration.return_value = AsyncMock()
            mock_cost_service.return_value = AsyncMock()

            # Test that both services can be called without errors
            stats = await ingest_service.ingest_messages(sample_messages)
            assert stats.messages_received == 3

            # Test message service operations
            messages, total = await message_service.list_messages(
                user_id="507f1f77bcf86cd799439011",
                filter_dict={},
                skip=0,
                limit=10,
                sort_order="asc",
            )

            # Verify service integration doesn't crash
            assert isinstance(messages, list)
            assert isinstance(total, int)
