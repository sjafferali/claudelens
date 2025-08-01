"""Sessions API endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_sessions():
    """List all sessions."""
    # Placeholder - to be implemented in Task 10
    return {"message": "Sessions endpoint - coming soon"}


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Get a specific session."""
    # Placeholder - to be implemented in Task 10
    return {"message": f"Session {session_id} endpoint - coming soon"}