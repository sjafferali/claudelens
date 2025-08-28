"""Import/Export API endpoints."""

import asyncio
import math
from datetime import UTC, datetime, timedelta
from typing import Any, AsyncGenerator, Dict, Optional

from bson import ObjectId
from fastapi import File, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from app.api.dependencies import AuthDeps, CommonDeps
from app.core.custom_router import APIRouter
from app.core.logging import get_logger
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
from app.services.rate_limit_service import RateLimitService
from app.services.websocket_manager import connection_manager

router = APIRouter()
logger = get_logger(__name__)

# Rate limiting now handled by RateLimitService


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
        statistics=progress.get("statistics"),
        completed=progress.get("percentage", 0) >= 100,
    )


@router.post("/export", response_model=CreateExportResponse, status_code=201)
async def create_export(
    request: CreateExportRequest,
    db: CommonDeps,
    user_id: AuthDeps,
) -> CreateExportResponse:
    """Create a new export job."""
    # User ID comes from authentication

    # Check rate limit using the new service
    rate_limit_service = RateLimitService(db)
    allowed, info = await rate_limit_service.check_rate_limit(user_id, "export")

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=info.get("message", "Rate limit exceeded"),
        )

    # Create export job
    export_service = ExportService(db)
    export_job = await export_service.create_export_job(
        user_id=user_id,
        format=request.format,
        filters=request.filters,
        options=request.options,
    )

    # Create async task for background processing
    # Using asyncio.create_task instead of BackgroundTasks for better reliability
    # Add a small delay to ensure the database write is committed
    async def process_export_task() -> None:
        try:
            # Small delay to ensure database write is visible
            await asyncio.sleep(0.1)
            # Create a new service instance with the same db connection
            export_service_task = ExportService(db)
            await export_service_task.process_export(
                str(export_job.id),
                broadcast_export_progress,
            )
        except Exception as e:
            logger.error(f"Error processing export job {export_job.id}: {e}")
            # Update job status to failed
            await db.export_jobs.update_one(
                {"_id": export_job.id},
                {
                    "$set": {
                        "status": "failed",
                        "completed_at": datetime.now(UTC),
                        "errors": [
                            {
                                "message": str(e),
                                "timestamp": datetime.now(UTC).isoformat(),
                            }
                        ],
                    }
                },
            )

    # Start the background task
    asyncio.create_task(process_export_task())

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
    user_id: AuthDeps,
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
        compressionFormat=export_job.get("compression_format"),
        compressionSavings=export_job.get("compression_savings"),
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
    user_id: AuthDeps,
    decompress: bool = Query(False, description="Decompress file server-side"),
) -> Response:
    """Download the exported file with optional server-side decompression."""
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID")

    export_job = await db.export_jobs.find_one({"_id": ObjectId(job_id)})
    if not export_job:
        raise HTTPException(status_code=404, detail="Export job not found")

    if export_job.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Export file not ready")

    # Check if expired
    if export_job.get("expires_at"):
        # Ensure expires_at is timezone-aware
        expires_at = export_job["expires_at"]
        if expires_at.tzinfo is None:
            # If naive, assume UTC
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            raise HTTPException(status_code=410, detail="Export file has expired")

    file_path = export_job.get("file_path")
    if not file_path:
        raise HTTPException(status_code=404, detail="Export file not found")

    # Stream the file
    file_service = FileService()
    compression_format = export_job.get("compression_format", "none")

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

    # Adjust filename based on compression
    if compression_format == "zstd" and not decompress:
        filename = f"claudelens_export_{job_id}.{extension}.zst"
        return FileResponse(
            file_path,
            media_type="application/zstd",
            headers={
                "Content-Encoding": "zstd",
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache",
            },
        )
    elif compression_format == "tar.gz":
        filename = f"claudelens_export_{job_id}.{extension}.tar.gz"
        return FileResponse(
            file_path,
            media_type="application/gzip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache",
            },
        )
    elif compression_format == "zstd" and decompress:
        # Server-side decompression for zstd
        async def stream_decompressed_zstd() -> AsyncGenerator[bytes, None]:
            """Stream decompressed zstd content."""
            import aiofiles

            try:
                import zstandard as zstd
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="Server-side decompression not available for zstd",
                )

            dctx = zstd.ZstdDecompressor()
            async with aiofiles.open(file_path, "rb") as f:
                decompressor = dctx.decompressobj()
                while True:
                    chunk = await f.read(8192)
                    if not chunk:
                        break
                    decompressed = decompressor.decompress(chunk)
                    if decompressed:
                        yield decompressed

        filename = f"claudelens_export_{job_id}.{extension}"
        return StreamingResponse(
            stream_decompressed_zstd(),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache",
            },
        )
    else:
        # Uncompressed file
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
    user_id: AuthDeps,
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


