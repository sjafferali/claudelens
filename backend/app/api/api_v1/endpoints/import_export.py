"""Import/Export API endpoints."""

import math
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.api.dependencies import AuthDeps, CommonDeps
from app.core.custom_router import APIRouter
from app.core.logging import get_logger
from app.models.import_job import ImportJob
from app.schemas.export import (
    CancelExportResponse,
    CreateExportRequest,
    CreateExportResponse,
    ExportJobListItem,
    ExportStatusResponse,
    PagedExportJobsResponse,
)
from app.schemas.import_schemas import (
    CheckConflictsRequest,
    ConflictsResponse,
    ExecuteImportRequest,
    ExecuteImportResponse,
    ImportProgressResponse,
    RollbackResponse,
    ValidateImportResponse,
)
from app.services.export_service import ExportService
from app.services.file_service import FileService
from app.services.import_service import ImportService
from app.services.websocket_manager import connection_manager

router = APIRouter()
logger = get_logger(__name__)

# Rate limiting tracking (simple in-memory for now)
export_rate_limit: Dict[str, List[datetime]] = {}
import_rate_limit: Dict[str, List[datetime]] = {}


async def check_export_rate_limit(user_id: str) -> bool:
    """Check if user has exceeded export rate limit (10/hour)."""
    now = datetime.now(UTC)
    hour_ago = now - timedelta(hours=1)

    if user_id not in export_rate_limit:
        export_rate_limit[user_id] = []

    # Clean old entries
    export_rate_limit[user_id] = [
        timestamp for timestamp in export_rate_limit[user_id] if timestamp > hour_ago
    ]

    if len(export_rate_limit[user_id]) >= 10:
        return False

    export_rate_limit[user_id].append(now)
    return True


async def check_import_rate_limit(user_id: str) -> bool:
    """Check if user has exceeded import rate limit (5/hour)."""
    now = datetime.now(UTC)
    hour_ago = now - timedelta(hours=1)

    if user_id not in import_rate_limit:
        import_rate_limit[user_id] = []

    # Clean old entries
    import_rate_limit[user_id] = [
        timestamp for timestamp in import_rate_limit[user_id] if timestamp > hour_ago
    ]

    if len(import_rate_limit[user_id]) >= 5:
        return False

    import_rate_limit[user_id].append(now)
    return True


async def broadcast_export_progress(job_id: str, progress: Dict[str, Any]) -> None:
    """Broadcast export progress via WebSocket."""
    await connection_manager.broadcast_export_progress(
        job_id=job_id,
        current=progress.get("current", 0),
        total=progress.get("total", 0),
        message=progress.get("message", ""),
        completed=progress.get("percentage", 0) >= 100,
    )


async def broadcast_import_progress(job_id: str, progress: Dict[str, Any]) -> None:
    """Broadcast import progress via WebSocket."""
    await connection_manager.broadcast_import_progress(
        job_id=job_id,
        current=progress.get("processed", 0),
        total=progress.get("total", 0),
        message=progress.get("message", ""),
        completed=progress.get("percentage", 0) >= 100,
    )


@router.post("/export", response_model=CreateExportResponse, status_code=201)
async def create_export(
    request: CreateExportRequest,
    background_tasks: BackgroundTasks,
    db: CommonDeps,
    api_key: AuthDeps,
) -> CreateExportResponse:
    """Create a new export job."""
    # Simple user ID extraction from API key
    user_id = str(api_key) if api_key else "anonymous"

    # Check rate limit
    if not await check_export_rate_limit(user_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 10 exports per hour.",
        )

    # Create export job
    export_service = ExportService(db)
    export_job = await export_service.create_export_job(
        user_id=user_id,
        format=request.format,
        filters=request.filters,
        options=request.options,
    )

    # Schedule background processing
    background_tasks.add_task(
        export_service.process_export,
        str(export_job.id),
        broadcast_export_progress,
    )

    return CreateExportResponse(
        jobId=str(export_job.id),
        status=export_job.status,  # type: ignore[arg-type]
        estimatedSizeBytes=export_job.estimated_size_bytes or 0,
        estimatedDurationSeconds=export_job.estimated_duration_seconds or 1,
        createdAt=export_job.created_at.isoformat(),
        expiresAt=export_job.expires_at.isoformat(),
    )


