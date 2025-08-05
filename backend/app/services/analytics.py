"""Analytics service implementation."""
import math
import re
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.analytics import (
    ActivityHeatmap,
    AnalyticsSummary,
    BenchmarkComparisonMatrix,
    BenchmarkEntity,
    BenchmarkEntityType,
    BenchmarkImprovement,
    BenchmarkInsights,
    BenchmarkMetrics,
    BenchmarkPercentileRanks,
    BenchmarkResponse,
    BranchAnalytics,
    BranchComparison,
    BranchMetrics,
    BranchTopOperation,
    BranchType,
    ConversationFlowAnalytics,
    ConversationFlowEdge,
    ConversationFlowMetrics,
    ConversationFlowNode,
    ConversationPattern,
    CostAnalytics,
    CostBreakdown,
    CostBreakdownItem,
    CostBreakdownResponse,
    CostDataPoint,
    CostMetrics,
    CostPrediction,
    CostPredictionPoint,
    CostSummary,
    CostTimePoint,
    DepthCorrelations,
    DepthDistribution,
    DepthRecommendations,
    DirectoryMetrics,
    DirectoryNode,
    DirectoryTotalMetrics,
    DirectoryUsageResponse,
    DistributionBucket,
    ErrorDetail,
    ErrorDetailsResponse,
    ErrorSummary,
    ExtractedTopic,
    GitBranchAnalyticsResponse,
    HeatmapCell,
    ModelUsage,
    ModelUsageStats,
    NormalizationMethod,
    PerformanceCorrelation,
    PerformanceFactorsAnalytics,
    PopularTopic,
    ResponseTimeAnalytics,
    ResponseTimeDataPoint,
    ResponseTimePercentiles,
    SessionDepthAnalytics,
    SessionHealth,
    SuccessRateMetrics,
    TimeRange,
    TokenAnalytics,
    TokenAnalyticsDataPoint,
    TokenBreakdown,
    TokenDataPoint,
    TokenDistributionBucket,
    TokenEfficiencyDetailed,
    TokenEfficiencyMetrics,
    TokenEfficiencySummary,
    TokenFormattedValues,
    TokenPercentiles,
    TokenPerformanceCorrelation,
    TokenPerformanceFactorsAnalytics,
    TokenUsageStats,
    ToolUsage,
    ToolUsageDetailed,
    ToolUsageSummary,
    TopicCategory,
    TopicCombination,
    TopicExtractionResponse,
    TopicSuggestionResponse,
)


