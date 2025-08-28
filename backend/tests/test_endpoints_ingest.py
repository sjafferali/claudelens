"""Tests for ingestion API endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.api.api_v1.endpoints.ingest import (
    ingest_batch,
    ingest_single,
    ingestion_status,
    update_project_metadata,
)
from app.core.exceptions import ValidationError
from app.schemas.ingest import (
    BatchIngestRequest,
    BatchIngestResponse,
    IngestStats,
    MessageIngest,
)


class TestIngestBatch:
    """Test batch ingestion endpoint."""

    @pytest.fixture
    def sample_message(self):
        """Create sample message."""
        return MessageIngest(
            uuid="test-uuid-123",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="test-session",
            message={"content": "Test message"},
        )

    @pytest.fixture
    def sample_request(self, sample_message):
        """Create sample batch request."""
        return BatchIngestRequest(
            messages=[sample_message], todos=[], config=None, overwrite_mode=False
        )

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        return Mock()

    @pytest.fixture
    def mock_api_key(self):
        """Create mock API key."""
        return "test-api-key"

    @pytest.mark.asyncio
    async def test_ingest_batch_success(self, sample_request, mock_db, mock_api_key):
        """Test successful batch ingestion."""
        background_tasks = BackgroundTasks()

        stats = IngestStats(
            messages_received=1,
            messages_processed=1,
            messages_skipped=0,
            messages_updated=0,
            messages_failed=0,
            sessions_created=1,
            sessions_updated=0,
            todos_processed=0,
            config_updated=False,
            duration_ms=100,
            projects_created=["project-id-123"],
        )

        with patch(
            "app.api.api_v1.endpoints.ingest.IngestService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service.ingest_messages = AsyncMock(return_value=stats)
            mock_service_class.return_value = mock_service

            result = await ingest_batch(
                sample_request, background_tasks, mock_db, mock_api_key
            )

            assert isinstance(result, BatchIngestResponse)
            assert result.success is True
            assert result.stats == stats
            assert "successfully" in result.message

            # IngestService now requires user_id parameter
            mock_service_class.assert_called_once_with(mock_db, mock_api_key)
            mock_service.ingest_messages.assert_called_once_with(
                sample_request.messages, overwrite_mode=False
            )

    @pytest.mark.asyncio
    async def test_ingest_batch_too_many_messages_endpoint_check(
        self, mock_db, mock_api_key
    ):
        """Test endpoint validation for too many messages."""
        # Test the endpoint logic directly rather than Pydantic validation
        # Create a valid request first
        message = MessageIngest(
            uuid="test-uuid",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="test-session",
            message={"content": "Test"},
        )

        # Manually create a request that bypasses Pydantic to test endpoint logic
        class LargeRequest:
            def __init__(self):
                self.messages = [message] * 1001  # > 1000 messages
                self.todos = []
                self.config = None
                self.overwrite_mode = False

        large_request = LargeRequest()
        background_tasks = BackgroundTasks()

        with pytest.raises(HTTPException) as exc_info:
            await ingest_batch(large_request, background_tasks, mock_db, mock_api_key)

        assert exc_info.value.status_code == 400
        assert "exceeds maximum" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_ingest_batch_empty_messages(self, mock_db, mock_api_key):
        """Test batch with no messages."""
        empty_request = BatchIngestRequest(
            messages=[], todos=[], config=None, overwrite_mode=False
        )

        background_tasks = BackgroundTasks()

        with pytest.raises(HTTPException) as exc_info:
            await ingest_batch(empty_request, background_tasks, mock_db, mock_api_key)

        assert exc_info.value.status_code == 400
        assert "No messages provided" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_ingest_batch_with_overwrite_mode(
        self, sample_message, mock_db, mock_api_key
    ):
        """Test batch ingestion with overwrite mode enabled."""
        request = BatchIngestRequest(
            messages=[sample_message], todos=[], config=None, overwrite_mode=True
        )

        background_tasks = BackgroundTasks()
        stats = IngestStats()

        with patch(
            "app.api.api_v1.endpoints.ingest.IngestService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service.ingest_messages = AsyncMock(return_value=stats)
            mock_service_class.return_value = mock_service

            await ingest_batch(request, background_tasks, mock_db, mock_api_key)

            mock_service.ingest_messages.assert_called_once_with(
                request.messages, overwrite_mode=True
            )

    @pytest.mark.asyncio
    async def test_ingest_batch_validation_error(
        self, sample_request, mock_db, mock_api_key
    ):
        """Test handling of validation errors."""
        background_tasks = BackgroundTasks()

        with patch(
            "app.api.api_v1.endpoints.ingest.IngestService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service.ingest_messages = AsyncMock(
                side_effect=ValidationError("Invalid message format")
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await ingest_batch(
                    sample_request, background_tasks, mock_db, mock_api_key
                )

            assert exc_info.value.status_code == 422
            assert "Invalid message format" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_ingest_batch_general_error(
        self, sample_request, mock_db, mock_api_key
    ):
        """Test handling of general errors."""
        background_tasks = BackgroundTasks()

        with patch(
            "app.api.api_v1.endpoints.ingest.IngestService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service.ingest_messages = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await ingest_batch(
                    sample_request, background_tasks, mock_db, mock_api_key
                )

            assert exc_info.value.status_code == 500
            assert "Failed to process batch" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_ingest_batch_with_projects_created(
        self, sample_request, mock_db, mock_api_key
    ):
        """Test batch ingestion with projects created triggers background task."""
        background_tasks = BackgroundTasks()

        stats = IngestStats(
            messages_received=1,
            messages_processed=1,
            projects_created=["project-1", "project-2"],
        )

        with (
            patch(
                "app.api.api_v1.endpoints.ingest.IngestService"
            ) as mock_service_class,
            patch("app.api.api_v1.endpoints.ingest.update_project_metadata"),
        ):
            mock_service = Mock()
            mock_service.ingest_messages = AsyncMock(return_value=stats)
            mock_service_class.return_value = mock_service

            result = await ingest_batch(
                sample_request, background_tasks, mock_db, mock_api_key
            )

            assert result.success is True
            # Background task should be scheduled but we can't easily test it directly

    @pytest.mark.asyncio
    async def test_ingest_batch_no_projects_created(
        self, sample_request, mock_db, mock_api_key
    ):
        """Test batch ingestion with no projects created."""
        background_tasks = BackgroundTasks()

        stats = IngestStats(
            messages_received=1,
            messages_processed=1,
            projects_created=[],  # No projects created
        )

        with patch(
            "app.api.api_v1.endpoints.ingest.IngestService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service.ingest_messages = AsyncMock(return_value=stats)
            mock_service_class.return_value = mock_service

            result = await ingest_batch(
                sample_request, background_tasks, mock_db, mock_api_key
            )

            assert result.success is True
            # No background task should be scheduled


class TestIngestSingle:
    """Test single message ingestion endpoint."""

    @pytest.fixture
    def sample_message(self):
        """Create sample message."""
        return MessageIngest(
            uuid="single-uuid",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="single-session",
            message={"content": "Single message"},
        )

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        return Mock()

    @pytest.fixture
    def mock_api_key(self):
        """Create mock API key."""
        return "test-api-key"

    @pytest.mark.asyncio
    async def test_ingest_single_success(self, sample_message, mock_db, mock_api_key):
        """Test successful single message ingestion."""
        stats = IngestStats(messages_received=1, messages_processed=1)

        with patch("app.api.api_v1.endpoints.ingest.ingest_batch") as mock_batch:
            mock_batch.return_value = BatchIngestResponse(
                success=True, stats=stats, message="Success"
            )

            result = await ingest_single(sample_message, mock_db, mock_api_key)

            assert isinstance(result, BatchIngestResponse)
            assert result.success is True

            # Check that ingest_batch was called with correct parameters
            mock_batch.assert_called_once()
            call_args = mock_batch.call_args[0]

            # Check BatchIngestRequest structure
            batch_request = call_args[0]
            assert isinstance(batch_request, BatchIngestRequest)
            assert len(batch_request.messages) == 1
            assert batch_request.messages[0] == sample_message
            assert batch_request.overwrite_mode is False
            assert batch_request.todos == []
            assert batch_request.config is None

    @pytest.mark.asyncio
    async def test_ingest_single_error_propagation(
        self, sample_message, mock_db, mock_api_key
    ):
        """Test error propagation from batch endpoint."""
        with patch("app.api.api_v1.endpoints.ingest.ingest_batch") as mock_batch:
            mock_batch.side_effect = HTTPException(
                status_code=422, detail="Validation failed"
            )

            with pytest.raises(HTTPException) as exc_info:
                await ingest_single(sample_message, mock_db, mock_api_key)

            assert exc_info.value.status_code == 422
            assert "Validation failed" in str(exc_info.value.detail)


class TestIngestionStatus:
    """Test ingestion status endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        db.messages = Mock()
        db.sessions = Mock()
        db.projects = Mock()
        db.ingestion_logs = Mock()
        return db

    @pytest.fixture
    def mock_api_key(self):
        """Create mock API key."""
        return "test-api-key"

    @pytest.mark.asyncio
    async def test_ingestion_status_success(self, mock_db, mock_api_key):
        """Test successful status retrieval."""
        # Mock collection counts
        mock_db.messages.estimated_document_count = AsyncMock(return_value=1000)
        mock_db.sessions.estimated_document_count = AsyncMock(return_value=50)
        mock_db.projects.estimated_document_count = AsyncMock(return_value=5)

        # Mock recent ingestion logs
        recent_logs = [
            {
                "timestamp": datetime.now(UTC),
                "messages_processed": 10,
                "duration_ms": 500,
            },
            {
                "timestamp": datetime.now(UTC),
                "messages_processed": 5,
                "duration_ms": 200,
            },
        ]

        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=recent_logs)
        mock_db.ingestion_logs.find.return_value = mock_cursor

        result = await ingestion_status(mock_db, mock_api_key)

        assert result["status"] == "operational"
        assert result["statistics"]["total_messages"] == 1000
        assert result["statistics"]["total_sessions"] == 50
        assert result["statistics"]["total_projects"] == 5
        assert len(result["recent_ingestions"]) == 2
        assert result["recent_ingestions"][0]["messages_processed"] == 10

    @pytest.mark.asyncio
    async def test_ingestion_status_empty_database(self, mock_db, mock_api_key):
        """Test status with empty database."""
        # Mock zero counts
        mock_db.messages.estimated_document_count = AsyncMock(return_value=0)
        mock_db.sessions.estimated_document_count = AsyncMock(return_value=0)
        mock_db.projects.estimated_document_count = AsyncMock(return_value=0)

        # Mock empty logs
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.ingestion_logs.find.return_value = mock_cursor

        result = await ingestion_status(mock_db, mock_api_key)

        assert result["status"] == "operational"
        assert result["statistics"]["total_messages"] == 0
        assert result["statistics"]["total_sessions"] == 0
        assert result["statistics"]["total_projects"] == 0
        assert result["recent_ingestions"] == []

    @pytest.mark.asyncio
    async def test_ingestion_status_database_error(self, mock_db, mock_api_key):
        """Test status endpoint with database error."""
        mock_db.messages.estimated_document_count = AsyncMock(
            side_effect=Exception("Database error")
        )

        with pytest.raises(Exception, match="Database error"):
            await ingestion_status(mock_db, mock_api_key)

    @pytest.mark.asyncio
    async def test_ingestion_status_logs_query_parameters(self, mock_db, mock_api_key):
        """Test that logs query uses correct parameters."""
        mock_db.messages.estimated_document_count = AsyncMock(return_value=1)
        mock_db.sessions.estimated_document_count = AsyncMock(return_value=1)
        mock_db.projects.estimated_document_count = AsyncMock(return_value=1)

        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.ingestion_logs.find.return_value = mock_cursor

        await ingestion_status(mock_db, mock_api_key)

        # Check find parameters
        mock_db.ingestion_logs.find.assert_called_once_with(
            {}, limit=10, sort=[("timestamp", -1)]
        )


