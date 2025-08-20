# MongoDB Bulk Operations Guide for ClaudeLens

## Overview
This document provides MongoDB bulk operation patterns specifically for the ClaudeLens application, focusing on efficient data import/export operations.

## Bulk Write Operations

### Basic Pattern
```python
from pymongo import InsertOne, UpdateOne, ReplaceOne, DeleteOne
from motor.motor_asyncio import AsyncIOMotorDatabase

async def bulk_write_example(db: AsyncIOMotorDatabase):
    operations = []

    # Build operations list
    for item in items:
        operations.append(
            ReplaceOne(
                filter={"uuid": item["uuid"]},
                replacement=item,
                upsert=True  # Insert if not exists
            )
        )

    # Execute in batches of 1000 (MongoDB limit)
    BATCH_SIZE = 1000
    for i in range(0, len(operations), BATCH_SIZE):
        batch = operations[i:i + BATCH_SIZE]
        result = await db.collection.bulk_write(batch, ordered=False)

        # Track results
        print(f"Inserted: {result.inserted_count}")
        print(f"Modified: {result.modified_count}")
        print(f"Upserted: {result.upserted_count}")
```

### ClaudeLens-Specific: Message Import Pattern
```python
# From backend/app/services/ingest.py
async def bulk_import_messages(self, messages: list[dict]) -> BulkWriteResult:
    """Import messages with deduplication using contentHash"""
    operations = []

    for msg in messages:
        # Generate content hash for deduplication
        content_str = json.dumps(msg.get("message", {}), sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()

        msg["contentHash"] = content_hash

        # Use contentHash for deduplication
        operations.append(
            ReplaceOne(
                filter={"contentHash": content_hash},
                replacement=msg,
                upsert=True
            )
        )

    # Execute bulk write with error handling
    try:
        result = await self.db.messages.bulk_write(
            operations,
            ordered=False  # Continue on error
        )
        return result
    except BulkWriteError as e:
        # Handle partial success
        successful = e.details.get("nInserted", 0) + e.details.get("nUpserted", 0)
        logger.error(f"Bulk write partial success: {successful}/{len(operations)}")
        raise
```

## Aggregation Pipeline for Export

### Efficient Session Export with Messages
```python
async def export_sessions_with_messages(
    db: AsyncIOMotorDatabase,
    filter_criteria: dict = None
) -> AsyncGenerator:
    """Stream sessions with their messages using aggregation"""

    pipeline = [
        # Stage 1: Match sessions
        {"$match": filter_criteria or {}},

        # Stage 2: Lookup messages (join)
        {
            "$lookup": {
                "from": "messages",
                "localField": "sessionId",
                "foreignField": "sessionId",
                "as": "messages"
            }
        },

        # Stage 3: Sort messages by timestamp
        {
            "$addFields": {
                "messages": {
                    "$sortArray": {
                        "input": "$messages",
                        "sortBy": {"timestamp": 1}
                    }
                }
            }
        },

        # Stage 4: Add computed fields
        {
            "$addFields": {
                "messageCount": {"$size": "$messages"},
                "totalCost": {
                    "$sum": "$messages.costUsd"
                }
            }
        },

        # Stage 5: Project final structure
        {
            "$project": {
                "_id": 0,
                "id": {"$toString": "$_id"},
                "sessionId": 1,
                "projectId": 1,
                "messages": 1,
                "messageCount": 1,
                "totalCost": 1,
                "startedAt": 1,
                "endedAt": 1
            }
        }
    ]

    # Stream results to avoid memory issues
    async with db.sessions.aggregate(
        pipeline,
        allowDiskUse=True  # Use disk for large sorts
    ) as cursor:
        async for document in cursor:
            # Convert Decimal128 to float for JSON serialization
            if "totalCost" in document:
                document["totalCost"] = float(str(document["totalCost"]))

            yield document
```

## Batch Processing Pattern

### Process Large Datasets in Chunks
```python
async def process_in_batches(
    data: list,
    batch_size: int = 1000,
    process_func: Callable
) -> dict:
    """Process large datasets in manageable batches"""

    stats = {
        "processed": 0,
        "failed": 0,
        "batches": 0
    }

    total_batches = (len(data) + batch_size - 1) // batch_size

    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        batch_num = i // batch_size + 1

        try:
            # Process batch
            await process_func(batch)
            stats["processed"] += len(batch)
            stats["batches"] += 1

            # Report progress
            progress = (batch_num / total_batches) * 100
            logger.info(f"Batch {batch_num}/{total_batches} processed ({progress:.1f}%)")

        except Exception as e:
            logger.error(f"Batch {batch_num} failed: {e}")
            stats["failed"] += len(batch)

            # Decide whether to continue or abort
            if stats["failed"] > len(data) * 0.1:  # >10% failure rate
                raise Exception("Too many failures, aborting batch processing")

    return stats
```

## Transaction Support for Critical Operations

