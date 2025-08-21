"""Project service layer."""

from datetime import UTC, datetime
from typing import Any, cast

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.project import ProjectInDB, ProjectStats, PyObjectId
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectWithStats


class ProjectService:
    """Service for project operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def list_projects(
        self,
        filter_dict: dict[str, Any],
        skip: int,
        limit: int,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[ProjectWithStats], int]:
        """List projects with pagination."""
        # Count total
        total = await self.db.projects.count_documents(filter_dict)

        # Build sort
        sort_direction = -1 if sort_order == "desc" else 1

        # Special handling for nested fields
        sort_field = "stats.message_count" if sort_by == "message_count" else sort_by

        # Get projects
        cursor = (
            self.db.projects.find(filter_dict)
            .sort(sort_field, sort_direction)
            .skip(skip)
            .limit(limit)
        )

        projects = []
        async for doc in cursor:
            # Convert ObjectId to string
            doc["_id"] = str(doc["_id"])
            # Enrich with real-time stats
            stats = await self._get_project_stats(ObjectId(doc["_id"]))
            doc["stats"] = stats
            projects.append(ProjectWithStats(**doc))

        return projects, total

    async def get_project(self, project_id: ObjectId) -> ProjectWithStats | None:
        """Get a single project."""
        doc = await self.db.projects.find_one({"_id": project_id})
        if not doc:
            return None

        # Convert ObjectId to string
        doc["_id"] = str(doc["_id"])
        # Enrich with stats
        stats = await self._get_project_stats(project_id)
        doc["stats"] = stats

        return ProjectWithStats(**doc)

    async def get_project_by_path(self, path: str) -> ProjectInDB | None:
        """Get project by path."""
        doc = await self.db.projects.find_one({"path": path})
        if doc:
            doc["_id"] = str(doc["_id"])
        return ProjectInDB(**doc) if doc else None

    async def create_project(self, project: ProjectCreate) -> ProjectInDB:
        """Create a new project."""
        doc = {
            "_id": ObjectId(),
            "name": project.name,
            "path": project.path,
            "description": project.description,
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }

        await self.db.projects.insert_one(doc)
        return ProjectInDB(
            _id=PyObjectId(cast(ObjectId, doc["_id"])),
            name=cast(str, doc["name"]),
            description=cast(str | None, doc.get("description")),
            path=cast(str, doc["path"]),
            stats=ProjectStats(),
            createdAt=cast(datetime, doc["createdAt"]),
            updatedAt=cast(datetime, doc["updatedAt"]),
        )

    async def update_project(
        self, project_id: ObjectId, update: ProjectUpdate
    ) -> ProjectInDB | None:
        """Update a project."""
        update_dict = update.model_dump(exclude_unset=True)
        if update_dict:
            update_dict["updatedAt"] = datetime.now(UTC)

            result = await self.db.projects.find_one_and_update(
                {"_id": project_id}, {"$set": update_dict}, return_document=True
            )

            if result:
                result["_id"] = str(result["_id"])
                return ProjectInDB(**result)
            return None

        # If no update provided, return existing project
        existing = await self.db.projects.find_one({"_id": project_id})
        if existing:
            existing["_id"] = str(existing["_id"])
            return ProjectInDB(**existing)
        return None

    async def delete_project(self, project_id: ObjectId, cascade: bool = False) -> bool:
        """Delete a project with robust error handling and recovery.

        Always performs cascade deletion to prevent orphaned data.
        The cascade parameter is kept for backward compatibility but is now ignored.
        """
        import os

        from app.services.project_deletion import ProjectDeletionService

        deletion_service = ProjectDeletionService(self.db)

        # Use faster retry for tests
        retry_delay = 0 if os.environ.get("TESTING") else 2.0

        # Use the robust deletion with recovery
        result = await deletion_service.delete_project_with_recovery(
            project_id, retry_delay=retry_delay
        )

        if not result["success"]:
            # Log the error but still try to clean up
            error_msg = result.get("error", "Unknown error")
            print(f"Project deletion failed: {error_msg}")

            # Try cleanup to remove any orphaned data
            await deletion_service._cleanup_orphaned_data(project_id)

        return bool(result["success"])

    async def delete_project_async(
        self, project_id: ObjectId, cascade: bool = False
    ) -> None:
        """Delete a project asynchronously with progress updates via WebSocket.

        Uses robust deletion with proper error handling and recovery.
        Always performs cascade deletion to prevent orphaned data.
        """
        from app.services.project_deletion import ProjectDeletionService
        from app.services.websocket_manager import connection_manager

        project_id_str = str(project_id)
        deletion_service = ProjectDeletionService(self.db)

        try:
            # Start deletion process
            await connection_manager.broadcast_deletion_progress(
                project_id=project_id_str,
                stage="initializing",
                progress=0,
                message="Starting robust project deletion...",
            )

            # Get counts for progress tracking
            await connection_manager.broadcast_deletion_progress(
                project_id=project_id_str,
                stage="analyzing",
                progress=10,
                message="Analyzing project data...",
            )

            session_ids = await self.db.sessions.distinct(
                "sessionId", {"projectId": project_id}
            )
            total_sessions = len(session_ids)

            if total_sessions == 0:
                message_count = 0
            else:
                message_count = await self.db.messages.count_documents(
                    {"sessionId": {"$in": session_ids}}
                )

            await connection_manager.broadcast_deletion_progress(
                project_id=project_id_str,
                stage="analyzing",
                progress=20,
                message=f"Found {message_count} messages in {total_sessions} sessions",
            )

            # Use robust deletion with recovery
            await connection_manager.broadcast_deletion_progress(
                project_id=project_id_str,
                stage="deleting",
                progress=30,
                message="Performing transactional deletion...",
            )

            result = await deletion_service.delete_project_with_recovery(project_id)

            if result["success"]:
                await connection_manager.broadcast_deletion_progress(
                    project_id=project_id_str,
                    stage="completed",
                    progress=100,
                    message=f"Successfully deleted: {result['messages_deleted']} messages, {result['sessions_deleted']} sessions",
                    completed=True,
                )
            else:
                error_msg = result.get("error", "Unknown error")

                # Attempt cleanup
                await connection_manager.broadcast_deletion_progress(
                    project_id=project_id_str,
                    stage="cleanup",
                    progress=80,
                    message="Deletion failed, attempting cleanup...",
                )

                cleanup_stats = await deletion_service.cleanup_all_orphaned_data()

                await connection_manager.broadcast_deletion_progress(
                    project_id=project_id_str,
                    stage="error",
                    progress=100,
                    message=f"Deletion failed: {error_msg}. Cleaned up {cleanup_stats['orphaned_messages']} orphaned messages and {cleanup_stats['orphaned_sessions']} orphaned sessions.",
                    completed=True,
                    error=error_msg,
                )

        except Exception as e:
            # Even on exception, try to clean up
            try:
                await deletion_service._cleanup_orphaned_data(project_id)
            except Exception:
                pass

            await connection_manager.broadcast_deletion_progress(
                project_id=project_id_str,
                stage="error",
                progress=0,
                message=f"Critical error: {str(e)}",
                completed=True,
                error=str(e),
            )
            raise

    async def get_project_statistics(self, project_id: ObjectId) -> dict | None:
        """Get detailed project statistics."""
        # Check project exists
        project = await self.db.projects.find_one({"_id": project_id})
        if not project:
            return None

        # Get session IDs
        session_ids = await self.db.sessions.distinct(
            "sessionId", {"projectId": project_id}
        )

        # Aggregate statistics
        pipeline: list[dict[str, Any]] = [
            {"$match": {"sessionId": {"$in": session_ids}}},
            {
                "$group": {
                    "_id": None,
                    "total_messages": {"$sum": 1},
                    "user_messages": {
                        "$sum": {"$cond": [{"$eq": ["$type", "user"]}, 1, 0]}
                    },
                    "assistant_messages": {
                        "$sum": {"$cond": [{"$eq": ["$type", "assistant"]}, 1, 0]}
                    },
                    "total_cost": {"$sum": {"$ifNull": ["$costUsd", 0]}},
                    "models_used": {"$addToSet": "$model"},
                    "first_message": {"$min": "$timestamp"},
                    "last_message": {"$max": "$timestamp"},
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)

        if result:
            stats: dict[str, Any] = result[0]
            stats["session_count"] = len(session_ids)
            stats["project_id"] = str(project_id)
            return stats

        return {
            "project_id": str(project_id),
            "session_count": 0,
            "total_messages": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "total_cost": 0,
            "models_used": [],
        }

    async def _get_project_stats(self, project_id: ObjectId) -> dict:
        """Get basic project statistics."""
        # Count sessions
        session_count = await self.db.sessions.count_documents(
            {"projectId": project_id}
        )

        # Count messages (through sessions)
        session_ids = await self.db.sessions.distinct(
            "sessionId", {"projectId": project_id}
        )

        message_count = await self.db.messages.count_documents(
            {"sessionId": {"$in": session_ids}}
        )

        return {"session_count": session_count, "message_count": message_count}