class TestUpdateProjectMetadata:
    """Test background project metadata update task."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        db.messages = Mock()
        db.projects = Mock()
        return db

    @pytest.mark.asyncio
    async def test_update_project_metadata_success(self, mock_db):
        """Test successful project metadata update."""
        project_ids = ["project-1", "project-2"]

        # Mock aggregation results
        aggregation_results = [
            {
                "_id": None,
                "message_count": 25,
                "session_count": ["session-1", "session-2", "session-3"],
            }
        ]

        mock_db.messages.aggregate.return_value.to_list = AsyncMock(
            return_value=aggregation_results
        )
        mock_db.projects.update_one = AsyncMock()

        await update_project_metadata(mock_db, project_ids)

        # Should call aggregate and update for each project
        assert mock_db.messages.aggregate.call_count == len(project_ids)
        assert mock_db.projects.update_one.call_count == len(project_ids)

        # Check update call structure
        update_call = mock_db.projects.update_one.call_args_list[0]
        assert update_call[0][0] == {"_id": "project-1"}
        update_data = update_call[0][1]["$set"]
        assert update_data["stats.message_count"] == 25
        assert update_data["stats.session_count"] == 3  # len of session_count array

    @pytest.mark.asyncio
    async def test_update_project_metadata_no_results(self, mock_db):
        """Test project metadata update with no aggregation results."""
        project_ids = ["empty-project"]

        # Mock empty aggregation results
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(return_value=[])
        mock_db.projects.update_one = AsyncMock()

        await update_project_metadata(mock_db, project_ids)

        # Should call aggregate but not update since no results
        mock_db.messages.aggregate.assert_called_once()
        mock_db.projects.update_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_project_metadata_empty_project_list(self, mock_db):
        """Test project metadata update with empty project list."""
        project_ids = []

        await update_project_metadata(mock_db, project_ids)

        # Should not call any database operations
        mock_db.messages.aggregate.assert_not_called()
        mock_db.projects.update_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_project_metadata_aggregation_error(self, mock_db):
        """Test handling aggregation errors."""
        project_ids = ["error-project"]

        mock_db.messages.aggregate.side_effect = Exception("Aggregation failed")
        mock_db.projects.update_one = AsyncMock()

        # Should not raise exception, should handle gracefully
        await update_project_metadata(mock_db, project_ids)

        # Update should not be called due to error
        mock_db.projects.update_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_project_metadata_update_error(self, mock_db):
        """Test handling update errors."""
        project_ids = ["update-error-project"]

        aggregation_results = [
            {"_id": None, "message_count": 5, "session_count": ["s1"]}
        ]
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(
            return_value=aggregation_results
        )
        mock_db.projects.update_one = AsyncMock(side_effect=Exception("Update failed"))

        # Should not raise exception, should handle gracefully
        await update_project_metadata(mock_db, project_ids)

    @pytest.mark.asyncio
    async def test_update_project_metadata_aggregation_pipeline_structure(
        self, mock_db
    ):
        """Test aggregation pipeline structure."""
        project_ids = ["test-project"]

        mock_db.messages.aggregate.return_value.to_list = AsyncMock(return_value=[])

        await update_project_metadata(mock_db, project_ids)

        # Check pipeline structure
        pipeline_call = mock_db.messages.aggregate.call_args[0][0]

        # Should have match and group stages
        assert any("$match" in stage for stage in pipeline_call)
        assert any("$group" in stage for stage in pipeline_call)

        # Match stage should filter by projectId
        match_stage = next(
            stage["$match"] for stage in pipeline_call if "$match" in stage
        )
        assert match_stage["projectId"] == "test-project"


class TestBatchSizeValidation:
    """Test batch size validation logic."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        return Mock()

    @pytest.fixture
    def mock_api_key(self):
        """Create mock API key."""
        return "test-api-key"

    @pytest.mark.asyncio
    async def test_batch_size_endpoint_validation(self, mock_db, mock_api_key):
        """Test endpoint-level batch size validation."""
        # Test the endpoint validation logic by creating a mock request object
        message = MessageIngest(
            uuid="test-uuid",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="test-session",
            message={"content": "Test"},
        )

        # Create mock request that bypasses Pydantic for testing endpoint logic
        class MockLargeRequest:
            def __init__(self, size):
                self.messages = [message] * size
                self.todos = []
                self.config = None
                self.overwrite_mode = False

        background_tasks = BackgroundTasks()

        # Test exactly 1000 (should pass)
        request_1000 = MockLargeRequest(1000)
        stats = IngestStats()

        with patch(
            "app.api.api_v1.endpoints.ingest.IngestService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service.ingest_messages = AsyncMock(return_value=stats)
            mock_service_class.return_value = mock_service

            result = await ingest_batch(
                request_1000, background_tasks, mock_db, mock_api_key
            )
            assert result.success is True

        # Test 1001 (should fail)
        request_1001 = MockLargeRequest(1001)

        with pytest.raises(HTTPException) as exc_info:
            await ingest_batch(request_1001, background_tasks, mock_db, mock_api_key)

        assert exc_info.value.status_code == 400
        assert "exceeds maximum" in str(exc_info.value.detail)


class TestEndpointIntegration:
    """Test endpoint integration scenarios."""

    @pytest.fixture
    def sample_message(self):
        """Create sample message."""
        return MessageIngest(
            uuid="integration-uuid",
            type="assistant",
            timestamp=datetime.now(UTC),
            sessionId="integration-session",
            message={"content": [{"type": "text", "text": "Integration test"}]},
        )

    @pytest.mark.asyncio
    async def test_single_to_batch_conversion(self, sample_message):
        """Test that single message endpoint correctly converts to batch format."""
        mock_db = Mock()
        mock_api_key = "test-key"

        stats = IngestStats(messages_received=1, messages_processed=1)
        expected_response = BatchIngestResponse(
            success=True, stats=stats, message="Success"
        )

        with patch("app.api.api_v1.endpoints.ingest.ingest_batch") as mock_batch:
            mock_batch.return_value = expected_response

            await ingest_single(sample_message, mock_db, mock_api_key)

            # Verify conversion
            mock_batch.assert_called_once()
            call_args = mock_batch.call_args[0]

            batch_request = call_args[0]
            assert len(batch_request.messages) == 1
            assert batch_request.messages[0].uuid == "integration-uuid"
            assert batch_request.messages[0].type == "assistant"

    @pytest.mark.asyncio
    async def test_background_task_scheduling(self):
        """Test background task scheduling behavior."""
        mock_db = Mock()
        mock_api_key = "test-key"
        background_tasks = BackgroundTasks()

        # Create request with projects to trigger background task
        sample_message = MessageIngest(
            uuid="bg-task-uuid",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="bg-session",
            message={"content": "Background task test"},
        )

        request = BatchIngestRequest(
            messages=[sample_message], todos=[], config=None, overwrite_mode=False
        )

        stats = IngestStats(
            messages_received=1,
            messages_processed=1,
            projects_created=["new-project-id"],
        )

        with patch(
            "app.api.api_v1.endpoints.ingest.IngestService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service.ingest_messages = AsyncMock(return_value=stats)
            mock_service_class.return_value = mock_service

            result = await ingest_batch(
                request, background_tasks, mock_db, mock_api_key
            )

            assert result.success is True
            # BackgroundTasks internals are complex to test directly,
            # but we can verify the main logic path succeeded


class TestErrorHandlingScenarios:
    """Test various error handling scenarios."""

    @pytest.fixture
    def valid_request(self):
        """Create valid request."""
        message = MessageIngest(
            uuid="error-test-uuid",
            type="user",
            timestamp=datetime.now(UTC),
            sessionId="error-session",
            message={"content": "Error test"},
        )
        return BatchIngestRequest(
            messages=[message], todos=[], config=None, overwrite_mode=False
        )

    @pytest.mark.asyncio
    async def test_service_initialization_error(self, valid_request):
        """Test service initialization error handling."""
        mock_db = Mock()
        background_tasks = BackgroundTasks()

        with patch(
            "app.api.api_v1.endpoints.ingest.IngestService"
        ) as mock_service_class:
            mock_service_class.side_effect = Exception("Service init failed")

            with pytest.raises(Exception, match="Service init failed"):
                await ingest_batch(valid_request, background_tasks, mock_db, "api-key")

    @pytest.mark.asyncio
    async def test_different_validation_error_messages(self, valid_request):
        """Test different validation error message formats."""
        mock_db = Mock()
        background_tasks = BackgroundTasks()

        error_messages = [
            "Invalid UUID format",
            "Missing required field: sessionId",
            "Timestamp format invalid",
        ]

        for error_msg in error_messages:
            with patch(
                "app.api.api_v1.endpoints.ingest.IngestService"
            ) as mock_service_class:
                mock_service = Mock()
                mock_service.ingest_messages = AsyncMock(
                    side_effect=ValidationError(error_msg)
                )
                mock_service_class.return_value = mock_service

                with pytest.raises(HTTPException) as exc_info:
                    await ingest_batch(
                        valid_request, background_tasks, mock_db, "api-key"
                    )

                assert exc_info.value.status_code == 422
                assert error_msg in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_service_method_call_parameters(self, valid_request):
        """Test that service method is called with correct parameters."""
        mock_db = Mock()
        background_tasks = BackgroundTasks()
        stats = IngestStats()

        with patch(
            "app.api.api_v1.endpoints.ingest.IngestService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service.ingest_messages = AsyncMock(return_value=stats)
            mock_service_class.return_value = mock_service

            await ingest_batch(valid_request, background_tasks, mock_db, "api-key")

            # Verify service was called with exact parameters
            mock_service.ingest_messages.assert_called_once_with(
                valid_request.messages, overwrite_mode=valid_request.overwrite_mode
            )
