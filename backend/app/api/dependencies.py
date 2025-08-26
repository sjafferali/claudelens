"""API dependencies."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.middleware.tenant import get_tenant_context, verify_tenant_from_api_key
from app.models.user import UserInDB, UserRole
from app.services.user import UserService


async def get_db() -> AsyncIOMotorDatabase:
    """Get database dependency."""
    return await get_database()


async def verify_api_key_header(
    request: Request,
    x_api_key: Annotated[str | None, Header()] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> str:
    """Verify API key from header.

    Allow requests from localhost/127.0.0.1 without authentication.
    This enables the frontend to communicate with the backend without API key.
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

    # For non-localhost requests, require API key
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify API key and get user
    user_id = await verify_tenant_from_api_key(x_api_key, db, request)
    return user_id


async def get_current_user(
    user_id: str = Depends(verify_api_key_header),
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
AuthDeps = Annotated[str, Depends(verify_api_key_header)]
CurrentUser = Annotated[UserInDB, Depends(get_current_user)]
AdminUser = Annotated[UserInDB, Depends(require_admin)]
