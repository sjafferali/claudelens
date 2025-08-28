"""Service for tracking and storing rate limit usage history."""

import asyncio
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Mapping, Optional, Sequence, cast

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.logging import get_logger
from app.models.rate_limit_usage import (
    RateLimitType,
    RateLimitUsageAggregation,
    UsageInterval,
    UserUsageSnapshot,
)
from app.services.rate_limit_service import RateLimitService

logger = get_logger(__name__)


class RateLimitUsageService:
    """Service for tracking and analyzing rate limit usage."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize the usage tracking service."""
        self.db = db
        self.rate_limit_service = RateLimitService(db)

        # In-memory cache for current period metrics
        self._current_metrics: Dict[str, Dict] = defaultdict(
            lambda: defaultdict(
                lambda: {
                    "requests": 0,
                    "allowed": 0,
                    "blocked": 0,
                    "response_times": [],
                    "bytes": 0,
                }
            )
        )
        self._last_flush = datetime.now(UTC)
        self._flush_interval = 60  # Flush to database every 60 seconds

    async def record_request(
        self,
        user_id: str,
        limit_type: RateLimitType,
        allowed: bool,
        response_time_ms: Optional[float] = None,
        bytes_transferred: Optional[int] = None,
    ) -> None:
        """Record a single request for rate limit tracking."""
        try:
            # Update in-memory metrics
            key = f"{user_id}:{limit_type.value}"
            metrics = self._current_metrics[key]

            metrics["requests"] += 1
            if allowed:
                metrics["allowed"] += 1
            else:
                metrics["blocked"] += 1

            if response_time_ms is not None:
                metrics["response_times"].append(response_time_ms)

            if bytes_transferred is not None:
                metrics["bytes"] += bytes_transferred

            # Check if we should flush to database
            if (
                datetime.now(UTC) - self._last_flush
            ).total_seconds() >= self._flush_interval:
                asyncio.create_task(self._flush_metrics())

        except Exception as e:
            logger.error(f"Error recording rate limit usage: {e}")

    async def _flush_metrics(self) -> None:
        """Flush current metrics to database."""
        try:
            if not self._current_metrics:
                return

            # Get current rate limit settings
            settings = await self.rate_limit_service.get_settings()

            # Prepare batch insert
            records = []
            timestamp = datetime.now(UTC)

            for key, metrics in self._current_metrics.items():
                user_id, limit_type = key.split(":", 1)

                # Calculate average response time
                avg_response_time = None
                if metrics["response_times"]:
                    avg_response_time = sum(metrics["response_times"]) / len(
                        metrics["response_times"]
                    )

                # Get limit value for this type
                limit_value = self._get_limit_value(settings, limit_type)
                limit_window = self._get_limit_window(settings, limit_type)

                # Calculate peak usage rate
                peak_rate = 0.0
                if limit_value > 0:
                    peak_rate = (metrics["requests"] / limit_value) * 100

                record = {
                    "user_id": user_id,
                    "limit_type": limit_type,
                    "timestamp": timestamp,
                    "requests_made": metrics["requests"],
                    "requests_allowed": metrics["allowed"],
                    "requests_blocked": metrics["blocked"],
                    "limit_value": limit_value,
                    "limit_window": limit_window,
                    "peak_usage_rate": min(peak_rate, 100.0),
                    "average_response_time_ms": avg_response_time,
                    "bytes_transferred": metrics["bytes"]
                    if metrics["bytes"] > 0
                    else None,
                }

                records.append(record)

            # Insert all records
            if records:
                await self.db.rate_limit_usage.insert_many(records)
                logger.info(f"Flushed {len(records)} rate limit usage records")

            # Clear metrics
            self._current_metrics.clear()
            self._last_flush = timestamp

        except Exception as e:
            logger.error(f"Error flushing rate limit metrics: {e}")

    def _get_limit_value(self, settings: Any, limit_type: str) -> int:
        """Get the limit value for a specific type."""
        limit_map = {
            "http": settings.http_calls_per_minute,
            "ingestion": settings.ingest_rate_limit_per_hour,
            "ai": settings.ai_rate_limit_per_minute,
            "export": settings.export_limit_per_hour,
            "import": settings.import_limit_per_hour,
            "backup": settings.backup_limit_per_hour,
            "restore": settings.restore_limit_per_hour,
            "search": settings.search_rate_limit_per_minute,
            "analytics": settings.analytics_rate_limit_per_minute,
            "websocket": settings.websocket_max_connections_per_user,
        }
        result = limit_map.get(limit_type, 0)
        return int(result) if result else 0

    def _get_limit_window(self, settings: Any, limit_type: str) -> int:
        """Get the limit window in seconds for a specific type."""
        window_map = {
            "http": settings.http_rate_limit_window_seconds,
            "ingestion": 3600,  # 1 hour
            "ai": 60,  # 1 minute
            "export": settings.rate_limit_window_hours * 3600,
            "import": settings.rate_limit_window_hours * 3600,
            "backup": settings.rate_limit_window_hours * 3600,
            "restore": settings.rate_limit_window_hours * 3600,
            "search": 60,  # 1 minute
            "analytics": 60,  # 1 minute
            "websocket": 1,  # per second for message rate
        }
        result = window_map.get(limit_type, 60)
        return int(result) if result else 60

    async def get_user_usage_history(
        self,
        user_id: str,
        limit_type: Optional[RateLimitType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: UsageInterval = UsageInterval.HOUR,
    ) -> List[RateLimitUsageAggregation]:
        """Get aggregated usage history for a user."""
        # Default to last 24 hours if no date range specified
        if not end_date:
            end_date = datetime.now(UTC)
        if not start_date:
            start_date = end_date - timedelta(days=1)

        # Build query
        query: Dict[str, Any] = {
            "user_id": user_id,
            "timestamp": {"$gte": start_date, "$lte": end_date},
        }

        if limit_type:
            query["limit_type"] = limit_type.value

        # Aggregation pipeline
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": {
                        "user_id": "$user_id",
                        "limit_type": "$limit_type",
                        "period": self._get_period_expression(interval),
                    },
                    "period_start": {"$min": "$timestamp"},
                    "period_end": {"$max": "$timestamp"},
                    "total_requests": {"$sum": "$requests_made"},
                    "total_allowed": {"$sum": "$requests_allowed"},
                    "total_blocked": {"$sum": "$requests_blocked"},
                    "peak_usage_rate": {"$max": "$peak_usage_rate"},
                    "avg_usage_rate": {"$avg": "$peak_usage_rate"},
                    "violation_count": {
                        "$sum": {"$cond": [{"$gt": ["$requests_blocked", 0]}, 1, 0]}
                    },
                    "response_times": {"$push": "$average_response_time_ms"},
                    "total_bytes": {"$sum": "$bytes_transferred"},
                }
            },
            {
                "$project": {
                    "user_id": "$_id.user_id",
                    "limit_type": "$_id.limit_type",
                    "period": "$_id.period",
                    "period_start": 1,
                    "period_end": 1,
                    "total_requests": 1,
                    "total_allowed": 1,
                    "total_blocked": 1,
                    "peak_usage_rate": 1,
                    "average_usage_rate": "$avg_usage_rate",
                    "violation_count": 1,
                    "avg_response_time_ms": {"$avg": "$response_times"},
                    "total_bytes_transferred": "$total_bytes",
                }
            },
            {"$sort": {"period_start": 1}},
        ]

        # Execute aggregation
        cursor = self.db.rate_limit_usage.aggregate(pipeline)
        results = await cursor.to_list(None)

        # Convert to models
        aggregations = []
        for result in results:
            aggregations.append(
                RateLimitUsageAggregation(
                    user_id=result["user_id"],
                    limit_type=RateLimitType(result["limit_type"]),
                    interval=interval,
                    period_start=result["period_start"],
                    period_end=result["period_end"],
                    total_requests=result["total_requests"],
                    total_allowed=result["total_allowed"],
                    total_blocked=result["total_blocked"],
                    peak_usage_rate=result["peak_usage_rate"],
                    average_usage_rate=result["average_usage_rate"],
                    violation_count=result["violation_count"],
                    avg_response_time_ms=result.get("avg_response_time_ms"),
                    p95_response_time_ms=result.get("p95_response_time_ms"),
                    p99_response_time_ms=result.get("p99_response_time_ms"),
                    total_bytes_transferred=result.get("total_bytes_transferred"),
                )
            )

        return aggregations

    def _get_period_expression(self, interval: UsageInterval) -> Dict:
        """Get MongoDB aggregation expression for time period."""
        if interval == UsageInterval.MINUTE:
            return {
                "year": {"$year": "$timestamp"},
                "month": {"$month": "$timestamp"},
                "day": {"$dayOfMonth": "$timestamp"},
                "hour": {"$hour": "$timestamp"},
                "minute": {"$minute": "$timestamp"},
            }
        elif interval == UsageInterval.HOUR:
            return {
                "year": {"$year": "$timestamp"},
                "month": {"$month": "$timestamp"},
                "day": {"$dayOfMonth": "$timestamp"},
                "hour": {"$hour": "$timestamp"},
            }
        elif interval == UsageInterval.DAY:
            return {
                "year": {"$year": "$timestamp"},
                "month": {"$month": "$timestamp"},
                "day": {"$dayOfMonth": "$timestamp"},
            }
        elif interval == UsageInterval.WEEK:
            return {"year": {"$year": "$timestamp"}, "week": {"$week": "$timestamp"}}
        elif interval == UsageInterval.MONTH:
            return {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}}
        else:
            return {}

    async def get_current_usage_snapshot(self, user_id: str) -> UserUsageSnapshot:
        """Get current usage snapshot for a user."""
        # Get current usage from rate limit service
        usage_stats = await self.rate_limit_service.get_usage_stats(user_id)
        settings = await self.rate_limit_service.get_settings()

        # Build snapshot
        snapshot = UserUsageSnapshot(
            user_id=user_id,
            timestamp=datetime.now(UTC),
            total_requests_today=0,  # Will be calculated below
            total_blocked_today=0,  # Will be calculated below
        )

        # Map usage stats to snapshot fields
        usage_map = {
            "http": "http_usage",
            "ingestion": "ingestion_usage",
            "ai": "ai_usage",
            "export": "export_usage",
            "import": "import_usage",
            "backup": "backup_usage",
            "restore": "restore_usage",
            "search": "search_usage",
            "analytics": "analytics_usage",
            "websocket": "websocket_usage",
        }

        # Add current usage from in-memory metrics
        for limit_type in RateLimitType:
            key = f"{user_id}:{limit_type.value}"
            if key in self._current_metrics:
                metrics = self._current_metrics[key]
                field_name = usage_map.get(
                    limit_type.value, f"{limit_type.value}_usage"
                )

                # Get limit value
                limit_value = self._get_limit_value(settings, limit_type.value)

                setattr(
                    snapshot,
                    field_name,
                    {
                        "current": metrics["requests"],
                        "limit": limit_value,
                        "remaining": max(0, limit_value - metrics["requests"]),
                        "blocked": metrics["blocked"],
                        "percentage_used": (metrics["requests"] / limit_value * 100)
                        if limit_value > 0
                        else 0,
                    },
                )

        # Add rate limit service stats for operations
        for op_type in ["export", "import", "backup", "restore"]:
            if op_type in usage_stats:
                field_name = f"{op_type}_usage"
                stats = usage_stats[op_type]
                setattr(
                    snapshot,
                    field_name,
                    {
                        "current": stats["current"],
                        "limit": stats["limit"],
                        "remaining": stats["remaining"],
                        "reset_in_seconds": stats.get("reset_in_seconds"),
                        "percentage_used": (stats["current"] / stats["limit"] * 100)
                        if stats["limit"] != "unlimited" and stats["limit"] > 0
                        else 0,
                    },
                )

        # Calculate daily totals
        today_start = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        daily_stats = await self.db.rate_limit_usage.aggregate(
            [
                {"$match": {"user_id": user_id, "timestamp": {"$gte": today_start}}},
                {
                    "$group": {
                        "_id": None,
                        "total_requests": {"$sum": "$requests_made"},
                        "total_blocked": {"$sum": "$requests_blocked"},
                    }
                },
            ]
        ).to_list(1)

        if daily_stats:
            snapshot.total_requests_today = daily_stats[0]["total_requests"]
            snapshot.total_blocked_today = daily_stats[0]["total_blocked"]

        return snapshot

    async def cleanup_old_data(self, retention_days: int = 30) -> int:
        """Clean up old usage data beyond retention period."""
        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)

        result = await self.db.rate_limit_usage.delete_many(
            {"timestamp": {"$lt": cutoff_date}}
        )

        logger.info(f"Cleaned up {result.deleted_count} old rate limit usage records")
        return result.deleted_count

    async def get_top_users_by_usage(
        self,
        limit_type: Optional[RateLimitType] = None,
        limit: int = 10,
        time_range_hours: int = 24,
    ) -> List[Dict]:
        """Get top users by rate limit usage."""
        start_time = datetime.now(UTC) - timedelta(hours=time_range_hours)

        match_query: Dict[str, Any] = {"timestamp": {"$gte": start_time}}

        if limit_type:
            match_query["limit_type"] = limit_type.value

        pipeline = [
            {"$match": match_query},
            {
                "$group": {
                    "_id": "$user_id",
                    "total_requests": {"$sum": "$requests_made"},
                    "total_blocked": {"$sum": "$requests_blocked"},
                    "avg_usage_rate": {"$avg": "$peak_usage_rate"},
                }
            },
            {"$sort": {"total_requests": -1}},
            {"$limit": limit},
        ]

        # Cast pipeline to proper type for mypy
        typed_pipeline = cast(Sequence[Mapping[str, Any]], pipeline)
        cursor = self.db.rate_limit_usage.aggregate(typed_pipeline)
        return await cursor.to_list(None)
