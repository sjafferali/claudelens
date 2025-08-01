# Task 12: Backend Analytics API Implementation

## Status
**Status:** TODO  
**Priority:** Medium  
**Estimated Time:** 3 hours

## Purpose
Implement analytics endpoints that provide insights into Claude usage patterns, costs, activity trends, and model performance. These endpoints power the frontend's dashboard and visualization features.

## Current State
- Database has message/session data
- No analytics endpoints
- No aggregation queries for insights

## Target State
- Activity heatmap data endpoint
- Cost analytics by time period
- Model usage statistics
- Token usage tracking
- Response time analysis
- Project comparison metrics

## Implementation Details

### 1. Analytics Router

**`backend/app/api/api_v1/endpoints/analytics.py`:**
```python
"""Analytics API endpoints."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import CommonDeps
from app.schemas.analytics import (
    ActivityHeatmap,
    CostAnalytics,
    ModelUsageStats,
    TokenUsageStats,
    TimeRange,
    AnalyticsSummary
)
from app.services.analytics import AnalyticsService

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    db: CommonDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS)
) -> AnalyticsSummary:
    """Get overall analytics summary.
    
    Returns high-level metrics including total messages, costs,
    active projects, and usage trends.
    """
    service = AnalyticsService(db)
    summary = await service.get_summary(time_range)
    return summary


@router.get("/activity/heatmap", response_model=ActivityHeatmap)
async def get_activity_heatmap(
    db: CommonDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    timezone: str = Query("UTC", description="Timezone for aggregation")
) -> ActivityHeatmap:
    """Get activity heatmap data.
    
    Returns message counts aggregated by hour and day of week,
    useful for visualizing usage patterns.
    """
    service = AnalyticsService(db)
    heatmap = await service.get_activity_heatmap(time_range, timezone)
    return heatmap


@router.get("/costs", response_model=CostAnalytics)
async def get_cost_analytics(
    db: CommonDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    group_by: str = Query("day", regex="^(hour|day|week|month)$"),
    project_id: Optional[str] = Query(None)
) -> CostAnalytics:
    """Get cost analytics over time.
    
    Returns cost data grouped by the specified time period,
    optionally filtered by project.
    """
    service = AnalyticsService(db)
    costs = await service.get_cost_analytics(
        time_range,
        group_by,
        project_id
    )
    return costs


@router.get("/models/usage", response_model=ModelUsageStats)
async def get_model_usage(
    db: CommonDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    project_id: Optional[str] = Query(None)
) -> ModelUsageStats:
    """Get model usage statistics.
    
    Returns usage data for each Claude model including message counts,
    costs, and average response times.
    """
    service = AnalyticsService(db)
    usage = await service.get_model_usage(time_range, project_id)
    return usage


@router.get("/tokens", response_model=TokenUsageStats)
async def get_token_usage(
    db: CommonDeps,
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS),
    group_by: str = Query("day", regex="^(hour|day|week|month)$")
) -> TokenUsageStats:
    """Get token usage statistics.
    
    Returns input and output token counts over time.
    """
    service = AnalyticsService(db)
    tokens = await service.get_token_usage(time_range, group_by)
    return tokens


@router.get("/projects/comparison")
async def compare_projects(
    db: CommonDeps,
    project_ids: List[str] = Query(..., description="Project IDs to compare"),
    time_range: TimeRange = Query(TimeRange.LAST_30_DAYS)
) -> Dict[str, Any]:
    """Compare analytics across multiple projects.
    
    Returns comparative metrics for the specified projects.
    """
    if len(project_ids) < 2 or len(project_ids) > 10:
        raise HTTPException(
            status_code=400,
            detail="Please provide between 2 and 10 project IDs"
        )
    
    service = AnalyticsService(db)
    comparison = await service.compare_projects(project_ids, time_range)
    return comparison


@router.get("/trends")
async def get_usage_trends(
    db: CommonDeps,
    time_range: TimeRange = Query(TimeRange.LAST_90_DAYS),
    metric: str = Query("messages", regex="^(messages|costs|sessions|response_time)$")
) -> Dict[str, Any]:
    """Get usage trends over time.
    
    Analyzes trends and provides insights on usage patterns.
    """
    service = AnalyticsService(db)
    trends = await service.analyze_trends(time_range, metric)
    return trends
```

