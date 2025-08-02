"""Analytics API endpoints."""
from typing import Any

from fastapi import HTTPException, Query

from app.api.dependencies import CommonDeps
from app.core.custom_router import APIRouter
from app.schemas.analytics import (
    ActivityHeatmap,
    AnalyticsSummary,
    CostAnalytics,
    ModelUsageStats,
    TimeRange,
    TokenUsageStats,
)
from app.services.analytics import AnalyticsService

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    db: CommonDeps, time_range: TimeRange = Query(TimeRange.LAST_30_DAYS)
) -> AnalyticsSummary:
    """Get overall analytics summary.

    Returns high-level metrics including total messages, costs,
    active projects, and usage trends.
    """
    service = AnalyticsService(db)
    return await service.get_summary(time_range)


@router.get("/activity/heatmap", response_model=ActivityHeatmap)
async def get_activity_heatmap(
    db: CommonDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    timezone: str = Query("UTC", description="Timezone for aggregation"),
) -> ActivityHeatmap:
    """Get activity heatmap data.

    Returns message counts aggregated by hour and day of week,
    useful for visualizing usage patterns.
    """
    service = AnalyticsService(db)
    return await service.get_activity_heatmap(time_range, timezone)


@router.get("/costs", response_model=CostAnalytics)
async def get_cost_analytics(
    db: CommonDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    group_by: str = Query("day", pattern="^(hour|day|week|month)$"),
    project_id: str | None = Query(None),
) -> CostAnalytics:
    """Get cost analytics over time.

    Returns cost data grouped by the specified time period,
    optionally filtered by project.
    """
    service = AnalyticsService(db)
    return await service.get_cost_analytics(time_range, group_by, project_id)


@router.get("/models/usage", response_model=ModelUsageStats)
async def get_model_usage(
    db: CommonDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    project_id: str | None = Query(None),
) -> ModelUsageStats:
    """Get model usage statistics.

    Returns usage data for each Claude model including message counts,
    costs, and average response times.
    """
    service = AnalyticsService(db)
    return await service.get_model_usage(time_range, project_id)


@router.get("/tokens", response_model=TokenUsageStats)
async def get_token_usage(
    db: CommonDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    group_by: str = Query("day", pattern="^(hour|day|week|month)$"),
) -> TokenUsageStats:
    """Get token usage statistics.

    Returns input and output token counts over time.
    """
    service = AnalyticsService(db)
    return await service.get_token_usage(time_range, group_by)


@router.get("/projects/comparison")
async def compare_projects(
    db: CommonDeps,
    project_ids: list[str] = Query(..., description="Project IDs to compare"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
) -> dict[str, Any]:
    """Compare analytics across multiple projects.

    Returns comparative metrics for the specified projects.
    """
    if len(project_ids) < 2 or len(project_ids) > 10:
        raise HTTPException(
            status_code=400, detail="Please provide between 2 and 10 project IDs"
        )

    service = AnalyticsService(db)
    return await service.compare_projects(project_ids, time_range)


@router.get("/trends")
async def get_usage_trends(
    db: CommonDeps,
    time_range: TimeRange = Query(TimeRange.LAST_90_DAYS),
    metric: str = Query(
        "messages", pattern="^(messages|costs|sessions|response_time)$"
    ),
) -> dict[str, Any]:
    """Get usage trends over time.

    Analyzes trends and provides insights on usage patterns.
    """
    service = AnalyticsService(db)
    return await service.analyze_trends(time_range, metric)
