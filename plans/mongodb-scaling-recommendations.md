# MongoDB Scaling Recommendations for ClaudeLens

## Executive Summary
Based on analysis of your current architecture, your app is well-suited for MongoDB Time-Series Collections with rolling partitions. Your message data is inherently time-based with timestamps, and your query patterns primarily filter by recent dates. This document outlines a scalable architecture to support billions of messages.

## Current State Analysis

### Data Model
- **Messages**: Time-series data with timestamps, UUIDs, session references
- **Sessions**: Aggregated conversation data with costs and message counts
- **Projects**: Organizational containers for sessions

### Query Patterns (from codebase analysis)
1. **Time-based queries**: Most analytics filter by date ranges (last 24h, 7d, 30d, etc.)
2. **Session-based access**: Messages frequently queried by sessionId
3. **Text search**: Full-text search across message content
4. **Analytics aggregations**: Complex pipelines for cost, usage, and activity metrics

### Current Indexes
You have good index coverage for current scale, including:
- Compound indexes on (sessionId, timestamp)
- Time-based indexes on createdAt, timestamp
- Text indexes for search functionality

## Recommended Architecture for Billions of Documents

### 1. MongoDB Time-Series Collections (Primary Recommendation)

Convert your messages collection to a Time-Series collection:

```javascript
db.createCollection("messages_timeseries", {
  timeseries: {
    timeField: "timestamp",
    metaField: "metadata",
    granularity: "minutes"  // Based on your message frequency
  },
  expireAfterSeconds: 31536000  // Optional: 1 year TTL
})

// Metadata structure
{
  sessionId: "...",
  userId: ObjectId("..."),
  projectId: ObjectId("..."),
  type: "user|assistant",
  model: "claude-3-5-sonnet",
  gitBranch: "main"
}
```

**Benefits:**
- Automatic bucketing reduces document count by ~10-100x
- Optimized storage compression (typically 50-80% reduction)
- Better query performance for time-range queries
- Built-in data expiration support

### 2. Rolling Collections Pattern with Date Partitioning

Implement a rolling collections strategy for manual control:

```python
# Collection naming pattern
messages_2025_01  # January 2025
messages_2025_02  # February 2025
messages_current  # Always writes here

# Implementation approach
class PartitionedMessageRepository:
    def get_collection_for_date(self, date: datetime):
        """Get the appropriate collection for a date."""
        if date >= datetime.now() - timedelta(days=30):
            return self.db.messages_current

        collection_name = f"messages_{date.strftime('%Y_%m')}"
        return self.db[collection_name]

    async def search_messages(self, start_date, end_date, query):
        """Search across multiple partitioned collections."""
        collections = self.get_collections_for_range(start_date, end_date)

        # Union query across collections
        results = []
        for collection in collections:
            partial_results = await collection.find(query).to_list()
            results.extend(partial_results)

        return sorted(results, key=lambda x: x['timestamp'])
```

**Monthly rotation script:**
```python
async def rotate_collections():
    """Run monthly to rotate collections."""
    db = await get_database()

    # Rename current to this month's archive
    current_month = datetime.now().strftime('%Y_%m')
    await db.messages_current.rename(f"messages_{current_month}")

    # Create new current collection with indexes
    await create_message_collection_with_indexes(db, "messages_current")

    # Optional: Archive old collections to S3/cold storage
    six_months_ago = datetime.now() - timedelta(days=180)
    archive_pattern = six_months_ago.strftime('%Y_%m')
    await archive_to_s3(f"messages_{archive_pattern}")
```

### 3. Sharding Strategy (For Horizontal Scaling)

When you exceed single-server capacity (~10-50 billion documents):

```javascript
// Enable sharding on database
sh.enableSharding("claudelens")

// For time-series collections (MongoDB 8.0+)
sh.shardCollection(
  "claudelens.messages_timeseries",
  {
    "metadata.sessionId": "hashed"  // NOT timeField (deprecated)
  }
)

// For regular collections
sh.shardCollection(
  "claudelens.messages",
  {
    "sessionId": "hashed",  // Primary shard key
    "timestamp": 1          // Secondary for range queries
  }
)
```

**Shard Key Recommendations:**
- **DO NOT** use timestamp alone (creates hotspots)
- **DO** use sessionId (hashed) for even distribution
- **Consider** compound keys for complex query patterns

### 4. Hybrid Architecture (Best of Both Worlds)

Combine approaches for maximum flexibility:

