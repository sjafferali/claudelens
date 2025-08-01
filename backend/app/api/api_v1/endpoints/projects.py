"""Projects API endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_projects():
    """List all projects."""
    # Placeholder - to be implemented in Task 10
    return {"message": "Projects endpoint - coming soon"}


@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get a specific project."""
    # Placeholder - to be implemented in Task 10
    return {"message": f"Project {project_id} endpoint - coming soon"}