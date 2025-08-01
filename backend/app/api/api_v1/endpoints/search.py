"""Search API endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def search():
    """Search messages and sessions."""
    # Placeholder - to be implemented in Task 11
    return {"message": "Search endpoint - coming soon"}


@router.post("/")
async def advanced_search():
    """Advanced search with filters."""
    # Placeholder - to be implemented in Task 11
    return {"message": "Advanced search endpoint - coming soon"}