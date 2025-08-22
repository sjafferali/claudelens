"""ClaudeLens API Client for MCP Server."""

import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel


class ClaudeLensAPIClient:
    """Client for interacting with ClaudeLens backend API."""

    def __init__(self, base_url: str = "http://localhost:8080", api_key: Optional[str] = None):
        """Initialize the API client.

        Args:
            base_url: Base URL of the ClaudeLens backend API
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_v1_url = f"{self.base_url}/api/v1"
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    # Session endpoints
    async def list_sessions(
        self,
        project_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        sort_by: str = "started_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """List sessions with pagination and filtering."""
        params = {
            "skip": skip,
            "limit": limit,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        if project_id:
            params["project_id"] = project_id
        if search:
            params["search"] = search

        response = await self.client.get(f"{self.api_v1_url}/sessions", params=params)
        response.raise_for_status()
        return response.json()

    async def get_session(self, session_id: str, include_messages: bool = False) -> Dict[str, Any]:
        """Get a specific session by ID."""
        params = {"include_messages": include_messages}
        response = await self.client.get(f"{self.api_v1_url}/sessions/{session_id}", params=params)
        response.raise_for_status()
        return response.json()

    async def get_session_messages(
        self, session_id: str, skip: int = 0, limit: int = 50
    ) -> Dict[str, Any]:
        """Get all messages for a session."""
        params = {"skip": skip, "limit": limit}
        response = await self.client.get(
            f"{self.api_v1_url}/sessions/{session_id}/messages", params=params
        )
        response.raise_for_status()
        return response.json()

    async def get_message_thread(
        self, session_id: str, message_uuid: str, depth: int = 10
    ) -> Dict[str, Any]:
        """Get the conversation thread for a specific message."""
        params = {"depth": depth}
        response = await self.client.get(
            f"{self.api_v1_url}/sessions/{session_id}/thread/{message_uuid}", params=params
        )
        response.raise_for_status()
        return response.json()

    async def generate_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Generate or regenerate a summary for a session."""
        response = await self.client.post(
            f"{self.api_v1_url}/sessions/{session_id}/generate-summary"
        )
        response.raise_for_status()
        return response.json()

    # Message endpoints
    async def list_messages(
        self,
        session_id: Optional[str] = None,
        type: Optional[str] = None,
        model: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
        sort_order: str = "asc",
    ) -> Dict[str, Any]:
        """List messages with pagination and filtering."""
        params = {"skip": skip, "limit": limit, "sort_order": sort_order}
        if session_id:
            params["session_id"] = session_id
        if type:
            params["type"] = type
        if model:
            params["model"] = model

        response = await self.client.get(f"{self.api_v1_url}/messages", params=params)
        response.raise_for_status()
        return response.json()

    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """Get a specific message by ID."""
        response = await self.client.get(f"{self.api_v1_url}/messages/{message_id}")
        response.raise_for_status()
        return response.json()

    async def get_message_by_uuid(self, uuid: str) -> Dict[str, Any]:
        """Get a message by its Claude UUID."""
        response = await self.client.get(f"{self.api_v1_url}/messages/uuid/{uuid}")
        response.raise_for_status()
        return response.json()

    async def get_message_context(
        self, message_id: str, before: int = 5, after: int = 5
    ) -> Dict[str, Any]:
        """Get a message with surrounding context."""
        params = {"before": before, "after": after}
        response = await self.client.get(
            f"{self.api_v1_url}/messages/{message_id}/context", params=params
        )
        response.raise_for_status()
        return response.json()

    # Search endpoints
    async def search_messages(
        self,
        query: str,
        project_ids: Optional[List[str]] = None,
        session_ids: Optional[List[str]] = None,
        message_types: Optional[List[str]] = None,
        models: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 20,
        highlight: bool = True,
        is_regex: bool = False,
    ) -> Dict[str, Any]:
        """Search across messages."""
        request_data = {
            "query": query,
            "skip": skip,
            "limit": limit,
            "highlight": highlight,
            "is_regex": is_regex,
        }

        # Add filters if provided
        filters = {}
        if project_ids:
            filters["project_ids"] = project_ids
        if session_ids:
            filters["session_ids"] = session_ids
        if message_types:
            filters["message_types"] = message_types
        if models:
            filters["models"] = models

        if filters:
            request_data["filters"] = filters

        response = await self.client.post(
            f"{self.api_v1_url}/search", json=request_data
        )
        response.raise_for_status()
        return response.json()

    async def search_code(
        self,
        query: str,
        language: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Search specifically for code snippets."""
        request_data = {
            "query": query,
            "skip": skip,
            "limit": limit,
            "filters": {"has_code": True},
        }

        if language:
            request_data["filters"]["code_language"] = language

        response = await self.client.post(
            f"{self.api_v1_url}/search/code", json=request_data
        )
        response.raise_for_status()
        return response.json()

    async def get_search_suggestions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get search suggestions based on partial query."""
        params = {"query": query, "limit": limit}
        response = await self.client.get(f"{self.api_v1_url}/search/suggestions", params=params)
        response.raise_for_status()
        return response.json()

    async def get_recent_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent search queries."""
        params = {"limit": limit}
        response = await self.client.get(f"{self.api_v1_url}/search/recent", params=params)
        response.raise_for_status()
        return response.json()

    # Project endpoints
    async def list_projects(self, skip: int = 0, limit: int = 20) -> Dict[str, Any]:
        """List projects with pagination."""
        params = {"skip": skip, "limit": limit}
        response = await self.client.get(f"{self.api_v1_url}/projects", params=params)
        response.raise_for_status()
        return response.json()

    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get a specific project by ID."""
        response = await self.client.get(f"{self.api_v1_url}/projects/{project_id}")
        response.raise_for_status()
        return response.json()

    # Analytics endpoints
    async def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for a specific session."""
        # Note: The backend doesn't have a specific session analytics endpoint
        # We'll return basic session info with statistics
        response = await self.client.get(f"{self.api_v1_url}/sessions/{session_id}")
        response.raise_for_status()
        session_data = response.json()

        # Return analytics-style response with available data
        return {
            "session_id": session_id,
            "message_count": session_data.get("messageCount", 0),
            "total_cost": session_data.get("totalCost", 0.0),
            "started_at": session_data.get("startedAt"),
            "ended_at": session_data.get("endedAt"),
            "duration": None,  # Could be calculated from start/end times
            "summary": session_data.get("summary", "No summary available")
        }

    async def get_project_analytics(self, project_id: str) -> Dict[str, Any]:
        """Get analytics for a specific project."""
        response = await self.client.get(f"{self.api_v1_url}/analytics/projects/{project_id}")
        response.raise_for_status()
        return response.json()

    # Export endpoints (for enhanced MCP integration)
    async def export_session_for_mcp(
        self,
        session_id: str,
        format: str = "json",
        include_metadata: bool = True,
        include_costs: bool = True,
        flatten_threads: bool = False,
    ) -> Dict[str, Any]:
        """Export a session in a format optimized for MCP consumption."""
        params = {
            "format": format,
            "include_metadata": include_metadata,
            "include_costs": include_costs,
            "flatten_threads": flatten_threads,
        }
        response = await self.client.get(
            f"{self.api_v1_url}/export/sessions/{session_id}/export", params=params
        )
        response.raise_for_status()
        return response.json()

    async def get_structured_conversations(
        self,
        project_id: Optional[str] = None,
        limit: int = 10,
        include_summaries: bool = True,
        include_costs: bool = True,
    ) -> Dict[str, Any]:
        """Get conversations in a structured format optimized for MCP resources."""
        params = {
            "limit": limit,
            "include_summaries": include_summaries,
            "include_costs": include_costs,
        }
        if project_id:
            params["project_id"] = project_id

        response = await self.client.get(
            f"{self.api_v1_url}/export/conversations/structured", params=params
        )
        response.raise_for_status()
        return response.json()
