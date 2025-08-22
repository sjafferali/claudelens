"""Backup service for handling backup operations."""

import asyncio
import json
import os
import time
from datetime import UTC, datetime
from typing import Any, AsyncGenerator, Callable, Dict, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.logging import get_logger
from app.models.backup_job import BackupJob
from app.models.backup_job import PyObjectId as JobPyObjectId
from app.models.backup_metadata import BackupMetadata
from app.models.backup_metadata import PyObjectId as MetadataPyObjectId
from app.schemas.backup_schemas import (
    BackupContents,
    BackupDetailResponse,
    BackupFilters,
    BackupMetadataResponse,
    BackupOptions,
    CreateBackupRequest,
    CreateBackupResponse,
    JobStatus,
    PagedBackupsResponse,
)
from app.services.compression_service import ChecksumCalculator, StreamingCompressor

logger = get_logger(__name__)

# Configuration
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/claudelens/backups")
BATCH_SIZE = 100
PROGRESS_UPDATE_INTERVAL = 1.0  # seconds


class BackupProgressTracker:
    """Track backup progress and send updates via WebSocket."""

    def __init__(
        self,
        job_id: str,
        total_items: int,
        update_callback: Optional[Callable] = None,
        db: Optional[AsyncIOMotorDatabase] = None,
    ):
        self.job_id = job_id
        self.total_items = total_items
        self.processed_items = 0
        self.update_callback = update_callback
        self.last_update_time = 0.0
        self.update_interval = PROGRESS_UPDATE_INTERVAL
        self.db = db
        self.current_item: Optional[str] = None

    async def increment(
        self, count: int = 1, current_item: Optional[str] = None
    ) -> None:
        """Increment progress and send update if needed."""
        self.processed_items += count
        if current_item:
            self.current_item = current_item

        # Throttle updates to avoid overwhelming WebSocket
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            await self.send_update()
            self.last_update_time = current_time

    async def send_update(self) -> None:
        """Send progress update via WebSocket and database."""
        progress = {
            "current": self.processed_items,
            "total": self.total_items,
            "percentage": (
                round((self.processed_items / self.total_items) * 100, 2)
                if self.total_items > 0
                else 0
            ),
            "current_item": self.current_item,
        }

        # Update progress in database
        if self.db:
            await self.db.backup_jobs.update_one(
                {"_id": ObjectId(self.job_id)}, {"$set": {"progress": progress}}
            )

        # Send progress via WebSocket
        if self.update_callback:
            await self.update_callback(self.job_id, progress)

    async def complete(self) -> None:
        """Mark backup as complete."""
        self.processed_items = self.total_items
        await self.send_update()


