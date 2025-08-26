"""Admin dashboard endpoints."""

import asyncio
from typing import Any, Dict, List, Mapping, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_db, require_admin
from app.models.user import UserInDB, UserRole
from app.services.storage_metrics import StorageMetricsService
from app.services.user import UserService

router = APIRouter()


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

    return {
        "system_metrics": system_metrics,
        "top_users": top_users,
    }


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
        activity.append(
            {
                "type": "session",
                "timestamp": session.get("startedAt"),
                "user": user.get("username") if user else "Unknown",
                "session_id": str(session["_id"]),
                "message_count": session.get("messageCount", 0),
                "total_cost": session.get("totalCost", 0),
            }
        )

    # Sort by timestamp
    activity.sort(key=lambda x: x["timestamp"], reverse=True)

    return activity[:limit]
