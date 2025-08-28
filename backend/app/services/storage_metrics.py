"""Storage metrics service for disk usage calculation."""

import asyncio
from datetime import UTC, datetime
from typing import Any, Dict, Mapping, Sequence

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class StorageMetricsService:
    """Calculate and cache storage metrics per tenant."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def calculate_user_metrics(self, user_id: str) -> Dict[str, Any]:
        """Calculate comprehensive storage metrics for a user."""
        user_oid = ObjectId(user_id)

        # Parallel aggregation pipelines for different collections
        # Note: messages are stored in rolling collections, handled separately
        tasks = [
            self._calculate_collection_metrics("sessions", user_oid),
            self._calculate_rolling_messages_metrics(user_oid),
            self._calculate_collection_metrics("projects", user_oid),
        ]

        results = await asyncio.gather(*tasks)

        # Combine results
        total_size = sum(r["total_size"] for r in results)
        total_count = sum(r["document_count"] for r in results)

        return {
            "user_id": user_id,
            "sessions": results[0],
            "messages": results[1],
            "projects": results[2],
            "total_disk_usage": total_size,
            "total_document_count": total_count,
            "breakdown": {
                "sessions_bytes": results[0]["total_size"],
                "messages_bytes": results[1]["total_size"],
                "projects_bytes": results[2]["total_size"],
            },
        }

    async def _calculate_collection_metrics(
        self, collection_name: str, user_id: ObjectId
    ) -> Dict[str, Any]:
        """Calculate metrics for a specific collection."""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": None,
                    "total_size": {"$sum": {"$bsonSize": "$$ROOT"}},
                    "document_count": {"$sum": 1},
                    "avg_size": {"$avg": {"$bsonSize": "$$ROOT"}},
                    "max_size": {"$max": {"$bsonSize": "$$ROOT"}},
                }
            },
        ]

        pipeline_typed: Sequence[Mapping[str, Any]] = pipeline  # type: ignore
        result = await self.db[collection_name].aggregate(pipeline_typed).to_list(1)

        if result:
            return dict(result[0])
        return {
            "total_size": 0,
            "document_count": 0,
            "avg_size": 0,
            "max_size": 0,
        }

    async def _calculate_rolling_messages_metrics(
        self, user_id: ObjectId
    ) -> Dict[str, Any]:
        """Calculate metrics for messages across rolling collections."""
        # Get all message collections (messages_YYYY_MM format)
        all_collections = await self.db.list_collection_names()
        message_collections = [c for c in all_collections if c.startswith("messages_")]

        if not message_collections:
            # Fallback to single messages collection if it exists
            if "messages" in all_collections:
                # Messages might have user_id field (old schema)
                return await self._calculate_collection_metrics("messages", user_id)
            return {
                "total_size": 0,
                "document_count": 0,
                "avg_size": 0,
                "max_size": 0,
            }

        # Get user's session IDs through projects
        # First get user's projects
        user_projects = await self.db.projects.find(
            {"user_id": user_id}, {"_id": 1}
        ).to_list(None)
        project_ids = [p["_id"] for p in user_projects]

        if not project_ids:
            return {
                "total_size": 0,
                "document_count": 0,
                "avg_size": 0,
                "max_size": 0,
            }

        # Get session IDs for user's projects
        session_ids = await self.db.sessions.distinct(
            "sessionId", {"projectId": {"$in": project_ids}}
        )

        if not session_ids:
            return {
                "total_size": 0,
                "document_count": 0,
                "avg_size": 0,
                "max_size": 0,
            }

        # Aggregate metrics across all message collections for these sessions
        total_size = 0
        total_count = 0
        max_size = 0
        all_sizes = []

        for collection_name in message_collections:
            pipeline = [
                {"$match": {"sessionId": {"$in": session_ids}}},
                {
                    "$group": {
                        "_id": None,
                        "total_size": {"$sum": {"$bsonSize": "$$ROOT"}},
                        "document_count": {"$sum": 1},
                        "avg_size": {"$avg": {"$bsonSize": "$$ROOT"}},
                        "max_size": {"$max": {"$bsonSize": "$$ROOT"}},
                    }
                },
            ]

            pipeline_typed: Sequence[Mapping[str, Any]] = pipeline  # type: ignore
            result = await self.db[collection_name].aggregate(pipeline_typed).to_list(1)

            if result and result[0]:
                total_size += result[0].get("total_size", 0)
                total_count += result[0].get("document_count", 0)
                max_size = max(max_size, result[0].get("max_size", 0))
                if result[0].get("document_count", 0) > 0:
                    all_sizes.append(result[0].get("avg_size", 0))

        avg_size = sum(all_sizes) / len(all_sizes) if all_sizes else 0

        return {
            "total_size": total_size,
            "document_count": total_count,
            "avg_size": avg_size,
            "max_size": max_size,
        }

    async def update_user_storage_cache(self, user_id: str) -> Dict[str, Any]:
        """Update cached storage metrics for a user."""
        metrics = await self.calculate_user_metrics(user_id)

        # Update user document with denormalized metrics
        await self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "project_count": metrics["projects"]["document_count"],
                    "session_count": metrics["sessions"]["document_count"],
                    "message_count": metrics["messages"]["document_count"],
                    "total_disk_usage": metrics["total_disk_usage"],
                    "storage_updated_at": datetime.now(UTC),
                }
            },
        )

        return metrics

    async def calculate_system_metrics(self) -> Dict[str, Any]:
        """Calculate system-wide storage metrics."""
        # Get aggregated metrics across all users
        # Note: messages are in rolling collections, handled separately

        # Calculate sessions and projects normally
        sessions_task = self._calculate_system_collection_metrics("sessions")
        projects_task = self._calculate_system_collection_metrics("projects")

        # Calculate messages across rolling collections
        messages_task = self._calculate_system_rolling_messages_metrics()

        results = await asyncio.gather(sessions_task, messages_task, projects_task)

        total_size = sum(r["total_size"] for r in results)
        total_docs = sum(r["document_count"] for r in results)

        breakdown = {
            "sessions_bytes": results[0]["total_size"],
            "sessions_count": results[0]["document_count"],
            "messages_bytes": results[1]["total_size"],
            "messages_count": results[1]["document_count"],
            "projects_bytes": results[2]["total_size"],
            "projects_count": results[2]["document_count"],
        }

        return {
            "total_disk_usage": total_size,
            "total_document_count": total_docs,
            "breakdown": breakdown,
            "calculated_at": datetime.now(UTC),
        }

    async def _calculate_system_collection_metrics(
        self, collection_name: str
    ) -> Dict[str, Any]:
        """Calculate system-wide metrics for a specific collection."""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_size": {"$sum": {"$bsonSize": "$$ROOT"}},
                    "document_count": {"$sum": 1},
                }
            }
        ]

        result = await self.db[collection_name].aggregate(pipeline).to_list(1)

        if result and result[0]:
            return {
                "total_size": result[0]["total_size"],
                "document_count": result[0]["document_count"],
            }
        return {"total_size": 0, "document_count": 0}

    async def _calculate_system_rolling_messages_metrics(self) -> Dict[str, Any]:
        """Calculate system-wide metrics for messages across rolling collections."""
        # Get all message collections
        all_collections = await self.db.list_collection_names()
        message_collections = [c for c in all_collections if c.startswith("messages_")]

        if not message_collections:
            # Fallback to single messages collection if it exists
            if "messages" in all_collections:
                return await self._calculate_system_collection_metrics("messages")
            return {"total_size": 0, "document_count": 0}

        # Aggregate across all rolling collections
        total_size = 0
        total_count = 0

        for collection_name in message_collections:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_size": {"$sum": {"$bsonSize": "$$ROOT"}},
                        "document_count": {"$sum": 1},
                    }
                }
            ]

            result = await self.db[collection_name].aggregate(pipeline).to_list(1)

            if result and result[0]:
                total_size += result[0]["total_size"]
                total_count += result[0]["document_count"]

        return {
            "total_size": total_size,
            "document_count": total_count,
        }

    async def get_top_users_by_storage(self, limit: int = 10) -> list:
        """Get top users by storage usage."""
        pipeline = [
            {"$sort": {"total_disk_usage": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 1,
                    "username": 1,
                    "email": 1,
                    "total_disk_usage": 1,
                    "session_count": 1,
                    "message_count": 1,
                    "project_count": 1,
                }
            },
        ]

        pipeline_typed: Sequence[Mapping[str, Any]] = pipeline  # type: ignore
        result = await self.db.users.aggregate(pipeline_typed).to_list(None)
        return result

    async def batch_update_all_users(self) -> Dict[str, Any]:
        """Batch update storage metrics for all users."""
        # Get all user IDs
        user_ids = await self.db.users.distinct("_id")

        # Update metrics for each user
        update_tasks = []
        for user_id in user_ids:
            update_tasks.append(self.update_user_storage_cache(str(user_id)))

        # Process in batches to avoid overwhelming the database
        batch_size = 10
        results = []
        for i in range(0, len(update_tasks), batch_size):
            batch = update_tasks[i : i + batch_size]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)

        return {
            "users_updated": len(results),
            "timestamp": datetime.now(UTC),
        }
