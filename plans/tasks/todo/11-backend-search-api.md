# Task 11: Backend Search API Implementation

## Status
**Status:** TODO
**Priority:** High
**Estimated Time:** 3 hours

## Purpose
Implement powerful search functionality across messages, sessions, and projects using MongoDB's full-text search capabilities. This enables users to quickly find conversations based on content, code snippets, or metadata.

## Current State
- Database has text indexes defined
- No search endpoints implemented
- No search service layer

## Target State
- Full-text search across message content
- Code-specific search capabilities
- Search filters by date, project, model
- Search result highlighting
- Search suggestions/autocomplete
- Search history tracking

## Implementation Details

### 1. Search Router

**`backend/app/api/api_v1/endpoints/search.py`:**
```python
"""Search API endpoints."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import CommonDeps
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchFilters,
    SearchSuggestion
)
from app.services.search import SearchService

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db: CommonDeps
) -> SearchResponse:
    """Perform a search across messages.

    Supports full-text search with filtering by project, date range,
    message type, and model. Returns results with relevance scoring
    and optional highlighting.
    """
    service = SearchService(db)

    # Validate request
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    if request.limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100")

    # Perform search
    results = await service.search_messages(
        query=request.query,
        filters=request.filters,
        skip=request.skip,
        limit=request.limit,
        highlight=request.highlight
    )

    return results


@router.get("/suggestions")
async def search_suggestions(
    db: CommonDeps,
    query: str = Query(..., min_length=2, description="Partial search query"),
    limit: int = Query(10, ge=1, le=20)
) -> List[SearchSuggestion]:
    """Get search suggestions based on partial query.

    Returns autocomplete suggestions from recent searches and
    common terms in the database.
    """
    service = SearchService(db)
    suggestions = await service.get_suggestions(query, limit)
    return suggestions


@router.get("/recent")
async def recent_searches(
    db: CommonDeps,
    limit: int = Query(10, ge=1, le=50)
) -> List[Dict[str, Any]]:
    """Get recent search queries.

    Returns the most recent searches performed, useful for
    quick access to common searches.
    """
    service = SearchService(db)
    recent = await service.get_recent_searches(limit)
    return recent


@router.post("/code")
async def search_code(
    request: SearchRequest,
    db: CommonDeps,
    language: Optional[str] = Query(None, description="Programming language filter")
) -> SearchResponse:
    """Search specifically for code snippets.

    Optimized for searching code blocks with language-specific filtering.
    """
    service = SearchService(db)

    # Add code-specific filtering
    if request.filters is None:
        request.filters = SearchFilters()

    request.filters.has_code = True
    if language:
        request.filters.code_language = language

    results = await service.search_code(
        query=request.query,
        filters=request.filters,
        skip=request.skip,
        limit=request.limit
    )

    return results


@router.get("/stats")
async def search_stats(db: CommonDeps) -> Dict[str, Any]:
    """Get search statistics.

    Returns information about search usage, popular queries,
    and search performance metrics.
    """
    service = SearchService(db)
    stats = await service.get_search_stats()
    return stats
```

### 2. Search Schemas

