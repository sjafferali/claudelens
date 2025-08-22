"""Backup API endpoints."""

import math
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import HTTPException, Query, WebSocket
from fastapi.responses import StreamingResponse

from app.api.dependencies import CommonDeps
from app.core.config import settings
from app.core.custom_router import APIRouter
from app.core.logging import get_logger
from app.schemas.backup_schemas import (
    BackupDetailResponse,
    BackupMetadataResponse,
    CreateBackupRequest,
    CreateBackupResponse,
    PagedBackupsResponse,
)
from app.services.backup_service import BackupService
from app.services.file_service import FileService
from app.services.websocket_manager import connection_manager

router = APIRouter()
logger = get_logger(__name__)

# Rate limiting tracking (simple in-memory for now)
backup_rate_limit: Dict[str, List[datetime]] = {}


async def check_backup_rate_limit(user_id: str) -> bool:
    """Check if user has exceeded backup rate limit."""
    now = datetime.now(UTC)
    window_ago = now - timedelta(hours=settings.RATE_LIMIT_WINDOW_HOURS)

    if user_id not in backup_rate_limit:
        backup_rate_limit[user_id] = []

    # Clean old entries
    backup_rate_limit[user_id] = [
        timestamp for timestamp in backup_rate_limit[user_id] if timestamp > window_ago
    ]

    if len(backup_rate_limit[user_id]) >= settings.BACKUP_RATE_LIMIT_PER_HOUR:
        return False

    backup_rate_limit[user_id].append(now)
    return True


async def broadcast_backup_progress(job_id: str, progress: Dict[str, Any]) -> None:
    """Broadcast backup progress via WebSocket."""
    # Create a backup progress event similar to export progress
    message = {
        "type": "backup_progress",
        "job_id": job_id,
        "progress": progress.get("percentage", 0),
        "current": progress.get("current", 0),
        "total": progress.get("total", 0),
        "message": progress.get("message", ""),
        "completed": progress.get("percentage", 0) >= 100,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    # Broadcast to all connections (using existing method)
    try:
        for websocket in connection_manager.active_connections:
            await websocket.send_json(message)
    except Exception as e:
        logger.warning(f"Failed to broadcast backup status: {e}")


@router.post("/", response_model=CreateBackupResponse, status_code=201)
async def create_backup(
    request: CreateBackupRequest,
    db: CommonDeps,
) -> CreateBackupResponse:
    """Create a new backup job."""
    # For now, allow anonymous backups similar to export endpoints
    # In production, this should be controlled by configuration
    user_id = "anonymous"

    # Check rate limit
    if not await check_backup_rate_limit(user_id):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {settings.BACKUP_RATE_LIMIT_PER_HOUR} backups per {settings.RATE_LIMIT_WINDOW_HOURS} hour(s).",
        )

    # Create backup job
    backup_service = BackupService(db)
    backup_response = await backup_service.create_backup(
        request=request,
        user_id=user_id,
    )

    # The backup service already starts the background task, so we just return the response
    return backup_response


@router.get("/", response_model=PagedBackupsResponse)
async def list_backups(
    db: CommonDeps,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at,desc"),
    status: str = Query(None),
    type: str = Query(None),
) -> PagedBackupsResponse:
    """List backups with pagination and filtering."""
    # For read-only operations, we don't require authentication
    # This matches the pattern used in other endpoints
    user_id = "anonymous"

    # Build filter
    filter_dict = {"created_by": user_id}
    if status:
        filter_dict["status"] = status
    if type:
        filter_dict["type"] = type

    # Parse sort parameter
    sort_parts = sort.split(",")
    sort_field = sort_parts[0]
    sort_direction = -1 if len(sort_parts) > 1 and sort_parts[1] == "desc" else 1

    # Get total count
    total = await db.backup_metadata.count_documents(filter_dict)

    # Get paginated results
    cursor = (
        db.backup_metadata.find(filter_dict)
        .sort(sort_field, sort_direction)
        .skip(page * size)
        .limit(size)
    )

    backups = []
    async for backup in cursor:
        backups.append(
            BackupMetadataResponse(
                _id=str(backup["_id"]),
                name=backup.get("name", ""),
                description=backup.get("description"),
                filename=backup.get("filename", ""),
                filepath=backup.get("filepath", ""),
                created_at=backup.get("created_at"),
                created_by=backup.get("created_by"),
                size_bytes=backup.get("size_bytes", 0),
                compressed_size_bytes=backup.get("compressed_size_bytes"),
                type=backup.get("type"),
                status=backup.get("status"),
                filters=backup.get("filters"),
                contents=backup.get("contents", {}),
                checksum=backup.get("checksum", ""),
                version=backup.get("version", "1.0"),
                download_url=backup.get("download_url"),
                can_restore=backup.get("can_restore", True),
                error_message=backup.get("error_message"),
            )
        )

    # Calculate summary statistics
    summary = {
        "total_size_bytes": sum(b.size_bytes for b in backups),
        "completed_count": len([b for b in backups if b.status == "completed"]),
        "failed_count": len([b for b in backups if b.status == "failed"]),
        "in_progress_count": len([b for b in backups if b.status == "in_progress"]),
    }

    return PagedBackupsResponse(
        items=backups,
        pagination={
            "page": page,
            "size": size,
            "total_elements": total,
            "total_pages": math.ceil(total / size) if size > 0 else 0,
        },
        summary=summary,
    )


