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