class AnalyticsService:
    """Service for analytics operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    def _safe_float(self, value: Any) -> float:
        """Safely convert a value to float, handling Decimal128."""
        if value is None:
            return 0.0
        if hasattr(value, "to_decimal"):
            # It's a Decimal128 object
            return float(str(value))
        return float(value)

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

    async def _resolve_session_id(self, session_id: str) -> str | None:
        """Resolve session ID from either MongoDB _id or sessionId UUID format."""
        if not session_id:
            return None

        # First try as MongoDB ObjectId
        try:
            if ObjectId.is_valid(session_id):
                doc = await self.db.sessions.find_one(
                    {"_id": ObjectId(session_id)}, {"sessionId": 1}
                )
                if doc:
                    return str(doc.get("sessionId"))
        except Exception:
            pass

        # If not found or not valid ObjectId, assume it's already a sessionId UUID
        # Verify it exists
        doc = await self.db.sessions.find_one(
            {"sessionId": session_id}, {"sessionId": 1}
        )
        if doc:
            return session_id

        return None

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
                    avg_cost=round(self._safe_float(result["avgCost"]), 4)
                    if result["avgCost"]
                    else None,
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
        total_cost = 0.0
        total_messages = 0
        cost_by_model_global: dict[str, float] = {}

        for result in results:
            # Parse timestamp
            timestamp = datetime.strptime(result["_id"], date_format)

            # Process model costs
            cost_by_model = {}
            for model_cost in result["costByModel"]:
                model = model_cost["model"] or "unknown"
                cost = self._safe_float(model_cost["cost"])
                cost_by_model[model] = cost
                cost_by_model_global[model] = cost_by_model_global.get(model, 0) + cost

            data_points.append(
                CostDataPoint(
                    timestamp=timestamp,
                    cost=round(self._safe_float(result["totalCost"]), 4),
                    message_count=result["messageCount"],
                    cost_by_model=cost_by_model,
                )
            )

            total_cost += self._safe_float(result["totalCost"])
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
            total_cost = self._safe_float(result.get("totalCost", 0))

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
                    "sessions": {"$addToSet": "$sessionId"},
                }
            },
            {
                "$project": {
                    "messageCount": 1,
                    "totalCost": 1,
                    "avgResponseTime": 1,
                    "modelCount": {"$size": "$models"},
                    "sessionCount": {"$size": "$sessions"},
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
        max_cost = 0.0
        min_response_time = float("inf")

        for result in results:
            project_id = str(result["_id"])
            project_name = project_map.get(project_id, "Unknown")
            message_count = result["messageCount"]
            total_cost = self._safe_float(result.get("totalCost", 0))
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
                    "session_count": result["sessionCount"],
                    "total_cost": round(total_cost, 2),
                    "avg_cost_per_message": round(
                        total_cost / message_count if message_count > 0 else 0, 4
                    ),
                    "avg_response_time_ms": avg_response,
                    "models_used": result["modelCount"],
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
        ]

        # Add projection stage for sessions metric to count set size
        if metric == "sessions":
            pipeline.append({"$project": {"_id": 1, "value": {"$size": "$value"}}})

        pipeline.extend(
            [
                {"$sort": {"_id": 1}},
                {"$limit": points},
            ]
        )

        results = await self.db.messages.aggregate(pipeline).to_list(None)

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
        # Convert Decimal128 to float if needed
        if hasattr(current, "to_decimal"):
            current = float(str(current))
        if hasattr(previous, "to_decimal"):
            previous = float(str(previous))

        # Ensure we have numeric values
        current = float(current) if current is not None else 0.0
        previous = float(previous) if previous is not None else 0.0

        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)

    async def _get_period_stats(self, time_filter: dict[str, Any]) -> dict[str, Any]:
        """Get basic stats for a time period using a single optimized aggregation."""
        pipeline: list[dict[str, Any]] = [
            {"$match": time_filter},
            {
                "$facet": {
                    # Count messages and calculate cost
                    "messageCostStats": [
                        {
                            "$group": {
                                "_id": None,
                                "count": {"$sum": 1},
                                "totalCost": {"$sum": "$costUsd"},
                            }
                        }
                    ],
                    # Count unique sessions
                    "sessionStats": [
                        {"$group": {"_id": "$sessionId"}},
                        {"$count": "count"},
                    ],
                    # Count unique projects (optimized with direct lookup)
                    "projectStats": [
                        # Group by sessionId first to reduce lookup size
                        {"$group": {"_id": "$sessionId"}},
                        {
                            "$lookup": {
                                "from": "sessions",
                                "localField": "_id",
                                "foreignField": "sessionId",
                                "as": "session",
                            }
                        },
                        {"$unwind": "$session"},
                        {"$group": {"_id": "$session.projectId"}},
                        {"$count": "count"},
                    ],
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)

        if not result:
            return {
                "total_messages": 0,
                "total_sessions": 0,
                "total_projects": 0,
                "total_cost": 0.0,
            }

        facet_results = result[0]

        # Extract message and cost stats
        message_cost_stats = facet_results.get("messageCostStats", [])
        message_count = message_cost_stats[0]["count"] if message_cost_stats else 0
        total_cost = message_cost_stats[0]["totalCost"] if message_cost_stats else 0

        # Extract session count
        session_stats = facet_results.get("sessionStats", [])
        session_count = session_stats[0]["count"] if session_stats else 0

        # Extract project count
        project_stats = facet_results.get("projectStats", [])
        project_count = project_stats[0]["count"] if project_stats else 0

        # Convert Decimal128 to float if needed
        if hasattr(total_cost, "to_decimal"):
            total_cost = float(str(total_cost))
        else:
            total_cost = float(total_cost) if total_cost is not None else 0.0

        return {
            "total_messages": message_count,
            "total_sessions": session_count,
            "total_projects": project_count,
            "total_cost": total_cost,
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

    async def get_tool_usage_summary(
        self,
        session_id: str | None = None,
        project_id: str | None = None,
        time_range: TimeRange = TimeRange.LAST_30_DAYS,
    ) -> ToolUsageSummary:
        """Get tool usage summary for stat card."""
        # Build match filter
        match_filter = self._get_time_filter(time_range)

        if session_id:
            resolved_id = await self._resolve_session_id(session_id)
            if resolved_id:
                match_filter["sessionId"] = resolved_id
            else:
                # Session not found, return empty result
                return ToolUsageSummary(
                    total_tool_calls=0,
                    unique_tools=0,
                    most_used_tool=None,
                )
        elif project_id:
            # Get session IDs for the project
            session_ids = await self.db.sessions.distinct(
                "sessionId", {"projectId": ObjectId(project_id)}
            )
            match_filter["sessionId"] = {"$in": session_ids}

        # Aggregation pipeline to extract and count tool calls
        pipeline: list[dict[str, Any]] = [
            {"$match": match_filter},
            # Look for messages with tool_calls in message field
            {
                "$match": {
                    "$or": [
                        {"message.tool_calls": {"$exists": True, "$ne": None}},
                        {"type": "tool_use"},  # Also count tool_use messages
                    ]
                }
            },
            # Unwind tool_calls array if it exists
            {
                "$addFields": {
                    "tools": {
                        "$cond": {
                            "if": {"$isArray": "$message.tool_calls"},
                            "then": "$message.tool_calls",
                            "else": {
                                "$cond": {
                                    "if": {"$eq": ["$type", "tool_use"]},
                                    "then": [
                                        {
                                            "name": "$messageData.name",
                                            "type": "tool_use",
                                        }
                                    ],
                                    "else": [],
                                }
                            },
                        }
                    }
                }
            },
            {"$unwind": {"path": "$tools", "preserveNullAndEmptyArrays": False}},
            # Extract tool name
            {
                "$addFields": {
                    "tool_name": {
                        "$cond": {
                            "if": {"$type": "$tools.name"},
                            "then": "$tools.name",
                            "else": {
                                "$cond": {
                                    "if": {"$type": "$tools.function.name"},
                                    "then": "$tools.function.name",
                                    "else": "unknown",
                                }
                            },
                        }
                    }
                }
            },
            # Group by tool name to count occurrences
            {
                "$group": {
                    "_id": "$tool_name",
                    "count": {"$sum": 1},
                }
            },
            # Sort by count descending
            {"$sort": {"count": -1}},
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        total_tool_calls = sum(result["count"] for result in results)
        unique_tools = len(results)
        most_used_tool = results[0]["_id"] if results else None

        return ToolUsageSummary(
            total_tool_calls=total_tool_calls,
            unique_tools=unique_tools,
            most_used_tool=most_used_tool,
        )

    async def get_tool_usage_detailed(
        self,
        session_id: str | None = None,
        project_id: str | None = None,
        time_range: TimeRange = TimeRange.LAST_30_DAYS,
    ) -> ToolUsageDetailed:
        """Get detailed tool usage analytics."""
        # Build match filter
        match_filter = self._get_time_filter(time_range)

        if session_id:
            resolved_id = await self._resolve_session_id(session_id)
            if resolved_id:
                match_filter["sessionId"] = resolved_id
            else:
                # Session not found, return empty result
                return ToolUsageDetailed(
                    tools=[],
                    total_calls=0,
                    session_id=session_id,
                    time_range=time_range,
                )
        elif project_id:
            # Get session IDs for the project
            session_ids = await self.db.sessions.distinct(
                "sessionId", {"projectId": ObjectId(project_id)}
            )
            match_filter["sessionId"] = {"$in": session_ids}

        # Aggregation pipeline for detailed tool usage
        pipeline: list[dict[str, Any]] = [
            {"$match": match_filter},
            # Look for messages with tool_calls
            {
                "$match": {
                    "$or": [
                        {"message.tool_calls": {"$exists": True, "$ne": None}},
                        {"type": "tool_use"},
                    ]
                }
            },
            # Process tool calls
            {
                "$addFields": {
                    "tools": {
                        "$cond": {
                            "if": {"$isArray": "$message.tool_calls"},
                            "then": "$message.tool_calls",
                            "else": {
                                "$cond": {
                                    "if": {"$eq": ["$type", "tool_use"]},
                                    "then": [
                                        {
                                            "name": "$messageData.name",
                                            "type": "tool_use",
                                        }
                                    ],
                                    "else": [],
                                }
                            },
                        }
                    }
                }
            },
            {"$unwind": {"path": "$tools", "preserveNullAndEmptyArrays": False}},
            # Extract tool name and add timestamp
            {
                "$addFields": {
                    "tool_name": {
                        "$cond": {
                            "if": {"$type": "$tools.name"},
                            "then": "$tools.name",
                            "else": {
                                "$cond": {
                                    "if": {"$type": "$tools.function.name"},
                                    "then": "$tools.function.name",
                                    "else": "unknown",
                                }
                            },
                        }
                    }
                }
            },
            # Filter out documents with null or unknown tool names
            {"$match": {"tool_name": {"$nin": [None, "unknown"]}}},
            # Group by tool name
            {
                "$group": {
                    "_id": "$tool_name",
                    "count": {"$sum": 1},
                    "last_used": {"$max": "$timestamp"},
                }
            },
            # Sort by count descending
            {"$sort": {"count": -1}},
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        # Calculate total calls and process results
        total_calls = sum(result["count"] for result in results)
        tools = []

        for result in results:
            tool_name = result.get("_id")
            if not tool_name:  # Skip if tool name is None or empty
                continue

            count = result["count"]
            percentage = (count / total_calls * 100) if total_calls > 0 else 0
            # Ensure percentage doesn't exceed 100%
            percentage = min(percentage, 100.0)

            # Categorize tools based on common patterns
            category = self._categorize_tool(tool_name)

            tools.append(
                ToolUsage(
                    name=tool_name,
                    count=count,
                    percentage=round(percentage, 1),
                    category=category,
                    last_used=result["last_used"],
                )
            )

        return ToolUsageDetailed(
            tools=tools,
            total_calls=total_calls,
            session_id=session_id,
            time_range=time_range,
        )

    def _categorize_tool(self, tool_name: str | None) -> str:
        """Categorize tool based on its name."""
        if not tool_name:
            return "unknown"

        tool_lower = tool_name.lower()

        # File operations
        if any(
            keyword in tool_lower
            for keyword in ["file", "read", "write", "edit", "create"]
        ):
            return "file"

        # Search operations
        if any(keyword in tool_lower for keyword in ["search", "find", "grep", "glob"]):
            return "search"

        # Execution operations
        if any(keyword in tool_lower for keyword in ["bash", "exec", "run", "command"]):
            return "execution"

        # Default category
        return "other"

    async def get_conversation_flow(
        self, session_id: str, include_sidechains: bool = True
    ) -> ConversationFlowAnalytics:
        """Get conversation flow analytics for visualization."""
        # Resolve session ID
        resolved_id = await self._resolve_session_id(session_id)
        if not resolved_id:
            return ConversationFlowAnalytics(
                nodes=[],
                edges=[],
                metrics=ConversationFlowMetrics(
                    max_depth=0,
                    branch_count=0,
                    sidechain_percentage=0.0,
                    avg_branch_length=0.0,
                    total_nodes=0,
                    total_cost=0.0,
                    avg_response_time_ms=None,
                ),
                session_id=session_id,
            )

        # Build match filter
        match_filter: dict[str, Any] = {"sessionId": resolved_id}
        if not include_sidechains:
            match_filter["isSidechain"] = {"$ne": True}

        # Get all messages for the session
        messages = (
            await self.db.messages.find(
                match_filter,
                {
                    "uuid": 1,
                    "parentUuid": 1,
                    "type": 1,
                    "isSidechain": 1,
                    "costUsd": 1,
                    "durationMs": 1,
                    "timestamp": 1,
                    "message": 1,
                    "toolUseResult": 1,
                },
            )
            .sort("timestamp", 1)
            .to_list(None)
        )

        if not messages:
            return ConversationFlowAnalytics(
                nodes=[],
                edges=[],
                metrics=ConversationFlowMetrics(
                    max_depth=0,
                    branch_count=0,
                    sidechain_percentage=0.0,
                    avg_branch_length=0.0,
                    total_nodes=0,
                    total_cost=0.0,
                    avg_response_time_ms=None,
                ),
                session_id=session_id,
            )

        # Build nodes
        nodes = []
        node_lookup = {}
        total_cost = 0.0
        response_times = []

        for msg in messages:
            # Calculate tool count
            tool_count = 0
            if msg.get("message") and msg["message"].get("tool_calls"):
                tool_count = len(msg["message"]["tool_calls"])
            elif msg.get("toolUseResult"):
                tool_count = 1

            # Generate summary from message content
            summary = self._generate_message_summary(msg)

            cost = self._safe_float(msg.get("costUsd", 0))
            total_cost += cost

            duration_ms = msg.get("durationMs")
            if duration_ms:
                response_times.append(duration_ms)

            node = ConversationFlowNode(
                id=msg["uuid"],
                parent_id=msg.get("parentUuid"),
                type=msg["type"],
                is_sidechain=msg.get("isSidechain", False),
                cost=cost,
                duration_ms=duration_ms,
                tool_count=tool_count,
                summary=summary,
                timestamp=msg["timestamp"],
            )

            nodes.append(node)
            node_lookup[msg["uuid"]] = node

        # Build edges
        edges = []
        for node in nodes:
            if node.parent_id and node.parent_id in node_lookup:
                edge_type = "sidechain" if node.is_sidechain else "main"
                edges.append(
                    ConversationFlowEdge(
                        source=node.parent_id,
                        target=node.id,
                        type=edge_type,
                    )
                )

        # Calculate metrics
        metrics = self._calculate_conversation_metrics(nodes, edges)
        metrics.total_cost = round(total_cost, 2)
        if response_times:
            metrics.avg_response_time_ms = round(
                sum(response_times) / len(response_times), 2
            )

        return ConversationFlowAnalytics(
            nodes=nodes,
            edges=edges,
            metrics=metrics,
            session_id=session_id,
        )

    async def get_session_health(
        self,
        session_id: str | None = None,
        time_range: TimeRange = TimeRange.LAST_30_DAYS,
    ) -> SessionHealth:
        """Get session health metrics based on tool execution results."""
        # Build match filter
        match_filter = self._get_time_filter(time_range)

        if session_id:
            match_filter["sessionId"] = session_id

        # Pipeline to analyze toolUseResult fields for success/error detection
        pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    **match_filter,
                    "toolUseResult": {"$exists": True, "$ne": None},
                }
            },
            {
                "$project": {
                    "sessionId": 1,
                    "timestamp": 1,
                    "toolUseResult": 1,
                    "isSuccess": {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {
                                        "$regexMatch": {
                                            "input": {
                                                "$convert": {
                                                    "input": "$toolUseResult",
                                                    "to": "string",
                                                    "onError": "",
                                                    "onNull": "",
                                                }
                                            },
                                            "regex": "error|Error|ERROR|failed|Failed|FAILED",
                                        }
                                    },
                                    {
                                        "$ne": [
                                            {"$ifNull": ["$toolUseResult.error", None]},
                                            None,
                                        ]
                                    },
                                    {
                                        "$ne": [
                                            {
                                                "$ifNull": [
                                                    "$toolUseResult.stderr",
                                                    None,
                                                ]
                                            },
                                            None,
                                        ]
                                    },
                                    {
                                        "$eq": [
                                            {"$ifNull": ["$toolUseResult.exitCode", 0]},
                                            {"$ne": [0, 0]},
                                        ]
                                    },
                                ]
                            },
                            "then": False,
                            "else": True,
                        }
                    },
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_operations": {"$sum": 1},
                    "successful_operations": {"$sum": {"$cond": ["$isSuccess", 1, 0]}},
                    "error_count": {"$sum": {"$cond": ["$isSuccess", 0, 1]}},
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)

        if not result:
            return SessionHealth(
                success_rate=100.0,
                total_operations=0,
                error_count=0,
                health_status="excellent",
            )

        data = result[0]
        total_ops = data["total_operations"]
        error_count = data["error_count"]
        success_rate = (
            (data["successful_operations"] / total_ops * 100)
            if total_ops > 0
            else 100.0
        )

        # Determine health status based on success rate
        if success_rate > 95:
            health_status = "excellent"
        elif success_rate > 80:
            health_status = "good"
        elif success_rate > 60:
            health_status = "fair"
        else:
            health_status = "poor"

        return SessionHealth(
            success_rate=round(success_rate, 1),
            total_operations=total_ops,
            error_count=error_count,
            health_status=health_status,
        )

    async def get_detailed_errors(
        self,
        session_id: str | None = None,
        time_range: TimeRange = TimeRange.LAST_30_DAYS,
        error_severity: str | None = None,
    ) -> ErrorDetailsResponse:
        """Get detailed error analytics with improved detection."""
        # Build match filter
        match_filter = self._get_time_filter(time_range)

        if session_id:
            resolved_id = await self._resolve_session_id(session_id)
            if resolved_id:
                match_filter["sessionId"] = resolved_id
            else:
                # Session not found, return empty result
                return ErrorDetailsResponse(
                    errors=[],
                    error_summary=ErrorSummary(by_type={}, by_tool={}),
                )

        errors = []
        error_by_type: dict[str, int] = {}
        error_by_tool: dict[str, int] = {}

        # 1. Find tool execution errors with better detection and tool name resolution
        tool_error_pipeline: List[Dict[str, Any]] = [
            {
                "$match": {
                    **match_filter,
                    "type": "tool_result",
                    "toolUseResult": {"$exists": True, "$ne": None},
                }
            },
            {
                "$lookup": {
                    "from": "messages",
                    "let": {"parent_uuid": "$parentUuid"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$uuid", "$$parent_uuid"]}}},
                        {"$project": {"messageData.name": 1}},
                    ],
                    "as": "tool_use_info",
                }
            },
            {"$sort": {"timestamp": -1}},
            {"$limit": 100},
        ]

        tool_results = await self.db.messages.aggregate(tool_error_pipeline).to_list(
            100
        )

        for doc in tool_results:
            tool_result = doc.get("toolUseResult", {})

            # Extract tool name from parent tool_use message
            tool_name = "unknown"
            if doc.get("tool_use_info"):
                tool_name = (
                    doc["tool_use_info"][0]
                    .get("messageData", {})
                    .get("name", "unknown")
                )

            # Better error detection logic
            error_detail = None

            # Check for explicit error field
            if (
                isinstance(tool_result, dict)
                and "error" in tool_result
                and tool_result["error"]
            ):
                error_detail = ErrorDetail(
                    timestamp=doc["timestamp"],
                    tool=tool_name,
                    error_type="execution_error",
                    severity="critical",
                    message=str(tool_result["error"])[:500],
                    context=f"Session: {doc['sessionId'][:8]}...",
                )

            # Check for meaningful stderr (not just warnings)
            elif (
                isinstance(tool_result, dict)
                and "stderr" in tool_result
                and tool_result["stderr"]
            ):
                stderr = str(tool_result["stderr"])
                # Only consider it an error if it contains actual error indicators
                error_indicators = [
                    "error:",
                    "fatal:",
                    "exception",
                    "traceback",
                    "permission denied",
                    "not found",
                    "no such file",
                    "cannot",
                    "failed to",
                    "unable to",
                ]
                if any(indicator in stderr.lower() for indicator in error_indicators):
                    error_detail = ErrorDetail(
                        timestamp=doc["timestamp"],
                        tool=tool_name,
                        error_type="stderr_error",
                        severity="warning",
                        message=stderr[:500],
                        context=f"Command: {tool_result.get('command', 'unknown')[:50]}",
                    )

            # Check for non-zero exit codes
            elif (
                isinstance(tool_result, dict)
                and "exitCode" in tool_result
                and tool_result["exitCode"] != 0
            ):
                stdout = tool_result.get("stdout", "")
                stderr = tool_result.get("stderr", "")
                message = f"Exit code {tool_result['exitCode']}"
                if stderr:
                    message += f": {stderr[:200]}"
                elif stdout:
                    message += f": {stdout[:200]}"

                error_detail = ErrorDetail(
                    timestamp=doc["timestamp"],
                    tool=tool_name,
                    error_type="exit_code_error",
                    severity="warning",
                    message=message,
                    context=f"Session: {doc['sessionId'][:8]}...",
                )

            if error_detail:
                # Apply severity filter
                if not error_severity or error_detail.severity == error_severity:
                    errors.append(error_detail)
                    error_by_type[error_detail.error_type] = (
                        error_by_type.get(error_detail.error_type, 0) + 1
                    )
                    error_by_tool[error_detail.tool] = (
                        error_by_tool.get(error_detail.tool, 0) + 1
                    )

        # 2. Find API errors in assistant messages
        api_error_pipeline: List[Dict[str, Any]] = [
            {
                "$match": {
                    **match_filter,
                    "type": "assistant",
                    "$or": [
                        {"content": {"$regex": "API Error:", "$options": "i"}},
                        {"content": {"$regex": "overloaded_error", "$options": "i"}},
                        {"content": {"$regex": "rate_limit_error", "$options": "i"}},
                    ],
                }
            },
            {"$sort": {"timestamp": -1}},
            {"$limit": 50},
        ]

        api_errors = await self.db.messages.aggregate(api_error_pipeline).to_list(50)

        for doc in api_errors:
            content = str(doc.get("content", ""))

            # Extract error details from API errors
            error_type = "api_error"
            severity = "critical"
            message = content[:500]

            if "overloaded" in content.lower():
                error_type = "api_overloaded"
                message = "Claude API is overloaded"
            elif "rate_limit" in content.lower():
                error_type = "api_rate_limit"
                message = "Claude API rate limit exceeded"

            error_detail = ErrorDetail(
                timestamp=doc["timestamp"],
                tool="claude_api",
                error_type=error_type,
                severity=severity,
                message=message,
                context=f"Model: {doc.get('model', 'unknown')}",
            )

            if not error_severity or error_detail.severity == error_severity:
                errors.append(error_detail)
                error_by_type[error_detail.error_type] = (
                    error_by_type.get(error_detail.error_type, 0) + 1
                )
                error_by_tool[error_detail.tool] = (
                    error_by_tool.get(error_detail.tool, 0) + 1
                )

        # 3. Find tool errors mentioned in assistant messages (e.g., "Failed to read file")
        tool_mention_pipeline: List[Dict[str, Any]] = [
            {
                "$match": {
                    **match_filter,
                    "type": "assistant",
                    "$or": [
                        {"content": {"$regex": "Failed to|failed to", "$options": "i"}},
                        {"content": {"$regex": "Error:|ERROR:", "$options": "i"}},
                        {"content": {"$regex": "Could not|could not", "$options": "i"}},
                        {"content": {"$regex": "Unable to|unable to", "$options": "i"}},
                    ],
                }
            },
            {"$sort": {"timestamp": -1}},
            {"$limit": 50},
        ]

        tool_mentions = await self.db.messages.aggregate(tool_mention_pipeline).to_list(
            50
        )

        for doc in tool_mentions:
            content = str(doc.get("content", ""))

            # Skip if it's already captured as API error
            if "API Error:" in content:
                continue

            # Extract error context
            lines = content.split("\n")
            error_lines = []
            for line in lines:
                lower_line = line.lower()
                if any(
                    phrase in lower_line
                    for phrase in ["failed to", "error:", "could not", "unable to"]
                ):
                    error_lines.append(line.strip())

            if error_lines:
                message = " | ".join(error_lines[:3])[:500]

                # Try to identify the tool from context
                tool_name = "unknown"
                tool_keywords = {
                    "read": ["read", "reading", "file"],
                    "write": ["write", "writing", "save", "create"],
                    "bash": ["command", "execute", "run", "bash"],
                    "search": ["search", "find", "grep"],
                    "edit": ["edit", "modify", "update"],
                }

                for tool, keywords in tool_keywords.items():
                    if any(kw in message.lower() for kw in keywords):
                        tool_name = tool
                        break

                error_detail = ErrorDetail(
                    timestamp=doc["timestamp"],
                    tool=tool_name,
                    error_type="operation_failed",
                    severity="warning",
                    message=message,
                    context=f"Session: {doc['sessionId'][:8]}...",
                )

                if not error_severity or error_detail.severity == error_severity:
                    errors.append(error_detail)
                    error_by_type[error_detail.error_type] = (
                        error_by_type.get(error_detail.error_type, 0) + 1
                    )
                    error_by_tool[error_detail.tool] = (
                        error_by_tool.get(error_detail.tool, 0) + 1
                    )

        # Sort errors by timestamp descending
        errors.sort(key=lambda x: x.timestamp, reverse=True)

        # Limit to most recent errors
        errors = errors[:50]

        error_summary = ErrorSummary(by_type=error_by_type, by_tool=error_by_tool)

        return ErrorDetailsResponse(errors=errors, error_summary=error_summary)

    async def get_success_rate(
        self,
        session_id: str | None = None,
        time_range: TimeRange = TimeRange.LAST_30_DAYS,
    ) -> SuccessRateMetrics:
        """Get success rate metrics based on tool execution results."""
        # Build match filter
        match_filter = self._get_time_filter(time_range)

        if session_id:
            match_filter["sessionId"] = session_id

        # Pipeline to calculate success rates
        pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    **match_filter,
                    "toolUseResult": {"$exists": True, "$ne": None},
                }
            },
            {
                "$project": {
                    "isSuccess": {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {
                                        "$regexMatch": {
                                            "input": {
                                                "$convert": {
                                                    "input": "$toolUseResult",
                                                    "to": "string",
                                                    "onError": "",
                                                    "onNull": "",
                                                }
                                            },
                                            "regex": "error|Error|ERROR|failed|Failed|FAILED",
                                        }
                                    },
                                    {
                                        "$ne": [
                                            {"$ifNull": ["$toolUseResult.error", None]},
                                            None,
                                        ]
                                    },
                                    {
                                        "$ne": [
                                            {
                                                "$ifNull": [
                                                    "$toolUseResult.stderr",
                                                    None,
                                                ]
                                            },
                                            None,
                                        ]
                                    },
                                    {
                                        "$eq": [
                                            {"$ifNull": ["$toolUseResult.exitCode", 0]},
                                            {"$ne": [0, 0]},
                                        ]
                                    },
                                ]
                            },
                            "then": False,
                            "else": True,
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_operations": {"$sum": 1},
                    "successful_operations": {"$sum": {"$cond": ["$isSuccess", 1, 0]}},
                    "failed_operations": {"$sum": {"$cond": ["$isSuccess", 0, 1]}},
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)

        if not result:
            return SuccessRateMetrics(
                success_rate=100.0,
                total_operations=0,
                successful_operations=0,
                failed_operations=0,
                time_range=time_range,
            )

        data = result[0]
        total_ops = data["total_operations"]
        successful_ops = data["successful_operations"]
        failed_ops = data["failed_operations"]
        # Calculate success rate, defaulting to 0% when no operations (more logical than 100%)
        success_rate = (successful_ops / total_ops * 100) if total_ops > 0 else 0.0
        # Ensure percentage is within valid range
        success_rate = min(max(success_rate, 0.0), 100.0)

        return SuccessRateMetrics(
            success_rate=round(success_rate, 1),
            total_operations=total_ops,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            time_range=time_range,
        )

    def _generate_message_summary(self, message: dict) -> str:
        """Generate a brief summary of message content."""
        msg_content = message.get("message", {})

        if not msg_content:
            return ""

        # For user messages
        if message["type"] == "user":
            content = msg_content.get("content", "")
            if isinstance(content, str):
                # Truncate long content
                return content[:100] + "..." if len(content) > 100 else content
            elif isinstance(content, list) and content:
                # Handle content arrays
                first_item = content[0]
                if isinstance(first_item, dict) and "text" in first_item:
                    text = str(first_item["text"])
                    return text[:100] + "..." if len(text) > 100 else text

        # For assistant messages
        elif message["type"] == "assistant":
            content = msg_content.get("content", "")
            if isinstance(content, str):
                return content[:100] + "..." if len(content) > 100 else content

            # Check for tool calls
            if msg_content.get("tool_calls"):
                tool_names = [
                    tc.get("function", {}).get("name", "unknown")
                    for tc in msg_content["tool_calls"]
                ]
                return f"Used tools: {', '.join(tool_names)}"

        # For tool use/result messages
        elif message["type"] == "tool_use":
            tool_name = msg_content.get("name", "unknown")
            return f"Tool: {tool_name}"

        return ""

    def _calculate_conversation_metrics(
        self, nodes: list[ConversationFlowNode], edges: list[ConversationFlowEdge]
    ) -> ConversationFlowMetrics:
        """Calculate conversation flow metrics."""
        # Build adjacency list for tree traversal
        children: dict[str, list[str]] = {}
        roots = set()

        for node in nodes:
            if node.parent_id is None:
                roots.add(node.id)
            else:
                if node.parent_id not in children:
                    children[node.parent_id] = []
                children[node.parent_id].append(node.id)

        # Calculate max depth
        max_depth = 0
        for root in roots:
            depth = self._calculate_tree_depth(root, children, 0)
            max_depth = max(max_depth, depth)

        # Count branches (nodes with multiple children)
        branch_count = sum(1 for node_id in children if len(children[node_id]) > 1)

        # Calculate sidechain percentage
        sidechain_count = sum(1 for node in nodes if node.is_sidechain)
        sidechain_percentage = (sidechain_count / len(nodes) * 100) if nodes else 0

        # Calculate average branch length
        branch_lengths: list[int] = []
        for root in roots:
            lengths: list[int] = []
            self._calculate_branch_lengths(root, children, 0, lengths)
            branch_lengths.extend(lengths)

        avg_branch_length = (
            sum(branch_lengths) / len(branch_lengths) if branch_lengths else 0
        )

        # Calculate total cost and average response time
        total_cost = sum(node.cost for node in nodes)
        response_times = [
            node.duration_ms for node in nodes if node.duration_ms is not None
        ]
        avg_response_time_ms = (
            sum(response_times) / len(response_times) if response_times else None
        )

        return ConversationFlowMetrics(
            max_depth=max_depth,
            branch_count=branch_count,
            sidechain_percentage=round(sidechain_percentage, 1),
            avg_branch_length=round(avg_branch_length, 1),
            total_nodes=len(nodes),
            total_cost=total_cost,
            avg_response_time_ms=avg_response_time_ms,
        )

    def _calculate_tree_depth(
        self, node_id: str, children: dict, current_depth: int
    ) -> int:
        """Recursively calculate the maximum depth of a tree."""
        if node_id not in children:
            return current_depth

        max_child_depth = current_depth
        for child_id in children[node_id]:
            child_depth = self._calculate_tree_depth(
                child_id, children, current_depth + 1
            )
            max_child_depth = max(max_child_depth, child_depth)

        return max_child_depth

    def _calculate_branch_lengths(
        self, node_id: str, children: dict, current_length: int, lengths: list
    ) -> None:
        """Recursively calculate branch lengths."""
        if node_id not in children:
            # Leaf node - record the length
            lengths.append(current_length)
            return

        # Continue down each branch
        for child_id in children[node_id]:
            self._calculate_branch_lengths(
                child_id, children, current_length + 1, lengths
            )

    async def get_directory_usage(
        self,
        time_range: TimeRange = TimeRange.LAST_30_DAYS,
        depth: int = 3,
        min_cost: float = 0.0,
    ) -> DirectoryUsageResponse:
        """Get directory usage analytics with hierarchical tree structure."""
        time_filter = self._get_time_filter(time_range)

        # Aggregation pipeline to get directory usage data
        pipeline: list[dict[str, Any]] = [
            {"$match": {**time_filter, "cwd": {"$exists": True, "$ne": None}}},
            {
                "$group": {
                    "_id": "$cwd",
                    "total_cost": {"$sum": "$costUsd"},
                    "message_count": {"$sum": 1},
                    "session_count": {"$addToSet": "$sessionId"},
                    "last_active": {"$max": "$timestamp"},
                }
            },
            {"$match": {"total_cost": {"$gte": min_cost}}},
            {
                "$project": {
                    "path": "$_id",
                    "total_cost": {"$ifNull": ["$total_cost", 0]},
                    "message_count": 1,
                    "session_count": {"$size": "$session_count"},
                    "last_active": 1,
                }
            },
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        if not results:
            # Return empty tree structure
            empty_metrics = DirectoryMetrics(
                cost=0.0,
                messages=0,
                sessions=0,
                avg_cost_per_session=0.0,
                last_active=datetime.utcnow(),
            )
            empty_node = DirectoryNode(
                path="/",
                name="root",
                metrics=empty_metrics,
                children=[],
                percentage_of_total=0.0,
            )
            total_metrics = DirectoryTotalMetrics(
                total_cost=0.0,
                total_messages=0,
                unique_directories=0,
            )
            return DirectoryUsageResponse(
                root=empty_node,
                total_metrics=total_metrics,
                time_range=time_range,
            )

        # Calculate total metrics from raw results
        # Note: We'll recalculate total_cost from the root node to avoid double-counting
        total_messages = sum(r["message_count"] for r in results)
        unique_directories = len(results)

        # Build hierarchical tree structure
        # First pass: build tree with temporary total
        temp_total = sum(self._safe_float(r.get("total_cost", 0)) for r in results)
        root_node = self._build_directory_tree(results, depth, temp_total)

        # Use the root node's aggregated cost as the true total
        # This avoids double-counting from nested directories
        total_cost = root_node.metrics.cost

        # Rebuild the tree with the correct total for accurate percentages
        root_node = self._build_directory_tree(results, depth, total_cost)

        total_metrics = DirectoryTotalMetrics(
            total_cost=round(total_cost, 2),
            total_messages=total_messages,
            unique_directories=unique_directories,
        )

        return DirectoryUsageResponse(
            root=root_node,
            total_metrics=total_metrics,
            time_range=time_range,
        )

    def _build_directory_tree(
        self, directory_data: list[dict], max_depth: int, total_cost: float
    ) -> DirectoryNode:
        """Build hierarchical directory tree from flat directory data."""
        # Create a tree structure from paths
        tree: dict[str, Any] = {}

        for data in directory_data:
            path = data["path"]
            if not path:
                continue

            # Normalize path across OS
            normalized_path = self._normalize_path(path)

            # Split path into components and limit depth
            parts = [p for p in normalized_path.split("/") if p]
            if max_depth > 0:
                parts = parts[:max_depth]

            # Build tree structure
            current = tree
            full_path = ""

            for i, part in enumerate(parts):
                full_path = full_path + "/" + part if full_path else "/" + part
                is_last_part = i == len(parts) - 1

                if part not in current:
                    current[part] = {
                        "_data": {
                            "path": full_path,
                            "name": part,
                            "cost": 0.0,
                            "messages": 0,
                            "sessions": 0,
                            "last_active": datetime.min,
                        },
                        "_children": {},
                    }

                node_data = current[part]["_data"]

                # Only add the full cost and messages to the deepest node
                # This prevents double counting when aggregating up the tree
                if is_last_part:
                    node_data["cost"] += self._safe_float(data.get("total_cost", 0))
                    node_data["messages"] += data["message_count"]

                # Always update sessions and last_active for all nodes in the path
                # Since we only have session_count (not the actual IDs), we'll track it differently
                if is_last_part:
                    node_data["sessions"] = data.get("session_count", 0)
                if data["last_active"] > node_data["last_active"]:
                    node_data["last_active"] = data["last_active"]

                current = current[part]["_children"]

        # Convert tree structure to DirectoryNode objects
        # Create a root node structure
        root_tree = {
            "_data": {
                "path": "/",
                "name": "root",
                "cost": 0.0,
                "messages": 0,
                "sessions": 0,
                "last_active": datetime.min,
            },
            "_children": tree,
        }
        return self._tree_to_directory_node(root_tree, "/", "root", total_cost)

    def _normalize_path(self, path: str) -> str:
        """Normalize directory path across different OS."""
        if not path:
            return ""

        # Handle Windows paths
        if "\\" in path:
            path = path.replace("\\", "/")

        # Remove drive letters for Windows paths
        if len(path) > 1 and path[1] == ":":
            path = path[2:]

        # Ensure starts with /
        if not path.startswith("/"):
            path = "/" + path

        # Remove trailing slash except for root
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]

        return path

    def _tree_to_directory_node(
        self, tree: dict, path: str, name: str, total_cost: float
    ) -> DirectoryNode:
        """Convert tree dictionary to DirectoryNode object."""
        # Calculate aggregate metrics for this node
        total_node_cost = 0.0
        total_messages = 0
        total_sessions = 0
        latest_activity = datetime.min

        # Collect data from all descendants
        def collect_metrics(node_tree: dict) -> None:
            nonlocal total_node_cost, total_messages, total_sessions, latest_activity

            for child_name, child_data in node_tree.items():
                if child_name == "_data":
                    continue

                child_info = child_data["_data"]
                total_node_cost += child_info["cost"]
                total_messages += child_info["messages"]
                total_sessions += child_info["sessions"]
                if child_info["last_active"] > latest_activity:
                    latest_activity = child_info["last_active"]

                # Recurse into children
                collect_metrics(child_data["_children"])

        # If this is a leaf node with actual data
        if "_data" in tree and (
            not tree.get("_children") or len(tree.get("_children", {})) == 0
        ):
            data = tree["_data"]
            total_node_cost = data["cost"]
            total_messages = data["messages"]
            total_sessions = data["sessions"]
            latest_activity = data["last_active"]
        else:
            # Aggregate from children
            collect_metrics(tree.get("_children", {}))

        # Calculate metrics
        session_count = total_sessions
        avg_cost_per_session = (
            total_node_cost / session_count if session_count > 0 else 0.0
        )
        percentage = (total_node_cost / total_cost * 100) if total_cost > 0 else 0.0

        # Ensure percentage doesn't exceed 100% due to floating point errors
        percentage = min(percentage, 100.0)

        # Ensure we have a valid timestamp
        if latest_activity == datetime.min:
            latest_activity = datetime.utcnow()

        metrics = DirectoryMetrics(
            cost=round(total_node_cost, 2),
            messages=total_messages,
            sessions=session_count,
            avg_cost_per_session=round(avg_cost_per_session, 4),
            last_active=latest_activity,
        )

        # Build children nodes
        children = []
        children_dict = tree.get("_children", {}) if isinstance(tree, dict) else {}

        for child_name, child_tree in children_dict.items():
            child_path = f"{path}/{child_name}" if path != "/" else f"/{child_name}"
            child_node = self._tree_to_directory_node(
                child_tree, child_path, child_name, total_cost
            )
            children.append(child_node)

        # Sort children by cost descending
        children.sort(key=lambda x: x.metrics.cost, reverse=True)

        return DirectoryNode(
            path=path,
            name=name,
            metrics=metrics,
            children=children,
            percentage_of_total=round(percentage, 2),
        )

    async def get_response_times(
        self, time_range: TimeRange, percentiles: list[int], group_by: str
    ) -> ResponseTimeAnalytics:
        """Get response time analytics with percentiles and distribution."""
        time_filter = self._get_time_filter(time_range)

        # Base filter for assistant messages with duration data
        base_filter = {
            **time_filter,
            "type": "assistant",
            "durationMs": {"$ne": None, "$gt": 0},
        }

        # Calculate overall percentiles
        overall_percentiles = await self._calculate_percentiles(
            base_filter, percentiles
        )

        # Get time series data
        time_series = await self._get_response_time_series(base_filter, group_by)

        # Get distribution buckets
        distribution = await self._get_response_time_distribution(base_filter)

        return ResponseTimeAnalytics(
            percentiles=overall_percentiles,
            time_series=time_series,
            distribution=distribution,
            time_range=time_range,
            group_by=group_by,
        )

    async def get_token_analytics(
        self, time_range: TimeRange, percentiles: list[int], group_by: str
    ) -> TokenAnalytics:
        """Get token usage analytics with percentiles and distribution."""
        time_filter = self._get_time_filter(time_range)

        # Base filter for assistant messages with token data
        base_filter = {
            **time_filter,
            "type": "assistant",
            "$or": [
                {"metadata.usage": {"$exists": True}},
                {"inputTokens": {"$exists": True}},
                {"outputTokens": {"$exists": True}},
                {"tokensInput": {"$exists": True}},
                {"tokensOutput": {"$exists": True}},
            ],
        }

        # Calculate overall percentiles for total tokens
        overall_percentiles = await self._calculate_token_percentiles(
            base_filter, percentiles
        )

        # Get time series data
        time_series = await self._get_token_time_series(base_filter, group_by)

        # Get distribution buckets
        distribution = await self._get_token_distribution(base_filter)

        return TokenAnalytics(
            percentiles=overall_percentiles,
            time_series=time_series,
            distribution=distribution,
            time_range=time_range,
            group_by=group_by,
        )

    async def get_performance_factors(
        self, time_range: TimeRange
    ) -> PerformanceFactorsAnalytics:
        """Get performance factors analysis."""
        time_filter = self._get_time_filter(time_range)

        # Base filter for assistant messages with duration data
        base_filter = {
            **time_filter,
            "type": "assistant",
            "durationMs": {"$ne": None, "$gt": 0},
        }

        # Calculate correlations for different factors
        correlations = []

        # Message length correlation
        msg_length_corr = await self._calculate_message_length_correlation(base_filter)
        if msg_length_corr:
            correlations.append(msg_length_corr)

        # Tool usage correlation
        tool_usage_corr = await self._calculate_tool_usage_correlation(base_filter)
        if tool_usage_corr:
            correlations.append(tool_usage_corr)

        # Model type correlation
        model_corr = await self._calculate_model_correlation(base_filter)
        if model_corr:
            correlations.extend(model_corr)

        # Time of day correlation
        time_of_day_corr = await self._calculate_time_of_day_correlation(base_filter)
        if time_of_day_corr:
            correlations.append(time_of_day_corr)

        # Generate recommendations based on correlations
        recommendations = self._generate_performance_recommendations(correlations)

        return PerformanceFactorsAnalytics(
            correlations=correlations,
            recommendations=recommendations,
            time_range=time_range,
        )

    async def get_token_performance_factors(
        self, time_range: TimeRange
    ) -> TokenPerformanceFactorsAnalytics:
        """Get token usage performance factors analysis."""
        time_filter = self._get_time_filter(time_range)

        # Base filter for assistant messages with token data
        base_filter = {
            **time_filter,
            "type": "assistant",
            "$or": [
                {"metadata.usage": {"$exists": True}},
                {"inputTokens": {"$exists": True}},
                {"outputTokens": {"$exists": True}},
                {"tokensInput": {"$exists": True}},
                {"tokensOutput": {"$exists": True}},
            ],
        }

        # Calculate correlations for different factors
        correlations = []

        # Message length correlation with tokens
        msg_length_corr = await self._calculate_token_message_length_correlation(
            base_filter
        )
        if msg_length_corr:
            correlations.append(msg_length_corr)

        # Tool usage correlation with tokens
        tool_usage_corr = await self._calculate_token_tool_usage_correlation(
            base_filter
        )
        if tool_usage_corr:
            correlations.append(tool_usage_corr)

        # Model type correlation with tokens
        model_corr = await self._calculate_token_model_correlation(base_filter)
        if model_corr:
            correlations.extend(model_corr)

        # Time of day correlation with tokens
        time_of_day_corr = await self._calculate_token_time_of_day_correlation(
            base_filter
        )
        if time_of_day_corr:
            correlations.append(time_of_day_corr)

        # Generate recommendations based on correlations
        recommendations = self._generate_token_performance_recommendations(correlations)

        return TokenPerformanceFactorsAnalytics(
            correlations=correlations,
            recommendations=recommendations,
            time_range=time_range,
        )

    async def _calculate_percentiles(
        self, base_filter: dict, percentiles: list[int]
    ) -> ResponseTimePercentiles:
        """Calculate response time percentiles using MongoDB 7.0+ $percentile operator."""
        # Build percentile expressions
        percentile_exprs = {}
        percentile_input = []
        for p in percentiles:
            percentile_input.append(p / 100.0)
            percentile_exprs[f"p{p}"] = {
                "$arrayElemAt": ["$percentiles", percentiles.index(p)]
            }

        pipeline = [
            {"$match": base_filter},
            {
                "$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "percentiles": {
                        "$percentile": {
                            "input": "$durationMs",
                            "p": percentile_input,
                            "method": "approximate",
                        }
                    },
                }
            },
            {"$project": {"_id": 0, "count": 1, **percentile_exprs}},
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)
        if not result or result[0]["count"] == 0:
            return ResponseTimePercentiles(p50=0, p90=0, p95=0, p99=0)

        # Extract percentile values
        percentile_values = {}
        for p in percentiles:
            key = f"p{p}"
            percentile_values[key] = float(result[0].get(key, 0))

        return ResponseTimePercentiles(
            p50=percentile_values.get("p50", 0),
            p90=percentile_values.get("p90", 0),
            p95=percentile_values.get("p95", 0),
            p99=percentile_values.get("p99", 0),
        )

    async def _calculate_token_percentiles(
        self, base_filter: dict, percentiles: list[int]
    ) -> TokenPercentiles:
        """Calculate token usage percentiles using MongoDB 7.0+ $percentile operator."""
        # Build percentile expressions
        percentile_exprs = {}
        percentile_input = []
        for p in percentiles:
            percentile_input.append(p / 100.0)
            percentile_exprs[f"p{p}"] = {
                "$arrayElemAt": ["$percentiles", percentiles.index(p)]
            }

        # Calculate total tokens from all possible fields
        total_tokens_expr = {
            "$add": [
                {"$ifNull": ["$inputTokens", 0]},
                {"$ifNull": ["$outputTokens", 0]},
                {"$ifNull": ["$tokensInput", 0]},
                {"$ifNull": ["$tokensOutput", 0]},
                {"$ifNull": ["$metadata.usage.input_tokens", 0]},
                {"$ifNull": ["$metadata.usage.output_tokens", 0]},
                {"$ifNull": ["$metadata.usage.cache_creation_input_tokens", 0]},
                {"$ifNull": ["$metadata.usage.cache_read_input_tokens", 0]},
            ]
        }

        pipeline = [
            {"$match": base_filter},
            {
                "$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "percentiles": {
                        "$percentile": {
                            "input": total_tokens_expr,
                            "p": percentile_input,
                            "method": "approximate",
                        }
                    },
                }
            },
            {"$project": {"_id": 0, "count": 1, **percentile_exprs}},
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)
        if not result or result[0]["count"] == 0:
            return TokenPercentiles(p50=0, p90=0, p95=0, p99=0)

        # Extract percentile values
        percentile_values = {}
        for p in percentiles:
            key = f"p{p}"
            percentile_values[key] = float(result[0].get(key, 0))

        return TokenPercentiles(
            p50=percentile_values.get("p50", 0),
            p90=percentile_values.get("p90", 0),
            p95=percentile_values.get("p95", 0),
            p99=percentile_values.get("p99", 0),
        )

    async def _get_response_time_series(
        self, base_filter: dict, group_by: str
    ) -> list[ResponseTimeDataPoint]:
        """Get response time time series data."""
        date_key: Any
        if group_by == "hour":
            group_format = "%Y-%m-%d %H:00:00"
            date_key = {"$dateToString": {"format": group_format, "date": "$timestamp"}}
        elif group_by == "day":
            group_format = "%Y-%m-%d"
            date_key = {"$dateToString": {"format": group_format, "date": "$timestamp"}}
        elif group_by == "model":
            date_key = "$model"
        elif group_by == "tool_count":
            # Count tools used in each message
            date_key = {
                "$size": {
                    "$ifNull": [
                        {"$objectToArray": {"$ifNull": ["$toolUseResult", {}]}},
                        [],
                    ]
                }
            }
        else:
            date_key = {
                "$dateToString": {"format": "%Y-%m-%d %H:00:00", "date": "$timestamp"}
            }

        pipeline = [
            {"$match": base_filter},
            {
                "$group": {
                    "_id": date_key,
                    "durations": {"$push": "$durationMs"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        time_series = []
        for result in results:
            durations = sorted(result["durations"])
            count = len(durations)

            if count == 0:
                continue

            avg_duration = sum(durations) / count
            p50_idx = int(0.5 * count)
            p90_idx = int(0.9 * count)

            if p50_idx >= count:
                p50_idx = count - 1
            if p90_idx >= count:
                p90_idx = count - 1

            # Parse timestamp for time-based grouping
            if group_by in ["hour", "day"]:
                timestamp = datetime.fromisoformat(result["_id"].replace("Z", "+00:00"))
            else:
                timestamp = datetime.utcnow()

            time_series.append(
                ResponseTimeDataPoint(
                    timestamp=timestamp,
                    avg_duration_ms=round(avg_duration, 2),
                    p50=float(durations[p50_idx]),
                    p90=float(durations[p90_idx]),
                    message_count=count,
                )
            )

        return time_series

    async def _get_response_time_distribution(
        self, base_filter: dict
    ) -> list[DistributionBucket]:
        """Get response time distribution buckets."""
        pipeline: list[dict[str, Any]] = [
            {"$match": base_filter},
            {
                "$bucket": {
                    "groupBy": "$durationMs",
                    "boundaries": [0, 1000, 5000, 10000, 30000, 60000, float("inf")],
                    "default": "60000+",
                    "output": {"count": {"$sum": 1}},
                }
            },
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        # Get total count for percentage calculation
        total_pipeline: list[dict[str, Any]] = [
            {"$match": base_filter},
            {"$count": "total"},
        ]
        total_result = await self.db.messages.aggregate(total_pipeline).to_list(1)
        total_count = total_result[0]["total"] if total_result else 0

        bucket_labels = {
            0: "0-1s",
            1000: "1-5s",
            5000: "5-10s",
            10000: "10-30s",
            30000: "30-60s",
            60000: "60s+",
            "60000+": "60s+",
        }

        distribution = []
        for result in results:
            bucket_id = result["_id"]
            count = result["count"]
            percentage = (count / total_count * 100) if total_count > 0 else 0

            bucket_label = bucket_labels.get(bucket_id, str(bucket_id))

            distribution.append(
                DistributionBucket(
                    bucket=bucket_label, count=count, percentage=round(percentage, 2)
                )
            )

        return distribution

    async def _get_token_time_series(
        self, base_filter: dict, group_by: str
    ) -> list[TokenAnalyticsDataPoint]:
        """Get token usage time series data."""
        date_key: Any
        if group_by == "hour":
            group_format = "%Y-%m-%d %H:00:00"
            date_key = {"$dateToString": {"format": group_format, "date": "$timestamp"}}
        elif group_by == "day":
            group_format = "%Y-%m-%d"
            date_key = {"$dateToString": {"format": group_format, "date": "$timestamp"}}
        elif group_by == "model":
            date_key = "$model"
        else:
            date_key = {
                "$dateToString": {"format": "%Y-%m-%d %H:00:00", "date": "$timestamp"}
            }

        # Expression to calculate total tokens
        total_tokens_expr = {
            "$add": [
                {"$ifNull": ["$inputTokens", 0]},
                {"$ifNull": ["$outputTokens", 0]},
                {"$ifNull": ["$tokensInput", 0]},
                {"$ifNull": ["$tokensOutput", 0]},
                {"$ifNull": ["$metadata.usage.input_tokens", 0]},
                {"$ifNull": ["$metadata.usage.output_tokens", 0]},
                {"$ifNull": ["$metadata.usage.cache_creation_input_tokens", 0]},
                {"$ifNull": ["$metadata.usage.cache_read_input_tokens", 0]},
            ]
        }

        pipeline = [
            {"$match": base_filter},
            {
                "$group": {
                    "_id": date_key,
                    "tokens": {"$push": total_tokens_expr},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        time_series = []
        for result in results:
            tokens = sorted(result["tokens"])
            count = len(tokens)

            if count == 0:
                continue

            avg_tokens = sum(tokens) / count
            p50_idx = int(0.5 * count)
            p90_idx = int(0.9 * count)

            if p50_idx >= count:
                p50_idx = count - 1
            if p90_idx >= count:
                p90_idx = count - 1

            # Parse timestamp for time-based grouping
            if group_by in ["hour", "day"]:
                timestamp = datetime.fromisoformat(result["_id"].replace("Z", "+00:00"))
            else:
                timestamp = datetime.utcnow()

            time_series.append(
                TokenAnalyticsDataPoint(
                    timestamp=timestamp,
                    avg_tokens=round(avg_tokens, 2),
                    p50=float(tokens[p50_idx]),
                    p90=float(tokens[p90_idx]),
                    message_count=count,
                )
            )

        return time_series

    async def _get_token_distribution(
        self, base_filter: dict
    ) -> list[TokenDistributionBucket]:
        """Get token usage distribution buckets."""
        # Expression to calculate total tokens
        total_tokens_expr = {
            "$add": [
                {"$ifNull": ["$inputTokens", 0]},
                {"$ifNull": ["$outputTokens", 0]},
                {"$ifNull": ["$tokensInput", 0]},
                {"$ifNull": ["$tokensOutput", 0]},
                {"$ifNull": ["$metadata.usage.input_tokens", 0]},
                {"$ifNull": ["$metadata.usage.output_tokens", 0]},
                {"$ifNull": ["$metadata.usage.cache_creation_input_tokens", 0]},
                {"$ifNull": ["$metadata.usage.cache_read_input_tokens", 0]},
            ]
        }

        pipeline: list[dict[str, Any]] = [
            {"$match": base_filter},
            {"$addFields": {"totalTokens": total_tokens_expr}},
            {
                "$bucket": {
                    "groupBy": "$totalTokens",
                    "boundaries": [0, 100, 500, 1000, 5000, 10000, 50000, float("inf")],
                    "default": "50000+",
                    "output": {"count": {"$sum": 1}},
                }
            },
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        # Get total count for percentage calculation
        total_pipeline: list[dict[str, Any]] = [
            {"$match": base_filter},
            {"$count": "total"},
        ]
        total_result = await self.db.messages.aggregate(total_pipeline).to_list(1)
        total_count = total_result[0]["total"] if total_result else 0

        bucket_labels = {
            0: "0-100",
            100: "100-500",
            500: "500-1k",
            1000: "1k-5k",
            5000: "5k-10k",
            10000: "10k-50k",
            50000: "50k+",
            "50000+": "50k+",
        }

        distribution = []
        for result in results:
            bucket_id = result["_id"]
            count = result["count"]
            percentage = (count / total_count * 100) if total_count > 0 else 0

            bucket_label = bucket_labels.get(bucket_id, str(bucket_id))

            distribution.append(
                TokenDistributionBucket(
                    bucket=bucket_label, count=count, percentage=round(percentage, 2)
                )
            )

        return distribution

    async def _calculate_message_length_correlation(
        self, base_filter: dict
    ) -> PerformanceCorrelation | None:
        """Calculate correlation between message length and response time."""
        pipeline = [
            {"$match": base_filter},
            {
                "$addFields": {
                    "messageLength": {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": ["$message", None]},
                                    {"$eq": [{"$type": "$message"}, "null"]},
                                    {"$not": ["$message"]},
                                ]
                            },
                            "then": 0,
                            "else": {"$strLenCP": {"$toString": "$message"}},
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "data": {
                        "$push": {"length": "$messageLength", "duration": "$durationMs"}
                    },
                    "count": {"$sum": 1},
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)
        if not result or result[0]["count"] < 10:  # Need at least 10 samples
            return None

        data = result[0]["data"]
        lengths = [d["length"] for d in data]
        durations = [d["duration"] for d in data]

        correlation = self._calculate_pearson_correlation(lengths, durations)
        avg_impact = sum(durations) / len(durations) - min(durations)

        return PerformanceCorrelation(
            factor="message_length",
            correlation_strength=correlation,
            impact_ms=round(avg_impact, 2),
            sample_size=len(data),
        )

    async def _calculate_tool_usage_correlation(
        self, base_filter: dict
    ) -> PerformanceCorrelation | None:
        """Calculate correlation between tool usage count and response time."""
        pipeline = [
            {"$match": base_filter},
            {
                "$addFields": {
                    "toolCount": {
                        "$size": {
                            "$ifNull": [
                                {"$objectToArray": {"$ifNull": ["$toolUseResult", {}]}},
                                [],
                            ]
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "data": {
                        "$push": {"toolCount": "$toolCount", "duration": "$durationMs"}
                    },
                    "count": {"$sum": 1},
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)
        if not result or result[0]["count"] < 10:
            return None

        data = result[0]["data"]
        tool_counts = [d["toolCount"] for d in data]
        durations = [d["duration"] for d in data]

        correlation = self._calculate_pearson_correlation(tool_counts, durations)
        avg_impact = sum(durations) / len(durations) - min(durations)

        return PerformanceCorrelation(
            factor="tool_usage_count",
            correlation_strength=correlation,
            impact_ms=round(avg_impact, 2),
            sample_size=len(data),
        )

    async def _calculate_model_correlation(
        self, base_filter: dict
    ) -> list[PerformanceCorrelation]:
        """Calculate correlation for different models."""
        pipeline = [
            {"$match": base_filter},
            {
                "$group": {
                    "_id": "$model",
                    "avgDuration": {"$avg": "$durationMs"},
                    "count": {"$sum": 1},
                }
            },
            {"$match": {"count": {"$gte": 5}}},  # At least 5 samples per model
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)
        if len(results) < 2:
            return []

        # Calculate baseline (fastest model)
        baseline_duration = min(r["avgDuration"] for r in results)

        correlations = []
        for result in results:
            model = result["_id"] or "unknown"
            avg_duration = result["avgDuration"]
            impact = avg_duration - baseline_duration

            # Use a simple impact-based correlation strength
            max_impact = max(r["avgDuration"] for r in results) - baseline_duration
            correlation_strength = impact / max_impact if max_impact > 0 else 0

            correlations.append(
                PerformanceCorrelation(
                    factor=f"model_{model}",
                    correlation_strength=correlation_strength,
                    impact_ms=round(impact, 2),
                    sample_size=result["count"],
                )
            )

        return correlations

    async def _calculate_time_of_day_correlation(
        self, base_filter: dict
    ) -> PerformanceCorrelation | None:
        """Calculate correlation between time of day and response time."""
        pipeline = [
            {"$match": base_filter},
            {"$addFields": {"hourOfDay": {"$hour": "$timestamp"}}},
            {
                "$group": {
                    "_id": None,
                    "data": {
                        "$push": {"hour": "$hourOfDay", "duration": "$durationMs"}
                    },
                    "count": {"$sum": 1},
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)
        if not result or result[0]["count"] < 20:
            return None

        data = result[0]["data"]
        hours = [d["hour"] for d in data]
        durations = [d["duration"] for d in data]

        correlation = self._calculate_pearson_correlation(hours, durations)
        avg_impact = max(durations) - min(durations)

        return PerformanceCorrelation(
            factor="time_of_day",
            correlation_strength=correlation,
            impact_ms=round(avg_impact * 0.1, 2),  # Scale down impact
            sample_size=len(data),
        )

    def _calculate_pearson_correlation(self, x: list[float], y: list[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = (
            (n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)
        ) ** 0.5

        if denominator == 0:
            return 0.0

        correlation = float(numerator / denominator)
        return float(max(-1.0, min(1.0, correlation)))  # Clamp to [-1, 1]

    async def _calculate_token_message_length_correlation(
        self, base_filter: dict
    ) -> TokenPerformanceCorrelation | None:
        """Calculate correlation between message length and token usage."""
        # Expression to calculate total tokens
        total_tokens_expr = {
            "$add": [
                {"$ifNull": ["$inputTokens", 0]},
                {"$ifNull": ["$outputTokens", 0]},
                {"$ifNull": ["$tokensInput", 0]},
                {"$ifNull": ["$tokensOutput", 0]},
                {"$ifNull": ["$metadata.usage.input_tokens", 0]},
                {"$ifNull": ["$metadata.usage.output_tokens", 0]},
                {"$ifNull": ["$metadata.usage.cache_creation_input_tokens", 0]},
                {"$ifNull": ["$metadata.usage.cache_read_input_tokens", 0]},
            ]
        }

        pipeline = [
            {"$match": base_filter},
            {
                "$addFields": {
                    "messageLength": {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": ["$message", None]},
                                    {"$eq": [{"$type": "$message"}, "null"]},
                                    {"$not": ["$message"]},
                                ]
                            },
                            "then": 0,
                            "else": {"$strLenCP": {"$toString": "$message"}},
                        }
                    },
                    "totalTokens": total_tokens_expr,
                }
            },
            {
                "$group": {
                    "_id": None,
                    "data": {
                        "$push": {"length": "$messageLength", "tokens": "$totalTokens"}
                    },
                    "count": {"$sum": 1},
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)
        if not result or result[0]["count"] < 10:  # Need at least 10 samples
            return None

        data = result[0]["data"]
        lengths = [d["length"] for d in data]
        tokens = [d["tokens"] for d in data]

        correlation = self._calculate_pearson_correlation(lengths, tokens)

        # Calculate average impact
        avg_tokens = sum(tokens) / len(tokens) if tokens else 0
        min_tokens = min(tokens) if tokens else 0
        impact = avg_tokens - min_tokens

        return TokenPerformanceCorrelation(
            factor="message_length_tokens",
            correlation_strength=round(correlation, 3),
            impact_tokens=impact,
            sample_size=len(data),
        )

    async def _calculate_token_tool_usage_correlation(
        self, base_filter: dict
    ) -> TokenPerformanceCorrelation | None:
        """Calculate correlation between tool usage and token consumption."""
        # Expression to calculate total tokens
        total_tokens_expr = {
            "$add": [
                {"$ifNull": ["$inputTokens", 0]},
                {"$ifNull": ["$outputTokens", 0]},
                {"$ifNull": ["$tokensInput", 0]},
                {"$ifNull": ["$tokensOutput", 0]},
                {"$ifNull": ["$metadata.usage.input_tokens", 0]},
                {"$ifNull": ["$metadata.usage.output_tokens", 0]},
                {"$ifNull": ["$metadata.usage.cache_creation_input_tokens", 0]},
                {"$ifNull": ["$metadata.usage.cache_read_input_tokens", 0]},
            ]
        }

        pipeline = [
            {"$match": base_filter},
            {
                "$addFields": {
                    "toolCount": {
                        "$size": {
                            "$ifNull": [
                                {"$objectToArray": {"$ifNull": ["$toolUseResult", {}]}},
                                [],
                            ]
                        }
                    },
                    "totalTokens": total_tokens_expr,
                }
            },
            {
                "$group": {
                    "_id": "$toolCount",
                    "avgTokens": {"$avg": "$totalTokens"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)
        if len(results) < 2:  # Need at least 2 data points
            return None

        tool_counts = [r["_id"] for r in results]
        avg_tokens = [r["avgTokens"] for r in results]

        correlation = self._calculate_pearson_correlation(tool_counts, avg_tokens)

        # Calculate average impact
        avg_tokens_overall = sum(avg_tokens) / len(avg_tokens) if avg_tokens else 0
        min_tokens = min(avg_tokens) if avg_tokens else 0
        impact = avg_tokens_overall - min_tokens

        return TokenPerformanceCorrelation(
            factor="tool_usage_tokens",
            correlation_strength=round(correlation, 3),
            impact_tokens=impact,
            sample_size=sum(r["count"] for r in results),
        )

    async def _calculate_token_model_correlation(
        self, base_filter: dict
    ) -> list[TokenPerformanceCorrelation]:
        """Calculate token usage patterns by model."""
        # Expression to calculate total tokens
        total_tokens_expr = {
            "$add": [
                {"$ifNull": ["$inputTokens", 0]},
                {"$ifNull": ["$outputTokens", 0]},
                {"$ifNull": ["$tokensInput", 0]},
                {"$ifNull": ["$tokensOutput", 0]},
                {"$ifNull": ["$metadata.usage.input_tokens", 0]},
                {"$ifNull": ["$metadata.usage.output_tokens", 0]},
                {"$ifNull": ["$metadata.usage.cache_creation_input_tokens", 0]},
                {"$ifNull": ["$metadata.usage.cache_read_input_tokens", 0]},
            ]
        }

        pipeline = [
            {"$match": base_filter},
            {"$addFields": {"totalTokens": total_tokens_expr}},
            {
                "$group": {
                    "_id": "$model",
                    "avgTokens": {"$avg": "$totalTokens"},
                    "medianTokens": {
                        "$percentile": {
                            "input": "$totalTokens",
                            "p": [0.5],
                            "method": "approximate",
                        }
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"avgTokens": -1}},
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)
        if not results:
            return []

        correlations = []
        base_model = results[0] if results else None

        for result in results:
            if result["count"] < 5:  # Skip models with too few samples
                continue

            relative_usage = (
                (result["avgTokens"] / base_model["avgTokens"]) if base_model else 1.0
            )

            impact = result["avgTokens"] - base_model["avgTokens"] if base_model else 0

            correlations.append(
                TokenPerformanceCorrelation(
                    factor=f"model_{result['_id']}_tokens",
                    correlation_strength=round(relative_usage - 1, 3),
                    impact_tokens=impact,
                    sample_size=result["count"],
                )
            )

        return correlations

    async def _calculate_token_time_of_day_correlation(
        self, base_filter: dict
    ) -> TokenPerformanceCorrelation | None:
        """Calculate correlation between time of day and token usage."""
        # Expression to calculate total tokens
        total_tokens_expr = {
            "$add": [
                {"$ifNull": ["$inputTokens", 0]},
                {"$ifNull": ["$outputTokens", 0]},
                {"$ifNull": ["$tokensInput", 0]},
                {"$ifNull": ["$tokensOutput", 0]},
                {"$ifNull": ["$metadata.usage.input_tokens", 0]},
                {"$ifNull": ["$metadata.usage.output_tokens", 0]},
                {"$ifNull": ["$metadata.usage.cache_creation_input_tokens", 0]},
                {"$ifNull": ["$metadata.usage.cache_read_input_tokens", 0]},
            ]
        }

        pipeline = [
            {"$match": base_filter},
            {
                "$addFields": {
                    "hour": {"$hour": "$timestamp"},
                    "totalTokens": total_tokens_expr,
                }
            },
            {
                "$group": {
                    "_id": "$hour",
                    "avgTokens": {"$avg": "$totalTokens"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)
        if len(results) < 6:  # Need data from at least 6 different hours
            return None

        hours = [r["_id"] for r in results]
        avg_tokens = [r["avgTokens"] for r in results]

        correlation = self._calculate_pearson_correlation(hours, avg_tokens)

        # Calculate average impact
        avg_tokens_overall = sum(avg_tokens) / len(avg_tokens) if avg_tokens else 0
        min_tokens = min(avg_tokens) if avg_tokens else 0
        impact = avg_tokens_overall - min_tokens

        return TokenPerformanceCorrelation(
            factor="time_of_day_tokens",
            correlation_strength=round(correlation, 3),
            impact_tokens=impact,
            sample_size=sum(r["count"] for r in results),
        )

    def _generate_token_performance_recommendations(
        self, correlations: list[TokenPerformanceCorrelation]
    ) -> list[str]:
        """Generate recommendations based on token usage correlations."""
        recommendations = []

        for corr in correlations:
            if "message_length" in corr.factor and corr.impact_tokens > 10000:
                if corr.correlation_strength > 0.7:
                    recommendations.append(
                        "Longer messages consume significantly more tokens. Consider being more concise in prompts."
                    )

            elif "tool_usage" in corr.factor and corr.impact_tokens > 5000:
                if corr.correlation_strength > 0.5:
                    recommendations.append(
                        "Tool usage increases token consumption. Review if all tool calls are necessary."
                    )

            elif "model_" in corr.factor and "_tokens" in corr.factor:
                if corr.correlation_strength > 0.5 and corr.impact_tokens > 10000:
                    model_name = corr.factor.replace("model_", "").replace(
                        "_tokens", ""
                    )
                    recommendations.append(
                        f"{model_name} uses more tokens than average. Consider using a more efficient model for simple tasks."
                    )

        # Add general recommendations
        if not recommendations:
            recommendations.append(
                "Token usage appears well-optimized. Continue monitoring for changes."
            )

        return recommendations[:5]  # Limit to top 5 recommendations

    def _generate_performance_recommendations(
        self, correlations: list[PerformanceCorrelation]
    ) -> list[str]:
        """Generate performance optimization recommendations."""
        recommendations = []

        for corr in correlations:
            if abs(corr.correlation_strength) < 0.3:
                continue  # Skip weak correlations

            if corr.factor == "message_length" and corr.correlation_strength > 0.5:
                recommendations.append(
                    "Consider breaking down long messages into smaller chunks to improve response times"
                )
            elif corr.factor == "tool_usage_count" and corr.correlation_strength > 0.6:
                recommendations.append(
                    "High tool usage significantly impacts response time. Consider optimizing tool usage patterns"
                )
            elif corr.factor.startswith("model_") and corr.impact_ms > 5000:
                model_name = corr.factor.replace("model_", "")
                recommendations.append(
                    f"Model '{model_name}' shows slower response times. Consider using a faster model for time-sensitive tasks"
                )
            elif corr.factor == "time_of_day" and abs(corr.correlation_strength) > 0.4:
                if corr.correlation_strength > 0:
                    recommendations.append(
                        "Response times appear slower during peak hours. Consider scheduling intensive tasks during off-peak times"
                    )
                else:
                    recommendations.append(
                        "Response times are better during certain hours. Consider leveraging these optimal time windows"
                    )

        if not recommendations:
            recommendations.append(
                "No significant performance patterns identified. Response times appear consistent across factors"
            )

        return recommendations

    async def get_git_branch_analytics(
        self,
        time_range: TimeRange,
        project_id: str | None = None,
        include_pattern: str | None = None,
        exclude_pattern: str | None = None,
    ) -> GitBranchAnalyticsResponse:
        """Get git branch analytics."""
        time_filter = self._get_time_filter(time_range)

        # Add project filter if specified
        if project_id:
            session_filter = {"projectId": ObjectId(project_id)}
            session_ids = await self.db.sessions.find(
                session_filter, {"sessionId": 1}
            ).to_list(None)
            session_id_list = [s["sessionId"] for s in session_ids]
            time_filter["sessionId"] = {"$in": session_id_list}

        # Build aggregation pipeline
        # For now, we'll include all messages and group by gitBranch (including empty/None)
        # to show "No Branch" data rather than hiding it
        pipeline: list[dict[str, Any]] = [
            {"$match": time_filter},
            # Add a hint to use the appropriate index
            {"$sort": {"timestamp": -1, "gitBranch": 1}},
            {
                "$group": {
                    "_id": "$gitBranch",
                    "cost": {"$sum": {"$ifNull": ["$costUsd", 0]}},
                    "messages": {"$sum": 1},
                    "sessions": {"$addToSet": "$sessionId"},
                    "first_activity": {"$min": "$timestamp"},
                    "last_activity": {"$max": "$timestamp"},
                    # Don't collect all tool results - we'll aggregate them separately
                }
            },
            {
                "$project": {
                    "branch": "$_id",
                    "cost": 1,
                    "messages": 1,
                    "sessions": {"$size": "$sessions"},
                    "first_activity": 1,
                    "last_activity": 1,
                    "active_days": {
                        "$add": [
                            {
                                "$divide": [
                                    {
                                        "$subtract": [
                                            "$last_activity",
                                            "$first_activity",
                                        ]
                                    },
                                    1000 * 60 * 60 * 24,
                                ]
                            },
                            1,
                        ]
                    },
                }
            },
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        # Get tool usage counts separately for each branch
        tool_usage_by_branch = await self._get_tool_usage_by_branch(time_filter)

        # Filter branches by patterns if specified
        filtered_results = []
        for result in results:
            branch_name = result["branch"]

            # Normalize branch name (remove remote prefix)
            normalized_branch = self._normalize_branch_name(branch_name)
            result["branch"] = normalized_branch

            # Apply include/exclude patterns
            if include_pattern and not re.match(include_pattern, normalized_branch):
                continue
            if exclude_pattern and re.match(exclude_pattern, normalized_branch):
                continue

            filtered_results.append(result)

        # Convert to branch analytics
        branches = []
        for result in filtered_results:
            branch_name = (
                result["branch"] or "No Branch"
            )  # Display "No Branch" for empty/None values
            branch_type = self._detect_branch_type(
                result["branch"]
            )  # Use original for type detection

            # Calculate top operations
            top_operations = []
            # Get tool usage for this branch from the separate aggregation
            branch_tool_usage = tool_usage_by_branch.get(result["branch"], {})

            # Get top 5 operations
            sorted_tools = sorted(
                branch_tool_usage.items(), key=lambda x: x[1], reverse=True
            )
            for tool_name, count in sorted_tools[:5]:
                top_operations.append(
                    BranchTopOperation(operation=tool_name, count=count)
                )

            # Calculate metrics
            cost = self._safe_float(result.get("cost", 0))
            messages = result.get("messages", 0)
            sessions = result.get("sessions", 0)
            avg_session_cost = cost / sessions if sessions > 0 else 0

            metrics = BranchMetrics(
                cost=round(cost, 2),
                messages=messages,
                sessions=sessions,
                avg_session_cost=round(avg_session_cost, 2),
                first_activity=result["first_activity"],
                last_activity=result["last_activity"],
                active_days=max(1, int(result.get("active_days", 1))),
            )

            branch_analytics = BranchAnalytics(
                name=branch_name,
                type=branch_type,
                metrics=metrics,
                top_operations=top_operations,
                cost_trend=0.0,  # TODO: Calculate trend from previous period
            )

            branches.append(branch_analytics)

        # Sort branches by cost descending
        branches.sort(key=lambda b: b.metrics.cost, reverse=True)

        # Calculate branch comparisons
        branch_comparisons = self._calculate_branch_comparisons(branches)

        return GitBranchAnalyticsResponse(
            branches=branches,
            branch_comparisons=branch_comparisons,
            time_range=time_range,
        )

    async def _get_tool_usage_by_branch(
        self, time_filter: dict[str, Any]
    ) -> dict[str, dict[str, int]]:
        """Get tool usage counts by branch using a separate aggregation."""
        # Use $objectToArray to convert toolUseResult keys to array for counting
        pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    **time_filter,
                    "toolUseResult": {"$exists": True, "$ne": None},
                }
            },
            # Convert toolUseResult object to array of key-value pairs
            {
                "$project": {
                    "gitBranch": 1,
                    "tools": {"$objectToArray": "$toolUseResult"},
                }
            },
            # Unwind the tools array to create a document per tool
            {"$unwind": "$tools"},
            # Group by branch and tool name to count usage
            {
                "$group": {
                    "_id": {
                        "branch": "$gitBranch",
                        "tool": "$tools.k",  # k is the key (tool name)
                    },
                    "count": {"$sum": 1},
                }
            },
            # Reshape to group by branch
            {
                "$group": {
                    "_id": "$_id.branch",
                    "tools": {"$push": {"tool": "$_id.tool", "count": "$count"}},
                }
            },
        ]

        results = await self.db.messages.aggregate(pipeline).to_list(None)

        # Convert to dictionary format
        tool_usage_by_branch: dict[str, dict[str, int]] = {}
        for result in results:
            branch = self._normalize_branch_name(result["_id"])
            tool_usage_by_branch[branch] = {}
            for tool_info in result["tools"]:
                tool_usage_by_branch[branch][tool_info["tool"]] = tool_info["count"]

        return tool_usage_by_branch

    def _normalize_branch_name(self, branch_name: Optional[str]) -> str:
        """Normalize branch name by removing remote prefix."""
        # Handle None or empty branch names
        if not branch_name:
            return ""

        # Remove common remote prefixes
        prefixes = [
            "origin/",
            "upstream/",
            "refs/heads/",
            "refs/remotes/origin/",
            "refs/remotes/upstream/",
        ]
        normalized = branch_name
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix) :]
                break
        return normalized

    def _detect_branch_type(self, branch_name: str) -> BranchType:
        """Detect branch type from branch name patterns."""
        # Handle empty or None branch names
        if not branch_name:
            return BranchType.OTHER

        branch_lower = branch_name.lower()

        # Main/master branches
        if branch_lower in ["main", "master", "develop", "dev"]:
            return BranchType.MAIN

        # Feature branches
        if any(
            pattern in branch_lower
            for pattern in ["feature/", "feat/", "feature-", "feat-"]
        ):
            return BranchType.FEATURE

        # Hotfix branches
        if any(
            pattern in branch_lower
            for pattern in ["hotfix/", "hotfix-", "fix/", "bugfix/"]
        ):
            return BranchType.HOTFIX

        # Release branches
        if any(pattern in branch_lower for pattern in ["release/", "release-", "rel/"]):
            return BranchType.RELEASE

        return BranchType.OTHER

    def _calculate_branch_comparisons(
        self, branches: list[BranchAnalytics]
    ) -> BranchComparison:
        """Calculate branch comparison metrics."""
        if not branches:
            return BranchComparison(
                main_vs_feature_cost_ratio=0.0,
                avg_feature_branch_lifetime_days=0.0,
                most_expensive_branch_type=BranchType.OTHER,
            )

        # Calculate costs by branch type
        type_costs: dict[BranchType, float] = {}
        feature_lifetimes: list[int] = []

        for branch in branches:
            branch_type = branch.type
            cost = branch.metrics.cost

            type_costs[branch_type] = type_costs.get(branch_type, 0) + cost

            if branch_type == BranchType.FEATURE:
                feature_lifetimes.append(branch.metrics.active_days)

        # Main vs feature cost ratio
        main_cost = type_costs.get(BranchType.MAIN, 0)
        feature_cost = type_costs.get(BranchType.FEATURE, 0)
        main_vs_feature_ratio = main_cost / feature_cost if feature_cost > 0 else 0.0

        # Average feature branch lifetime
        avg_feature_lifetime = (
            sum(feature_lifetimes) / len(feature_lifetimes)
            if feature_lifetimes
            else 0.0
        )

        # Most expensive branch type
        most_expensive_type = (
            max(type_costs.items(), key=lambda x: x[1])[0]
            if type_costs
            else BranchType.OTHER
        )

        return BranchComparison(
            main_vs_feature_cost_ratio=round(main_vs_feature_ratio, 2),
            avg_feature_branch_lifetime_days=round(avg_feature_lifetime, 1),
            most_expensive_branch_type=most_expensive_type,
        )

    async def get_token_efficiency_summary(
        self,
        session_id: str | None = None,
        time_range: TimeRange = TimeRange.LAST_30_DAYS,
        include_cache_metrics: bool = True,
    ) -> TokenEfficiencySummary:
        """Get token efficiency summary for stat card display."""
        # Build match filter
        match_filter = self._get_time_filter(time_range)

        if session_id:
            match_filter["sessionId"] = session_id

        # Aggregation pipeline to calculate token totals
        pipeline: list[dict[str, Any]] = [
            {"$match": match_filter},
            {
                "$group": {
                    "_id": None,
                    "total_input": {"$sum": {"$ifNull": ["$usage.input_tokens", 0]}},
                    "total_output": {"$sum": {"$ifNull": ["$usage.output_tokens", 0]}},
                    "total_cost": {
                        "$sum": {"$ifNull": [{"$ifNull": ["$cost_usd", "$costUsd"]}, 0]}
                    },
                    "message_count": {"$sum": 1},
                    # Extract cache tokens from usage field
                    "cache_creation": {
                        "$sum": {"$ifNull": ["$usage.cache_creation_input_tokens", 0]}
                    },
                    "cache_read": {
                        "$sum": {"$ifNull": ["$usage.cache_read_input_tokens", 0]}
                    },
                    "cache_tokens": {
                        "$sum": {
                            "$add": [
                                {
                                    "$ifNull": [
                                        "$usage.cache_creation_input_tokens",
                                        0,
                                    ]
                                },
                                {
                                    "$ifNull": [
                                        "$usage.cache_read_input_tokens",
                                        0,
                                    ]
                                },
                            ]
                        }
                    },
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)

        if not result:
            return TokenEfficiencySummary(
                total_tokens=0, formatted_total="0", cost_estimate=0.0, trend="stable"
            )

        data = result[0]
        total_input = int(self._safe_float(data.get("total_input", 0)))
        total_output = int(self._safe_float(data.get("total_output", 0)))
        total_tokens = total_input + total_output
        total_cost = self._safe_float(data.get("total_cost", 0))

        # Format total tokens
        formatted_total = self._format_token_count(total_tokens)

        # Calculate trend (simplified - could be enhanced with previous period comparison)
        trend = "stable"  # TODO: Implement trend calculation

        return TokenEfficiencySummary(
            total_tokens=total_tokens,
            formatted_total=formatted_total,
            cost_estimate=round(total_cost, 2),
            trend=trend,
        )

    async def get_token_efficiency_detailed(
        self,
        session_id: str | None = None,
        time_range: TimeRange = TimeRange.LAST_30_DAYS,
        include_cache_metrics: bool = True,
    ) -> TokenEfficiencyDetailed:
        """Get detailed token efficiency analytics for details panel."""
        # Build match filter
        match_filter = self._get_time_filter(time_range)

        if session_id:
            resolved_id = await self._resolve_session_id(session_id)
            if resolved_id:
                match_filter["sessionId"] = resolved_id
            else:
                # Session not found, return empty result
                empty_breakdown = TokenBreakdown(
                    input_tokens=0,
                    output_tokens=0,
                    cache_creation=0,
                    cache_read=0,
                    total=0,
                )
                empty_metrics = TokenEfficiencyMetrics(
                    cache_hit_rate=0.0,
                    input_output_ratio=0.0,
                    avg_tokens_per_message=0.0,
                    cost_per_token=0.0,
                )
                empty_formatted = TokenFormattedValues(
                    total="0", input="0", output="0", cache_creation="0", cache_read="0"
                )
                return TokenEfficiencyDetailed(
                    token_breakdown=empty_breakdown,
                    efficiency_metrics=empty_metrics,
                    formatted_values=empty_formatted,
                    session_id=session_id,
                    time_range=time_range,
                    generated_at=datetime.utcnow(),
                )

        # Aggregation pipeline for detailed token analysis
        pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    **match_filter,
                    "usage": {"$exists": True},
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_input": {
                        "$sum": {
                            "$ifNull": [
                                "$usage.input_tokens",
                                0,
                            ]
                        }
                    },
                    "total_output": {
                        "$sum": {
                            "$ifNull": [
                                "$usage.output_tokens",
                                0,
                            ]
                        }
                    },
                    "total_cost": {
                        "$sum": {"$ifNull": [{"$ifNull": ["$cost_usd", "$costUsd"]}, 0]}
                    },
                    "message_count": {"$sum": 1},
                    # Extract cache metrics from usage field
                    "cache_creation": {
                        "$sum": {
                            "$ifNull": [
                                "$usage.cache_creation_input_tokens",
                                0,
                            ]
                        }
                    },
                    "cache_read": {
                        "$sum": {"$ifNull": ["$usage.cache_read_input_tokens", 0]}
                    },
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)

        if not result:
            # Return empty result structure
            empty_breakdown = TokenBreakdown(
                input_tokens=0, output_tokens=0, cache_creation=0, cache_read=0, total=0
            )
            empty_metrics = TokenEfficiencyMetrics(
                cache_hit_rate=0.0,
                input_output_ratio=0.0,
                avg_tokens_per_message=0.0,
                cost_per_token=0.0,
            )
            empty_formatted = TokenFormattedValues(
                total="0", input="0", output="0", cache_creation="0", cache_read="0"
            )

            return TokenEfficiencyDetailed(
                token_breakdown=empty_breakdown,
                efficiency_metrics=empty_metrics,
                formatted_values=empty_formatted,
                session_id=session_id,
                time_range=time_range,
            )

        data = result[0]
        total_input = int(self._safe_float(data.get("total_input", 0)))
        total_output = int(self._safe_float(data.get("total_output", 0)))
        cache_creation = (
            int(self._safe_float(data.get("cache_creation", 0)))
            if include_cache_metrics
            else 0
        )
        cache_read = (
            int(self._safe_float(data.get("cache_read", 0)))
            if include_cache_metrics
            else 0
        )
        total_tokens = total_input + total_output
        total_cost = self._safe_float(data.get("total_cost", 0))
        message_count = int(self._safe_float(data.get("message_count", 1)))

        # Build token breakdown
        token_breakdown = TokenBreakdown(
            input_tokens=total_input,
            output_tokens=total_output,
            cache_creation=cache_creation,
            cache_read=cache_read,
            total=total_tokens,
        )

        # Calculate efficiency metrics
        cache_hit_rate = 0.0
        if cache_creation + cache_read > 0:
            cache_hit_rate = (cache_read / (cache_creation + cache_read)) * 100
            # Ensure cache hit rate is within valid range
            cache_hit_rate = min(max(cache_hit_rate, 0.0), 100.0)

        input_output_ratio = 0.0
        if total_output > 0:
            input_output_ratio = total_input / total_output

        avg_tokens_per_message = (
            total_tokens / message_count if message_count > 0 else 0
        )
        cost_per_token = total_cost / total_tokens if total_tokens > 0 else 0

        efficiency_metrics = TokenEfficiencyMetrics(
            cache_hit_rate=round(cache_hit_rate, 1),
            input_output_ratio=round(input_output_ratio, 2),
            avg_tokens_per_message=round(avg_tokens_per_message, 1),
            cost_per_token=round(cost_per_token, 6),
        )

        # Format values for display
        formatted_values = TokenFormattedValues(
            total=self._format_token_count(total_tokens),
            input=self._format_token_count(total_input),
            output=self._format_token_count(total_output),
            cache_creation=self._format_token_count(cache_creation),
            cache_read=self._format_token_count(cache_read),
        )

        return TokenEfficiencyDetailed(
            token_breakdown=token_breakdown,
            efficiency_metrics=efficiency_metrics,
            formatted_values=formatted_values,
            session_id=session_id,
            time_range=time_range,
        )

    def _format_token_count(self, count: int) -> str:
        """Format token count for display (e.g., 45K, 1.2M)."""
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        elif count >= 1_000:
            return f"{count // 1_000}K"
        else:
            return str(count)

    async def get_session_depth_analytics(
        self,
        time_range: TimeRange,
        project_id: str | None = None,
        min_depth: int = 0,
        include_sidechains: bool = True,
    ) -> SessionDepthAnalytics:
        """Get session depth analytics.

        Analyzes conversation depth patterns, correlations, and provides optimization recommendations.
        """
        time_filter = self._get_time_filter(time_range)

        # Add project filter if specified
        if project_id:
            # First get sessions for the project
            sessions_cursor = self.db.sessions.find({"projectId": ObjectId(project_id)})
            session_ids = [session["sessionId"] async for session in sessions_cursor]
            if not session_ids:
                # No sessions found for this project
                return SessionDepthAnalytics(
                    depth_distribution=[],
                    depth_correlations=DepthCorrelations(
                        depth_vs_cost=0.0, depth_vs_duration=0.0, depth_vs_success=0.0
                    ),
                    patterns=[],
                    recommendations=DepthRecommendations(
                        optimal_depth_range=(0, 0),
                        warning_threshold=0,
                        tips=["No data available for this project"],
                    ),
                    time_range=time_range,
                )
            time_filter["sessionId"] = {"$in": session_ids}

        # Get all messages with their conversation tree structure
        messages_pipeline = [
            {"$match": time_filter},
            {
                "$project": {
                    "uuid": 1,
                    "sessionId": 1,
                    "parentUuid": 1,
                    "isSidechain": 1,
                    "costUsd": 1,
                    "durationMs": 1,
                    "timestamp": 1,
                    "type": 1,
                }
            },
            {"$sort": {"sessionId": 1, "timestamp": 1}},
        ]

        messages = await self.db.messages.aggregate(messages_pipeline).to_list(None)

        # Build conversation trees per session and calculate depths
        session_data: dict[str, list[dict[str, Any]]] = {}
        session_depths: dict[str, dict[str, int]] = {}

        for message in messages:
            session_id = message["sessionId"]

            if session_id not in session_data:
                session_data[session_id] = []
                session_depths[session_id] = {}

            session_data[session_id].append(message)

        # Calculate depth for each session
        depth_stats = []

        for session_id, session_messages in session_data.items():
            depths = self._calculate_conversation_depths(
                session_messages, include_sidechains
            )
            if not depths:
                continue

            max_depth = max(depths.values())
            avg_depth = sum(depths.values()) / len(depths)

            # Skip sessions below minimum depth
            if max_depth < min_depth:
                continue

            # Calculate session metrics
            session_cost = sum(
                self._safe_float(msg.get("costUsd", 0))
                for msg in session_messages
                if msg.get("costUsd") is not None
            )
            session_duration = sum(
                msg.get("durationMs", 0) or 0
                for msg in session_messages
                if msg.get("durationMs")
            )
            message_count = len(session_messages)

            # Calculate success rate (simplified - based on non-null costs as proxy for successful assistant responses)
            successful_responses = sum(
                1
                for msg in session_messages
                if msg.get("costUsd") and msg.get("type") == "assistant"
            )
            total_requests = sum(
                1 for msg in session_messages if msg.get("type") == "user"
            )
            success_rate = (
                (successful_responses / total_requests * 100)
                if total_requests > 0
                else 0
            )

            depth_stats.append(
                {
                    "session_id": session_id,
                    "max_depth": max_depth,
                    "avg_depth": avg_depth,
                    "cost": session_cost,
                    "duration": session_duration,
                    "message_count": message_count,
                    "success_rate": success_rate,
                    "branch_count": len(
                        [d for d in depths.values() if d > 1]
                    ),  # Messages with depth > 1 indicate branching
                }
            )

        if not depth_stats:
            return SessionDepthAnalytics(
                depth_distribution=[],
                depth_correlations=DepthCorrelations(
                    depth_vs_cost=0.0, depth_vs_duration=0.0, depth_vs_success=0.0
                ),
                patterns=[],
                recommendations=DepthRecommendations(
                    optimal_depth_range=(0, 0),
                    warning_threshold=0,
                    tips=["No conversations found matching the specified criteria"],
                ),
                time_range=time_range,
            )

        # Calculate depth distribution
        depth_distribution = self._calculate_depth_distribution(depth_stats)

        # Calculate correlations
        depth_correlations = self._calculate_depth_correlations(depth_stats)

        # Identify conversation patterns
        patterns = self._identify_conversation_patterns(depth_stats)

        # Generate recommendations
        recommendations = self._generate_depth_recommendations(
            depth_stats, depth_distribution
        )

        return SessionDepthAnalytics(
            depth_distribution=depth_distribution,
            depth_correlations=depth_correlations,
            patterns=patterns,
            recommendations=recommendations,
            time_range=time_range,
        )

    def _calculate_conversation_depths(
        self, messages: list[dict], include_sidechains: bool
    ) -> dict[str, int]:
        """Calculate depth for each message in a conversation."""
        depths: dict[str, int] = {}
        message_map = {msg["uuid"]: msg for msg in messages}

        def get_depth(uuid: str) -> int:
            if uuid in depths:
                return depths[uuid]

            message = message_map.get(uuid)
            if not message:
                return 0

            # Skip sidechains if not included
            if not include_sidechains and message.get("isSidechain", False):
                depths[uuid] = 0
                return 0

            parent_uuid = message.get("parentUuid")
            if not parent_uuid:
                depths[uuid] = 1
                return 1

            parent_depth = get_depth(parent_uuid)
            depths[uuid] = parent_depth + 1
            return int(depths[uuid])

        # Calculate depths for all messages
        for message in messages:
            get_depth(message["uuid"])

        return depths

    def _calculate_depth_distribution(
        self, depth_stats: list[dict]
    ) -> list[DepthDistribution]:
        """Calculate depth distribution statistics."""
        from collections import defaultdict

        depth_groups = defaultdict(list)
        total_sessions = len(depth_stats)

        # Group sessions by max depth
        for stat in depth_stats:
            depth_groups[stat["max_depth"]].append(stat)

        distribution = []
        for depth in sorted(depth_groups.keys()):
            sessions = depth_groups[depth]
            session_count = len(sessions)
            avg_cost = sum(s["cost"] for s in sessions) / session_count
            avg_messages = sum(s["message_count"] for s in sessions) / session_count
            percentage = (session_count / total_sessions) * 100

            distribution.append(
                DepthDistribution(
                    depth=depth,
                    session_count=session_count,
                    avg_cost=round(avg_cost, 4),
                    avg_messages=int(avg_messages),
                    percentage=round(percentage, 1),
                )
            )

        return distribution

    def _calculate_depth_correlations(
        self, depth_stats: list[dict]
    ) -> DepthCorrelations:
        """Calculate correlations between depth and other metrics."""
        if len(depth_stats) < 2:
            return DepthCorrelations(
                depth_vs_cost=0.0,
                depth_vs_duration=0.0,
                depth_vs_success=0.0,
            )

        depths = [s["max_depth"] for s in depth_stats]
        costs = [s["cost"] for s in depth_stats]
        durations = [s["duration"] for s in depth_stats if s["duration"] > 0]
        success_rates = [s["success_rate"] for s in depth_stats]

        def calculate_correlation(x: list[float], y: list[float]) -> float:
            """Calculate Pearson correlation coefficient."""
            if len(x) != len(y) or len(x) < 2:
                return 0.0

            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(xi * yi for xi, yi in zip(x, y))
            sum_x2 = sum(xi * xi for xi in x)
            sum_y2 = sum(yi * yi for yi in y)

            denominator = (
                (n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)
            ) ** 0.5
            if denominator == 0:
                return 0.0

            return float((n * sum_xy - sum_x * sum_y) / denominator)

        depth_vs_cost = calculate_correlation(depths, costs)

        # For duration correlation, only use sessions with duration data
        duration_depths = [
            depth_stats[i]["max_depth"]
            for i in range(len(depth_stats))
            if depth_stats[i]["duration"] > 0
        ]
        depth_vs_duration = (
            calculate_correlation(duration_depths, durations)
            if len(durations) >= 2
            else 0.0
        )

        depth_vs_success = calculate_correlation(depths, success_rates)

        return DepthCorrelations(
            depth_vs_cost=round(depth_vs_cost, 3),
            depth_vs_duration=round(depth_vs_duration, 3),
            depth_vs_success=round(depth_vs_success, 3),
        )

    def _identify_conversation_patterns(
        self, depth_stats: list[dict]
    ) -> list[ConversationPattern]:
        """Identify common conversation patterns."""
        patterns: list[ConversationPattern] = []
        total_sessions = len(depth_stats)

        if total_sessions == 0:
            return patterns

        # Categorize sessions by depth and branching patterns
        shallow_wide = [
            s for s in depth_stats if s["max_depth"] <= 3 and s["branch_count"] >= 2
        ]
        deep_narrow = [
            s for s in depth_stats if s["max_depth"] > 6 and s["branch_count"] <= 1
        ]
        balanced = [
            s for s in depth_stats if 3 < s["max_depth"] <= 6 and s["branch_count"] >= 1
        ]
        linear = [s for s in depth_stats if s["branch_count"] == 0]

        pattern_data = [
            (
                shallow_wide,
                "shallow-wide",
                "Quick iterations with multiple exploration paths",
            ),
            (
                deep_narrow,
                "deep-narrow",
                "Extended single-thread conversations with deep exploration",
            ),
            (
                balanced,
                "balanced",
                "Moderate depth with some branching and exploration",
            ),
            (linear, "linear", "Straightforward conversations without branching"),
        ]

        for sessions, name, description in pattern_data:
            if sessions:
                frequency = len(sessions)
                avg_cost = sum(s["cost"] for s in sessions) / frequency

                patterns.append(
                    ConversationPattern(
                        pattern_name=name,
                        frequency=frequency,
                        avg_cost=round(avg_cost, 4),
                        typical_use_case=description,
                    )
                )

        return patterns

    def _generate_depth_recommendations(
        self, depth_stats: list[dict], distribution: list[DepthDistribution]
    ) -> DepthRecommendations:
        """Generate optimization recommendations based on depth analysis."""
        if not depth_stats:
            return DepthRecommendations(
                optimal_depth_range=(0, 0),
                warning_threshold=0,
                tips=["No data available for recommendations"],
            )

        # Find optimal depth range based on cost efficiency
        cost_by_depth = {}
        for dist in distribution:
            cost_by_depth[dist.depth] = dist.avg_cost

        if cost_by_depth:
            # Find depths with below-average cost
            avg_cost = sum(cost_by_depth.values()) / len(cost_by_depth)
            efficient_depths = [d for d, c in cost_by_depth.items() if c <= avg_cost]

            if efficient_depths:
                optimal_range = (min(efficient_depths), max(efficient_depths))
            else:
                # Fallback to middle range
                all_depths = list(cost_by_depth.keys())
                optimal_range = (min(all_depths), max(all_depths))
        else:
            optimal_range = (1, 5)  # Default reasonable range

        # Set warning threshold (significantly above optimal range)
        warning_threshold = max(optimal_range[1] * 2, 10)

        # Generate tips
        tips = []
        max_depth = max(s["max_depth"] for s in depth_stats)
        avg_depth = sum(s["max_depth"] for s in depth_stats) / len(depth_stats)

        if avg_depth > 8:
            tips.append(
                "Consider breaking complex conversations into smaller, focused sessions"
            )

        if max_depth > 15:
            tips.append(
                "Very deep conversations detected - review if all iterations were necessary"
            )

        # Check for cost efficiency
        high_cost_sessions = [s for s in depth_stats if s["cost"] > 1.0]  # $1+ sessions
        if (
            len(high_cost_sessions) > len(depth_stats) * 0.1
        ):  # More than 10% are high cost
            tips.append(
                "High-cost sessions detected - consider optimizing conversation structure"
            )

        # Check for branching patterns
        low_branch_sessions = [s for s in depth_stats if s["branch_count"] == 0]
        if (
            len(low_branch_sessions) > len(depth_stats) * 0.7
        ):  # More than 70% are linear
            tips.append(
                "Most conversations are linear - consider exploring alternative approaches when stuck"
            )

        if not tips:
            tips.append("Conversation depth patterns look healthy")

        return DepthRecommendations(
            optimal_depth_range=optimal_range,
            warning_threshold=warning_threshold,
            tips=tips,
        )

    # Cost Prediction Dashboard Methods

    def _format_cost(self, cost: float) -> str:
        """Format cost according to the requirements."""
        if cost == 0:
            return "$0.00"
        if cost < 0.01:
            return "<$0.01"
        if cost < 1:
            return f"${cost:.2f}"
        if cost < 100:
            return f"${cost:.2f}"
        return f"${cost:.0f}"

    async def get_cost_summary(
        self, session_id: str | None, project_id: str | None, time_range: TimeRange
    ) -> CostSummary:
        """Get cost summary for stat card display."""
        time_filter = self._get_time_filter(time_range)

        # Build base filter
        base_filter = {**time_filter, "costUsd": {"$exists": True, "$ne": None}}

        # Add session filter if specified
        if session_id:
            base_filter["sessionId"] = session_id

        # Add project filter if specified
        if project_id:
            session_ids = await self.db.sessions.distinct(
                "sessionId", {"projectId": ObjectId(project_id)}
            )
            if "sessionId" in base_filter:
                # If session_id is already specified, ensure it's in the project
                if session_id not in session_ids:
                    base_filter["sessionId"] = {"$in": []}  # Empty result
            else:
                base_filter["sessionId"] = {"$in": session_ids}

        # Get current period cost
        current_cost = await self.db.messages.aggregate(
            [
                {"$match": base_filter},
                {"$group": {"_id": None, "total_cost": {"$sum": "$costUsd"}}},
            ]
        ).to_list(None)

        total_cost = (
            self._safe_float(current_cost[0]["total_cost"]) if current_cost else 0.0
        )

        # Get previous period for trend calculation
        trend = "stable"
        if time_range != TimeRange.ALL_TIME:
            prev_filter = self._get_previous_period_filter(time_range)
            if session_id:
                prev_filter["sessionId"] = session_id
            if project_id:
                prev_filter["sessionId"] = {"$in": session_ids}
            prev_filter["costUsd"] = {"$exists": True, "$ne": None}

            prev_cost = await self.db.messages.aggregate(
                [
                    {"$match": prev_filter},
                    {"$group": {"_id": None, "total_cost": {"$sum": "$costUsd"}}},
                ]
            ).to_list(None)

            prev_total = (
                self._safe_float(prev_cost[0]["total_cost"]) if prev_cost else 0.0
            )

            if prev_total > 0:
                change_pct = ((total_cost - prev_total) / prev_total) * 100
                if change_pct > 5:
                    trend = "up"
                elif change_pct < -5:
                    trend = "down"

        # Determine period string
        period_map = {
            TimeRange.LAST_24_HOURS: "24h",
            TimeRange.LAST_7_DAYS: "7d",
            TimeRange.LAST_30_DAYS: "30d",
            TimeRange.LAST_90_DAYS: "90d",
            TimeRange.LAST_YEAR: "1y",
            TimeRange.ALL_TIME: "all time",
        }
        period = period_map.get(time_range, "custom")

        return CostSummary(
            total_cost=round(total_cost, 4),
            formatted_cost=self._format_cost(total_cost),
            currency="USD",
            trend=trend,
            period=period,
        )

    async def get_cost_breakdown(
        self, session_id: str | None, project_id: str | None, time_range: TimeRange
    ) -> CostBreakdownResponse:
        """Get detailed cost breakdown for analytics panels."""
        time_filter = self._get_time_filter(time_range)

        # Build base filter
        base_filter = {**time_filter, "costUsd": {"$exists": True, "$ne": None}}

        # Add session filter if specified
        if session_id:
            resolved_id = await self._resolve_session_id(session_id)
            if resolved_id:
                base_filter["sessionId"] = resolved_id
            else:
                # Session not found, return empty result
                return CostBreakdownResponse(
                    cost_breakdown=CostBreakdown(by_model=[], by_time=[]),
                    cost_metrics=CostMetrics(
                        avg_cost_per_message=0.0,
                        avg_cost_per_hour=0.0,
                        most_expensive_model=None,
                    ),
                    time_range=time_range,
                    session_id=session_id,
                    project_id=project_id,
                )

        # Add project filter if specified
        if project_id:
            session_ids = await self.db.sessions.distinct(
                "sessionId", {"projectId": ObjectId(project_id)}
            )
            if "sessionId" in base_filter:
                if session_id not in session_ids:
                    base_filter["sessionId"] = {"$in": []}
            else:
                base_filter["sessionId"] = {"$in": session_ids}

        # Get cost breakdown by model
        model_breakdown = await self.db.messages.aggregate(
            [
                {"$match": base_filter},
                {
                    "$group": {
                        "_id": {"$ifNull": ["$model", "unknown"]},
                        "cost": {"$sum": "$costUsd"},
                        "message_count": {"$sum": 1},
                    }
                },
                {"$sort": {"cost": -1}},
            ]
        ).to_list(None)

        total_cost = sum(self._safe_float(item["cost"]) for item in model_breakdown)

        by_model = []
        for item in model_breakdown:
            model = item["_id"]
            cost = self._safe_float(item["cost"])
            message_count = item["message_count"]
            percentage = (cost / total_cost * 100) if total_cost > 0 else 0

            by_model.append(
                CostBreakdownItem(
                    model=model,
                    cost=round(cost, 4),
                    percentage=round(percentage, 2),
                    message_count=message_count,
                )
            )

        # Get cost breakdown over time (daily)
        daily_costs = await self.db.messages.aggregate(
            [
                {"$match": base_filter},
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$timestamp",
                            }
                        },
                        "cost": {"$sum": "$costUsd"},
                    }
                },
                {"$sort": {"_id": 1}},
            ]
        ).to_list(None)

        by_time = []
        cumulative_cost = 0.0
        for item in daily_costs:
            date_str = item["_id"]
            cost = self._safe_float(item["cost"])
            cumulative_cost += cost

            try:
                timestamp = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue

            by_time.append(
                CostTimePoint(
                    timestamp=timestamp,
                    cost=round(cost, 4),
                    cumulative=round(cumulative_cost, 4),
                )
            )

        # Calculate metrics
        message_count = await self.db.messages.count_documents(base_filter)
        avg_cost_per_message = total_cost / message_count if message_count > 0 else 0

        # Calculate avg cost per hour (rough estimate based on time range)
        hours_in_period = {
            TimeRange.LAST_24_HOURS: 24,
            TimeRange.LAST_7_DAYS: 168,
            TimeRange.LAST_30_DAYS: 720,
            TimeRange.LAST_90_DAYS: 2160,
            TimeRange.LAST_YEAR: 8760,
        }.get(
            time_range, 720
        )  # Default to 30 days

        avg_cost_per_hour = total_cost / hours_in_period if hours_in_period > 0 else 0

        most_expensive_model = by_model[0].model if by_model else None

        cost_breakdown = CostBreakdown(by_model=by_model, by_time=by_time)
        cost_metrics = CostMetrics(
            avg_cost_per_message=round(avg_cost_per_message, 4),
            avg_cost_per_hour=round(avg_cost_per_hour, 4),
            most_expensive_model=most_expensive_model,
        )

        return CostBreakdownResponse(
            cost_breakdown=cost_breakdown,
            cost_metrics=cost_metrics,
            time_range=time_range,
            session_id=session_id,
            project_id=project_id,
        )

    async def get_cost_prediction(
        self, session_id: str | None, project_id: str | None, prediction_days: int
    ) -> CostPrediction:
        """Get cost forecasting predictions."""
        # Use the last 30 days as historical data for prediction
        historical_filter = self._get_time_filter(TimeRange.LAST_30_DAYS)

        # Build base filter
        base_filter = {**historical_filter, "costUsd": {"$exists": True, "$ne": None}}

        # Add session filter if specified
        if session_id:
            base_filter["sessionId"] = session_id

        # Add project filter if specified
        if project_id:
            session_ids = await self.db.sessions.distinct(
                "sessionId", {"projectId": ObjectId(project_id)}
            )
            if "sessionId" in base_filter:
                if session_id not in session_ids:
                    base_filter["sessionId"] = {"$in": []}
            else:
                base_filter["sessionId"] = {"$in": session_ids}

        # Get daily costs for the last 30 days
        daily_costs = await self.db.messages.aggregate(
            [
                {"$match": base_filter},
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$timestamp",
                            }
                        },
                        "cost": {"$sum": "$costUsd"},
                    }
                },
                {"$sort": {"_id": 1}},
            ]
        ).to_list(None)

        if not daily_costs:
            # No historical data, return zero predictions
            predictions = []
            start_date = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            for i in range(prediction_days):
                prediction_date = start_date + timedelta(days=i + 1)
                predictions.append(
                    CostPredictionPoint(
                        date=prediction_date,
                        predicted_cost=0.0,
                        confidence_interval=(0.0, 0.0),
                    )
                )

            return CostPrediction(
                predictions=predictions,
                total_predicted=0.0,
                confidence_level=0.95,
                model_accuracy=0.0,
                prediction_days=prediction_days,
                session_id=session_id,
                project_id=project_id,
            )

        # Calculate simple moving average for prediction
        costs = [self._safe_float(item["cost"]) for item in daily_costs]

        # Simple prediction: use the average of recent days
        recent_days = min(7, len(costs))  # Use last 7 days or all available
        avg_daily_cost = (
            sum(costs[-recent_days:]) / recent_days if recent_days > 0 else 0
        )

        # Calculate standard deviation for confidence intervals
        if len(costs) > 1:
            variance = (
                sum((cost - avg_daily_cost) ** 2 for cost in costs[-recent_days:])
                / recent_days
            )
            std_dev = variance**0.5
        else:
            std_dev = avg_daily_cost * 0.2  # 20% uncertainty if only one data point

        # Generate predictions
        predictions = []
        start_date = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        total_predicted = 0.0

        for i in range(prediction_days):
            prediction_date = start_date + timedelta(days=i + 1)

            # Simple linear prediction with slight decay for longer periods
            decay_factor = 0.95 ** (i // 7)  # Decay every 7 days
            predicted_cost = avg_daily_cost * decay_factor

            # 95% confidence interval (±1.96 standard deviations)
            margin = 1.96 * std_dev * decay_factor
            confidence_lower = max(0, predicted_cost - margin)
            confidence_upper = predicted_cost + margin

            predictions.append(
                CostPredictionPoint(
                    date=prediction_date,
                    predicted_cost=round(predicted_cost, 4),
                    confidence_interval=(
                        round(confidence_lower, 4),
                        round(confidence_upper, 4),
                    ),
                )
            )

            total_predicted += predicted_cost

        # Mock model accuracy (would be calculated from historical prediction performance)
        model_accuracy = 75.0  # Assume 75% accuracy for simple moving average model

        return CostPrediction(
            predictions=predictions,
            total_predicted=round(total_predicted, 4),
            confidence_level=0.95,
            model_accuracy=model_accuracy,
            prediction_days=prediction_days,
            session_id=session_id,
            project_id=project_id,
        )

    # Topic Extraction Methods

    def _get_topic_rules(self) -> dict[str, dict[str, Any]]:
        """Get topic detection rules with keywords and patterns."""
        return {
            "Web Development": {
                "keywords": [
                    "react",
                    "vue",
                    "angular",
                    "frontend",
                    "css",
                    "html",
                    "javascript",
                    "typescript",
                    "jsx",
                    "tsx",
                    "webpack",
                    "vite",
                    "npm",
                    "yarn",
                    "bootstrap",
                    "tailwind",
                ],
                "file_extensions": [
                    ".js",
                    ".jsx",
                    ".ts",
                    ".tsx",
                    ".css",
                    ".scss",
                    ".html",
                    ".vue",
                ],
                "category": TopicCategory.WEB_DEVELOPMENT,
                "weight": 1.0,
            },
            "API Integration": {
                "keywords": [
                    "claude",
                    "anthropic",
                    "api",
                    "webhook",
                    "endpoint",
                    "rest",
                    "graphql",
                    "json",
                    "http",
                    "curl",
                    "fetch",
                    "axios",
                ],
                "file_extensions": [".json", ".yaml", ".yml"],
                "category": TopicCategory.API_INTEGRATION,
                "weight": 1.0,
            },
            "Data Visualization": {
                "keywords": [
                    "chart",
                    "graph",
                    "plot",
                    "dashboard",
                    "metrics",
                    "d3",
                    "plotly",
                    "matplotlib",
                    "seaborn",
                    "visualization",
                    "analytics",
                ],
                "file_extensions": [".csv", ".json"],
                "category": TopicCategory.DATA_VISUALIZATION,
                "weight": 1.0,
            },
            "Machine Learning": {
                "keywords": [
                    "ml",
                    "ai",
                    "model",
                    "training",
                    "prediction",
                    "tensorflow",
                    "pytorch",
                    "sklearn",
                    "pandas",
                    "numpy",
                    "jupyter",
                    "notebook",
                ],
                "file_extensions": [".py", ".ipynb"],
                "category": TopicCategory.MACHINE_LEARNING,
                "weight": 1.0,
            },
            "Database Operations": {
                "keywords": [
                    "mongodb",
                    "sql",
                    "postgres",
                    "mysql",
                    "database",
                    "query",
                    "collection",
                    "schema",
                    "migration",
                    "orm",
                ],
                "file_extensions": [".sql", ".db"],
                "category": TopicCategory.DATABASE_OPERATIONS,
                "weight": 1.0,
            },
            "DevOps/Deployment": {
                "keywords": [
                    "docker",
                    "kubernetes",
                    "deployment",
                    "ci/cd",
                    "github actions",
                    "pipeline",
                    "terraform",
                    "aws",
                    "azure",
                    "gcp",
                    "nginx",
                    "apache",
                ],
                "file_extensions": [".dockerfile", ".yml", ".yaml", ".tf"],
                "category": TopicCategory.DEVOPS_DEPLOYMENT,
                "weight": 1.0,
            },
            "Testing/QA": {
                "keywords": [
                    "test",
                    "jest",
                    "vitest",
                    "pytest",
                    "junit",
                    "unit test",
                    "integration test",
                    "mock",
                    "assert",
                    "spec",
                ],
                "file_extensions": [".test.js", ".test.ts", ".spec.js", ".spec.ts"],
                "category": TopicCategory.TESTING_QA,
                "weight": 1.0,
            },
            "Documentation": {
                "keywords": [
                    "readme",
                    "documentation",
                    "docs",
                    "markdown",
                    "wiki",
                    "guide",
                    "tutorial",
                    "comment",
                ],
                "file_extensions": [".md", ".rst", ".txt"],
                "category": TopicCategory.DOCUMENTATION,
                "weight": 0.8,
            },
        }

    def _extract_keywords_from_content(self, content: str) -> list[str]:
        """Extract relevant keywords from message content."""
        # Convert to lowercase for matching
        content_lower = content.lower()

        # Extract file paths and extensions
        file_patterns = re.findall(r"\b\w+\.\w+\b", content_lower)

        # Also extract file paths with slashes
        path_patterns = re.findall(r"[\w/\-_]+\.\w+", content_lower)
        file_patterns.extend(path_patterns)

        # Extract framework/library mentions - expanded list
        tech_patterns = re.findall(
            r"\b(?:react|vue|angular|python|javascript|typescript|node|express|django|flask|mongodb|postgresql|mysql|docker|kubernetes|aws|azure|gcp|github|gitlab|ci/cd|api|rest|graphql|jwt|oauth|npm|yarn|pip|conda|webpack|vite|babel|eslint|prettier|jest|vitest|pytest|jupyter|pandas|numpy|tensorflow|pytorch|sklearn|matplotlib|seaborn|plotly|d3|bootstrap|tailwind|sass|scss|css|html|json|yaml|xml|sql|nosql|redis|elasticsearch|nginx|apache|terraform|ansible|jenkins|gradle|maven|spring|django|rails|laravel|nextjs|nuxt|svelte|solid|fastapi|sqlalchemy|alembic|pydantic|uvicorn|poetry|pytest|mypy|ruff|black|flake8|pre-commit|git|bash|linux|macos|windows|vscode|intellij|vim|emacs|chrome|firefox|safari|edge|postman|insomnia|swagger|openapi|grpc|websocket|mqtt|kafka|rabbitmq|celery|cron|systemd|prometheus|grafana|elasticsearch|kibana|logstash|sentry|datadog|newrelic|jenkins|circleci|travisci|githubactions|gitlab-ci|bitbucket|jira|confluence|slack|discord|teams|zoom|figma|sketch|adobe|photoshop|illustrator|premiere|aftereffects|blender|unity|unreal|godot|flutter|dart|kotlin|swift|objective-c|rust|go|golang|ruby|php|perl|scala|clojure|haskell|elixir|erlang|julia|r|matlab|fortran|c\+\+|cpp|java|csharp|dotnet|aspnet|blazor|xamarin|electron|ionic|capacitor|quasar|vuetify|material-ui|ant-design|chakra-ui|semantic-ui|bulma|foundation|materialize|jquery|backbone|ember|polymer|lit|stencil|alpine|htmx|turbo|stimulus|hotwire|phoenix|rails|sinatra|bottle|pyramid|tornado|sanic|starlette|gin|echo|fiber|iris|beego|revel|buffalo|chi|gorilla|mux|httprouter|fasthttp|actix|rocket|warp|tide|async-std|tokio|hyper|reqwest|surf|isahc|ureq|curl|wget|httpie|fetch|axios|superagent|got|node-fetch|request|bent|phin|needle|undici|ky|redaxios|cross-fetch|isomorphic-fetch|whatwg-fetch|unfetch|swr|react-query|apollo|relay|urql|graphql-request|mercurius|graphql-yoga|graphql-tools|graphql-codegen|graphql-inspector|graphql-voyager|graphiql|altair|playground|postwoman|hoppscotch|paw|bruno|thunderclient|restclient|soapui|katalon|selenium|cypress|playwright|puppeteer|webdriver|nightwatch|testcafe|codecept|detox|appium|espresso|xctest|robolectric|junit|testng|nunit|xunit|mstest|jasmine|karma|protractor|enzyme|react-testing-library|vue-test-utils|angular-testing|svelte-testing|solid-testing|vitest|uvu|ava|tap|qunit|intern|nightwatch|webdriverio|selenium-webdriver|chromedriver|geckodriver|safaridriver|edgedriver|iedriver)\b",
            content_lower,
        )

        # Extract tool usage patterns - both old and new formats
        tool_patterns = re.findall(r"\[tool\s+(?:use|result):\s*(\w+)\]", content_lower)

        # Also look for tool usage in different formats
        tool_patterns2 = re.findall(
            r"(?:using|calling|executing)\s+(?:the\s+)?(\w+)\s+tool", content_lower
        )
        tool_patterns.extend(tool_patterns2)

        # Look for file operation indicators
        file_op_patterns = re.findall(
            r"(?:reading|writing|editing|creating|updating|deleting)\s+(?:file\s+)?([/\w\-_.]+\.\w+)",
            content_lower,
        )
        file_patterns.extend(file_op_patterns)

        # Combine all extracted keywords
        keywords = []
        keywords.extend([pattern.lower() for pattern in file_patterns])
        keywords.extend([pattern.lower() for pattern in tech_patterns])
        keywords.extend([pattern.lower() for pattern in tool_patterns])

        return list(set(keywords))  # Remove duplicates

    def _calculate_topic_relevance(
        self,
        keywords: list[str],
        topic_rule: dict[str, Any],
        session_context: dict[str, Any],
    ) -> float:
        """Calculate relevance score for a topic based on keywords and context."""
        base_score = 0.0
        matched_keywords = []

        # Check keyword matches
        rule_keywords = [kw.lower() for kw in topic_rule["keywords"]]
        for keyword in keywords:
            if keyword in rule_keywords:
                base_score += topic_rule["weight"]
                matched_keywords.append(keyword)

        # Check file extension matches
        rule_extensions = topic_rule.get("file_extensions", [])
        for keyword in keywords:
            if any(keyword.endswith(ext) for ext in rule_extensions):
                base_score += topic_rule["weight"] * 0.8
                matched_keywords.append(keyword)

        # Apply context boosts
        if session_context.get("tool_usage"):
            relevant_tools = {
                "Web Development": ["Read", "Edit", "Write", "Grep"],
                "API Integration": ["WebFetch", "Bash"],
                "Database Operations": ["Bash", "Read", "Edit"],
                "DevOps/Deployment": ["Bash", "Read", "Write"],
                "Testing/QA": ["Bash", "Read", "Edit"],
                "Documentation": ["Read", "Write", "Edit"],
            }

            topic_name = None
            for name, rule in self._get_topic_rules().items():
                if rule == topic_rule:
                    topic_name = name
                    break

            if topic_name and topic_name in relevant_tools:
                used_tools = set(session_context["tool_usage"].keys())
                relevant_topic_tools = set(relevant_tools[topic_name])
                if used_tools & relevant_topic_tools:
                    base_score *= 1.2

        # Normalize score to 0-1 range
        relevance_score = min(base_score / 5.0, 1.0)

        return relevance_score

    async def extract_session_topics(
        self, session_id: str, confidence_threshold: float = 0.3
    ) -> TopicExtractionResponse:
        """Extract topics from a session's messages and tool usage."""
        # Resolve session ID
        resolved_id = await self._resolve_session_id(session_id)
        if not resolved_id:
            return TopicExtractionResponse(
                session_id=session_id,
                topics=[],
                suggested_topics=[],
                extraction_method="keyword",
                confidence_threshold=confidence_threshold,
            )

        # Get session messages
        messages = await self.db.messages.find({"sessionId": resolved_id}).to_list(None)

        if not messages:
            return TopicExtractionResponse(
                session_id=resolved_id,
                topics=[],
                suggested_topics=[],
                extraction_method="keyword",
                confidence_threshold=confidence_threshold,
            )

        # Extract all content and build session context
        all_content = ""
        all_keywords = []
        tool_usage: dict[str, int] = {}

        for message in messages:
            # Extract content from message
            content = message.get("content", "")
            if content:
                if isinstance(content, list):
                    # Handle Claude API format with content blocks
                    text_content = " ".join(
                        [
                            block.get("text", "")
                            for block in content
                            if isinstance(block, dict) and block.get("type") == "text"
                        ]
                    )
                    all_content += " " + text_content
                else:
                    all_content += " " + str(content)

            # Track tool usage from tool_use messages
            if message.get("type") == "tool_use" and message.get("messageData"):
                tool_name = message["messageData"].get("name")
                if tool_name:
                    tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1

            # Extract keywords from working directory
            if message.get("cwd"):
                cwd_keywords = self._extract_keywords_from_content(message["cwd"])
                all_keywords.extend(cwd_keywords)

        # Extract keywords from all content
        content_keywords = self._extract_keywords_from_content(all_content)
        all_keywords.extend(content_keywords)

        # Remove duplicates
        all_keywords = list(set(all_keywords))

        # Build session context
        session_context = {
            "tool_usage": tool_usage,
            "message_count": len(messages),
            "has_errors": any(
                msg.get("toolUseResult", {}).get("error") for msg in messages
            ),
        }

        # Apply topic rules
        topic_rules = self._get_topic_rules()
        extracted_topics = []

        for topic_name, rule in topic_rules.items():
            relevance_score = self._calculate_topic_relevance(
                all_keywords, rule, session_context
            )

            if relevance_score >= confidence_threshold:
                # Find matched keywords for this topic
                matched_keywords = []
                rule_keywords = [kw.lower() for kw in rule["keywords"]]
                rule_extensions = rule.get("file_extensions", [])

                for keyword in all_keywords:
                    if keyword in rule_keywords or any(
                        keyword.endswith(ext) for ext in rule_extensions
                    ):
                        matched_keywords.append(keyword)

                confidence = min(relevance_score, 1.0)

                extracted_topics.append(
                    ExtractedTopic(
                        name=topic_name,
                        confidence=confidence,
                        category=rule["category"],
                        relevance_score=relevance_score,
                        keywords=matched_keywords[:5],  # Limit to top 5 keywords
                    )
                )

        # Sort by relevance score
        extracted_topics.sort(key=lambda t: t.relevance_score, reverse=True)

        # Generate suggested topics (topics with lower confidence)
        suggested_topics = []
        for topic_name, rule in topic_rules.items():
            if topic_name not in [t.name for t in extracted_topics]:
                relevance_score = self._calculate_topic_relevance(
                    all_keywords, rule, session_context
                )
                if 0.1 <= relevance_score < confidence_threshold:
                    suggested_topics.append(topic_name)

        return TopicExtractionResponse(
            session_id=session_id,
            topics=extracted_topics,
            suggested_topics=suggested_topics[:5],  # Limit to top 5 suggestions
            extraction_method="keyword",
            confidence_threshold=confidence_threshold,
        )

    async def get_topic_suggestions(
        self, time_range: TimeRange = TimeRange.LAST_30_DAYS
    ) -> TopicSuggestionResponse:
        """Get popular topics and combinations across sessions."""
        time_filter = self._get_time_filter(time_range)

        # Get all sessions in time range
        sessions = await self.db.sessions.find(time_filter).to_list(None)
        session_ids = [session["sessionId"] for session in sessions]

        if not session_ids:
            return TopicSuggestionResponse(
                popular_topics=[], topic_combinations=[], time_range=time_range
            )

        # For demo purposes, return some mock popular topics
        # In a real implementation, this would analyze all sessions
        popular_topics = [
            PopularTopic(
                name="Web Development",
                session_count=min(len(session_ids), 25),
                trend="trending",
                percentage_change=15.2,
            ),
            PopularTopic(
                name="API Integration",
                session_count=min(len(session_ids), 18),
                trend="stable",
                percentage_change=2.1,
            ),
            PopularTopic(
                name="Database Operations",
                session_count=min(len(session_ids), 12),
                trend="declining",
                percentage_change=-8.3,
            ),
            PopularTopic(
                name="Testing/QA",
                session_count=min(len(session_ids), 10),
                trend="trending",
                percentage_change=22.5,
            ),
        ]

        topic_combinations = [
            TopicCombination(
                topics=["Web Development", "API Integration"],
                frequency=min(len(session_ids), 8),
                confidence=0.85,
            ),
            TopicCombination(
                topics=["Database Operations", "API Integration"],
                frequency=min(len(session_ids), 6),
                confidence=0.72,
            ),
            TopicCombination(
                topics=["Web Development", "Testing/QA"],
                frequency=min(len(session_ids), 5),
                confidence=0.68,
            ),
        ]

        return TopicSuggestionResponse(
            popular_topics=popular_topics,
            topic_combinations=topic_combinations,
            time_range=time_range,
        )

    # Performance Benchmarking Methods

    async def get_benchmarks(
        self,
        entity_type: BenchmarkEntityType,
        entity_ids: list[str],
        time_range: TimeRange,
        normalization_method: NormalizationMethod,
        include_percentile_ranks: bool = True,
    ) -> BenchmarkResponse:
        """Get performance benchmarks for specified entities."""
        # Get raw metrics for each entity
        raw_metrics = []
        for entity_id in entity_ids:
            entity_metrics = await self._get_entity_raw_metrics(
                entity_type, entity_id, time_range
            )
            raw_metrics.append({"entity_id": entity_id, **entity_metrics})

        # Calculate normalized scores
        normalized_metrics = self._normalize_metrics(raw_metrics, normalization_method)

        # Calculate percentile ranks if requested
        percentile_ranks = (
            self._calculate_percentile_ranks(raw_metrics)
            if include_percentile_ranks
            else None
        )

        # Create benchmark entities
        benchmarks = []
        for i, entity_id in enumerate(entity_ids):
            entity_name = await self._get_entity_name(entity_type, entity_id)

            benchmark_metrics: BenchmarkMetrics = BenchmarkMetrics(
                **normalized_metrics[i]
            )

            percentile_rank = (
                BenchmarkPercentileRanks(**percentile_ranks[i])
                if percentile_ranks
                else BenchmarkPercentileRanks(
                    cost_efficiency=0, speed=0, quality=0, productivity=0
                )
            )

            strengths, improvement_areas = self._analyze_entity_performance(
                normalized_metrics[i]
            )

            benchmarks.append(
                BenchmarkEntity(
                    entity=entity_name,
                    entity_type=entity_type,
                    metrics=benchmark_metrics,
                    percentile_ranks=percentile_rank,
                    strengths=strengths,
                    improvement_areas=improvement_areas,
                )
            )

        # Create comparison matrix
        comparison_matrix = self._create_comparison_matrix(benchmarks)

        # Generate insights
        insights = self._generate_benchmark_insights(benchmarks, raw_metrics)

        return BenchmarkResponse(
            benchmarks=benchmarks,
            comparison_matrix=comparison_matrix,
            insights=insights,
            normalization_method=normalization_method,
            time_range=time_range,
        )

    async def get_benchmark_comparison(
        self,
        primary_entity_id: str,
        comparison_entity_ids: list[str],
        entity_type: BenchmarkEntityType,
        time_range: TimeRange,
        metrics_to_compare: list[str] | None = None,
    ) -> BenchmarkResponse:
        """Get focused benchmark comparison against a primary entity."""
        all_entity_ids = [primary_entity_id] + comparison_entity_ids

        # Use the standard benchmark method but with focus on comparison
        result = await self.get_benchmarks(
            entity_type=entity_type,
            entity_ids=all_entity_ids,
            time_range=time_range,
            normalization_method=NormalizationMethod.Z_SCORE,
            include_percentile_ranks=True,
        )

        # Filter metrics if specified
        if metrics_to_compare:
            result = self._filter_benchmark_metrics(result, metrics_to_compare)

        return result

    async def _get_entity_raw_metrics(
        self, entity_type: BenchmarkEntityType, entity_id: str, time_range: TimeRange
    ) -> dict[str, float]:
        """Get raw performance metrics for an entity."""
        time_filter = self._get_time_filter(time_range)

        if entity_type == BenchmarkEntityType.PROJECT:
            # Get session IDs for this project
            session_ids = await self.db.sessions.distinct(
                "sessionId", {"projectId": ObjectId(entity_id)}
            )
            message_filter = {**time_filter, "sessionId": {"$in": session_ids}}

        elif entity_type == BenchmarkEntityType.TIME_PERIOD:
            # For time periods, entity_id is a date range identifier
            period_filter = self._get_time_period_filter(entity_id)
            message_filter = {**period_filter}

        else:  # TEAM - would need team mapping logic
            # For now, treat as project
            session_ids = await self.db.sessions.distinct(
                "sessionId", {"projectId": ObjectId(entity_id)}
            )
            message_filter = {**time_filter, "sessionId": {"$in": session_ids}}

        # Calculate KPIs
        cost_efficiency = await self._calculate_cost_efficiency(message_filter)
        speed_score = await self._calculate_speed_score(message_filter)
        quality_score = await self._calculate_quality_score(message_filter)
        productivity_score = await self._calculate_productivity_score(message_filter)
        complexity_handling = await self._calculate_complexity_handling(message_filter)

        return {
            "cost_efficiency_raw": cost_efficiency,
            "speed_score_raw": speed_score,
            "quality_score_raw": quality_score,
            "productivity_score_raw": productivity_score,
            "complexity_handling_raw": complexity_handling,
        }

    async def _calculate_cost_efficiency(self, message_filter: dict[str, Any]) -> float:
        """Calculate cost efficiency metric (lower cost per outcome is better)."""
        pipeline = [
            {"$match": {**message_filter, "costUsd": {"$exists": True, "$gt": 0}}},
            {
                "$group": {
                    "_id": None,
                    "total_cost": {"$sum": "$costUsd"},
                    "total_messages": {"$sum": 1},
                    "successful_operations": {
                        "$sum": {"$cond": [{"$ne": ["$errors", []]}, 0, 1]}
                    },
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)
        if not result:
            return 0.0

        data = result[0]
        total_cost = self._safe_float(data.get("total_cost", 0))
        if total_cost == 0:
            return 0.0

        # Cost efficiency = successful operations per dollar (higher is better)
        efficiency = data["successful_operations"] / total_cost
        return float(efficiency * 100)  # Scale to 0-100 range

    async def _calculate_speed_score(self, message_filter: dict[str, Any]) -> float:
        """Calculate speed performance score based on response times."""
        pipeline = [
            {"$match": {**message_filter, "durationMs": {"$exists": True, "$gt": 0}}},
            {
                "$group": {
                    "_id": None,
                    "avg_duration": {"$avg": "$durationMs"},
                    "count": {"$sum": 1},
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)
        if not result or result[0]["count"] == 0:
            return 50.0  # Neutral score

        avg_duration = result[0]["avg_duration"]
        # Convert to speed score (lower duration = higher score)
        # Using inverse log scale: score = 100 - log10(duration_seconds) * 20
        duration_seconds = avg_duration / 1000
        if duration_seconds <= 0:
            return 100.0

        speed_score = max(0.0, 100.0 - (math.log10(duration_seconds) * 20.0))
        return float(min(100.0, speed_score))

    async def _calculate_quality_score(self, message_filter: dict[str, Any]) -> float:
        """Calculate quality score based on error rates."""
        pipeline = [
            {"$match": message_filter},
            {
                "$group": {
                    "_id": None,
                    "total_messages": {"$sum": 1},
                    "error_messages": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$exists": ["$errors", True]},
                                        {"$ne": ["$errors", []]},
                                        {"$ne": ["$errors", None]},
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)
        if not result or result[0]["total_messages"] == 0:
            return 100.0  # Perfect score if no data

        data = result[0]
        error_rate = data["error_messages"] / data["total_messages"]
        quality_score = (1 - error_rate) * 100
        return float(max(0.0, quality_score))

    async def _calculate_productivity_score(
        self, message_filter: dict[str, Any]
    ) -> float:
        """Calculate productivity score based on tasks per session."""
        # Get session-level productivity
        session_pipeline = [
            {"$match": message_filter},
            {
                "$group": {
                    "_id": "$sessionId",
                    "message_count": {"$sum": 1},
                    "tool_calls": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$exists": ["$tools", True]},
                                        {"$ne": ["$tools", []]},
                                        {"$ne": ["$tools", None]},
                                    ]
                                },
                                {"$size": "$tools"},
                                0,
                            ]
                        }
                    },
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_messages_per_session": {"$avg": "$message_count"},
                    "avg_tools_per_session": {"$avg": "$tool_calls"},
                    "session_count": {"$sum": 1},
                }
            },
        ]

        result = await self.db.messages.aggregate(session_pipeline).to_list(1)
        if not result or result[0]["session_count"] == 0:
            return 50.0  # Neutral score

        data = result[0]
        # Productivity = weighted combination of messages and tool usage
        messages_score = min(
            100.0, data["avg_messages_per_session"] * 2.0
        )  # Scale by 2
        tools_score = min(100.0, data["avg_tools_per_session"] * 5.0)  # Scale by 5

        productivity_score = messages_score * 0.6 + tools_score * 0.4
        return float(min(100.0, productivity_score))

    async def _calculate_complexity_handling(
        self, message_filter: dict[str, Any]
    ) -> float:
        """Calculate complexity handling score based on conversation depth and branching."""
        pipeline = [
            {"$match": message_filter},
            {
                "$group": {
                    "_id": "$sessionId",
                    "message_count": {"$sum": 1},
                    "avg_depth": {"$avg": {"$ifNull": ["$conversationDepth", 1]}},
                    "has_sidechains": {
                        "$max": {"$cond": [{"$eq": ["$isSidechain", True]}, 1, 0]}
                    },
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_session_depth": {"$avg": "$avg_depth"},
                    "sidechain_percentage": {"$avg": "$has_sidechains"},
                    "avg_session_length": {"$avg": "$message_count"},
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)
        if not result:
            return 50.0  # Neutral score

        data = result[0]
        depth_score = min(100.0, data["avg_session_depth"] * 10.0)  # Scale depth
        branch_score = data["sidechain_percentage"] * 100.0  # Percentage to score
        length_score = min(100.0, data["avg_session_length"] * 3.0)  # Scale length

        complexity_score = depth_score * 0.4 + branch_score * 0.3 + length_score * 0.3
        return float(min(100.0, complexity_score))

    def _normalize_metrics(
        self, raw_metrics: list[dict[str, Any]], method: NormalizationMethod
    ) -> list[dict[str, float]]:
        """Normalize raw metrics using specified method."""
        metric_keys = [
            "cost_efficiency_raw",
            "speed_score_raw",
            "quality_score_raw",
            "productivity_score_raw",
            "complexity_handling_raw",
        ]

        # Extract values for each metric
        metric_values = {key: [m[key] for m in raw_metrics] for key in metric_keys}

        normalized_results = []

        for i in range(len(raw_metrics)):
            normalized = {}

            for key in metric_keys:
                values = metric_values[key]
                current_value = values[i]

                if method == NormalizationMethod.Z_SCORE:
                    if len(values) > 1 and statistics.stdev(values) > 0:
                        mean_val = statistics.mean(values)
                        std_val = statistics.stdev(values)
                        z_score = (current_value - mean_val) / std_val
                        # Convert z-score to 0-100 scale (z-scores typically range -3 to +3)
                        normalized_score = max(0, min(100, 50 + (z_score * 15)))
                    else:
                        normalized_score = 50.0  # Neutral if no variation

                elif method == NormalizationMethod.MIN_MAX:
                    min_val = min(values)
                    max_val = max(values)
                    if max_val > min_val:
                        normalized_score = (
                            (current_value - min_val) / (max_val - min_val)
                        ) * 100
                        # Ensure normalized score is within 0-100 range
                        normalized_score = min(max(normalized_score, 0.0), 100.0)
                    else:
                        normalized_score = 50.0  # Neutral if no variation

                elif method == NormalizationMethod.PERCENTILE_RANK:
                    sorted_values = sorted(values)
                    rank = sorted_values.index(current_value) + 1
                    normalized_score = (rank / len(values)) * 100
                    # Ensure percentile rank is within 0-100 range
                    normalized_score = min(max(normalized_score, 0.0), 100.0)

                # Map to final metric names
                final_key = key.replace("_raw", "").replace("score_raw", "score")
                normalized[final_key] = round(normalized_score, 2)

            # Calculate overall score as weighted average
            normalized["overall_score"] = round(
                (
                    normalized["cost_efficiency"] * 0.25
                    + normalized["speed_score"] * 0.20
                    + normalized["quality_score"] * 0.25
                    + normalized["productivity_score"] * 0.15
                    + normalized["complexity_handling"] * 0.15
                ),
                2,
            )

            normalized_results.append(normalized)

        return normalized_results

    def _calculate_percentile_ranks(
        self, raw_metrics: list[dict[str, Any]]
    ) -> list[dict[str, float]]:
        """Calculate percentile ranks for metrics."""
        metric_keys = [
            "cost_efficiency_raw",
            "speed_score_raw",
            "quality_score_raw",
            "productivity_score_raw",
        ]

        percentile_results = []

        for i in range(len(raw_metrics)):
            percentiles = {}

            for key in metric_keys:
                values = [m[key] for m in raw_metrics]
                current_value = values[i]

                # Calculate percentile rank
                rank = sum(1 for v in values if v <= current_value)
                percentile = (rank / len(values)) * 100

                # Map to final names
                final_key = key.replace("_raw", "").replace("score_raw", "")
                percentiles[final_key] = round(percentile, 1)

            percentile_results.append(percentiles)

        return percentile_results

    async def _get_entity_name(
        self, entity_type: BenchmarkEntityType, entity_id: str
    ) -> str:
        """Get display name for entity."""
        if entity_type == BenchmarkEntityType.PROJECT:
            project = await self.db.projects.find_one({"_id": ObjectId(entity_id)})
            return project["name"] if project else f"Project {entity_id[:8]}"
        elif entity_type == BenchmarkEntityType.TIME_PERIOD:
            return entity_id  # Time periods are passed as readable names
        else:  # TEAM
            return f"Team {entity_id}"

    def _analyze_entity_performance(
        self, metrics: dict[str, float]
    ) -> tuple[list[str], list[str]]:
        """Analyze entity performance to identify strengths and improvement areas."""
        strengths = []
        improvement_areas = []

        metric_names = {
            "cost_efficiency": "Cost Efficiency",
            "speed_score": "Response Speed",
            "quality_score": "Quality & Reliability",
            "productivity_score": "Productivity",
            "complexity_handling": "Complexity Handling",
        }

        for key, name in metric_names.items():
            score = metrics.get(key, 0)
            if score >= 75:
                strengths.append(name)
            elif score <= 40:
                improvement_areas.append(name)

        return strengths, improvement_areas

    def _create_comparison_matrix(
        self, benchmarks: list[BenchmarkEntity]
    ) -> BenchmarkComparisonMatrix:
        """Create comparison matrix for benchmarks."""
        headers = [b.entity for b in benchmarks]

        # Matrix rows: cost_efficiency, speed_score, quality_score, productivity_score, complexity_handling
        metric_keys = [
            "cost_efficiency",
            "speed_score",
            "quality_score",
            "productivity_score",
            "complexity_handling",
        ]

        data = []
        best_performers = []

        for metric_key in metric_keys:
            row = []
            best_score = -1
            best_performer = ""

            for benchmark in benchmarks:
                score = getattr(benchmark.metrics, metric_key)
                row.append(score)

                if score > best_score:
                    best_score = score
                    best_performer = benchmark.entity

            data.append(row)
            best_performers.append(best_performer)

        return BenchmarkComparisonMatrix(
            headers=headers, data=data, best_performer_per_metric=best_performers
        )

    def _generate_benchmark_insights(
        self, benchmarks: list[BenchmarkEntity], raw_metrics: list[dict[str, Any]]
    ) -> BenchmarkInsights:
        """Generate insights and recommendations from benchmark analysis."""
        # Top performers by overall score
        sorted_benchmarks = sorted(
            benchmarks, key=lambda b: b.metrics.overall_score, reverse=True
        )
        top_performers = [b.entity for b in sorted_benchmarks[:3]]

        # Biggest improvements (mock data for now - would need historical comparison)
        improvements = [
            BenchmarkImprovement(
                entity=benchmarks[0].entity,
                metric="Speed Performance",
                improvement=15.2,
                improvement_percentage=12.3,
            )
        ]

        # Generate recommendations
        recommendations = []

        # Analyze common weak areas
        weak_areas: dict[str, int] = {}
        for benchmark in benchmarks:
            for area in benchmark.improvement_areas:
                weak_areas[area] = weak_areas.get(area, 0) + 1

        if weak_areas:
            most_common_weakness = max(weak_areas.items(), key=lambda x: x[1])
            recommendations.append(
                f"Focus on improving {most_common_weakness[0]} - "
                f"{most_common_weakness[1]} entities need attention in this area"
            )

        # Performance-based recommendations
        avg_cost_efficiency = statistics.mean(
            [b.metrics.cost_efficiency for b in benchmarks]
        )
        if avg_cost_efficiency < 60:
            recommendations.append(
                "Consider optimizing cost efficiency through better prompt engineering "
                "and reducing unnecessary API calls"
            )

        avg_speed = statistics.mean([b.metrics.speed_score for b in benchmarks])
        if avg_speed < 60:
            recommendations.append(
                "Improve response times by optimizing message complexity and "
                "reducing tool usage in non-critical operations"
            )

        return BenchmarkInsights(
            top_performers=top_performers,
            biggest_improvements=improvements,
            recommendations=recommendations,
        )

    def _filter_benchmark_metrics(
        self, result: BenchmarkResponse, metrics_to_compare: list[str]
    ) -> BenchmarkResponse:
        """Filter benchmark results to specific metrics."""
        # This would filter the comparison matrix and adjust insights
        # For now, return the full result
        return result

    def _get_time_period_filter(self, period_id: str) -> dict[str, Any]:
        """Get time filter for a specific period identifier."""
        # Parse period_id to determine time range
        # Format could be "2024-01" for January 2024, "2024-Q1" for Q1, etc.
        # For now, return a basic filter
        return self._get_time_filter(TimeRange.LAST_30_DAYS)
