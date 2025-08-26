"""Projects API endpoints."""

from bson import ObjectId
from fastapi import HTTPException, Query

from app.api.dependencies import AuthDeps, CommonDeps
from app.core.custom_router import APIRouter
from app.core.exceptions import NotFoundError
from app.schemas.common import PaginatedResponse
from app.schemas.project import Project, ProjectCreate, ProjectUpdate, ProjectWithStats
from app.services.project import ProjectService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ProjectWithStats])
async def list_projects(
    db: CommonDeps,
    user_id: AuthDeps,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="Search in project names"),
    sort_by: str = Query(
        "updated_at", pattern="^(name|created_at|updated_at|message_count)$"
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
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
        user_id,
        filter_dict=filter_dict,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return PaginatedResponse(
        items=projects,
        total=total,
        skip=skip,
        limit=limit,
        has_more=skip + limit < total,
    )


@router.get("/{project_id}", response_model=ProjectWithStats)
async def get_project(
    project_id: str, db: CommonDeps, user_id: AuthDeps
) -> ProjectWithStats:
    """Get a specific project by ID.

    Returns the project with detailed statistics.
    """
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")

    service = ProjectService(db)
    project = await service.get_project(user_id, ObjectId(project_id))

    if not project:
        raise NotFoundError("Project", project_id)

    return project


@router.post("/", response_model=Project, status_code=201)
async def create_project(
    project: ProjectCreate, db: CommonDeps, user_id: AuthDeps
) -> Project:
    """Create a new project.

    Projects are usually created automatically during ingestion,
    but this endpoint allows manual creation.
    """
    service = ProjectService(db)

    # Check if project with same path exists
    existing = await service.get_project_by_path(user_id, project.path)
    if existing:
        # Return existing project instead of 409 error
        return Project(
            _id=str(existing.id),
            name=existing.name,
            description=existing.description,
            path=existing.path,
            createdAt=existing.created_at,
            updatedAt=existing.updated_at,
        )

    created = await service.create_project(user_id, project)
    return Project(
        _id=str(created.id),
        name=created.name,
        description=created.description,
        path=created.path,
        createdAt=created.created_at,
        updatedAt=created.updated_at,
    )


@router.patch("/{project_id}", response_model=Project)
async def update_project(
    project_id: str, update: ProjectUpdate, db: CommonDeps, user_id: AuthDeps
) -> Project:
    """Update a project's metadata."""
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")

    service = ProjectService(db)
    updated = await service.update_project(user_id, ObjectId(project_id), update)

    if not updated:
        raise NotFoundError("Project", project_id)

    return Project(
        _id=str(updated.id),
        name=updated.name,
        description=updated.description,
        path=updated.path,
        createdAt=updated.created_at,
        updatedAt=updated.updated_at,
    )


@router.delete("/{project_id}", status_code=200)
async def delete_project(
    project_id: str,
    db: CommonDeps,
    user_id: AuthDeps,
    cascade: bool = Query(
        True,
        description="Delete all associated data (always enabled to prevent orphaned data)",
    ),
) -> dict:
    """Delete a project.

    Always deletes all associated sessions and messages to prevent orphaned data.
    The cascade parameter is kept for backward compatibility but is now always treated as True.

    For large projects, deletion happens asynchronously with progress updates via WebSocket.
    """
    import asyncio

    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")

    service = ProjectService(db)

    # Check if project exists
    project = await service.get_project(user_id, ObjectId(project_id))
    if not project:
        raise NotFoundError("Project", project_id)

    # For projects with many messages, use async deletion
    if project.stats and project.stats.message_count > 1000:
        # Start async deletion in background (always cascade)
        asyncio.create_task(
            service.delete_project_async(user_id, ObjectId(project_id), cascade=True)
        )

        return {
            "message": "Deletion started",
            "async": True,
            "project_id": project_id,
            "estimated_messages": project.stats.message_count,
            "note": "Progress updates will be sent via WebSocket",
        }
    else:
        # Use synchronous deletion for smaller projects (always cascade)
        deleted = await service.delete_project(
            user_id, ObjectId(project_id), cascade=True
        )

        if not deleted:
            raise NotFoundError("Project", project_id)

        return {
            "message": "Project and all associated data deleted successfully",
            "async": False,
            "project_id": project_id,
        }


@router.get("/{project_id}/stats")
async def get_project_stats(project_id: str, db: CommonDeps, user_id: AuthDeps) -> dict:
    """Get detailed statistics for a project.

    Returns message counts by type, cost breakdown, and activity timeline.
    """
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")

    service = ProjectService(db)
    stats = await service.get_project_statistics(user_id, ObjectId(project_id))

    if not stats:
        raise NotFoundError("Project", project_id)

    return stats
