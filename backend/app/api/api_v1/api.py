"""Main API router."""

from app.api.api_v1.endpoints import (
    analytics,
    export,
    ingest,
    messages,
    projects,
    prompts,
    search,
    sessions,
)
from app.core.custom_router import APIRouter

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])

api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])

api_router.include_router(messages.router, prefix="/messages", tags=["messages"])

api_router.include_router(search.router, prefix="/search", tags=["search"])

api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])

api_router.include_router(export.router, prefix="/export", tags=["export"])

api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])


@api_router.get("/health")
async def api_health() -> dict[str, str]:
    """API health check."""
    return {"status": "ok", "api_version": "v1"}
