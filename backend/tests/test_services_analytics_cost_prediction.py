"""Comprehensive tests for analytics service cost prediction functions."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from app.schemas.analytics import (
    CostBreakdownResponse,
    CostPrediction,
    CostPredictionPoint,
    CostSummary,
    TimeRange,
)
from app.services.analytics import AnalyticsService


class TestAnalyticsServiceCostPrediction:
    """Test analytics service cost prediction functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        return db

    @pytest.fixture
    def analytics_service(self, mock_db):
        """Create analytics service with mock database."""
        return AnalyticsService(mock_db)

    @pytest.fixture
    def sample_cost_data(self):
        """Sample cost aggregation results."""
        return [
            {"_id": None, "total_cost": 15.75},
            {"_id": "claude-3-5-sonnet-20241022", "cost": 10.50, "message_count": 25},
            {"_id": "claude-3-opus-20240229", "cost": 5.25, "message_count": 12},
        ]

    @pytest.fixture
    def sample_daily_costs(self):
        """Sample daily cost data for time series."""
        base_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        return [
            {"_id": (base_date - timedelta(days=7)).strftime("%Y-%m-%d"), "cost": 2.15},
            {"_id": (base_date - timedelta(days=6)).strftime("%Y-%m-%d"), "cost": 3.42},
            {"_id": (base_date - timedelta(days=5)).strftime("%Y-%m-%d"), "cost": 1.87},
            {"_id": (base_date - timedelta(days=4)).strftime("%Y-%m-%d"), "cost": 4.23},
            {"_id": (base_date - timedelta(days=3)).strftime("%Y-%m-%d"), "cost": 2.94},
            {"_id": (base_date - timedelta(days=2)).strftime("%Y-%m-%d"), "cost": 3.67},
            {"_id": (base_date - timedelta(days=1)).strftime("%Y-%m-%d"), "cost": 2.58},
        ]

    @pytest.fixture
    def empty_cost_data(self):
        """Empty cost aggregation results."""
        return []

    # Test get_cost_summary

    @pytest.mark.asyncio
    async def test_get_cost_summary_basic(self, analytics_service, sample_cost_data):
        """Test basic functionality of get_cost_summary."""
        # Mock the database aggregation for current and previous periods
        current_cost = [{"_id": None, "total_cost": 15.75}]
        previous_cost = [{"_id": None, "total_cost": 15.0}]  # Small change, within 5%

        mock_cursor_current = AsyncMock()
        mock_cursor_current.to_list = AsyncMock(return_value=current_cost)

        mock_cursor_previous = AsyncMock()
        mock_cursor_previous.to_list = AsyncMock(return_value=previous_cost)

        # Mock aggregation to return different results for current vs previous period
        analytics_service.db.messages.aggregate.side_effect = [
            mock_cursor_current,
            mock_cursor_previous,
        ]

        # Call the method
        result = await analytics_service.get_cost_summary(
            None, None, TimeRange.LAST_30_DAYS
        )

        # Verify result
        assert isinstance(result, CostSummary)
        assert result.total_cost == 15.75
        assert result.formatted_cost == "$15.75"
        assert result.currency == "USD"
        assert result.trend == "stable"  # Change is 5%, which is stable
        assert result.period == "30d"

        # Verify database was called twice (current + previous period)
        assert analytics_service.db.messages.aggregate.call_count == 2

    @pytest.mark.asyncio
    async def test_get_cost_summary_with_trend_up(self, analytics_service):
        """Test get_cost_summary with upward trend."""
        current_cost = [{"_id": None, "total_cost": 100.0}]
        previous_cost = [{"_id": None, "total_cost": 80.0}]  # 25% increase

        mock_cursor_current = AsyncMock()
        mock_cursor_current.to_list = AsyncMock(return_value=current_cost)

        mock_cursor_previous = AsyncMock()
        mock_cursor_previous.to_list = AsyncMock(return_value=previous_cost)

        # Mock aggregation to return different results for current vs previous period
        analytics_service.db.messages.aggregate.side_effect = [
            mock_cursor_current,
            mock_cursor_previous,
        ]

        result = await analytics_service.get_cost_summary(
            None, None, TimeRange.LAST_7_DAYS
        )

        assert result.total_cost == 100.0
        assert result.trend == "up"  # >5% increase

    @pytest.mark.asyncio
    async def test_get_cost_summary_with_trend_down(self, analytics_service):
        """Test get_cost_summary with downward trend."""
        current_cost = [{"_id": None, "total_cost": 70.0}]
        previous_cost = [{"_id": None, "total_cost": 100.0}]  # 30% decrease

        mock_cursor_current = AsyncMock()
        mock_cursor_current.to_list = AsyncMock(return_value=current_cost)

        mock_cursor_previous = AsyncMock()
        mock_cursor_previous.to_list = AsyncMock(return_value=previous_cost)

        analytics_service.db.messages.aggregate.side_effect = [
            mock_cursor_current,
            mock_cursor_previous,
        ]

        result = await analytics_service.get_cost_summary(
            None, None, TimeRange.LAST_7_DAYS
        )

        assert result.total_cost == 70.0
        assert result.trend == "down"  # >5% decrease

    @pytest.mark.asyncio
    async def test_get_cost_summary_with_session_id(self, analytics_service):
        """Test get_cost_summary with session filter."""
        test_session_id = "test-session-123"

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(
            return_value=[{"_id": None, "total_cost": 5.25}]
        )
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_cost_summary(
            test_session_id, None, TimeRange.LAST_24_HOURS
        )

        assert result.total_cost == 5.25
        assert result.period == "24h"

        # Verify session filter was applied
        call_args = analytics_service.db.messages.aggregate.call_args[0][0]
        match_stage = call_args[0]
        assert match_stage["$match"]["sessionId"] == test_session_id

    @pytest.mark.asyncio
    async def test_get_cost_summary_with_project_id(self, analytics_service):
        """Test get_cost_summary with project filter."""
        test_project_id = str(ObjectId())
        test_session_ids = ["session1", "session2", "session3"]

        # Mock sessions.distinct call
        analytics_service.db.sessions.distinct = AsyncMock(
            return_value=test_session_ids
        )

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(
            return_value=[{"_id": None, "total_cost": 12.34}]
        )
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_cost_summary(
            None, test_project_id, TimeRange.LAST_90_DAYS
        )

        # Verify sessions.distinct was called
        analytics_service.db.sessions.distinct.assert_called_once_with(
            "sessionId", {"projectId": ObjectId(test_project_id)}
        )

        assert result.total_cost == 12.34
        assert result.period == "90d"

    @pytest.mark.asyncio
    async def test_get_cost_summary_zero_cost(self, analytics_service, empty_cost_data):
        """Test get_cost_summary with zero cost."""
        mock_cursor_current = AsyncMock()
        mock_cursor_current.to_list = AsyncMock(return_value=empty_cost_data)

        mock_cursor_previous = AsyncMock()
        mock_cursor_previous.to_list = AsyncMock(return_value=empty_cost_data)

        analytics_service.db.messages.aggregate.side_effect = [
            mock_cursor_current,
            mock_cursor_previous,
        ]

        result = await analytics_service.get_cost_summary(
            None, None, TimeRange.LAST_30_DAYS
        )

        assert result.total_cost == 0.0
        assert result.formatted_cost == "$0.00"  # Zero cost formats as $0.00
        assert result.trend == "stable"

    @pytest.mark.asyncio
    async def test_get_cost_summary_all_time_no_trend(self, analytics_service):
        """Test get_cost_summary with ALL_TIME (no trend calculation)."""
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(
            return_value=[{"_id": None, "total_cost": 50.0}]
        )
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_cost_summary(
            None, None, TimeRange.ALL_TIME
        )

        assert result.total_cost == 50.0
        assert result.period == "all time"
        assert result.trend == "stable"  # No trend calculation for ALL_TIME

        # Should only call aggregate once (no previous period query)
        analytics_service.db.messages.aggregate.assert_called_once()

    # Test get_cost_breakdown

    @pytest.mark.asyncio
    async def test_get_cost_breakdown_basic(
        self, analytics_service, sample_daily_costs
    ):
        """Test basic functionality of get_cost_breakdown."""
        model_breakdown = [
            {"_id": "claude-3-5-sonnet-20241022", "cost": 10.50, "message_count": 25},
            {"_id": "claude-3-opus-20240229", "cost": 5.25, "message_count": 12},
        ]

        # Mock multiple aggregation calls
        mock_cursor_model = AsyncMock()
        mock_cursor_model.to_list = AsyncMock(return_value=model_breakdown)

        mock_cursor_daily = AsyncMock()
        mock_cursor_daily.to_list = AsyncMock(return_value=sample_daily_costs)

        # Mock count_documents for message count
        analytics_service.db.messages.count_documents = AsyncMock(return_value=37)

        analytics_service.db.messages.aggregate.side_effect = [
            mock_cursor_model,
            mock_cursor_daily,
        ]

        result = await analytics_service.get_cost_breakdown(
            None, None, TimeRange.LAST_7_DAYS
        )

        # Verify result structure
        assert isinstance(result, CostBreakdownResponse)
        assert result.time_range == TimeRange.LAST_7_DAYS
        assert result.session_id is None
        assert result.project_id is None

        # Verify cost breakdown
        assert len(result.cost_breakdown.by_model) == 2
        assert result.cost_breakdown.by_model[0].model == "claude-3-5-sonnet-20241022"
        assert result.cost_breakdown.by_model[0].cost == 10.50
        assert result.cost_breakdown.by_model[0].message_count == 25
        assert (
            result.cost_breakdown.by_model[0].percentage == 66.67
        )  # 10.50/15.75 * 100

        assert result.cost_breakdown.by_model[1].model == "claude-3-opus-20240229"
        assert result.cost_breakdown.by_model[1].cost == 5.25
        assert result.cost_breakdown.by_model[1].percentage == 33.33  # 5.25/15.75 * 100

        # Verify time series data
        assert len(result.cost_breakdown.by_time) == 7
        assert result.cost_breakdown.by_time[0].cost == 2.15
        assert result.cost_breakdown.by_time[-1].cost == 2.58

        # Verify cumulative costs are increasing
        cumulative_costs = [point.cumulative for point in result.cost_breakdown.by_time]
        assert all(
            cumulative_costs[i] >= cumulative_costs[i - 1]
            for i in range(1, len(cumulative_costs))
        )

        # Verify metrics
        assert result.cost_metrics.avg_cost_per_message == round(15.75 / 37, 4)
        assert result.cost_metrics.avg_cost_per_hour == round(
            15.75 / 168, 4
        )  # 7 days = 168 hours
        assert result.cost_metrics.most_expensive_model == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_get_cost_breakdown_session_not_found(self, analytics_service):
        """Test get_cost_breakdown when session is not found."""
        test_session_id = "nonexistent-session"
        analytics_service._resolve_session_id = AsyncMock(return_value=None)

        result = await analytics_service.get_cost_breakdown(
            test_session_id, None, TimeRange.LAST_30_DAYS
        )

        # Verify session resolution was called
        analytics_service._resolve_session_id.assert_called_once_with(test_session_id)

        # Verify empty result is returned
        assert isinstance(result, CostBreakdownResponse)
        assert result.cost_breakdown.by_model == []
        assert result.cost_breakdown.by_time == []
        assert result.cost_metrics.avg_cost_per_message == 0.0
        assert result.cost_metrics.avg_cost_per_hour == 0.0
        assert result.cost_metrics.most_expensive_model is None
        assert result.session_id == test_session_id

        # Verify database aggregation was not called
        analytics_service.db.messages.aggregate.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_cost_breakdown_empty_data(
        self, analytics_service, empty_cost_data
    ):
        """Test get_cost_breakdown with empty data."""
        # Mock empty aggregation results
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=empty_cost_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor
        analytics_service.db.messages.count_documents = AsyncMock(return_value=0)

        result = await analytics_service.get_cost_breakdown(
            None, None, TimeRange.LAST_30_DAYS
        )

        assert result.cost_breakdown.by_model == []
        assert result.cost_breakdown.by_time == []
        assert result.cost_metrics.avg_cost_per_message == 0.0
        assert result.cost_metrics.most_expensive_model is None

    @pytest.mark.asyncio
    async def test_get_cost_breakdown_with_invalid_date(self, analytics_service):
        """Test get_cost_breakdown handles invalid date formats gracefully."""
        model_breakdown = [
            {"_id": "claude-3-5-sonnet-20241022", "cost": 10.0, "message_count": 20},
        ]

        daily_costs_with_invalid = [
            {"_id": "2024-01-15", "cost": 5.0},  # Valid date
            {"_id": "invalid-date", "cost": 3.0},  # Invalid date
            {"_id": "2024-01-16", "cost": 7.0},  # Valid date
        ]

        mock_cursor_model = AsyncMock()
        mock_cursor_model.to_list = AsyncMock(return_value=model_breakdown)

        mock_cursor_daily = AsyncMock()
        mock_cursor_daily.to_list = AsyncMock(return_value=daily_costs_with_invalid)

        analytics_service.db.messages.count_documents = AsyncMock(return_value=20)
        analytics_service.db.messages.aggregate.side_effect = [
            mock_cursor_model,
            mock_cursor_daily,
        ]

        result = await analytics_service.get_cost_breakdown(
            None, None, TimeRange.LAST_7_DAYS
        )

        # Should only include valid dates (skip the invalid one)
        assert len(result.cost_breakdown.by_time) == 2
        assert all(
            isinstance(point.timestamp, datetime)
            for point in result.cost_breakdown.by_time
        )

    # Test get_cost_prediction

    @pytest.mark.asyncio
    async def test_get_cost_prediction_basic(
        self, analytics_service, sample_daily_costs
    ):
        """Test basic functionality of get_cost_prediction."""
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_daily_costs)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_cost_prediction(None, None, 7)

        # Verify result structure
        assert isinstance(result, CostPrediction)
        assert len(result.predictions) == 7
        assert result.prediction_days == 7
        assert result.confidence_level == 0.95
        assert result.model_accuracy == 75.0
        assert result.session_id is None
        assert result.project_id is None

        # Verify predictions have reasonable values
        for prediction in result.predictions:
            assert isinstance(prediction, CostPredictionPoint)
            assert prediction.predicted_cost >= 0
            assert len(prediction.confidence_interval) == 2
            assert prediction.confidence_interval[0] >= 0  # Lower bound >= 0
            assert (
                prediction.confidence_interval[1] >= prediction.confidence_interval[0]
            )  # Upper >= Lower
            assert isinstance(prediction.date, datetime)

        # Verify predictions are in chronological order
        dates = [p.date for p in result.predictions]
        assert dates == sorted(dates)

        # Verify total predicted cost
        expected_total = sum(p.predicted_cost for p in result.predictions)
        assert result.total_predicted == round(expected_total, 4)

    @pytest.mark.asyncio
    async def test_get_cost_prediction_no_historical_data(self, analytics_service):
        """Test get_cost_prediction with no historical data."""
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_cost_prediction(None, None, 14)

        # Verify zero predictions when no historical data
        assert len(result.predictions) == 14
        assert result.total_predicted == 0.0
        assert result.model_accuracy == 0.0

        # Verify all predictions are zero
        for prediction in result.predictions:
            assert prediction.predicted_cost == 0.0
            assert prediction.confidence_interval == (0.0, 0.0)

    @pytest.mark.asyncio
    async def test_get_cost_prediction_with_session_id(
        self, analytics_service, sample_daily_costs
    ):
        """Test get_cost_prediction with session filter."""
        test_session_id = "test-session-456"

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_daily_costs)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_cost_prediction(test_session_id, None, 5)

        assert result.session_id == test_session_id
        assert len(result.predictions) == 5

        # Verify session filter was applied
        call_args = analytics_service.db.messages.aggregate.call_args[0][0]
        match_stage = call_args[0]
        assert match_stage["$match"]["sessionId"] == test_session_id

    @pytest.mark.asyncio
    async def test_get_cost_prediction_with_project_id(
        self, analytics_service, sample_daily_costs
    ):
        """Test get_cost_prediction with project filter."""
        test_project_id = str(ObjectId())
        test_session_ids = ["session1", "session2"]

        # Mock sessions.distinct call
        analytics_service.db.sessions.distinct = AsyncMock(
            return_value=test_session_ids
        )

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_daily_costs)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_cost_prediction(None, test_project_id, 10)

        # Verify sessions.distinct was called
        analytics_service.db.sessions.distinct.assert_called_once_with(
            "sessionId", {"projectId": ObjectId(test_project_id)}
        )

        assert result.project_id == test_project_id
        assert len(result.predictions) == 10

    @pytest.mark.asyncio
    async def test_get_cost_prediction_single_data_point(self, analytics_service):
        """Test get_cost_prediction with only one day of data."""
        single_day_data = [
            {"_id": "2024-01-15", "cost": 5.0},
        ]

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=single_day_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_cost_prediction(None, None, 3)

        # Should still generate predictions based on single data point
        assert len(result.predictions) == 3
        assert all(p.predicted_cost > 0 for p in result.predictions)

        # With single data point, should use 20% uncertainty
        for prediction in result.predictions:
            predicted = prediction.predicted_cost
            lower, upper = prediction.confidence_interval
            # Should have reasonable confidence interval
            assert upper > predicted > lower >= 0

    @pytest.mark.asyncio
    async def test_get_cost_prediction_decay_factor(
        self, analytics_service, sample_daily_costs
    ):
        """Test that cost prediction applies decay factor for longer periods."""
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_daily_costs)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_cost_prediction(None, None, 30)

        # Verify predictions decrease over time due to decay factor
        predictions = result.predictions

        # Check that predictions in later weeks are generally lower
        # (due to 0.95 decay factor applied every 7 days)
        week1_avg = sum(p.predicted_cost for p in predictions[:7]) / 7
        week4_avg = sum(p.predicted_cost for p in predictions[21:28]) / 7

        assert week4_avg < week1_avg, "Later predictions should be lower due to decay"

    @pytest.mark.asyncio
    async def test_get_cost_prediction_confidence_intervals(self, analytics_service):
        """Test confidence interval calculations in cost prediction."""
        # Use consistent data to verify confidence interval calculations
        consistent_data = [
            {"_id": f"2024-01-{i:02d}", "cost": 10.0} for i in range(1, 8)
        ]

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=consistent_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_cost_prediction(None, None, 5)

        # With consistent data, standard deviation should be 0
        # So confidence intervals should be tight around the predicted value
        for prediction in result.predictions:
            predicted = prediction.predicted_cost
            lower, upper = prediction.confidence_interval

            # Should be approximately equal (small margin due to decay factor)
            assert abs(predicted - 10.0) < 1.0  # Close to average
            assert lower >= 0
            assert upper >= predicted >= lower

    @pytest.mark.asyncio
    async def test_get_cost_prediction_high_variance_data(self, analytics_service):
        """Test cost prediction with high variance historical data."""
        high_variance_data = [
            {"_id": "2024-01-15", "cost": 1.0},
            {"_id": "2024-01-16", "cost": 20.0},
            {"_id": "2024-01-17", "cost": 2.0},
            {"_id": "2024-01-18", "cost": 18.0},
            {"_id": "2024-01-19", "cost": 3.0},
        ]

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=high_variance_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_cost_prediction(None, None, 3)

        # With high variance, confidence intervals should be wider
        for prediction in result.predictions:
            lower, upper = prediction.confidence_interval
            interval_width = upper - lower

            # Wider confidence intervals due to high variance
            assert interval_width > 5.0  # Expect significant uncertainty

    # Test error handling

    @pytest.mark.asyncio
    async def test_cost_functions_database_error(self, analytics_service):
        """Test error handling when database operations fail."""
        # Mock database aggregation to raise an exception
        analytics_service.db.messages.aggregate.side_effect = Exception(
            "Database connection error"
        )

        # Test that exceptions are propagated for all cost functions
        with pytest.raises(Exception, match="Database connection error"):
            await analytics_service.get_cost_summary(None, None, TimeRange.LAST_30_DAYS)

        with pytest.raises(Exception, match="Database connection error"):
            await analytics_service.get_cost_breakdown(
                None, None, TimeRange.LAST_30_DAYS
            )

        with pytest.raises(Exception, match="Database connection error"):
            await analytics_service.get_cost_prediction(None, None, 7)

    @pytest.mark.asyncio
    async def test_cost_functions_with_session_and_project_conflict(
        self, analytics_service
    ):
        """Test cost functions when session is specified but not in project."""
        test_session_id = "session-not-in-project"
        test_project_id = str(ObjectId())

        # Mock sessions.distinct to return sessions that don't include test_session_id
        analytics_service.db.sessions.distinct = AsyncMock(
            return_value=["other-session-1", "other-session-2"]
        )

        # For get_cost_summary - should use project sessions instead of session filter
        mock_cursor_current = AsyncMock()
        mock_cursor_current.to_list = AsyncMock(return_value=[])

        mock_cursor_previous = AsyncMock()
        mock_cursor_previous.to_list = AsyncMock(return_value=[])

        analytics_service.db.messages.aggregate.side_effect = [
            mock_cursor_current,
            mock_cursor_previous,
        ]

        result = await analytics_service.get_cost_summary(
            test_session_id, test_project_id, TimeRange.LAST_7_DAYS
        )

        # Should return zero cost since session is not in project
        assert result.total_cost == 0.0

        # Verify the filter was set to exclude all results since session not in project
        call_args = analytics_service.db.messages.aggregate.call_args_list[0][0][0]
        match_stage = call_args[0]
        assert match_stage["$match"]["sessionId"] == {"$in": []}

    # Test edge cases

    @pytest.mark.asyncio
    async def test_cost_summary_very_small_costs(self, analytics_service):
        """Test cost summary formatting with very small costs."""
        # Test with very small cost
        mock_cursor_current = AsyncMock()
        mock_cursor_current.to_list = AsyncMock(
            return_value=[{"_id": None, "total_cost": 0.0001}]
        )

        mock_cursor_previous = AsyncMock()
        mock_cursor_previous.to_list = AsyncMock(return_value=[])

        analytics_service.db.messages.aggregate.side_effect = [
            mock_cursor_current,
            mock_cursor_previous,
        ]

        result = await analytics_service.get_cost_summary(
            None, None, TimeRange.LAST_24_HOURS
        )

        assert result.total_cost == 0.0001
        assert result.formatted_cost == "<$0.01"  # Very small amounts format as <$0.01

    @pytest.mark.asyncio
    async def test_cost_breakdown_zero_message_count(self, analytics_service):
        """Test cost breakdown when message count is zero."""
        model_breakdown = [
            {"_id": "claude-3-5-sonnet-20241022", "cost": 5.0, "message_count": 5},
        ]

        mock_cursor_model = AsyncMock()
        mock_cursor_model.to_list = AsyncMock(return_value=model_breakdown)

        mock_cursor_daily = AsyncMock()
        mock_cursor_daily.to_list = AsyncMock(return_value=[])

        # Mock zero message count
        analytics_service.db.messages.count_documents = AsyncMock(return_value=0)

        analytics_service.db.messages.aggregate.side_effect = [
            mock_cursor_model,
            mock_cursor_daily,
        ]

        result = await analytics_service.get_cost_breakdown(
            None, None, TimeRange.LAST_30_DAYS
        )

        # Should handle zero message count gracefully
        assert result.cost_metrics.avg_cost_per_message == 0.0

    @pytest.mark.asyncio
    async def test_cost_prediction_extreme_days(
        self, analytics_service, sample_daily_costs
    ):
        """Test cost prediction with extreme prediction periods."""
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_daily_costs)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Test very short prediction period
        result_short = await analytics_service.get_cost_prediction(None, None, 1)
        assert len(result_short.predictions) == 1

        # Test long prediction period (with significant decay)
        result_long = await analytics_service.get_cost_prediction(None, None, 365)
        assert len(result_long.predictions) == 365

        # Verify significant decay over a year
        first_week_avg = sum(p.predicted_cost for p in result_long.predictions[:7]) / 7
        last_week_avg = sum(p.predicted_cost for p in result_long.predictions[-7:]) / 7
        assert (
            last_week_avg < first_week_avg * 0.5
        )  # Should be significantly lower due to decay

    @pytest.mark.asyncio
    async def test_cost_functions_time_range_variations(self, analytics_service):
        """Test all cost functions work with different time ranges."""
        time_ranges = [
            TimeRange.LAST_24_HOURS,
            TimeRange.LAST_7_DAYS,
            TimeRange.LAST_30_DAYS,
            TimeRange.LAST_90_DAYS,
            TimeRange.LAST_YEAR,
        ]

        for time_range in time_ranges:
            # Test cost summary
            mock_cursor_current = AsyncMock()
            mock_cursor_current.to_list = AsyncMock(
                return_value=[{"_id": None, "total_cost": 10.0}]
            )

            mock_cursor_previous = AsyncMock()
            mock_cursor_previous.to_list = AsyncMock(
                return_value=[{"_id": None, "total_cost": 10.0}]
            )

            analytics_service.db.messages.aggregate.side_effect = [
                mock_cursor_current,
                mock_cursor_previous,
            ]

            summary = await analytics_service.get_cost_summary(None, None, time_range)
            assert isinstance(summary, CostSummary)

            # Reset for next iteration
            analytics_service.db.messages.aggregate.reset_mock()

        # Test ALL_TIME separately (only calls aggregate once)
        analytics_service.db.messages.aggregate.reset_mock()
        analytics_service.db.messages.aggregate.side_effect = None  # Clear side_effect

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(
            return_value=[{"_id": None, "total_cost": 10.0}]
        )
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        summary = await analytics_service.get_cost_summary(
            None, None, TimeRange.ALL_TIME
        )
        assert isinstance(summary, CostSummary)
