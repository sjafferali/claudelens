"""User management endpoints."""


from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_db, require_admin
from app.models.user import UserCreate, UserInDB, UserResponse, UserRole, UserUpdate
from app.schemas.common import PaginatedResponse
from app.services.user import UserService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: str | None = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> PaginatedResponse[UserResponse]:
    """List all users (admin only)."""
    user_service = UserService(db)
    role_enum: Optional[UserRole] = UserRole(role) if role else None
    users, total = await user_service.list_users(skip=skip, limit=limit, role=role_enum)

    # Convert to response models
    user_responses = []
    for user in users:
        user_responses.append(
            UserResponse(
                id=str(user.id),
                email=user.email,
                username=user.username,
                role=user.role,
                created_at=user.created_at,
                updated_at=user.updated_at,
                project_count=user.project_count,
                session_count=user.session_count,
                message_count=user.message_count,
                total_disk_usage=user.total_disk_usage,
                api_key_count=len(user.api_keys),
            )
        )

    return PaginatedResponse(
        items=user_responses,
        total=total,
        skip=skip,
        limit=limit,
        has_more=skip + limit < total,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> UserResponse:
    """Get a specific user (admin only)."""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at,
        project_count=user.project_count,
        session_count=user.session_count,
        message_count=user.message_count,
        total_disk_usage=user.total_disk_usage,
        api_key_count=len(user.api_keys),
    )


@router.post("/", response_model=dict)
async def create_user(
    user_data: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> dict:
    """Create a new user (admin only)."""
    user_service = UserService(db)

    try:
        user, api_key = await user_service.create_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "user": UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
            project_count=0,
            session_count=0,
            message_count=0,
            total_disk_usage=0,
            api_key_count=1,
        ),
        "api_key": api_key,  # Only shown once!
    }


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> UserResponse:
    """Update a user (admin only)."""
    user_service = UserService(db)
    user = await user_service.update_user(user_id, user_update)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at,
        project_count=user.project_count,
        session_count=user.session_count,
        message_count=user.message_count,
        total_disk_usage=user.total_disk_usage,
        api_key_count=len(user.api_keys),
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> dict:
    """Delete a user and all their data (admin only)."""
    user_service = UserService(db)
    success = await user_service.delete_user(user_id)

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}


@router.post("/{user_id}/api-keys")
async def generate_api_key(
    user_id: str,
    key_name: str = Query(..., description="Name for the new API key"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> dict:
    """Generate a new API key for a user (admin only)."""
    user_service = UserService(db)
    api_key = await user_service.generate_new_api_key(user_id, key_name)

    if not api_key:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "api_key": api_key,  # Only shown once!
        "message": "API key generated successfully. Store it securely as it won't be shown again.",
    }


@router.delete("/{user_id}/api-keys/{key_hash}")
async def revoke_api_key(
    user_id: str,
    key_hash: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin_user: UserInDB = Depends(require_admin),
) -> dict:
    """Revoke an API key (admin only)."""
    user_service = UserService(db)
    success = await user_service.revoke_api_key(user_id, key_hash)

    if not success:
        raise HTTPException(status_code=404, detail="User or API key not found")

    return {"message": "API key revoked successfully"}
