# Simplified Rolling Collections Implementation

## Overview
A clean, straightforward approach to handling billions of messages using monthly collections. Messages are automatically routed to the appropriate monthly collection based on their timestamp, with collections created on-demand.

## Architecture

### Collection Naming Convention

```python
# Simple monthly collections
messages_2024_01  # January 2024
messages_2024_02  # February 2024
messages_2024_03  # March 2024
messages_2025_01  # January 2025
# ... collections created automatically as needed
```

### Core Principles

1. **Automatic Collection Creation**: Collections created on-demand when messages arrive
2. **Timestamp-Based Routing**: Messages go to collections based on their timestamp
3. **Consistent Indexing**: All collections get the same optimized indexes
4. **Parallel Querying**: Queries efficiently span relevant collections
5. **No Migration Needed**: Start fresh with new structure

## Implementation

### Core Service

```python
"""Simple rolling collections message service."""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
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
        self,
        collection_name: str
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

    async def create_indexes(self, collection: AsyncIOMotorCollection):
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

    async def insert_message(
        self,
        message_data: Dict[str, Any]
    ) -> str:
        """
        Insert a message into the appropriate monthly collection.
        """
        # Parse timestamp
        timestamp = message_data.get('timestamp', datetime.now(UTC))
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            message_data['timestamp'] = timestamp

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
        sort_order: str = "desc"
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
                "timestamp",
                DESCENDING if sort_order == "desc" else ASCENDING
            )
            fetch_tasks.append(cursor.to_list(limit + skip))

        # Execute parallel queries
        counts = await asyncio.gather(*count_tasks, return_exceptions=True)
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        # Process results
        all_messages = []
        total_count = 0

        for i, (count, messages) in enumerate(zip(counts, results)):
            if not isinstance(count, Exception):
                total_count += count
            if not isinstance(messages, Exception):
                all_messages.extend(messages)

        # Sort combined results
        all_messages.sort(
            key=lambda x: x.get('timestamp', datetime.min.replace(tzinfo=UTC)),
            reverse=(sort_order == "desc")
        )

        # Apply pagination
        return all_messages[skip:skip + limit], total_count

    def _extract_date_range(self, filter_dict: Dict) -> tuple[datetime, datetime]:
        """Extract date range from filter, defaulting to last 90 days."""
        if 'timestamp' in filter_dict and isinstance(filter_dict['timestamp'], dict):
            ts_filter = filter_dict['timestamp']
            start = ts_filter.get('$gte', datetime(2020, 1, 1, tzinfo=UTC))
            end = ts_filter.get('$lte', datetime.now(UTC))
            return start, end

        # Default: last 90 days
        end = datetime.now(UTC)
        start = end - timedelta(days=90)
        return start, end

    async def get_collections_for_range(
        self,
        start_date: datetime,
        end_date: datetime
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
        self,
        pipeline: List[Dict],
        start_date: datetime,
        end_date: datetime
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
        combined = []
        for result in results:
            if not isinstance(result, Exception):
                combined.extend(result)

        return combined
```

### Integration with Existing Services

```python
# Update your existing MessageService to use RollingMessageService
from app.services.rolling_message_service import RollingMessageService

class MessageService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.rolling_service = RollingMessageService(db)

    async def create_message(self, message_data: Dict[str, Any]) -> str:
        """Create a new message using rolling collections."""
        return await self.rolling_service.insert_message(message_data)

    async def list_messages(
        self,
        filter_dict: Dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Message], int]:
        """List messages across partitioned collections."""
        docs, total = await self.rolling_service.find_messages(
            filter_dict, skip, limit
        )
        messages = [Message(**doc) for doc in docs]
        return messages, total
```

### Query Patterns

```python
# 1. Always include timestamp hints when possible
async def query_with_date_hint(service: RollingMessageService):
    # Good: Includes timestamp filter
    results, count = await service.find_messages({
        "sessionId": "abc-123",
        "timestamp": {"$gte": datetime(2024, 1, 1, tzinfo=UTC)}
    })

    # Less efficient: No timestamp hint
    results, count = await service.find_messages({
        "sessionId": "abc-123"
    })  # Will search last 90 days by default

# 2. Use aggregations for analytics
async def get_cost_by_month(service: RollingMessageService):
    pipeline = [
        {"$group": {
            "_id": {
                "year": {"$year": "$timestamp"},
                "month": {"$month": "$timestamp"}
            },
            "totalCost": {"$sum": "$costUsd"},
            "messageCount": {"$sum": 1}
        }},
        {"$sort": {"_id": -1}}
    ]

    start_date = datetime(2024, 1, 1, tzinfo=UTC)
    end_date = datetime.now(UTC)

    results = await service.aggregate_across_collections(
        pipeline, start_date, end_date
    )
    return results

# 3. Efficient search with text indexes
async def search_messages(service: RollingMessageService):
    # Text search leverages indexes on each collection
    results, total = await service.find_messages({
        "$text": {"$search": "error exception"},
        "timestamp": {
            "$gte": datetime.now(UTC) - timedelta(days=30)
        }
    })
    return results
```

