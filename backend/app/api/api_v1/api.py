"""Main API router."""

from app.api.api_v1.endpoints import (
    admin,
    analytics,
    auth,
    backup,
    export,
    import_export,
    ingest,
    messages,
    projects,
    prompts,
    rate_limit_settings,
    restore,
    search,
    sessions,
    users,
)
from app.core.custom_router import APIRouter

# Import AI settings conditionally to avoid test failures
try:
    from app.api.api_v1.endpoints import ai_settings

    AI_SETTINGS_AVAILABLE = True
except ImportError:
    AI_SETTINGS_AVAILABLE = False

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])

api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])

api_router.include_router(messages.router, prefix="/messages", tags=["messages"])

api_router.include_router(search.router, prefix="/search", tags=["search"])

api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])

api_router.include_router(export.router, prefix="/export", tags=["export"])

api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])

# Include AI settings router if available
if AI_SETTINGS_AVAILABLE:
    api_router.include_router(
        ai_settings.router, prefix="/ai-settings", tags=["AI Settings"]
    )

# New import/export endpoints with comprehensive functionality
api_router.include_router(import_export.router, prefix="", tags=["import-export"])

# Backup and restore endpoints
api_router.include_router(backup.router, prefix="/backups", tags=["backup"])
api_router.include_router(restore.router, prefix="/restore", tags=["restore"])

# Rate limit settings endpoints
api_router.include_router(
    rate_limit_settings.router, prefix="/settings", tags=["settings"]
)


@api_router.get("/health")
async def api_health() -> dict[str, str]:
    """API health check."""
    return {"status": "ok", "api_version": "v1"}
