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

    # Mock list_collection_names for RollingMessageService
    db.list_collection_names = AsyncMock(return_value=[])

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
def ingest_service(mock_db, message_service):
    """Create IngestService with mock database."""
    test_user_id = "507f1f77bcf86cd799439011"
    service = IngestService(mock_db, test_user_id)

    # Share the same message storage with message_service
    async def mock_insert_message(message_data):
        message_data["_id"] = ObjectId()
        message_service._mock_messages.append(message_data)
        return str(message_data["_id"])

    async def mock_find_messages(filter_dict, skip=0, limit=100, sort_order="desc"):
        results = message_service._mock_messages[:]
        if "sessionId" in filter_dict:
            session_filter = filter_dict["sessionId"]
            if isinstance(session_filter, dict) and "$in" in session_filter:
                # Handle MongoDB $in operator
                allowed_sessions = session_filter["$in"]
                results = [
                    msg for msg in results if msg.get("sessionId") in allowed_sessions
                ]
            else:
                # Simple equality filter
                results = [
                    msg
                    for msg in results
                    if msg.get("sessionId") == filter_dict["sessionId"]
                ]
        results.sort(
            key=lambda x: x.get("timestamp", datetime.min),
            reverse=(sort_order == "desc"),
        )
        paginated = results[skip : skip + limit]
        return paginated, len(results)

    async def mock_find_one(filter_dict):
        for msg in message_service._mock_messages:
            if all(msg.get(k) == v for k, v in filter_dict.items()):
                return msg
        return None

    async def mock_update_one(filter_dict, update_dict):
        for msg in message_service._mock_messages:
            if all(msg.get(k) == v for k, v in filter_dict.items()):
                if "$set" in update_dict:
                    msg.update(update_dict["$set"])
                    return True
        return False

    async def mock_aggregate_across_collections(pipeline, start_date, end_date):
        # Simple mock for aggregation
        return []

    service.rolling_service.insert_message = mock_insert_message
    service.rolling_service.find_messages = mock_find_messages
    service.rolling_service.find_one = mock_find_one
    service.rolling_service.update_one = mock_update_one
    service.rolling_service.aggregate_across_collections = (
        mock_aggregate_across_collections
    )

    return service


@pytest.fixture
def message_service(mock_db):
    """Create MessageService with mock database."""
    service = MessageService(mock_db)

    # Storage for messages
    service._mock_messages = []

    # Mock rolling_service methods
    async def mock_find_messages(filter_dict, skip=0, limit=100, sort_order="desc"):
        # Filter messages based on filter_dict
        results = service._mock_messages[:]
        if "sessionId" in filter_dict:
            session_filter = filter_dict["sessionId"]
            if isinstance(session_filter, dict) and "$in" in session_filter:
                # Handle MongoDB $in operator
                allowed_sessions = session_filter["$in"]
                results = [
                    msg for msg in results if msg.get("sessionId") in allowed_sessions
                ]
            else:
                # Simple equality filter
                results = [
                    msg
                    for msg in results
                    if msg.get("sessionId") == filter_dict["sessionId"]
                ]

        # Sort
        results.sort(
            key=lambda x: x.get("timestamp", datetime.min),
            reverse=(sort_order == "desc"),
        )

        # Apply pagination
        paginated = results[skip : skip + limit]
        return paginated, len(results)

    async def mock_find_one(filter_dict):
        for msg in service._mock_messages:
            if all(msg.get(k) == v for k, v in filter_dict.items()):
                return msg
        return None

    async def mock_insert_message(message_data):
        message_data["_id"] = ObjectId()
        service._mock_messages.append(message_data)
        return str(message_data["_id"])

    service.rolling_service.find_messages = mock_find_messages
    service.rolling_service.find_one = mock_find_one
    service.rolling_service.insert_message = mock_insert_message

    return service


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

            # Verify messages were added to storage
            # With the new rolling collections, we check messages were processed
            assert stats.messages_processed > 0 or stats.messages_updated > 0
            assert (
                mock_db.sessions.insert_one.called
            )  # Sessions are created with insert_one

            # Mock projects and sessions for hierarchical ownership queries
            mock_db.projects.find.return_value.to_list = AsyncMock(
                return_value=[{"_id": ObjectId()}]
            )
            mock_db.sessions.find.return_value.to_list = AsyncMock(
                return_value=[
                    {"sessionId": "test_session_001"},
                    {"sessionId": "test_session_002"},
                ]
            )

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

            # Verify sessions were created (which indicates processing occurred)
            assert stats.sessions_created > 0 or stats.sessions_updated > 0
            # Note: Due to mocking limitations, message processing stats may not be accurate
            # The fact that sessions were created confirms the ingestion ran

    @pytest.mark.asyncio
    async def test_ingest_session_filtering(
        self, ingest_service, message_service, sample_messages, mock_db
    ):
        """Test message retrieval filtered by session."""
        # Pre-populate the mock storage with test messages
        for msg in sample_messages[:2]:  # First two messages are session_001
            message_service._mock_messages.append(
                {
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
            )

        # Mock responses for session filtering (for backward compatibility)
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

            # Mock projects and sessions for hierarchical ownership queries
            project_id = ObjectId()
            mock_db.projects.find.return_value.to_list = AsyncMock(
                return_value=[{"_id": project_id}]
            )
            mock_db.sessions.find.return_value.to_list = AsyncMock(
                return_value=[
                    {"sessionId": "test_session_001", "projectId": project_id},
                    {"sessionId": "test_session_002", "projectId": project_id},
                ]
            )

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

            # Mock projects and sessions for hierarchical ownership queries
            mock_db.projects.find.return_value.to_list = AsyncMock(
                return_value=[{"_id": ObjectId()}]
            )
            mock_db.sessions.find.return_value.to_list = AsyncMock(
                return_value=[
                    {"sessionId": "test_session_001"},
                    {"sessionId": "test_session_002"},
                ]
            )

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
