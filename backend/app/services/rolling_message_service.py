"""Simple rolling collections message service."""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel

from app.core.logging import get_logger

logger = get_logger(__name__)


class RollingMessageService:
    """Service for managing monthly partitioned message collections."""

    # Cache to track which collections exist and have indexes
    _indexed_collections: Set[str] = set()

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    def get_collection_name(self, timestamp: datetime) -> str:
        """
        Get collection name for a given timestamp.
        Format: messages_YYYY_MM
        """
        return f"messages_{timestamp.strftime('%Y_%m')}"

    async def ensure_collection_with_indexes(
        self, collection_name: str
    ) -> AsyncIOMotorCollection:
        """
        Get or create collection with indexes.
        """
        collection = self.db[collection_name]

        # Create indexes if not already done
        if collection_name not in self._indexed_collections:
            await self.create_indexes(collection)
            self._indexed_collections.add(collection_name)
            logger.info(f"Created collection with indexes: {collection_name}")

        return collection

    async def create_indexes(self, collection: AsyncIOMotorCollection) -> None:
        """
        Create standard indexes for message collections.
        All collections get the same comprehensive index set.
        """
        indexes = [
            # Unique identifier
            IndexModel([("uuid", ASCENDING)], unique=True),
            # Core query patterns
            IndexModel([("sessionId", ASCENDING), ("timestamp", ASCENDING)]),
            IndexModel([("timestamp", DESCENDING)]),
            IndexModel([("user_id", ASCENDING), ("timestamp", DESCENDING)]),
            IndexModel([("type", ASCENDING), ("timestamp", DESCENDING)]),
            # Message relationships
            IndexModel([("parentUuid", ASCENDING)]),
            # Analytics queries
            IndexModel([("model", ASCENDING), ("timestamp", DESCENDING)]),
            IndexModel([("costUsd", DESCENDING)]),
            IndexModel([("gitBranch", ASCENDING), ("timestamp", DESCENDING)]),
            # Text search
            IndexModel([("$**", TEXT)]),
        ]

        try:
            await collection.create_indexes(indexes)
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    async def insert_message(self, message_data: Dict[str, Any]) -> str:
        """
        Insert a message into the appropriate monthly collection.
        """
        # Parse timestamp
        timestamp = message_data.get("timestamp", datetime.now(UTC))
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            message_data["timestamp"] = timestamp

        # Get target collection
        collection_name = self.get_collection_name(timestamp)
        collection = await self.ensure_collection_with_indexes(collection_name)

        # Insert message
        result = await collection.insert_one(message_data)
        logger.debug(f"Inserted message into {collection_name}")
        return str(result.inserted_id)

    async def find_messages(
        self,
        filter_dict: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort_order: str = "desc",
    ) -> tuple[List[Dict], int]:
        """
        Find messages across relevant monthly collections.
        """
        # Extract date range from filter
        start_date, end_date = self._extract_date_range(filter_dict)

        # Get collections for date range
        collection_names = await self.get_collections_for_range(start_date, end_date)
        if not collection_names:
            return [], 0

        # Query collections in parallel
        count_tasks = []
        fetch_tasks = []

        for coll_name in collection_names:
            collection = self.db[coll_name]
            count_tasks.append(collection.count_documents(filter_dict))

            # Fetch extra to handle pagination across collections
            cursor = collection.find(filter_dict).sort(
                "timestamp", DESCENDING if sort_order == "desc" else ASCENDING
            )
            fetch_tasks.append(cursor.to_list(limit + skip))

        # Execute parallel queries
        counts = await asyncio.gather(*count_tasks, return_exceptions=True)
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        # Process results
        all_messages: list[dict[str, Any]] = []
        total_count = 0

        for i, (count, messages) in enumerate(zip(counts, results)):
            if not isinstance(count, Exception) and isinstance(count, int):
                total_count += count
            if not isinstance(messages, Exception) and isinstance(messages, list):
                all_messages.extend(messages)

        # Sort combined results
        all_messages.sort(
            key=lambda x: x.get("timestamp", datetime.min.replace(tzinfo=UTC)),
            reverse=(sort_order == "desc"),
        )

        # Apply pagination
        return all_messages[skip : skip + limit], total_count

    def _extract_date_range(self, filter_dict: Dict) -> tuple[datetime, datetime]:
        """Extract date range from filter, defaulting to last 90 days."""
        if "timestamp" in filter_dict and isinstance(filter_dict["timestamp"], dict):
            ts_filter = filter_dict["timestamp"]
            start = ts_filter.get("$gte", datetime(2020, 1, 1, tzinfo=UTC))
            end = ts_filter.get("$lte", datetime.now(UTC))
            return start, end

        # Default: last 90 days
        end = datetime.now(UTC)
        start = end - timedelta(days=90)
        return start, end

    async def get_collections_for_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[str]:
        """
        Get collection names that cover the date range.
        Only returns collections that actually exist.
        """
        collections = set()
        current = start_date.replace(day=1)

        # Generate monthly collection names
        while current <= end_date:
            collections.add(self.get_collection_name(current))

            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        # Filter to existing collections
        existing = await self.db.list_collection_names()
        return sorted([c for c in collections if c in existing])

    async def aggregate_across_collections(
        self, pipeline: List[Dict], start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        """
        Run aggregation pipeline across multiple collections.
        """
        collections = await self.get_collections_for_range(start_date, end_date)
        if not collections:
            return []

        # Run aggregations in parallel
        tasks = []
        for coll_name in collections:
            collection = self.db[coll_name]
            tasks.append(collection.aggregate(pipeline).to_list(None))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        combined: list[dict[str, Any]] = []
        for result in results:
            if not isinstance(result, Exception) and isinstance(result, list):
                combined.extend(result)

        return combined

    async def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict]:
        """
        Find a single document across collections.
        """
        # If we have a timestamp hint, use it to target specific collection
        if "timestamp" in filter_dict:
            timestamp = filter_dict["timestamp"]
            if isinstance(timestamp, datetime):
                collection_name = self.get_collection_name(timestamp)
                if collection_name in await self.db.list_collection_names():
                    return await self.db[collection_name].find_one(filter_dict)

        # Otherwise search recent collections
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=90)
        collections = await self.get_collections_for_range(start_date, end_date)

        for coll_name in reversed(collections):  # Start with most recent
            doc = await self.db[coll_name].find_one(filter_dict)
            if doc:
                return dict(doc)

        return None

    async def update_one(
        self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]
    ) -> bool:
        """
        Update a single document across collections.
        """
        # First find the document
        doc = await self.find_one(filter_dict)
        if not doc:
            return False

        # Update in the correct collection
        collection_name = self.get_collection_name(doc["timestamp"])
        result = await self.db[collection_name].update_one(filter_dict, update_dict)
        return result.modified_count > 0

    async def count_documents(self, filter_dict: Dict[str, Any]) -> int:
        """
        Count documents across collections matching filter.
        """
        start_date, end_date = self._extract_date_range(filter_dict)
        collections = await self.get_collections_for_range(start_date, end_date)

        if not collections:
            return 0

        # Count in parallel
        tasks = []
        for coll_name in collections:
            collection = self.db[coll_name]
            tasks.append(collection.count_documents(filter_dict))

        counts = await asyncio.gather(*tasks, return_exceptions=True)
        total = sum(
            c for c in counts if not isinstance(c, Exception) and isinstance(c, int)
        )
        return total

    async def get_storage_metrics(self) -> Dict:
        """Monitor collection sizes and document counts."""
        collections = await self.db.list_collection_names()
        message_collections = [c for c in collections if c.startswith("messages_")]

        metrics = {}
        total_docs = 0
        total_size_mb = 0

        for coll_name in sorted(message_collections):
            stats = await self.db.command("collStats", coll_name)
            doc_count = stats.get("count", 0)
            size_mb = stats.get("size", 0) / 1024 / 1024

            metrics[coll_name] = {"documents": doc_count, "size_mb": round(size_mb, 2)}

            total_docs += doc_count
            total_size_mb += size_mb

        return {
            "collections": metrics,
            "total_documents": total_docs,
            "total_size_mb": round(total_size_mb, 2),
        }

    async def cleanup_empty_collections(self) -> List[str]:
        """Remove empty collections periodically."""
        collections = await self.db.list_collection_names()
        dropped = []

        for coll_name in collections:
            if coll_name.startswith("messages_"):
                count = await self.db[coll_name].count_documents({})
                if count == 0:
                    await self.db[coll_name].drop()
                    logger.info(f"Dropped empty collection: {coll_name}")
                    dropped.append(coll_name)

        return dropped
