"""Robust project deletion service with transaction support and recovery."""

import asyncio
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClientSession, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.core.logging import get_logger

logger = get_logger(__name__)


class ProjectDeletionService:
    """Service for robust project deletion with proper cleanup."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._deletion_tasks: dict[str, asyncio.Task] = {}

    async def delete_project_transactional(
        self, project_id: ObjectId, force: bool = False
    ) -> dict[str, Any]:
        """Delete a project with transaction support for atomicity.

        Args:
            project_id: The project ID to delete
            force: If True, skip safety checks and force deletion

        Returns:
            Dict with deletion results
        """
        project_id_str = str(project_id)

        # Check if deletion is already in progress
        if project_id_str in self._deletion_tasks:
            task = self._deletion_tasks[project_id_str]
            if not task.done():
                return {
                    "success": False,
                    "error": "Deletion already in progress for this project",
                    "task_id": id(task),
                }

        # Check if client supports transactions (not available in mocks/standalone)
        if not hasattr(self.db, "client"):
            # Fall back to non-transactional
            return await self._delete_without_transaction(project_id)

        # Start a session for transaction
        async with await self.db.client.start_session() as session:
            try:
                # Start transaction
                async with session.start_transaction():
                    return await self._delete_with_session(project_id, session, force)
            except Exception as e:
                logger.error(f"Transaction failed for project {project_id}: {e}")
                # Transaction automatically rolls back on exception
                raise

    async def _delete_with_session(
        self,
        project_id: ObjectId,
        session: AsyncIOMotorClientSession,
        force: bool = False,
    ) -> dict[str, Any]:
        """Execute deletion within a transaction session.

        This ensures atomicity - either everything is deleted or nothing is.
        """
        stats = {
            "project_id": str(project_id),
            "deleted_at": datetime.now(UTC).isoformat(),
            "messages_deleted": 0,
            "sessions_deleted": 0,
            "project_deleted": False,
            "success": False,
            "error": None,
        }

        try:
            # 1. First verify project exists
            project = await self.db.projects.find_one(
                {"_id": project_id}, session=session
            )
            if not project:
                stats["error"] = "Project not found"
                return stats

            # 2. Get all session IDs for this project
            sessions_cursor = self.db.sessions.find(
                {"projectId": project_id}, {"sessionId": 1}, session=session
            )
            session_ids = []
            async for doc in sessions_cursor:
                if "sessionId" in doc:
                    session_ids.append(doc["sessionId"])

            logger.info(f"Found {len(session_ids)} sessions for project {project_id}")

            # 3. Delete in reverse order (most dependent first)
            # This ensures if we're interrupted, we don't lose the parent references

            # Delete all messages first
            if session_ids:
                messages_result = await self.db.messages.delete_many(
                    {"sessionId": {"$in": session_ids}}, session=session
                )
                stats["messages_deleted"] = messages_result.deleted_count
                logger.info(f"Deleted {messages_result.deleted_count} messages")

            # Delete all sessions
            sessions_result = await self.db.sessions.delete_many(
                {"projectId": project_id}, session=session
            )
            stats["sessions_deleted"] = sessions_result.deleted_count
            logger.info(f"Deleted {sessions_result.deleted_count} sessions")

            # Finally delete the project
            project_result = await self.db.projects.delete_one(
                {"_id": project_id}, session=session
            )
            stats["project_deleted"] = project_result.deleted_count > 0
            logger.info(f"Deleted project: {project_result.deleted_count > 0}")

            stats["success"] = True
            return stats

        except PyMongoError as e:
            stats["error"] = f"Database error: {str(e)}"
            logger.error(f"MongoDB error during deletion: {e}")
            raise
        except Exception as e:
            stats["error"] = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error during deletion: {e}")
            raise

    async def delete_project_with_recovery(
        self, project_id: ObjectId, max_retries: int = 3, retry_delay: float = 2.0
    ) -> dict[str, Any]:
        """Delete a project with automatic retry on failure.

        This method will retry the deletion if it fails, ensuring
        eventual consistency even if there are transient failures.

        Args:
            project_id: The project to delete
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries (seconds). Set to 0 for tests.
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Deletion attempt {attempt + 1}/{max_retries} for project {project_id}"
                )

                # Try transactional deletion first
                try:
                    result = await self.delete_project_transactional(project_id)
                    if result["success"]:
                        return result
                    last_error = result.get("error", "Unknown error")
                except Exception as e:
                    logger.warning(
                        f"Transactional deletion failed, trying non-transactional: {e}"
                    )
                    # Fall back to non-transactional deletion if transactions aren't supported
                    result = await self._delete_without_transaction(project_id)
                    if result["success"]:
                        return result
                    last_error = result.get("error", str(e))

                # Wait before retry (exponential backoff)
                if attempt < max_retries - 1 and retry_delay > 0:
                    wait_time = retry_delay * (2**attempt)
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)

            except Exception as e:
                last_error = str(e)
                logger.error(f"Attempt {attempt + 1} failed: {e}")

        # All retries failed
        return {
            "success": False,
            "error": f"Failed after {max_retries} attempts. Last error: {last_error}",
            "project_id": str(project_id),
        }

    async def _delete_without_transaction(self, project_id: ObjectId) -> dict[str, Any]:
        """Fallback non-transactional deletion with careful ordering.

        This deletes in an order that minimizes orphans if interrupted:
        1. Mark project as "deleting"
        2. Delete messages
        3. Delete sessions
        4. Delete project
        """
        stats: dict[str, Any] = {
            "project_id": str(project_id),
            "deleted_at": datetime.now(UTC).isoformat(),
            "messages_deleted": 0,
            "sessions_deleted": 0,
            "project_deleted": False,
            "success": False,
            "error": None,
        }

        try:
            # 1. Mark project as being deleted (add a deletion flag)
            mark_result = await self.db.projects.update_one(
                {"_id": project_id},
                {"$set": {"isDeleting": True, "deletionStartedAt": datetime.now(UTC)}},
            )

            if mark_result.matched_count == 0:
                stats["error"] = "Project not found"
                return stats

            # 2. Get session IDs
            session_ids = await self.db.sessions.distinct(
                "sessionId", {"projectId": project_id}
            )
            logger.info(f"Found {len(session_ids)} sessions to delete")

            # 3. Delete messages in batches to avoid timeouts
            if session_ids:
                batch_size = 1000
                for i in range(0, len(session_ids), batch_size):
                    batch = session_ids[i : i + batch_size]
                    result = await self.db.messages.delete_many(
                        {"sessionId": {"$in": batch}}
                    )
                    deleted_count = (
                        result.deleted_count if result.deleted_count is not None else 0
                    )
                    current_count = stats.get("messages_deleted", 0)
                    if isinstance(current_count, int):
                        stats["messages_deleted"] = current_count + deleted_count
                    else:
                        stats["messages_deleted"] = deleted_count

                logger.info(f"Deleted {stats['messages_deleted']} messages")

            # 4. Delete sessions
            sessions_result = await self.db.sessions.delete_many(
                {"projectId": project_id}
            )
            stats["sessions_deleted"] = sessions_result.deleted_count
            logger.info(f"Deleted {sessions_result.deleted_count} sessions")

            # 5. Finally delete the project
            project_result = await self.db.projects.delete_one({"_id": project_id})
            stats["project_deleted"] = project_result.deleted_count > 0

            stats["success"] = True
            return stats

        except Exception as e:
            stats["error"] = str(e)
            logger.error(f"Error during non-transactional deletion: {e}")

            # Try to clean up any partial deletion
            await self._cleanup_orphaned_data(project_id)
            return stats

    async def _cleanup_orphaned_data(self, project_id: ObjectId) -> None:
        """Clean up any orphaned data from a failed deletion.

        This method is called when a deletion fails to ensure
        we don't leave orphaned sessions or messages.
        """
        try:
            logger.info(f"Cleaning up orphaned data for project {project_id}")

            # Check if project still exists
            project = await self.db.projects.find_one({"_id": project_id})

            if not project:
                # Project is gone, clean up orphaned sessions and messages
                logger.info(
                    "Project deleted but may have orphaned data, cleaning up..."
                )

                # Find and delete orphaned sessions
                sessions = await self.db.sessions.find(
                    {"projectId": project_id}, {"sessionId": 1}
                ).to_list(None)

                if sessions:
                    session_ids = [s["sessionId"] for s in sessions if "sessionId" in s]

                    # Delete orphaned messages
                    if session_ids:
                        result = await self.db.messages.delete_many(
                            {"sessionId": {"$in": session_ids}}
                        )
                        logger.info(
                            f"Cleaned up {result.deleted_count} orphaned messages"
                        )

                    # Delete orphaned sessions
                    result = await self.db.sessions.delete_many(
                        {"projectId": project_id}
                    )
                    logger.info(f"Cleaned up {result.deleted_count} orphaned sessions")
            else:
                # Project still exists, remove deletion flag if present
                await self.db.projects.update_one(
                    {"_id": project_id},
                    {"$unset": {"isDeleting": "", "deletionStartedAt": ""}},
                )

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def cleanup_all_orphaned_data(self) -> dict[str, int]:
        """Find and clean up all orphaned data in the database.

        This should be run periodically to ensure database consistency.
        """
        stats = {
            "orphaned_sessions": 0,
            "orphaned_messages": 0,
            "incomplete_deletions": 0,
        }

        try:
            # 1. Find projects marked as deleting (incomplete deletions)
            deleting_projects = await self.db.projects.find(
                {"isDeleting": True}
            ).to_list(None)

            for project in deleting_projects:
                # Resume deletion for projects that were being deleted
                deletion_started = project.get("deletionStartedAt")
                if deletion_started:
                    # If deletion was started more than 1 hour ago, resume it
                    time_diff = datetime.now(UTC) - deletion_started
                    if time_diff.total_seconds() > 3600:  # 1 hour
                        logger.info(f"Resuming deletion for project {project['_id']}")
                        await self.delete_project_with_recovery(project["_id"])
                        stats["incomplete_deletions"] += 1

            # 2. Find all valid project IDs
            project_ids = await self.db.projects.distinct("_id")

            # 3. Find and delete orphaned sessions
            orphaned_sessions = await self.db.sessions.find(
                {"projectId": {"$nin": project_ids}}
            ).to_list(None)

            if orphaned_sessions:
                session_ids = [
                    s.get("sessionId") for s in orphaned_sessions if s.get("sessionId")
                ]

                # Delete messages for orphaned sessions
                if session_ids:
                    result = await self.db.messages.delete_many(
                        {"sessionId": {"$in": session_ids}}
                    )
                    stats["orphaned_messages"] += result.deleted_count

                # Delete orphaned sessions
                result = await self.db.sessions.delete_many(
                    {"projectId": {"$nin": project_ids}}
                )
                stats["orphaned_sessions"] = result.deleted_count

            # 4. Find all valid session IDs
            valid_session_ids = await self.db.sessions.distinct("sessionId")

            # 5. Delete orphaned messages (messages without valid sessions)
            result = await self.db.messages.delete_many(
                {"sessionId": {"$nin": valid_session_ids}}
            )
            stats["orphaned_messages"] += result.deleted_count

            logger.info(f"Cleanup complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise
