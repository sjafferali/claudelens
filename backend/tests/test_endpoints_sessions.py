"""Tests for sessions API endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.api.api_v1.endpoints.sessions import router
from app.schemas.message import Message
from app.schemas.session import Session, SessionDetail


@pytest.fixture
def test_client():
    """Create a test client with the sessions router."""
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
    app.include_router(router, prefix="/api/v1/sessions")
    return TestClient(app)


@pytest.fixture
def mock_session_service():
    """Mock SessionService for testing."""
    with patch("app.api.api_v1.endpoints.sessions.SessionService") as mock:
        yield mock


@pytest.fixture
def sample_session():
    """Sample session data for testing."""
    return Session(
        id="507f1f77bcf86cd799439011",
        session_id="session123",
        project_id="507f1f77bcf86cd799439012",
        started_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        ended_at=datetime(2025, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
        message_count=10,
        total_cost=0.05,
        summary="Test session summary",
    )


@pytest.fixture
def sample_session_detail():
    """Sample session detail data for testing."""
    return SessionDetail(
        id="507f1f77bcf86cd799439011",
        session_id="session123",
        project_id="507f1f77bcf86cd799439012",
        started_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        ended_at=datetime(2025, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
        message_count=10,
        total_cost=0.05,
        summary="Test session summary",
        messages=[],
    )


@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
    return [
        Message(
            id="507f1f77bcf86cd799439013",
            uuid="msg1",
            session_id="507f1f77bcf86cd799439011",
            type="user",
            content="Test message 1",
            timestamp=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            created_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        ),
        Message(
            id="507f1f77bcf86cd799439014",
            uuid="msg2",
            session_id="507f1f77bcf86cd799439011",
            type="assistant",
            content="Test response 1",
            timestamp=datetime(2025, 1, 1, 10, 1, 0, tzinfo=timezone.utc),
            created_at=datetime(2025, 1, 1, 10, 1, 0, tzinfo=timezone.utc),
        ),
    ]


class TestListSessions:
    """Tests for list sessions endpoint."""

    def test_list_sessions_success(
        self, test_client: TestClient, mock_session_service, sample_session
    ):
        """Test successful session listing."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_sessions.return_value = ([sample_session], 1)
        mock_session_service.return_value = mock_service

        # Make request
        response = test_client.get("/api/v1/sessions/")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["_id"] == sample_session.id
        assert data["has_more"] is False

        # Verify service was called with user_id
        mock_service.list_sessions.assert_called_once_with(
            "test_user_id",
            filter_dict={},
            skip=0,
            limit=20,
            sort_by="started_at",
            sort_order="desc",
        )

    def test_list_sessions_with_project_filter(
        self, test_client: TestClient, mock_session_service, sample_session
    ):
        """Test listing sessions filtered by project."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_sessions.return_value = ([sample_session], 1)
        mock_session_service.return_value = mock_service

        # Make request
        project_id = "507f1f77bcf86cd799439012"
        response = test_client.get(f"/api/v1/sessions/?project_id={project_id}")

        # Verify
        assert response.status_code == 200
        mock_service.list_sessions.assert_called_once_with(
            "test_user_id",
            filter_dict={"projectId": ObjectId(project_id)},
            skip=0,
            limit=20,
            sort_by="started_at",
            sort_order="desc",
        )

    def test_list_sessions_invalid_project_id(
        self, test_client: TestClient, mock_session_service
    ):
        """Test listing sessions with invalid project ID."""
        response = test_client.get("/api/v1/sessions/?project_id=invalid")
        assert response.status_code == 400
        assert "Invalid project ID" in response.json()["detail"]

    def test_list_sessions_with_search(
        self, test_client: TestClient, mock_session_service, sample_session
    ):
        """Test listing sessions with search query."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_sessions.return_value = ([sample_session], 1)
        mock_session_service.return_value = mock_service

        # Make request
        response = test_client.get("/api/v1/sessions/?search=test")

        # Verify
        assert response.status_code == 200
        mock_service.list_sessions.assert_called_once_with(
            "test_user_id",
            filter_dict={"$text": {"$search": "test"}},
            skip=0,
            limit=20,
            sort_by="started_at",
            sort_order="desc",
        )

    def test_list_sessions_with_date_filters(
        self, test_client: TestClient, mock_session_service, sample_session
    ):
        """Test listing sessions with date filters."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_sessions.return_value = ([sample_session], 1)
        mock_session_service.return_value = mock_service

        # Make request
        start_date = "2025-01-01T00:00:00"
        end_date = "2025-01-31T23:59:59"
        response = test_client.get(
            f"/api/v1/sessions/?start_date={start_date}&end_date={end_date}"
        )

        # Verify
        assert response.status_code == 200
        mock_service.list_sessions.assert_called_once()
        call_args = mock_service.list_sessions.call_args
        assert call_args.kwargs["filter_dict"]["startedAt"]["$gte"]
        assert call_args.kwargs["filter_dict"]["startedAt"]["$lte"]


class TestGetSession:
    """Tests for get session endpoint."""

    def test_get_session_success(
        self, test_client: TestClient, mock_session_service, sample_session_detail
    ):
        """Test successful session retrieval."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_session.return_value = sample_session_detail
        mock_session_service.return_value = mock_service

        # Make request
        session_id = "507f1f77bcf86cd799439011"
        response = test_client.get(f"/api/v1/sessions/{session_id}")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["_id"] == sample_session_detail.id
        assert data["session_id"] == sample_session_detail.session_id

        # Verify service was called with user_id
        mock_service.get_session.assert_called_once_with(
            "test_user_id", session_id, include_messages=False
        )

    def test_get_session_not_found(self, test_client: TestClient, mock_session_service):
        """Test session retrieval when session not found."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_session.return_value = None
        mock_session_service.return_value = mock_service

        # Make request
        session_id = "507f1f77bcf86cd799439011"
        response = test_client.get(f"/api/v1/sessions/{session_id}")

        # Verify
        assert response.status_code == 404

    def test_get_session_with_messages(
        self, test_client: TestClient, mock_session_service, sample_session_detail
    ):
        """Test session retrieval with messages included."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_session.return_value = sample_session_detail
        mock_session_service.return_value = mock_service

        # Make request
        session_id = "507f1f77bcf86cd799439011"
        response = test_client.get(
            f"/api/v1/sessions/{session_id}?include_messages=true"
        )

        # Verify
        assert response.status_code == 200
        mock_service.get_session.assert_called_once_with(
            "test_user_id", session_id, include_messages=True
        )


