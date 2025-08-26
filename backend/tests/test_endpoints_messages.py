"""Tests for messages API endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.api_v1.endpoints.messages import router
from app.schemas.message import Message, MessageDetail


@pytest.fixture
def test_client():
    """Create a test client with the messages router."""
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    from app.api.dependencies import get_db
    from app.core.exceptions import ClaudeLensException

    app = FastAPI()

    # Add exception handler
    @app.exception_handler(ClaudeLensException)
    async def claudelens_exception_handler(request: Request, exc: ClaudeLensException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_type": exc.error_type,
            },
        )

    # Mock the database dependency
    async def mock_get_db():
        return AsyncMock()

    # Mock the auth dependency to return a test user ID
    from app.api.dependencies import verify_api_key_header

    async def mock_verify_api_key():
        return "test_user_id"

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[verify_api_key_header] = mock_verify_api_key
    app.include_router(router, prefix="/api/v1/messages")
    return TestClient(app)


@pytest.fixture
def mock_message_service():
    """Mock MessageService for testing."""
    with patch("app.api.api_v1.endpoints.messages.MessageService") as mock:
        yield mock


@pytest.fixture
def sample_message():
    """Sample message data for testing."""
    return Message(
        id="507f1f77bcf86cd799439011",
        uuid="msg1",
        type="user",
        session_id="session123",
        content="Test message content",
        timestamp=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        created_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        model="claude-3-sonnet",
    )


@pytest.fixture
def sample_message_detail():
    """Sample message detail data for testing."""
    return MessageDetail(
        id="507f1f77bcf86cd799439011",
        uuid="msg1",
        type="user",
        session_id="session123",
        content="Test message content",
        timestamp=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        created_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        model="claude-3-sonnet",
        usage={"input_tokens": 100, "output_tokens": 200},
        cost_usd=0.005,
    )


class TestListMessages:
    """Tests for list messages endpoint."""

    def test_list_messages_success(
        self, test_client: TestClient, mock_message_service, sample_message
    ):
        """Test successful message listing."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_messages.return_value = ([sample_message], 1)
        mock_message_service.return_value = mock_service

        # Make request
        response = test_client.get("/api/v1/messages/")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["_id"] == sample_message.id
        assert data["has_more"] is False

        # Verify service was called with user_id
        mock_service.list_messages.assert_called_once_with(
            "test_user_id", filter_dict={}, skip=0, limit=50, sort_order="asc"
        )

    def test_list_messages_with_session_filter(
        self, test_client: TestClient, mock_message_service, sample_message
    ):
        """Test listing messages filtered by session."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_messages.return_value = ([sample_message], 1)
        mock_message_service.return_value = mock_service

        # Make request
        session_id = "test_session"
        response = test_client.get(f"/api/v1/messages/?session_id={session_id}")

        # Verify
        assert response.status_code == 200
        mock_service.list_messages.assert_called_once_with(
            "test_user_id",
            filter_dict={"sessionId": session_id},
            skip=0,
            limit=50,
            sort_order="asc",
        )

    def test_list_messages_with_type_filter(
        self, test_client: TestClient, mock_message_service, sample_message
    ):
        """Test listing messages filtered by type."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_messages.return_value = ([sample_message], 1)
        mock_message_service.return_value = mock_service

        # Make request
        message_type = "user"
        response = test_client.get(f"/api/v1/messages/?type={message_type}")

        # Verify
        assert response.status_code == 200
        mock_service.list_messages.assert_called_once_with(
            "test_user_id",
            filter_dict={"type": message_type},
            skip=0,
            limit=50,
            sort_order="asc",
        )

    def test_list_messages_with_model_filter(
        self, test_client: TestClient, mock_message_service, sample_message
    ):
        """Test listing messages filtered by model."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_messages.return_value = ([sample_message], 1)
        mock_message_service.return_value = mock_service

        # Make request
        model = "claude-3-sonnet"
        response = test_client.get(f"/api/v1/messages/?model={model}")

        # Verify
        assert response.status_code == 200
        mock_service.list_messages.assert_called_once_with(
            "test_user_id",
            filter_dict={"model": model},
            skip=0,
            limit=50,
            sort_order="asc",
        )

    def test_list_messages_with_multiple_filters(
        self, test_client: TestClient, mock_message_service, sample_message
    ):
        """Test listing messages with multiple filters."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_messages.return_value = ([sample_message], 1)
        mock_message_service.return_value = mock_service

        # Make request
        response = test_client.get(
            "/api/v1/messages/?session_id=test_session&type=user&model=claude-3-sonnet"
        )

        # Verify
        assert response.status_code == 200
        mock_service.list_messages.assert_called_once_with(
            "test_user_id",
            filter_dict={
                "sessionId": "test_session",
                "type": "user",
                "model": "claude-3-sonnet",
            },
            skip=0,
            limit=50,
            sort_order="asc",
        )

    def test_list_messages_with_pagination(
        self, test_client: TestClient, mock_message_service, sample_message
    ):
        """Test listing messages with pagination."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_messages.return_value = ([sample_message], 100)
        mock_message_service.return_value = mock_service

        # Make request
        response = test_client.get("/api/v1/messages/?skip=20&limit=10")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 20
        assert data["limit"] == 10
        assert data["has_more"] is True  # 20 + 10 < 100

        # Verify service call
        mock_service.list_messages.assert_called_once_with(
            "test_user_id", filter_dict={}, skip=20, limit=10, sort_order="asc"
        )

    def test_list_messages_with_sort_order(
        self, test_client: TestClient, mock_message_service, sample_message
    ):
        """Test listing messages with sort order."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_messages.return_value = ([sample_message], 1)
        mock_message_service.return_value = mock_service

        # Make request
        response = test_client.get("/api/v1/messages/?sort_order=desc")

        # Verify
        assert response.status_code == 200
        mock_service.list_messages.assert_called_once_with(
            "test_user_id", filter_dict={}, skip=0, limit=50, sort_order="desc"
        )

    def test_list_messages_invalid_sort_order(
        self, test_client: TestClient, mock_message_service
    ):
        """Test listing messages with invalid sort order."""
        response = test_client.get("/api/v1/messages/?sort_order=invalid")
        assert response.status_code == 422  # Validation error

    def test_list_messages_invalid_limit(
        self, test_client: TestClient, mock_message_service
    ):
        """Test listing messages with invalid limit."""
        # Test limit too low
        response = test_client.get("/api/v1/messages/?limit=0")
        assert response.status_code == 422

        # Test limit too high
        response = test_client.get("/api/v1/messages/?limit=2000")
        assert response.status_code == 422

    def test_list_messages_invalid_skip(
        self, test_client: TestClient, mock_message_service
    ):
        """Test listing messages with invalid skip."""
        response = test_client.get("/api/v1/messages/?skip=-1")
        assert response.status_code == 422

    def test_list_messages_empty_result(
        self, test_client: TestClient, mock_message_service
    ):
        """Test listing messages with empty result."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_messages.return_value = ([], 0)
        mock_message_service.return_value = mock_service

        # Make request
        response = test_client.get("/api/v1/messages/")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0
        assert data["has_more"] is False


class TestGetMessage:
    """Tests for get message endpoint."""

    def test_get_message_success(
        self, test_client: TestClient, mock_message_service, sample_message_detail
    ):
        """Test successful message retrieval."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_message.return_value = sample_message_detail
        mock_message_service.return_value = mock_service

        # Make request
        message_id = sample_message_detail.id
        response = test_client.get(f"/api/v1/messages/{message_id}")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["_id"] == message_id
        assert data["content"] == sample_message_detail.content

        # Verify service was called with user_id
        mock_service.get_message.assert_called_once_with("test_user_id", message_id)

    def test_get_message_not_found(self, test_client: TestClient, mock_message_service):
        """Test getting non-existent message."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_message.return_value = None
        mock_message_service.return_value = mock_service

        # Make request
        response = test_client.get("/api/v1/messages/nonexistent")

        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestGetMessageByUuid:
    """Tests for get message by UUID endpoint."""

    def test_get_message_by_uuid_success(
        self, test_client: TestClient, mock_message_service, sample_message_detail
    ):
        """Test successful message retrieval by UUID."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_message_by_uuid.return_value = sample_message_detail
        mock_message_service.return_value = mock_service

        # Make request
        uuid = sample_message_detail.uuid
        response = test_client.get(f"/api/v1/messages/uuid/{uuid}")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == uuid
        assert data["content"] == sample_message_detail.content

        # Verify service was called with user_id
        mock_service.get_message_by_uuid.assert_called_once_with("test_user_id", uuid)

    def test_get_message_by_uuid_not_found(
        self, test_client: TestClient, mock_message_service
    ):
        """Test getting non-existent message by UUID."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_message_by_uuid.return_value = None
        mock_message_service.return_value = mock_service

        # Make request
        response = test_client.get("/api/v1/messages/uuid/nonexistent")

        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestGetMessageContext:
    """Tests for get message context endpoint."""

    def test_get_message_context_success(
        self, test_client: TestClient, mock_message_service
    ):
        """Test successful message context retrieval."""
        # Setup mock
        context_data = {
            "target": {"id": "msg1", "content": "Test message"},
            "before": [{"id": "before1", "content": "Before message"}],
            "after": [{"id": "after1", "content": "After message"}],
            "session_id": "test_session",
        }
        mock_service = AsyncMock()
        mock_service.get_message_context.return_value = context_data
        mock_message_service.return_value = mock_service

        # Make request
        message_id = "msg1"
        response = test_client.get(f"/api/v1/messages/{message_id}/context")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["target"]["id"] == "msg1"
        assert len(data["before"]) == 1
        assert len(data["after"]) == 1

        # Verify service was called with user_id
        mock_service.get_message_context.assert_called_once_with(
            "test_user_id", message_id, 5, 5
        )

    def test_get_message_context_with_custom_params(
        self, test_client: TestClient, mock_message_service
    ):
        """Test getting message context with custom before/after parameters."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_message_context.return_value = {
            "target": {},
            "before": [],
            "after": [],
            "session_id": "test_session",
        }
        mock_message_service.return_value = mock_service

        # Make request
        message_id = "msg1"
        response = test_client.get(
            f"/api/v1/messages/{message_id}/context?before=10&after=15"
        )

        # Verify
        assert response.status_code == 200
        mock_service.get_message_context.assert_called_once_with(
            "test_user_id", message_id, 10, 15
        )

    def test_get_message_context_invalid_params(
        self, test_client: TestClient, mock_message_service
    ):
        """Test getting message context with invalid parameters."""
        message_id = "msg1"

        # Test negative before
        response = test_client.get(f"/api/v1/messages/{message_id}/context?before=-1")
        assert response.status_code == 422

        # Test too large after
        response = test_client.get(f"/api/v1/messages/{message_id}/context?after=100")
        assert response.status_code == 422

    def test_get_message_context_not_found(
        self, test_client: TestClient, mock_message_service
    ):
        """Test getting context for non-existent message."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_message_context.return_value = None
        mock_message_service.return_value = mock_service

        # Make request
        response = test_client.get("/api/v1/messages/nonexistent/context")

        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestMessageCostOperations:
    """Tests for message cost-related endpoints."""

    def test_update_message_cost_success(
        self, test_client: TestClient, mock_message_service
    ):
        """Test successful message cost update."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.update_message_cost.return_value = True
        mock_message_service.return_value = mock_service

        # Make request
        message_id = "msg1"
        cost_usd = 0.005
        response = test_client.patch(
            f"/api/v1/messages/{message_id}/cost?cost_usd={cost_usd}"
        )

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message_id"] == message_id
        assert data["cost_usd"] == cost_usd

        # Verify service was called with user_id
        mock_service.update_message_cost.assert_called_once_with(
            "test_user_id", message_id, cost_usd
        )

    def test_update_message_cost_not_found(
        self, test_client: TestClient, mock_message_service
    ):
        """Test updating cost for non-existent message."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.update_message_cost.return_value = False
        mock_message_service.return_value = mock_service

        # Make request
        message_id = "nonexistent"
        cost_usd = 0.005
        response = test_client.patch(
            f"/api/v1/messages/{message_id}/cost?cost_usd={cost_usd}"
        )

        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_message_cost_invalid_cost(
        self, test_client: TestClient, mock_message_service
    ):
        """Test updating message cost with invalid cost value."""
        message_id = "msg1"

        # Test missing cost parameter
        response = test_client.patch(f"/api/v1/messages/{message_id}/cost")
        assert response.status_code == 422

    def test_batch_update_costs_success(
        self, test_client: TestClient, mock_message_service
    ):
        """Test successful batch cost update."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.batch_update_costs.return_value = 2
        mock_message_service.return_value = mock_service

        # Make request
        cost_updates = {"msg1": 0.005, "msg2": 0.010}
        response = test_client.post(
            "/api/v1/messages/batch-update-costs", json=cost_updates
        )

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["updated_count"] == 2
        assert data["requested_count"] == 2

        # Verify service was called with user_id
        mock_service.batch_update_costs.assert_called_once_with(
            "test_user_id", cost_updates
        )

    def test_batch_update_costs_partial_success(
        self, test_client: TestClient, mock_message_service
    ):
        """Test batch cost update with partial success."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.batch_update_costs.return_value = 1  # Only 1 out of 2 updated
        mock_message_service.return_value = mock_service

        # Make request
        cost_updates = {"msg1": 0.005, "msg2": 0.010}
        response = test_client.post(
            "/api/v1/messages/batch-update-costs", json=cost_updates
        )

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["updated_count"] == 1
        assert data["requested_count"] == 2

    def test_batch_update_costs_empty_updates(
        self, test_client: TestClient, mock_message_service
    ):
        """Test batch cost update with empty updates."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.batch_update_costs.return_value = 0
        mock_message_service.return_value = mock_service

        # Make request
        cost_updates = {}
        response = test_client.post(
            "/api/v1/messages/batch-update-costs", json=cost_updates
        )

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["updated_count"] == 0
        assert data["requested_count"] == 0


class TestCalculateMessageCosts:
    """Tests for calculate message costs endpoint."""

    def test_calculate_costs_no_parameters(
        self, test_client: TestClient, mock_message_service
    ):
        """Test calculate costs without session_id or message_ids."""
        response = test_client.post("/api/v1/messages/calculate-costs")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Either session_id or message_ids must be provided" in data["error"]
