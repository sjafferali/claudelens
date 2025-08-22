"""Rate limit settings API endpoints."""

from typing import Dict, Optional

from fastapi import HTTPException

from app.api.dependencies import CommonDeps
from app.core.custom_router import APIRouter
from app.core.logging import get_logger
from app.schemas.rate_limit_settings import (
    RateLimitSettingsResponse,
    RateLimitSettingsUpdate,
)
from app.services.rate_limit_service import RateLimitService

router = APIRouter()
logger = get_logger(__name__)


@router.get("/rate-limit-settings", response_model=RateLimitSettingsResponse)
async def get_rate_limit_settings(db: CommonDeps) -> RateLimitSettingsResponse:
    """Get current rate limit settings."""
    service = RateLimitService(db)
    settings = await service.get_settings()

    # Get current usage for the anonymous user (for display purposes)
    usage_stats = await service.get_usage_stats("anonymous")

    return RateLimitSettingsResponse(
        export_limit_per_hour=settings.export_limit_per_hour,
        import_limit_per_hour=settings.import_limit_per_hour,
        backup_limit_per_hour=settings.backup_limit_per_hour,
        restore_limit_per_hour=settings.restore_limit_per_hour,
        max_upload_size_mb=settings.max_upload_size_mb,
        max_export_size_mb=settings.max_export_size_mb,
        max_backup_size_gb=settings.max_backup_size_gb,
        max_page_size=settings.max_page_size,
        default_page_size=settings.default_page_size,
        rate_limit_window_hours=settings.rate_limit_window_hours,
        rate_limiting_enabled=settings.rate_limiting_enabled,
        updated_at=settings.updated_at,
        updated_by=settings.updated_by,
        current_usage=usage_stats,
    )


@router.put("/rate-limit-settings", response_model=RateLimitSettingsResponse)
async def update_rate_limit_settings(
    request: RateLimitSettingsUpdate,
    db: CommonDeps,
) -> RateLimitSettingsResponse:
    """Update rate limit settings."""
    service = RateLimitService(db)

    # Convert request to dict, excluding None values
    updates = request.dict(exclude_none=True)

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    # Update settings
    settings = await service.update_settings(updates, updated_by="admin")

    # Get current usage
    usage_stats = await service.get_usage_stats("anonymous")

    return RateLimitSettingsResponse(
        export_limit_per_hour=settings.export_limit_per_hour,
        import_limit_per_hour=settings.import_limit_per_hour,
        backup_limit_per_hour=settings.backup_limit_per_hour,
        restore_limit_per_hour=settings.restore_limit_per_hour,
        max_upload_size_mb=settings.max_upload_size_mb,
        max_export_size_mb=settings.max_export_size_mb,
        max_backup_size_gb=settings.max_backup_size_gb,
        max_page_size=settings.max_page_size,
        default_page_size=settings.default_page_size,
        rate_limit_window_hours=settings.rate_limit_window_hours,
        rate_limiting_enabled=settings.rate_limiting_enabled,
        updated_at=settings.updated_at,
        updated_by=settings.updated_by,
        current_usage=usage_stats,
    )


@router.post("/rate-limit-settings/reset")
async def reset_rate_limits(
    db: CommonDeps,
    user_id: str = "anonymous",
    limit_type: Optional[str] = None,
) -> Dict:
    """Reset rate limits for a user."""
    service = RateLimitService(db)

    await service.reset_user_limits(user_id, limit_type)

    return {
        "message": f"Rate limits reset for user {user_id}",
        "limit_type": limit_type or "all",
    }


@router.get("/rate-limit-settings/usage")
async def get_rate_limit_usage(
    db: CommonDeps,
    user_id: str = "anonymous",
) -> Dict:
    """Get current rate limit usage for a user."""
    service = RateLimitService(db)
    usage_stats = await service.get_usage_stats(user_id)

    return {"user_id": user_id, "usage": usage_stats}
