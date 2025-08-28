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
from app.models.user import UserInDB, UserRole
from app.schemas.oidc import (
    OIDCSettingsResponse,
    OIDCSettingsUpdate,
    OIDCTestConnectionRequest,
    OIDCTestConnectionResponse,
)
from app.services.oidc_service import oidc_service
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


@router.post("/users/{user_id}/change-role")
async def change_user_role(
    user_id: str,
    new_role: UserRole,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> Dict[str, Any]:
    """Change a user's role."""
    user_service = UserService(db)
    from app.models.user import UserUpdate

    user = await user_service.update_user(user_id, UserUpdate(role=new_role))

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

    # Aggregation pipeline to join projects with users
    pipeline: List[Dict[str, Any]] = [
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "owner",
            }
        },
        {"$unwind": {"path": "$owner", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id": 1,
                "name": 1,
                "path": 1,
                "createdAt": 1,
                "updatedAt": 1,
                "stats": 1,
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

    # Get projects with owners
    projects = await db.projects.aggregate(pipeline).to_list(None)

    # Convert BSON types for JSON serialization
    projects = convert_bson_types(projects)

    # Get total count
    total = await db.projects.count_documents({})

    return {"items": projects, "total": total, "skip": skip, "limit": limit}
