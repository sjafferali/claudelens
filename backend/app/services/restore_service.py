"""Restore service for handling backup restore operations."""

import asyncio
import json
import os
from datetime import UTC, datetime
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.logging import get_logger
from app.models.backup_job import PyObjectId, RestoreJob
from app.schemas.backup_schemas import (
    BackupContents,
    ConflictResolution,
    CreateRestoreRequest,
    CreateRestoreResponse,
    JobStatus,
    PreviewBackupResponse,
    RestoreMode,
    RestoreProgressResponse,
)
from app.services.compression_service import StreamingCompressor

logger = get_logger(__name__)

# Configuration
BATCH_SIZE = 100
RESTORE_CHUNK_SIZE = 8192


class RestoreTransaction:
    """Track restore operations for potential rollback."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.inserted_ids: List[tuple[str, str]] = []
        self.updated_ids: List[tuple[str, str]] = []
        self.backup_data: Dict[str, Dict[str, Any]] = {}
        self.id_mappings: Dict[str, str] = {}  # old_id -> new_id mapping

    async def backup_existing(self, collection: str, doc_id: str) -> None:
        """Backup existing document before update."""
        existing = await self.db[collection].find_one({"_id": ObjectId(doc_id)})
        if existing:
            if collection not in self.backup_data:
                self.backup_data[collection] = {}
            self.backup_data[collection][doc_id] = existing
            self.updated_ids.append((collection, doc_id))
        else:
            self.inserted_ids.append((collection, doc_id))

    async def track_insertion(self, collection: str, doc_id: str) -> None:
        """Track a newly inserted document."""
        self.inserted_ids.append((collection, doc_id))

    def track_insert(self, collection: str, doc_id: str) -> None:
        """Alias for track_insertion for compatibility."""
        self.inserted_ids.append((collection, doc_id))

    def track_update(self, collection: str, doc_id: str) -> None:
        """Track an updated document."""
        self.updated_ids.append((collection, doc_id))

    def add_id_mapping(self, old_id: str, new_id: str) -> None:
        """Track ObjectId mapping for reference updates."""
        self.id_mappings[old_id] = new_id

    def clear(self) -> None:
        """Clear all tracked operations."""
        self.inserted_ids.clear()
        self.updated_ids.clear()
        self.backup_data.clear()
        self.id_mappings.clear()

    async def rollback(self) -> None:
        """Rollback all changes made during restore."""
        logger.info("Starting restore rollback")

        # Delete inserted documents
        for collection, doc_id in self.inserted_ids:
            try:
                await self.db[collection].delete_one({"_id": ObjectId(doc_id)})
            except Exception as e:
                logger.error(
                    f"Failed to rollback inserted document {doc_id} in {collection}: {e}"
                )

        # Restore updated documents
        for collection, backups in self.backup_data.items():
            for doc_id, backup in backups.items():
                try:
                    await self.db[collection].replace_one(
                        {"_id": ObjectId(doc_id)}, backup
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to restore document {doc_id} in {collection}: {e}"
                    )

        logger.info("Restore rollback completed")


class RestoreService:
    """Service for handling backup restore operations."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """Initialize the restore service."""
        self.db = db

    async def create_restore_job(
        self, request: CreateRestoreRequest, user_id: str = "anonymous"
    ) -> CreateRestoreResponse:
        """
        Create a new restore job and start processing in background.

        Args:
            request: Restore creation request
            user_id: User ID

        Returns:
            CreateRestoreResponse with job details
        """
        # Validate backup exists and is restorable
        backup = await self.db.backup_metadata.find_one(
            {"_id": ObjectId(request.backup_id)}
        )
        if not backup:
            raise ValueError(f"Backup {request.backup_id} not found")

        if backup["status"] != "completed":
            raise ValueError(
                f"Backup {request.backup_id} is not completed and cannot be restored"
            )

        # Create restore job
        job_id = PyObjectId()
        restore_job = RestoreJob(
            _id=job_id,
            backup_id=request.backup_id,
            user_id=user_id,
            mode=request.mode.value,
            target=request.target,
            options=request.options or {},
            selections=request.selections,
            conflict_resolution=request.conflict_resolution.value,
            status="queued",
        )

        # Save to database
        job_data = restore_job.model_dump(by_alias=True)
        job_data["_id"] = job_id
        await self.db.restore_jobs.insert_one(job_data)

        # Start processing in background
        asyncio.create_task(self._process_restore(str(job_id), request))

        logger.info(f"Created restore job {job_id} for backup {request.backup_id}")

        # Return the response with job details
        return CreateRestoreResponse(
            job_id=str(job_id),
            status=JobStatus.QUEUED,
            created_at=datetime.now(UTC),
            backup_id=request.backup_id,
            mode=request.mode,
            estimated_duration_seconds=60,  # Basic estimate
            message="Restore job created successfully",
        )

    async def _process_restore(
        self, job_id: str, request: CreateRestoreRequest
    ) -> None:
        """
        Process restore job in background.

        Args:
            job_id: Restore job ID
            request: Original restore request
        """
        transaction = RestoreTransaction(self.db)

        try:
            # Update status to validating
            await self.db.restore_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": "validating",
                        "started_at": datetime.now(UTC),
                    }
                },
            )

            # Validate backup
            validation_result = await self.validate_backup(request.backup_id)
            if not validation_result["valid"]:
                raise ValueError(
                    f"Backup validation failed: {validation_result['errors']}"
                )

            await self.db.restore_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {"validation_result": validation_result}},
            )

            # Update status to processing
            await self.db.restore_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {"status": "processing"}},
            )

            # Process restore
            statistics = await self.restore_backup(
                request.backup_id,
                {
                    "mode": request.mode,
                    "conflict_resolution": request.conflict_resolution,
                    "selections": request.selections,
                    "transaction": transaction,
                    "job_id": job_id,
                },
            )

            # Update job completion
            await self.db.restore_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.now(UTC),
                        "statistics": statistics,
                        "rollback_available": True,
                        "rollback_data": {
                            "inserted_count": len(transaction.inserted_ids),
                            "updated_count": len(transaction.updated_ids),
                            "id_mappings_count": len(transaction.id_mappings),
                        },
                        "progress": {
                            "current": statistics.get("total_processed", 0),
                            "total": statistics.get("total_processed", 0),
                            "percentage": 100,
                            "current_collection": None,
                            "message": "Restore completed successfully",
                        },
                    }
                },
            )

            # Add restore to backup history
            await self.db.backup_metadata.update_one(
                {"_id": ObjectId(request.backup_id)},
                {
                    "$push": {
                        "restore_history": {
                            "job_id": job_id,
                            "user_id": request.backup_id,  # Using backup_id as user_id placeholder
                            "restored_at": datetime.now(UTC),
                            "mode": request.mode,
                            "conflict_resolution": request.conflict_resolution,
                            "statistics": statistics,
                        }
                    }
                },
            )

            logger.info(f"Completed restore job {job_id}")

        except Exception as e:
            logger.error(f"Error processing restore job {job_id}: {e}")

            # Rollback changes
            try:
                await transaction.rollback()
            except Exception as rollback_error:
                logger.error(
                    f"Failed to rollback restore job {job_id}: {rollback_error}"
                )

            # Update job with error
            await self.db.restore_jobs.update_one(
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

    async def execute_restore(
        self, job_id: str, request: CreateRestoreRequest
    ) -> Dict[str, Any]:
        """
        Execute restore operation (compatibility method for tests).

        Args:
            job_id: Restore job ID
            request: Restore request

        Returns:
            Restore statistics
        """
        return await self.restore_backup(
            request.backup_id,
            {
                "mode": request.mode,
                "conflict_resolution": request.conflict_resolution,
                "selections": request.selections,
                "job_id": job_id,
            },
        )

    async def restore_backup(
        self, backup_id: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Restore data from backup.

        Args:
            backup_id: Backup ID to restore
            options: Restore options

        Returns:
            Restore statistics
        """
        statistics = {
            "collections_processed": 0,
            "documents_processed": 0,
            "documents_inserted": 0,
            "documents_updated": 0,
            "documents_skipped": 0,
            "conflicts_resolved": 0,
            "total_processed": 0,
        }

        job_id = options.get("job_id")

        # Start MongoDB session for atomic operations
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                try:
                    # Stream backup data and process in batches
                    current_collection = None
                    batch: list[Dict[str, Any]] = []

                    async for document in self._stream_backup_data(backup_id):
                        if "collection" in document:
                            # Process previous batch if switching collections
                            if batch and current_collection:
                                batch_stats = await self._restore_batch(
                                    batch, options, session
                                )
                                self._update_statistics(statistics, batch_stats)
                                batch = []

                            current_collection = document["collection"]
                            statistics["collections_processed"] += 1

                            # Update progress
                            if job_id:
                                await self.db.restore_jobs.update_one(
                                    {"_id": ObjectId(job_id)},
                                    {
                                        "$set": {
                                            "progress.current_collection": current_collection,
                                            "progress.message": f"Restoring {current_collection}",
                                        }
                                    },
                                )

                            logger.info(
                                f"Starting restore of collection: {current_collection}"
                            )
                            continue

                        # Add document to batch
                        document["_collection"] = current_collection
                        batch.append(document)

                        # Process batch when it reaches size limit
                        if len(batch) >= BATCH_SIZE:
                            # Check if we're in merge mode
                            if (
                                options.get("mode") == "merge"
                                or options.get("mode") == RestoreMode.MERGE
                            ):
                                batch_stats = await self._merge_collection_data(
                                    current_collection or "",
                                    batch,
                                    options.get("merge_strategy", "deep"),
                                )
                                # Convert merge result to expected format
                                if isinstance(batch_stats, dict):
                                    batch_stats = {
                                        "processed": batch_stats.get("merged", 0)
                                        + batch_stats.get("inserted", 0),
                                        "inserted": batch_stats.get("inserted", 0),
                                        "updated": batch_stats.get("merged", 0),
                                        "skipped": 0,
                                        "conflicts": batch_stats.get("conflicts", 0),
                                    }
                            else:
                                batch_stats = await self._restore_batch(
                                    batch, options, session
                                )
                            self._update_statistics(statistics, batch_stats)
                            batch = []

                    # Process final batch
                    if batch and current_collection:
                        # Check if we're in merge mode
                        if (
                            options.get("mode") == "merge"
                            or options.get("mode") == RestoreMode.MERGE
                        ):
                            batch_stats = await self._merge_collection_data(
                                current_collection or "",
                                batch,
                                options.get("merge_strategy", "deep"),
                            )
                            # Convert merge result to expected format
                            if isinstance(batch_stats, dict):
                                batch_stats = {
                                    "processed": batch_stats.get("merged", 0)
                                    + batch_stats.get("inserted", 0),
                                    "inserted": batch_stats.get("inserted", 0),
                                    "updated": batch_stats.get("merged", 0),
                                    "skipped": 0,
                                    "conflicts": batch_stats.get("conflicts", 0),
                                }
                        else:
                            batch_stats = await self._restore_batch(
                                batch, options, session
                            )
                        self._update_statistics(statistics, batch_stats)

                    # Commit transaction
                    await session.commit_transaction()

                except Exception as e:
                    await session.abort_transaction()
                    raise e

        statistics["total_processed"] = statistics["documents_processed"]
        return statistics

    async def validate_backup(self, backup_id: str, return_tuple: bool = False) -> Any:
        """
        Validate backup integrity and compatibility.

        Args:
            backup_id: Backup ID to validate

        Returns:
            Validation result
        """
        validation_result: Dict[str, Any] = {
            "valid": False,
            "backup_id": backup_id,
            "errors": [],
            "warnings": [],
            "metadata": {},
        }
        errors = validation_result["errors"]
        warnings = validation_result["warnings"]

        try:
            # Get backup metadata
            backup = await self.db.backup_metadata.find_one(
                {"_id": ObjectId(backup_id)}
            )
            if not backup:
                errors.append("Backup not found")
                return validation_result

            validation_result["metadata"] = {
                "name": backup["name"],
                "created_at": backup["created_at"],
                "type": backup["type"],
                "size_bytes": backup["size_bytes"],
                "checksum": backup["checksum"],
            }

            # Check backup file exists
            if not os.path.exists(backup["filepath"]):
                errors.append("Backup file not found on disk")
                return validation_result

            # Validate file integrity by checking first few chunks
            try:
                chunk_count = 0
                async for _ in self._stream_backup_data(backup_id):
                    chunk_count += 1
                    if chunk_count > 10:  # Sample first 10 chunks
                        break

                if chunk_count == 0:
                    errors.append("Backup file appears to be empty or corrupted")
                    return validation_result

            except Exception as e:
                errors.append(f"Failed to read backup file: {str(e)}")
                return validation_result

            # Check for potential conflicts (basic check)
            if backup["contents"]:
                total_docs = backup["contents"].get("total_documents", 0)
                if total_docs > 100000:
                    warnings.append(
                        f"Large backup with {total_docs} documents may take significant time to restore"
                    )

            validation_result["valid"] = len(errors) == 0

        except Exception as e:
            errors.append(f"Validation failed: {str(e)}")

        # Support both return formats for backward compatibility
        if return_tuple:
            # Legacy format for tests
            if validation_result["valid"]:
                return (True, None)
            else:
                return (False, errors[0] if errors else "Validation failed")

        return validation_result

    async def preview_backup(self, backup_id: str) -> PreviewBackupResponse:
        """
        Preview backup contents without restoring.

        Args:
            backup_id: Backup ID to preview

        Returns:
            Preview information
        """
        backup = await self.db.backup_metadata.find_one({"_id": ObjectId(backup_id)})
        if not backup:
            raise ValueError(f"Backup {backup_id} not found")

        # Sample some documents from each collection
        preview_data: Dict[str, Any] = {}
        current_collection = None
        sample_count = 0
        max_samples_per_collection = 5

        try:
            async for document in self._stream_backup_data(backup_id):
                if "collection" in document:
                    current_collection = document["collection"]
                    preview_data[current_collection] = []
                    sample_count = 0
                    continue

                if current_collection and sample_count < max_samples_per_collection:
                    # Remove sensitive data for preview
                    preview_doc = {
                        "_id": document.get("_id"),
                        "type": type(document).__name__,
                        "fields": list(document.keys())[:10],  # First 10 fields
                    }
                    preview_data[current_collection].append(preview_doc)
                    sample_count += 1

        except Exception as e:
            logger.warning(
                f"Failed to generate full preview for backup {backup_id}: {e}"
            )

        return PreviewBackupResponse(
            backup_id=backup_id,
            name=backup["name"],
            created_at=backup["created_at"],
            type=backup["type"],
            contents=BackupContents(**backup["contents"]),
            filters=backup.get("filters"),
            size_bytes=backup["size_bytes"],
            compressed_size_bytes=backup.get("compressed_size_bytes"),
            preview_data=preview_data,
            can_restore=backup["status"] == "completed",
            warnings=["Preview shows limited sample data"] if preview_data else [],
        )

    async def _restore_batch(
        self, batch: List[Dict[str, Any]], options: Dict[str, Any], session: Any
    ) -> Dict[str, Any]:
        """
        Restore a batch of documents.

        Args:
            batch: List of documents to restore
            options: Restore options
            session: MongoDB session

        Returns:
            Batch processing statistics
        """
        stats = {
            "processed": len(batch),
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "conflicts": 0,
        }

        if not batch:
            return stats

        collection_name = batch[0].get("_collection")
        if not collection_name:
            return stats

        collection = self.db[collection_name]
        conflict_resolution = options.get(
            "conflict_resolution", ConflictResolution.SKIP
        )
        transaction = options.get("transaction")

        for document in batch:
            try:
                # Remove metadata fields
                doc = {k: v for k, v in document.items() if not k.startswith("_")}

                # Check if document should be restored in selective mode
                if (
                    options.get("mode") == "selective"
                    or options.get("mode") == RestoreMode.SELECTIVE
                ):
                    selections = options.get("selections", {})
                    if selections:
                        criteria = selections.get("criteria", {})

                        # Filter by project IDs
                        if collection_name == "projects" and criteria.get(
                            "project_ids"
                        ):
                            if str(doc.get("_id", "")) not in criteria["project_ids"]:
                                stats["skipped"] += 1
                                continue

                        # Filter by session IDs
                        if collection_name == "sessions":
                            session_id = str(doc.get("_id", ""))
                            project_id = str(doc.get("projectId", ""))

                            # Check if session is explicitly selected
                            if (
                                criteria.get("session_ids")
                                and session_id not in criteria["session_ids"]
                            ):
                                # Also check if its project is selected
                                if (
                                    not criteria.get("project_ids")
                                    or project_id not in criteria["project_ids"]
                                ):
                                    stats["skipped"] += 1
                                    continue

                        # Filter messages by their session
                        if collection_name == "messages":
                            session_id = doc.get("sessionId", "")
                            # Check if this message's session is being restored
                            if (
                                criteria.get("session_ids")
                                and session_id not in criteria["session_ids"]
                            ):
                                # Skip this message as its session is not selected
                                stats["skipped"] += 1
                                continue

                # Handle ObjectId conversion
                if "_id" in doc and isinstance(doc["_id"], str):
                    original_id = doc["_id"]
                    doc["_id"] = ObjectId(original_id)

                    # Check if document already exists
                    existing = await collection.find_one(
                        {"_id": doc["_id"]}, session=session
                    )

                    if existing:
                        stats["conflicts"] += 1
                        resolved_docs = await self._handle_conflicts(
                            [doc], conflict_resolution
                        )

                        if resolved_docs:
                            resolved_doc = resolved_docs[0]
                            if conflict_resolution == ConflictResolution.OVERWRITE:
                                if transaction:
                                    await transaction.backup_existing(
                                        collection_name, str(doc["_id"])
                                    )
                                await collection.replace_one(
                                    {"_id": doc["_id"]}, resolved_doc, session=session
                                )
                                stats["updated"] += 1
                            elif conflict_resolution == ConflictResolution.RENAME:
                                new_id = ObjectId()
                                resolved_doc["_id"] = new_id
                                if transaction:
                                    await transaction.track_insertion(
                                        collection_name, str(new_id)
                                    )
                                    transaction.add_id_mapping(original_id, str(new_id))
                                await collection.insert_one(
                                    resolved_doc, session=session
                                )
                                stats["inserted"] += 1
                            else:  # SKIP
                                stats["skipped"] += 1
                        else:
                            stats["skipped"] += 1
                    else:
                        # New document
                        if transaction:
                            await transaction.track_insertion(
                                collection_name, str(doc["_id"])
                            )
                        await collection.insert_one(doc, session=session)
                        stats["inserted"] += 1
                else:
                    # Document without _id, generate new one
                    new_id = ObjectId()
                    doc["_id"] = new_id
                    if transaction:
                        await transaction.track_insertion(collection_name, str(new_id))
                    await collection.insert_one(doc, session=session)
                    stats["inserted"] += 1

            except Exception as e:
                logger.error(f"Failed to restore document in {collection_name}: {e}")
                # Continue processing other documents

        return stats

    async def _handle_conflicts(
        self, documents: List[Dict], resolution: str
    ) -> List[Dict]:
        """
        Handle document conflicts based on resolution strategy.

        Args:
            documents: List of documents with conflicts
            resolution: Conflict resolution strategy

        Returns:
            List of resolved documents
        """
        if resolution == ConflictResolution.SKIP:
            return []
        elif resolution == ConflictResolution.OVERWRITE:
            return documents
        elif resolution == ConflictResolution.RENAME:
            # Generate new IDs for renamed documents
            for doc in documents:
                doc["_id"] = ObjectId()
            return documents
        elif resolution == ConflictResolution.MERGE:
            # Basic merge strategy - for now, just return the incoming documents
            # In a full implementation, this would merge fields intelligently
            return documents
        else:
            return []

    async def _stream_backup_data(self, backup_id: str) -> AsyncGenerator[Dict, None]:
        """
        Stream backup data for processing.

        Args:
            backup_id: Backup ID to stream

        Yields:
            Backup data chunks
        """
        backup = await self.db.backup_metadata.find_one({"_id": ObjectId(backup_id)})
        if not backup:
            raise ValueError(f"Backup {backup_id} not found")

        file_path = backup["filepath"]
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Backup file not found: {file_path}")

        # Check if backup is compressed
        is_compressed = backup.get("compression", {}).get("enabled", True)

        try:
            if is_compressed:
                # Stream and decompress
                compressor = StreamingCompressor()

                async def read_compressed_file() -> AsyncGenerator[bytes, None]:
                    with open(file_path, "rb") as f:
                        while True:
                            chunk = f.read(RESTORE_CHUNK_SIZE)
                            if not chunk:
                                break
                            yield chunk

                # Decompress and parse JSON lines
                buffer = b""
                async for decompressed_chunk in compressor.decompress_stream(
                    read_compressed_file()
                ):
                    buffer += decompressed_chunk

                    # Process complete lines
                    while b"\n" in buffer:
                        line_bytes, buffer = buffer.split(b"\n", 1)
                        if line_bytes.strip():
                            try:
                                data = json.loads(line_bytes.decode("utf-8"))

                                # Handle different data types
                                if "header" in data:
                                    continue  # Skip header
                                elif "collection" in data:
                                    yield {"collection": data["collection"]}
                                    # Yield documents from this collection
                                    for doc in data.get("documents", []):
                                        yield doc
                                else:
                                    yield data

                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse JSON line: {e}")
                                continue

                # Process remaining buffer
                if buffer.strip():
                    try:
                        data = json.loads(buffer.decode("utf-8"))
                        yield data
                    except json.JSONDecodeError:
                        pass

            else:
                # Read uncompressed file
                with open(file_path, "r") as f:
                    for text_line in f:
                        if text_line.strip():
                            try:
                                data = json.loads(text_line)

                                if "header" in data:
                                    continue
                                elif "collection" in data:
                                    yield {"collection": data["collection"]}
                                    for doc in data.get("documents", []):
                                        yield doc
                                else:
                                    yield data

                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse JSON line: {e}")
                                continue

        except Exception as e:
            logger.error(f"Error streaming backup data: {e}")
            raise

    def _update_statistics(self, total_stats: Dict, batch_stats: Dict) -> None:
        """Update total statistics with batch statistics."""
        total_stats["documents_processed"] += batch_stats["processed"]
        total_stats["documents_inserted"] += batch_stats["inserted"]
        total_stats["documents_updated"] += batch_stats["updated"]
        total_stats["documents_skipped"] += batch_stats["skipped"]
        total_stats["conflicts_resolved"] += batch_stats["conflicts"]

    async def get_restore_progress(self, job_id: str) -> RestoreProgressResponse:
        """
        Get restore job progress.

        Args:
            job_id: Restore job ID

        Returns:
            Progress information
        """
        job = await self.db.restore_jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise ValueError(f"Restore job {job_id} not found")

        return RestoreProgressResponse(
            job_id=job_id,
            status=job["status"],
            progress=job.get("progress", {}),
            statistics=job.get("statistics", {}),
            errors=job.get("errors", []),
            completed_at=job.get("completed_at"),
        )

    async def _handle_conflict_resolution(
        self,
        collection_name_or_document: Any,
        documents_or_existing: Any = None,
        resolution_or_none: Any = None,
        transaction: Any = None,
    ) -> Any:
        """
        Handle conflict resolution - supports both single document and batch operations.

        This method supports two signatures:
        1. Single document: _handle_conflict_resolution(document, existing, resolution)
        2. Batch operation: _handle_conflict_resolution(collection_name, documents, resolution, transaction)
        """
        # Check if this is batch operation (4 arguments)
        if transaction is not None:
            # Batch operation
            collection_name = collection_name_or_document
            documents = documents_or_existing
            resolution = resolution_or_none

            stats = {
                "inserted": 0,
                "updated": 0,
                "skipped": 0,
            }

            collection = self.db[collection_name]

            for doc in documents:
                existing = await collection.find_one({"_id": doc.get("_id")})

                if existing:
                    if resolution == ConflictResolution.SKIP:
                        stats["skipped"] += 1
                    elif resolution == ConflictResolution.OVERWRITE:
                        await collection.replace_one({"_id": doc["_id"]}, doc)
                        stats["updated"] += 1
                    elif resolution == ConflictResolution.RENAME:
                        new_doc = doc.copy()
                        new_doc["_id"] = ObjectId()
                        new_doc["name"] = f"{doc.get('name', 'Document')} (Restored)"
                        await collection.insert_one(new_doc)
                        stats["inserted"] += 1
                else:
                    await collection.insert_one(doc)
                    stats["inserted"] += 1

            return stats

        # Single document operation (3 arguments)
        else:
            document = collection_name_or_document
            existing = documents_or_existing
            resolution = resolution_or_none

            if resolution == ConflictResolution.SKIP:
                return None
            elif resolution == ConflictResolution.OVERWRITE:
                return document
            elif resolution == ConflictResolution.RENAME:
                # Create new document with different ID
                new_doc = document.copy()
                new_doc["_id"] = ObjectId()
                return new_doc
            elif resolution == ConflictResolution.MERGE:
                # Merge existing and new document
                merged = existing.copy()
                merged.update(document)
                return merged
            else:
                return None

    def _map_object_ids(
        self, documents_or_document: Any, id_mappings: Optional[Dict[str, str]] = None
    ) -> Any:
        """
        Map ObjectIds in document references.

        Supports two modes:
        1. Single document with mappings: _map_object_ids(document, id_mappings)
        2. Multiple documents (creates new IDs): _map_object_ids(documents)

        Args:
            documents_or_document: Document(s) to process
            id_mappings: Optional mapping of old IDs to new IDs

        Returns:
            For single document: Document with updated references
            For multiple documents: Tuple of (mapped_docs, id_mapping)
        """
        # Check if this is batch operation (list of documents)
        if isinstance(documents_or_document, list):
            documents = documents_or_document
            id_mapping = {}
            mapped_docs = []

            # First pass: Create new IDs for all documents
            for doc in documents:
                old_id = doc.get("_id")
                if old_id:
                    new_id = ObjectId()
                    id_mapping[str(old_id)] = new_id
                    new_doc = doc.copy()
                    new_doc["_id"] = new_id
                    mapped_docs.append(new_doc)
                else:
                    mapped_docs.append(doc.copy())

            # Second pass: Update references
            for doc in mapped_docs:
                for key, value in doc.items():
                    if key != "_id" and isinstance(value, ObjectId):
                        str_id = str(value)
                        if str_id in id_mapping:
                            doc[key] = id_mapping[str_id]
                    elif key.endswith("_id") and value in id_mapping:
                        doc[key] = id_mapping[value]

            return mapped_docs, id_mapping

        # Single document operation
        else:
            document = documents_or_document
            if not id_mappings:
                return document

            def map_value(value: Any) -> Any:
                if isinstance(value, str) and value in id_mappings:
                    return id_mappings[value]
                elif isinstance(value, dict):
                    return {k: map_value(v) for k, v in value.items()}
                elif isinstance(value, list):
                    return [map_value(item) for item in value]
                else:
                    return value

            return {key: map_value(value) for key, value in document.items()}

    async def _decompress_backup(
        self, backup_path: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Decompress and stream backup data.

        Args:
            backup_path: Path to compressed backup file

        Yields:
            Decompressed backup data
        """
        compressor = StreamingCompressor()

        async def read_file() -> AsyncGenerator[bytes, None]:
            with open(backup_path, "rb") as f:
                while True:
                    chunk = f.read(RESTORE_CHUNK_SIZE)
                    if not chunk:
                        break
                    yield chunk

        buffer = b""
        async for decompressed_chunk in compressor.decompress_stream(read_file()):
            buffer += decompressed_chunk

            # Process complete lines
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                if line.strip():
                    try:
                        data = json.loads(line.decode("utf-8"))
                        yield data
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON line: {e}")
                        continue

        # Process remaining buffer
        if buffer.strip():
            try:
                data = json.loads(buffer.decode("utf-8"))
                yield data
            except json.JSONDecodeError:
                pass

    async def create_restore_job_from_upload(
        self,
        user_id: str,
        file_path: str,
        filename: str,
        mode: str = "full",
        conflict_resolution: str = "skip",
    ) -> CreateRestoreResponse:
        """
        Create a restore job from an uploaded backup file.

        Args:
            user_id: User ID
            file_path: Path to uploaded backup file
            filename: Original filename
            mode: Restore mode
            conflict_resolution: Conflict resolution strategy

        Returns:
            CreateRestoreResponse with job details
        """
        # Create a temporary backup metadata entry for the uploaded file
        backup_id = str(PyObjectId())

        # Save backup metadata for the uploaded file
        backup_metadata = {
            "_id": ObjectId(backup_id),
            "name": f"Upload: {filename}",
            "description": "Uploaded backup file for restore",
            "filename": filename,
            "filepath": file_path,
            "created_at": datetime.now(UTC),
            "created_by": user_id,
            "size_bytes": os.path.getsize(file_path)
            if os.path.exists(file_path)
            else 0,
            "type": "full",
            "status": "completed",
            "contents": {},
            "checksum": "",
            "version": "1.0.0",
        }

        await self.db.backup_metadata.insert_one(backup_metadata)

        # Create restore request
        request = CreateRestoreRequest(
            backup_id=backup_id,
            mode=RestoreMode(mode),
            conflict_resolution=ConflictResolution(conflict_resolution),
        )

        # Create restore job using existing method
        return await self.create_restore_job(request, user_id)

    async def process_restore_from_upload(
        self, job_id: str, file_path: str, progress_callback: Optional[Callable] = None
    ) -> None:
        """
        Process restore from an uploaded file.

        Args:
            job_id: Restore job ID
            file_path: Path to uploaded backup file
            progress_callback: Optional callback for progress updates
        """
        # Get the job to find the backup_id
        job = await self.db.restore_jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise ValueError(f"Restore job {job_id} not found")

        # Create restore request from job data
        request = CreateRestoreRequest(
            backup_id=job["backup_id"],
            mode=job["mode"],
            conflict_resolution=job.get("conflict_resolution", "skip"),
            target=job.get("target"),
            options=job.get("options"),
            selections=job.get("selections"),
        )

        # Process the restore using existing method
        await self._process_restore(job_id, request)

    async def preview_backup_contents(self, backup_id: str) -> Dict[str, Any]:
        """
        Get preview data for a backup.

        Args:
            backup_id: Backup ID to preview

        Returns:
            Preview data dictionary
        """
        backup = await self.db.backup_metadata.find_one({"_id": ObjectId(backup_id)})
        if not backup:
            raise ValueError(f"Backup {backup_id} not found")

        preview_data: Dict[str, Any] = {
            "collections": {},
            "summary": {
                "total_documents": 0,
                "collections_count": 0,
            },
        }

        # If backup has contents metadata, use it
        if backup.get("contents"):
            contents = backup["contents"]
            total_docs = contents.get("total_documents", 0)
            preview_data["summary"]["total_documents"] = (
                total_docs if isinstance(total_docs, int) else 0
            )
            preview_data["summary"]["collections_count"] = sum(
                1 for k, v in contents.items() if k.endswith("_count") and v > 0
            )

            # Try to get sample data from the backup file
            try:
                sample_limit = 10  # Limit samples per collection
                samples_by_collection: Dict[str, List[Dict[str, Any]]] = {}
                current_collection = None
                collection_counts: Dict[str, int] = {}

                # Stream through backup to get samples
                async for document in self._stream_backup_data(backup_id):
                    if "collection" in document:
                        current_collection = document["collection"]
                        if current_collection not in samples_by_collection:
                            samples_by_collection[current_collection] = []
                            collection_counts[current_collection] = 0
                    elif (
                        current_collection
                        and collection_counts[current_collection] < sample_limit
                    ):
                        # Add sample document
                        samples_by_collection[current_collection].append(document)
                        collection_counts[current_collection] += 1

                    # Stop if we have enough samples
                    if all(
                        count >= sample_limit for count in collection_counts.values()
                    ):
                        break

                # Add samples to preview data
                for collection_name, samples in samples_by_collection.items():
                    preview_data["collections"][collection_name] = {
                        "count": contents.get(
                            f"{collection_name[:-1]}_count", len(samples)
                        ),
                        "sample_data": samples,
                    }
            except Exception as e:
                logger.warning(f"Could not extract sample data from backup: {e}")
                # Fall back to metadata only
                for key, count in contents.items():
                    if key.endswith("_count") and key != "total_documents":
                        collection_name = key.replace("_count", "s")
                        preview_data["collections"][collection_name] = {
                            "count": count if isinstance(count, int) else 0,
                            "sample_data": [],
                        }

        return preview_data

    async def _extract_preview_data(
        self, backup_path: str, limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract preview data from backup.

        Args:
            backup_path: Path to backup file
            limit: Number of documents to preview per collection

        Returns:
            Preview data by collection
        """
        preview_data: Dict[str, List[Dict[str, Any]]] = {}
        current_collection = None
        count = 0

        async for data in self._decompress_backup(backup_path):
            if "collection" in data:
                current_collection = data["collection"]
                preview_data[current_collection] = []
                count = 0
            elif current_collection and count < limit:
                preview_data[current_collection].append(data)
                count += 1

        return preview_data

    async def _restore_collection(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        options: Dict[str, Any],
    ) -> Dict[str, int]:
        """
        Restore a specific collection.

        Args:
            collection_name: Collection name
            documents: Documents to restore
            options: Restore options

        Returns:
            Statistics for the restoration
        """
        stats = {
            "restored": 0,
            "skipped": 0,
            "failed": 0,
        }

        collection = self.db[collection_name]

        for doc in documents:
            try:
                # Remove metadata fields
                clean_doc = {
                    k: v for k, v in doc.items() if not k.startswith("_backup_")
                }

                # Check if document exists
                existing = None
                if "_id" in clean_doc:
                    existing = await collection.find_one({"_id": clean_doc["_id"]})

                if existing:
                    if options.get("overwrite_existing"):
                        await collection.replace_one(
                            {"_id": clean_doc["_id"]}, clean_doc
                        )
                        stats["restored"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    await collection.insert_one(clean_doc)
                    stats["restored"] += 1

            except Exception as e:
                logger.error(f"Failed to restore document in {collection_name}: {e}")
                stats["failed"] += 1

        return stats

    async def _merge_collection_data(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        merge_strategy: str = "deep",
    ) -> Dict[str, int]:
        """
        Merge collection data with existing data.

        Args:
            collection_name: Collection name
            documents: Documents to merge
            merge_strategy: Merge strategy ('deep' or 'shallow')

        Returns:
            Statistics for the merge operation
        """
        stats = {
            "merged": 0,
            "created": 0,
            "skipped": 0,
            "failed": 0,
        }

        collection = self.db[collection_name]

        for doc in documents:
            try:
                # Remove metadata fields
                clean_doc = {
                    k: v for k, v in doc.items() if not k.startswith("_backup_")
                }

                if "_id" in clean_doc:
                    existing = await collection.find_one({"_id": clean_doc["_id"]})

                    if existing:
                        if merge_strategy == "deep":
                            # Deep merge - recursively merge nested objects
                            merged_doc = self._deep_merge(existing, clean_doc)
                        else:
                            # Shallow merge - top-level only
                            merged_doc = {**existing, **clean_doc}

                        await collection.replace_one(
                            {"_id": clean_doc["_id"]}, merged_doc
                        )
                        stats["merged"] += 1
                    else:
                        await collection.insert_one(clean_doc)
                        stats["created"] += 1
                else:
                    # No ID, always create new
                    await collection.insert_one(clean_doc)
                    stats["created"] += 1

            except Exception as e:
                logger.error(f"Failed to merge document in {collection_name}: {e}")
                stats["failed"] += 1

        return stats

    def _deep_merge(
        self, existing: Dict[str, Any], new: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            existing: Existing document
            new: New document to merge

        Returns:
            Merged document
        """
        result = existing.copy()

        for key, value in new.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result
