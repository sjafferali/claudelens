"""Tests for the restore service - Fixed version."""

import os
import tempfile
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from app.schemas.backup_schemas import (
    ConflictResolution,
    CreateRestoreRequest,
    JobStatus,
    RestoreMode,
)
from app.services.restore_service import RestoreService, RestoreTransaction


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment with temp directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["BACKUP_DIR"] = tmpdir
        yield tmpdir
        # Cleanup
        if "BACKUP_DIR" in os.environ:
            del os.environ["BACKUP_DIR"]


@pytest.fixture
def mock_db():
    """Create a mock database."""
    db = MagicMock()
    db.backup_metadata = MagicMock()
    db.restore_jobs = MagicMock()
    db.projects = MagicMock()
    db.sessions = MagicMock()
    db.messages = MagicMock()
    db.client = MagicMock()
    return db


@pytest.fixture
def restore_service(mock_db):
    """Create a restore service with mock database."""
    return RestoreService(mock_db)


@pytest.fixture
def sample_restore_request():
    """Sample restore request for testing."""
    return CreateRestoreRequest(
        backup_id="507f1f77bcf86cd799439011",
        mode=RestoreMode.FULL,
        conflict_resolution=ConflictResolution.SKIP,
    )


class TestRestoreService:
    """Test cases for RestoreService."""

    @pytest.mark.asyncio
    async def test_create_restore_job(
        self, restore_service, mock_db, sample_restore_request
    ):
        """Test creating a restore job."""
        # Setup
        mock_db.backup_metadata.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(sample_restore_request.backup_id),
                "status": "completed",
                "filepath": "/path/to/backup.zst",
            }
        )
        mock_db.restore_jobs.insert_one = AsyncMock()

        # Execute
        response = await restore_service.create_restore_job(sample_restore_request)

        # Assert
        assert response is not None
        assert hasattr(response, "job_id")
        assert isinstance(response.job_id, str)
        assert response.status == JobStatus.QUEUED
        assert response.backup_id == sample_restore_request.backup_id
        mock_db.restore_jobs.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_backup(self, restore_service, mock_db):
        """Test backup validation."""
        # Setup
        backup_id = "507f1f77bcf86cd799439011"
        mock_db.backup_metadata.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(backup_id),
                "name": "Test Backup",
                "created_at": datetime.now(UTC),
                "type": "full",
                "size_bytes": 1024000,
                "checksum": "abcd1234",
                "status": "completed",
                "filepath": "/path/to/backup.zst",
                "contents": {"total_documents": 100},
            }
        )

        with patch("os.path.exists", return_value=True):
            with patch.object(restore_service, "_stream_backup_data") as mock_stream:
                # Mock streaming some data chunks
                async def mock_generator():
                    for i in range(5):
                        yield {"test": i}

                mock_stream.return_value = mock_generator()

                # Execute
                result = await restore_service.validate_backup(backup_id)

                # Assert
                assert result["valid"] is True
                assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_backup_missing_file(self, restore_service, mock_db):
        """Test validation with missing backup file."""
        # Setup
        backup_id = "507f1f77bcf86cd799439011"
        mock_db.backup_metadata.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(backup_id),
                "name": "Test Backup",
                "created_at": datetime.now(UTC),
                "type": "full",
                "size_bytes": 1024000,
                "checksum": "abcd1234",
                "status": "completed",
                "filepath": "/path/to/backup.zst",
            }
        )

        with patch("os.path.exists", return_value=False):
            # Execute
            result = await restore_service.validate_backup(backup_id)

            # Assert
            assert result["valid"] is False
            assert any("not found" in err.lower() for err in result["errors"])

    @pytest.mark.asyncio
    async def test_preview_backup(self, restore_service, mock_db):
        """Test backup preview."""
        # Setup
        backup_id = "507f1f77bcf86cd799439011"
        mock_db.backup_metadata.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(backup_id),
                "name": "Test Backup",
                "created_at": datetime.now(UTC),
                "type": "full",
                "contents": {"projects_count": 2, "sessions_count": 10},
                "size_bytes": 1024000,
                "status": "completed",
                "filepath": "/path/to/backup.zst",
            }
        )

        with patch.object(restore_service, "_stream_backup_data") as mock_stream:
            # Mock streaming collection data
            async def mock_generator():
                yield {"collection": "projects"}
                yield {"_id": "p1", "name": "Project 1"}
                yield {"collection": "sessions"}
                yield {"_id": "s1", "title": "Session 1"}

            mock_stream.return_value = mock_generator()

            # Execute
            preview = await restore_service.preview_backup(backup_id)

            # Assert
            assert preview.backup_id == backup_id
            assert preview.can_restore is True
            assert "projects" in preview.preview_data

    @pytest.mark.asyncio
    async def test_restore_with_conflicts(self, restore_service, mock_db):
        """Test restore with conflict resolution."""
        # Setup
        backup_id = "507f1f77bcf86cd799439011"
        options = {
            "mode": RestoreMode.FULL,
            "conflict_resolution": ConflictResolution.OVERWRITE,
            "job_id": str(ObjectId()),  # Use valid ObjectId for job_id
        }

        # Mock database session with proper context manager
        mock_session = AsyncMock()
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock()
        mock_transaction.__aexit__ = AsyncMock()
        mock_session.start_transaction = MagicMock(return_value=mock_transaction)
        mock_session.commit_transaction = AsyncMock()
        mock_session.abort_transaction = AsyncMock()

        # Mock the client.start_session context manager
        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cm.__aexit__ = AsyncMock()
        mock_db.client.start_session = AsyncMock(return_value=mock_session_cm)

        with patch.object(restore_service, "_stream_backup_data") as mock_stream:

            async def mock_generator():
                yield {"collection": "projects"}
                yield {"_id": "p1", "name": "Project 1"}

            mock_stream.return_value = mock_generator()

            with patch.object(restore_service, "_restore_batch") as mock_batch:
                mock_batch.return_value = {
                    "processed": 1,
                    "inserted": 0,
                    "updated": 1,
                    "skipped": 0,
                    "conflicts": 1,
                }

                # Execute
                result = await restore_service.restore_backup(backup_id, options)

                # Assert
                assert result["total_processed"] >= 0
                assert "documents_processed" in result
                assert "documents_inserted" in result


