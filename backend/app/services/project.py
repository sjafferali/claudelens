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
        """Delete a project."""
        if cascade:
            # Delete all associated data
            # Get all session IDs
            session_ids = await self.db.sessions.distinct(
                "sessionId", {"projectId": project_id}
            )

            # Delete messages
            await self.db.messages.delete_many({"sessionId": {"$in": session_ids}})

            # Delete sessions
            await self.db.sessions.delete_many({"projectId": project_id})

        # Delete project
        result = await self.db.projects.delete_one({"_id": project_id})
        return result.deleted_count > 0

    async def delete_project_async(
        self, project_id: ObjectId, cascade: bool = False
    ) -> None:
        """Delete a project asynchronously with progress updates via WebSocket."""
        from app.services.websocket_manager import connection_manager

        project_id_str = str(project_id)

        try:
            # Start deletion process
            await connection_manager.broadcast_deletion_progress(
                project_id=project_id_str,
                stage="initializing",
                progress=0,
                message="Starting project deletion...",
            )

            if cascade:
                # Get all session IDs and count for progress tracking
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
                    # Count total messages for progress tracking
                    message_count = await self.db.messages.count_documents(
                        {"sessionId": {"$in": session_ids}}
                    )

                await connection_manager.broadcast_deletion_progress(
                    project_id=project_id_str,
                    stage="analyzing",
                    progress=20,
                    message=f"Found {message_count} messages in {total_sessions} sessions",
                )

                # Delete messages in batches for large projects
                if message_count > 0:
                    await connection_manager.broadcast_deletion_progress(
                        project_id=project_id_str,
                        stage="deleting_messages",
                        progress=30,
                        message=f"Deleting {message_count} messages...",
                    )

                    # Delete messages in batches of 1000 to avoid timeouts
                    batch_size = 1000
                    total_batches = (message_count + batch_size - 1) // batch_size

                    for batch_idx in range(total_batches):
                        skip = batch_idx * batch_size

                        # Get batch of message IDs
                        message_batch = (
                            await self.db.messages.find(
                                {"sessionId": {"$in": session_ids}}, {"_id": 1}
                            )
                            .skip(skip)
                            .limit(batch_size)
                            .to_list(batch_size)
                        )

                        if message_batch:
                            message_ids = [msg["_id"] for msg in message_batch]
                            await self.db.messages.delete_many(
                                {"_id": {"$in": message_ids}}
                            )

                        progress = 30 + (batch_idx + 1) / total_batches * 50
                        await connection_manager.broadcast_deletion_progress(
                            project_id=project_id_str,
                            stage="deleting_messages",
                            progress=int(progress),
                            message=f"Deleted batch {batch_idx + 1}/{total_batches} of messages",
                        )

                # Delete sessions
                if total_sessions > 0:
                    await connection_manager.broadcast_deletion_progress(
                        project_id=project_id_str,
                        stage="deleting_sessions",
                        progress=80,
                        message=f"Deleting {total_sessions} sessions...",
                    )

                    await self.db.sessions.delete_many({"projectId": project_id})

                await connection_manager.broadcast_deletion_progress(
                    project_id=project_id_str,
                    stage="deleting_sessions",
                    progress=90,
                    message="All associated data deleted",
                )

            # Delete project
            await connection_manager.broadcast_deletion_progress(
                project_id=project_id_str,
                stage="deleting_project",
                progress=95,
                message="Deleting project metadata...",
            )

            result = await self.db.projects.delete_one({"_id": project_id})

            if result.deleted_count > 0:
                await connection_manager.broadcast_deletion_progress(
                    project_id=project_id_str,
                    stage="completed",
                    progress=100,
                    message="Project successfully deleted",
                    completed=True,
                )
            else:
                raise ValueError("Project not found or already deleted")

        except Exception as e:
            await connection_manager.broadcast_deletion_progress(
                project_id=project_id_str,
                stage="error",
                progress=0,
                message="Deletion failed",
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
