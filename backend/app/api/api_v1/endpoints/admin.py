"""Admin dashboard endpoints."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Sequence, cast

from bson import Decimal128, ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel as PydanticBaseModel

from app.api.dependencies import get_db, require_admin
from app.models.oidc_settings import OIDCSettingsInDB
from app.models.rate_limit_settings import RateLimitSettings
from app.models.user import UserInDB, UserRole
from app.schemas.oidc import (
    OIDCSettingsResponse,
    OIDCSettingsUpdate,
    OIDCTestConnectionRequest,
    OIDCTestConnectionResponse,
)
from app.services.oidc_service import oidc_service
from app.services.rate_limit_service import RateLimitService
from app.services.rolling_message_service import RollingMessageService
from app.services.storage_metrics import StorageMetricsService
from app.services.user import UserService

router = APIRouter()


def convert_bson_types(obj: Any) -> Any:
    """Recursively convert BSON types to JSON-serializable types."""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, Decimal128):
        return float(str(obj))
    elif isinstance(obj, dict):
        return {key: convert_bson_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_bson_types(item) for item in obj]
    else:
        return obj


def convert_decimal128(value: Any) -> Any:
    """Convert Decimal128 values to float for JSON serialization."""
    if isinstance(value, Decimal128):
        return float(str(value))
    return value


@router.get("/stats")
async def get_admin_statistics(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """Get system-wide statistics for admin dashboard."""
    # Aggregate user statistics
    user_stats_pipeline = [
        {
            "$group": {
                "_id": "$role",
                "count": {"$sum": 1},
                "total_storage": {"$sum": "$total_disk_usage"},
                "avg_storage": {"$avg": "$total_disk_usage"},
            }
        }
    ]

    # Get top users by storage
    top_users_pipeline = [
        {"$sort": {"total_disk_usage": -1}},
        {"$limit": 10},
        {
            "$project": {
                "username": 1,
                "email": 1,
                "total_disk_usage": 1,
                "session_count": 1,
                "message_count": 1,
                "project_count": 1,
            }
        },
    ]

    # Run aggregations in parallel
    user_stats_typed: Sequence[Mapping[str, Any]] = user_stats_pipeline  # type: ignore
    top_users_typed: Sequence[Mapping[str, Any]] = top_users_pipeline  # type: ignore
    user_stats_task = db.users.aggregate(user_stats_typed).to_list(None)
    top_users_task = db.users.aggregate(top_users_typed).to_list(None)
    total_users_task = db.users.count_documents({})

    user_stats, top_users, total_users = await asyncio.gather(
        user_stats_task, top_users_task, total_users_task
    )

    # Calculate system totals
    total_sessions = await db.sessions.count_documents({})

    # Count messages across rolling collections
    all_collections = await db.list_collection_names()
    message_collections = [c for c in all_collections if c.startswith("messages_")]
    total_messages = 0
    if message_collections:
        for coll_name in message_collections:
            count = await db[coll_name].count_documents({})
            total_messages += count
    else:
        # Fallback to single messages collection if it exists
        total_messages = await db.messages.count_documents({})

    total_projects = await db.projects.count_documents({})

    # Format user stats by role
    users_by_role = {}
    total_storage_bytes = 0
    for stat in user_stats:
        role = stat["_id"]
        users_by_role[role] = {
            "count": stat["count"],
            "total_storage": stat["total_storage"],
            "avg_storage": stat["avg_storage"],
        }
        total_storage_bytes += stat["total_storage"]

    # Format top users
    formatted_top_users = []
    for user in top_users:
        formatted_top_users.append(
            {
                "id": str(user["_id"]),
                "username": user.get("username", "N/A"),
                "email": user.get("email", "N/A"),
                "total_disk_usage": user.get("total_disk_usage", 0),
                "session_count": user.get("session_count", 0),
                "message_count": user.get("message_count", 0),
                "project_count": user.get("project_count", 0),
            }
        )

    return {
        "total_users": total_users,
        "users_by_role": users_by_role,
        "top_users_by_storage": formatted_top_users,
        "system_totals": {
            "total_storage_bytes": total_storage_bytes,
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_projects": total_projects,
        },
    }


@router.get("/users")
async def get_admin_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    role: str | None = None,
    search: str | None = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """Get paginated list of users with detailed information."""
    # Build query
    query: Dict[str, Any] = {}
    if role:
        query["role"] = role
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]

    # Determine sort direction
    sort_direction = -1 if sort_order == "desc" else 1

    # Get total count
    total = await db.users.count_documents(query)

    # Get users
    cursor = db.users.find(query).sort(sort_by, sort_direction).skip(skip).limit(limit)

    users = []
    async for user in cursor:
        users.append(
            {
                "id": str(user["_id"]),
                "username": user.get("username"),
                "email": user.get("email"),
                "role": user.get("role"),
                "created_at": user.get("created_at"),
                "updated_at": user.get("updated_at"),
                "project_count": user.get("project_count", 0),
                "session_count": user.get("session_count", 0),
                "message_count": user.get("message_count", 0),
                "total_disk_usage": user.get("total_disk_usage", 0),
                "api_key_count": len(user.get("api_keys", [])),
                "last_active": max(
                    (
                        key.get("last_used")
                        for key in user.get("api_keys", [])
                        if key.get("last_used")
                    ),
                    default=None,
                ),
            }
        )

    return {
        "items": users,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/users/{user_id}/recalculate-storage")
async def recalculate_user_storage(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """Recalculate storage metrics for a specific user."""
    storage_service = StorageMetricsService(db)
    metrics = await storage_service.update_user_storage_cache(user_id)

    return {
        "message": "Storage metrics recalculated successfully",
        "metrics": metrics,
    }


@router.post("/recalculate-all-storage")
async def recalculate_all_storage(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """Recalculate storage metrics for all users (may take time)."""
    storage_service = StorageMetricsService(db)
    result = await storage_service.batch_update_all_users()

    return {
        "message": "Storage metrics recalculated for all users",
        "result": result,
    }


@router.delete("/users/{user_id}/cascade")
async def delete_user_cascade(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """Delete a user and all their data (cascade delete)."""
    from bson import ObjectId

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    user_oid = ObjectId(user_id)

    # Delete in order of dependencies
    delete_tasks = [
        db.messages.delete_many({"user_id": user_oid}),
        db.sessions.delete_many({"user_id": user_oid}),
        db.projects.delete_many({"user_id": user_oid}),
    ]

    results = await asyncio.gather(*delete_tasks)

    # Finally delete the user
    user_result = await db.users.delete_one({"_id": user_oid})

    if user_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "deleted": {
            "messages": results[0].deleted_count,
            "sessions": results[1].deleted_count,
            "projects": results[2].deleted_count,
            "user": 1,
        }
    }


class ChangeRoleRequest(PydanticBaseModel):
    """Request model for changing user role."""

    new_role: UserRole


@router.post("/users/{user_id}/change-role")
async def change_user_role(
    user_id: str,
    request: ChangeRoleRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """Change a user's role."""
    user_service = UserService(db)
    from app.models.user import UserUpdate

    user = await user_service.update_user(user_id, UserUpdate(role=request.new_role))

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "message": "User role updated successfully",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    }


