"""Tests for backup API endpoints."""

import os
import tempfile
from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.schemas.backup_schemas import (
    BackupContents,
    BackupMetadataResponse,
    BackupStatus,
    BackupType,
    CreateBackupResponse,
    CreateRestoreResponse,
    JobStatus,
    RestoreMode,
)


@pytest.fixture
def test_client():
    """Create a test client with the backup router."""
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    from app.api.api_v1.endpoints.backup import router
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
    mock_db = AsyncMock()
    # Set up default behavior for database collections
    mock_db.backup_metadata.find_one = AsyncMock(return_value=None)

    # Create a mock cursor with chainable methods for find()
    mock_cursor = MagicMock()
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)

    # Make the cursor async iterable
    async def async_generator():
        # Yield nothing by default (empty results)
        return
        yield

    mock_cursor.__aiter__ = lambda self: async_generator()

    mock_db.backup_metadata.find = MagicMock(return_value=mock_cursor)
    mock_db.backup_metadata.count_documents = AsyncMock(return_value=0)
    mock_db.backup_metadata.insert_one = AsyncMock()
    mock_db.backup_metadata.update_one = AsyncMock()
    mock_db.backup_metadata.delete_one = AsyncMock(
        return_value=MagicMock(deleted_count=1)
    )
    mock_db.backup_jobs.find_one = AsyncMock(return_value=None)
    mock_db.backup_jobs.insert_one = AsyncMock()
    mock_db.restore_jobs.find_one = AsyncMock(return_value=None)
    mock_db.restore_jobs.insert_one = AsyncMock()

    # Mock collections for BackupService's _estimate_backup_size
    for collection_name in [
        "sessions",
        "messages",
        "projects",
        "prompts",
        "ai_settings",
    ]:
        mock_collection = MagicMock()
        mock_collection.count_documents = AsyncMock(return_value=0)
        setattr(mock_db, collection_name, mock_collection)

    # Support dictionary-style access for db[collection]
    def getitem(self, name):
        if not hasattr(mock_db, name):
            mock_collection = MagicMock()
            mock_collection.count_documents = AsyncMock(return_value=0)
            setattr(mock_db, name, mock_collection)
        return getattr(mock_db, name)

    mock_db.__getitem__ = getitem

    async def mock_get_db():
        return mock_db

    app.dependency_overrides[get_db] = mock_get_db
    app.include_router(router, prefix="/api/v1/backups")

    # Add restore routes
    from app.api.api_v1.endpoints import restore

    app.include_router(restore.router, prefix="/api/v1/restore")

    # Attach mock_db to client for easy access in tests
    client = TestClient(app)
    client.mock_db = mock_db
    return client


@pytest.fixture
def mock_backup_service():
    """Mock BackupService for testing."""
    with patch("app.api.api_v1.endpoints.backup.BackupService") as mock:
        yield mock


@pytest.fixture
def mock_restore_service():
    """Mock RestoreService for testing."""
    with patch("app.api.api_v1.endpoints.restore.RestoreService") as mock:
        yield mock


@pytest.fixture
def sample_backup_response():
    """Sample backup response for testing."""
    return CreateBackupResponse(
        job_id="507f1f77bcf86cd799439011",
        backup_id="507f1f77bcf86cd799439012",
        status=JobStatus.QUEUED,
        created_at=datetime.now(UTC),
        estimated_size_bytes=1024000,
        estimated_duration_seconds=300,
        message="Backup job created successfully",
    )