**`backend/app/schemas/search.py`:**
```python
"""Search schemas."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    """Search filter options."""
    project_ids: Optional[List[str]] = Field(None, description="Filter by project IDs")
    session_ids: Optional[List[str]] = Field(None, description="Filter by session IDs")
    message_types: Optional[List[str]] = Field(None, description="Filter by message types")
    models: Optional[List[str]] = Field(None, description="Filter by AI models")
    start_date: Optional[datetime] = Field(None, description="Messages after this date")
    end_date: Optional[datetime] = Field(None, description="Messages before this date")
    has_code: Optional[bool] = Field(None, description="Only messages with code blocks")
    code_language: Optional[str] = Field(None, description="Code language filter")
    min_cost: Optional[float] = Field(None, description="Minimum message cost")
    max_cost: Optional[float] = Field(None, description="Maximum message cost")


class SearchRequest(BaseModel):
    """Search request parameters."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    filters: Optional[SearchFilters] = Field(None, description="Search filters")
    skip: int = Field(0, ge=0, description="Number of results to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of results to return")
    highlight: bool = Field(True, description="Include highlighted snippets")


class SearchHighlight(BaseModel):
    """Search result highlight."""
    field: str = Field(..., description="Field containing the match")
    snippet: str = Field(..., description="Text snippet with match")
    score: float = Field(..., description="Relevance score")


class SearchResult(BaseModel):
    """Individual search result."""
    message_id: str = Field(..., description="Message ID")
    session_id: str = Field(..., description="Session ID")
    project_id: str = Field(..., description="Project ID")
    project_name: str = Field(..., description="Project name")

    message_type: str = Field(..., description="Message type")
    timestamp: datetime = Field(..., description="Message timestamp")

    content_preview: str = Field(..., description="Content preview")
    highlights: List[SearchHighlight] = Field(default_factory=list)

    score: float = Field(..., description="Search relevance score")

    # Optional enriched data
    session_summary: Optional[str] = None
    model: Optional[str] = None
    cost_usd: Optional[float] = None


class SearchResponse(BaseModel):
    """Search response with results and metadata."""
    query: str = Field(..., description="Original search query")
    total: int = Field(..., description="Total number of matching results")
    skip: int = Field(..., description="Number of results skipped")
    limit: int = Field(..., description="Maximum results returned")

    results: List[SearchResult] = Field(..., description="Search results")

    took_ms: int = Field(..., description="Search duration in milliseconds")
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class SearchSuggestion(BaseModel):
    """Search autocomplete suggestion."""
    text: str = Field(..., description="Suggestion text")
    type: str = Field(..., description="Suggestion type (query, project, model)")
    count: Optional[int] = Field(None, description="Number of occurrences")
```

### 3. Search Service Implementation