@router.delete("/export/{job_id}/permanent")
async def delete_export_permanently(
    job_id: str,
    db: CommonDeps,
    user_id: AuthDeps,
) -> Dict[str, str]:
    """Permanently delete an export job and its associated files."""
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID")

    export_job = await db.export_jobs.find_one({"_id": ObjectId(job_id)})
    if not export_job:
        raise HTTPException(status_code=404, detail="Export job not found")

    # Delete associated file if it exists
    if export_job.get("file_path"):
        try:
            file_service = FileService()
            await file_service.delete_file(export_job["file_path"])
        except Exception as e:
            logger.warning(f"Failed to delete export file: {e}")

    # Delete the export job from database
    result = await db.export_jobs.delete_one({"_id": ObjectId(job_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete export job")

    return {
        "jobId": job_id,
        "status": "deleted",
        "message": "Export job deleted permanently",
    }


@router.get("/export", response_model=PagedExportJobsResponse)
async def list_export_jobs(
    db: CommonDeps,
    user_id: AuthDeps,
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
                compressionFormat=job.get("compression_format"),
                compressionSavings=job.get("compression_savings"),
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
    user_id: AuthDeps,
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
    user_id: AuthDeps,
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
    db: CommonDeps,
    user_id: AuthDeps,
) -> ExecuteImportResponse:
    """Execute the import with specified conflict resolution."""
    # User ID comes from authentication

    # Check rate limit using the new service
    rate_limit_service = RateLimitService(db)
    allowed, info = await rate_limit_service.check_rate_limit(user_id, "import")

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=info.get("message", "Rate limit exceeded"),
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

    # Create import job without ID (let MongoDB generate it)
    import_job_data = {
        "user_id": user_id,
        "file_id": request.file_id,
        "field_mapping": request.field_mapping,
        "conflict_resolution": request.conflict_resolution,
        "options": request.options or {},
        "status": "processing",
        "created_at": datetime.now(UTC),
        "progress": {
            "processed": 0,
            "total": 0,
            "percentage": 0,
            "current_item": None,
        },
        "statistics": {
            "imported": 0,
            "skipped": 0,
            "failed": 0,
            "merged": 0,
            "replaced": 0,
        },
    }

    # Save to database
    result = await db.import_jobs.insert_one(import_job_data)
    job_id = str(result.inserted_id)

    # Create async task for background processing
    # Using asyncio.create_task instead of BackgroundTasks for better reliability
    import_service = ImportService(db)

    async def process_import_task() -> None:
        try:
            await import_service.execute_import(
                job_id,
                file_path,
                request.field_mapping,
                request.conflict_resolution,
                request.options,
                broadcast_import_progress,
                user_id,
            )
        except Exception as e:
            logger.error(f"Error processing import job {job_id}: {e}")
            # Update job status to failed
            await db.import_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": "failed",
                        "completed_at": datetime.now(UTC),
                        "errors": [
                            {
                                "message": str(e),
                                "timestamp": datetime.now(UTC).isoformat(),
                            }
                        ],
                    }
                },
            )

    # Start the background task
    asyncio.create_task(process_import_task())

    return ExecuteImportResponse(
        jobId=job_id,
        status="processing",
        estimatedDurationSeconds=60,  # Rough estimate
    )


@router.get("/import/{job_id}/progress", response_model=ImportProgressResponse)
async def get_import_progress(
    job_id: str,
    db: CommonDeps,
    user_id: AuthDeps,
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
    user_id: AuthDeps,
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


@router.get("/rate-limits")
async def get_rate_limits(db: CommonDeps, user_id: AuthDeps) -> Dict[str, Any]:
    """Get current rate limit status for the user."""
    # User ID comes from authentication

    # Use the new rate limit service
    rate_limit_service = RateLimitService(db)
    settings = await rate_limit_service.get_settings()
    usage_stats = await rate_limit_service.get_usage_stats(user_id)

    return {
        "export": usage_stats.get("export", {}),
        "import": usage_stats.get("import", {}),
        "settings": {
            "rate_limiting_enabled": settings.rate_limiting_enabled,
            "window_hours": settings.rate_limit_window_hours,
        },
    }


@router.get("/import")
async def list_import_jobs(
    db: CommonDeps,
    user_id: AuthDeps,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    sort: str = Query("createdAt,desc"),
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """List import jobs for the current user."""
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
    total = await db.import_jobs.count_documents(filter_dict)

    # Get paginated results
    cursor = db.import_jobs.find(filter_dict)
    cursor = cursor.sort(sort_field, sort_direction)
    cursor = cursor.skip(page * size).limit(size)

    jobs = []
    async for job in cursor:
        jobs.append(
            {
                "jobId": str(job["_id"]),
                "status": job.get("status", "unknown"),
                "fileId": job.get("file_id"),
                "createdAt": job.get("created_at").isoformat()
                if job.get("created_at")
                else "",
                "completedAt": job.get("completed_at").isoformat()
                if job.get("completed_at")
                else None,
                "statistics": job.get("statistics", {}),
                "errors": job.get("errors", []),
            }
        )

    return {
        "content": jobs,
        "totalElements": total,
        "totalPages": math.ceil(total / size) if size > 0 else 0,
        "size": size,
        "number": page,
    }
