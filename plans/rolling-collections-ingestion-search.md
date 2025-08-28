# Rolling Collections: Ingestion & Progressive Search Implementation

## 1. CLI Ingestion Integration

### Update IngestService for Rolling Collections

```python
# backend/app/services/ingest.py

from app.services.rolling_message_service import RollingMessageService

class IngestService:
    """Service for ingesting Claude messages into rolling collections."""

    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id
        self.rolling_service = RollingMessageService(db)
        self._project_cache: dict[str, ObjectId] = {}
        self._session_cache: dict[str, ObjectId] = {}

    async def _store_message(
        self,
        message_doc: dict[str, Any],
        overwrite_mode: bool = False
    ) -> tuple[bool, bool]:
        """Store a single message using rolling collections."""

        # Parse timestamp for collection routing
        timestamp = message_doc.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            message_doc['timestamp'] = timestamp

        # Check if message exists (across all collections)
        uuid = message_doc['uuid']
        existing = await self._find_existing_message(uuid)

        if existing and not overwrite_mode:
            return False, False  # Skipped

        if existing and overwrite_mode:
            # Update in the appropriate collection
            collection_name = self.rolling_service.get_collection_name(timestamp)
            collection = await self.rolling_service.ensure_collection_with_indexes(collection_name)

            await collection.replace_one(
                {"uuid": uuid},
                message_doc,
                upsert=True
            )
            return True, True  # Processed, Updated

        # Insert new message
        await self.rolling_service.insert_message(message_doc)
        return True, False  # Processed, Not updated

    async def _find_existing_message(self, uuid: str) -> Optional[dict]:
        """Find message by UUID across all collections."""
        collections = await self.db.list_collection_names()
        message_collections = [c for c in collections if c.startswith('messages_')]

        for coll_name in message_collections:
            doc = await self.db[coll_name].find_one({"uuid": uuid})
            if doc:
                return doc
        return None
```

### CLI Message Flow

```yaml
# How messages flow from CLI to rolling collections

1. CLI collects messages:
   claude-cli export --format json > messages.json

2. CLI sends batch to API:
   POST /api/v1/ingest/batch
   {
     "messages": [...],
     "overwrite_mode": false
   }

3. IngestService routes by timestamp:
   - January 2024 message → messages_2024_01
   - December 2023 message → messages_2023_12
   - Current message → messages_2025_01

4. Collections auto-created as needed:
   - First message for a month creates collection
   - Indexes created automatically
   - No manual setup required
```

## 2. Progressive Search Implementation

### Backend: Streaming Search Service

```python
# backend/app/services/progressive_search.py

from typing import AsyncIterator
import asyncio
from datetime import datetime, timedelta

class ProgressiveSearchService:
    """Service for progressive, streaming search across rolling collections."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.rolling_service = RollingMessageService(db)

    async def progressive_search(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit_per_collection: int = 20
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Progressively search collections from newest to oldest.
        Yields results as they're found.
        """
        # Default to searching from now backwards
        if not end_date:
            end_date = datetime.now(UTC)
        if not start_date:
            start_date = end_date - timedelta(days=365)  # 1 year default

        # Get collections in reverse chronological order
        all_collections = await self._get_collections_for_range(start_date, end_date)
        all_collections.reverse()  # Start with newest

        # Build search query
        search_query = self._build_search_query(query, filters)

        # Search each collection and yield results
        for collection_name in all_collections:
            # Yield progress update
            month_year = self._extract_month_year(collection_name)
            yield {
                "type": "progress",
                "collection": collection_name,
                "status": f"Searching {month_year}...",
                "timestamp": datetime.now(UTC).isoformat()
            }

            # Search this collection
            collection = self.db[collection_name]
            try:
                cursor = collection.find(search_query).sort(
                    "timestamp", -1
                ).limit(limit_per_collection)

                results = await cursor.to_list(limit_per_collection)

                for doc in results:
                    # Convert ObjectId to string
                    doc['_id'] = str(doc['_id'])

                    # Yield each result
                    yield {
                        "type": "result",
                        "collection": collection_name,
                        "data": doc,
                        "timestamp": datetime.now(UTC).isoformat()
                    }

                # Yield collection complete
                yield {
                    "type": "collection_complete",
                    "collection": collection_name,
                    "count": len(results),
                    "timestamp": datetime.now(UTC).isoformat()
                }

            except Exception as e:
                # Yield error but continue
                yield {
                    "type": "error",
                    "collection": collection_name,
                    "error": str(e),
                    "timestamp": datetime.now(UTC).isoformat()
                }

            # Small delay to allow client processing
            await asyncio.sleep(0.1)

        # Yield search complete
        yield {
            "type": "complete",
            "collections_searched": len(all_collections),
            "timestamp": datetime.now(UTC).isoformat()
        }

    def _build_search_query(self, query: str, filters: Dict = None) -> Dict:
        """Build MongoDB search query."""
        search_query = {
            "$or": [
                {"message.content": {"$regex": query, "$options": "i"}},
                {"content": {"$regex": query, "$options": "i"}},
                {"summary": {"$regex": query, "$options": "i"}}
            ]
        }

        if filters:
            if "sessionId" in filters:
                search_query["sessionId"] = filters["sessionId"]
            if "type" in filters:
                search_query["type"] = filters["type"]
            if "model" in filters:
                search_query["model"] = filters["model"]

        return search_query

    def _extract_month_year(self, collection_name: str) -> str:
        """Extract readable month/year from collection name."""
        # messages_2024_01 -> "January 2024"
        try:
            parts = collection_name.split('_')
            year = parts[1]
            month = int(parts[2])
            month_names = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            return f"{month_names[month-1]} {year}"
        except:
            return collection_name

    async def _get_collections_for_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[str]:
        """Get collections for date range."""
        collections = set()
        current = start_date.replace(day=1)

        while current <= end_date:
            collections.add(f"messages_{current.strftime('%Y_%m')}")
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        # Only return existing collections
        existing = await self.db.list_collection_names()
        return sorted([c for c in collections if c in existing])
```

