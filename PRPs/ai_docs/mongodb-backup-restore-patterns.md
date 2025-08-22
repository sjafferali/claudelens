# MongoDB Backup and Restore Implementation Patterns

## MongoDB Data Export/Import with Motor (AsyncIO)

### Streaming Large Collections

When dealing with large MongoDB collections, use cursor-based streaming to avoid memory issues:

```python
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import AsyncGenerator, Dict, Any
import json

async def stream_collection_data(
    db: AsyncIOMotorDatabase,
    collection_name: str,
    batch_size: int = 100
) -> AsyncGenerator[List[Dict[str, Any]], None]:
    """Stream collection data in batches to avoid memory issues."""
    collection = db[collection_name]
    cursor = collection.find({}).batch_size(batch_size)

    batch = []
    async for document in cursor:
        # Convert ObjectId to string for JSON serialization
        document['_id'] = str(document['_id'])
        batch.append(document)

        if len(batch) >= batch_size:
            yield batch
            batch = []

    # Yield remaining documents
    if batch:
        yield batch
```

### Preserving ObjectId References

When backing up related collections, maintain referential integrity:

```python
from bson import ObjectId
from typing import Dict, Set

class ReferenceMapper:
    """Maps old ObjectIds to new ones during restore."""

    def __init__(self):
        self.id_map: Dict[str, str] = {}

    def add_mapping(self, old_id: str, new_id: str):
        """Add ID mapping for reference updates."""
        self.id_map[old_id] = new_id

    def update_references(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Update all ObjectId references in a document."""
        for key, value in document.items():
            if isinstance(value, str) and value in self.id_map:
                document[key] = self.id_map[value]
            elif isinstance(value, dict):
                document[key] = self.update_references(value)
            elif isinstance(value, list):
                document[key] = [
                    self.update_references(item) if isinstance(item, dict) else item
                    for item in value
                ]
        return document
```

### Efficient Bulk Operations

Use bulk write operations for faster restore:

```python
from pymongo import InsertOne, UpdateOne, ReplaceOne
from typing import List, Dict, Any

async def bulk_restore_documents(
    db: AsyncIOMotorDatabase,
    collection_name: str,
    documents: List[Dict[str, Any]],
    mode: str = 'insert'  # 'insert', 'upsert', 'replace'
) -> Dict[str, int]:
    """Restore documents using bulk operations for efficiency."""
    collection = db[collection_name]
    operations = []

    for doc in documents:
        # Convert string ID back to ObjectId
        if '_id' in doc and isinstance(doc['_id'], str):
            doc['_id'] = ObjectId(doc['_id'])

        if mode == 'insert':
            operations.append(InsertOne(doc))
        elif mode == 'upsert':
            operations.append(
                UpdateOne(
                    {'_id': doc['_id']},
                    {'$set': doc},
                    upsert=True
                )
            )
        elif mode == 'replace':
            operations.append(
                ReplaceOne(
                    {'_id': doc['_id']},
                    doc,
                    upsert=True
                )
            )

    if operations:
        result = await collection.bulk_write(operations, ordered=False)
        return {
            'inserted': result.inserted_count,
            'modified': result.modified_count,
            'upserted': len(result.upserted_ids) if result.upserted_ids else 0
        }

    return {'inserted': 0, 'modified': 0, 'upserted': 0}
```

### Transaction Support for Consistency

Use transactions for atomic backup/restore operations:

```python
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any

async def restore_with_transaction(
    client: AsyncIOMotorClient,
    database_name: str,
    restore_data: Dict[str, List[Dict[str, Any]]]
) -> bool:
    """Restore multiple collections in a single transaction."""
    async with await client.start_session() as session:
        async with session.start_transaction():
            try:
                db = client[database_name]

                for collection_name, documents in restore_data.items():
                    collection = db[collection_name]

                    # Clear existing data if doing full restore
                    await collection.delete_many({}, session=session)

                    # Insert new data
                    if documents:
                        await collection.insert_many(documents, session=session)

                # Commit happens automatically when exiting the context
                return True

            except Exception as e:
                # Transaction automatically aborts on exception
                raise Exception(f"Restore failed: {str(e)}")
```

### Index Preservation

Backup and restore indexes along with data:

```python
async def backup_indexes(
    db: AsyncIOMotorDatabase,
    collection_name: str
) -> List[Dict[str, Any]]:
    """Backup collection indexes."""
    collection = db[collection_name]
    indexes = []

    async for index in collection.list_indexes():
        # Skip the default _id index
        if index['name'] != '_id_':
            indexes.append({
                'keys': index['key'],
                'options': {
                    k: v for k, v in index.items()
                    if k not in ['key', 'v', 'ns']
                }
            })

    return indexes

async def restore_indexes(
    db: AsyncIOMotorDatabase,
    collection_name: str,
    indexes: List[Dict[str, Any]]
):
    """Restore collection indexes."""
    collection = db[collection_name]

    for index_spec in indexes:
        keys = list(index_spec['keys'].items())
        options = index_spec.get('options', {})

        try:
            await collection.create_index(keys, **options)
        except Exception as e:
            # Log but don't fail - index might already exist
            print(f"Warning: Could not create index {options.get('name')}: {e}")
```