class TestGetSessionMessages:
    """Tests for get session messages endpoint."""

    def test_get_session_messages_success(
        self,
        test_client: TestClient,
        mock_session_service,
        sample_messages,
        sample_session,
    ):
        """Test successful session messages retrieval."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_session.return_value = sample_session
        mock_service.get_session_messages.return_value = sample_messages
        mock_session_service.return_value = mock_service

        # Make request
        session_id = "507f1f77bcf86cd799439011"
        response = test_client.get(f"/api/v1/sessions/{session_id}/messages")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert "session" in data
        assert "messages" in data
        assert len(data["messages"]) == len(sample_messages)
        assert data["skip"] == 0
        assert data["limit"] == 50

        # Verify service was called with user_id
        mock_service.get_session.assert_called_once_with("test_user_id", session_id)
        mock_service.get_session_messages.assert_called_once_with(
            "test_user_id", session_id, skip=0, limit=50
        )

    def test_get_session_messages_with_pagination(
        self,
        test_client: TestClient,
        mock_session_service,
        sample_messages,
        sample_session,
    ):
        """Test session messages retrieval with pagination."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_session.return_value = sample_session
        mock_service.get_session_messages.return_value = sample_messages
        mock_session_service.return_value = mock_service

        # Make request
        session_id = "507f1f77bcf86cd799439011"
        response = test_client.get(
            f"/api/v1/sessions/{session_id}/messages?skip=10&limit=50"
        )

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 10
        assert data["limit"] == 50

        # Verify service calls
        mock_service.get_session.assert_called_once_with("test_user_id", session_id)
        mock_service.get_session_messages.assert_called_once_with(
            "test_user_id", session_id, skip=10, limit=50
        )


class TestGenerateSessionSummary:
    """Tests for generate session summary endpoint."""

    def test_generate_summary_success(
        self, test_client: TestClient, mock_session_service
    ):
        """Test successful summary generation."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.generate_summary.return_value = "Generated summary"
        mock_session_service.return_value = mock_service

        # Make request
        session_id = "507f1f77bcf86cd799439011"
        response = test_client.post(f"/api/v1/sessions/{session_id}/generate-summary")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == "Generated summary"

        # Verify service was called with user_id
        mock_service.generate_summary.assert_called_once_with(
            "test_user_id", session_id
        )

    def test_generate_summary_not_found(
        self, test_client: TestClient, mock_session_service
    ):
        """Test summary generation for non-existent session."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.generate_summary.return_value = None
        mock_session_service.return_value = mock_service

        # Make request
        session_id = "507f1f77bcf86cd799439011"
        response = test_client.post(f"/api/v1/sessions/{session_id}/generate-summary")

        # Verify
        assert response.status_code == 404


class TestGetMessageThread:
    """Tests for get message thread endpoint."""

    def test_get_message_thread_success(
        self, test_client: TestClient, mock_session_service, sample_messages
    ):
        """Test successful message thread retrieval."""
        # Setup mock thread response
        thread_response = {
            "target": sample_messages[0],
            "ancestors": [],
            "descendants": [],
        }
        mock_service = AsyncMock()
        mock_service.get_message_thread.return_value = thread_response
        mock_session_service.return_value = mock_service

        # Make request
        session_id = "507f1f77bcf86cd799439011"
        message_uuid = "msg1"
        response = test_client.get(
            f"/api/v1/sessions/{session_id}/thread/{message_uuid}"
        )

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert "target" in data
        assert "ancestors" in data
        assert "descendants" in data

        # Verify service was called with user_id
        mock_service.get_message_thread.assert_called_once_with(
            "test_user_id", session_id, message_uuid, 10
        )

    def test_get_message_thread_not_found(
        self, test_client: TestClient, mock_session_service
    ):
        """Test message thread retrieval for non-existent message."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_message_thread.return_value = None
        mock_session_service.return_value = mock_service

        # Make request
        session_id = "507f1f77bcf86cd799439011"
        message_uuid = "nonexistent"
        response = test_client.get(
            f"/api/v1/sessions/{session_id}/thread/{message_uuid}"
        )

        # Verify
        assert response.status_code == 404

    def test_get_message_thread_with_custom_depth(
        self, test_client: TestClient, mock_session_service
    ):
        """Test message thread retrieval with custom depth."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_message_thread.return_value = {
            "target": None,
            "ancestors": [],
            "descendants": [],
        }
        mock_session_service.return_value = mock_service

        # Make request
        session_id = "507f1f77bcf86cd799439011"
        message_uuid = "msg1"
        response = test_client.get(
            f"/api/v1/sessions/{session_id}/thread/{message_uuid}?depth=10"
        )

        # Verify
        assert response.status_code == 200
        mock_service.get_message_thread.assert_called_once_with(
            "test_user_id", session_id, message_uuid, 10
        )
