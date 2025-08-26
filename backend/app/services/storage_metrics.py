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
        tasks = [
            self._calculate_collection_metrics("sessions", user_oid),
            self._calculate_collection_metrics("messages", user_oid),
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
        collections = ["sessions", "messages", "projects"]
        tasks = []

        for collection in collections:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_size": {"$sum": {"$bsonSize": "$$ROOT"}},
                        "document_count": {"$sum": 1},
                    }
                }
            ]
            tasks.append(self.db[collection].aggregate(pipeline).to_list(1))

        results = await asyncio.gather(*tasks)

        total_size = 0
        total_docs = 0
        breakdown = {}

        for i, collection in enumerate(collections):
            if results[i]:
                size = results[i][0]["total_size"]
                count = results[i][0]["document_count"]
            else:
                size = 0
                count = 0

            total_size += size
            total_docs += count
            breakdown[f"{collection}_bytes"] = size
            breakdown[f"{collection}_count"] = count

        return {
            "total_disk_usage": total_size,
            "total_document_count": total_docs,
            "breakdown": breakdown,
            "calculated_at": datetime.now(UTC),
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
