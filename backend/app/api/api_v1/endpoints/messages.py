"""Messages API endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_messages():
    """List all messages."""
    # Placeholder - to be implemented in Task 10
    return {"message": "Messages endpoint - coming soon"}


@router.get("/{message_id}")
async def get_message(message_id: str):
    """Get a specific message."""
    # Placeholder - to be implemented in Task 10
    return {"message": f"Message {message_id} endpoint - coming soon"}