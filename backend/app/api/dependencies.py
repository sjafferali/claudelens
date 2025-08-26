"""API dependencies."""

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.middleware.tenant import get_tenant_context, verify_tenant_from_api_key
from app.models.user import UserInDB, UserRole
from app.services.auth import AuthService
from app.services.user import UserService

# Bearer token scheme for JWT
bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIOMotorDatabase:
    """Get database dependency."""
    return await get_database()


async def verify_api_key_or_jwt(
    request: Request,
    x_api_key: Annotated[str | None, Header()] = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> str:
    """Verify authentication via API key or JWT token.

    Supports:
    1. OIDC session (for SSO)
    2. JWT Bearer token (for UI)
    3. X-API-Key header (for programmatic access)
    4. Localhost access without authentication (for development)
    """
    # Check if request is from localhost (nginx proxy or direct)
    if request:
        # Get the real client IP from headers set by nginx
        x_real_ip = request.headers.get("X-Real-IP", "")
        x_forwarded_for = request.headers.get("X-Forwarded-For", "")
        client_host = request.client.host if request.client else ""

        # Check if request is from localhost/127.0.0.1
        localhost_ips = {"127.0.0.1", "localhost", "::1"}
        if (
            client_host in localhost_ips
            or x_real_ip in localhost_ips
            or x_forwarded_for.split(",")[0].strip() in localhost_ips
        ):
            # Create a default development user context
            context = await get_tenant_context(request)
            # Get or create default admin user for development
            user_service = UserService(db)
            default_user = await db.users.find_one({"username": "admin"})
            if not default_user:
                # Create default admin user
                from app.models.user import UserCreate

                user, _ = await user_service.create_user(
                    UserCreate(
                        email="admin@localhost",
                        username="admin",
                        role=UserRole.ADMIN,
                    )
                )
                context.user_id = str(user.id)
                context.user_role = UserRole.ADMIN
                return str(user.id)
            else:
                context.user_id = str(default_user["_id"])
                context.user_role = UserRole(default_user.get("role", "admin"))
                return str(default_user["_id"])

    # For non-localhost requests, check for authentication
    # First check for OIDC session
    if hasattr(request, "session") and request.session and request.session.get("user"):
        user_data = request.session.get("user")
        if user_data:
            context = await get_tenant_context(request)
            context.user_id = str(user_data.get("id"))
            context.user_role = UserRole(user_data.get("role", "user"))
            return str(user_data.get("id"))

    # Then try JWT token (for UI)
    if credentials and credentials.credentials:
        token_data = AuthService.decode_access_token(credentials.credentials)
        if token_data:
            # JWT is valid, set up tenant context
            context = await get_tenant_context(request)
            context.user_id = token_data.user_id
            context.user_role = UserRole(token_data.role)
            return token_data.user_id

    # Then try API key (for programmatic access)
    if x_api_key:
        user_id = await verify_tenant_from_api_key(x_api_key, db, request)
        return user_id

    # No valid authentication found
    raise HTTPException(
        status_code=401,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer, ApiKey"},
    )


async def get_current_user(
    user_id: str = Depends(verify_api_key_or_jwt),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserInDB:
    """Get the current authenticated user."""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def require_admin(
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """Require admin role for access."""
    context = await get_tenant_context(request)
    if context.user_role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# Common dependencies
CommonDeps = Annotated[AsyncIOMotorDatabase, Depends(get_db)]
AuthDeps = Annotated[str, Depends(verify_api_key_or_jwt)]
CurrentUser = Annotated[UserInDB, Depends(get_current_user)]
AdminUser = Annotated[UserInDB, Depends(require_admin)]

# Backward compatibility alias for tests
verify_api_key_header = verify_api_key_or_jwt
