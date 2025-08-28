"""Rate limit usage endpoints for users."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_current_user, get_db
from app.models.rate_limit_usage import (
    RateLimitType,
    RateLimitUsageAggregation,
    UsageInterval,
    UserUsageSnapshot,
)
from app.models.user import UserInDB
from app.services.rate_limit_usage_service import RateLimitUsageService

router = APIRouter()


@router.get("/usage/current", response_model=UserUsageSnapshot)
async def get_current_usage(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
) -> UserUsageSnapshot:
    """Get current rate limit usage snapshot for the authenticated user."""
    service = RateLimitUsageService(db)
    return await service.get_current_usage_snapshot(str(current_user.id))


@router.get("/usage/history")
async def get_usage_history(
    limit_type: Optional[RateLimitType] = Query(
        None, description="Filter by rate limit type"
    ),
    interval: UsageInterval = Query(
        UsageInterval.HOUR, description="Aggregation interval"
    ),
    start_date: Optional[datetime] = Query(
        None, description="Start date (defaults to 24h ago)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date (defaults to now)"
    ),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
) -> List[RateLimitUsageAggregation]:
    """Get historical rate limit usage for the authenticated user."""
    service = RateLimitUsageService(db)

    # Default to last 24 hours if not specified
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        # Adjust default range based on interval
        if interval == UsageInterval.MINUTE:
            start_date = end_date - timedelta(hours=1)
        elif interval == UsageInterval.HOUR:
            start_date = end_date - timedelta(days=1)
        elif interval == UsageInterval.DAY:
            start_date = end_date - timedelta(days=30)
        elif interval == UsageInterval.WEEK:
            start_date = end_date - timedelta(days=90)
        elif interval == UsageInterval.MONTH:
            start_date = end_date - timedelta(days=365)

    # Limit the date range to prevent excessive queries
    max_range_days = {
        UsageInterval.MINUTE: 1,
        UsageInterval.HOUR: 7,
        UsageInterval.DAY: 90,
        UsageInterval.WEEK: 365,
        UsageInterval.MONTH: 730,  # 2 years
    }

    max_days = max_range_days.get(interval, 7)
    if (end_date - start_date).days > max_days:
        raise HTTPException(
            status_code=400,
            detail=f"Date range too large for {interval.value} interval. Maximum {max_days} days allowed.",
        )

    return await service.get_user_usage_history(
        user_id=str(current_user.id),
        limit_type=limit_type,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
    )


@router.get("/usage/summary")
async def get_usage_summary(
    time_range_hours: int = Query(24, ge=1, le=720, description="Time range in hours"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get usage summary statistics for the authenticated user."""
    service = RateLimitUsageService(db)

    start_date = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
    end_date = datetime.now(timezone.utc)

    # Get aggregated data for all rate limit types
    summary = {}

    for limit_type in RateLimitType:
        history = await service.get_user_usage_history(
            user_id=str(current_user.id),
            limit_type=limit_type,
            start_date=start_date,
            end_date=end_date,
            interval=UsageInterval.HOUR
            if time_range_hours <= 24
            else UsageInterval.DAY,
        )

        if history:
            # Calculate summary statistics
            total_requests = sum(h.total_requests for h in history)
            total_blocked = sum(h.total_blocked for h in history)
            total_allowed = sum(h.total_allowed for h in history)
            peak_usage = max((h.peak_usage_rate for h in history), default=0.0)
            avg_usage = (
                sum(h.average_usage_rate for h in history) / len(history)
                if history
                else 0.0
            )
            violations = sum(h.violation_count for h in history)

            # Calculate average response time if available
            response_times = [
                h.avg_response_time_ms for h in history if h.avg_response_time_ms
            ]
            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else None
            )

            # Calculate total data transferred if applicable
            total_bytes = sum(h.total_bytes_transferred or 0 for h in history)

            summary[limit_type.value] = {
                "total_requests": total_requests,
                "total_allowed": total_allowed,
                "total_blocked": total_blocked,
                "block_rate": (total_blocked / total_requests * 100)
                if total_requests > 0
                else 0,
                "peak_usage_rate": peak_usage,
                "average_usage_rate": avg_usage,
                "violation_count": violations,
                "average_response_time_ms": avg_response_time,
                "total_bytes_transferred": total_bytes if total_bytes > 0 else None,
            }

    # Add overall statistics
    all_requests = sum((s.get("total_requests") or 0) for s in summary.values())
    all_blocked = sum((s.get("total_blocked") or 0) for s in summary.values())
    all_violations = sum((s.get("violation_count") or 0) for s in summary.values())

    return {
        "time_range_hours": time_range_hours,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "by_type": summary,
        "overall": {
            "total_requests": all_requests,
            "total_blocked": all_blocked,
            "block_rate": (all_blocked / all_requests * 100) if all_requests > 0 else 0,
            "total_violations": all_violations,
        },
    }


@router.get("/usage/chart-data")
async def get_usage_chart_data(
    limit_type: RateLimitType = Query(..., description="Rate limit type to chart"),
    interval: UsageInterval = Query(
        UsageInterval.HOUR, description="Aggregation interval"
    ),
    hours: int = Query(24, ge=1, le=720, description="Hours of data to retrieve"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get rate limit usage data formatted for charting."""
    service = RateLimitUsageService(db)

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(hours=hours)

    history = await service.get_user_usage_history(
        user_id=str(current_user.id),
        limit_type=limit_type,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
    )

    # Format for chart visualization
    timestamps = []
    requests = []
    allowed = []
    blocked = []
    usage_rates = []

    for record in history:
        timestamps.append(record.period_start.isoformat())
        requests.append(record.total_requests)
        allowed.append(record.total_allowed)
        blocked.append(record.total_blocked)
        usage_rates.append(record.average_usage_rate)

    return {
        "limit_type": limit_type.value,
        "interval": interval.value,
        "timestamps": timestamps,
        "series": {
            "requests": requests,
            "allowed": allowed,
            "blocked": blocked,
            "usage_rate": usage_rates,
        },
        "metadata": {
            "total_requests": sum(requests),
            "total_blocked": sum(blocked),
            "peak_usage_rate": max(usage_rates) if usage_rates else 0,
            "average_usage_rate": sum(usage_rates) / len(usage_rates)
            if usage_rates
            else 0,
        },
    }


@router.post("/usage/flush")
async def flush_usage_metrics(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, str]:
    """Force flush current in-memory usage metrics to database.

    This is typically handled automatically but can be triggered manually if needed.
    """
    service = RateLimitUsageService(db)

    # Only allow if user is authenticated (any user can flush their own metrics)
    try:
        await service._flush_metrics()
        return {"message": "Usage metrics flushed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to flush metrics: {str(e)}"
        )