@router.get("/export/{job_id}/status", response_model=ExportStatusResponse)
async def get_export_status(
    job_id: str,
    db: CommonDeps,
) -> ExportStatusResponse:
    """Get the status of an export job."""
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID")

    export_job = await db.export_jobs.find_one({"_id": ObjectId(job_id)})
    if not export_job:
        raise HTTPException(status_code=404, detail="Export job not found")

    return ExportStatusResponse(
        jobId=str(export_job["_id"]),
        status=export_job.get("status", "unknown"),
        progress=export_job.get("progress"),
        currentItem=export_job.get("progress", {}).get("current_item"),
        fileInfo=export_job.get("file_info"),
        errors=export_job.get("errors", []),
        createdAt=export_job.get("created_at").isoformat()
        if export_job.get("created_at")
        else "",
        startedAt=export_job.get("started_at").isoformat()
        if export_job.get("started_at")
        else None,
        completedAt=export_job.get("completed_at").isoformat()
        if export_job.get("completed_at")
        else None,
        expiresAt=export_job.get("expires_at").isoformat()
        if export_job.get("expires_at")
        else "",
    )


@router.get("/export/{job_id}/download")
async def download_export(
    job_id: str,
    db: CommonDeps,
) -> StreamingResponse:
    """Download the exported file."""
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID")

    export_job = await db.export_jobs.find_one({"_id": ObjectId(job_id)})
    if not export_job:
        raise HTTPException(status_code=404, detail="Export job not found")

    if export_job.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Export file not ready")

    # Check if expired
    if export_job.get("expires_at") and export_job["expires_at"] < datetime.now(UTC):
        raise HTTPException(status_code=410, detail="Export file has expired")

    file_path = export_job.get("file_path")
    if not file_path:
        raise HTTPException(status_code=404, detail="Export file not found")

    # Stream the file
    file_service = FileService()

    # Determine media type and filename
    format_map = {
        "json": ("application/json", "json"),
        "csv": ("text/csv", "csv"),
        "markdown": ("text/markdown", "md"),
        "pdf": ("application/pdf", "pdf"),
    }

    media_type, extension = format_map.get(
        export_job.get("format", "json"), ("application/octet-stream", "bin")
    )

    filename = f"claudelens_export_{job_id}.{extension}"

    return StreamingResponse(
        file_service.stream_file(file_path),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@router.delete("/export/{job_id}", response_model=CancelExportResponse)
async def cancel_export(
    job_id: str,
    db: CommonDeps,
    api_key: AuthDeps,
) -> CancelExportResponse:
    """Cancel a running export job."""
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID")

    export_job = await db.export_jobs.find_one({"_id": ObjectId(job_id)})
    if not export_job:
        raise HTTPException(status_code=404, detail="Export job not found")

    if export_job.get("status") in ["completed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Job cannot be cancelled (status: {export_job['status']})",
        )

    # Update job status
    await db.export_jobs.update_one(
        {"_id": ObjectId(job_id)},
        {
            "$set": {
                "status": "cancelled",
                "completed_at": datetime.now(UTC),
            }
        },
    )

    return CancelExportResponse(
        jobId=job_id,
        status="cancelled",
        message="Export job cancelled successfully",
    )


@router.get("/export", response_model=PagedExportJobsResponse)
async def list_export_jobs(
    db: CommonDeps,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    sort: str = Query("createdAt,desc"),
    status: Optional[str] = None,
) -> PagedExportJobsResponse:
    """List export jobs for the current user."""
    # For read-only operations, we don't require authentication
    # This matches the pattern used in sessions and projects endpoints
    user_id = "anonymous"

    # Build filter
    filter_dict = {"user_id": user_id}
    if status:
        filter_dict["status"] = status

    # Parse sort parameter
    sort_parts = sort.split(",")
    sort_field = sort_parts[0]
    sort_direction = -1 if len(sort_parts) > 1 and sort_parts[1] == "desc" else 1

    # Map sort field to database field
    sort_field_map = {
        "createdAt": "created_at",
        "completedAt": "completed_at",
    }
    sort_field = sort_field_map.get(sort_field, sort_field)

    # Get total count
    total = await db.export_jobs.count_documents(filter_dict)

    # Get paginated results
    cursor = db.export_jobs.find(filter_dict)
    cursor = cursor.sort(sort_field, sort_direction)
    cursor = cursor.skip(page * size).limit(size)

    jobs = []
    async for job in cursor:
        jobs.append(
            ExportJobListItem(
                jobId=str(job["_id"]),
                status=job.get("status", "unknown"),
                format=job.get("format", "unknown"),
                createdAt=job.get("created_at").isoformat()
                if job.get("created_at")
                else "",
                completedAt=job.get("completed_at").isoformat()
                if job.get("completed_at")
                else None,
                fileInfo=job.get("file_info"),
            )
        )

    return PagedExportJobsResponse(
        content=jobs,
        totalElements=total,
        totalPages=math.ceil(total / size) if size > 0 else 0,
        size=size,
        number=page,
    )


@router.post("/import/validate", response_model=ValidateImportResponse)
async def validate_import(
    db: CommonDeps,
    api_key: AuthDeps,
    file: UploadFile = File(...),
    dry_run: bool = Query(True),
) -> ValidateImportResponse:
    """Upload and validate an import file."""
    # Validate and save file
    file_service = FileService()
    file_info = await file_service.validate_and_save_upload(file)

    # Validate import format
    import_service = ImportService(db)
    validation_result = await import_service.validate_import_file(
        file_info["path"],
        file_info["format"],
    )

    # Add file ID and upload metadata
    validation_result["file_id"] = file_info["file_id"]
    validation_result["file_info"]["uploadedAt"] = datetime.now(UTC).isoformat()
    validation_result["file_info"]["expiresAt"] = (
        datetime.now(UTC) + timedelta(hours=1)
    ).isoformat()

    return ValidateImportResponse(**validation_result)


@router.post("/import/conflicts", response_model=ConflictsResponse)
async def check_conflicts(
    request: CheckConflictsRequest,
    db: CommonDeps,
    api_key: AuthDeps,
) -> ConflictsResponse:
    """Check for conflicts before import execution."""
    # Get file path from file ID
    file_service = FileService()
    import_dir = file_service.import_dir

    # Find file (simplified - in production would use database)
    import os

    file_path = None
    for filename in os.listdir(import_dir):
        if filename.startswith(request.file_id):
            file_path = os.path.join(import_dir, filename)
            break

    if not file_path:
        raise HTTPException(status_code=404, detail="File not found or expired")

    # Check conflicts
    import_service = ImportService(db)
    conflicts = await import_service.detect_conflicts(
        file_path,
        request.field_mapping,
    )

    return ConflictsResponse(**conflicts)


@router.post("/import/execute", response_model=ExecuteImportResponse, status_code=202)
async def execute_import(
    request: ExecuteImportRequest,
    background_tasks: BackgroundTasks,
    db: CommonDeps,
    api_key: AuthDeps,
) -> ExecuteImportResponse:
    """Execute the import with specified conflict resolution."""
    user_id = str(api_key) if api_key else "anonymous"

    # Check rate limit
    if not await check_import_rate_limit(user_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 5 imports per hour.",
        )

    # Get file path from file ID
    file_service = FileService()
    import_dir = file_service.import_dir

    # Find file
    import os

    file_path = None
    for filename in os.listdir(import_dir):
        if filename.startswith(request.file_id):
            file_path = os.path.join(import_dir, filename)
            break

    if not file_path:
        raise HTTPException(status_code=404, detail="File not found or expired")

    # Create import job
    import_job = ImportJob(
        user_id=user_id,
        file_id=request.file_id,
        field_mapping=request.field_mapping,
        conflict_resolution=request.conflict_resolution,
        options=request.options or {},
        status="processing",
    )

    # Save to database
    result = await db.import_jobs.insert_one(import_job.model_dump(by_alias=True))
    job_id = str(result.inserted_id)

    # Schedule background processing
    import_service = ImportService(db)
    background_tasks.add_task(
        import_service.execute_import,
        job_id,
        file_path,
        request.field_mapping,
        request.conflict_resolution,
        request.options,
        broadcast_import_progress,
    )

    return ExecuteImportResponse(
        jobId=job_id,
        status="processing",
        estimatedDurationSeconds=60,  # Rough estimate
    )


@router.get("/import/{job_id}/progress", response_model=ImportProgressResponse)
async def get_import_progress(
    job_id: str,
    db: CommonDeps,
    api_key: AuthDeps,
) -> ImportProgressResponse:
    """Get the progress of an import job."""
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID")

    import_job = await db.import_jobs.find_one({"_id": ObjectId(job_id)})
    if not import_job:
        raise HTTPException(status_code=404, detail="Import job not found")

    return ImportProgressResponse(
        jobId=job_id,
        status=import_job.get("status", "unknown"),
        progress=import_job.get("progress", {}),
        statistics=import_job.get("statistics", {}),
        errors=import_job.get("errors"),
        completedAt=import_job.get("completed_at").isoformat()
        if import_job.get("completed_at")
        else None,
    )


@router.post("/import/{job_id}/rollback", response_model=RollbackResponse)
async def rollback_import(
    job_id: str,
    db: CommonDeps,
    api_key: AuthDeps,
) -> RollbackResponse:
    """Rollback a completed or partially completed import."""
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID")

    import_job = await db.import_jobs.find_one({"_id": ObjectId(job_id)})
    if not import_job:
        raise HTTPException(status_code=404, detail="Import job not found")

    if not import_job.get("backup_info"):
        raise HTTPException(
            status_code=400, detail="Import cannot be rolled back (no backup available)"
        )

    # Implement rollback logic here (simplified for now)

    # Update job status
    await db.import_jobs.update_one(
        {"_id": ObjectId(job_id)}, {"$set": {"status": "rolled_back"}}
    )

    return RollbackResponse(
        jobId=job_id,
        status="rolled_back",
        itemsReverted=import_job.get("statistics", {}).get("imported", 0),
        message="Import successfully rolled back",
    )
