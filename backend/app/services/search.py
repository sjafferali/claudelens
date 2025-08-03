"""Search service implementation."""
import logging
import re
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.search import (
    SearchFilters,
    SearchHighlight,
    SearchResponse,
    SearchResult,
    SearchSuggestion,
)

logger = logging.getLogger(__name__)


class SearchService:
    """Service for search operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def search_messages(
        self,
        query: str,
        filters: SearchFilters | None,
        skip: int,
        limit: int,
        highlight: bool = True,
    ) -> SearchResponse:
        """Search messages with full-text search."""
        start_time = datetime.now(UTC)

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
        duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

        # Log search
        await self._log_search(query, filters, total, duration_ms)

        return SearchResponse(
            query=query,
            total=total,
            skip=skip,
            limit=limit,
            results=search_results,
            took_ms=duration_ms,
            filters_applied=filters.dict(exclude_none=True) if filters else {},
        )

    async def search_code(
        self, query: str, filters: SearchFilters | None, skip: int, limit: int
    ) -> SearchResponse:
        """Search specifically for code blocks."""
        # Enhance query for code search
        code_query = self._enhance_code_query(query)

        # Add code-specific stages to pipeline
        return await self.search_messages(
            query=code_query, filters=filters, skip=skip, limit=limit, highlight=True
        )

    def _build_search_pipeline(
        self, query: str, filters: SearchFilters | None, skip: int, limit: int
    ) -> list[dict[str, Any]]:
        """Build MongoDB aggregation pipeline for search."""
        pipeline: list[dict[str, Any]] = []

        # Text search stage
        pipeline.append({"$match": {"$text": {"$search": query}}})

        # Add text score
        pipeline.append({"$addFields": {"score": {"$meta": "textScore"}}})

        # Join with sessions and projects BEFORE filtering
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "sessions",
                        "localField": "sessionId",
                        "foreignField": "sessionId",
                        "as": "session",
                    }
                },
                {"$unwind": {"path": "$session", "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": "projects",
                        "localField": "session.projectId",
                        "foreignField": "_id",
                        "as": "project",
                    }
                },
                {"$unwind": {"path": "$project", "preserveNullAndEmptyArrays": True}},
            ]
        )

        # Add filters AFTER joins
        if filters:
            filter_stage = self._build_filter_stage(filters)
            if filter_stage:
                pipeline.append({"$match": filter_stage})

        # Sort by relevance
        pipeline.append({"$sort": {"score": -1, "timestamp": -1}})

        # Pagination
        pipeline.append({"$skip": skip})
        pipeline.append({"$limit": limit})

        return pipeline

    def _build_count_pipeline(
        self, query: str, filters: SearchFilters | None
    ) -> list[dict[str, Any]]:
        """Build pipeline for counting total results."""
        pipeline: list[dict[str, Any]] = []

        # Text search
        pipeline.append({"$match": {"$text": {"$search": query}}})

        # Need to join if we have project filters
        if filters and filters.project_ids:
            pipeline.extend(
                [
                    {
                        "$lookup": {
                            "from": "sessions",
                            "localField": "sessionId",
                            "foreignField": "sessionId",
                            "as": "session",
                        }
                    },
                    {
                        "$unwind": {
                            "path": "$session",
                            "preserveNullAndEmptyArrays": True,
                        }
                    },
                ]
            )

        # Add filters
        if filters:
            filter_stage = self._build_filter_stage(filters)
            if filter_stage:
                pipeline.append({"$match": filter_stage})

        # Count
        pipeline.append({"$count": "total"})

        return pipeline

    def _build_filter_stage(self, filters: SearchFilters) -> dict[str, Any]:
        """Build filter stage from search filters."""
        conditions: dict[str, Any] = {}

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
            conditions["message.model"] = {"$in": filters.models}

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
                {"toolUseResult": {"$regex": r"```", "$options": "i"}},
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
        self, doc: dict[str, Any], query: str, highlight: bool
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
            model=doc.get("message", {}).get("model")
            if isinstance(doc.get("message"), dict)
            else None,
            cost_usd=doc.get("costUsd"),
        )

    def _create_preview(self, content: str, query: str, max_length: int = 200) -> str:
        """Create a content preview with query context."""
        if not content:
            return ""

        # Find query in content (case-insensitive)
        query_lower = query.lower()
        content_lower = content.lower()

        pos = content_lower.find(query_lower)
        if pos == -1:
            # Query not found, return beginning
            return (
                content[:max_length] + "..." if len(content) > max_length else content
            )

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
        self, doc: dict[str, Any], query: str
    ) -> list[SearchHighlight]:
        """Create search highlights."""
        highlights = []

        # Check message content
        if doc.get("message") and isinstance(doc["message"], dict):
            content = doc["message"].get("content", "")
            if content and query.lower() in content.lower():
                snippet = self._create_preview(content, query, max_length=150)
                highlights.append(
                    SearchHighlight(field="message.content", snippet=snippet, score=1.0)
                )

        # Check tool results
        if doc.get("toolUseResult"):
            tool_result = str(doc["toolUseResult"])
            if query.lower() in tool_result.lower():
                snippet = self._create_preview(tool_result, query, max_length=150)
                highlights.append(
                    SearchHighlight(field="toolUseResult", snippet=snippet, score=0.8)
                )

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
        self, partial_query: str, limit: int
    ) -> list[SearchSuggestion]:
        """Get search suggestions."""
        suggestions = []

        # Get from recent searches
        recent_searches = (
            await self.db.search_logs.find(
                {"query": {"$regex": f"^{re.escape(partial_query)}", "$options": "i"}},
                {"query": 1, "count": 1},
            )
            .sort("count", -1)
            .limit(limit // 2)
            .to_list(limit // 2)
        )

        for search in recent_searches:
            suggestions.append(
                SearchSuggestion(
                    text=search["query"], type="query", count=search.get("count", 1)
                )
            )

        # Get project names
        project_names = (
            await self.db.projects.find(
                {"name": {"$regex": f"^{re.escape(partial_query)}", "$options": "i"}},
                {"name": 1},
            )
            .limit(limit // 4)
            .to_list(limit // 4)
        )

        for project in project_names:
            suggestions.append(
                SearchSuggestion(text=project["name"], type="project", count=None)
            )

        # Get models
        models = await self.db.messages.distinct("model")
        for model in models:
            if model and partial_query.lower() in model.lower():
                suggestions.append(
                    SearchSuggestion(text=model, type="model", count=None)
                )

        return suggestions[:limit]

    async def get_recent_searches(self, limit: int) -> list[dict[str, Any]]:
        """Get recent search queries."""
        recent = (
            await self.db.search_logs.find(
                {}, {"query": 1, "timestamp": 1, "result_count": 1}
            )
            .sort("timestamp", -1)
            .limit(limit)
            .to_list(limit)
        )

        return [
            {
                "query": r["query"],
                "timestamp": r["timestamp"],
                "result_count": r.get("result_count", 0),
            }
            for r in recent
        ]

    async def get_search_stats(self) -> dict[str, Any]:
        """Get search statistics."""
        # Total searches
        total_searches = await self.db.search_logs.count_documents({})

        # Popular queries
        popular_pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$query", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]

        popular_queries = await self.db.search_logs.aggregate(popular_pipeline).to_list(
            10
        )

        # Average search time
        avg_time_pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": None, "avg_duration": {"$avg": "$duration_ms"}}}
        ]

        avg_time_result = await self.db.search_logs.aggregate(
            avg_time_pipeline
        ).to_list(1)

        avg_duration = avg_time_result[0]["avg_duration"] if avg_time_result else 0

        return {
            "total_searches": total_searches,
            "popular_queries": [
                {"query": q["_id"], "count": q["count"]} for q in popular_queries
            ],
            "average_duration_ms": round(avg_duration, 2),
        }

    async def _log_search(
        self,
        query: str,
        filters: SearchFilters | None,
        result_count: int,
        duration_ms: int,
    ) -> None:
        """Log search for analytics."""
        log_entry = {
            "query": query,
            "filters": filters.dict(exclude_none=True) if filters else {},
            "result_count": result_count,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(UTC),
        }

        await self.db.search_logs.insert_one(log_entry)

        # Update search count
        await self.db.search_logs.update_one(
            {"query": query}, {"$inc": {"count": 1}}, upsert=True
        )