### 2. Analytics Schemas

**`backend/app/schemas/analytics.py`:**
```python
"""Analytics schemas."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TimeRange(str, Enum):
    """Predefined time ranges for analytics."""
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    LAST_YEAR = "1y"
    ALL_TIME = "all"


class AnalyticsSummary(BaseModel):
    """Overall analytics summary."""
    total_messages: int
    total_sessions: int
    total_projects: int
    total_cost: float
    
    messages_trend: float = Field(..., description="Percentage change from previous period")
    cost_trend: float = Field(..., description="Percentage change from previous period")
    
    most_active_project: Optional[str] = None
    most_used_model: Optional[str] = None
    
    time_range: TimeRange
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class HeatmapCell(BaseModel):
    """Single cell in activity heatmap."""
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    hour: int = Field(..., ge=0, le=23)
    count: int = Field(..., ge=0)
    
    # Optional enrichment
    avg_cost: Optional[float] = None
    avg_response_time: Optional[float] = None


class ActivityHeatmap(BaseModel):
    """Activity heatmap data."""
    cells: List[HeatmapCell]
    total_messages: int
    time_range: TimeRange
    timezone: str
    
    # Peak activity times
    peak_hour: Optional[int] = None
    peak_day: Optional[int] = None


class CostDataPoint(BaseModel):
    """Cost data point in time series."""
    timestamp: datetime
    cost: float
    message_count: int
    
    # Breakdown by model
    cost_by_model: Optional[Dict[str, float]] = None


class CostAnalytics(BaseModel):
    """Cost analytics over time."""
    data_points: List[CostDataPoint]
    total_cost: float
    average_cost_per_message: float
    
    time_range: TimeRange
    group_by: str
    
    # Cost breakdown
    cost_by_model: Dict[str, float]
    cost_by_project: Optional[Dict[str, float]] = None


class ModelUsage(BaseModel):
    """Usage statistics for a single model."""
    model: str
    message_count: int
    total_cost: float
    avg_cost_per_message: float
    
    avg_response_time_ms: Optional[float] = None
    avg_tokens_input: Optional[float] = None
    avg_tokens_output: Optional[float] = None
    
    # Usage trend
    trend_percentage: Optional[float] = None


class ModelUsageStats(BaseModel):
    """Model usage statistics."""
    models: List[ModelUsage]
    total_models: int
    time_range: TimeRange
    
    # Most/least used
    most_used: Optional[str] = None
    least_used: Optional[str] = None


class TokenDataPoint(BaseModel):
    """Token usage data point."""
    timestamp: datetime
    input_tokens: int
    output_tokens: int
    total_tokens: int


class TokenUsageStats(BaseModel):
    """Token usage statistics."""
    data_points: List[TokenDataPoint]
    total_input_tokens: int
    total_output_tokens: int
    
    avg_input_tokens_per_message: float
    avg_output_tokens_per_message: float
    
    time_range: TimeRange
    group_by: str
```

### 3. Analytics Service Implementation