**`backend/app/services/search.py`:**
```python
"""Search service implementation."""
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging

from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchFilters,
    SearchHighlight,
    SearchSuggestion
)

logger = logging.getLogger(__name__)


class SearchService:
    """Service for search operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def search_messages(
        self,
        query: str,
        filters: Optional[SearchFilters],
        skip: int,
        limit: int,
        highlight: bool = True
    ) -> SearchResponse:
        """Search messages with full-text search."""
        start_time = datetime.utcnow()

        # Build search pipeline
        pipeline = self._build_search_pipeline(query, filters, skip, limit)

        # Execute search
        cursor = self.db.messages.aggregate(pipeline)
        results = await cursor.to_list(limit)

        # Get total count
        count_pipeline = self._build_count_pipeline(query, filters)
        count_result = await self.db.messages.aggregate(count_pipeline).to_list(1)
        total = count_result[0]["total"] if count_result else 0

        # Process results
        search_results = []
        for doc in results:
            result = await self._process_search_result(doc, query, highlight)
            search_results.append(result)

        # Calculate duration
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Log search
        await self._log_search(query, filters, total, duration_ms)

        return SearchResponse(
            query=query,
            total=total,
            skip=skip,
            limit=limit,
            results=search_results,
            took_ms=duration_ms,
            filters_applied=filters.dict(exclude_none=True) if filters else {}
        )

    async def search_code(
        self,
        query: str,
        filters: Optional[SearchFilters],
        skip: int,
        limit: int
    ) -> SearchResponse:
        """Search specifically for code blocks."""
        # Enhance query for code search
        code_query = self._enhance_code_query(query)

        # Add code-specific stages to pipeline
        return await self.search_messages(
            query=code_query,
            filters=filters,
            skip=skip,
            limit=limit,
            highlight=True
        )

    def _build_search_pipeline(
        self,
        query: str,
        filters: Optional[SearchFilters],
        skip: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Build MongoDB aggregation pipeline for search."""
        pipeline = []

        # Text search stage
        pipeline.append({
            "$match": {
                "$text": {"$search": query}
            }
        })

        # Add filters
        if filters:
            filter_stage = self._build_filter_stage(filters)
            if filter_stage:
                pipeline.append({"$match": filter_stage})

        # Add text score
        pipeline.append({
            "$addFields": {
                "score": {"$meta": "textScore"}
            }
        })

        # Sort by relevance
        pipeline.append({
            "$sort": {"score": -1, "timestamp": -1}
        })

        # Join with sessions and projects
        pipeline.extend([
            {
                "$lookup": {
                    "from": "sessions",
                    "localField": "sessionId",
                    "foreignField": "sessionId",
                    "as": "session"
                }
            },
            {
                "$unwind": {
                    "path": "$session",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$lookup": {
                    "from": "projects",
                    "localField": "session.projectId",
                    "foreignField": "_id",
                    "as": "project"
                }
            },
            {
                "$unwind": {
                    "path": "$project",
                    "preserveNullAndEmptyArrays": True
                }
            }
        ])

        # Pagination
        pipeline.append({"$skip": skip})
        pipeline.append({"$limit": limit})

        return pipeline

    def _build_count_pipeline(
        self,
        query: str,
        filters: Optional[SearchFilters]
    ) -> List[Dict[str, Any]]:
        """Build pipeline for counting total results."""
        pipeline = []

        # Text search
        pipeline.append({
            "$match": {
                "$text": {"$search": query}
            }
        })

        # Add filters
        if filters:
            filter_stage = self._build_filter_stage(filters)
            if filter_stage:
                pipeline.append({"$match": filter_stage})

        # Count
        pipeline.append({
            "$count": "total"
        })

        return pipeline

    def _build_filter_stage(self, filters: SearchFilters) -> Dict[str, Any]:
        """Build filter stage from search filters."""
        conditions = {}

        if filters.project_ids:
            # Need to join with sessions first
            conditions["session.projectId"] = {
                "$in": [ObjectId(pid) for pid in filters.project_ids]
            }

        if filters.session_ids:
            conditions["sessionId"] = {"$in": filters.session_ids}

        if filters.message_types:
            conditions["type"] = {"$in": filters.message_types}

        if filters.models:
            conditions["model"] = {"$in": filters.models}

        if filters.start_date:
            conditions["timestamp"] = {"$gte": filters.start_date}

        if filters.end_date:
            if "timestamp" in conditions:
                conditions["timestamp"]["$lte"] = filters.end_date
            else:
                conditions["timestamp"] = {"$lte": filters.end_date}

        if filters.has_code:
            conditions["$or"] = [
                {"message.content": {"$regex": r"```", "$options": "i"}},
                {"toolUseResult": {"$regex": r"```", "$options": "i"}}
            ]

        if filters.min_cost is not None:
            conditions["costUsd"] = {"$gte": filters.min_cost}

        if filters.max_cost is not None:
            if "costUsd" in conditions:
                conditions["costUsd"]["$lte"] = filters.max_cost
            else:
                conditions["costUsd"] = {"$lte": filters.max_cost}

        return conditions

    async def _process_search_result(
        self,
        doc: Dict[str, Any],
        query: str,
        highlight: bool
    ) -> SearchResult:
        """Process a search result document."""
        # Extract content
        content = ""
        if doc.get("message") and isinstance(doc["message"], dict):
            content = doc["message"].get("content", "")
        elif doc.get("message"):
            content = str(doc["message"])

        # Create preview
        preview = self._create_preview(content, query, max_length=200)

        # Create highlights
        highlights = []
        if highlight:
            highlights = self._create_highlights(doc, query)

        return SearchResult(
            message_id=str(doc["_id"]),
            session_id=doc["sessionId"],
            project_id=str(doc.get("project", {}).get("_id", "")),
            project_name=doc.get("project", {}).get("name", "Unknown"),
            message_type=doc["type"],
            timestamp=doc["timestamp"],
            content_preview=preview,
            highlights=highlights,
            score=doc.get("score", 0),
            session_summary=doc.get("session", {}).get("summary"),
            model=doc.get("model"),
            cost_usd=doc.get("costUsd")
        )

    def _create_preview(
        self,
        content: str,
        query: str,
        max_length: int = 200
    ) -> str:
        """Create a content preview with query context."""
        if not content:
            return ""

        # Find query in content (case-insensitive)
        query_lower = query.lower()
        content_lower = content.lower()

        pos = content_lower.find(query_lower)
        if pos == -1:
            # Query not found, return beginning
            return content[:max_length] + "..." if len(content) > max_length else content

        # Center preview around query
        start = max(0, pos - max_length // 2)
        end = min(len(content), pos + len(query) + max_length // 2)

        preview = content[start:end]

        # Add ellipsis
        if start > 0:
            preview = "..." + preview
        if end < len(content):
            preview = preview + "..."

        return preview

    def _create_highlights(
        self,
        doc: Dict[str, Any],
        query: str
    ) -> List[SearchHighlight]:
        """Create search highlights."""
        highlights = []

        # Check message content
        if doc.get("message") and isinstance(doc["message"], dict):
            content = doc["message"].get("content", "")
            if content and query.lower() in content.lower():
                snippet = self._create_preview(content, query, max_length=150)
                highlights.append(SearchHighlight(
                    field="message.content",
                    snippet=snippet,
                    score=1.0
                ))

        # Check tool results
        if doc.get("toolUseResult"):
            tool_result = str(doc["toolUseResult"])
            if query.lower() in tool_result.lower():
                snippet = self._create_preview(tool_result, query, max_length=150)
                highlights.append(SearchHighlight(
                    field="toolUseResult",
                    snippet=snippet,
                    score=0.8
                ))

        return highlights

    def _enhance_code_query(self, query: str) -> str:
        """Enhance query for code search."""
        # Add common code-related terms
        code_terms = ["function", "class", "def", "import", "return"]

        # Check if query already contains code terms
        query_lower = query.lower()
        has_code_term = any(term in query_lower for term in code_terms)

        if not has_code_term:
            # Add code context
            return f"{query} code function"

        return query

    async def get_suggestions(
        self,
        partial_query: str,
        limit: int
    ) -> List[SearchSuggestion]:
        """Get search suggestions."""
        suggestions = []

        # Get from recent searches
        recent_searches = await self.db.search_logs.find(
            {"query": {"$regex": f"^{re.escape(partial_query)}", "$options": "i"}},
            {"query": 1, "count": 1}
        ).sort("count", -1).limit(limit // 2).to_list(limit // 2)

        for search in recent_searches:
            suggestions.append(SearchSuggestion(
                text=search["query"],
                type="query",
                count=search.get("count", 1)
            ))

        # Get project names
        project_names = await self.db.projects.find(
            {"name": {"$regex": f"^{re.escape(partial_query)}", "$options": "i"}},
            {"name": 1}
        ).limit(limit // 4).to_list(limit // 4)

        for project in project_names:
            suggestions.append(SearchSuggestion(
                text=project["name"],
                type="project"
            ))

        # Get models
        models = await self.db.messages.distinct("model")
        for model in models:
            if model and partial_query.lower() in model.lower():
                suggestions.append(SearchSuggestion(
                    text=model,
                    type="model"
                ))

        return suggestions[:limit]

    async def get_recent_searches(self, limit: int) -> List[Dict[str, Any]]:
        """Get recent search queries."""
        recent = await self.db.search_logs.find(
            {},
            {"query": 1, "timestamp": 1, "result_count": 1}
        ).sort("timestamp", -1).limit(limit).to_list(limit)

        return [
            {
                "query": r["query"],
                "timestamp": r["timestamp"],
                "result_count": r.get("result_count", 0)
            }
            for r in recent
        ]

    async def get_search_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        # Total searches
        total_searches = await self.db.search_logs.count_documents({})

        # Popular queries
        popular_pipeline = [
            {"$group": {
                "_id": "$query",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]

        popular_queries = await self.db.search_logs.aggregate(
            popular_pipeline
        ).to_list(10)

        # Average search time
        avg_time_pipeline = [
            {"$group": {
                "_id": None,
                "avg_duration": {"$avg": "$duration_ms"}
            }}
        ]

        avg_time_result = await self.db.search_logs.aggregate(
            avg_time_pipeline
        ).to_list(1)

        avg_duration = avg_time_result[0]["avg_duration"] if avg_time_result else 0

        return {
            "total_searches": total_searches,
            "popular_queries": [
                {"query": q["_id"], "count": q["count"]}
                for q in popular_queries
            ],
            "average_duration_ms": round(avg_duration, 2)
        }

    async def _log_search(
        self,
        query: str,
        filters: Optional[SearchFilters],
        result_count: int,
        duration_ms: int
    ):
        """Log search for analytics."""
        log_entry = {
            "query": query,
            "filters": filters.dict(exclude_none=True) if filters else {},
            "result_count": result_count,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow()
        }

        await self.db.search_logs.insert_one(log_entry)

        # Update search count
        await self.db.search_logs.update_one(
            {"query": query},
            {"$inc": {"count": 1}},
            upsert=True
        )
```

## Required Technologies
- MongoDB full-text search
- Text indexes on message content
- Aggregation pipelines
- Regular expressions for highlighting

## Success Criteria
- [ ] Full-text search working across messages
- [ ] Search filters apply correctly
- [ ] Results sorted by relevance
- [ ] Search highlighting implemented
- [ ] Code search optimized
- [ ] Autocomplete suggestions working
- [ ] Search performance < 200ms
- [ ] Search history tracked
- [ ] API documentation complete

## Notes
- Use MongoDB text indexes for performance
- Consider Elasticsearch for advanced features
- Implement search result caching
- Monitor search performance metrics
- Add search analytics for insights
