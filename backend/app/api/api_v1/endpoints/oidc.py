"""OIDC authentication endpoints."""

import logging
from typing import Any, Dict

from fastapi import Depends, HTTPException, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_db
from app.core.custom_router import APIRouter
from app.models.user import UserInDB
from app.services.auth import AuthService
from app.services.oidc_service import oidc_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/login")
async def oidc_login(
    request: Request, db: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """Initiate OIDC authentication flow."""
    logger.info("OIDC login endpoint called")
    logger.debug(f"Request URL: {request.url}")
    logger.debug(f"Request headers: {dict(request.headers)}")

    # Load and check OIDC configuration
    await oidc_service.load_settings(db)
    if not oidc_service.is_configured():
        logger.error("OIDC authentication is not configured")
        raise HTTPException(
            status_code=503, detail="OIDC authentication is not configured"
        )

    # Build redirect URI - should point to the frontend callback route
    # Extract the origin from the request headers (typically from Referer or Origin)
    origin = request.headers.get("origin") or request.headers.get("referer", "")
    if origin:
        # Remove trailing slash and path if present
        origin = origin.rstrip("/").split("/login")[0].split("/api")[0]
        redirect_uri = f"{origin}/auth/oidc/callback"
    else:
        # Fallback: construct from request URL, replacing backend port with frontend port
        base_url = str(request.base_url).rstrip("/")
        # Common development setup: backend on 8001, frontend on 5173
        if ":8001" in base_url or ":8080" in base_url:
            frontend_url = base_url.replace(":8001", ":5173").replace(":8080", ":5173")
            redirect_uri = f"{frontend_url}/auth/oidc/callback"
        else:
            # Production: assume same domain
            redirect_uri = f"{base_url}/auth/oidc/callback"

    logger.info(f"Using redirect URI: {redirect_uri}")

    # Initiate OIDC login flow
    authorization_url = await oidc_service.initiate_login(request, redirect_uri)
    logger.info(f"Returning authorization URL: {authorization_url[:100]}...")

    return {"authorization_url": authorization_url}


@router.post("/callback")
async def oidc_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from OIDC provider"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    redirect_uri: str = Query(
        ..., description="Redirect URI used in authorization request"
    ),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Dict[str, Any]:
    """Handle OIDC callback - exchange authorization code for token.

    This endpoint is called by the frontend after the OIDC provider
    redirects back with an authorization code.
    """
    logger.info("OIDC callback endpoint called")
    logger.debug(
        f"Code: {code[:8]}..., State: {state[:8]}..., Redirect URI: {redirect_uri}"
    )

    import time

    start_time = time.time()

    # Load OIDC configuration
    logger.info("Loading OIDC settings")
    await oidc_service.load_settings(db)
    logger.info(f"Settings loaded, time elapsed: {time.time() - start_time:.2f}s")

    if not oidc_service.is_configured():
        logger.error("OIDC authentication is not configured during callback")
        raise HTTPException(
            status_code=503, detail="OIDC authentication is not configured"
        )

    # Handle callback and get or create user
    logger.info("Processing OIDC callback - exchanging code for token")
    exchange_start = time.time()
    user: UserInDB = await oidc_service.exchange_code_for_token(
        code=code, state=state, redirect_uri=redirect_uri, request=request, db=db
    )
    logger.info(
        f"User authenticated: {user.username}, exchange took: {time.time() - exchange_start:.2f}s"
    )

    # Create JWT token for the authenticated user
    token_data = {
        "sub": user.username,
        "user_id": str(user.id),
        "role": user.role.value,
    }
    access_token = AuthService.create_access_token(data=token_data)
    logger.info(f"Created access token for user: {user.username}")

    # Return user info and token
    result = {
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
    logger.info(
        f"OIDC callback successful for user: {user.username}, total time: {time.time() - start_time:.2f}s"
    )
    return result


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


@router.get("/test-metadata")
async def test_metadata(db: AsyncIOMotorDatabase = Depends(get_db)) -> Dict[str, Any]:
    """Test OIDC metadata fetching."""
    import time

    await oidc_service.load_settings(db)
    if not oidc_service._settings:
        raise HTTPException(status_code=503, detail="OIDC not configured")

    start_time = time.time()
    metadata = await oidc_service._get_cached_metadata()
    elapsed = time.time() - start_time

    if not metadata:
        raise HTTPException(status_code=503, detail="Failed to fetch metadata")

    return {
        "success": True,
        "fetch_time": elapsed,
        "token_endpoint": metadata.get("token_endpoint"),
        "userinfo_endpoint": metadata.get("userinfo_endpoint"),
        "issuer": metadata.get("issuer"),
    }