class TestRestoreTransaction:
    """Test cases for RestoreTransaction."""

    @pytest.mark.asyncio
    async def test_transaction_backup_existing(self, mock_db):
        """Test backing up existing document."""
        # Setup
        transaction = RestoreTransaction(mock_db)
        doc_id = "507f1f77bcf86cd799439011"
        collection = "projects"

        mock_db[collection].find_one = AsyncMock(
            return_value={
                "_id": ObjectId(doc_id),
                "name": "Existing Project",
            }
        )

        # Execute
        await transaction.backup_existing(collection, doc_id)

        # Assert
        assert len(transaction.updated_ids) == 1
        assert (collection, doc_id) in transaction.updated_ids
        assert doc_id in transaction.backup_data[collection]

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, mock_db):
        """Test transaction rollback."""
        # Setup
        transaction = RestoreTransaction(mock_db)

        # Add some operations to rollback
        transaction.inserted_ids = [("projects", "507f1f77bcf86cd799439011")]
        transaction.backup_data = {
            "sessions": {
                "507f1f77bcf86cd799439012": {
                    "_id": ObjectId("507f1f77bcf86cd799439012"),
                    "title": "Old Session",
                }
            }
        }
        transaction.updated_ids = [("sessions", "507f1f77bcf86cd799439012")]

        mock_db["projects"].delete_one = AsyncMock()
        mock_db["sessions"].replace_one = AsyncMock()

        # Execute
        await transaction.rollback()

        # Assert
        mock_db["projects"].delete_one.assert_called_once()
        mock_db["sessions"].replace_one.assert_called_once()

    def test_transaction_add_id_mapping(self, mock_db):
        """Test adding ID mapping."""
        # Setup
        transaction = RestoreTransaction(mock_db)
        old_id = "507f1f77bcf86cd799439011"
        new_id = "507f1f77bcf86cd799439012"

        # Execute
        transaction.add_id_mapping(old_id, new_id)

        # Assert
        assert transaction.id_mappings[old_id] == new_id

    @pytest.mark.asyncio
    async def test_transaction_track_insertion(self, mock_db):
        """Test tracking insertions."""
        # Setup
        transaction = RestoreTransaction(mock_db)
        collection = "projects"
        doc_id = "507f1f77bcf86cd799439011"

        # Execute
        await transaction.track_insertion(collection, doc_id)

        # Assert
        assert (collection, doc_id) in transaction.inserted_ids