class PasswordResetRequest(PydanticBaseModel):
    """Request model for password reset."""

    new_password: str


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    request: PasswordResetRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """Reset a user's password (admin only)."""
    from app.services.auth import AuthService

    # Validate password strength
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters long"
        )

    # Check if password contains at least one number and one letter
    if not any(c.isdigit() for c in request.new_password):
        raise HTTPException(
            status_code=400, detail="Password must contain at least one number"
        )

    if not any(c.isalpha() for c in request.new_password):
        raise HTTPException(
            status_code=400, detail="Password must contain at least one letter"
        )

    # Hash the new password
    password_hash = AuthService.hash_password(request.new_password)

    # Check if user exists
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update password_hash directly
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "password_hash": password_hash,
                "updated_at": datetime.now(timezone.utc),
                "auth_method": "local",  # Ensure auth method is set to local
            }
        },
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update password")

    return {
        "message": f"Password reset successfully for user {user['username']}",
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
        },
    }


@router.get("/storage/breakdown")
async def get_storage_breakdown(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """Get storage breakdown by collection and user."""
    storage_service = StorageMetricsService(db)

    # Get system metrics
    system_metrics = await storage_service.calculate_system_metrics()

    # Get top users by storage
    top_users = await storage_service.get_top_users_by_storage(limit=20)

    # Transform system_metrics to match frontend expectations
    by_collection = {}
    if system_metrics.get("breakdown"):
        # Extract collection sizes from breakdown
        for key, value in system_metrics["breakdown"].items():
            if key.endswith("_bytes"):
                collection_name = key.replace("_bytes", "")
                by_collection[collection_name] = value

    transformed_metrics = {
        "total_size_bytes": system_metrics.get("total_disk_usage", 0),
        "by_collection": by_collection,
        "by_user": [],  # This would require additional aggregation if needed
    }

    # Format top users
    formatted_top_users = []
    for user in top_users:
        formatted_top_users.append(
            {
                "user_id": str(user.get("_id", "")),
                "username": user.get("username", "Unknown"),
                "total_disk_usage": user.get("total_disk_usage", 0),
                "session_count": user.get("session_count", 0),
                "message_count": user.get("message_count", 0),
                "project_count": user.get("project_count", 0),
            }
        )

    # Convert any BSON types to JSON-serializable types
    result = convert_bson_types(
        {
            "system_metrics": transformed_metrics,
            "top_users": formatted_top_users,
        }
    )

    # Cast the result to the correct type for mypy
    return cast(Dict[str, Any], result)


@router.get("/activity/recent")
async def get_recent_activity(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> List[Dict[str, Any]]:
    """Get recent system activity."""
    # Get recent sessions
    recent_sessions = (
        await db.sessions.find({})
        .sort("startedAt", -1)
        .limit(limit)
        .to_list(length=limit)
    )

    activity = []
    for session in recent_sessions:
        # Get user info
        user = await db.users.find_one({"_id": session.get("user_id")})

        # Convert totalCost from Decimal128 to float
        total_cost = session.get("totalCost", 0)
        total_cost = convert_decimal128(total_cost)

        activity.append(
            {
                "type": "session",
                "timestamp": session.get("startedAt"),
                "user": user.get("username") if user else "Unknown",
                "session_id": str(session["_id"]),
                "message_count": session.get("messageCount", 0),
                "total_cost": total_cost,
            }
        )

    # Sort by timestamp
    activity.sort(key=lambda x: x["timestamp"], reverse=True)

    return activity[:limit]


# OIDC Settings Management Endpoints


@router.get("/oidc-settings", response_model=OIDCSettingsResponse)
async def get_oidc_settings(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> OIDCSettingsResponse:
    """Get OIDC settings."""
    settings = await oidc_service.load_settings(db)

    if not settings:
        # Return default settings if none exist
        from app.models.oidc_settings import PyObjectId

        settings = OIDCSettingsInDB(
            _id=PyObjectId(),
            enabled=False,
            client_id="",
            client_secret_encrypted="",
            discovery_endpoint="",
            redirect_uri="",
            scopes=["openid", "email", "profile"],
            auto_create_users=True,
            default_role="user",
        )

    return OIDCSettingsResponse(
        _id=str(settings.id),
        enabled=settings.enabled,
        client_id=settings.client_id,
        discovery_endpoint=settings.discovery_endpoint,
        redirect_uri=settings.redirect_uri,
        scopes=settings.scopes,
        auto_create_users=settings.auto_create_users,
        default_role=settings.default_role,
        api_key_configured=bool(settings.client_secret_encrypted),
        created_at=settings.created_at,
        updated_at=settings.updated_at,
        updated_by=settings.updated_by,
    )


@router.put("/oidc-settings", response_model=OIDCSettingsResponse)
async def update_oidc_settings(
    settings_update: OIDCSettingsUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> OIDCSettingsResponse:
    """Update OIDC settings."""
    # Load existing settings or create new
    existing = await oidc_service.load_settings(db)

    if existing:
        # Update existing settings
        settings_dict = existing.model_dump()
        update_dict = settings_update.model_dump(exclude_unset=True)

        # Handle client secret encryption if provided
        if "client_secret" in update_dict and update_dict["client_secret"]:
            update_dict["client_secret_encrypted"] = oidc_service.encrypt_client_secret(
                update_dict.pop("client_secret")
            )
        elif "client_secret" in update_dict:
            update_dict.pop("client_secret")

        settings_dict.update(update_dict)
        settings_dict["updated_by"] = str(admin_user.id)
        settings = OIDCSettingsInDB(**settings_dict)
    else:
        # Create new settings
        settings_dict = settings_update.model_dump(exclude_unset=True)

        # Handle client secret encryption
        if "client_secret" in settings_dict and settings_dict["client_secret"]:
            settings_dict[
                "client_secret_encrypted"
            ] = oidc_service.encrypt_client_secret(settings_dict.pop("client_secret"))
        else:
            settings_dict.pop("client_secret", None)
            settings_dict["client_secret_encrypted"] = ""

        settings_dict["updated_by"] = str(admin_user.id)
        settings = OIDCSettingsInDB(**settings_dict)

    # Save settings
    await oidc_service.save_settings(db, settings)

    return OIDCSettingsResponse(
        _id=str(settings.id),
        enabled=settings.enabled,
        client_id=settings.client_id,
        discovery_endpoint=settings.discovery_endpoint,
        redirect_uri=settings.redirect_uri,
        scopes=settings.scopes,
        auto_create_users=settings.auto_create_users,
        default_role=settings.default_role,
        api_key_configured=bool(settings.client_secret_encrypted),
        created_at=settings.created_at,
        updated_at=settings.updated_at,
        updated_by=settings.updated_by,
    )


@router.post("/oidc-settings/test", response_model=OIDCTestConnectionResponse)
async def test_oidc_connection(
    test_request: OIDCTestConnectionRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> OIDCTestConnectionResponse:
    """Test OIDC connection."""
    # Load settings if no override endpoint provided
    if not test_request.discovery_endpoint:
        await oidc_service.load_settings(db)

    # Test connection
    result = await oidc_service.test_connection(test_request.discovery_endpoint)

    return OIDCTestConnectionResponse(**result)


@router.delete("/oidc-settings")
async def delete_oidc_settings(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, str]:
    """Delete OIDC settings."""
    result = await db.oidc_settings.delete_many({})

    # Clear OIDC service configuration
    oidc_service._configured = False
    oidc_service._settings = None

    return {"message": f"Deleted {result.deleted_count} OIDC settings"}


@router.get("/rate-limits")
async def get_rate_limit_settings(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> RateLimitSettings:
    """Get current rate limit settings."""
    service = RateLimitService(db)
    return await service.get_settings()


@router.put("/rate-limits")
async def update_rate_limit_settings(
    settings: RateLimitSettings,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> RateLimitSettings:
    """Update rate limit settings."""
    service = RateLimitService(db)

    # Convert settings to dict and remove metadata fields
    updates = settings.dict(exclude={"updated_at", "updated_by"})

    # Update settings with admin user info
    updated_settings = await service.update_settings(
        updates, updated_by=admin_user.username
    )

    return updated_settings


@router.post("/rate-limits/reset")
async def reset_rate_limit_settings(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, str]:
    """Reset rate limit settings to defaults."""
    # Delete existing settings
    await db.settings.delete_one({"key": "rate_limits"})

    # Get fresh defaults
    service = RateLimitService(db)
    await service.get_settings()  # This will create defaults

    return {"message": "Rate limit settings reset to defaults"}


@router.get("/rate-limits/usage")
async def get_rate_limit_usage(
    user_id: str | None = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """Get rate limit usage statistics for all users or a specific user."""
    service = RateLimitService(db)

    if user_id:
        # Get usage for specific user
        stats = await service.get_usage_stats(user_id)
        return {"user_id": user_id, "usage": stats}

    # Get usage for all users with recent activity
    users = await db.users.find({}).to_list(100)
    all_stats = []

    for user in users:
        user_id = str(user["_id"])
        stats = await service.get_usage_stats(user_id)

        # Only include users with some activity
        if any(stat["current"] > 0 for stat in stats.values()):
            all_stats.append(
                {
                    "user_id": user_id,
                    "username": user.get("username", "Unknown"),
                    "usage": stats,
                }
            )

    return {"users": all_stats}


@router.post("/rate-limits/reset-user/{user_id}")
async def reset_user_rate_limits(
    user_id: str,
    limit_type: str | None = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, str]:
    """Reset rate limits for a specific user."""
    service = RateLimitService(db)

    if limit_type:
        # Validate limit type
        valid_types = ["export", "import", "backup", "restore"]
        if limit_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid limit type. Must be one of: {', '.join(valid_types)}",
            )

    await service.reset_user_limits(user_id, limit_type)

    if limit_type:
        return {"message": f"Reset {limit_type} rate limits for user {user_id}"}
    return {"message": f"Reset all rate limits for user {user_id}"}


@router.post("/rate-limits/cleanup-usage-data")
async def cleanup_usage_data(
    retention_days: int = Query(30, ge=1, le=365, description="Days of data to retain"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """Clean up old rate limit usage data."""
    from app.services.rate_limit_usage_service import RateLimitUsageService

    service = RateLimitUsageService(db)
    deleted_count = await service.cleanup_old_data(retention_days)

    return {
        "message": f"Cleaned up usage data older than {retention_days} days",
        "deleted_count": deleted_count,
    }


@router.get("/rate-limits/top-users")
async def get_top_users_by_usage(
    limit: int = Query(10, ge=1, le=100, description="Number of users to return"),
    hours: int = Query(24, ge=1, le=720, description="Time range in hours"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """Get top users by rate limit usage."""
    from app.services.rate_limit_usage_service import RateLimitUsageService

    service = RateLimitUsageService(db)
    top_users = await service.get_top_users_by_usage(
        limit_type=None, limit=limit, time_range_hours=hours
    )

    # Enhance with user details
    enhanced_users = []
    for user_data in top_users:
        user = None
        user_id_str = str(user_data["_id"])

        # Try to find user by ObjectId if the string is a valid ObjectId
        if ObjectId.is_valid(user_id_str):
            try:
                user = await db.users.find_one({"_id": ObjectId(user_id_str)})
            except Exception:
                pass

        # If not found and it looks like a client ID (e.g., "api:xxxxx" or "ip:xxxxx")
        if not user and ":" in user_id_str:
            # Extract the type and identifier
            id_type, id_value = user_id_str.split(":", 1)

            if id_type == "api":
                # For API keys, search by partial API key hash
                # Note: This won't find the exact user since we only have the first 8 chars
                # Instead, let's mark it as an API key user
                user = {"username": f"API Key User ({id_value})"}
            elif id_type == "ip":
                # For IP-based users
                user = {"username": f"IP User ({id_value})"}
            else:
                user = {"username": user_id_str}

        # If still not found, try as username
        if not user:
            user = await db.users.find_one({"username": user_id_str})

        # Default to showing the raw ID if no user found
        if not user:
            user = {"username": f"Unknown ({user_id_str})"}

        enhanced_users.append(
            {
                "user_id": str(user_data["_id"]),
                "username": user.get("username", "Unknown") if user else "Unknown",
                "total_requests": user_data["total_requests"],
                "total_blocked": user_data["total_blocked"],
                "avg_usage_rate": user_data["avg_usage_rate"],
            }
        )

    return {"time_range_hours": hours, "top_users": enhanced_users}


@router.post("/rate-limits/flush")
async def flush_rate_limit_metrics(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, str]:
    """Manually flush rate limit metrics from memory to database.

    This forces an immediate write of any accumulated rate limit usage data
    that is normally buffered in memory for performance.
    """
    from app.services.rate_limit_usage_service import RateLimitUsageService

    service = RateLimitUsageService(db)

    try:
        await service._flush_metrics()
        return {"message": "Rate limit metrics flushed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to flush metrics: {str(e)}"
        )


class ProjectOwnershipTransfer(PydanticBaseModel):
    """Request model for transferring project ownership."""

    project_id: str
    new_owner_id: str


class ProjectOwnershipResponse(PydanticBaseModel):
    """Response model for project ownership operations."""

    success: bool
    message: str
    project_id: str
    previous_owner_id: str
    new_owner_id: str


@router.post("/projects/transfer-ownership")
async def transfer_project_ownership(
    request: ProjectOwnershipTransfer,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> ProjectOwnershipResponse:
    """Transfer ownership of a project to another user (admin only)."""

    # Validate project exists
    if not ObjectId.is_valid(request.project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")

    project = await db.projects.find_one({"_id": ObjectId(request.project_id)})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate new owner exists
    if not ObjectId.is_valid(request.new_owner_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    new_owner = await db.users.find_one({"_id": ObjectId(request.new_owner_id)})
    if not new_owner:
        raise HTTPException(status_code=404, detail="New owner user not found")

    # Store previous owner for response
    previous_owner_id = str(project.get("user_id", "unknown"))

    # Update project ownership
    result = await db.projects.update_one(
        {"_id": ObjectId(request.project_id)},
        {"$set": {"user_id": ObjectId(request.new_owner_id)}},
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=500, detail="Failed to update project ownership"
        )

    return ProjectOwnershipResponse(
        success=True,
        message=f"Successfully transferred project ownership to {new_owner['username']}",
        project_id=request.project_id,
        previous_owner_id=previous_owner_id,
        new_owner_id=request.new_owner_id,
    )


@router.get("/projects/with-owners")
async def list_projects_with_owners(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """List all projects with their owner information (admin only)."""

    # Aggregation pipeline to join projects with users and calculate stats
    pipeline: List[Dict[str, Any]] = [
        # Join with users to get owner info
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "owner",
            }
        },
        {"$unwind": {"path": "$owner", "preserveNullAndEmptyArrays": True}},
        # Join with sessions to count sessions for this project
        {
            "$lookup": {
                "from": "sessions",
                "let": {"project_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$project_id", "$$project_id"]}}},
                    {"$count": "count"},
                ],
                "as": "session_stats",
            }
        },
        # Format the final output
        {
            "$project": {
                "_id": 1,
                "name": 1,
                "path": 1,
                "createdAt": 1,
                "updatedAt": 1,
                "stats": {
                    "session_count": {
                        "$ifNull": [{"$arrayElemAt": ["$session_stats.count", 0]}, 0]
                    },
                    "message_count": 0,  # Will be calculated separately due to rolling collections
                },
                "owner": {
                    "_id": "$owner._id",
                    "username": "$owner.username",
                    "email": "$owner.email",
                },
            }
        },
        {"$sort": {"createdAt": -1}},
        {"$skip": skip},
        {"$limit": limit},
    ]

    # Get projects with owners and session counts
    projects = await db.projects.aggregate(pipeline).to_list(None)

    # Now calculate message counts for each project
    # We need to check all rolling message collections
    all_collections = await db.list_collection_names()
    message_collections = [c for c in all_collections if c.startswith("messages_")]

    # Also check if there's a non-rolling messages collection
    if "messages" in all_collections:
        message_collections.append("messages")

    # Calculate message counts per project
    for project in projects:
        project_id = project["_id"]
        total_messages = 0

        # Count messages across all message collections
        for coll_name in message_collections:
            count = await db[coll_name].count_documents({"project_id": project_id})
            total_messages += count

        # Update the message count in stats
        project["stats"]["message_count"] = total_messages

    # Convert BSON types for JSON serialization
    projects = convert_bson_types(projects)

    # Get total count
    total = await db.projects.count_documents({})

    return {"items": projects, "total": total, "skip": skip, "limit": limit}


# Rolling Collections Monitoring Endpoints


@router.get("/collections/stats")
async def get_collections_statistics(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """Get statistics about rolling message collections."""
    rolling_service = RollingMessageService(db)
    metrics = await rolling_service.get_storage_metrics()

    # Add additional insights
    collection_names = list(metrics["collections"].keys())

    # Calculate growth trends if we have multiple collections
    monthly_growth = []
    if len(collection_names) > 1:
        sorted_collections = sorted(collection_names)
        for i in range(1, len(sorted_collections)):
            prev_docs = metrics["collections"][sorted_collections[i - 1]]["documents"]
            curr_docs = metrics["collections"][sorted_collections[i]]["documents"]
            if prev_docs > 0:
                growth_rate = ((curr_docs - prev_docs) / prev_docs) * 100
            else:
                growth_rate = 100 if curr_docs > 0 else 0

            monthly_growth.append(
                {
                    "month": sorted_collections[i],
                    "growth_rate": round(growth_rate, 2),
                    "documents": curr_docs,
                }
            )

    return {
        "metrics": metrics,
        "collection_count": len(collection_names),
        "monthly_growth": monthly_growth,
        "average_collection_size_mb": (
            round(metrics["total_size_mb"] / len(collection_names), 2)
            if collection_names
            else 0
        ),
        "status": "healthy" if metrics["total_documents"] > 0 else "empty",
    }


@router.post("/collections/cleanup")
async def cleanup_empty_collections(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """Remove empty message collections."""
    rolling_service = RollingMessageService(db)
    dropped_collections = await rolling_service.cleanup_empty_collections()

    return {
        "message": f"Cleaned up {len(dropped_collections)} empty collections",
        "dropped_collections": dropped_collections,
    }


@router.get("/collections/list")
async def list_message_collections(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """List all message collections with detailed information."""
    collections = await db.list_collection_names()
    message_collections = [c for c in collections if c.startswith("messages_")]

    collection_details = []
    for coll_name in sorted(message_collections):
        stats = await db.command("collStats", coll_name)

        # Get date range for collection
        sample = await db[coll_name].find_one({}, {"timestamp": 1})

        collection_details.append(
            {
                "name": coll_name,
                "document_count": stats.get("count", 0),
                "size_mb": round(stats.get("size", 0) / 1024 / 1024, 2),
                "avg_doc_size": stats.get("avgObjSize", 0),
                "index_count": len(stats.get("indexDetails", {})),
                "index_size_mb": round(stats.get("totalIndexSize", 0) / 1024 / 1024, 2),
                "oldest_message": sample.get("timestamp") if sample else None,
            }
        )

    return {
        "collections": collection_details,
        "total_collections": len(collection_details),
        "total_documents": sum(c["document_count"] for c in collection_details),
        "total_size_mb": sum(c["size_mb"] for c in collection_details),
    }


@router.post("/collections/migrate")
async def migrate_messages_to_rolling_collections(
    limit: int = Query(1000, description="Number of messages to migrate per batch"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Migrate existing messages from single collection to rolling collections.
    This endpoint helps with the transition to the new rolling collections architecture.
    """
    rolling_service = RollingMessageService(db)

    # Check if old messages collection exists
    collections = await db.list_collection_names()
    if "messages" not in collections:
        return {"message": "No legacy messages collection found", "migrated": 0}

    # Get a batch of messages from the old collection
    old_messages = await db.messages.find({}).limit(limit).to_list(limit)

    if not old_messages:
        return {"message": "No messages to migrate", "migrated": 0}

    # Migrate messages
    migrated_count = 0
    failed_count = 0

    for msg in old_messages:
        try:
            # Remove _id to let MongoDB generate new one
            msg_copy = msg.copy()
            original_id = msg_copy.pop("_id")

            # Insert into rolling collection
            await rolling_service.insert_message(msg_copy)

            # Delete from old collection
            await db.messages.delete_one({"_id": original_id})

            migrated_count += 1
        except Exception as e:
            failed_count += 1
            # Log error but continue migration
            import logging

            logging.error(f"Failed to migrate message {msg.get('uuid')}: {e}")

    # Check remaining messages
    remaining = await db.messages.count_documents({})

    return {
        "message": "Migration batch completed",
        "migrated": migrated_count,
        "failed": failed_count,
        "remaining_in_old_collection": remaining,
        "migration_complete": remaining == 0,
    }
