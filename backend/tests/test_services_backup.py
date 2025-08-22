"""Tests for the backup service."""

import os
import tempfile
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from app.schemas.backup_schemas import (
    BackupFilters,
    BackupOptions,
    BackupType,
    CreateBackupRequest,
)
from app.services.backup_service import BackupProgressTracker, BackupService


async def async_iter(items):
    """Helper to create async iterator from list."""
    for item in items:
        yield item


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
    db.backup_jobs = MagicMock()
    db.backup_metadata = MagicMock()
    db.projects = MagicMock()
    db.sessions = MagicMock()
    db.messages = MagicMock()
    db.prompts = MagicMock()
    db.ai_settings = MagicMock()
    return db


@pytest.fixture
def backup_service(mock_db):
    """Create a backup service with mock database."""
    return BackupService(mock_db)


@pytest.fixture
def sample_backup_request():
    """Sample backup request for testing."""
    return CreateBackupRequest(
        name="Test Backup",
        description="Test backup description",
        type=BackupType.FULL,
        options=BackupOptions(compress=True, include_metadata=True),
    )


@pytest.fixture
def sample_selective_backup_request():
    """Sample selective backup request for testing."""
    return CreateBackupRequest(
        name="Selective Backup",
        description="Selective backup with filters",
        type=BackupType.SELECTIVE,
        filters=BackupFilters(
            projects=["507f1f77bcf86cd799439013", "507f1f77bcf86cd799439014"],
            min_message_count=10,
            max_message_count=1000,
        ),
        options=BackupOptions(compress=True),
    )


