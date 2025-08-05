"""Tests for projects API endpoints."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.api.api_v1.endpoints.projects import router
from app.models.project import ProjectInDB, ProjectStats, PyObjectId
from app.schemas.project import ProjectWithStats


@pytest.fixture
def mock_db():
    """Create a mock database."""
    return MagicMock()


@pytest.fixture
def mock_project_service():
    """Create a mock project service."""
    with patch("app.api.api_v1.endpoints.projects.ProjectService") as mock:
        yield mock


@pytest.fixture
def test_client():
    """Create a test client with the projects router."""
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

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

    app.include_router(router, prefix="/projects")
    return TestClient(app)


@pytest.fixture
def sample_project_with_stats():
    """Create a sample project with statistics."""
    return ProjectWithStats(
        _id="507f1f77bcf86cd799439011",
        name="Test Project",
        path="/projects/test",
        description="A test project",
        stats={"message_count": 100, "session_count": 10},
        createdAt=datetime.now(UTC),
        updatedAt=datetime.now(UTC),
    )


@pytest.fixture
def sample_project_in_db():
    """Create a sample ProjectInDB instance."""
    return ProjectInDB(
        id=PyObjectId("507f1f77bcf86cd799439011"),
        name="Test Project",
        path="/projects/test",
        description="A test project",
        stats=ProjectStats(message_count=0, session_count=0),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestProjectsEndpoints:
    """Test cases for projects API endpoints."""

    @pytest.mark.asyncio
    async def test_list_projects_empty(
        self, test_client, mock_project_service, mock_db
    ):
        """Test listing projects when none exist."""
        # Setup
        mock_service_instance = MagicMock()
        mock_service_instance.list_projects = AsyncMock(return_value=([], 0))
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request with mock db
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.get("/projects/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["skip"] == 0
        assert data["limit"] == 20
        assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_list_projects_with_data(
        self, test_client, mock_project_service, mock_db, sample_project_with_stats
    ):
        """Test listing projects with data."""
        # Setup
        mock_service_instance = MagicMock()
        mock_service_instance.list_projects = AsyncMock(
            return_value=([sample_project_with_stats], 1)
        )
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.get("/projects/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test Project"
        assert data["items"][0]["stats"]["message_count"] == 100
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_list_projects_with_pagination(
        self, test_client, mock_project_service, mock_db
    ):
        """Test listing projects with pagination parameters."""
        # Setup
        mock_service_instance = MagicMock()
        mock_service_instance.list_projects = AsyncMock(return_value=([], 50))
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.get("/projects/?skip=20&limit=10")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 20
        assert data["limit"] == 10
        assert data["has_more"] is True  # 20 + 10 < 50

        # Verify service was called with correct params
        mock_service_instance.list_projects.assert_called_once_with(
            filter_dict={},
            skip=20,
            limit=10,
            sort_by="updated_at",
            sort_order="desc",
        )

    @pytest.mark.asyncio
    async def test_list_projects_with_search(
        self, test_client, mock_project_service, mock_db
    ):
        """Test listing projects with search filter."""
        # Setup
        mock_service_instance = MagicMock()
        mock_service_instance.list_projects = AsyncMock(return_value=([], 0))
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.get("/projects/?search=test")

        # Assert
        assert response.status_code == 200

        # Verify filter was applied
        call_args = mock_service_instance.list_projects.call_args
        assert call_args[1]["filter_dict"] == {"$text": {"$search": "test"}}

    @pytest.mark.asyncio
    async def test_list_projects_with_sorting(
        self, test_client, mock_project_service, mock_db
    ):
        """Test listing projects with different sort options."""
        # Setup
        mock_service_instance = MagicMock()
        mock_service_instance.list_projects = AsyncMock(return_value=([], 0))
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.get(
                "/projects/?sort_by=message_count&sort_order=asc"
            )

        # Assert
        assert response.status_code == 200

        # Verify sort params
        call_args = mock_service_instance.list_projects.call_args
        assert call_args[1]["sort_by"] == "message_count"
        assert call_args[1]["sort_order"] == "asc"

    @pytest.mark.asyncio
    async def test_list_projects_invalid_sort_field(self, test_client, mock_db):
        """Test listing projects with invalid sort field."""

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.get("/projects/?sort_by=invalid")

        # Assert - FastAPI validation should reject this
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_project_success(
        self, test_client, mock_project_service, mock_db, sample_project_with_stats
    ):
        """Test getting a specific project successfully."""
        # Setup
        project_id = "507f1f77bcf86cd799439011"
        mock_service_instance = MagicMock()
        mock_service_instance.get_project = AsyncMock(
            return_value=sample_project_with_stats
        )
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.get(f"/projects/{project_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["_id"] == project_id
        assert data["name"] == "Test Project"
        assert data["stats"]["message_count"] == 100

    @pytest.mark.asyncio
    async def test_get_project_not_found(
        self, test_client, mock_project_service, mock_db
    ):
        """Test getting a non-existent project."""
        # Setup
        project_id = "507f1f77bcf86cd799439011"
        mock_service_instance = MagicMock()
        mock_service_instance.get_project = AsyncMock(return_value=None)
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.get(f"/projects/{project_id}")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == f"Project with id '{project_id}' not found"

    @pytest.mark.asyncio
    async def test_get_project_invalid_id(self, test_client, mock_db):
        """Test getting a project with invalid ObjectId."""

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.get("/projects/invalid-id")

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid project ID"

    @pytest.mark.asyncio
    async def test_get_project_stats_success(
        self, test_client, mock_project_service, mock_db
    ):
        """Test getting project statistics successfully."""
        # Setup
        project_id = "507f1f77bcf86cd799439011"
        stats_data = {
            "project_id": project_id,
            "session_count": 10,
            "total_messages": 100,
            "user_messages": 50,
            "assistant_messages": 50,
            "total_cost": 1.23,
            "models_used": ["claude-3-opus"],
        }

        mock_service_instance = MagicMock()
        mock_service_instance.get_project_statistics = AsyncMock(
            return_value=stats_data
        )
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.get(f"/projects/{project_id}/stats")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert data["total_messages"] == 100
        assert data["total_cost"] == 1.23

    @pytest.mark.asyncio
    async def test_get_project_stats_not_found(
        self, test_client, mock_project_service, mock_db
    ):
        """Test getting stats for non-existent project."""
        # Setup
        project_id = "507f1f77bcf86cd799439011"
        mock_service_instance = MagicMock()
        mock_service_instance.get_project_statistics = AsyncMock(return_value=None)
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.get(f"/projects/{project_id}/stats")

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_project_stats_invalid_id(self, test_client, mock_db):
        """Test getting stats with invalid project ID."""

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.get("/projects/invalid-id/stats")

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid project ID"

    @pytest.mark.asyncio
    async def test_list_projects_limit_validation(self, test_client, mock_db):
        """Test list projects with limit validation."""
        # Test limit too high
        with patch("app.api.dependencies.get_db", return_value=mock_db):
            response = test_client.get("/projects/?limit=101")
        assert response.status_code == 422

        # Test limit too low
        with patch("app.api.dependencies.get_db", return_value=mock_db):
            response = test_client.get("/projects/?limit=0")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_projects_skip_validation(self, test_client, mock_db):
        """Test list projects with skip validation."""
        # Test negative skip
        with patch("app.api.dependencies.get_db", return_value=mock_db):
            response = test_client.get("/projects/?skip=-1")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_project_new(
        self, test_client, mock_project_service, mock_db, sample_project_in_db
    ):
        """Test creating a new project."""
        # Setup
        mock_service_instance = MagicMock()
        mock_service_instance.get_project_by_path = AsyncMock(return_value=None)
        mock_service_instance.create_project = AsyncMock(
            return_value=sample_project_in_db
        )
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.post(
                "/projects/",
                json={
                    "name": "Test Project",
                    "path": "/projects/test",
                    "description": "A test project",
                },
            )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["path"] == "/projects/test"
        assert data["description"] == "A test project"

    @pytest.mark.asyncio
    async def test_create_project_existing_path(
        self, test_client, mock_project_service, mock_db, sample_project_in_db
    ):
        """Test creating a project with existing path returns existing project."""
        # Setup
        mock_service_instance = MagicMock()
        mock_service_instance.get_project_by_path = AsyncMock(
            return_value=sample_project_in_db
        )
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.post(
                "/projects/",
                json={
                    "name": "Different Name",
                    "path": "/projects/test",
                    "description": "Different description",
                },
            )

        # Assert - should return the existing project
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"  # Original name
        assert data["path"] == "/projects/test"
        assert data["description"] == "A test project"  # Original description
        # Should not call create_project
        mock_service_instance.create_project.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_project_success(
        self, test_client, mock_project_service, mock_db, sample_project_in_db
    ):
        """Test successfully updating a project."""
        # Setup
        project_id = "507f1f77bcf86cd799439011"

        # Modify the sample project for update
        updated_project = sample_project_in_db
        updated_project.name = "Updated Name"
        updated_project.description = "Updated description"

        mock_service_instance = MagicMock()
        mock_service_instance.update_project = AsyncMock(return_value=updated_project)
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.patch(
                f"/projects/{project_id}",
                json={"name": "Updated Name", "description": "Updated description"},
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_project_not_found(
        self, test_client, mock_project_service, mock_db
    ):
        """Test updating a non-existent project."""
        # Setup
        project_id = "507f1f77bcf86cd799439011"
        mock_service_instance = MagicMock()
        mock_service_instance.update_project = AsyncMock(return_value=None)
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.patch(
                f"/projects/{project_id}", json={"name": "New Name"}
            )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == f"Project with id '{project_id}' not found"

    @pytest.mark.asyncio
    async def test_update_project_invalid_id(self, test_client, mock_db):
        """Test updating a project with invalid ID."""

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.patch("/projects/invalid-id", json={"name": "Test"})

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid project ID"

    @pytest.mark.asyncio
    async def test_delete_project_success(
        self, test_client, mock_project_service, mock_db
    ):
        """Test successfully deleting a project."""
        # Setup
        project_id = "507f1f77bcf86cd799439011"
        mock_service_instance = MagicMock()
        mock_service_instance.delete_project = AsyncMock(return_value=True)
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.delete(f"/projects/{project_id}")

        # Assert
        assert response.status_code == 204
        assert response.content == b""
        # Verify cascade was False by default
        mock_service_instance.delete_project.assert_called_once_with(
            ObjectId(project_id), cascade=False
        )

    @pytest.mark.asyncio
    async def test_delete_project_with_cascade(
        self, test_client, mock_project_service, mock_db
    ):
        """Test deleting a project with cascade."""
        # Setup
        project_id = "507f1f77bcf86cd799439011"
        mock_service_instance = MagicMock()
        mock_service_instance.delete_project = AsyncMock(return_value=True)
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.delete(f"/projects/{project_id}?cascade=true")

        # Assert
        assert response.status_code == 204
        # Verify cascade was True
        mock_service_instance.delete_project.assert_called_once_with(
            ObjectId(project_id), cascade=True
        )

    @pytest.mark.asyncio
    async def test_delete_project_not_found(
        self, test_client, mock_project_service, mock_db
    ):
        """Test deleting a non-existent project."""
        # Setup
        project_id = "507f1f77bcf86cd799439011"
        mock_service_instance = MagicMock()
        mock_service_instance.delete_project = AsyncMock(return_value=False)
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.delete(f"/projects/{project_id}")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == f"Project with id '{project_id}' not found"

    @pytest.mark.asyncio
    async def test_delete_project_invalid_id(self, test_client, mock_db):
        """Test deleting a project with invalid ID."""

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.delete("/projects/invalid-id")

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid project ID"

    @pytest.mark.asyncio
    async def test_create_project_validation_error(self, test_client, mock_db):
        """Test creating a project with invalid data."""

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request with missing required fields
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.post("/projects/", json={"name": "Test"})

        # Assert
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_update_project_empty_update(
        self, test_client, mock_project_service, mock_db, sample_project_in_db
    ):
        """Test updating a project with empty update."""
        # Setup
        project_id = "507f1f77bcf86cd799439011"
        mock_service_instance = MagicMock()
        mock_service_instance.update_project = AsyncMock(
            return_value=sample_project_in_db
        )
        mock_project_service.return_value = mock_service_instance

        # Mock get_db to return an async generator
        async def mock_get_db():
            yield mock_db

        # Make request with empty update
        with patch("app.api.dependencies.get_db", mock_get_db):
            response = test_client.patch(f"/projects/{project_id}", json={})

        # Assert
        assert response.status_code == 200
        # Should still call update with empty dict
        mock_service_instance.update_project.assert_called_once()