### Atomic Session Import with Rollback
```python
async def import_session_transactional(
    db: AsyncIOMotorDatabase,
    session_data: dict,
    messages: list[dict]
) -> bool:
    """Import session and messages atomically"""

    async with await db.client.start_session() as session:
        async with session.start_transaction():
            try:
                # Insert session
                session_result = await db.sessions.insert_one(
                    session_data,
                    session=session
                )

                # Prepare messages with session reference
                for msg in messages:
                    msg["sessionId"] = session_result.inserted_id

                # Bulk insert messages
                if messages:
                    await db.messages.insert_many(
                        messages,
                        session=session
                    )

                # Update project statistics
                await db.projects.update_one(
                    {"_id": session_data["projectId"]},
                    {
                        "$inc": {
                            "stats.sessionCount": 1,
                            "stats.messageCount": len(messages)
                        }
                    },
                    session=session
                )

                # Commit transaction
                await session.commit_transaction()
                return True

            except Exception as e:
                # Rollback on any error
                await session.abort_transaction()
                logger.error(f"Transaction failed: {e}")
                raise
```

## Performance Optimization Tips

### 1. Indexing for Bulk Operations
```python
# Create indexes before bulk operations
async def ensure_indexes(db: AsyncIOMotorDatabase):
    # Compound index for deduplication
    await db.messages.create_index(
        [("sessionId", 1), ("contentHash", 1)],
        unique=True
    )

    # Index for export queries
    await db.sessions.create_index([
        ("projectId", 1),
        ("startedAt", -1)
    ])

    # Text index for search
    await db.messages.create_index([
        ("message.content", "text")
    ])
```

### 2. Memory-Efficient Streaming
```python
async def stream_large_export(
    db: AsyncIOMotorDatabase,
    batch_size: int = 100
) -> AsyncGenerator:
    """Stream data in batches to avoid memory issues"""

    # Use cursor with batch size
    cursor = db.sessions.find({}).batch_size(batch_size)

    async for document in cursor:
        # Process and yield each document
        processed = await process_document(document)
        yield processed

    # Cursor automatically closed when iteration completes
```

### 3. Parallel Processing
```python
import asyncio
from typing import List

async def parallel_bulk_operations(
    db: AsyncIOMotorDatabase,
    operation_groups: List[List]
) -> List[BulkWriteResult]:
    """Execute multiple bulk operations in parallel"""

    async def execute_bulk(operations):
        return await db.collection.bulk_write(operations, ordered=False)

    # Run operations in parallel
    tasks = [execute_bulk(ops) for ops in operation_groups]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle results
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]

    if failed:
        logger.error(f"{len(failed)} bulk operations failed")

    return successful
```

## Error Handling Patterns

### Handling Bulk Write Errors
```python
from pymongo.errors import BulkWriteError

async def safe_bulk_write(
    db: AsyncIOMotorDatabase,
    operations: list
) -> dict:
    """Execute bulk write with comprehensive error handling"""

    stats = {
        "attempted": len(operations),
        "succeeded": 0,
        "failed": 0,
        "errors": []
    }

    try:
        result = await db.collection.bulk_write(operations, ordered=False)
        stats["succeeded"] = result.inserted_count + result.modified_count

    except BulkWriteError as e:
        # Extract useful information from bulk write error
        write_errors = e.details.get("writeErrors", [])

        for error in write_errors:
            stats["errors"].append({
                "index": error.get("index"),
                "code": error.get("code"),
                "message": error.get("errmsg")
            })

        # Calculate successful operations
        stats["succeeded"] = (
            e.details.get("nInserted", 0) +
            e.details.get("nUpserted", 0) +
            e.details.get("nModified", 0)
        )

        stats["failed"] = stats["attempted"] - stats["succeeded"]

        # Log summary
        logger.warning(
            f"Bulk write partial success: "
            f"{stats['succeeded']}/{stats['attempted']} succeeded"
        )

    return stats
```

## ClaudeLens-Specific Gotchas

1. **Decimal128 for Costs**: Always use `Decimal128` for monetary values
```python
from bson import Decimal128
cost = Decimal128(str(float_value))
```

2. **PyObjectId Type**: Use custom PyObjectId for MongoDB ObjectIds
```python
from app.models.py_object_id import PyObjectId
object_id = PyObjectId(str_id)
```

3. **Content Hash Deduplication**: Messages use SHA-256 hash
```python
import hashlib
content_hash = hashlib.sha256(content.encode()).hexdigest()
```

4. **Batch Size Limit**: MongoDB limits bulk operations to 1000 documents
```python
MONGODB_BATCH_LIMIT = 1000
```

5. **Connection Pooling**: Use motor's built-in connection pooling
```python
client = AsyncIOMotorClient(
    MONGODB_URL,
    maxPoolSize=50,
    minPoolSize=10
)
```

## Testing Bulk Operations

### Unit Test Example
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_bulk_import():
    # Mock database
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.inserted_count = 100
    mock_result.modified_count = 50

    mock_db.messages.bulk_write.return_value = mock_result

    # Test bulk import
    service = ImportService(mock_db)
    stats = await service.bulk_import(test_messages)

    # Assertions
    assert stats.imported == 150
    assert mock_db.messages.bulk_write.called

    # Verify batch size limit
    call_args = mock_db.messages.bulk_write.call_args
    assert len(call_args[0][0]) <= 1000
```

This guide provides MongoDB-specific patterns optimized for ClaudeLens's data model and requirements.