### Monitoring

```python
async def get_storage_metrics(service: RollingMessageService):
    """Monitor collection sizes and document counts."""
    collections = await service.db.list_collection_names()
    message_collections = [c for c in collections if c.startswith('messages_')]

    metrics = {}
    total_docs = 0
    total_size_mb = 0

    for coll_name in sorted(message_collections):
        stats = await service.db.command('collStats', coll_name)
        doc_count = stats.get('count', 0)
        size_mb = stats.get('size', 0) / 1024 / 1024

        metrics[coll_name] = {
            'documents': doc_count,
            'size_mb': round(size_mb, 2)
        }

        total_docs += doc_count
        total_size_mb += size_mb

    return {
        'collections': metrics,
        'total_documents': total_docs,
        'total_size_mb': round(total_size_mb, 2)
    }

async def cleanup_empty_collections(service: RollingMessageService):
    """Remove empty collections periodically."""
    collections = await service.db.list_collection_names()

    for coll_name in collections:
        if coll_name.startswith('messages_'):
            count = await service.db[coll_name].count_documents({})
            if count == 0:
                await service.db[coll_name].drop()
                logger.info(f"Dropped empty collection: {coll_name}")
```

## Key Benefits

### Why Rolling Collections?

1. **Linear Scalability**
   - Each collection stays at manageable size (~100M documents max)
   - Query performance remains consistent as data grows
   - No single collection bottleneck

2. **Efficient Queries**
   - Only relevant collections are queried
   - Parallel execution across collections
   - Better index utilization

3. **Simple Management**
   - Easy to backup/restore specific time periods
   - Can delete old data by dropping collections
   - Clear data lifecycle

4. **Flexible Historical Writes**
   - Can write to any time period
   - Collections created automatically as needed
   - No complex migration required

## Performance Tips

### Query Optimization
- **Always include timestamp filters** to minimize collections scanned
- **Use parallel aggregations** for analytics across multiple collections
- **Cache frequently accessed** historical data
- **Leverage indexes** - each collection has optimized indexes

### Write Optimization
- **Batch inserts** when importing historical data
- **Use bulk operations** for better throughput
- **Collections auto-created** on first write - no manual setup

## Example Analytics Update

```python
# Update your analytics service to work with partitioned data
class AnalyticsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.rolling_service = RollingMessageService(db)

    async def get_summary(self, time_range: TimeRange) -> AnalyticsSummary:
        """Get analytics summary across partitioned collections."""
        start_date, end_date = self._get_date_range(time_range)

        # Build aggregation pipeline
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }},
            {"$group": {
                "_id": None,
                "totalMessages": {"$sum": 1},
                "totalCost": {"$sum": "$costUsd"},
                "uniqueSessions": {"$addToSet": "$sessionId"}
            }}
        ]

        # Run across relevant collections
        results = await self.rolling_service.aggregate_across_collections(
            pipeline, start_date, end_date
        )

        # Process results
        if results:
            summary = results[0]
            return AnalyticsSummary(
                totalMessages=summary['totalMessages'],
                totalCost=summary['totalCost'],
                sessionCount=len(summary['uniqueSessions'])
            )

        return AnalyticsSummary()
```

## Implementation Steps

### 1. Deploy Service (Day 1)
```bash
# Add the RollingMessageService to your codebase
cp rolling_message_service.py backend/app/services/
```

### 2. Update Message Service (Day 1)
```python
# Modify existing MessageService to use rolling collections
def __init__(self, db):
    self.rolling_service = RollingMessageService(db)

async def create_message(self, data):
    return await self.rolling_service.insert_message(data)
```

### 3. Start Using (Day 1)
- New messages automatically go to monthly collections
- No migration needed - start fresh
- Existing code continues to work with minimal changes

### 4. Monitor Growth (Ongoing)
```python
# Set up monitoring endpoint
@router.get("/admin/collections/stats")
async def get_collection_stats(db: AsyncIOMotorDatabase):
    service = RollingMessageService(db)
    return await get_storage_metrics(service)
```

## Considerations

### Collection Limits
- MongoDB supports 10,000+ collections per database
- Each monthly collection = ~30-50M messages/month capacity
- At 1M messages/day, each collection holds ~30 days

### Index Strategy
- All collections get same indexes for consistency
- Text search index on all collections for full-text search
- Total index overhead: ~20-30% of data size

### Query Complexity
- Queries spanning many months touch multiple collections
- Sorting across collections requires client-side merge
- Aggregations run in parallel then merge results

## Summary

This simplified rolling collections approach provides:

✅ **No migration complexity** - Start fresh immediately
✅ **Automatic scaling** - Collections created as needed
✅ **Historical flexibility** - Write to any time period
✅ **Simple implementation** - One service class handles everything
✅ **Predictable performance** - Each collection stays small

Perfect for applications that need to scale to billions of documents while maintaining query performance and operational simplicity.
