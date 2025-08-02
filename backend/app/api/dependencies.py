"""API dependencies."""
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.security import verify_api_key


async def get_db() -> AsyncIOMotorDatabase:
    """Get database dependency."""
    return await get_database()


async def verify_api_key_header(
    x_api_key: Annotated[str | None, Header()] = None
) -> str:
    """Verify API key from header."""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if not verify_api_key(x_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return x_api_key


# Common dependencies
CommonDeps = Annotated[AsyncIOMotorDatabase, Depends(get_db)]
AuthDeps = Annotated[str, Depends(verify_api_key_header)]