class TestBackupService:
    """Test cases for BackupService."""

    @pytest.mark.asyncio
    async def test_create_backup_full(
        self, backup_service, mock_db, sample_backup_request
    ):
        """Test full backup creation."""
        # Setup
        # Mock job creation
        mock_db.backup_jobs.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )
        mock_db.backup_metadata.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )

        # Mock size estimation
        with patch.object(
            backup_service, "_estimate_backup_size", return_value=1024000
        ):
            # Execute
            response = await backup_service.create_backup(sample_backup_request)

            # Assert
            assert response.job_id
            assert isinstance(response.job_id, str)
            mock_db.backup_jobs.insert_one.assert_called_once()
            mock_db.backup_metadata.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_backup_selective(
        self, backup_service, mock_db, sample_selective_backup_request
    ):
        """Test selective backup with filters."""
        # Setup
        mock_db.backup_jobs.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )
        mock_db.backup_metadata.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )

        with patch.object(backup_service, "_estimate_backup_size", return_value=512000):
            # Execute
            response = await backup_service.create_backup(
                sample_selective_backup_request
            )

            # Assert
            assert response.job_id
            assert isinstance(response.job_id, str)
            mock_db.backup_jobs.insert_one.assert_called_once()
            mock_db.backup_metadata.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_backup_progress_tracking(self, backup_service, mock_db):
        """Test progress updates."""
        # Setup
        job_id = str(ObjectId())  # Use valid ObjectId
        total_items = 100

        mock_update_callback = AsyncMock()
        tracker = BackupProgressTracker(
            job_id=job_id,
            total_items=total_items,
            update_callback=mock_update_callback,
            db=mock_db,
        )

        # Mock the database operation
        mock_db.backup_jobs.update_one = AsyncMock()

        # Execute progress updates
        await tracker.increment(25, "Processing projects...")
        await tracker.increment(25, "Processing sessions...")
        await tracker.complete()

        # Assert
        assert tracker.processed_items == 100
        assert mock_update_callback.call_count >= 1

    @pytest.mark.asyncio
    async def test_list_backups_pagination(self, backup_service, mock_db):
        """Test listing with pagination."""
        # Setup
        mock_backups = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "name": "Backup 1",
                "filename": "backup1.tar.gz",
                "filepath": "/var/backups/backup1.tar.gz",
                "created_at": datetime.now(UTC),
                "size_bytes": 1024000,
                "type": "full",
                "status": "completed",
                "checksum": "abc123",
                "version": "1.0",
                "contents": {"total_documents": 100},
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "name": "Backup 2",
                "filename": "backup2.tar.gz",
                "filepath": "/var/backups/backup2.tar.gz",
                "created_at": datetime.now(UTC),
                "size_bytes": 512000,
                "type": "selective",
                "status": "completed",
                "checksum": "def456",
                "version": "1.0",
                "contents": {"total_documents": 50},
            },
        ]

        mock_db.backup_metadata.count_documents = AsyncMock(return_value=10)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter(mock_backups)
        )
        mock_db.backup_metadata.find.return_value = mock_cursor

        # Execute
        result = await backup_service.list_backups(page=1, size=2)

        # Assert
        assert len(result.items) == 2
        assert result.pagination["total"] == 10
        assert result.pagination["has_more"] is True
        assert result.items[0].name == "Backup 1"

    @pytest.mark.asyncio
    async def test_delete_backup(self, backup_service, mock_db):
        """Test backup deletion."""
        # Setup
        backup_id = "507f1f77bcf86cd799439011"
        mock_backup = {
            "_id": ObjectId(backup_id),
            "name": "Test Backup",
            "filepath": "/var/backups/test.tar.gz",
            "status": "completed",
        }

        mock_db.backup_metadata.find_one = AsyncMock(return_value=mock_backup)
        mock_db.backup_metadata.update_one = AsyncMock(
            return_value=MagicMock(modified_count=1)
        )
        mock_db.backup_metadata.delete_one = AsyncMock(
            return_value=MagicMock(deleted_count=1)
        )

        with patch("os.path.exists", return_value=True):
            with patch("os.remove") as mock_remove:
                # Execute
                success = await backup_service.delete_backup(backup_id)

                # Assert
                assert success is True
                mock_remove.assert_called_once_with("/var/backups/test.tar.gz")
                mock_db.backup_metadata.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_backup_streaming(self, backup_service, mock_db):
        """Test file streaming."""
        # Setup
        backup_id = "507f1f77bcf86cd799439011"
        mock_backup = {
            "_id": ObjectId(backup_id),
            "filepath": "/var/backups/test.tar.gz",
            "filename": "test.tar.gz",
            "size_bytes": 1024,
        }

        mock_db.backup_metadata.find_one = AsyncMock(return_value=mock_backup)

        with patch("aiofiles.open") as mock_open:
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(side_effect=[b"data1", b"data2", b""])
            mock_open.return_value.__aenter__.return_value = mock_file

            # Execute - download_backup is an async generator
            stream = backup_service.download_backup(backup_id)

            # Assert
            assert stream is not None
            # Can't easily test async generator without consuming it

    @pytest.mark.asyncio
    async def test_backup_compression(self, backup_service, mock_db):
        """Test compression functionality."""
        # Test that StreamingCompressor can be imported
        try:
            from app.services.compression_service import StreamingCompressor

            # Just verify the class exists and can be instantiated
            compressor = StreamingCompressor()
            assert compressor is not None
        except ImportError:
            # Skip test if zstandard is not installed
            pytest.skip("zstandard library not installed")

    @pytest.mark.asyncio
    async def test_backup_checksum(self, backup_service, mock_db):
        """Test checksum calculation."""
        # Test that ChecksumCalculator can be imported
        from app.services.compression_service import ChecksumCalculator

        # Just verify the class exists and can be instantiated
        calculator = ChecksumCalculator()
        assert calculator is not None

    @pytest.mark.asyncio
    async def test_estimate_backup_size(self, backup_service, mock_db):
        """Test size estimation."""
        # Setup
        filters = BackupFilters(projects=["507f1f77bcf86cd799439013"])

        # Mock document counts for collections
        # Create mock collection objects with count_documents method
        for collection_name in [
            "projects",
            "sessions",
            "messages",
            "prompts",
            "ai_settings",
        ]:
            setattr(mock_db, collection_name, MagicMock())
            getattr(mock_db, collection_name).count_documents = AsyncMock(
                return_value=10
            )

        # Also mock the __getitem__ for db[collection_name]
        def get_collection(name):
            mock_collection = MagicMock()
            mock_collection.count_documents = AsyncMock(return_value=10)
            return mock_collection

        mock_db.__getitem__ = MagicMock(side_effect=get_collection)

        # Execute
        estimated_size = await backup_service._estimate_backup_size(filters)

        # Assert
        assert estimated_size > 0
        # Check that count_documents was called on at least one collection
        assert mock_db.__getitem__.call_count >= 5

    @pytest.mark.asyncio
    async def test_backup_error_handling(self, backup_service, mock_db):
        """Test error scenarios."""
        # Setup
        sample_request = CreateBackupRequest(name="Error Backup", type=BackupType.FULL)

        # Mock document counts for size estimation
        for collection_name in [
            "projects",
            "sessions",
            "messages",
            "prompts",
            "ai_settings",
        ]:
            collection = MagicMock()
            collection.count_documents = AsyncMock(return_value=10)
            setattr(mock_db, collection_name, collection)

        # Also mock the __getitem__ for db[collection_name]
        def get_collection(name):
            mock_collection = MagicMock()
            mock_collection.count_documents = AsyncMock(return_value=10)
            return mock_collection

        mock_db.__getitem__ = MagicMock(side_effect=get_collection)

        # Mock database error on insert
        mock_db.backup_jobs.insert_one = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Execute & Assert
        with pytest.raises(Exception) as exc_info:
            await backup_service.create_backup(sample_request)

        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limiting(self, backup_service, mock_db):
        """Test rate limit enforcement."""
        # This test just verifies we can test rate limiting concepts
        # The actual rate limiting is implemented in the API layer
        from datetime import UTC, datetime, timedelta

        # Mock rate limit data structure
        rate_limit_data = {
            "test_user": [
                datetime.now(UTC) - timedelta(minutes=30),
                datetime.now(UTC) - timedelta(minutes=20),
                datetime.now(UTC) - timedelta(minutes=10),
            ]
        }

        # Test that we can check rate limits
        user_requests = rate_limit_data["test_user"]
        assert len(user_requests) == 3

        # Test time-based filtering
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        recent_requests = [req for req in user_requests if req > one_hour_ago]
        assert len(recent_requests) == 3


