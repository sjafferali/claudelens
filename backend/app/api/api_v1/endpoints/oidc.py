"""OIDC authentication endpoints."""

from typing import Any, Dict

from fastapi import Depends, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_db
from app.core.custom_router import APIRouter
from app.models.user import UserInDB
from app.services.auth import AuthService
from app.services.oidc_service import oidc_service

router = APIRouter()


@router.get("/login")
async def oidc_login(
    request: Request, db: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """Initiate OIDC authentication flow."""
    # Load and check OIDC configuration
    await oidc_service.load_settings(db)
    if not oidc_service.is_configured():
        raise HTTPException(
            status_code=503, detail="OIDC authentication is not configured"
        )

    # Build redirect URI
    redirect_uri = str(request.url_for("oidc_callback"))

    # Initiate OIDC login flow
    authorization_url = await oidc_service.initiate_login(request, redirect_uri)

    return {"authorization_url": authorization_url}


@router.get("/callback")
async def oidc_callback(
    request: Request, db: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """Handle OIDC callback and authenticate user."""
    # Load OIDC configuration
    await oidc_service.load_settings(db)
    if not oidc_service.is_configured():
        raise HTTPException(
            status_code=503, detail="OIDC authentication is not configured"
        )

    # Handle callback and get or create user
    user: UserInDB = await oidc_service.handle_callback(request, db)

    # Create JWT token for the authenticated user
    token_data = {
        "sub": user.username,
        "user_id": str(user.id),
        "role": user.role.value,
    }
    access_token = AuthService.create_access_token(data=token_data)

    # Return user info and token
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "auth_method": user.auth_method,
        },
    }


@router.post("/logout")
async def oidc_logout(request: Request) -> Dict[str, str]:
    """Logout from OIDC session."""
    await oidc_service.logout(request)
    return {"message": "Successfully logged out"}


@router.get("/status")
async def oidc_status(db: AsyncIOMotorDatabase = Depends(get_db)) -> Dict[str, Any]:
    """Get OIDC configuration status."""
    await oidc_service.load_settings(db)

    return {
        "enabled": oidc_service.is_configured(),
        "configured": oidc_service._settings is not None,
        "provider": oidc_service._settings.discovery_endpoint
        if oidc_service._settings
        else None,
    }
