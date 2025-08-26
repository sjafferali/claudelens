"""Restore API endpoints."""

import asyncio
from datetime import UTC, datetime
from typing import Any, Dict, Optional

from bson import ObjectId
from fastapi import File, HTTPException, UploadFile, WebSocket

from app.api.dependencies import AuthDeps, CommonDeps
from app.core.custom_router import APIRouter
from app.core.logging import get_logger
from app.schemas.backup_schemas import (
    CreateRestoreRequest,
    CreateRestoreResponse,
    PreviewBackupResponse,
    RestoreProgressResponse,
)
from app.services.file_service import FileService
from app.services.rate_limit_service import RateLimitService
from app.services.restore_service import RestoreService
from app.services.websocket_manager import connection_manager

router = APIRouter()
logger = get_logger(__name__)

# Rate limiting now handled by RateLimitService


async def broadcast_restore_progress(job_id: str, progress: Dict[str, Any]) -> None:
    """Broadcast restore progress via WebSocket."""
    # Create a restore progress event similar to import progress
    message = {
        "type": "restore_progress",
        "job_id": job_id,
        "progress": progress.get("percentage", 0),
        "current": progress.get("processed", 0),
        "total": progress.get("total", 0),
        "message": progress.get("message", ""),
        "statistics": progress.get("statistics"),
        "completed": progress.get("percentage", 0) >= 100,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    # Broadcast to all connections (using existing method)
    try:
        for websocket in connection_manager.active_connections:
            await websocket.send_json(message)
    except Exception as e:
        logger.warning(f"Failed to broadcast restore status: {e}")


@router.post("/", response_model=CreateRestoreResponse, status_code=201)
async def create_restore(
    request: CreateRestoreRequest,
    db: CommonDeps,
    user_id: AuthDeps,
) -> CreateRestoreResponse:
    """Create a restore job from an existing backup."""
    # User ID comes from authentication

    # Check rate limit using the new service
    rate_limit_service = RateLimitService(db)
    allowed, info = await rate_limit_service.check_rate_limit(user_id, "restore")

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=info.get("message", "Rate limit exceeded"),
        )

    # Validate backup exists
    if not ObjectId.is_valid(request.backup_id):
        raise HTTPException(status_code=400, detail="Invalid backup ID")

    backup = await db.backup_metadata.find_one({"_id": ObjectId(request.backup_id)})
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    if backup.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Backup is not ready for restore")

    # Create restore job
    restore_service = RestoreService(db)
    restore_response = await restore_service.create_restore_job(
        request=request,
        user_id=user_id,
    )

    # The restore service already starts the background processing
    return restore_response