```python
# Hot/Warm/Cold tier architecture
HOT_TIER = "messages_current"        # Last 7 days (SSD, all indexes)
WARM_TIER = "messages_timeseries"    # 7-90 days (Time-series, compressed)
COLD_TIER = "messages_archive_*"     # 90+ days (Minimal indexes)

class TieredMessageService:
    async def write_message(self, message):
        """Always write to hot tier."""
        await self.db[HOT_TIER].insert_one(message)

    async def migrate_to_warm(self):
        """Daily job to move 7+ day old messages."""
        cutoff = datetime.now() - timedelta(days=7)

        # Bulk move to time-series collection
        messages = await self.db[HOT_TIER].find(
            {"timestamp": {"$lt": cutoff}}
        ).to_list()

        if messages:
            await self.db[WARM_TIER].insert_many(messages)
            await self.db[HOT_TIER].delete_many(
                {"timestamp": {"$lt": cutoff}}
            )

    async def archive_to_cold(self):
        """Monthly job for 90+ day old data."""
        # Move to date-partitioned collections with minimal indexes
        pass
```

## Implementation Roadmap

### Phase 1: Immediate Optimizations (Week 1)
1. Add missing compound indexes for common query patterns
2. Implement query result caching for analytics
3. Add connection pooling optimization

### Phase 2: Time-Series Migration (Week 2-3)
1. Create parallel time-series collection
2. Dual-write to both collections
3. Migrate historical data in batches
4. Validate query compatibility
5. Cutover to time-series as primary

### Phase 3: Partitioning Implementation (Week 4-5)
1. Implement collection rotation logic
2. Update repositories to handle multiple collections
3. Create migration scripts
4. Test with production-like data volumes

### Phase 4: Sharding Preparation (Future)
1. Deploy MongoDB replica sets
2. Set up config servers and mongos routers
3. Choose and test shard keys
4. Pre-split chunks for initial distribution

## Query Pattern Optimizations

### 1. Aggregation Pipeline Optimization
```python
# Current approach (scans all documents)
pipeline = [
    {"$match": {"timestamp": {"$gte": start_date}}},
    {"$group": {...}}
]

# Optimized with partitioning
async def optimized_analytics(start_date, end_date):
    # Only query relevant partitions
    collections = get_collections_for_range(start_date, end_date)

    # Parallel aggregation
    tasks = [
        collection.aggregate(pipeline).to_list()
        for collection in collections
    ]
    results = await asyncio.gather(*tasks)

    # Merge results
    return merge_aggregation_results(results)
```

### 2. Search Optimization
```python
# Implement search result materialization
class SearchIndexService:
    async def build_search_index(self):
        """Pre-compute searchable content."""
        # Create dedicated search collection with denormalized data
        await self.db.message_search.create_index([
            ("content", "text"),
            ("sessionId", 1),
            ("timestamp", -1)
        ])
```

## Monitoring and Maintenance

### Key Metrics to Track
- Collection sizes and document counts
- Query response times by pattern
- Index usage statistics
- Storage growth rate

### Maintenance Jobs
```python
# Weekly: Analyze index usage
async def analyze_indexes():
    stats = await db.messages.index_stats()
    unused = [idx for idx in stats if idx['accesses']['ops'] < 100]
    logger.warning(f"Unused indexes: {unused}")

# Monthly: Compact collections
async def compact_collections():
    for collection_name in get_all_message_collections():
        await db.command('compact', collection_name)
```

## Cost-Benefit Analysis

### Current Approach
- **Pros**: Simple, no migration needed
- **Cons**: Will hit limits at ~500M-1B documents

### Time-Series Collections
- **Pros**:
  - 50-80% storage reduction
  - 10-100x fewer documents to index
  - Built-in TTL support
- **Cons**:
  - Requires migration
  - Some query pattern changes

### Rolling Collections
- **Pros**:
  - Complete control over data lifecycle
  - Easy archival/deletion
  - Can optimize indexes per time period
- **Cons**:
  - More complex query logic
  - Manual management overhead

### Recommendation
**Start with Time-Series Collections** for immediate benefits, then add **Rolling Collections** pattern when you exceed 1B documents or need more control over data lifecycle.

## Conclusion

Your application is well-positioned for scaling with its time-based data model. The combination of MongoDB Time-Series Collections and a rolling partition strategy will handle billions of messages efficiently while maintaining query performance.

Priority actions:
1. Test Time-Series Collections with your data
2. Implement collection partitioning logic
3. Plan sharding strategy for future horizontal scaling
