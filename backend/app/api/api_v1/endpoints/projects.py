"""Projects API endpoints."""

from bson import ObjectId
from fastapi import HTTPException, Query

from app.api.dependencies import CommonDeps
from app.core.custom_router import APIRouter
from app.core.exceptions import NotFoundError
from app.schemas.common import PaginatedResponse
from app.schemas.project import Project, ProjectCreate, ProjectUpdate, ProjectWithStats
from app.services.project import ProjectService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ProjectWithStats])
async def list_projects(
    db: CommonDeps,
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
async def get_project(project_id: str, db: CommonDeps) -> ProjectWithStats:
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
async def create_project(project: ProjectCreate, db: CommonDeps) -> Project:
    """Create a new project.

    Projects are usually created automatically during ingestion,
    but this endpoint allows manual creation.
    """
    service = ProjectService(db)

    # Check if project with same path exists
    existing = await service.get_project_by_path(project.path)
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Project with path '{project.path}' already exists"
        )

    created = await service.create_project(project)
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
    project_id: str, update: ProjectUpdate, db: CommonDeps
) -> Project:
    """Update a project's metadata."""
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")

    service = ProjectService(db)
    updated = await service.update_project(ObjectId(project_id), update)

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


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    db: CommonDeps,
    cascade: bool = Query(False, description="Delete all associated data"),
) -> None:
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
async def get_project_stats(project_id: str, db: CommonDeps) -> dict:
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