@router.post("/upload", response_model=CreateRestoreResponse, status_code=202)
async def restore_from_upload(
    db: CommonDeps,
    user_id: AuthDeps,
    file: UploadFile = File(...),
    mode: str = "full",
    conflict_resolution: str = "skip",
) -> CreateRestoreResponse:
    """Upload a backup file and create a restore job."""
    # User ID comes from authentication

    # Check rate limit using the new service
    rate_limit_service = RateLimitService(db)
    allowed, info = await rate_limit_service.check_rate_limit(user_id, "restore")

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=info.get("message", "Rate limit exceeded"),
        )

    # Validate file type and size
    if not file.filename or not file.filename.endswith(".claudelens"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .claudelens backup files are supported.",
        )

    # Check file size (max 1GB)
    if file.size and file.size > 1024 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 1GB.",
        )

    # Save uploaded file
    file_service = FileService()
    file_info = await file_service.validate_and_save_upload(
        file, allowed_extensions=[".claudelens"]
    )

    # Create restore job with uploaded file
    restore_service = RestoreService(db)
    restore_job = await restore_service.create_restore_job_from_upload(
        user_id=user_id,
        file_path=file_info["path"],
        filename=file_info["filename"],
        mode=mode,
        conflict_resolution=conflict_resolution,
    )

    # Create async task for background processing
    async def process_restore_task() -> None:
        try:
            # Small delay to ensure database write is visible
            await asyncio.sleep(0.1)
            # Create a new service instance with the same db connection
            restore_service_task = RestoreService(db)
            await restore_service_task.process_restore_from_upload(
                restore_job.job_id,
                file_info["path"],
                broadcast_restore_progress,
            )
        except Exception as e:
            logger.error(
                f"Error processing restore upload job {restore_job.job_id}: {e}"
            )
            # Update job status to failed
            await db.restore_jobs.update_one(
                {"_id": ObjectId(restore_job.job_id)},
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
    asyncio.create_task(process_restore_task())

    return restore_job


@router.get("/{job_id}/status", response_model=RestoreProgressResponse)
async def get_restore_status(
    job_id: str,
    db: CommonDeps,
    user_id: AuthDeps,
) -> RestoreProgressResponse:
    """Get the status and progress of a restore job."""
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID")

    restore_job = await db.restore_jobs.find_one({"_id": ObjectId(job_id)})
    if not restore_job:
        raise HTTPException(status_code=404, detail="Restore job not found")

    return RestoreProgressResponse(
        job_id=job_id,
        status=restore_job.get("status", "unknown"),
        progress=restore_job.get("progress", {}),
        statistics=restore_job.get("statistics", {}),
        errors=restore_job.get("errors", []),
        completed_at=restore_job.get("completed_at"),
    )


@router.get("/preview/{backup_id}", response_model=PreviewBackupResponse)
async def preview_backup(
    backup_id: str,
    db: CommonDeps,
    user_id: AuthDeps,
) -> PreviewBackupResponse:
    """Preview the contents of a backup before restoring."""
    if not ObjectId.is_valid(backup_id):
        raise HTTPException(status_code=400, detail="Invalid backup ID")

    backup = await db.backup_metadata.find_one({"_id": ObjectId(backup_id)})
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    if backup.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Backup is not ready for preview")

    # Get preview data from backup service
    restore_service = RestoreService(db)
    preview_data = await restore_service.preview_backup_contents(backup_id)

    # Check for potential warnings
    warnings = []
    if backup.get("version") != "1.0":
        warnings.append(
            f"Backup version {backup.get('version')} may not be fully compatible"
        )

    contents = backup.get("contents", {})
    if contents.get("messages_count", 0) > 10000:
        warnings.append("Large backup - restore may take significant time")

    return PreviewBackupResponse(
        backup_id=backup_id,
        name=backup.get("name", ""),
        created_at=backup.get("created_at"),
        type=backup.get("type"),
        contents=contents,
        filters=backup.get("filters"),
        size_bytes=backup.get("size_bytes", 0),
        compressed_size_bytes=backup.get("compressed_size_bytes"),
        preview_data=preview_data,
        can_restore=backup.get("can_restore", True),
        warnings=warnings,
    )


@router.get("/jobs", response_model=Dict[str, Any])
async def list_restore_jobs(
    db: CommonDeps,
    user_id: AuthDeps,
    page: int = 0,
    size: int = 20,
    sort: str = "created_at,desc",
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """List restore jobs (restore history) for the current user."""
    # For now, use anonymous user (same as other endpoints)
    user_id = "anonymous"

    # Build filter
    filter_dict = {"user_id": user_id}
    if status:
        filter_dict["status"] = status

    # Parse sort parameter
    sort_parts = sort.split(",")
    sort_field = sort_parts[0]
    sort_direction = -1 if len(sort_parts) > 1 and sort_parts[1] == "desc" else 1

    # Get total count
    total = await db.restore_jobs.count_documents(filter_dict)

    # Get paginated results
    cursor = db.restore_jobs.find(filter_dict)
    cursor = cursor.sort(sort_field, sort_direction)
    cursor = cursor.skip(page * size).limit(size)

    jobs = []
    async for job in cursor:
        # Get backup name if available
        backup_name = "Unknown"
        if job.get("backup_id"):
            backup = await db.backup_metadata.find_one(
                {"_id": ObjectId(job["backup_id"])}
            )
            if backup:
                backup_name = backup.get("name", "Unknown")

        jobs.append(
            {
                "job_id": str(job["_id"]),
                "backup_id": job.get("backup_id"),
                "backup_name": backup_name,
                "status": job.get("status", "unknown"),
                "mode": job.get("mode", "unknown"),
                "conflict_resolution": job.get("conflict_resolution"),
                "created_at": job.get("created_at").isoformat()
                if job.get("created_at")
                else "",
                "started_at": job.get("started_at").isoformat()
                if job.get("started_at")
                else None,
                "completed_at": job.get("completed_at").isoformat()
                if job.get("completed_at")
                else None,
                "statistics": job.get("statistics", {}),
                "errors": job.get("errors", []),
                "progress": job.get("progress", {}),
            }
        )

    return {
        "items": jobs,
        "pagination": {
            "page": page,
            "size": size,
            "total_elements": total,
            "total_pages": (total + size - 1) // size if size > 0 else 0,
        },
    }


@router.websocket("/ws/restore/{job_id}")
async def restore_websocket(websocket: WebSocket, job_id: str) -> None:
    """WebSocket endpoint for restore progress updates."""
    await connection_manager.connect(websocket)
    try:
        # Keep connection alive and listen for disconnect
        while True:
            try:
                # Wait for ping/pong to keep connection alive
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except Exception:
                break
    except Exception as e:
        logger.error(f"WebSocket error for restore {job_id}: {e}")
    finally:
        await connection_manager.disconnect(websocket)
