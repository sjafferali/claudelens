"""Debug endpoint for checking authentication and rate limit status."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_db
from app.middleware.tenant import get_tenant_context

router = APIRouter()


@router.get("/status")
async def get_status(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Dict[str, Any]:
    """Get current authentication and request status."""

    # Get tenant context
    context = await get_tenant_context(request)

    # Get user details if authenticated
    user_details: Optional[Dict[str, Any]] = None
    if context.user_id:
        from bson import ObjectId

        try:
            user = await db.users.find_one({"_id": ObjectId(context.user_id)})
            if user:
                user_details = {
                    "id": str(user["_id"]),
                    "username": user.get("username"),
                    "email": user.get("email"),
                    "role": user.get("role"),
                }
        except Exception:
            # User ID might not be a valid ObjectId
            user_details = {
                "id": context.user_id,
                "username": "Unknown",
                "email": None,
                "role": str(context.user_role) if context.user_role else None,
            }

    # Get authentication method
    auth_method = "none"
    if request.headers.get("X-API-Key"):
        auth_method = "api_key"
        # Show which API key was used (partial)
        api_key = request.headers.get("X-API-Key", "")
        if len(api_key) > 12:
            auth_method += f" ({api_key[:8]}...{api_key[-4:]})"
    elif request.headers.get("Authorization"):
        auth_method = "bearer_token"
    elif (
        hasattr(request, "session") and request.session and request.session.get("user")
    ):
        auth_method = "session"
    elif context.user_id:
        auth_method = "localhost_default"

    # Get rate limit info
    rate_limit_info: Dict[str, Optional[str]] = {
        "client_id": None,
        "user_id_for_tracking": None,
    }

    # Check what the rate limit middleware would see
    if hasattr(request.state, "user_id"):
        rate_limit_info["user_id_from_state"] = str(request.state.user_id)

    if hasattr(request.state, "tenant_context"):
        tenant_context_obj = request.state.tenant_context
        if hasattr(tenant_context_obj, "user_id") and tenant_context_obj.user_id:
            rate_limit_info["user_id_from_context"] = str(tenant_context_obj.user_id)

    # Simulate what _get_client_id would return
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        rate_limit_info["client_id"] = f"api:{api_key_header[:8]}"
    elif request.client:
        rate_limit_info["client_id"] = f"ip:{request.client.host}"
    else:
        rate_limit_info["client_id"] = "unknown"

    # Get request details
    request_details = {
        "method": request.method,
        "path": request.url.path,
        "client_host": request.client.host if request.client else None,
        "headers": {
            "X-API-Key": "present" if request.headers.get("X-API-Key") else "absent",
            "Authorization": "present"
            if request.headers.get("Authorization")
            else "absent",
            "X-Real-IP": request.headers.get("X-Real-IP"),
            "X-Forwarded-For": request.headers.get("X-Forwarded-For"),
        },
    }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "authenticated": bool(context.user_id),
        "authentication_method": auth_method,
        "user": user_details,
        "tenant_context": {
            "user_id": context.user_id,
            "user_role": str(context.user_role) if context.user_role else None,
            "api_key_name": context.api_key_name,
            "permissions": context.permissions,
        },
        "rate_limit_tracking": rate_limit_info,
        "request": request_details,
    }


@router.get("/rate-limit-test")
async def test_rate_limit_tracking(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Dict[str, Any]:
    """Test what user ID would be used for rate limit tracking."""

    # This simulates what the rate limit middleware sees
    user_id = None
    source = "none"

    # Check tenant context first (same as rate limit middleware)
    if hasattr(request.state, "tenant_context"):
        tenant_context = request.state.tenant_context
        if hasattr(tenant_context, "user_id") and tenant_context.user_id:
            user_id = str(tenant_context.user_id)
            source = "tenant_context"

    # Check request.state.user_id
    if not user_id and hasattr(request.state, "user_id"):
        user_id_value = request.state.user_id
        if user_id_value:
            user_id = str(user_id_value)
            source = "request.state.user_id"

    # Check request.state.user
    if (
        not user_id
        and hasattr(request.state, "user")
        and hasattr(request.state.user, "id")
    ):
        user_id = str(request.state.user.id)
        source = "request.state.user"

    # Fall back to client ID
    if not user_id:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            user_id = f"api_{api_key[:8]}"
            source = "api_key_prefix"
        elif request.client:
            user_id = f"ip_{request.client.host}"
            source = "ip_address"
        else:
            user_id = "unknown"
            source = "unknown"

    # Try to identify the actual user if we have a proper user_id
    user_details = None
    if user_id and "_" not in user_id and "unknown" not in user_id:
        from bson import ObjectId

        try:
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user_details = {
                    "username": user.get("username"),
                    "email": user.get("email"),
                }
        except Exception:
            pass

    return {
        "rate_limit_user_id": user_id,
        "source": source,
        "identified_user": user_details,
        "explanation": {
            "api_key_present": bool(request.headers.get("X-API-Key")),
            "has_tenant_context": hasattr(request.state, "tenant_context"),
            "has_user_id_state": hasattr(request.state, "user_id"),
            "has_user_state": hasattr(request.state, "user"),
        },
    }
