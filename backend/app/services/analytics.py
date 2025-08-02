"""Analytics service implementation."""
from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.analytics import (
    ActivityHeatmap,
    AnalyticsSummary,
    CostAnalytics,
    CostDataPoint,
    HeatmapCell,
    ModelUsage,
    ModelUsageStats,
    TimeRange,
    TokenDataPoint,
    TokenUsageStats,
)


class AnalyticsService:
    """Service for analytics operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    def _get_time_filter(self, time_range: TimeRange) -> dict[str, Any]:
        """Convert time range to MongoDB filter."""
        now = datetime.utcnow()

        if time_range == TimeRange.LAST_24_HOURS:
            start = now - timedelta(hours=24)
        elif time_range == TimeRange.LAST_7_DAYS:
            start = now - timedelta(days=7)
        elif time_range == TimeRange.LAST_30_DAYS:
            start = now - timedelta(days=30)
        elif time_range == TimeRange.LAST_90_DAYS:
            start = now - timedelta(days=90)
        elif time_range == TimeRange.LAST_YEAR:
            start = now - timedelta(days=365)
        else:  # ALL_TIME
            return {}

        return {"timestamp": {"$gte": start}}

    async def get_summary(self, time_range: TimeRange) -> AnalyticsSummary:
        """Get analytics summary."""
        time_filter = self._get_time_filter(time_range)

        # Current period stats
        current_stats = await self._get_period_stats(time_filter)

        # Previous period stats for trends
        if time_range != TimeRange.ALL_TIME:
            prev_filter = self._get_previous_period_filter(time_range)
            prev_stats = await self._get_period_stats(prev_filter)

            # Calculate trends
            messages_trend = self._calculate_trend(
                current_stats["total_messages"], prev_stats["total_messages"]
            )
            cost_trend = self._calculate_trend(
                current_stats["total_cost"], prev_stats["total_cost"]
            )
        else:
            messages_trend = 0
            cost_trend = 0

        # Get most active project
        project_pipeline: list[dict[str, Any]] = [
            {"$match": time_filter},
            {
                "$lookup": {
                    "from": "sessions",
                    "localField": "sessionId",
                    "foreignField": "sessionId",
                    "as": "session",
                }
            },
            {"$unwind": "$session"},
            {"$group": {"_id": "$session.projectId", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1},
            {
                "$lookup": {
                    "from": "projects",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "project",
                }
            },
            {"$unwind": "$project"},
        ]

        project_result = await self.db.messages.aggregate(project_pipeline).to_list(1)
        most_active_project = (
            project_result[0]["project"]["name"] if project_result else None
        )

        # Get most used model
        model_pipeline: list[dict[str, Any]] = [
            {"$match": {**time_filter, "model": {"$exists": True}}},
            {"$group": {"_id": "$model", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1},
        ]

        model_result = await self.db.messages.aggregate(model_pipeline).to_list(1)
        most_used_model = model_result[0]["_id"] if model_result else None

        return AnalyticsSummary(
            total_messages=current_stats["total_messages"],
            total_sessions=current_stats["total_sessions"],
            total_projects=current_stats["total_projects"],
            total_cost=round(current_stats["total_cost"], 2),
            messages_trend=messages_trend,
            cost_trend=cost_trend,
            most_active_project=most_active_project,
            most_used_model=most_used_model,
            time_range=time_range,
        )

    async def get_activity_heatmap(
        self, time_range: TimeRange, timezone: str = "UTC"
    ) -> ActivityHeatmap:
        """Get activity heatmap data."""
        time_filter = self._get_time_filter(time_range)

        # Aggregation pipeline for heatmap
        pipeline: list[dict[str, Any]] = [
            {"$match": time_filter},
            {
                "$project": {
                    "hour": {"$hour": {"date": "$timestamp", "timezone": timezone}},
                    "dayOfWeek": {
                        "$subtract": [
                            {
                                "$dayOfWeek": {
                                    "date": "$timestamp",
                                    "timezone": timezone,
                                }
                            },
                            1,
                        ]
                    },  # Convert to 0-6 (Mon-Sun)
                    "costUsd": 1,
                    "durationMs": 1,
                }
            },
            {
                "$group": {
                    "_id": {"hour": "$hour", "dayOfWeek": "$dayOfWeek"},
                    "count": {"$sum": 1},
                    "avgCost": {"$avg": "$costUsd"},
                    "avgResponseTime": {"$avg": "$durationMs"},
                }
            },
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        # Convert to heatmap cells
        cells = []
        hour_counts: dict[int, int] = {}
        day_counts: dict[int, int] = {}

        for result in results:
            hour = result["_id"]["hour"]
            day = result["_id"]["dayOfWeek"]
            count = result["count"]

            # Track for peak calculations
            hour_counts[hour] = hour_counts.get(hour, 0) + count
            day_counts[day] = day_counts.get(day, 0) + count

            cells.append(
                HeatmapCell(
                    day_of_week=day,
                    hour=hour,
                    count=count,
                    avg_cost=round(result["avgCost"], 4) if result["avgCost"] else None,
                    avg_response_time=result["avgResponseTime"],
                )
            )

        # Find peak times
        peak_hour = (
            max(hour_counts, key=lambda x: hour_counts[x]) if hour_counts else None
        )
        peak_day = max(day_counts, key=lambda x: day_counts[x]) if day_counts else None

        total_messages = sum(cell.count for cell in cells)

        return ActivityHeatmap(
            cells=cells,
            total_messages=total_messages,
            time_range=time_range,
            timezone=timezone,
            peak_hour=peak_hour,
            peak_day=peak_day,
        )

    async def get_cost_analytics(
        self, time_range: TimeRange, group_by: str, project_id: str | None = None
    ) -> CostAnalytics:
        """Get cost analytics over time."""
        time_filter = self._get_time_filter(time_range)

        # Add project filter if specified
        if project_id:
            session_ids = await self.db.sessions.distinct(
                "sessionId", {"projectId": ObjectId(project_id)}
            )
            time_filter["sessionId"] = {"$in": session_ids}

        # Determine date grouping
        date_format = self._get_date_format(group_by)

        # Aggregation pipeline
        pipeline: list[dict[str, Any]] = [
            {"$match": {**time_filter, "costUsd": {"$exists": True}}},
            {
                "$group": {
                    "_id": {
                        "date": {
                            "$dateToString": {
                                "format": date_format,
                                "date": "$timestamp",
                            }
                        },
                        "model": "$model",
                    },
                    "cost": {"$sum": "$costUsd"},
                    "count": {"$sum": 1},
                }
            },
            {
                "$group": {
                    "_id": "$_id.date",
                    "totalCost": {"$sum": "$cost"},
                    "messageCount": {"$sum": "$count"},
                    "costByModel": {"$push": {"model": "$_id.model", "cost": "$cost"}},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        # Process results
        data_points = []
        total_cost = 0
        total_messages = 0
        cost_by_model_global: dict[str, float] = {}

        for result in results:
            # Parse timestamp
            timestamp = datetime.strptime(result["_id"], date_format)

            # Process model costs
            cost_by_model = {}
            for model_cost in result["costByModel"]:
                model = model_cost["model"] or "unknown"
                cost = model_cost["cost"]
                cost_by_model[model] = cost
                cost_by_model_global[model] = cost_by_model_global.get(model, 0) + cost

            data_points.append(
                CostDataPoint(
                    timestamp=timestamp,
                    cost=round(result["totalCost"], 4),
                    message_count=result["messageCount"],
                    cost_by_model=cost_by_model,
                )
            )

            total_cost += result["totalCost"]
            total_messages += result["messageCount"]

        avg_cost = total_cost / total_messages if total_messages > 0 else 0

        return CostAnalytics(
            data_points=data_points,
            total_cost=round(total_cost, 2),
            average_cost_per_message=round(avg_cost, 4),
            time_range=time_range,
            group_by=group_by,
            cost_by_model={k: round(v, 2) for k, v in cost_by_model_global.items()},
        )

    async def get_model_usage(
        self, time_range: TimeRange, project_id: str | None = None
    ) -> ModelUsageStats:
        """Get model usage statistics."""
        time_filter = self._get_time_filter(time_range)

        # Add project filter if specified
        if project_id:
            session_ids = await self.db.sessions.distinct(
                "sessionId", {"projectId": ObjectId(project_id)}
            )
            time_filter["sessionId"] = {"$in": session_ids}

        # Aggregation pipeline
        pipeline: list[dict[str, Any]] = [
            {"$match": {**time_filter, "model": {"$exists": True}}},
            {
                "$group": {
                    "_id": "$model",
                    "count": {"$sum": 1},
                    "totalCost": {"$sum": "$costUsd"},
                    "avgResponseTime": {"$avg": "$durationMs"},
                    "avgInputTokens": {"$avg": "$tokensInput"},
                    "avgOutputTokens": {"$avg": "$tokensOutput"},
                }
            },
            {"$sort": {"count": -1}},
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        # Process results
        models = []
        max_count = 0
        min_count = float("inf")
        most_used = None
        least_used = None

        for result in results:
            model = result["_id"]
            count = result["count"]
            total_cost = result["totalCost"] or 0

            # Track most/least used
            if count > max_count:
                max_count = count
                most_used = model
            if count < min_count:
                min_count = count
                least_used = model

            models.append(
                ModelUsage(
                    model=model,
                    message_count=count,
                    total_cost=round(total_cost, 2),
                    avg_cost_per_message=round(
                        total_cost / count if count > 0 else 0, 4
                    ),
                    avg_response_time_ms=result["avgResponseTime"],
                    avg_tokens_input=result["avgInputTokens"],
                    avg_tokens_output=result["avgOutputTokens"],
                )
            )

        return ModelUsageStats(
            models=models,
            total_models=len(models),
            time_range=time_range,
            most_used=most_used,
            least_used=least_used,
        )

    async def get_token_usage(
        self, time_range: TimeRange, group_by: str
    ) -> TokenUsageStats:
        """Get token usage statistics."""
        time_filter = self._get_time_filter(time_range)
        date_format = self._get_date_format(group_by)

        # Aggregation pipeline
        pipeline: list[dict[str, Any]] = [
            {"$match": time_filter},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": date_format, "date": "$timestamp"}
                    },
                    "inputTokens": {"$sum": "$tokensInput"},
                    "outputTokens": {"$sum": "$tokensOutput"},
                    "messageCount": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        # Process results
        data_points = []
        total_input = 0
        total_output = 0
        total_messages = 0

        for result in results:
            timestamp = datetime.strptime(result["_id"], date_format)
            input_tokens = result["inputTokens"] or 0
            output_tokens = result["outputTokens"] or 0

            data_points.append(
                TokenDataPoint(
                    timestamp=timestamp,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                )
            )

            total_input += input_tokens
            total_output += output_tokens
            total_messages += result["messageCount"]

        avg_input = total_input / total_messages if total_messages > 0 else 0
        avg_output = total_output / total_messages if total_messages > 0 else 0

        return TokenUsageStats(
            data_points=data_points,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            avg_input_tokens_per_message=round(avg_input, 2),
            avg_output_tokens_per_message=round(avg_output, 2),
            time_range=time_range,
            group_by=group_by,
        )

    async def compare_projects(
        self, project_ids: list[str], time_range: TimeRange
    ) -> dict[str, Any]:
        """Compare analytics across multiple projects."""
        time_filter = self._get_time_filter(time_range)

        # Convert string IDs to ObjectIds
        project_oids = [ObjectId(pid) for pid in project_ids]

        # Get project info
        projects = await self.db.projects.find({"_id": {"$in": project_oids}}).to_list(
            None
        )

        project_map = {str(p["_id"]): p["name"] for p in projects}

        # Analytics pipeline
        pipeline: list[dict[str, Any]] = [
            {"$match": time_filter},
            {
                "$lookup": {
                    "from": "sessions",
                    "localField": "sessionId",
                    "foreignField": "sessionId",
                    "as": "session",
                }
            },
            {"$unwind": "$session"},
            {"$match": {"session.projectId": {"$in": project_oids}}},
            {
                "$group": {
                    "_id": "$session.projectId",
                    "messageCount": {"$sum": 1},
                    "totalCost": {"$sum": "$costUsd"},
                    "avgResponseTime": {"$avg": "$durationMs"},
                    "models": {"$addToSet": "$model"},
                    "sessionCount": {"$addToSet": "$sessionId"},
                }
            },
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        # Process results
        comparison: dict[str, Any] = {
            "projects": [],
            "time_range": time_range.value,
            "metrics": {
                "highest_usage": None,
                "highest_cost": None,
                "fastest_response": None,
            },
        }

        max_messages = 0
        max_cost = 0
        min_response_time = float("inf")

        for result in results:
            project_id = str(result["_id"])
            project_name = project_map.get(project_id, "Unknown")
            message_count = result["messageCount"]
            total_cost = result["totalCost"] or 0
            avg_response = result["avgResponseTime"] or 0

            # Track extremes
            if message_count > max_messages:
                max_messages = message_count
                comparison["metrics"]["highest_usage"] = project_name

            if total_cost > max_cost:
                max_cost = total_cost
                comparison["metrics"]["highest_cost"] = project_name

            if avg_response > 0 and avg_response < min_response_time:
                min_response_time = avg_response
                comparison["metrics"]["fastest_response"] = project_name

            comparison["projects"].append(
                {
                    "id": project_id,
                    "name": project_name,
                    "message_count": message_count,
                    "session_count": len(result["sessionCount"]),
                    "total_cost": round(total_cost, 2),
                    "avg_cost_per_message": round(
                        total_cost / message_count if message_count > 0 else 0, 4
                    ),
                    "avg_response_time_ms": avg_response,
                    "models_used": len(result["models"]),
                }
            )

        return comparison

    async def analyze_trends(
        self, time_range: TimeRange, metric: str
    ) -> dict[str, Any]:
        """Analyze usage trends."""
        time_filter = self._get_time_filter(time_range)

        # Determine aggregation based on time range
        if time_range == TimeRange.LAST_24_HOURS:
            group_by = "hour"
            points = 24
        elif time_range == TimeRange.LAST_7_DAYS:
            group_by = "day"
            points = 7
        elif time_range == TimeRange.LAST_30_DAYS:
            group_by = "day"
            points = 30
        else:
            group_by = "week"
            points = 12

        date_format = self._get_date_format(group_by)

        # Build aggregation based on metric
        group_stage: dict[str, Any] = {
            "_id": {"$dateToString": {"format": date_format, "date": "$timestamp"}}
        }

        if metric == "messages":
            group_stage["value"] = {"$sum": 1}
        elif metric == "costs":
            group_stage["value"] = {"$sum": "$costUsd"}
        elif metric == "sessions":
            group_stage["value"] = {"$addToSet": "$sessionId"}
        elif metric == "response_time":
            group_stage["value"] = {"$avg": "$durationMs"}

        pipeline: list[dict[str, Any]] = [
            {"$match": time_filter},
            {"$group": group_stage},
            {"$sort": {"_id": 1}},
            {"$limit": points},
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        # Process results
        if metric == "sessions":
            # Convert sets to counts
            for result in results:
                result["value"] = len(result["value"])

        # Calculate trend statistics
        values = [r["value"] or 0 for r in results]

        if len(values) > 1:
            # Simple linear regression for trend
            x = list(range(len(values)))
            n = len(values)

            sum_x = sum(x)
            sum_y = sum(values)
            sum_xy = sum(i * v for i, v in enumerate(values))
            sum_x2 = sum(i * i for i in x)

            # Slope calculation
            if n * sum_x2 - sum_x * sum_x != 0:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                trend = (
                    "increasing"
                    if slope > 0
                    else "decreasing"
                    if slope < 0
                    else "stable"
                )
            else:
                slope = 0
                trend = "stable"

            # Calculate percentage change
            if values[0] != 0:
                change_percentage = ((values[-1] - values[0]) / values[0]) * 100
            else:
                change_percentage = 100 if values[-1] > 0 else 0
        else:
            trend = "insufficient_data"
            change_percentage = 0
            slope = 0

        return {
            "metric": metric,
            "time_range": time_range.value,
            "data_points": [
                {
                    "timestamp": r["_id"],
                    "value": round(r["value"], 2)
                    if isinstance(r["value"], float)
                    else r["value"],
                }
                for r in results
            ],
            "trend": trend,
            "change_percentage": round(change_percentage, 2),
            "average": round(sum(values) / len(values), 2) if values else 0,
            "peak": max(values) if values else 0,
            "low": min(values) if values else 0,
        }

    def _get_date_format(self, group_by: str) -> str:
        """Get MongoDB date format string."""
        formats = {
            "hour": "%Y-%m-%dT%H:00:00",
            "day": "%Y-%m-%d",
            "week": "%Y-W%V",
            "month": "%Y-%m",
        }
        return formats.get(group_by, "%Y-%m-%d")

    def _calculate_trend(self, current: float, previous: float) -> float:
        """Calculate percentage change."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)

    async def _get_period_stats(self, time_filter: dict[str, Any]) -> dict[str, Any]:
        """Get basic stats for a time period."""
        # Message count
        message_count = await self.db.messages.count_documents(time_filter)

        # Session count
        session_ids = await self.db.messages.distinct("sessionId", time_filter)
        session_count = len(session_ids)

        # Project count
        project_pipeline: list[dict[str, Any]] = [
            {"$match": time_filter},
            {
                "$lookup": {
                    "from": "sessions",
                    "localField": "sessionId",
                    "foreignField": "sessionId",
                    "as": "session",
                }
            },
            {"$unwind": "$session"},
            {"$group": {"_id": "$session.projectId"}},
        ]

        project_result = await self.db.messages.aggregate(project_pipeline).to_list(
            None
        )
        project_count = len(project_result)

        # Total cost
        cost_pipeline: list[dict[str, Any]] = [
            {"$match": time_filter},
            {"$group": {"_id": None, "totalCost": {"$sum": "$costUsd"}}},
        ]

        cost_result = await self.db.messages.aggregate(cost_pipeline).to_list(1)
        total_cost = cost_result[0]["totalCost"] if cost_result else 0

        return {
            "total_messages": message_count,
            "total_sessions": session_count,
            "total_projects": project_count,
            "total_cost": total_cost or 0,
        }

    def _get_previous_period_filter(self, time_range: TimeRange) -> dict[str, Any]:
        """Get filter for previous period (for trend calculation)."""
        now = datetime.utcnow()

        if time_range == TimeRange.LAST_24_HOURS:
            start = now - timedelta(hours=48)
            end = now - timedelta(hours=24)
        elif time_range == TimeRange.LAST_7_DAYS:
            start = now - timedelta(days=14)
            end = now - timedelta(days=7)
        elif time_range == TimeRange.LAST_30_DAYS:
            start = now - timedelta(days=60)
            end = now - timedelta(days=30)
        elif time_range == TimeRange.LAST_90_DAYS:
            start = now - timedelta(days=180)
            end = now - timedelta(days=90)
        elif time_range == TimeRange.LAST_YEAR:
            start = now - timedelta(days=730)
            end = now - timedelta(days=365)
        else:
            return {}

        return {"timestamp": {"$gte": start, "$lt": end}}
