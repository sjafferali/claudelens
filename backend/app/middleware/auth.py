"""Authentication middleware."""

from typing import Callable, cast

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import get_database
from app.middleware.tenant import get_tenant_context, verify_tenant_from_api_key
from app.models.user import UserRole
from app.services.auth import AuthService


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to authenticate requests and populate tenant context."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and populate authentication context."""
        # Skip authentication for health checks and docs
        if request.url.path in [
            "/health",
            "/api/v1/health",
            "/api/v1/docs",
            "/api/v1/openapi.json",
            "/api/v1/redoc",
        ]:
            response = await call_next(request)
            return cast(Response, response)

        # Try to extract user information for request context
        try:
            context = await get_tenant_context(request)

            # Check for OIDC session
            # Check if session middleware is installed by looking at scope
            if "session" in request.scope:
                user_data = request.session.get("user")
                if user_data:
                    context.user_id = str(user_data.get("id"))
                    context.user_role = UserRole(user_data.get("role", "user"))
                    # Also set on request.state for other middleware
                    request.state.user_id = context.user_id

            # Check for JWT Bearer token
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                token_data = AuthService.decode_access_token(token)
                if token_data:
                    context.user_id = token_data.user_id
                    context.user_role = UserRole(token_data.role)
                    # Also set on request.state for other middleware
                    request.state.user_id = context.user_id

            # Check for API key
            api_key = request.headers.get("X-API-Key")
            if api_key and not context.user_id:
                db = await get_database()
                user_id = await verify_tenant_from_api_key(api_key, db, request)
                # Re-get context to ensure it's properly set
                context = await get_tenant_context(request)
                # Also set user_id directly on request.state for other middleware
                request.state.user_id = user_id

            # Check for localhost access (development mode)
            if not context.user_id:
                # Get the real client IP
                x_real_ip = request.headers.get("X-Real-IP", "")
                x_forwarded_for = request.headers.get("X-Forwarded-For", "")
                client_host = request.client.host if request.client else ""

                localhost_ips = {"127.0.0.1", "localhost", "::1"}
                if (
                    client_host in localhost_ips
                    or x_real_ip in localhost_ips
                    or (
                        x_forwarded_for
                        and x_forwarded_for.split(",")[0].strip() in localhost_ips
                    )
                ):
                    # Get or create default admin user for development
                    db = await get_database()
                    default_user = await db.users.find_one({"username": "admin"})
                    if default_user:
                        context.user_id = str(default_user["_id"])
                        context.user_role = UserRole(default_user.get("role", "admin"))
                        # Also set on request.state for other middleware
                        request.state.user_id = context.user_id

        except Exception:
            # Don't block requests if authentication fails
            # The actual endpoints will handle authentication requirements
            pass

        # Continue processing the request
        response = await call_next(request)
        return cast(Response, response)
