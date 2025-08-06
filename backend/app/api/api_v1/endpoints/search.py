"""Search API endpoints."""

from typing import Any

from fastapi import HTTPException, Query

from app.api.dependencies import CommonDeps
from app.core.custom_router import APIRouter
from app.schemas.search import (
    SearchFilters,
    SearchRequest,
    SearchResponse,
    SearchSuggestion,
)
from app.services.search import SearchService

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest, db: CommonDeps) -> SearchResponse:
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
    return await service.search_messages(
        query=request.query,
        filters=request.filters,
        skip=request.skip,
        limit=request.limit,
        highlight=request.highlight,
        is_regex=request.is_regex,
    )


@router.get("/suggestions")
async def search_suggestions(
    db: CommonDeps,
    query: str = Query(..., min_length=2, description="Partial search query"),
    limit: int = Query(10, ge=1, le=20),
) -> list[SearchSuggestion]:
    """Get search suggestions based on partial query.

    Returns autocomplete suggestions from recent searches and
    common terms in the database.
    """
    service = SearchService(db)
    return await service.get_suggestions(query, limit)


@router.get("/recent")
async def recent_searches(
    db: CommonDeps, limit: int = Query(10, ge=1, le=50)
) -> list[dict[str, Any]]:
    """Get recent search queries.

    Returns the most recent searches performed, useful for
    quick access to common searches.
    """
    service = SearchService(db)
    return await service.get_recent_searches(limit)


@router.post("/code")
async def search_code(
    request: SearchRequest,
    db: CommonDeps,
    language: str | None = Query(None, description="Programming language filter"),
) -> SearchResponse:
    """Search specifically for code snippets.

    Optimized for searching code blocks with language-specific filtering.
    """
    service = SearchService(db)

    # Add code-specific filtering
    if request.filters is None:
        request.filters = SearchFilters(
            project_ids=None,
            session_ids=None,
            message_types=None,
            models=None,
            start_date=None,
            end_date=None,
            has_code=None,
            code_language=None,
            min_cost=None,
            max_cost=None,
        )

    request.filters.has_code = True
    if language:
        request.filters.code_language = language

    return await service.search_code(
        query=request.query,
        filters=request.filters,
        skip=request.skip,
        limit=request.limit,
    )


@router.get("/stats")
async def search_stats(db: CommonDeps) -> dict[str, Any]:
    """Get search statistics.

    Returns information about search usage, popular queries,
    and search performance metrics.
    """
    service = SearchService(db)
    return await service.get_search_stats()
