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

    app.dependency_overrides[get_db] = mock_get_db
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
        mock_service.list_sessions.assert_called_once()
        call_args = mock_service.list_sessions.call_args
        assert call_args[1]["filter_dict"]["projectId"] == ObjectId(project_id)

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
        mock_service.list_sessions.assert_called_once()
        call_args = mock_service.list_sessions.call_args
        assert "$text" in call_args[1]["filter_dict"]
        assert call_args[1]["filter_dict"]["$text"]["$search"] == "test"

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
        assert "startedAt" in call_args[1]["filter_dict"]
        assert "$gte" in call_args[1]["filter_dict"]["startedAt"]
        assert "$lte" in call_args[1]["filter_dict"]["startedAt"]

    def test_list_sessions_with_pagination(
        self, test_client: TestClient, mock_session_service, sample_session
    ):
        """Test listing sessions with pagination."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_sessions.return_value = ([sample_session], 100)
        mock_session_service.return_value = mock_service

        # Make request
        response = test_client.get("/api/v1/sessions/?skip=20&limit=10")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 20
        assert data["limit"] == 10
        assert data["has_more"] is True  # 20 + 10 < 100

    def test_list_sessions_with_sorting(
        self, test_client: TestClient, mock_session_service, sample_session
    ):
        """Test listing sessions with sorting."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_sessions.return_value = ([sample_session], 1)
        mock_session_service.return_value = mock_service

        # Make request
        response = test_client.get(
            "/api/v1/sessions/?sort_by=total_cost&sort_order=asc"
        )

        # Verify
        assert response.status_code == 200
        mock_service.list_sessions.assert_called_once()
        call_args = mock_service.list_sessions.call_args
        assert call_args[1]["sort_by"] == "total_cost"
        assert call_args[1]["sort_order"] == "asc"

    def test_list_sessions_invalid_sort_field(
        self, test_client: TestClient, mock_session_service
    ):
        """Test listing sessions with invalid sort field."""
        response = test_client.get("/api/v1/sessions/?sort_by=invalid_field")
        assert response.status_code == 422  # Validation error


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
        session_id = sample_session_detail.id
        response = test_client.get(f"/api/v1/sessions/{session_id}")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["_id"] == session_id
        assert data["summary"] == sample_session_detail.summary

    def test_get_session_with_messages(
        self, test_client: TestClient, mock_session_service, sample_session_detail
    ):
        """Test getting session with messages included."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_session.return_value = sample_session_detail
        mock_session_service.return_value = mock_service

        # Make request
        session_id = sample_session_detail.id
        response = test_client.get(
            f"/api/v1/sessions/{session_id}?include_messages=true"
        )

        # Verify
        assert response.status_code == 200
        mock_service.get_session.assert_called_once_with(
            session_id, include_messages=True
        )

    def test_get_session_not_found(self, test_client: TestClient, mock_session_service):
        """Test getting non-existent session."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_session.return_value = None
        mock_session_service.return_value = mock_service

        # Make request
        response = test_client.get("/api/v1/sessions/nonexistent")

        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestGetSessionMessages:
    """Tests for get session messages endpoint."""

    def test_get_session_messages_success(
        self,
        test_client: TestClient,
        mock_session_service,
        sample_session_detail,
        sample_messages,
    ):
        """Test successful retrieval of session messages."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_session.return_value = sample_session_detail
        mock_service.get_session_messages.return_value = sample_messages
        mock_session_service.return_value = mock_service

        # Make request
        session_id = sample_session_detail.id
        response = test_client.get(f"/api/v1/sessions/{session_id}/messages")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["session"]["_id"] == session_id
        assert len(data["messages"]) == 2
        assert data["messages"][0]["content"] == "Test message 1"

    def test_get_session_messages_with_pagination(
        self,
        test_client: TestClient,
        mock_session_service,
        sample_session_detail,
        sample_messages,
    ):
        """Test getting session messages with pagination."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_session.return_value = sample_session_detail
        mock_service.get_session_messages.return_value = sample_messages
        mock_session_service.return_value = mock_service

        # Make request
        session_id = sample_session_detail.id
        response = test_client.get(
            f"/api/v1/sessions/{session_id}/messages?skip=10&limit=20"
        )

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 10
        assert data["limit"] == 20
        mock_service.get_session_messages.assert_called_once_with(
            session_id, skip=10, limit=20
        )

    def test_get_session_messages_session_not_found(
        self, test_client: TestClient, mock_session_service
    ):
        """Test getting messages for non-existent session."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_session.return_value = None
        mock_session_service.return_value = mock_service

        # Make request
        response = test_client.get("/api/v1/sessions/nonexistent/messages")

        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestGetMessageThread:
    """Tests for get message thread endpoint."""

    def test_get_message_thread_success(
        self, test_client: TestClient, mock_session_service
    ):
        """Test successful retrieval of message thread."""
        # Setup mock
        thread_data = {
            "message": {"uuid": "msg1", "content": "Test message"},
            "parents": [{"uuid": "parent1", "content": "Parent message"}],
            "children": [{"uuid": "child1", "content": "Child message"}],
        }
        mock_service = AsyncMock()
        mock_service.get_message_thread.return_value = thread_data
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
        assert data["message"]["uuid"] == "msg1"
        assert len(data["parents"]) == 1
        assert len(data["children"]) == 1

    def test_get_message_thread_with_depth(
        self, test_client: TestClient, mock_session_service
    ):
        """Test getting message thread with custom depth."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_message_thread.return_value = {"message": {}}
        mock_session_service.return_value = mock_service

        # Make request
        session_id = "507f1f77bcf86cd799439011"
        message_uuid = "msg1"
        response = test_client.get(
            f"/api/v1/sessions/{session_id}/thread/{message_uuid}?depth=5"
        )

        # Verify
        assert response.status_code == 200
        mock_service.get_message_thread.assert_called_once_with(
            session_id, message_uuid, 5
        )

    def test_get_message_thread_not_found(
        self, test_client: TestClient, mock_session_service
    ):
        """Test getting non-existent message thread."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_message_thread.return_value = None
        mock_session_service.return_value = mock_service

        # Make request
        response = test_client.get("/api/v1/sessions/session1/thread/nonexistent")

        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestGenerateSessionSummary:
    """Tests for generate session summary endpoint."""

    def test_generate_summary_success(
        self, test_client: TestClient, mock_session_service
    ):
        """Test successful summary generation."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.generate_summary.return_value = "Generated summary text"
        mock_session_service.return_value = mock_service

        # Make request
        session_id = "507f1f77bcf86cd799439011"
        response = test_client.post(f"/api/v1/sessions/{session_id}/generate-summary")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["summary"] == "Generated summary text"

    def test_generate_summary_session_not_found(
        self, test_client: TestClient, mock_session_service
    ):
        """Test generating summary for non-existent session."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.generate_summary.return_value = None
        mock_session_service.return_value = mock_service

        # Make request
        response = test_client.post("/api/v1/sessions/nonexistent/generate-summary")

        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
