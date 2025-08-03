"""Ingestion service for processing messages."""
import asyncio
import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

from bson import Decimal128, ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReplaceOne

from app.schemas.ingest import IngestStats, MessageIngest

logger = logging.getLogger(__name__)


class IngestService:
    """Service for ingesting Claude messages."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._project_cache: dict[str, ObjectId] = {}
        self._session_cache: dict[str, ObjectId] = {}

    async def ingest_messages(
        self, messages: list[MessageIngest], overwrite_mode: bool = False
    ) -> IngestStats:
        """Ingest a batch of messages.

        Args:
            messages: List of messages to ingest
            overwrite_mode: If True, update existing messages on UUID conflicts
        """
        logger.info(
            f"Starting ingest of {len(messages)} messages (overwrite={overwrite_mode})"
        )

        start_time = datetime.now(UTC)
        stats = IngestStats(
            messages_received=len(messages),
            messages_processed=0,
            messages_skipped=0,
            messages_failed=0,
            messages_updated=0,
            sessions_created=0,
            sessions_updated=0,
            todos_processed=0,
            config_updated=False,
            duration_ms=0,
        )

        # Group messages by session
        sessions_map: dict[str, list[MessageIngest]] = {}
        for message in messages:
            session_id = message.sessionId
            if session_id not in sessions_map:
                sessions_map[session_id] = []
            sessions_map[session_id].append(message)

        # Process each session
        tasks = []
        for session_id, session_messages in sessions_map.items():
            task = self._process_session_messages(
                session_id, session_messages, stats, overwrite_mode
            )
            tasks.append(task)

        # Run all sessions in parallel
        await asyncio.gather(*tasks, return_exceptions=True)

        # Calculate duration
        duration = (datetime.now(UTC) - start_time).total_seconds() * 1000
        stats.duration_ms = int(duration)

        # Log final stats
        logger.info(
            f"Ingestion completed: {stats.messages_processed} processed, "
            f"{stats.messages_skipped} skipped, {stats.messages_failed} failed "
            f"({stats.duration_ms}ms)"
        )

        # Log ingestion
        await self._log_ingestion(stats)

        return stats

    async def _process_session_messages(
        self,
        session_id: str,
        messages: list[MessageIngest],
        stats: IngestStats,
        overwrite_mode: bool = False,
    ) -> None:
        """Process messages for a single session."""
        try:
            # Ensure session exists
            session_obj_id = await self._ensure_session(session_id, messages[0])
            if session_obj_id:
                stats.sessions_created += 1
            else:
                stats.sessions_updated += 1

            # Get existing message hashes for deduplication (skip if overwrite mode)
            existing_hashes = set()
            if not overwrite_mode:
                existing_hashes = await self._get_existing_hashes(session_id)

            # Process each message
            new_messages = []
            for message in messages:
                # Skip deduplication check in overwrite mode
                if not overwrite_mode:
                    # Generate hash for deduplication
                    message_hash = self._hash_message(message)

                    if message_hash in existing_hashes:
                        stats.messages_skipped += 1
                        continue

                # Convert to database model
                try:
                    message_doc = self._message_to_doc(message, session_id)
                    new_messages.append(message_doc)
                    if not overwrite_mode:
                        existing_hashes.add(self._hash_message(message))
                except Exception as e:
                    logger.error(f"Error processing message {message.uuid}: {e}")
                    stats.messages_failed += 1

            # Bulk insert/update messages
            if new_messages:
                if overwrite_mode:
                    # Use bulk write with upserts
                    operations = []
                    for msg in new_messages:
                        # Remove _id from replacement document to avoid immutable field error
                        replacement_doc = {k: v for k, v in msg.items() if k != "_id"}
                        operations.append(
                            ReplaceOne(
                                filter={"uuid": msg["uuid"]},
                                replacement=replacement_doc,
                                upsert=True,
                            )
                        )

                    try:
                        bulk_result = await self.db.messages.bulk_write(operations)
                        # Track inserts and updates separately
                        stats.messages_processed += bulk_result.inserted_count
                        stats.messages_updated += bulk_result.modified_count
                    except Exception as e:
                        logger.error(f"MongoDB bulk write failed: {e}")
                        stats.messages_failed += len(new_messages)
                        # Add error detail for the response
                        error_msg = (
                            f"Bulk write failed for session {session_id}: {str(e)}"
                        )
                        if hasattr(stats, "error_details"):
                            stats.error_details.append(error_msg)
                        return
                else:
                    # Original insert behavior
                    try:
                        insert_result = await self.db.messages.insert_many(new_messages)
                        stats.messages_processed += len(insert_result.inserted_ids)
                    except Exception as e:
                        logger.error(f"MongoDB insert failed: {e}")
                        stats.messages_failed += len(new_messages)
                        # Add error detail for the response
                        error_msg = f"Insert failed for session {session_id}: {str(e)}"
                        if hasattr(stats, "error_details"):
                            stats.error_details.append(error_msg)
                        return

                # Update session statistics
                await self._update_session_stats(session_id)

        except Exception as e:
            logger.error(f"Error processing session {session_id}: {e}")
            stats.messages_failed += len(messages)

    async def _ensure_session(
        self, session_id: str, first_message: MessageIngest
    ) -> ObjectId | None:
        """Ensure session exists, create if needed."""
        # Check cache first
        if session_id in self._session_cache:
            return None

        # Check database
        existing = await self.db.sessions.find_one({"sessionId": session_id})
        if existing:
            self._session_cache[session_id] = existing["_id"]
            return None

        # Extract project info from path
        project_path = None
        project_name = "Unknown Project"

        if first_message.cwd:
            # The cwd should be the full project path
            # Extract project name from the last part of the path
            project_path = first_message.cwd
            path_parts = project_path.rstrip("/").split("/")
            if path_parts:
                project_name = path_parts[-1]

            # Also check for Claude path format
            # e.g., /Users/user/Library/Application Support/Claude/projects/my-project
            if "projects" in path_parts:
                idx = path_parts.index("projects")
                if idx + 1 < len(path_parts):
                    # Use the more specific project name if found
                    project_name = path_parts[idx + 1]

        # Ensure project exists
        effective_path = project_path or first_message.cwd or "unknown"
        project_id = await self._ensure_project(effective_path, project_name)

        # Create session
        session_doc = {
            "_id": ObjectId(),
            "sessionId": session_id,
            "projectId": project_id,
            "startedAt": first_message.timestamp,
            "endedAt": first_message.timestamp,
            "messageCount": 0,
            "totalCost": Decimal128("0.0"),  # MongoDB expects Decimal128, not float
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }

        await self.db.sessions.insert_one(session_doc)
        session_id_obj = session_doc["_id"]
        assert isinstance(session_id_obj, ObjectId)
        self._session_cache[session_id] = session_id_obj

        return session_id_obj

    async def _ensure_project(self, project_path: str, project_name: str) -> ObjectId:
        """Ensure project exists, create if needed."""
        # Check cache first
        if project_path in self._project_cache:
            return self._project_cache[project_path]

        # Check database
        existing = await self.db.projects.find_one({"path": project_path})
        if existing:
            self._project_cache[project_path] = existing["_id"]
            project_id = existing["_id"]
            assert isinstance(project_id, ObjectId)
            return project_id

        # Create project
        project_doc = {
            "_id": ObjectId(),
            "name": project_name,
            "path": project_path,
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
            "stats": {"message_count": 0, "session_count": 0},
        }

        await self.db.projects.insert_one(project_doc)
        project_id = project_doc["_id"]
        assert isinstance(project_id, ObjectId)
        self._project_cache[project_path] = project_id

        return project_id

    async def _get_existing_hashes(self, session_id: str) -> set[str]:
        """Get existing message hashes for a session."""
        cursor = self.db.messages.find({"sessionId": session_id}, {"contentHash": 1})

        hashes = set()
        async for doc in cursor:
            if "contentHash" in doc:
                hashes.add(doc["contentHash"])

        return hashes

    def _hash_message(self, message: MessageIngest) -> str:
        """Generate hash for message deduplication."""
        # Create deterministic string representation
        hash_data = {
            "uuid": message.uuid,
            "type": message.type,
            "timestamp": message.timestamp.isoformat(),
            "content": message.message,
        }

        content = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()

    def _message_to_doc(self, message: MessageIngest, session_id: str) -> dict:
        """Convert message to database document."""

        doc = {
            "_id": ObjectId(),
            "uuid": message.uuid,
            "sessionId": session_id,
            "type": message.type,
            "timestamp": message.timestamp,
            "parentUuid": message.parentUuid,
            "contentHash": self._hash_message(message),
            "createdAt": datetime.now(UTC),
        }

        # Add message content - extract text content from message object
        if message.message:
            # Handle different message formats
            if isinstance(message.message, dict):
                content = ""

                # Extract content based on message type
                if message.type == "user":
                    # User messages can have string or array content
                    raw_content = message.message.get("content", "")

                    if isinstance(raw_content, str):
                        # Direct string content
                        content = raw_content
                    elif isinstance(raw_content, list):
                        # Array-based content (tool results or text)
                        text_parts = []
                        for part in raw_content:
                            if isinstance(part, dict):
                                if part.get("type") == "text":
                                    text_parts.append(part.get("text", ""))
                                elif part.get("type") == "tool_result":
                                    # Include tool result content
                                    tool_content = part.get("content", "")
                                    if tool_content:
                                        text_parts.append(
                                            f"[Tool Result: {tool_content}]"
                                        )
                        content = "\n".join(text_parts)

                elif message.type == "assistant":
                    # Assistant messages with content array
                    content_parts = message.message.get("content", [])
                    if isinstance(content_parts, list):
                        # Extract different content types
                        text_parts = []
                        thinking_parts = []
                        tool_uses = []

                        for part in content_parts:
                            if isinstance(part, dict):
                                part_type = part.get("type")

                                if part_type == "text":
                                    text_parts.append(part.get("text", ""))
                                elif part_type == "thinking":
                                    # Store thinking separately but include in content
                                    thinking = part.get("thinking", "")
                                    if thinking:
                                        thinking_parts.append(thinking)
                                elif part_type == "tool_use":
                                    # Format tool use for display
                                    tool_name = part.get("name", "Unknown")
                                    tool_uses.append(f"[Using tool: {tool_name}]")

                        # Combine all parts
                        all_parts = []
                        if thinking_parts:
                            all_parts.append("[Thinking]\n" + "\n".join(thinking_parts))
                        if text_parts:
                            all_parts.extend(text_parts)
                        if tool_uses:
                            all_parts.extend(tool_uses)

                        content = "\n\n".join(all_parts) if all_parts else ""

                        # Store thinking separately if present
                        if thinking_parts:
                            doc["thinking"] = "\n".join(thinking_parts)
                    else:
                        content = str(content_parts)

                elif message.type == "summary":
                    # Summary messages don't have standard message format
                    content = message.message.get("summary", "")
                else:
                    # For other types, convert to string
                    content = str(message.message)

                # Store the content as a simple string
                doc["content"] = content or ""

                # Store the full message object for reference
                doc["messageData"] = message.message
            else:
                # If message is already a string, use it directly
                doc["content"] = str(message.message)

        # Add optional fields
        optional_fields = [
            "userType",
            "cwd",
            "model",
            "durationMs",
            "requestId",
            "version",
            "gitBranch",
            "isSidechain",
            "toolUseResult",
            "summary",
            "leafUuid",
        ]
        for field in optional_fields:
            value = getattr(message, field, None)
            if value is not None:
                doc[field] = value

        # Handle costUsd separately to convert to Decimal128
        cost_usd = getattr(message, "costUsd", None)
        if cost_usd is not None:
            doc["costUsd"] = Decimal128(str(cost_usd))

        # Add any extra fields
        if message.extra_fields:
            doc["metadata"] = message.extra_fields

        return doc

    async def _update_session_stats(self, session_id: str) -> None:
        """Update session statistics."""
        # Aggregate statistics
        pipeline: list[dict[str, Any]] = [
            {"$match": {"sessionId": session_id}},
            {
                "$group": {
                    "_id": None,
                    "messageCount": {"$sum": 1},
                    "totalCost": {"$sum": {"$ifNull": ["$costUsd", 0]}},
                    "startTime": {"$min": "$timestamp"},
                    "endTime": {"$max": "$timestamp"},
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)

        if result:
            stats = result[0]
            await self.db.sessions.update_one(
                {"sessionId": session_id},
                {
                    "$set": {
                        "messageCount": stats["messageCount"],
                        "totalCost": Decimal128(
                            str(stats["totalCost"])
                        ),  # Convert to Decimal128
                        "startedAt": stats["startTime"],
                        "endedAt": stats["endTime"],
                        "updatedAt": datetime.now(UTC),
                    }
                },
            )

    async def _log_ingestion(self, stats: IngestStats) -> None:
        """Log ingestion statistics."""
        log_entry = {
            "timestamp": datetime.now(UTC),
            "messages_processed": stats.messages_processed,
            "messages_skipped": stats.messages_skipped,
            "messages_failed": stats.messages_failed,
            "duration_ms": stats.duration_ms,
        }

        await self.db.ingestion_logs.insert_one(log_entry)