**`backend/app/services/analytics.py`:**
```python
"""Analytics service implementation."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import pytz

from app.schemas.analytics import (
    TimeRange,
    AnalyticsSummary,
    ActivityHeatmap,
    HeatmapCell,
    CostAnalytics,
    CostDataPoint,
    ModelUsageStats,
    ModelUsage,
    TokenUsageStats,
    TokenDataPoint
)


class AnalyticsService:
    """Service for analytics operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    def _get_time_filter(self, time_range: TimeRange) -> Dict[str, Any]:
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
                current_stats["total_messages"],
                prev_stats["total_messages"]
            )
            cost_trend = self._calculate_trend(
                current_stats["total_cost"],
                prev_stats["total_cost"]
            )
        else:
            messages_trend = 0
            cost_trend = 0
        
        # Get most active project
        project_pipeline = [
            {"$match": time_filter},
            {"$lookup": {
                "from": "sessions",
                "localField": "sessionId",
                "foreignField": "sessionId",
                "as": "session"
            }},
            {"$unwind": "$session"},
            {"$group": {
                "_id": "$session.projectId",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 1},
            {"$lookup": {
                "from": "projects",
                "localField": "_id",
                "foreignField": "_id",
                "as": "project"
            }},
            {"$unwind": "$project"}
        ]
        
        project_result = await self.db.messages.aggregate(project_pipeline).to_list(1)
        most_active_project = project_result[0]["project"]["name"] if project_result else None
        
        # Get most used model
        model_pipeline = [
            {"$match": {**time_filter, "model": {"$exists": True}}},
            {"$group": {
                "_id": "$model",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 1}
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
            time_range=time_range
        )
    
    async def get_activity_heatmap(
        self,
        time_range: TimeRange,
        timezone: str = "UTC"
    ) -> ActivityHeatmap:
        """Get activity heatmap data."""
        time_filter = self._get_time_filter(time_range)
        
        # Aggregation pipeline for heatmap
        pipeline = [
            {"$match": time_filter},
            {"$project": {
                "hour": {"$hour": {"date": "$timestamp", "timezone": timezone}},
                "dayOfWeek": {"$subtract": [
                    {"$dayOfWeek": {"date": "$timestamp", "timezone": timezone}},
                    1
                ]},  # Convert to 0-6 (Mon-Sun)
                "costUsd": 1,
                "durationMs": 1
            }},
            {"$group": {
                "_id": {
                    "hour": "$hour",
                    "dayOfWeek": "$dayOfWeek"
                },
                "count": {"$sum": 1},
                "avgCost": {"$avg": "$costUsd"},
                "avgResponseTime": {"$avg": "$durationMs"}
            }}
        ]
        
        results = await self.db.messages.aggregate(pipeline).to_list(None)
        
        # Convert to heatmap cells
        cells = []
        hour_counts = {}
        day_counts = {}
        
        for result in results:
            hour = result["_id"]["hour"]
            day = result["_id"]["dayOfWeek"]
            count = result["count"]
            
            # Track for peak calculations
            hour_counts[hour] = hour_counts.get(hour, 0) + count
            day_counts[day] = day_counts.get(day, 0) + count
            
            cells.append(HeatmapCell(
                day_of_week=day,
                hour=hour,
                count=count,
                avg_cost=round(result["avgCost"], 4) if result["avgCost"] else None,
                avg_response_time=result["avgResponseTime"]
            ))
        
        # Find peak times
        peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None
        peak_day = max(day_counts, key=day_counts.get) if day_counts else None
        
        total_messages = sum(cell.count for cell in cells)
        
        return ActivityHeatmap(
            cells=cells,
            total_messages=total_messages,
            time_range=time_range,
            timezone=timezone,
            peak_hour=peak_hour,
            peak_day=peak_day
        )
    
    async def get_cost_analytics(
        self,
        time_range: TimeRange,
        group_by: str,
        project_id: Optional[str] = None
    ) -> CostAnalytics:
        """Get cost analytics over time."""
        time_filter = self._get_time_filter(time_range)
        
        # Add project filter if specified
        if project_id:
            session_ids = await self.db.sessions.distinct(
                "sessionId",
                {"projectId": ObjectId(project_id)}
            )
            time_filter["sessionId"] = {"$in": session_ids}
        
        # Determine date grouping
        date_format = self._get_date_format(group_by)
        
        # Aggregation pipeline
        pipeline = [
            {"$match": {**time_filter, "costUsd": {"$exists": True}}},
            {"$group": {
                "_id": {
                    "date": {"$dateToString": {
                        "format": date_format,
                        "date": "$timestamp"
                    }},
                    "model": "$model"
                },
                "cost": {"$sum": "$costUsd"},
                "count": {"$sum": 1}
            }},
            {"$group": {
                "_id": "$_id.date",
                "totalCost": {"$sum": "$cost"},
                "messageCount": {"$sum": "$count"},
                "costByModel": {
                    "$push": {
                        "model": "$_id.model",
                        "cost": "$cost"
                    }
                }
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = await self.db.messages.aggregate(pipeline).to_list(None)
        
        # Process results
        data_points = []
        total_cost = 0
        total_messages = 0
        cost_by_model_global = {}
        
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
            
            data_points.append(CostDataPoint(
                timestamp=timestamp,
                cost=round(result["totalCost"], 4),
                message_count=result["messageCount"],
                cost_by_model=cost_by_model
            ))
            
            total_cost += result["totalCost"]
            total_messages += result["messageCount"]
        
        avg_cost = total_cost / total_messages if total_messages > 0 else 0
        
        return CostAnalytics(
            data_points=data_points,
            total_cost=round(total_cost, 2),
            average_cost_per_message=round(avg_cost, 4),
            time_range=time_range,
            group_by=group_by,
            cost_by_model={k: round(v, 2) for k, v in cost_by_model_global.items()}
        )
    
    def _get_date_format(self, group_by: str) -> str:
        """Get MongoDB date format string."""
        formats = {
            "hour": "%Y-%m-%dT%H:00:00",
            "day": "%Y-%m-%d",
            "week": "%Y-W%V",
            "month": "%Y-%m"
        }
        return formats.get(group_by, "%Y-%m-%d")
    
    def _calculate_trend(self, current: float, previous: float) -> float:
        """Calculate percentage change."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)
    
    async def _get_period_stats(self, time_filter: Dict[str, Any]) -> Dict[str, Any]:
        """Get basic stats for a time period."""
        # Message count
        message_count = await self.db.messages.count_documents(time_filter)
        
        # Session count
        session_ids = await self.db.messages.distinct("sessionId", time_filter)
        session_count = len(session_ids)
        
        # Project count
        project_pipeline = [
            {"$match": time_filter},
            {"$lookup": {
                "from": "sessions",
                "localField": "sessionId",
                "foreignField": "sessionId",
                "as": "session"
            }},
            {"$unwind": "$session"},
            {"$group": {"_id": "$session.projectId"}}
        ]
        
        project_result = await self.db.messages.aggregate(project_pipeline).to_list(None)
        project_count = len(project_result)
        
        # Total cost
        cost_pipeline = [
            {"$match": time_filter},
            {"$group": {
                "_id": None,
                "totalCost": {"$sum": "$costUsd"}
            }}
        ]
        
        cost_result = await self.db.messages.aggregate(cost_pipeline).to_list(1)
        total_cost = cost_result[0]["totalCost"] if cost_result else 0
        
        return {
            "total_messages": message_count,
            "total_sessions": session_count,
            "total_projects": project_count,
            "total_cost": total_cost or 0
        }
    
    def _get_previous_period_filter(self, time_range: TimeRange) -> Dict[str, Any]:
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
```

## Required Technologies
- MongoDB aggregation framework
- Time series data processing
- Statistical calculations
- Timezone handling with pytz

## Success Criteria
- [ ] Summary endpoint provides key metrics
- [ ] Activity heatmap shows usage patterns
- [ ] Cost analytics tracks spending over time
- [ ] Model usage statistics accurate
- [ ] Token usage tracking implemented
- [ ] Project comparison working
- [ ] Trend analysis functional
- [ ] Performance optimized for large datasets
- [ ] All calculations accurate

## Notes
- Use aggregation pipelines for efficiency
- Cache results for expensive queries
- Consider pre-aggregating common metrics
- Handle timezones properly for global users
- Ensure cost calculations are precise