"""Debug version of ingestion service with extensive logging."""
import asyncio
import hashlib
import json
import logging
import traceback
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.ingest import IngestStats, MessageIngest

# Set up detailed logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add console handler with detailed format
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


class IngestServiceDebug:
    """Debug version of IngestService with extensive logging."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._project_cache: dict[str, ObjectId] = {}
        self._session_cache: dict[str, ObjectId] = {}
        logger.info("IngestServiceDebug initialized")

    async def ingest_messages(self, messages: list[MessageIngest]) -> IngestStats:
        """Ingest a batch of messages with debug logging."""
        logger.info(f"=== Starting ingestion of {len(messages)} messages ===")

        start_time = datetime.now(UTC)
        stats = IngestStats(
            messages_received=len(messages),
            messages_processed=0,
            messages_skipped=0,
            messages_failed=0,
            sessions_created=0,
            sessions_updated=0,
            todos_processed=0,
            config_updated=False,
            duration_ms=0,
        )

        try:
            # Log first message details
            if messages:
                first_msg = messages[0]
                logger.debug(f"First message type: {first_msg.type}")
                logger.debug(f"First message UUID: {first_msg.uuid}")
                logger.debug(f"First message sessionId: {first_msg.sessionId}")
                logger.debug(
                    f"First message has 'message' field: {hasattr(first_msg, 'message')}"
                )
                if hasattr(first_msg, "message"):
                    logger.debug(f"Message field type: {type(first_msg.message)}")

            # Group messages by session
            sessions_map: dict[str, list[MessageIngest]] = {}
            for message in messages:
                session_id = message.sessionId
                if session_id not in sessions_map:
                    sessions_map[session_id] = []
                sessions_map[session_id].append(message)

            logger.info(f"Messages grouped into {len(sessions_map)} sessions")

            # Process each session
            tasks = []
            for session_id, session_messages in sessions_map.items():
                logger.debug(
                    f"Creating task for session {session_id} with {len(session_messages)} messages"
                )
                task = self._process_session_messages(
                    session_id, session_messages, stats
                )
                tasks.append(task)

            # Run all sessions in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Task {i} failed with exception: {result}")
                    logger.error(traceback.format_exc())

            # Calculate duration
            duration = (datetime.now(UTC) - start_time).total_seconds() * 1000
            stats.duration_ms = int(duration)

            logger.info("=== Ingestion completed ===")
            logger.info(f"Messages received: {stats.messages_received}")
            logger.info(f"Messages processed: {stats.messages_processed}")
            logger.info(f"Messages failed: {stats.messages_failed}")
            logger.info(f"Messages skipped: {stats.messages_skipped}")
            logger.info(f"Sessions created: {stats.sessions_created}")
            logger.info(f"Duration: {stats.duration_ms}ms")

            # Log ingestion
            await self._log_ingestion(stats)

            return stats

        except Exception as e:
            logger.error(f"Fatal error in ingest_messages: {e}")
            logger.error(traceback.format_exc())
            raise

    async def _process_session_messages(
        self, session_id: str, messages: list[MessageIngest], stats: IngestStats
    ) -> None:
        """Process messages for a single session with debug logging."""
        logger.debug(f"=== Processing session {session_id} ===")

        try:
            # Ensure session exists
            logger.debug(f"Ensuring session exists for {session_id}")
            session_obj_id = await self._ensure_session(session_id, messages[0])
            if session_obj_id:
                stats.sessions_created += 1
                logger.info(f"Created new session with ObjectId: {session_obj_id}")
            else:
                stats.sessions_updated += 1
                logger.debug("Session already exists")

            # Get existing message hashes for deduplication
            existing_hashes = await self._get_existing_hashes(session_id)
            logger.debug(f"Found {len(existing_hashes)} existing message hashes")

            # Process each message
            new_messages = []
            for i, message in enumerate(messages):
                logger.debug(
                    f"Processing message {i+1}/{len(messages)}: {message.uuid}"
                )

                # Generate hash for deduplication
                message_hash = self._hash_message(message)
                logger.debug(f"Message hash: {message_hash}")

                if message_hash in existing_hashes:
                    stats.messages_skipped += 1
                    logger.debug("Message skipped (duplicate)")
                    continue

                # Convert to database model
                try:
                    message_doc = self._message_to_doc(message, session_id)
                    logger.debug("Message converted to doc successfully")
                    logger.debug(f"Doc has content field: {'content' in message_doc}")
                    if "content" in message_doc:
                        logger.debug(
                            f"Content preview: {message_doc['content'][:100]}..."
                        )

                    new_messages.append(message_doc)
                    existing_hashes.add(message_hash)
                except Exception as e:
                    logger.error(f"Error processing message {message.uuid}: {e}")
                    logger.error(traceback.format_exc())
                    stats.messages_failed += 1

            # Bulk insert new messages
            if new_messages:
                logger.info(f"Inserting {len(new_messages)} new messages into MongoDB")
                try:
                    result = await self.db.messages.insert_many(new_messages)
                    stats.messages_processed += len(result.inserted_ids)
                    logger.info(
                        f"Successfully inserted {len(result.inserted_ids)} messages"
                    )
                except Exception as e:
                    logger.error(f"MongoDB insert failed: {e}")
                    logger.error(traceback.format_exc())
                    stats.messages_failed += len(new_messages)
                    return

                # Update session statistics
                try:
                    await self._update_session_stats(session_id)
                    logger.debug("Updated session statistics")
                except Exception as e:
                    logger.error(f"Failed to update session stats: {e}")

        except Exception as e:
            logger.error(f"Error processing session {session_id}: {e}")
            logger.error(traceback.format_exc())
            stats.messages_failed += len(messages)

    async def _ensure_session(
        self, session_id: str, first_message: MessageIngest
    ) -> ObjectId | None:
        """Ensure session exists, create if needed."""
        logger.debug(f"_ensure_session called for {session_id}")

        # Check cache first
        if session_id in self._session_cache:
            logger.debug("Session found in cache")
            return None

        # Check database
        existing = await self.db.sessions.find_one({"sessionId": session_id})
        if existing:
            logger.debug("Session found in database")
            self._session_cache[session_id] = existing["_id"]
            return None

        logger.info(f"Creating new session {session_id}")

        # Extract project info from path
        project_path = None
        project_name = "Unknown Project"

        if first_message.cwd:
            project_path = first_message.cwd
            path_parts = project_path.rstrip("/").split("/")
            if path_parts:
                project_name = path_parts[-1]
            logger.debug(f"Project path: {project_path}")
            logger.debug(f"Project name: {project_name}")

        # Ensure project exists
        effective_path = project_path or first_message.cwd or "unknown"
        project_id = await self._ensure_project(effective_path, project_name)
        logger.debug(f"Project ID: {project_id}")

        # Create session
        session_doc = {
            "_id": ObjectId(),
            "sessionId": session_id,
            "projectId": project_id,
            "startedAt": first_message.timestamp,
            "endedAt": first_message.timestamp,
            "messageCount": 0,
            "totalCost": 0.0,
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }

        try:
            await self.db.sessions.insert_one(session_doc)
            session_id_obj = session_doc["_id"]
            assert isinstance(session_id_obj, ObjectId)
            self._session_cache[session_id] = session_id_obj
            logger.info(f"Session created successfully with ID: {session_id_obj}")
            return session_id_obj
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise

    async def _ensure_project(self, project_path: str, project_name: str) -> ObjectId:
        """Ensure project exists, create if needed."""
        logger.debug(
            f"_ensure_project called: path={project_path}, name={project_name}"
        )

        # Check cache first
        if project_path in self._project_cache:
            logger.debug("Project found in cache")
            return self._project_cache[project_path]

        # Check database
        existing = await self.db.projects.find_one({"path": project_path})
        if existing:
            logger.debug(f"Project found in database: {existing['_id']}")
            self._project_cache[project_path] = existing["_id"]
            project_id = existing["_id"]
            assert isinstance(project_id, ObjectId)
            return project_id

        # Create project
        logger.info(f"Creating new project: {project_name}")
        project_doc = {
            "_id": ObjectId(),
            "name": project_name,
            "path": project_path,
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
            "stats": {"message_count": 0, "session_count": 0},
        }

        try:
            await self.db.projects.insert_one(project_doc)
            project_id = project_doc["_id"]
            assert isinstance(project_id, ObjectId)
            self._project_cache[project_path] = project_id
            logger.info(f"Project created successfully with ID: {project_id}")
            return project_id
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise

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
        """Convert message to database document with debug logging."""
        logger.debug(f"_message_to_doc called for message {message.uuid}")

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
            logger.debug(f"Message has 'message' field, type: {type(message.message)}")

            # Handle different message formats
            if isinstance(message.message, dict):
                content = ""

                # Extract content based on message type
                if message.type == "user":
                    # User messages can have string or array content
                    raw_content = message.message.get("content", "")
                    logger.debug(f"User message content type: {type(raw_content)}")

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
                    logger.debug(
                        f"Assistant message content type: {type(content_parts)}"
                    )

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
                logger.debug(f"Extracted content length: {len(content)}")

                # Store the full message object for reference
                doc["messageData"] = message.message
            else:
                # If message is already a string, use it directly
                doc["content"] = str(message.message)
                logger.debug(f"Message is string, content: {doc['content'][:100]}...")

        # Add optional fields
        optional_fields = [
            "userType",
            "cwd",
            "model",
            "costUsd",
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

        # Add any extra fields
        if message.extra_fields:
            doc["metadata"] = message.extra_fields

        logger.debug(f"Document created with fields: {list(doc.keys())}")
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
                        "totalCost": stats["totalCost"],
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
