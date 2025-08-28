"""Import service for handling import operations."""

import json
from datetime import UTC, datetime
from typing import Any, Dict, Literal, Optional

import aiofiles
from bson import Decimal128, ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.logging import get_logger
from app.services.file_service import FileService

logger = get_logger(__name__)


class ImportTransaction:
    """Track import operations for potential rollback."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.inserted_ids: list[tuple[str, str]] = []
        self.updated_ids: list[tuple[str, str]] = []
        self.backup_data: dict[str, dict[str, Any]] = {}

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

    async def rollback(self) -> None:
        """Rollback all changes made during import."""
        # Delete inserted documents
        for collection, doc_id in self.inserted_ids:
            await self.db[collection].delete_one({"_id": ObjectId(doc_id)})

        # Restore updated documents
        for collection, backups in self.backup_data.items():
            for doc_id, backup in backups.items():
                await self.db[collection].replace_one({"_id": ObjectId(doc_id)}, backup)


class ImportService:
    """Service for handling import operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize the import service."""
        self.db = db
        self.file_service = FileService()

    async def validate_import_file(
        self,
        file_path: str,
        file_format: str,
    ) -> Dict[str, Any]:
        """
        Validate an import file and extract metadata.

        Args:
            file_path: Path to the file to validate
            file_format: File format (json, csv, md, jsonl)

        Returns:
            Validation result with file info
        """
        validation_result: Dict[str, Any] = {
            "valid": False,
            "format": file_format,
            "file_info": {},
            "field_mapping": {
                "detected_fields": [],
                "mapping_suggestions": {},
            },
            "validation_warnings": [],
            "validation_errors": [],
        }

        try:
            # Get file info
            file_info = await self.file_service.get_file_info(file_path)
            validation_result["file_info"]["sizeBytes"] = file_info["size"]

            # Validate based on format
            if file_format == "json":
                result = await self._validate_json_import(file_path)
            elif file_format == "csv":
                result = await self._validate_csv_import(file_path)
            elif file_format in ["md", "markdown"]:
                result = await self._validate_markdown_import(file_path)
            elif file_format == "jsonl":
                result = await self._validate_jsonl_import(file_path)
            else:
                validation_result["validation_errors"].append(
                    {"message": f"Unsupported file format: {file_format}"}
                )
                return validation_result

            validation_result.update(result)

            # Set valid flag if no errors
            validation_result["valid"] = (
                len(validation_result["validation_errors"]) == 0
            )

        except Exception as e:
            logger.error(f"Error validating import file: {e}")
            validation_result["validation_errors"].append(
                {"message": f"Validation failed: {str(e)}"}
            )

        return validation_result

    async def _validate_json_import(self, file_path: str) -> Dict[str, Any]:
        """Validate JSON import file."""
        result: Dict[str, Any] = {
            "file_info": {},
            "field_mapping": {
                "detected_fields": [],
                "mapping_suggestions": {},
            },
            "validation_warnings": [],
            "validation_errors": [],
        }

        try:
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()
                data = json.loads(content)

            # Check structure
            if not isinstance(data, dict):
                result["validation_errors"].append(
                    {"message": "JSON must be an object with 'conversations' array"}
                )
                return result

            conversations = data.get("conversations", [])
            if not isinstance(conversations, list):
                result["validation_errors"].append(
                    {"message": "'conversations' must be an array"}
                )
                return result

            if not conversations:
                result["validation_warnings"].append(
                    {
                        "message": "No conversations found in file",
                        "severity": "warning",
                    }
                )
                return result

            # Analyze first conversation for field mapping
            first_conv = conversations[0]
            detected_fields = list(first_conv.keys())
            result["field_mapping"]["detected_fields"] = detected_fields

            # Suggest field mappings
            field_map = {
                "id": "id",
                "title": "title",
                "summary": "summary",
                "messages": "messages",
                "createdAt": "created_at",
                "created_at": "created_at",
                "updatedAt": "updated_at",
                "updated_at": "updated_at",
                "costUsd": "cost_usd",
                "cost_usd": "cost_usd",
                "messageCount": "message_count",
                "message_count": "message_count",
            }

            for field in detected_fields:
                if field in field_map:
                    result["field_mapping"]["mapping_suggestions"][field] = field_map[
                        field
                    ]

            # Count conversations and messages
            total_messages = sum(len(c.get("messages", [])) for c in conversations)

            result["file_info"]["conversationsCount"] = len(conversations)
            result["file_info"]["messagesCount"] = total_messages

            # Extract date range
            dates = []
            for conv in conversations:
                if conv.get("createdAt"):
                    try:
                        dates.append(
                            datetime.fromisoformat(
                                conv["createdAt"].replace("Z", "+00:00")
                            )
                        )
                    except (ValueError, KeyError, AttributeError):
                        pass

            if dates:
                result["file_info"]["dateRange"] = {
                    "start": min(dates).isoformat(),
                    "end": max(dates).isoformat(),
                }

        except json.JSONDecodeError as e:
            result["validation_errors"].append(
                {
                    "message": f"Invalid JSON: {str(e)}",
                    "line": e.lineno if hasattr(e, "lineno") else None,
                }
            )
        except Exception as e:
            result["validation_errors"].append(
                {"message": f"Error reading file: {str(e)}"}
            )

        return result

    async def _validate_csv_import(self, file_path: str) -> Dict[str, Any]:
        """Validate CSV import file."""
        import csv

        result: Dict[str, Any] = {
            "file_info": {},
            "field_mapping": {
                "detected_fields": [],
                "mapping_suggestions": {},
            },
            "validation_warnings": [],
            "validation_errors": [],
        }

        try:
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()

            lines = content.splitlines()
            if not lines:
                result["validation_errors"].append({"message": "CSV file is empty"})
                return result

            reader = csv.DictReader(lines)
            rows = list(reader)

            if not rows:
                result["validation_warnings"].append(
                    {
                        "message": "No data rows found in CSV",
                        "severity": "warning",
                    }
                )
                return result

            # Get detected fields from CSV headers
            result["field_mapping"]["detected_fields"] = reader.fieldnames

            # Count rows
            result["file_info"]["conversationsCount"] = len(rows)
            result["file_info"]["messagesCount"] = 0  # CSV doesn't contain messages

            # Note that CSV format has limitations
            result["validation_warnings"].append(
                {
                    "message": "CSV format does not support message details. Only conversation metadata will be imported.",
                    "severity": "info",
                }
            )

        except Exception as e:
            result["validation_errors"].append(
                {"message": f"Error reading CSV file: {str(e)}"}
            )

        return result

    async def _validate_markdown_import(self, file_path: str) -> Dict[str, Any]:
        """Validate Markdown import file."""
        result: Dict[str, Any] = {
            "file_info": {},
            "field_mapping": {
                "detected_fields": [],
                "mapping_suggestions": {},
            },
            "validation_warnings": [],
            "validation_errors": [],
        }

        # Markdown import would require parsing - simplified for now
        result["validation_warnings"].append(
            {
                "message": "Markdown import is limited to basic conversation structure",
                "severity": "info",
            }
        )

        try:
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()

            # Count conversations (## headers)
            conversation_count = content.count("\n## ")

            result["file_info"]["conversationsCount"] = conversation_count
            result["file_info"]["messagesCount"] = 0  # Would need parsing

        except Exception as e:
            result["validation_errors"].append(
                {"message": f"Error reading Markdown file: {str(e)}"}
            )

        return result

    async def _validate_jsonl_import(self, file_path: str) -> Dict[str, Any]:
        """Validate JSON Lines import file."""
        result: Dict[str, Any] = {
            "file_info": {},
            "field_mapping": {
                "detected_fields": [],
                "mapping_suggestions": {},
            },
            "validation_warnings": [],
            "validation_errors": [],
        }

        try:
            conversations = []
            async with aiofiles.open(file_path, "r") as f:
                line_num = 0
                async for line in f:
                    line_num += 1
                    if line.strip():
                        try:
                            conv = json.loads(line)
                            conversations.append(conv)
                        except json.JSONDecodeError as e:
                            result["validation_errors"].append(
                                {
                                    "message": f"Invalid JSON on line {line_num}: {str(e)}",
                                    "line": line_num,
                                }
                            )

            if conversations:
                # Analyze first conversation
                result["field_mapping"]["detected_fields"] = list(
                    conversations[0].keys()
                )
                result["file_info"]["conversationsCount"] = len(conversations)

                # Count messages
                total_messages = sum(len(c.get("messages", [])) for c in conversations)
                result["file_info"]["messagesCount"] = total_messages

        except Exception as e:
            result["validation_errors"].append(
                {"message": f"Error reading JSONL file: {str(e)}"}
            )

        return result

    async def detect_conflicts(
        self,
        file_path: str,
        field_mapping: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Detect conflicts between import data and existing data.

        Args:
            file_path: Path to the import file
            field_mapping: Field mapping configuration

        Returns:
            Conflicts information
        """
        conflicts = []

        try:
            # Load import data
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()
                data = json.loads(content)

            conversations = data.get("conversations", [])

            for conv in conversations:
                # Check if conversation exists
                conv_id = conv.get(field_mapping.get("id", "id"))
                if conv_id:
                    existing = await self.db.sessions.find_one({"sessionId": conv_id})
                    if existing:
                        conflicts.append(
                            {
                                "existing_id": str(existing["_id"]),
                                "import_id": conv_id,
                                "title": conv.get(
                                    field_mapping.get("title", "title"), ""
                                ),
                                "existing_data": {
                                    "messagesCount": existing.get("messageCount", 0),
                                    "lastUpdated": existing.get("updatedAt").isoformat()
                                    if existing.get("updatedAt")
                                    else None,
                                    "costUsd": existing.get("totalCost", 0.0),
                                },
                                "import_data": {
                                    "messagesCount": len(conv.get("messages", [])),
                                    "lastUpdated": conv.get(
                                        "updatedAt", conv.get("updated_at")
                                    ),
                                    "costUsd": conv.get(
                                        "costUsd", conv.get("cost_usd", 0.0)
                                    ),
                                },
                                "suggested_action": self._suggest_conflict_action(
                                    existing, conv
                                ),
                            }
                        )

        except Exception as e:
            logger.error(f"Error detecting conflicts: {e}")

        return {
            "conflicts_count": len(conflicts),
            "conflicts": conflicts,
        }

    def _suggest_conflict_action(self, existing: Dict, importing: Dict) -> str:
        """Suggest conflict resolution action."""
        # Simple heuristic - if import is newer, suggest replace
        try:
            existing_date = existing.get("updatedAt", existing.get("createdAt"))
            import_date_str = importing.get("updatedAt", importing.get("updated_at"))
            if import_date_str:
                import_date = datetime.fromisoformat(
                    import_date_str.replace("Z", "+00:00")
                )
                if existing_date and import_date > existing_date:
                    return "replace"
        except (ValueError, KeyError, AttributeError):
            pass

        return "skip"

    async def execute_import(
        self,
        job_id: str,
        file_path: str,
        field_mapping: Dict[str, str],
        conflict_resolution: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Any] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the import with conflict resolution.

        Args:
            job_id: Import job ID
            file_path: Path to the import file
            field_mapping: Field mapping configuration
            conflict_resolution: Conflict resolution strategy
            options: Import options
            progress_callback: Optional callback for progress updates
            user_id: Optional user ID for filtering

        Returns:
            Import statistics
        """
        statistics = {
            "imported": 0,
            "skipped": 0,
            "failed": 0,
            "merged": 0,
            "replaced": 0,
        }

        transaction = (
            ImportTransaction(self.db)
            if options and options.get("createBackup", True)
            else None
        )

        try:
            # Load import data
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()
                data = json.loads(content)

            conversations = data.get("conversations", [])
            total = len(conversations)

            # Update job status
            await self.db.import_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": "processing",
                        "started_at": datetime.now(UTC),
                        "progress.total": total,
                    }
                },
            )

            # Process conversations
            for idx, conv in enumerate(conversations):
                try:
                    result = await self._import_conversation(
                        conv,
                        field_mapping,
                        conflict_resolution,
                        transaction,
                        user_id,
                    )

                    statistics[result] += 1

                    # Update progress - broadcast every item or at intervals for large imports
                    if progress_callback:
                        # For small imports (< 100 items), update every item
                        # For large imports, update every 10 items
                        should_update = total < 100 or idx % 10 == 0 or idx == total - 1
                        if should_update:
                            await progress_callback(
                                job_id,
                                {
                                    "processed": idx + 1,
                                    "total": total,
                                    "percentage": round((idx + 1) / total * 100, 2),
                                    "message": f"Processing conversation {idx + 1} of {total}",
                                    "statistics": statistics,
                                },
                            )

                    # Update database progress periodically
                    if idx % 10 == 0 or idx == total - 1:
                        await self.db.import_jobs.update_one(
                            {"_id": ObjectId(job_id)},
                            {
                                "$set": {
                                    "progress.processed": idx + 1,
                                    "progress.percentage": round(
                                        (idx + 1) / total * 100, 2
                                    ),
                                    "statistics": statistics,
                                }
                            },
                        )

                except Exception as e:
                    logger.error(f"Error importing conversation: {e}", exc_info=True)
                    statistics["failed"] += 1

                    # Add detailed error information to job
                    error_details = {
                        "conversation_index": idx,
                        "conversation_id": conv.get(
                            field_mapping.get("id", "id"), "unknown"
                        ),
                        "error": str(e),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }

                    # Update job with error details
                    await self.db.import_jobs.update_one(
                        {"_id": ObjectId(job_id)},
                        {"$push": {"errors": error_details}},
                    )

            # Update job completion
            await self.db.import_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.now(UTC),
                        "statistics": statistics,
                        "progress.processed": total,
                        "progress.percentage": 100,
                    }
                },
            )

        except Exception as e:
            logger.error(f"Import execution failed: {e}")

            # Rollback if transaction exists
            if transaction:
                await transaction.rollback()

            # Update job with error
            await self.db.import_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": "failed",
                        "completed_at": datetime.now(UTC),
                        "errors": [{"message": str(e)}],
                    }
                },
            )

            raise

        return statistics

    async def _import_conversation(
        self,
        conversation: Dict[str, Any],
        field_mapping: Dict[str, str],
        conflict_resolution: Dict[str, Any],
        transaction: Optional[ImportTransaction],
        user_id: Optional[str] = None,
    ) -> Literal["imported", "skipped", "replaced", "merged", "failed"]:
        """Import a single conversation."""
        # Map fields
        session_id = conversation.get(field_mapping.get("id", "id"))

        # Check for existing
        existing = (
            await self.db.sessions.find_one({"sessionId": session_id})
            if session_id
            else None
        )

        if existing:
            # Handle conflict
            strategy = conflict_resolution.get("specificResolutions", {}).get(
                session_id, conflict_resolution.get("defaultStrategy", "skip")
            )

            if strategy == "skip":
                return "skipped"
            elif strategy == "replace":
                if transaction:
                    await transaction.backup_existing("sessions", str(existing["_id"]))

                # Replace existing
                await self.db.sessions.replace_one(
                    {"_id": existing["_id"]},
                    self._map_conversation_to_session(conversation, field_mapping),
                )

                # Replace messages
                if session_id:
                    await self.db.messages.delete_many({"sessionId": session_id})
                    await self._import_messages(conversation, session_id, field_mapping)

                return "replaced"
            elif strategy == "merge":
                # Merge logic would go here
                return "merged"
        else:
            # Import new conversation
            session_data = self._map_conversation_to_session(
                conversation, field_mapping, user_id
            )
            result = await self.db.sessions.insert_one(session_data)

            if transaction:
                transaction.inserted_ids.append(("sessions", str(result.inserted_id)))

            # Import messages
            new_session_id = session_id if session_id else str(result.inserted_id)
            await self._import_messages(conversation, new_session_id, field_mapping)

            return "imported"

        return "failed"

    def _map_conversation_to_session(
        self, conv: Dict, field_mapping: Dict, user_id: Optional[str] = None
    ) -> Dict:
        """Map imported conversation to session model."""
        # Get summary and ensure it's a string (required by schema)
        summary = conv.get(field_mapping.get("summary", "summary"))
        if summary is None:
            summary = ""  # Convert null to empty string

        # Get cost and convert to Decimal128 (required by schema)
        cost_value = conv.get("costUsd", conv.get("cost_usd", 0.0))
        total_cost = Decimal128(str(cost_value))

        session_data = {
            "sessionId": conv.get(field_mapping.get("id", "id"), str(ObjectId())),
            "projectId": ObjectId(conv.get("projectId"))
            if conv.get("projectId")
            else None,
            "title": conv.get(field_mapping.get("title", "title"), ""),
            "summary": summary,
            "startedAt": datetime.fromisoformat(
                conv.get("createdAt", datetime.now(UTC).isoformat()).replace(
                    "Z", "+00:00"
                )
            ),
            "endedAt": datetime.fromisoformat(
                conv.get("updatedAt", datetime.now(UTC).isoformat()).replace(
                    "Z", "+00:00"
                )
            ),
            "messageCount": len(conv.get("messages", [])),
            "totalCost": total_cost,
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }

        # Add user_id if provided
        if user_id:
            session_data["user_id"] = ObjectId(user_id)

        return session_data

    async def _import_messages(
        self, conv: Dict, session_id: str, field_mapping: Dict
    ) -> None:
        """Import messages for a conversation."""
        messages = conv.get(field_mapping.get("messages", "messages"), [])

        if not messages:
            return

        # Prepare bulk operations
        operations = []
        for msg in messages:
            operations.append(
                {
                    "sessionId": session_id,
                    "uuid": msg.get("id", str(ObjectId())),
                    "type": msg.get("type", "unknown"),
                    "userType": msg.get("type"),
                    "timestamp": datetime.fromisoformat(
                        msg.get("timestamp", datetime.now(UTC).isoformat()).replace(
                            "Z", "+00:00"
                        )
                    ),
                    "message": {"text": msg.get("content", "")},
                    "model": msg.get("model"),
                    "costUsd": msg.get("costUsd", msg.get("cost_usd")),
                    "createdAt": datetime.now(UTC),
                }
            )

        if operations:
            await self.db.messages.insert_many(operations)
