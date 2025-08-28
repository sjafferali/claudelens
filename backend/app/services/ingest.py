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
from app.services.cost_calculation import CostCalculationService
from app.services.realtime_integration import get_integration_service

logger = logging.getLogger(__name__)


class IngestService:
    """Service for ingesting Claude messages."""

    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id
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
            session_summary = None  # Track if we find a summary message

            for message in messages:
                # Check if this is a summary message
                if message.type == "summary" and message.summary:
                    session_summary = message.summary
                    # Skip storing summary messages as regular messages
                    stats.messages_processed += 1  # Count it as processed
                    continue

                # Skip deduplication check in overwrite mode
                if not overwrite_mode:
                    # Generate hash for deduplication
                    message_hash = self._hash_message(message)

                    if message_hash in existing_hashes:
                        stats.messages_skipped += 1
                        continue

                # Convert to database model(s)
                try:
                    message_docs = self._message_to_doc(message, session_id)
                    new_messages.extend(message_docs)  # Extend instead of append
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

                        # Trigger real-time updates for new/updated messages
                        if (
                            bulk_result.inserted_count > 0
                            or bulk_result.modified_count > 0
                        ):
                            integration_service = get_integration_service(self.db)
                            for message in messages:
                                if message.sessionId == session_id:
                                    # Convert MessageIngest to dict for integration
                                    message_dict = message.model_dump()
                                    asyncio.create_task(
                                        integration_service.on_message_ingested(
                                            message_dict
                                        )
                                    )
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

                        # Trigger real-time updates for new messages
                        if len(insert_result.inserted_ids) > 0:
                            integration_service = get_integration_service(self.db)
                            for message in messages:
                                if message.sessionId == session_id:
                                    # Convert MessageIngest to dict for integration
                                    message_dict = message.model_dump()
                                    asyncio.create_task(
                                        integration_service.on_message_ingested(
                                            message_dict
                                        )
                                    )
                    except Exception as e:
                        logger.error(f"MongoDB insert failed: {e}")
                        stats.messages_failed += len(new_messages)
                        # Add error detail for the response
                        error_msg = f"Insert failed for session {session_id}: {str(e)}"
                        if hasattr(stats, "error_details"):
                            stats.error_details.append(error_msg)
                        return

                # Update session statistics and summary if found
                await self._update_session_stats(session_id, session_summary)

        except Exception as e:
            logger.error(f"Error processing session {session_id}: {e}")
            stats.messages_failed += len(messages)

    async def _ensure_session(
        self, session_id: str, first_message: MessageIngest
    ) -> ObjectId | None:
        """Ensure session exists, create if needed."""
        # Check cache first - include user_id in cache key
        cache_key = f"{self.user_id}:{session_id}"
        if cache_key in self._session_cache:
            return None

        # Check database - find session by ID and verify project ownership
        existing = await self.db.sessions.find_one({"sessionId": session_id})
        if existing:
            # Verify the project belongs to this user
            project = await self.db.projects.find_one(
                {"_id": existing["projectId"], "user_id": ObjectId(self.user_id)}
            )
            if project:
                # Session exists and belongs to this user's project
                self._session_cache[cache_key] = existing["_id"]
                return None
            # Session exists but belongs to another user's project
            # Continue to create a new session for this user

        # Extract project info from path
        project_path = None
        project_name = "Unknown Project"

        # Check if we have a _project_path field from the sync engine
        # It might be in extra_fields
        extra_project_path = first_message.extra_fields.get("_project_path")
        if extra_project_path:
            project_path = extra_project_path
            # Extract project name from the Claude project path
            path_parts = project_path.rstrip("/").split("/")
            if path_parts:
                project_name = path_parts[-1]
        elif first_message.cwd:
            # Fallback to using cwd if no _project_path
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

        # Create session (without user_id - ownership through project)
        session_doc = {
            "_id": ObjectId(),
            # No user_id - ownership inherited from project
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
        self._session_cache[cache_key] = session_id_obj

        return session_id_obj

    async def _ensure_project(self, project_path: str, project_name: str) -> ObjectId:
        """Ensure project exists, create if needed."""
        # Check cache first - include user_id in cache key
        cache_key = f"{self.user_id}:{project_path}"
        if cache_key in self._project_cache:
            return self._project_cache[cache_key]

        # Check database - filter by user_id
        existing = await self.db.projects.find_one(
            {"path": project_path, "user_id": ObjectId(self.user_id)}
        )
        if existing:
            self._project_cache[cache_key] = existing["_id"]
            project_id = existing["_id"]
            assert isinstance(project_id, ObjectId)
            return project_id

        # Create project with user_id
        project_doc = {
            "_id": ObjectId(),
            "user_id": ObjectId(self.user_id),  # Add user_id
            "name": project_name,
            "path": project_path,
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
            "stats": {"message_count": 0, "session_count": 0},
        }

        await self.db.projects.insert_one(project_doc)
        project_id = project_doc["_id"]
        assert isinstance(project_id, ObjectId)
        self._project_cache[cache_key] = project_id

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
        hash_data: dict[str, Any] = {
            "uuid": message.uuid,
            "type": message.type,
            "timestamp": message.timestamp.isoformat(),
        }

        # Add content based on message type
        if message.type == "summary" and message.summary:
            hash_data["content"] = message.summary
        else:
            hash_data["content"] = message.message

        content = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()

    def _message_to_doc(self, message: MessageIngest, session_id: str) -> list[dict]:
        """Convert message to database document(s).

        Returns a list of documents because tool_use and tool_result parts
        need to be split into separate messages.
        """

        docs = []

        # First, handle special cases where we need to split messages
        if message.type == "assistant" and isinstance(message.message, dict):
            content_parts = message.message.get("content", [])
            if isinstance(content_parts, list):
                # Separate regular content from tool uses
                text_parts = []
                thinking_parts = []
                tool_use_parts = []

                for part in content_parts:
                    if isinstance(part, dict):
                        part_type = part.get("type")
                        if part_type == "text":
                            text_parts.append(part.get("text", ""))
                        elif part_type == "thinking":
                            thinking = part.get("thinking", "")
                            if thinking:
                                thinking_parts.append(thinking)
                        elif part_type == "tool_use":
                            tool_use_parts.append(part)

                # Always create the main assistant message, even if it's empty
                main_doc = {
                    "_id": ObjectId(),
                    # No user_id - ownership inherited from session's project
                    "uuid": message.uuid,
                    "sessionId": session_id,
                    "type": "assistant",
                    "timestamp": message.timestamp,
                    "parentUuid": message.parentUuid,
                    "contentHash": self._hash_message(message),
                    "createdAt": datetime.now(UTC),
                }

                # Combine text content
                all_parts = []
                if thinking_parts:
                    all_parts.append("[Thinking]\n" + "\n".join(thinking_parts))
                    main_doc["thinking"] = "\n".join(thinking_parts)
                if text_parts:
                    all_parts.extend(text_parts)

                # Add tool use summaries if there are tool uses
                if tool_use_parts:
                    tool_summaries = []
                    for tool_part in tool_use_parts:
                        tool_name = tool_part.get("name", "Unknown")
                        tool_input = tool_part.get("input", {})

                        # Create a meaningful summary based on the tool
                        if tool_name == "Read":
                            file_path = tool_input.get("file_path", "")
                            tool_summaries.append(f"📄 Reading file: {file_path}")
                        elif tool_name == "Write":
                            file_path = tool_input.get("file_path", "")
                            tool_summaries.append(f"✏️ Writing to file: {file_path}")
                        elif tool_name == "Edit":
                            file_path = tool_input.get("file_path", "")
                            tool_summaries.append(f"✏️ Editing file: {file_path}")
                        elif tool_name == "MultiEdit":
                            file_path = tool_input.get("file_path", "")
                            edits = tool_input.get("edits", [])
                            tool_summaries.append(
                                f"✏️ Multiple edits ({len(edits)}) to: {file_path}"
                            )
                        elif tool_name == "LS":
                            path = tool_input.get("path", "")
                            tool_summaries.append(f"📁 Listing directory: {path}")
                        elif tool_name == "Glob":
                            pattern = tool_input.get("pattern", "")
                            tool_summaries.append(
                                f"🔍 Finding files matching: {pattern}"
                            )
                        elif tool_name == "Grep":
                            pattern = tool_input.get("pattern", "")
                            tool_summaries.append(f"🔍 Searching for: {pattern}")
                        elif tool_name == "Bash":
                            command = tool_input.get("command", "")
                            if len(command) > 60:
                                command = command[:60] + "..."
                            tool_summaries.append(f"💻 Running command: {command}")
                        elif tool_name == "WebSearch":
                            query = tool_input.get("query", "")
                            tool_summaries.append(f"🌐 Web search: {query}")
                        elif tool_name == "WebFetch":
                            url = tool_input.get("url", "")
                            tool_summaries.append(f"🌐 Fetching: {url}")
                        elif tool_name == "NotebookRead":
                            path = tool_input.get("notebook_path", "")
                            tool_summaries.append(f"📓 Reading notebook: {path}")
                        elif tool_name == "NotebookEdit":
                            path = tool_input.get("notebook_path", "")
                            tool_summaries.append(f"📓 Editing notebook: {path}")
                        elif tool_name == "TodoWrite":
                            todos = tool_input.get("todos", [])
                            tool_summaries.append(
                                f"📝 Updating todo list ({len(todos)} items)"
                            )
                        elif tool_name == "Task":
                            desc = tool_input.get("description", "")
                            tool_summaries.append(f"🤖 Running agent task: {desc}")
                        elif tool_name == "ExitPlanMode":
                            tool_summaries.append("📋 Exiting plan mode")
                        else:
                            # Generic summary for other tools
                            tool_summaries.append(f"🔧 Using tool: {tool_name}")

                    all_parts.append("\n".join(tool_summaries))

                main_doc["content"] = "\n\n".join(all_parts) if all_parts else ""
                main_doc[
                    "messageData"
                ] = message.message  # Store the full original message

                # Extract and store usage data if available
                if isinstance(message.message, dict) and "usage" in message.message:
                    main_doc["usage"] = message.message["usage"]

                # Add optional fields
                self._add_optional_fields(main_doc, message)
                docs.append(main_doc)

                # Create separate tool_use messages
                logger.info(
                    f"Creating {len(tool_use_parts)} tool_use messages from assistant message {message.uuid}"
                )
                for i, tool_part in enumerate(tool_use_parts):
                    tool_uuid = f"{message.uuid}_tool_{i}"
                    tool_doc = {
                        "_id": ObjectId(),
                        # No user_id - ownership inherited from session's project
                        "uuid": tool_uuid,
                        "sessionId": session_id,
                        "type": "tool_use",
                        "timestamp": message.timestamp,
                        "parentUuid": message.uuid,  # Parent is the assistant message
                        "isSidechain": True,  # Mark tool messages as sidechains
                        "createdAt": datetime.now(UTC),
                    }

                    # Store tool use content as JSON
                    tool_doc["content"] = json.dumps(tool_part, ensure_ascii=False)
                    tool_doc["messageData"] = tool_part

                    tool_name = tool_part.get("name", "Unknown")
                    logger.debug(
                        f"Created tool_use message {tool_uuid} for tool '{tool_name}' with parent {message.uuid}"
                    )

                    # Add optional fields (but exclude costUsd for tool messages)
                    self._add_optional_fields(tool_doc, message, exclude_cost=True)
                    docs.append(tool_doc)

                return docs

        elif message.type == "user" and isinstance(message.message, dict):
            raw_content = message.message.get("content", "")
            if isinstance(raw_content, list):
                # Separate text from tool results
                text_parts = []
                tool_result_parts = []

                for part in raw_content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                        elif part.get("type") == "tool_result":
                            tool_result_parts.append(part)

                # Always create main user message
                main_doc = {
                    "_id": ObjectId(),
                    # No user_id - ownership inherited from session's project
                    "uuid": message.uuid,
                    "sessionId": session_id,
                    "type": "user",
                    "timestamp": message.timestamp,
                    "parentUuid": message.parentUuid,
                    "contentHash": self._hash_message(message),
                    "createdAt": datetime.now(UTC),
                }

                # Create content - only include text parts in user message
                if text_parts:
                    main_doc["content"] = "\n".join(text_parts)
                    main_doc[
                        "messageData"
                    ] = message.message  # Store the full original message
                    # Add optional fields
                    self._add_optional_fields(main_doc, message)
                    docs.append(main_doc)
                elif not tool_result_parts:
                    # Only create empty user message if there are no tool results either
                    main_doc["content"] = ""
                    main_doc[
                        "messageData"
                    ] = message.message  # Store the full original message
                    # Add optional fields
                    self._add_optional_fields(main_doc, message)
                    docs.append(main_doc)

                # Create separate tool_result messages
                logger.info(
                    f"Creating {len(tool_result_parts)} tool_result messages from user message {message.uuid}"
                )
                for i, result_part in enumerate(tool_result_parts):
                    result_uuid = f"{message.uuid}_result_{i}"
                    parent_tool_uuid = f"{message.parentUuid}_tool_{i}"
                    result_doc = {
                        "_id": ObjectId(),
                        # No user_id - ownership inherited from session's project
                        "uuid": result_uuid,
                        "sessionId": session_id,
                        "type": "tool_result",
                        "timestamp": message.timestamp,
                        "parentUuid": parent_tool_uuid,  # Parent is the corresponding tool_use message
                        "isSidechain": True,  # Mark tool result messages as sidechains
                        "createdAt": datetime.now(UTC),
                    }

                    logger.debug(
                        f"Created tool_result message {result_uuid} with parent {parent_tool_uuid}"
                    )

                    # Extract tool result content
                    tool_content = result_part.get("content", "")
                    result_doc["content"] = (
                        tool_content
                        if isinstance(tool_content, str)
                        else json.dumps(tool_content, ensure_ascii=False)
                    )
                    result_doc["messageData"] = result_part

                    # Add optional fields (but exclude costUsd for tool result messages)
                    self._add_optional_fields(result_doc, message, exclude_cost=True)
                    docs.append(result_doc)

                return docs

        # For all other cases, create a single document using the original logic
        return [self._create_default_doc(message, session_id)]

    def _create_default_doc(self, message: MessageIngest, session_id: str) -> dict:
        """Create a default document using the original logic."""
        doc = {
            "_id": ObjectId(),
            # No user_id - ownership inherited from session's project
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
                    # For other types, try to extract content field
                    if "content" in message.message:
                        content = message.message.get("content", "")
                        if isinstance(content, list):
                            # Extract text from content array
                            text_parts = []
                            for part in content:
                                if (
                                    isinstance(part, dict)
                                    and part.get("type") == "text"
                                ):
                                    text_parts.append(part.get("text", ""))
                            content = "\n".join(text_parts)
                    else:
                        # Last resort - convert to string
                        content = str(message.message)

                # Store the content as a simple string
                doc["content"] = content or ""

                # Store the full message object for reference
                doc["messageData"] = message.message
            else:
                # If message is already a string, use it directly
                doc["content"] = str(message.message)

        # Add optional fields
        self._add_optional_fields(doc, message)
        return doc

    def _add_optional_fields(
        self, doc: dict, message: MessageIngest, exclude_cost: bool = False
    ) -> None:
        """Add optional fields to a document.

        Args:
            doc: The document to add fields to
            message: The source message
            exclude_cost: If True, skip adding costUsd field (for tool/result messages)
        """
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
                # Don't overwrite manually set isSidechain for tool messages
                if field == "isSidechain" and "isSidechain" in doc:
                    continue
                doc[field] = value

        # Handle costUsd - calculate if not provided but we have usage data
        # Skip cost calculation for tool_use and tool_result messages
        if not exclude_cost:
            cost_usd = getattr(message, "costUsd", None)
            if cost_usd is None and message.type == "assistant" and message.message:
                # Try to calculate cost from usage data
                msg_data = message.message
                if (
                    isinstance(msg_data, dict)
                    and "usage" in msg_data
                    and "model" in msg_data
                ):
                    usage = msg_data["usage"]
                    cost_service = CostCalculationService()
                    cost_usd = cost_service.calculate_message_cost(
                        model=msg_data["model"],
                        input_tokens=usage.get("input_tokens"),
                        output_tokens=usage.get("output_tokens"),
                        cache_creation_input_tokens=usage.get(
                            "cache_creation_input_tokens"
                        ),
                        cache_read_input_tokens=usage.get("cache_read_input_tokens"),
                    )

            if cost_usd is not None:
                doc["costUsd"] = Decimal128(str(cost_usd))

        # Add any extra fields
        if message.extra_fields:
            doc["metadata"] = message.extra_fields

    async def _update_session_stats(
        self, session_id: str, summary: str | None = None
    ) -> None:
        """Update session statistics and optionally the summary."""
        # Aggregate statistics
        pipeline: list[dict[str, Any]] = [
            {"$match": {"sessionId": session_id}},
            {
                "$group": {
                    "_id": None,
                    "messageCount": {"$sum": 1},
                    "totalCost": {"$sum": {"$ifNull": ["$costUsd", 0]}},
                    # Aggregate input tokens from all possible fields
                    "inputTokens": {
                        "$sum": {
                            "$add": [
                                {"$ifNull": ["$tokensInput", 0]},
                                {"$ifNull": ["$inputTokens", 0]},
                                {"$ifNull": ["$metadata.usage.input_tokens", 0]},
                                {
                                    "$ifNull": [
                                        "$metadata.usage.cache_creation_input_tokens",
                                        0,
                                    ]
                                },
                                {
                                    "$ifNull": [
                                        "$metadata.usage.cache_read_input_tokens",
                                        0,
                                    ]
                                },
                            ]
                        }
                    },
                    # Aggregate output tokens from all possible fields
                    "outputTokens": {
                        "$sum": {
                            "$add": [
                                {"$ifNull": ["$tokensOutput", 0]},
                                {"$ifNull": ["$outputTokens", 0]},
                                {"$ifNull": ["$metadata.usage.output_tokens", 0]},
                            ]
                        }
                    },
                    # Count tool usage from both tool_use messages and tool_calls array
                    "toolUseCount": {
                        "$sum": {
                            "$add": [
                                # Count tool_use type messages
                                {"$cond": [{"$eq": ["$type", "tool_use"]}, 1, 0]},
                                # Count tool_calls in message field
                                {
                                    "$cond": [
                                        {"$isArray": "$message.tool_calls"},
                                        {"$size": "$message.tool_calls"},
                                        0,
                                    ]
                                },
                            ]
                        }
                    },
                    "startTime": {"$min": "$timestamp"},
                    "endTime": {"$max": "$timestamp"},
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)

        if result:
            stats = result[0]
            # Build update data
            update_data = {
                "messageCount": stats["messageCount"],
                "totalCost": Decimal128(
                    str(stats["totalCost"])
                ),  # Convert to Decimal128
                "totalTokens": stats.get("inputTokens", 0)
                + stats.get("outputTokens", 0),
                "inputTokens": stats.get("inputTokens", 0),
                "outputTokens": stats.get("outputTokens", 0),
                "toolsUsed": stats.get("toolUseCount", 0),
                "startedAt": stats["startTime"],
                "endedAt": stats["endTime"],
                "updatedAt": datetime.now(UTC),
            }

            # Add summary if provided
            if summary:
                update_data["summary"] = summary

            # Update session
            update_result = await self.db.sessions.update_one(
                {"sessionId": session_id},
                {"$set": update_data},
            )

            # Extract summary from messages if available, or generate if needed
            if update_result.modified_count > 0:
                session = await self.db.sessions.find_one({"sessionId": session_id})
                if session and not session.get("summary"):
                    # First, try to find a summary in the messages
                    message_with_summary = await self.db.messages.find_one(
                        {
                            "sessionId": session_id,
                            "summary": {"$exists": True, "$ne": None},
                        }
                    )

                    if message_with_summary and message_with_summary.get("summary"):
                        # Extract summary from message and store it on the session
                        await self.db.sessions.update_one(
                            {"sessionId": session_id},
                            {"$set": {"summary": message_with_summary["summary"]}},
                        )
                    else:
                        # Fallback to generating summary
                        from .session import SessionService

                        session_service = SessionService(self.db)
                        # Use the user_id from self instead of from session
                        await session_service.generate_summary(
                            self.user_id, str(session["_id"])
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
