"""Enhanced rate limiting middleware with usage tracking."""

import asyncio
import time
from typing import Any, Callable, Optional, cast

from fastapi import Request, Response
from starlette.responses import JSONResponse

from app.middleware.rate_limit import RateLimitMiddleware
from app.models.rate_limit_usage import RateLimitType


class RateLimitTrackingMiddleware(RateLimitMiddleware):
    """Rate limiting middleware with usage tracking capabilities."""

    def __init__(self, app: Any, calls: int = 100, period: int = 60) -> None:
        super().__init__(app, calls, period)
        self._usage_service: Optional[Any] = None
        self._usage_service_init = False

    async def _get_usage_service(self) -> Optional[Any]:
        """Lazy load usage service to avoid circular imports."""
        if not self._usage_service_init:
            try:
                from app.core.database import get_database
                from app.services.rate_limit_usage_service import RateLimitUsageService

                db = await get_database()
                self._usage_service = RateLimitUsageService(db)
                self._usage_service_init = True
            except Exception:
                # Service unavailable, continue without tracking
                self._usage_service_init = True
                pass

        return self._usage_service

    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request if available."""
        # Try to get from request state (set by auth middleware)
        if hasattr(request.state, "user_id"):
            user_id_value: Any = request.state.user_id
            return str(user_id_value) if user_id_value else None

        # Try to get from request state user object
        if hasattr(request.state, "user") and hasattr(request.state.user, "id"):
            user_id: Any = request.state.user.id
            return str(user_id)

        # Fall back to client ID as user ID for tracking
        return self._get_client_id(request)

    def _determine_limit_type(self, path: str) -> Optional[RateLimitType]:
        """Determine the rate limit type based on request path."""
        path_lower = path.lower()

        # Map paths to rate limit types
        if "/ingest" in path_lower:
            return RateLimitType.INGESTION
        elif (
            "/ai" in path_lower or "/prompt" in path_lower or "/generate" in path_lower
        ):
            return RateLimitType.AI
        elif "/export" in path_lower:
            return RateLimitType.EXPORT
        elif "/import" in path_lower:
            return RateLimitType.IMPORT
        elif "/backup" in path_lower:
            return RateLimitType.BACKUP
        elif "/restore" in path_lower:
            return RateLimitType.RESTORE
        elif "/search" in path_lower:
            return RateLimitType.SEARCH
        elif "/analytics" in path_lower or "/stats" in path_lower:
            return RateLimitType.ANALYTICS
        elif "/ws" in path_lower or "/websocket" in path_lower:
            return RateLimitType.WEBSOCKET
        else:
            # Default to HTTP for general API calls
            return RateLimitType.HTTP

    async def dispatch(
        self, request: Request, call_next: Callable[..., Any]
    ) -> Response:
        """Enhanced dispatch with usage tracking."""
        start_time = time.time()

        # Determine rate limit type
        limit_type = self._determine_limit_type(request.url.path)

        # Get user ID
        user_id = self._get_user_id(request)

        # Skip rate limiting for excluded paths
        excluded_paths = [
            "/health",
            "/api/v1/health",
            "/api/v1/messages/calculate-costs",
            "/api/v1/projects",
            "/api/v1/admin/rate-limits",
            "/api/v1/rate-limits/usage",  # Don't rate limit usage queries
        ]

        if request.url.path in excluded_paths:
            response = await call_next(request)
            return cast(Response, response)

        # Get current settings
        calls_limit, period_seconds, enabled = await self._get_settings(request)

        # Track the request attempt
        response_time_ms = None
        bytes_transferred = None

        # If rate limiting is disabled, just track and pass through
        if not enabled:
            response = await call_next(request)
            response_time_ms = (time.time() - start_time) * 1000

            # Track usage if service is available
            await self._track_usage(
                user_id, limit_type, True, response_time_ms, bytes_transferred
            )

            return cast(Response, response)

        # Get client identifier
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
            # Track the blocked request
            await self._track_usage(user_id, limit_type, False, None, None)

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
        response = await call_next(request)
        response_time_ms = (time.time() - start_time) * 1000

        # Try to get response size if available
        if hasattr(response, "headers") and "content-length" in response.headers:
            try:
                bytes_transferred = int(response.headers["content-length"])
            except (ValueError, TypeError):
                pass

        # Track the successful request
        await self._track_usage(
            user_id, limit_type, True, response_time_ms, bytes_transferred
        )

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(calls_limit)
        response.headers["X-RateLimit-Remaining"] = str(
            calls_limit - len(self.clients[client_id])
        )
        response.headers["X-RateLimit-Reset"] = str(int(now + period_seconds))

        # Start cleanup task if not running
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

        return cast(Response, response)

    async def _track_usage(
        self,
        user_id: Optional[str],
        limit_type: Optional[RateLimitType],
        allowed: bool,
        response_time_ms: Optional[float],
        bytes_transferred: Optional[int],
    ) -> None:
        """Track usage if service is available."""
        if not user_id or not limit_type:
            return

        usage_service = await self._get_usage_service()
        if usage_service:
            try:
                await usage_service.record_request(
                    user_id=user_id,
                    limit_type=limit_type,
                    allowed=allowed,
                    response_time_ms=response_time_ms,
                    bytes_transferred=bytes_transferred,
                )
            except Exception:
                # Don't let tracking failures affect the request
                pass