### API: WebSocket Endpoint for Streaming

```python
# backend/app/api/api_v1/endpoints/search_stream.py

from fastapi import WebSocket, WebSocketDisconnect, Query
from app.services.progressive_search import ProgressiveSearchService

router = APIRouter()

@router.websocket("/search/stream")
async def stream_search(
    websocket: WebSocket,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """WebSocket endpoint for progressive search with real-time updates."""
    await websocket.accept()

    try:
        # Wait for search request
        data = await websocket.receive_json()

        query = data.get("query")
        filters = data.get("filters", {})
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if not query:
            await websocket.send_json({
                "type": "error",
                "message": "Query is required"
            })
            return

        # Create search service
        search_service = ProgressiveSearchService(db)

        # Stream results
        async for result in search_service.progressive_search(
            query, filters, start_date, end_date
        ):
            await websocket.send_json(result)

            # Check for client disconnect or stop signal
            try:
                # Non-blocking receive with timeout
                client_msg = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=0.01
                )
                if client_msg.get("action") == "stop":
                    await websocket.send_json({
                        "type": "stopped",
                        "message": "Search stopped by user"
                    })
                    break
            except asyncio.TimeoutError:
                pass  # No message, continue

    except WebSocketDisconnect:
        logger.info("Client disconnected from search stream")
    except Exception as e:
        logger.error(f"Error in search stream: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()
```

### Alternative: Server-Sent Events (SSE)

```python
# backend/app/api/api_v1/endpoints/search_sse.py

from fastapi import Request
from sse_starlette.sse import EventSourceResponse

@router.get("/search/progressive")
async def progressive_search_sse(
    request: Request,
    query: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    filters: Optional[str] = None,  # JSON string
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """SSE endpoint for progressive search."""

    async def generate():
        search_service = ProgressiveSearchService(db)

        # Parse filters
        parsed_filters = json.loads(filters) if filters else {}

        async for result in search_service.progressive_search(
            query, parsed_filters, start_date, end_date
        ):
            # Check if client disconnected
            if await request.is_disconnected():
                break

            # Send as SSE event
            yield {
                "event": result["type"],
                "data": json.dumps(result)
            }

    return EventSourceResponse(generate())
```

## 3. Frontend Implementation

### React Component for Progressive Search

