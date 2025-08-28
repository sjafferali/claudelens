"""Rate limiting middleware."""

import asyncio
import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any, Optional, cast

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Dynamic rate limiting middleware that uses database settings."""

    def __init__(self, app: Any, calls: int = 100, period: int = 60) -> None:
        super().__init__(app)
        # Default values (will be overridden by database settings)
        self.default_calls = calls
        self.default_period = period
        self.clients: dict[str, list] = defaultdict(list)
        self._cleanup_task: asyncio.Task[Any] | None = None
        self._settings_cache: Optional[Any] = None
        self._cache_timestamp: Optional[float] = None
        self._cache_ttl = 60  # Cache settings for 60 seconds

    async def _get_settings(self, request: Optional[Request]) -> tuple[int, int, bool]:
        """Get rate limit settings from cache or database."""
        now = time.time()

        # Check cache
        if self._settings_cache and self._cache_timestamp:
            if now - self._cache_timestamp < self._cache_ttl:
                return (
                    self._settings_cache.http_calls_per_minute,
                    self._settings_cache.http_rate_limit_window_seconds,
                    self._settings_cache.http_rate_limit_enabled
                    and self._settings_cache.rate_limiting_enabled,
                )

        # Try to get from database
        try:
            # Import here to avoid circular dependency
            from app.core.database import get_database
            from app.services.rate_limit_service import RateLimitService

            db = await get_database()
            service = RateLimitService(db)
            settings = await service.get_settings()

            self._settings_cache = settings
            self._cache_timestamp = now

            return (
                settings.http_calls_per_minute,
                settings.http_rate_limit_window_seconds,
                settings.http_rate_limit_enabled and settings.rate_limiting_enabled,
            )
        except Exception:
            # Fall back to defaults if database is unavailable
            return (self.default_calls, self.default_period, True)

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
            "/api/v1/admin/rate-limits",  # Allow admin to update rate limits
        ]

        if request.url.path in excluded_paths:
            return cast(Response, await call_next(request))

        # Get current settings
        calls_limit, period_seconds, enabled = await self._get_settings(request)

        # If rate limiting is disabled, pass through
        if not enabled:
            return cast(Response, await call_next(request))

        # Get client identifier (IP or API key)
        client_id = self._get_client_id(request)

        # Check rate limit
        now = time.time()

        # Clean old entries
        self.clients[client_id] = [
            timestamp
            for timestamp in self.clients[client_id]
            if timestamp > now - period_seconds
        ]

        # Check if limit exceeded
        if len(self.clients[client_id]) >= calls_limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={
                    "Retry-After": str(period_seconds),
                    "X-RateLimit-Limit": str(calls_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + period_seconds)),
                },
            )

        # Record this call
        self.clients[client_id].append(now)

        # Process request
        response: Response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(calls_limit)
        response.headers["X-RateLimit-Remaining"] = str(
            calls_limit - len(self.clients[client_id])
        )
        response.headers["X-RateLimit-Reset"] = str(int(now + period_seconds))

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
            # Get current period from settings
            _, period_seconds, _ = await self._get_settings(None)
            await asyncio.sleep(period_seconds)
            now = time.time()

            # Clean up old entries
            for client_id in list(self.clients.keys()):
                self.clients[client_id] = [
                    timestamp
                    for timestamp in self.clients[client_id]
                    if timestamp > now - period_seconds
                ]

                # Remove empty entries
                if not self.clients[client_id]:
                    del self.clients[client_id]