@pytest.fixture
def temp_backup_dir():
    """Create a temporary directory for backup testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy backup file
        backup_file = os.path.join(tmpdir, "test_backup.tar.gz")
        with open(backup_file, "wb") as f:
            f.write(b"dummy backup content")
        yield tmpdir


@pytest.fixture
def sample_backup_metadata(temp_backup_dir):
    """Sample backup metadata for testing."""
    backup_file = os.path.join(temp_backup_dir, "test_backup.tar.gz")
    return BackupMetadataResponse(
        id="507f1f77bcf86cd799439012",
        name="Test Backup",
        description="Test backup description",
        filename="test_backup.tar.gz",
        filepath=backup_file,
        created_at=datetime.now(UTC),
        size_bytes=1024000,
        compressed_size_bytes=512000,
        type=BackupType.FULL,
        status=BackupStatus.COMPLETED,
        contents=BackupContents(
            projects_count=5,
            sessions_count=20,
            messages_count=100,
            prompts_count=10,
            ai_settings_count=2,
            total_documents=137,
        ),
        checksum="abc123hash",
        version="1.0",
        can_restore=True,
    )


class TestCreateBackupEndpoint:
    """Tests for POST /api/v1/backups."""

    def test_create_backup_endpoint(
        self, test_client: TestClient, mock_backup_service, sample_backup_response
    ):
        """Test POST /api/v1/backups."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.create_backup.return_value = sample_backup_response
        mock_backup_service.return_value = mock_service

        # Mock rate limit check
        with patch(
            "app.api.api_v1.endpoints.backup.RateLimitService"
        ) as mock_rate_limit:
            mock_rate_limit_instance = AsyncMock()
            mock_rate_limit_instance.check_rate_limit.return_value = (True, {})
            mock_rate_limit.return_value = mock_rate_limit_instance

            # Make request
            backup_request = {
                "name": "Test Backup",
                "description": "Test backup description",
                "type": "full",
                "options": {
                    "compress": True,
                    "include_metadata": True,
                },
            }
            response = test_client.post("/api/v1/backups/", json=backup_request)

            # Verify
            assert response.status_code == 201
            data = response.json()
            assert data["job_id"] == "507f1f77bcf86cd799439011"
            assert data["backup_id"] == "507f1f77bcf86cd799439012"
            assert data["status"] == "queued"

    def test_create_backup_selective_type(
        self, test_client: TestClient, mock_backup_service, sample_backup_response
    ):
        """Test creating selective backup with filters."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.create_backup.return_value = sample_backup_response
        mock_backup_service.return_value = mock_service

        with patch(
            "app.api.api_v1.endpoints.backup.RateLimitService"
        ) as mock_rate_limit:
            mock_rate_limit_instance = AsyncMock()
            mock_rate_limit_instance.check_rate_limit.return_value = (True, {})
            mock_rate_limit.return_value = mock_rate_limit_instance

            # Make request
            backup_request = {
                "name": "Selective Backup",
                "type": "selective",
                "filters": {
                    "projects": [
                        "507f1f77bcf86cd799439013",
                        "507f1f77bcf86cd799439014",
                    ],
                    "min_message_count": 10,
                    "max_message_count": 1000,
                },
                "options": {"compress": True},
            }
            response = test_client.post("/api/v1/backups/", json=backup_request)

            # Verify
            assert response.status_code == 201
            mock_service.create_backup.assert_called_once()

    def test_create_backup_rate_limiting(
        self, test_client: TestClient, mock_backup_service
    ):
        """Test rate limit enforcement."""
        # Mock rate limit exceeded
        with patch(
            "app.api.api_v1.endpoints.backup.RateLimitService"
        ) as mock_rate_limit:
            mock_rate_limit_instance = AsyncMock()
            mock_rate_limit_instance.check_rate_limit.return_value = (
                False,
                {"message": "Rate limit exceeded"},
            )
            mock_rate_limit.return_value = mock_rate_limit_instance

            backup_request = {
                "name": "Rate Limited Backup",
                "type": "full",
            }
            response = test_client.post("/api/v1/backups/", json=backup_request)

            # Verify
            assert response.status_code == 429
            assert "rate limit" in response.json()["detail"].lower()

    def test_create_backup_validation_errors(self, test_client: TestClient):
        """Test validation error handling."""
        # Test missing required fields
        response = test_client.post("/api/v1/backups/", json={})
        assert response.status_code == 422

        # Test invalid backup type
        backup_request = {
            "name": "Invalid Backup",
            "type": "invalid_type",
        }
        response = test_client.post("/api/v1/backups/", json=backup_request)
        assert response.status_code == 422

        # Test invalid name (too short)
        backup_request = {
            "name": "AB",  # Too short
            "type": "full",
        }
        response = test_client.post("/api/v1/backups/", json=backup_request)
        assert response.status_code == 422

    def test_create_backup_selective_without_filters(self, test_client: TestClient):
        """Test selective backup without filters (should fail)."""
        backup_request = {
            "name": "Selective Without Filters",
            "type": "selective",
            # Missing filters for selective type
        }
        response = test_client.post("/api/v1/backups/", json=backup_request)
        assert response.status_code == 422


class TestListBackupsEndpoint:
    """Tests for GET /api/v1/backups."""

    def test_list_backups_endpoint(
        self,
        test_client: TestClient,
        mock_backup_service,
        sample_backup_metadata,
        temp_backup_dir,
    ):
        """Test GET /api/v1/backups."""
        # Setup mock database to return backups
        backup_file = os.path.join(temp_backup_dir, "test_backup.tar.gz")
        backup_doc = {
            "_id": ObjectId("507f1f77bcf86cd799439012"),
            "name": "Test Backup",
            "description": "Test backup description",
            "filename": "test_backup.tar.gz",
            "filepath": backup_file,
            "created_at": datetime.now(UTC),
            "size_bytes": 1024000,
            "compressed_size_bytes": 512000,
            "type": "full",
            "status": "completed",
            "contents": {
                "projects_count": 5,
                "sessions_count": 20,
                "messages_count": 100,
                "prompts_count": 10,
                "ai_settings_count": 2,
                "total_documents": 137,
            },
            "checksum": "abc123",
            "version": "1.0",
            "can_restore": True,
        }

        # Set up the mock cursor to return the backup document
        async def async_generator():
            yield backup_doc

        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.__aiter__ = lambda self: async_generator()

        test_client.mock_db.backup_metadata.find.return_value = mock_cursor
        test_client.mock_db.backup_metadata.count_documents.return_value = 1

        # Make request
        response = test_client.get("/api/v1/backups/")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        # Debug: print the actual keys to see what we have
        if data["items"]:
            print(f"Item keys: {list(data['items'][0].keys())}")
        # The field should be 'id' not '_id' due to Pydantic serialization
        assert (
            "id" in data["items"][0] or "_id" in data["items"][0]
        ), f"Neither 'id' nor '_id' found in {list(data['items'][0].keys())}"
        item_id = data["items"][0].get("id") or data["items"][0].get("_id")
        assert item_id == "507f1f77bcf86cd799439012"
        assert data["pagination"]["total_elements"] == 1

    def test_list_backups_with_pagination(
        self, test_client: TestClient, mock_backup_service
    ):
        """Test listing backups with pagination parameters."""
        # Setup database mock with empty results
        test_client.mock_db.backup_metadata.count_documents.return_value = 100

        # Create a mock cursor that returns empty results
        async def async_generator():
            return
            yield

        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.__aiter__ = lambda self: async_generator()

        test_client.mock_db.backup_metadata.find.return_value = mock_cursor

        # Make request with pagination params
        response = test_client.get("/api/v1/backups/?page=2&size=10")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["size"] == 10
        assert data["pagination"]["total_elements"] == 100
        assert data["pagination"]["total_pages"] == 10

        # Verify the cursor methods were called with correct values
        mock_cursor.skip.assert_called_with(20)  # page 2 * size 10
        mock_cursor.limit.assert_called_with(10)

    def test_list_backups_with_filters(
        self, test_client: TestClient, mock_backup_service
    ):
        """Test listing backups with filters."""
        # Setup mock database to return filtered results
        test_client.mock_db.backup_metadata.count_documents.return_value = 0

        # Create an empty async generator for find results
        async def empty_generator():
            return
            yield

        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.__aiter__ = lambda self: empty_generator()

        test_client.mock_db.backup_metadata.find.return_value = mock_cursor

        # Make request
        response = test_client.get("/api/v1/backups/?status=completed&type=full")

        # Verify
        assert response.status_code == 200
        # Verify that find was called with the correct filters
        test_client.mock_db.backup_metadata.find.assert_called_once()
        call_args = test_client.mock_db.backup_metadata.find.call_args[0][0]
        assert "status" in call_args
        assert call_args["status"] == "completed"
        assert "type" in call_args
        assert call_args["type"] == "full"


class TestGetBackupDetailEndpoint:
    """Tests for GET /api/v1/backups/{id}."""

    def test_get_backup_detail_endpoint(
        self, test_client: TestClient, mock_backup_service, temp_backup_dir
    ):
        """Test GET /api/v1/backups/{id}."""
        # Setup mock database to return a backup document
        backup_id = "507f1f77bcf86cd799439012"
        backup_file = os.path.join(temp_backup_dir, "test_backup.tar.gz")
        test_client.mock_db.backup_metadata.find_one.return_value = {
            "_id": ObjectId(backup_id),
            "name": "Test Backup",
            "filename": "test_backup.tar.gz",
            "filepath": backup_file,
            "created_at": datetime.now(UTC),
            "size_bytes": 1024000,
            "type": "full",
            "status": "completed",
            "contents": {
                "projects_count": 10,
                "sessions_count": 50,
                "messages_count": 100,
                "prompts_count": 5,
                "ai_settings_count": 2,
                "total_documents": 167,
            },
            "checksum": "abc123",
            "version": "1.0",
            "storage_location": "/var/backups/",
            "can_restore": True,
        }

        # Make request
        response = test_client.get(f"/api/v1/backups/{backup_id}")

        # Verify
        assert response.status_code == 200
        data = response.json()
        # Debug: print the actual keys
        print(f"Response keys: {list(data.keys())}")
        # The response should have "id" field (Pydantic converts _id to id)
        assert (
            "id" in data or "_id" in data
        ), f"Neither 'id' nor '_id' found in {list(data.keys())}"
        item_id = data.get("id") or data.get("_id")
        assert item_id == "507f1f77bcf86cd799439012"
        assert data["storage_location"] == "/var/backups/"

    def test_get_backup_detail_not_found(
        self, test_client: TestClient, mock_backup_service
    ):
        """Test getting non-existent backup detail."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_backup_detail.return_value = None
        mock_backup_service.return_value = mock_service

        # Use valid ObjectId that doesn't exist
        backup_id = str(ObjectId())

        # Make request
        response = test_client.get(f"/api/v1/backups/{backup_id}")

        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDownloadBackupEndpoint:
    """Tests for GET /api/v1/backups/{id}/download."""

    def test_download_backup_endpoint(
        self, test_client: TestClient, mock_backup_service, temp_backup_dir
    ):
        """Test GET /api/v1/backups/{id}/download."""
        # Setup database mock to return a completed backup
        backup_id = "507f1f77bcf86cd799439012"
        backup_file = os.path.join(temp_backup_dir, "test_backup.tar.gz")
        test_client.mock_db.backup_metadata.find_one.return_value = {
            "_id": ObjectId(backup_id),
            "status": "completed",
            "filepath": backup_file,
            "filename": "test_backup.tar.gz",
        }

        # Setup file service mock
        with patch("app.api.api_v1.endpoints.backup.FileService") as mock_file_service:
            # Create a simple generator for streaming
            def file_generator():
                yield b"backup file content"

            mock_file_service.return_value.stream_file = MagicMock(
                return_value=file_generator()
            )

            # Make request
            response = test_client.get(f"/api/v1/backups/{backup_id}/download")

        # Verify
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        assert "attachment; filename=" in response.headers["content-disposition"]

    def test_download_backup_not_found(
        self, test_client: TestClient, mock_backup_service
    ):
        """Test downloading non-existent backup."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.download_backup.return_value = None
        mock_backup_service.return_value = mock_service

        # Use valid ObjectId that doesn't exist
        backup_id = str(ObjectId())

        # Make request
        response = test_client.get(f"/api/v1/backups/{backup_id}/download")

        # Verify
        assert response.status_code == 404


class TestDeleteBackupEndpoint:
    """Tests for DELETE /api/v1/backups/{id}."""

    def test_delete_backup_endpoint(self, test_client: TestClient, mock_backup_service):
        """Test DELETE /api/v1/backups/{id}."""
        # Setup database mock to return a backup
        backup_id = "507f1f77bcf86cd799439012"
        test_client.mock_db.backup_metadata.find_one.return_value = {
            "_id": ObjectId(backup_id),
            "name": "Test Backup",
            "filepath": "/var/backups/test.tar.gz",
        }
        test_client.mock_db.backup_metadata.delete_one.return_value = MagicMock(
            deleted_count=1
        )

        # Setup file service mock
        with patch("app.api.api_v1.endpoints.backup.FileService") as mock_file_service:
            mock_file_service.return_value.delete_file = AsyncMock()

            # Make request
            response = test_client.delete(f"/api/v1/backups/{backup_id}")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["backup_id"] == backup_id
        assert "message" in data

    def test_delete_backup_not_found(
        self, test_client: TestClient, mock_backup_service
    ):
        """Test deleting non-existent backup."""
        # The database mock is already set up to return None for find_one
        # which will trigger the 404 response

        # Use valid ObjectId that doesn't exist
        backup_id = str(ObjectId())

        # Make request
        response = test_client.delete(f"/api/v1/backups/{backup_id}")

        # Verify
        assert response.status_code == 404


class TestBackupWebSocketProgress:
    """Tests for backup WebSocket progress updates."""

    @pytest.mark.skip(reason="WebSocket testing requires special setup")
    async def test_backup_websocket_progress(self, test_client: TestClient):
        """Test WebSocket progress updates."""
        # WebSocket testing would require a more complex setup
        # Skipping for now as it's not critical to the backup/restore functionality
        pass


class TestCreateRestoreEndpoint:
    """Tests for POST /api/v1/restore."""

    def test_create_restore_endpoint(
        self, test_client: TestClient, mock_restore_service
    ):
        """Test POST /api/v1/restore."""
        # Setup database mock to return a completed backup
        backup_id = "507f1f77bcf86cd799439012"
        test_client.mock_db.backup_metadata.find_one.return_value = {
            "_id": ObjectId(backup_id),
            "status": "completed",
        }

        # Setup mock restore service
        restore_response = CreateRestoreResponse(
            job_id="507f1f77bcf86cd799439015",
            status=JobStatus.QUEUED,
            created_at=datetime.now(UTC),
            backup_id=backup_id,
            mode=RestoreMode.FULL,
            estimated_duration_seconds=600,
            message="Restore job created successfully",
        )

        mock_service = AsyncMock()
        mock_service.create_restore_job.return_value = restore_response
        mock_restore_service.return_value = mock_service

        # Mock rate limit check
        with patch(
            "app.api.api_v1.endpoints.restore.RateLimitService"
        ) as mock_rate_limit:
            mock_rate_limit_instance = AsyncMock()
            mock_rate_limit_instance.check_rate_limit.return_value = (True, {})
            mock_rate_limit.return_value = mock_rate_limit_instance

            # Make request
            restore_request = {
                "backup_id": backup_id,
                "mode": "full",
                "conflict_resolution": "skip",
            }
            response = test_client.post("/api/v1/restore/", json=restore_request)

            # Verify
            assert response.status_code == 201
            data = response.json()
            assert data["job_id"] == "507f1f77bcf86cd799439015"
            assert data["backup_id"] == "507f1f77bcf86cd799439012"

    def test_create_restore_selective_mode(
        self, test_client: TestClient, mock_restore_service
    ):
        """Test creating selective restore."""
        # Setup database mock to return a completed backup
        backup_id = "507f1f77bcf86cd799439012"
        test_client.mock_db.backup_metadata.find_one.return_value = {
            "_id": ObjectId(backup_id),
            "status": "completed",
        }

        # Setup mock
        restore_response = CreateRestoreResponse(
            job_id="507f1f77bcf86cd799439013",
            status=JobStatus.QUEUED,
            created_at=datetime.now(UTC),
            backup_id=backup_id,
            mode=RestoreMode.SELECTIVE,
            message="Selective restore job created",
        )

        mock_service = AsyncMock()
        mock_service.create_restore_job.return_value = restore_response
        mock_restore_service.return_value = mock_service

        # Mock rate limit check
        with patch(
            "app.api.api_v1.endpoints.restore.RateLimitService"
        ) as mock_rate_limit:
            mock_rate_limit_instance = AsyncMock()
            mock_rate_limit_instance.check_rate_limit.return_value = (True, {})
            mock_rate_limit.return_value = mock_rate_limit_instance

            # Make request
            restore_request = {
                "backup_id": backup_id,
                "mode": "selective",
                "selections": {
                    "collections": ["projects", "sessions"],
                    "projects": ["project1"],
                },
                "conflict_resolution": "overwrite",
            }
            response = test_client.post("/api/v1/restore/", json=restore_request)

            # Verify
            assert response.status_code == 201
            data = response.json()
            assert data["mode"] == "selective"


class TestUploadRestoreEndpoint:
    """Tests for POST /api/v1/restore/upload."""

    def test_upload_restore_endpoint(
        self, test_client: TestClient, mock_restore_service
    ):
        """Test POST /api/v1/restore/upload."""
        # Setup mocks
        with patch("app.api.api_v1.endpoints.restore.FileService") as mock_file_service:
            # Mock file service to return file info
            mock_file_service.return_value.validate_and_save_upload = AsyncMock(
                return_value={
                    "path": "/tmp/test_upload.claudelens",
                    "filename": "backup.claudelens",
                    "size": 1024,
                }
            )

            # Setup restore service mock
            restore_response = CreateRestoreResponse(
                job_id="507f1f77bcf86cd799439016",
                status=JobStatus.QUEUED,
                created_at=datetime.now(UTC),
                backup_id="507f1f77bcf86cd799439017",
                mode=RestoreMode.FULL,
                message="Upload restore job created",
            )
            mock_service = AsyncMock()
            mock_service.create_restore_job_from_upload.return_value = restore_response
            mock_restore_service.return_value = mock_service

            # Mock rate limit check
            with patch(
                "app.api.api_v1.endpoints.restore.RateLimitService"
            ) as mock_rate_limit:
                mock_rate_limit_instance = AsyncMock()
                mock_rate_limit_instance.check_rate_limit.return_value = (True, {})
                mock_rate_limit.return_value = mock_rate_limit_instance

                # Create test file
                test_file_content = b"fake backup file content"
                files = {
                    "file": (
                        "backup.claudelens",
                        BytesIO(test_file_content),
                        "application/octet-stream",
                    )
                }

                # Make request
                response = test_client.post(
                    "/api/v1/restore/upload",
                    files=files,
                    params={"mode": "full", "conflict_resolution": "skip"},
                )

                # Verify
                assert response.status_code == 202
                data = response.json()
                assert "job_id" in data

    def test_upload_restore_file_validation(self, test_client: TestClient):
        """Test file upload validation."""
        # Mock rate limit check for all requests
        with patch(
            "app.api.api_v1.endpoints.restore.RateLimitService"
        ) as mock_rate_limit:
            mock_rate_limit_instance = AsyncMock()
            mock_rate_limit_instance.check_rate_limit.return_value = (True, {})
            mock_rate_limit.return_value = mock_rate_limit_instance

            # Test missing file - FastAPI returns 422 for missing required field
            response = test_client.post("/api/v1/restore/upload")
            assert response.status_code == 422

            # Test invalid file type - endpoint returns 400 for wrong file type
            files = {"file": ("backup.txt", BytesIO(b"content"), "text/plain")}
            response = test_client.post("/api/v1/restore/upload", files=files)
            assert response.status_code == 400


class TestGetRestoreStatusEndpoint:
    """Tests for GET /api/v1/restore/{id}/status."""

    def test_get_restore_status_endpoint(
        self, test_client: TestClient, mock_restore_service
    ):
        """Test GET /api/v1/restore/{id}/status."""
        # Setup database mock to return a restore job
        job_id = "507f1f77bcf86cd799439015"
        test_client.mock_db.restore_jobs.find_one.return_value = {
            "_id": ObjectId(job_id),
            "status": "processing",
            "progress": {
                "completed_items": 50,
                "total_items": 100,
                "percentage": 50.0,
                "current_collection": "sessions",
            },
            "statistics": {
                "inserted": 30,
                "updated": 15,
                "skipped": 5,
            },
            "errors": [],
        }

        # Make request
        response = test_client.get(f"/api/v1/restore/{job_id}/status")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "processing"
        assert data["progress"]["percentage"] == 50.0

    def test_get_restore_status_not_found(
        self, test_client: TestClient, mock_restore_service
    ):
        """Test getting status for non-existent restore job."""
        # Use a valid ObjectId that doesn't exist
        job_id = str(ObjectId())

        # The mock_db is already set to return None for find_one by default

        # Make request
        response = test_client.get(f"/api/v1/restore/{job_id}/status")

        # Verify
        assert response.status_code == 404


class TestPreviewBackupEndpoint:
    """Tests for GET /api/v1/restore/preview/{id}."""

    def test_preview_backup_endpoint(
        self, test_client: TestClient, mock_restore_service
    ):
        """Test GET /api/v1/restore/preview/{id}."""
        # Setup database mock to return a completed backup
        backup_id = "507f1f77bcf86cd799439012"
        test_client.mock_db.backup_metadata.find_one.return_value = {
            "_id": ObjectId(backup_id),
            "name": "Test Backup",
            "created_at": datetime.now(UTC),
            "type": "full",
            "status": "completed",
            "contents": {
                "projects_count": 5,
                "sessions_count": 20,
                "messages_count": 100,
            },
            "size_bytes": 1024000,
            "can_restore": True,
            "version": "1.0",
        }

        # Setup restore service mock
        preview_data = {
            "collections": {
                "projects": {"count": 5, "sample_data": []},
                "sessions": {"count": 20, "sample_data": []},
            },
            "summary": {"total_documents": 125, "collections_count": 5},
        }
        mock_service = AsyncMock()
        mock_service.preview_backup_contents.return_value = preview_data
        mock_restore_service.return_value = mock_service

        # Make request
        response = test_client.get(f"/api/v1/restore/preview/{backup_id}")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["backup_id"] == "507f1f77bcf86cd799439012"
        assert data["can_restore"] is True
        assert "collections" in data["preview_data"]
        assert "projects" in data["preview_data"]["collections"]

    def test_preview_backup_with_warnings(
        self, test_client: TestClient, mock_restore_service
    ):
        """Test preview with warnings."""
        # Setup database mock and backup_id
        backup_id = "507f1f77bcf86cd799439012"
        test_client.mock_db.backup_metadata.find_one.return_value = {
            "_id": ObjectId(backup_id),
            "name": "Old Backup",
            "created_at": datetime.now(UTC),
            "type": "full",
            "status": "completed",
            "contents": {"messages_count": 15000},  # Large count to trigger warning
            "size_bytes": 1024000,
            "version": "0.9.0",  # Old version to trigger warning
            "can_restore": False,
        }

        # Setup restore service mock
        preview_data = {"collections": {}, "summary": {}}
        mock_service = AsyncMock()
        mock_service.preview_backup_contents.return_value = preview_data
        mock_restore_service.return_value = mock_service

        # Make request
        response = test_client.get(f"/api/v1/restore/preview/{backup_id}")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["can_restore"] is False
        assert len(data["warnings"]) == 2


class TestRestoreValidationErrors:
    """Tests for restore validation errors."""

    def test_restore_validation_errors(self, test_client: TestClient):
        """Test validation errors."""
        # Test missing backup_id
        response = test_client.post("/api/v1/restore/", json={"mode": "full"})
        assert response.status_code == 422

        # Test invalid mode
        response = test_client.post(
            "/api/v1/restore/",
            json={
                "backup_id": "507f1f77bcf86cd799439012",
                "mode": "invalid_mode",
            },
        )
        assert response.status_code == 422

        # Test invalid conflict resolution
        response = test_client.post(
            "/api/v1/restore/",
            json={
                "backup_id": "507f1f77bcf86cd799439012",
                "mode": "full",
                "conflict_resolution": "invalid_resolution",
            },
        )
        assert response.status_code == 422