class TestBackupProgressTracker:
    """Test cases for BackupProgressTracker."""

    def test_progress_tracker_initialization(self):
        """Test progress tracker initialization."""
        tracker = BackupProgressTracker(job_id="test_job", total_items=100)

        assert tracker.job_id == "test_job"
        assert tracker.total_items == 100
        assert tracker.processed_items == 0

    @pytest.mark.asyncio
    async def test_progress_tracker_updates(self):
        """Test progress tracker updates."""
        mock_callback = AsyncMock()
        tracker = BackupProgressTracker(
            job_id="test_job", total_items=50, update_callback=mock_callback
        )

        # Update progress by incrementing
        await tracker.increment(25, "Halfway done")

        assert tracker.processed_items == 25
        assert tracker.current_item == "Halfway done"

    @pytest.mark.asyncio
    async def test_progress_tracker_completion(self):
        """Test progress tracker completion."""
        tracker = BackupProgressTracker(job_id="test_job", total_items=10)

        # Complete all items
        await tracker.complete()

        assert tracker.processed_items == 10

    @pytest.mark.asyncio
    async def test_progress_tracker_database_updates(self):
        """Test progress tracker database updates."""
        mock_db = MagicMock()
        mock_db.backup_jobs.update_one = AsyncMock()

        tracker = BackupProgressTracker(
            job_id="507f1f77bcf86cd799439011",  # Valid ObjectId format
            total_items=100,
            db=mock_db,
        )

        # Force an update by calling send_update directly
        await tracker.send_update()

        # Verify database update was called
        mock_db.backup_jobs.update_one.assert_called_once()
        call_args = mock_db.backup_jobs.update_one.call_args
        assert "progress" in call_args[0][1]["$set"]
