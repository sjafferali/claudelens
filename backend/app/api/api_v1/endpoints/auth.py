"""Authentication endpoints for login/logout."""

from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.api.dependencies import get_db
from app.models.user import UserInDB
from app.services.auth import AuthService
from app.services.storage_metrics import StorageMetricsService
from app.services.user import UserService

router = APIRouter()

# OAuth2 scheme for JWT bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class Token(BaseModel):
    """JWT token response model."""

    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


class UserInfo(BaseModel):
    """User information response model."""

    id: str
    username: str
    email: str
    role: str


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Token:
    """Login endpoint for username/password authentication."""
    # Find user by username or email
    user_doc = await db.users.find_one(
        {"$or": [{"username": form_data.username}, {"email": form_data.username}]}
    )

    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user has a password (some users might only have API keys)
    if not user_doc.get("password_hash"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account requires API key authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not AuthService.verify_password(form_data.password, user_doc["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user_doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    # Create access token
    access_token = AuthService.create_access_token(
        data={
            "sub": user_doc["username"],
            "user_id": str(user_doc["_id"]),
            "role": user_doc.get("role", "user"),
        }
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=UserInfo)
async def register(
    username: str,
    email: str,
    password: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserInfo:
    """Register a new user with username/password."""
    # Check if user already exists
    existing = await db.users.find_one(
        {"$or": [{"email": email}, {"username": username}]}
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists",
        )

    # Hash password
    password_hash = AuthService.hash_password(password)

    # Create user
    from datetime import UTC, datetime

    user_doc = {
        "email": email,
        "username": username,
        "password_hash": password_hash,
        "role": "user",  # Default role
        "api_keys": [],
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "is_active": True,
        "project_count": 0,
        "session_count": 0,
        "message_count": 0,
        "total_disk_usage": 0,
    }

    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    return UserInfo(
        id=str(user_doc["_id"]),
        username=str(user_doc["username"]),
        email=str(user_doc["email"]),
        role=str(user_doc["role"]),
    )


async def get_current_user_from_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserInDB:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    token_data = AuthService.decode_access_token(token)
    if token_data is None:
        raise credentials_exception

    # Get user from database
    user_service = UserService(db)
    user = await user_service.get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception

    return user


@router.get("/me", response_model=UserInfo)
async def get_current_user(
    current_user: UserInDB = Depends(get_current_user_from_token),
) -> UserInfo:
    """Get current user information."""
    return UserInfo(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
    )


class ChangePasswordRequest(BaseModel):
    """Change password request model."""

    current_password: str
    new_password: str


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserInDB = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """Change the current user's password."""
    # Verify current password
    if not current_user.password_hash or not AuthService.verify_password(
        request.current_password, current_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Hash new password
    new_password_hash = AuthService.hash_password(request.new_password)

    # Update user's password
    from datetime import UTC, datetime

    result = await db.users.update_one(
        {"_id": current_user.id},
        {
            "$set": {
                "password_hash": new_password_hash,
                "updated_at": datetime.now(UTC),
            }
        },
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )

    return {"message": "Password changed successfully"}


class ApiKeyResponse(BaseModel):
    """API key information."""

    name: str
    hash: str
    created_at: str


@router.get("/me/api-keys", response_model=list[ApiKeyResponse])
async def get_my_api_keys(
    current_user: UserInDB = Depends(get_current_user_from_token),
) -> list[ApiKeyResponse]:
    """Get the current user's API keys."""
    return [
        ApiKeyResponse(
            name=key.name,
            hash=key.key_hash,
            created_at=key.created_at.isoformat() if key.created_at else "",
        )
        for key in current_user.api_keys
    ]


@router.post("/me/api-keys")
async def generate_my_api_key(
    key_name: str,
    current_user: UserInDB = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """Generate a new API key for the current user."""
    user_service = UserService(db)
    api_key = await user_service.generate_new_api_key(str(current_user.id), key_name)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate API key",
        )

    return {
        "api_key": api_key,
        "message": "API key generated successfully. Store it securely as it won't be shown again.",
    }


@router.delete("/me/api-keys/{key_hash}")
async def revoke_my_api_key(
    key_hash: str,
    current_user: UserInDB = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """Revoke one of the current user's API keys."""
    user_service = UserService(db)
    success = await user_service.revoke_api_key(str(current_user.id), key_hash)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return {"message": "API key revoked successfully"}


@router.get("/me/usage", response_model=Dict[str, Any])
async def get_my_usage_metrics(
    current_user: UserInDB = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Dict[str, Any]:
    """Get current user's usage metrics including storage and resource counts."""
    storage_service = StorageMetricsService(db)

    # Get storage metrics
    metrics = await storage_service.calculate_user_metrics(str(current_user.id))

    # Get resource counts directly from database
    user_projects = await db.projects.find(
        {"user_id": current_user.id}, {"_id": 1}
    ).to_list(None)
    project_ids = [p["_id"] for p in user_projects]

    project_count = len(project_ids)

    # Count sessions for user's projects
    session_count = 0
    if project_ids:
        session_count = await db.sessions.count_documents(
            {"projectId": {"$in": project_ids}}
        )

    # Count messages across rolling collections for user's sessions
    message_count = 0
    if project_ids:
        session_ids = await db.sessions.distinct(
            "sessionId", {"projectId": {"$in": project_ids}}
        )

        if session_ids:
            # Count across rolling collections
            all_collections = await db.list_collection_names()
            message_collections = [
                c for c in all_collections if c.startswith("messages_")
            ]

            if message_collections:
                for coll_name in message_collections:
                    count = await db[coll_name].count_documents(
                        {"sessionId": {"$in": session_ids}}
                    )
                    message_count += count
            else:
                # Fallback to single messages collection
                message_count = await db.messages.count_documents(
                    {"sessionId": {"$in": session_ids}}
                )

    return {
        "storage": {
            "total_bytes": metrics.get("total_disk_usage", 0),
            "breakdown": {
                "sessions": metrics.get("sessions", {}).get("total_size", 0),
                "messages": metrics.get("messages", {}).get("total_size", 0),
                "projects": metrics.get("projects", {}).get("total_size", 0),
            },
        },
        "counts": {
            "projects": project_count,
            "sessions": session_count,
            "messages": message_count,
        },
        "details": {
            "sessions": metrics.get("sessions", {}),
            "messages": metrics.get("messages", {}),
            "projects": metrics.get("projects", {}),
        },
    }
