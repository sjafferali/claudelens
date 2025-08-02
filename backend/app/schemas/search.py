"""Search schemas."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    """Search filter options."""

    project_ids: list[str] | None = Field(None, description="Filter by project IDs")
    session_ids: list[str] | None = Field(None, description="Filter by session IDs")
    message_types: list[str] | None = Field(None, description="Filter by message types")
    models: list[str] | None = Field(None, description="Filter by AI models")
    start_date: datetime | None = Field(None, description="Messages after this date")
    end_date: datetime | None = Field(None, description="Messages before this date")
    has_code: bool | None = Field(None, description="Only messages with code blocks")
    code_language: str | None = Field(None, description="Code language filter")
    min_cost: float | None = Field(None, description="Minimum message cost")
    max_cost: float | None = Field(None, description="Maximum message cost")


class SearchRequest(BaseModel):
    """Search request parameters."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    filters: SearchFilters | None = Field(None, description="Search filters")
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
    highlights: list[SearchHighlight] = Field(default_factory=list)

    score: float = Field(..., description="Search relevance score")

    # Optional enriched data
    session_summary: str | None = None
    model: str | None = None
    cost_usd: float | None = None


class SearchResponse(BaseModel):
    """Search response with results and metadata."""

    query: str = Field(..., description="Original search query")
    total: int = Field(..., description="Total number of matching results")
    skip: int = Field(..., description="Number of results skipped")
    limit: int = Field(..., description="Maximum results returned")

    results: list[SearchResult] = Field(..., description="Search results")

    took_ms: int = Field(..., description="Search duration in milliseconds")
    filters_applied: dict[str, Any] = Field(default_factory=dict)


class SearchSuggestion(BaseModel):
    """Search autocomplete suggestion."""

    text: str = Field(..., description="Suggestion text")
    type: str = Field(..., description="Suggestion type (query, project, model)")
    count: int | None = Field(None, description="Number of occurrences")