```typescript
// frontend/components/ProgressiveSearch.tsx

import { useState, useEffect, useRef } from 'react';

interface SearchResult {
  id: string;
  sessionId: string;
  content: string;
  timestamp: string;
  collection: string;
}

interface SearchProgress {
  collection: string;
  status: string;
}

export function ProgressiveSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [progress, setProgress] = useState<SearchProgress | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [collectionsSearched, setCollectionsSearched] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const startSearch = () => {
    if (!query) return;

    // Clear previous results
    setResults([]);
    setCollectionsSearched([]);
    setIsSearching(true);

    // Connect to WebSocket
    const ws = new WebSocket('ws://localhost:8000/api/v1/search/stream');
    wsRef.current = ws;

    ws.onopen = () => {
      // Send search query
      ws.send(JSON.stringify({
        query,
        filters: {},
        start_date: null,  // Search all history
        end_date: null
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'progress':
          setProgress({
            collection: data.collection,
            status: data.status
          });
          break;

        case 'result':
          setResults(prev => [...prev, {
            id: data.data._id,
            sessionId: data.data.sessionId,
            content: data.data.message?.content || data.data.content,
            timestamp: data.data.timestamp,
            collection: data.collection
          }]);
          break;

        case 'collection_complete':
          setCollectionsSearched(prev => [...prev, data.collection]);
          setProgress(null);
          break;

        case 'complete':
          setIsSearching(false);
          setProgress(null);
          break;

        case 'error':
          console.error('Search error:', data.error);
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsSearching(false);
    };

    ws.onclose = () => {
      setIsSearching(false);
      setProgress(null);
    };
  };

  const stopSearch = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'stop' }));
      wsRef.current.close();
    }
    setIsSearching(false);
    setProgress(null);
  };

  const navigateToResult = (result: SearchResult) => {
    // Navigate to the message
    window.location.href = `/sessions/${result.sessionId}#${result.id}`;
  };

  return (
    <div className="progressive-search">
      {/* Search Input */}
      <div className="search-bar">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !isSearching && startSearch()}
          placeholder="Search messages..."
          disabled={isSearching}
        />

        {!isSearching ? (
          <button onClick={startSearch} disabled={!query}>
            Search
          </button>
        ) : (
          <button onClick={stopSearch} className="stop-button">
            Stop Search
          </button>
        )}
      </div>

      {/* Progress Indicator */}
      {progress && (
        <div className="search-progress">
          <div className="spinner" />
          <span>{progress.status}</span>
        </div>
      )}

      {/* Collections Searched */}
      {collectionsSearched.length > 0 && (
        <div className="collections-searched">
          <small>
            Searched: {collectionsSearched.map(c =>
              c.replace('messages_', '').replace('_', '/')
            ).join(', ')}
          </small>
        </div>
      )}

      {/* Results */}
      <div className="search-results">
        {results.map((result) => (
          <div
            key={result.id}
            className="search-result"
            onClick={() => navigateToResult(result)}
          >
            <div className="result-header">
              <span className="session-id">{result.sessionId}</span>
              <span className="timestamp">
                {new Date(result.timestamp).toLocaleDateString()}
              </span>
            </div>
            <div className="result-content">
              {result.content.substring(0, 200)}...
            </div>
            <div className="result-collection">
              From: {result.collection.replace('messages_', '').replace('_', '/')}
            </div>
          </div>
        ))}
      </div>

      {/* Results Count */}
      {!isSearching && results.length > 0 && (
        <div className="results-summary">
          Found {results.length} results across {collectionsSearched.length} months
        </div>
      )}
    </div>
  );
}
```

### CSS for Progressive Search UI

```css
/* frontend/styles/progressive-search.css */

.progressive-search {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-bar input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
}

.search-bar button {
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.stop-button {
  background-color: #dc3545;
  color: white;
}

.search-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px;
  background: linear-gradient(90deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 8px;
  margin-bottom: 15px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid #0ea5e9;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.collections-searched {
  margin-bottom: 10px;
  color: #6b7280;
  font-size: 14px;
}

.search-results {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-result {
  padding: 15px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.search-result:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.result-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #6b7280;
}

.result-content {
  color: #1f2937;
  line-height: 1.5;
  margin-bottom: 8px;
}

.result-collection {
  font-size: 12px;
  color: #9ca3af;
}

.results-summary {
  margin-top: 20px;
  padding: 10px;
  background: #f9fafb;
  border-radius: 8px;
  text-align: center;
  color: #4b5563;
}
```

## 4. Benefits of This Implementation

### For Ingestion
✅ **Automatic Routing** - Messages go to correct monthly collection based on timestamp
✅ **No Manual Setup** - Collections created on-demand
✅ **Handles Historical Data** - Can ingest messages from any time period
✅ **Efficient Updates** - Only searches relevant collections for duplicates

### For Progressive Search
✅ **User Control** - Can stop search anytime when result is found
✅ **Real-time Feedback** - Shows which month is being searched
✅ **Incremental Results** - Results appear as found, no waiting
✅ **Efficient** - Searches newest data first (most likely what user wants)
✅ **Scalable** - Only searches collections user needs

## 5. Alternative: Paginated Collection Search

```python
# For non-streaming environments, use paginated approach

class PaginatedSearchService:
    """Search collections one at a time with pagination."""

    async def search_next_collection(
        self,
        query: str,
        last_collection: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search the next collection in sequence."""

        # Get all collections
        all_collections = await self._get_all_message_collections()
        all_collections.reverse()  # Newest first

        # Find next collection to search
        if last_collection:
            try:
                idx = all_collections.index(last_collection)
                if idx < len(all_collections) - 1:
                    next_collection = all_collections[idx + 1]
                else:
                    return {"complete": True, "results": []}
            except ValueError:
                next_collection = all_collections[0]
        else:
            next_collection = all_collections[0] if all_collections else None

        if not next_collection:
            return {"complete": True, "results": []}

        # Search this collection
        collection = self.db[next_collection]
        results = await collection.find(
            {"$text": {"$search": query}}
        ).limit(limit).to_list(limit)

        return {
            "complete": False,
            "collection": next_collection,
            "results": results,
            "next_collection": all_collections[all_collections.index(next_collection) + 1]
                if all_collections.index(next_collection) < len(all_collections) - 1
                else None
        }
```

This implementation fully supports your requirements for both ingestion and progressive search with the rolling collections architecture.
