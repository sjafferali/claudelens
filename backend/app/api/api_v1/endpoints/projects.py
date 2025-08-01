"""Projects API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.api.dependencies import CommonDeps
from app.schemas.project import Project, ProjectCreate, ProjectUpdate, ProjectWithStats
from app.schemas.common import PaginatedResponse
from app.services.project import ProjectService
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ProjectWithStats])
async def list_projects(
    db: CommonDeps,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search in project names"),
    sort_by: str = Query("updated_at", regex="^(name|created_at|updated_at|message_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
) -> PaginatedResponse[ProjectWithStats]:
    """List all projects with pagination and filtering.
    
    Returns projects with their statistics including message and session counts.
    """
    service = ProjectService(db)
    
    # Build filter
    filter_dict = {}
    if search:
        filter_dict["$text"] = {"$search": search}
    
    # Get projects
    projects, total = await service.list_projects(
        filter_dict=filter_dict,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return PaginatedResponse(
        items=projects,
        total=total,
        skip=skip,
        limit=limit,
        has_more=skip + limit < total
    )


@router.get("/{project_id}", response_model=ProjectWithStats)
async def get_project(
    project_id: str,
    db: CommonDeps
) -> ProjectWithStats:
    """Get a specific project by ID.
    
    Returns the project with detailed statistics.
    """
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    service = ProjectService(db)
    project = await service.get_project(ObjectId(project_id))
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    return project


@router.post("/", response_model=Project, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: CommonDeps
) -> Project:
    """Create a new project.
    
    Projects are usually created automatically during ingestion,
    but this endpoint allows manual creation.
    """
    service = ProjectService(db)
    
    # Check if project with same path exists
    existing = await service.get_project_by_path(project.path)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Project with path '{project.path}' already exists"
        )
    
    created = await service.create_project(project)
    return created


@router.patch("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    update: ProjectUpdate,
    db: CommonDeps
) -> Project:
    """Update a project's metadata."""
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    service = ProjectService(db)
    updated = await service.update_project(ObjectId(project_id), update)
    
    if not updated:
        raise NotFoundError("Project", project_id)
    
    return updated


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    db: CommonDeps,
    cascade: bool = Query(False, description="Delete all associated data")
):
    """Delete a project.
    
    If cascade=true, also deletes all sessions and messages.
    Otherwise, only deletes the project metadata.
    """
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    service = ProjectService(db)
    deleted = await service.delete_project(ObjectId(project_id), cascade=cascade)
    
    if not deleted:
        raise NotFoundError("Project", project_id)


@router.get("/{project_id}/stats")
async def get_project_stats(
    project_id: str,
    db: CommonDeps
) -> dict:
    """Get detailed statistics for a project.
    
    Returns message counts by type, cost breakdown, and activity timeline.
    """
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    service = ProjectService(db)
    stats = await service.get_project_statistics(ObjectId(project_id))
    
    if not stats:
        raise NotFoundError("Project", project_id)
    
    return stats