### Incremental Backup Support

Track changes for incremental backups:

```python
from datetime import datetime
from typing import Optional

async def get_incremental_changes(
    db: AsyncIOMotorDatabase,
    collection_name: str,
    last_backup_time: datetime,
    batch_size: int = 100
) -> AsyncGenerator[List[Dict[str, Any]], None]:
    """Get documents modified since last backup."""
    collection = db[collection_name]

    # Query for documents modified after last backup
    query = {
        '$or': [
            {'updated_at': {'$gt': last_backup_time}},
            {'created_at': {'$gt': last_backup_time}}
        ]
    }

    cursor = collection.find(query).batch_size(batch_size)

    batch = []
    async for document in cursor:
        document['_id'] = str(document['_id'])
        batch.append(document)

        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch
```

### Compression with Zstandard

Use zstandard for optimal compression:

```python
import zstandard as zstd
import json
from typing import AsyncGenerator

async def compress_backup_stream(
    data_generator: AsyncGenerator[List[Dict], None],
    compression_level: int = 3
) -> AsyncGenerator[bytes, None]:
    """Compress backup data stream using zstandard."""
    cctx = zstd.ZstdCompressor(level=compression_level)

    # Start compression stream
    compressor = cctx.stream_writer(None)

    async for batch in data_generator:
        # Convert batch to JSON
        json_data = json.dumps(batch, ensure_ascii=False)

        # Compress and yield
        compressed = compressor.compress(json_data.encode('utf-8'))
        if compressed:
            yield compressed

    # Flush remaining data
    final = compressor.flush()
    if final:
        yield final
```

### Validation and Integrity Checks

Ensure backup integrity:

```python
import hashlib
from typing import Dict, Any

class BackupValidator:
    """Validate backup integrity and completeness."""

    def __init__(self):
        self.checksum = hashlib.sha256()
        self.document_count = 0
        self.collections_backed_up = set()

    def update(self, collection_name: str, documents: List[Dict[str, Any]]):
        """Update validation state with new documents."""
        self.collections_backed_up.add(collection_name)
        self.document_count += len(documents)

        # Update checksum
        for doc in documents:
            doc_str = json.dumps(doc, sort_keys=True)
            self.checksum.update(doc_str.encode('utf-8'))

    def get_metadata(self) -> Dict[str, Any]:
        """Get backup metadata for validation."""
        return {
            'checksum': self.checksum.hexdigest(),
            'document_count': self.document_count,
            'collections': list(self.collections_backed_up),
            'timestamp': datetime.utcnow().isoformat()
        }
```

## Performance Optimization Tips

1. **Batch Size**: Use 100-500 documents per batch for optimal memory/performance balance
2. **Projection**: Only backup necessary fields if full documents aren't needed
3. **Parallel Processing**: Process multiple collections concurrently using asyncio.gather()
4. **Connection Pooling**: Reuse database connections; don't create new ones per operation
5. **Index Creation**: Defer index creation until after data restore for better performance

## Error Handling Patterns

```python
from enum import Enum
from typing import Optional

class BackupError(Exception):
    """Base exception for backup operations."""
    pass

class RestoreError(Exception):
    """Base exception for restore operations."""
    pass

class BackupStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

async def safe_backup_operation(
    operation_func,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """Wrapper for safe backup operations with error handling."""
    try:
        result = await operation_func(*args, **kwargs)
        return {
            'status': BackupStatus.COMPLETED,
            'result': result,
            'error': None
        }
    except asyncio.CancelledError:
        return {
            'status': BackupStatus.CANCELLED,
            'result': None,
            'error': 'Operation cancelled by user'
        }
    except Exception as e:
        return {
            'status': BackupStatus.FAILED,
            'result': None,
            'error': str(e)
        }
```

## Testing Patterns

```python
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from testcontainers.mongodb import MongoDbContainer

@pytest.fixture
async def test_db():
    """Create test MongoDB instance using testcontainers."""
    with MongoDbContainer("mongo:7.0") as mongo:
        client = AsyncIOMotorClient(mongo.get_connection_url())
        db = client.test_database

        # Setup test data
        await db.test_collection.insert_many([
            {'name': 'test1', 'value': 1},
            {'name': 'test2', 'value': 2}
        ])

        yield db

        # Cleanup
        client.close()

async def test_backup_restore_cycle(test_db):
    """Test complete backup and restore cycle."""
    # Backup
    backup_data = []
    async for batch in stream_collection_data(test_db, 'test_collection'):
        backup_data.extend(batch)

    # Clear collection
    await test_db.test_collection.delete_many({})

    # Restore
    result = await bulk_restore_documents(
        test_db,
        'test_collection',
        backup_data
    )

    # Verify
    count = await test_db.test_collection.count_documents({})
    assert count == len(backup_data)
```

## Security Considerations

1. **Encryption**: Always encrypt backup files at rest
2. **Access Control**: Restrict backup/restore operations to authorized users only
3. **Audit Logging**: Log all backup/restore operations with user details
4. **Secure Storage**: Store backups in secure locations with proper permissions
5. **Data Sanitization**: Remove sensitive data from backups if needed
6. **Transport Security**: Use TLS for network transfers
