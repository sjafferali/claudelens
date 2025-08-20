"""API dependencies."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.security import verify_api_key


async def get_db() -> AsyncIOMotorDatabase:
    """Get database dependency."""
    return await get_database()


async def verify_api_key_header(
    request: Request,
    x_api_key: Annotated[str | None, Header()] = None,
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
            # Return a special identifier for localhost requests
            return "localhost"

    # For non-localhost requests, require API key
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not verify_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    return x_api_key


# Common dependencies
CommonDeps = Annotated[AsyncIOMotorDatabase, Depends(get_db)]
AuthDeps = Annotated[str, Depends(verify_api_key_header)]
