"""Rate limiting middleware."""

import asyncio
import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any, cast

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(self, app: Any, calls: int = 100, period: int = 60) -> None:
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: dict[str, list] = defaultdict(list)
        self._cleanup_task: asyncio.Task[Any] | None = None

    async def dispatch(
        self, request: Request, call_next: Callable[..., Any]
    ) -> Response:
        """Check rate limit before processing request."""
        # Skip rate limiting for health checks and certain API endpoints
        excluded_paths = [
            "/health",
            "/api/v1/health",
            "/api/v1/messages/calculate-costs",  # Cost calculation should not be rate limited
            "/api/v1/projects",  # Project creation from sync should not be rate limited
        ]

        if request.url.path in excluded_paths:
            return cast(Response, await call_next(request))

        # Get client identifier (IP or API key)
        client_id = self._get_client_id(request)

        # Check rate limit
        now = time.time()

        # Clean old entries
        self.clients[client_id] = [
            timestamp
            for timestamp in self.clients[client_id]
            if timestamp > now - self.period
        ]

        # Check if limit exceeded
        if len(self.clients[client_id]) >= self.calls:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={
                    "Retry-After": str(self.period),
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + self.period)),
                },
            )

        # Record this call
        self.clients[client_id].append(now)

        # Process request
        response: Response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(
            self.calls - len(self.clients[client_id])
        )
        response.headers["X-RateLimit-Reset"] = str(int(now + self.period))

        # Start cleanup task if not running
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api:{api_key[:8]}"

        # Fall back to IP
        if request.client:
            return f"ip:{request.client.host}"

        return "unknown"

    async def _periodic_cleanup(self) -> None:
        """Periodically clean up old entries."""
        while True:
            await asyncio.sleep(self.period)
            now = time.time()

            # Clean up old entries
            for client_id in list(self.clients.keys()):
                self.clients[client_id] = [
                    timestamp
                    for timestamp in self.clients[client_id]
                    if timestamp > now - self.period
                ]

                # Remove empty entries
                if not self.clients[client_id]:
                    del self.clients[client_id]