@router.get("/{backup_id}", response_model=BackupDetailResponse)
async def get_backup_details(
    backup_id: str,
    db: CommonDeps,
) -> BackupDetailResponse:
    """Get detailed backup information."""
    if not ObjectId.is_valid(backup_id):
        raise HTTPException(status_code=400, detail="Invalid backup ID")

    backup = await db.backup_metadata.find_one({"_id": ObjectId(backup_id)})
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    return BackupDetailResponse(
        _id=str(backup["_id"]),
        name=backup.get("name", ""),
        description=backup.get("description"),
        filename=backup.get("filename", ""),
        filepath=backup.get("filepath", ""),
        created_at=backup.get("created_at"),
        created_by=backup.get("created_by"),
        size_bytes=backup.get("size_bytes", 0),
        compressed_size_bytes=backup.get("compressed_size_bytes"),
        type=backup.get("type"),
        status=backup.get("status"),
        filters=backup.get("filters"),
        contents=backup.get("contents", {}),
        checksum=backup.get("checksum", ""),
        version=backup.get("version", "1.0"),
        download_url=backup.get("download_url"),
        can_restore=backup.get("can_restore", True),
        error_message=backup.get("error_message"),
        storage_location=backup.get("storage_location", ""),
        encryption=backup.get("encryption"),
        compression=backup.get("compression"),
        restore_history=backup.get("restore_history", []),
        validation_status=backup.get("validation_status"),
    )


@router.get("/{backup_id}/download")
async def download_backup(
    backup_id: str,
    db: CommonDeps,
) -> StreamingResponse:
    """Download a backup file."""
    if not ObjectId.is_valid(backup_id):
        raise HTTPException(status_code=400, detail="Invalid backup ID")

    backup = await db.backup_metadata.find_one({"_id": ObjectId(backup_id)})
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    if backup.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Backup file not ready")

    file_path = backup.get("filepath")
    if not file_path:
        raise HTTPException(status_code=404, detail="Backup file not found")

    # Stream the file
    file_service = FileService()
    filename = backup.get("filename", f"backup_{backup_id}.claudelens")

    return StreamingResponse(
        file_service.stream_file(file_path),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: str,
    db: CommonDeps,
) -> Dict[str, Any]:
    """Delete a backup and its associated files."""
    if not ObjectId.is_valid(backup_id):
        raise HTTPException(status_code=400, detail="Invalid backup ID")

    obj_id = ObjectId(backup_id)
    backup = await db.backup_metadata.find_one({"_id": obj_id})
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    # Update status to deleting first
    await db.backup_metadata.update_one(
        {"_id": obj_id},
        {"$set": {"status": "deleting", "deleted_at": datetime.now(UTC)}},
    )

    # Delete associated file if it exists
    if backup.get("filepath"):
        try:
            file_service = FileService()
            await file_service.delete_file(backup["filepath"])
        except Exception as e:
            logger.warning(f"Failed to delete backup file: {e}")

    # Delete the backup from database
    result = await db.backup_metadata.delete_one({"_id": obj_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete backup")

    return {
        "backup_id": backup_id,
        "status": "deleted",
        "message": "Backup deleted successfully",
    }


@router.websocket("/ws/backup/{job_id}")
async def backup_websocket(websocket: WebSocket, job_id: str) -> None:
    """WebSocket endpoint for backup progress updates."""
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
        logger.error(f"WebSocket error for backup {job_id}: {e}")
    finally:
        await connection_manager.disconnect(websocket)