class BackupService:
    """Service for handling backup operations."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """Initialize the backup service."""
        self.db = db
        self.backup_dir = BACKUP_DIR

        # Ensure backup directory exists (skip if it's a test or we don't have permissions)
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
        except (PermissionError, OSError) as e:
            logger.warning(f"Could not create backup directory {self.backup_dir}: {e}")

    async def create_backup(
        self, request: CreateBackupRequest, user_id: str = "anonymous"
    ) -> CreateBackupResponse:
        """
        Create a new backup job and start processing in background.

        Args:
            request: Backup creation request
            user_id: User ID

        Returns:
            CreateBackupResponse with job details
        """
        # Estimate backup size and duration
        estimated_size = await self._estimate_backup_size(request.filters)
        estimated_duration = self._estimate_duration(estimated_size)

        # Create backup job with explicit ObjectId
        job_id = JobPyObjectId()
        backup_id = str(MetadataPyObjectId())  # Generate backup ID

        backup_job = BackupJob(
            _id=job_id,
            backup_id=backup_id,
            user_id=user_id,
            type=request.type.value,
            filters=request.filters.model_dump() if request.filters else {},
            options=request.options.model_dump() if request.options else {},
            status="queued",
            estimated_size_bytes=estimated_size,
            estimated_duration_seconds=estimated_duration,
        )

        # Save to database
        job_data = backup_job.model_dump(by_alias=True)
        job_data["_id"] = job_id
        await self.db.backup_jobs.insert_one(job_data)

        # Create backup metadata placeholder
        backup_metadata = BackupMetadata(
            _id=MetadataPyObjectId(backup_id),
            name=request.name,
            description=request.description,
            filename=f"{backup_id}.backup.zst",
            filepath=os.path.join(self.backup_dir, f"{backup_id}.backup.zst"),
            created_by=user_id,
            size_bytes=0,
            type=request.type.value,
            status="pending",
            filters=request.filters.model_dump() if request.filters else None,
            contents={},
            checksum="",
        )

        # Save backup metadata
        metadata_data = backup_metadata.model_dump(by_alias=True)
        metadata_data["_id"] = ObjectId(backup_id)
        await self.db.backup_metadata.insert_one(metadata_data)

        # Start processing in background
        asyncio.create_task(self._process_backup(str(job_id), request))

        logger.info(f"Created backup job {job_id} for user {user_id}")

        # Return the response with job details
        return CreateBackupResponse(
            job_id=str(job_id),
            backup_id=backup_id,
            status=JobStatus.QUEUED,
            created_at=datetime.now(UTC),
            estimated_size_bytes=estimated_size,
            estimated_duration_seconds=estimated_duration,
            message="Backup job created successfully",
        )

    async def _process_backup(self, job_id: str, request: CreateBackupRequest) -> None:
        """
        Process backup job in background.

        Args:
            job_id: Backup job ID
            request: Original backup request
        """
        try:
            # Update status to processing
            await self.db.backup_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": "processing",
                        "started_at": datetime.now(UTC),
                    }
                },
            )

            # Get job to access backup_id
            job_doc = await self.db.backup_jobs.find_one({"_id": ObjectId(job_id)})
            if not job_doc:
                raise ValueError(f"Job {job_id} not found")
            backup_id = job_doc["backup_id"]

            # Update backup metadata status
            await self.db.backup_metadata.update_one(
                {"_id": ObjectId(backup_id)},
                {"$set": {"status": "in_progress"}},
            )

            # Generate backup content
            content_generator = self._stream_collections(request.filters)

            # Set up compression if enabled
            options = request.options or BackupOptions(split_size_mb=100)
            if options.compress:
                compressor = StreamingCompressor(
                    compression_level=options.compression_level
                )
                content_generator = compressor.compress_stream(content_generator)

            # Calculate checksum while writing
            checksum_calculator = ChecksumCalculator()
            backup_path = os.path.join(self.backup_dir, f"{backup_id}.backup.zst")

            size = 0
            contents = {
                "projects_count": 0,
                "sessions_count": 0,
                "messages_count": 0,
                "prompts_count": 0,
                "ai_settings_count": 0,
                "total_documents": 0,
            }

            # Write backup file
            with open(backup_path, "wb") as f:
                async for chunk in content_generator:
                    size += len(chunk)
                    checksum_calculator.update(chunk)
                    f.write(chunk)

            # Get actual content counts
            contents = await self._count_backup_contents(request.filters)
            checksum = checksum_calculator.hexdigest()

            # Update backup metadata with final info
            await self.db.backup_metadata.update_one(
                {"_id": ObjectId(backup_id)},
                {
                    "$set": {
                        "status": "completed",
                        "size_bytes": size,
                        "compressed_size_bytes": size if options.compress else None,
                        "contents": contents,
                        "checksum": checksum,
                        "compression": (
                            {
                                "enabled": options.compress,
                                "level": options.compression_level,
                                "algorithm": "zstd",
                            }
                            if options.compress
                            else None
                        ),
                    }
                },
            )

            # Update job completion
            await self.db.backup_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.now(UTC),
                        "statistics": {
                            "file_size": size,
                            "checksum": checksum,
                            **contents,
                        },
                    }
                },
            )

            logger.info(f"Completed backup job {job_id}, created backup {backup_id}")

        except Exception as e:
            logger.error(f"Error processing backup job {job_id}: {e}")

            # Update job status to failed
            await self.db.backup_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": "failed",
                        "completed_at": datetime.now(UTC),
                        "errors": [
                            {
                                "message": str(e),
                                "timestamp": datetime.now(UTC).isoformat(),
                            }
                        ],
                    }
                },
            )

            # Update backup metadata status
            job_doc = await self.db.backup_jobs.find_one({"_id": ObjectId(job_id)})
            if job_doc and job_doc.get("backup_id"):
                await self.db.backup_metadata.update_one(
                    {"_id": ObjectId(job_doc["backup_id"])},
                    {
                        "$set": {
                            "status": "failed",
                            "error_message": str(e),
                        }
                    },
                )

            # Clean up partial files
            try:
                if job_doc:
                    backup_path = os.path.join(
                        self.backup_dir, f"{job_doc['backup_id']}.backup.zst"
                    )
                else:
                    backup_path = None
                if backup_path and os.path.exists(backup_path):
                    os.remove(backup_path)
            except Exception as cleanup_error:
                logger.warning(
                    f"Failed to cleanup partial backup file: {cleanup_error}"
                )

    async def _stream_collections(
        self, filters: Optional[BackupFilters]
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream database collections as backup data.

        Args:
            filters: Optional backup filters

        Yields:
            Backup data in chunks
        """
        backup_data = {
            "version": "1.0.0",
            "created_at": datetime.now(UTC).isoformat(),
            "collections": {},
        }

        # Stream header
        yield json.dumps({"header": backup_data}).encode("utf-8") + b"\n"

        # Define collections to backup
        collections = ["sessions", "messages", "projects", "prompts", "ai_settings"]

        for collection_name in collections:
            yield f'{{"collection":"{collection_name}","documents":['.encode("utf-8")

            # Build query based on filters
            query = await self._build_collection_query(collection_name, filters)

            # Stream documents in batches
            first_doc = True
            cursor = self.db[collection_name].find(query).batch_size(BATCH_SIZE)

            async for document in cursor:
                if not first_doc:
                    yield b","
                first_doc = False

                # Convert ObjectId to string for JSON serialization
                doc_json = self._serialize_document(document)
                yield json.dumps(doc_json).encode("utf-8")

            yield b"]}\n"

    async def _build_collection_query(
        self, collection_name: str, filters: Optional[BackupFilters]
    ) -> Dict[str, Any]:
        """Build MongoDB query for collection based on filters."""
        if not filters:
            return {}

        query: Dict[str, Any] = {}

        # Date range filters
        if filters.date_range:
            date_field = self._get_date_field_for_collection(collection_name)
            if date_field:
                date_query = {}
                if filters.date_range.get("start"):
                    date_query["$gte"] = filters.date_range["start"]
                if filters.date_range.get("end"):
                    date_query["$lte"] = filters.date_range["end"]
                if date_query:
                    query[date_field] = date_query

        # Project filters
        if filters.projects and collection_name in ["sessions", "messages"]:
            project_ids = [ObjectId(pid) for pid in filters.projects]
            if collection_name == "sessions":
                query["projectId"] = {"$in": project_ids}
            elif collection_name == "messages":
                # Find sessions in projects first
                session_ids = []
                async for session in self.db.sessions.find(
                    {"projectId": {"$in": project_ids}}, {"sessionId": 1}
                ):
                    session_ids.append(session["sessionId"])
                if session_ids:
                    query["sessionId"] = {"$in": session_ids}

        # Session filters
        if filters.sessions and collection_name == "messages":
            query["sessionId"] = {"$in": filters.sessions}
        elif filters.sessions and collection_name == "sessions":
            query["sessionId"] = {"$in": filters.sessions}

        return query

    def _get_date_field_for_collection(self, collection_name: str) -> Optional[str]:
        """Get the appropriate date field for a collection."""
        date_fields = {
            "sessions": "startedAt",
            "messages": "timestamp",
            "projects": "createdAt",
            "prompts": "createdAt",
            "ai_settings": "createdAt",
        }
        return date_fields.get(collection_name)

    def _serialize_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize MongoDB document for JSON output."""
        serialized: Dict[str, Any] = {}
        for key, value in document.items():
            if isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = self._serialize_document(value)
            elif isinstance(value, list):
                serialized[key] = [
                    self._serialize_document(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                serialized[key] = value
        return serialized

    async def _count_backup_contents(
        self, filters: Optional[BackupFilters]
    ) -> Dict[str, int]:
        """Count documents that will be included in backup."""
        contents = {
            "projects_count": 0,
            "sessions_count": 0,
            "messages_count": 0,
            "prompts_count": 0,
            "ai_settings_count": 0,
            "total_documents": 0,
        }

        collections = {
            "projects": "projects_count",
            "sessions": "sessions_count",
            "messages": "messages_count",
            "prompts": "prompts_count",
            "ai_settings": "ai_settings_count",
        }

        for collection_name, count_field in collections.items():
            query = await self._build_collection_query(collection_name, filters)
            count = await self.db[collection_name].count_documents(query)
            contents[count_field] = count
            contents["total_documents"] += count

        return contents

    async def list_backups(
        self, page: int = 1, size: int = 20, filters: Optional[Dict] = None
    ) -> PagedBackupsResponse:
        """
        List available backups with pagination.

        Args:
            page: Page number (1-based)
            size: Page size
            filters: Optional filters

        Returns:
            Paginated backup list
        """
        skip = (page - 1) * size
        query = {}

        # Apply filters if provided
        if filters:
            if filters.get("status"):
                query["status"] = {"$in": filters["status"]}
            if filters.get("type"):
                query["type"] = {"$in": filters["type"]}
            if filters.get("date_range"):
                date_range = filters["date_range"]
                date_query = {}
                if date_range.get("start"):
                    date_query["$gte"] = datetime.fromisoformat(date_range["start"])
                if date_range.get("end"):
                    date_query["$lte"] = datetime.fromisoformat(date_range["end"])
                if date_query:
                    query["created_at"] = date_query

        # Get total count
        total = await self.db.backup_metadata.count_documents(query)

        # Get backups
        cursor = (
            self.db.backup_metadata.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(size)
        )

        backups = []
        async for backup in cursor:
            backup_response = BackupMetadataResponse(
                _id=str(backup["_id"]),
                name=backup["name"],
                description=backup.get("description"),
                filename=backup["filename"],
                filepath=backup["filepath"],
                created_at=backup["created_at"],
                created_by=backup.get("created_by"),
                size_bytes=backup["size_bytes"],
                compressed_size_bytes=backup.get("compressed_size_bytes"),
                type=backup["type"],
                status=backup["status"],
                filters=(
                    BackupFilters(**backup["filters"])
                    if backup.get("filters")
                    else None
                ),
                contents=BackupContents(**backup["contents"]),
                checksum=backup["checksum"],
                version=backup["version"],
                can_restore=backup["status"] == "completed",
                error_message=backup.get("error_message"),
            )
            backups.append(backup_response)

        # Calculate summary
        total_size = sum(b.size_bytes for b in backups)

        # Get status counts for summary
        status_counts = await self._get_backup_counts_by_status()

        return PagedBackupsResponse(
            items=backups,
            pagination={
                "page": page,
                "size": size,
                "total": total,  # Keep for backward compatibility with tests
                "total_elements": total,  # For frontend
                "total_pages": (total + size - 1) // size,
                "has_more": page < (total + size - 1) // size,
            },
            summary={
                "total_size_bytes": total_size,
                "completed_count": status_counts.get("completed", 0),
                "failed_count": status_counts.get("failed", 0),
                "in_progress_count": status_counts.get("in_progress", 0)
                + status_counts.get("pending", 0),
            },
        )

    async def get_backup(self, backup_id: str) -> BackupDetailResponse:
        """
        Get detailed backup information.

        Args:
            backup_id: Backup ID

        Returns:
            Detailed backup information
        """
        backup = await self.db.backup_metadata.find_one({"_id": ObjectId(backup_id)})
        if not backup:
            raise ValueError(f"Backup {backup_id} not found")

        return BackupDetailResponse(
            _id=str(backup["_id"]),
            name=backup["name"],
            description=backup.get("description"),
            filename=backup["filename"],
            filepath=backup["filepath"],
            created_at=backup["created_at"],
            created_by=backup.get("created_by"),
            size_bytes=backup["size_bytes"],
            compressed_size_bytes=backup.get("compressed_size_bytes"),
            type=backup["type"],
            status=backup["status"],
            filters=(
                BackupFilters(**backup["filters"]) if backup.get("filters") else None
            ),
            contents=BackupContents(**backup["contents"]),
            checksum=backup["checksum"],
            version=backup["version"],
            can_restore=backup["status"] == "completed",
            error_message=backup.get("error_message"),
            storage_location=backup["filepath"],
            compression=backup.get("compression"),
            encryption=backup.get("encryption"),
            restore_history=backup.get("restore_history", []),
        )

    async def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup and its files.

        Args:
            backup_id: Backup ID

        Returns:
            True if deleted successfully
        """
        backup = await self.db.backup_metadata.find_one({"_id": ObjectId(backup_id)})
        if not backup:
            return False

        try:
            # Update status to deleting
            await self.db.backup_metadata.update_one(
                {"_id": ObjectId(backup_id)}, {"$set": {"status": "deleting"}}
            )

            # Delete physical file
            if os.path.exists(backup["filepath"]):
                os.remove(backup["filepath"])

            # Delete from database
            await self.db.backup_metadata.delete_one({"_id": ObjectId(backup_id)})

            logger.info(f"Deleted backup {backup_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting backup {backup_id}: {e}")
            # Restore status
            await self.db.backup_metadata.update_one(
                {"_id": ObjectId(backup_id)}, {"$set": {"status": backup["status"]}}
            )
            return False

    async def download_backup(self, backup_id: str) -> AsyncGenerator[bytes, None]:
        """
        Stream backup file for download.

        Args:
            backup_id: Backup ID

        Yields:
            File content in chunks
        """
        backup = await self.db.backup_metadata.find_one({"_id": ObjectId(backup_id)})
        if not backup:
            raise ValueError(f"Backup {backup_id} not found")

        if backup["status"] != "completed":
            raise ValueError(f"Backup {backup_id} is not ready for download")

        file_path = backup["filepath"]
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Backup file not found: {file_path}")

        # Stream file in chunks
        chunk_size = 8192
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    async def _estimate_backup_size(self, filters: Optional[BackupFilters]) -> int:
        """Estimate backup size based on filters."""
        if not filters:
            # Estimate full backup size
            collections = ["sessions", "messages", "projects", "prompts", "ai_settings"]
            total_docs = 0
            for collection in collections:
                count = await self.db[collection].count_documents({})
                total_docs += count

            # Rough estimate: 2KB per document
            return total_docs * 2048

        # For filtered backups, count specific documents
        contents = await self._count_backup_contents(filters)
        return contents["total_documents"] * 2048

    def _estimate_duration(self, estimated_size: int) -> int:
        """Estimate processing duration in seconds."""
        # Roughly 1MB per second processing
        return max(1, estimated_size // (1024 * 1024))

    async def _get_backup_counts_by_status(self) -> Dict[str, int]:
        """Get backup counts grouped by status."""
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        result = {}
        async for doc in self.db.backup_metadata.aggregate(pipeline):
            result[doc["_id"]] = doc["count"]
        return result

    async def _get_backup_counts_by_type(self) -> Dict[str, int]:
        """Get backup counts grouped by type."""
        pipeline = [{"$group": {"_id": "$type", "count": {"$sum": 1}}}]
        result = {}
        async for doc in self.db.backup_metadata.aggregate(pipeline):
            result[doc["_id"]] = doc["count"]
        return result
