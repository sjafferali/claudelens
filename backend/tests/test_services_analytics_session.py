"""Basic tests for analytics service session-related functionality."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from app.schemas.analytics import TimeRange
from app.services.analytics import AnalyticsService


class TestAnalyticsServiceSessionBasic:
    """Test analytics service session functionality (basic tests only)."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.messages = AsyncMock()
        db.sessions = AsyncMock()
        return db

    @pytest.fixture
    def analytics_service(self, mock_db):
        """Create analytics service with mock database."""
        return AnalyticsService(mock_db)

    @pytest.mark.asyncio
    async def test_resolve_session_id_valid(self, analytics_service, mock_db):
        """Test resolving valid session ID."""
        session_id = "test-session-123"
        mock_db.sessions.find_one.return_value = {"sessionId": session_id}

        result = await analytics_service._resolve_session_id(session_id)

        assert result == session_id

    @pytest.mark.asyncio
    async def test_resolve_session_id_invalid(self, analytics_service, mock_db):
        """Test resolving invalid session ID."""
        session_id = "invalid-session"
        mock_db.sessions.find_one.return_value = None

        result = await analytics_service._resolve_session_id(session_id)

        assert result is None

    def test_safe_float_method_basic(self, analytics_service):
        """Test the _safe_float utility method with basic cases."""
        # Test None value
        assert analytics_service._safe_float(None) == 0.0

        # Test regular float
        assert analytics_service._safe_float(5.5) == 5.5

        # Test integer
        assert analytics_service._safe_float(10) == 10.0

    def test_get_time_filter_method(self, analytics_service):
        """Test the _get_time_filter utility method."""
        # Test different time ranges
        time_filter_7d = analytics_service._get_time_filter(TimeRange.LAST_7_DAYS)
        assert "timestamp" in time_filter_7d
        assert "$gte" in time_filter_7d["timestamp"]

        time_filter_30d = analytics_service._get_time_filter(TimeRange.LAST_30_DAYS)
        assert "timestamp" in time_filter_30d
        assert "$gte" in time_filter_30d["timestamp"]

        # 30 days should be earlier than 7 days
        assert (
            time_filter_30d["timestamp"]["$gte"] < time_filter_7d["timestamp"]["$gte"]
        )

        # Test ALL_TIME range
        time_filter_all = analytics_service._get_time_filter(TimeRange.ALL_TIME)
        assert time_filter_all == {}

    @pytest.mark.asyncio
    async def test_resolve_session_id_with_objectid(self, analytics_service, mock_db):
        """Test resolving session ID when input is a valid ObjectId."""
        object_id = ObjectId()
        session_id = "test-session-456"

        # Mock finding session by ObjectId first
        mock_db.sessions.find_one.side_effect = [
            {"sessionId": session_id},  # First call with ObjectId
            None,  # Second call shouldn't happen
        ]

        result = await analytics_service._resolve_session_id(str(object_id))

        assert result == session_id

    @pytest.mark.asyncio
    async def test_resolve_session_id_empty_input(self, analytics_service, mock_db):
        """Test resolving session ID with empty input."""
        result = await analytics_service._resolve_session_id("")
        assert result is None

        result = await analytics_service._resolve_session_id(None)
        assert result is None

    def test_time_filter_covers_correct_ranges(self, analytics_service):
        """Test that time filters generate correct date ranges."""
        now = datetime.utcnow()

        # Test 24 hours
        filter_24h = analytics_service._get_time_filter(TimeRange.LAST_24_HOURS)
        expected_24h = now - timedelta(hours=24)
        actual_24h = filter_24h["timestamp"]["$gte"]
        # Allow 1 second difference for test execution time
        assert abs((actual_24h - expected_24h).total_seconds()) < 1

        # Test 7 days
        filter_7d = analytics_service._get_time_filter(TimeRange.LAST_7_DAYS)
        expected_7d = now - timedelta(days=7)
        actual_7d = filter_7d["timestamp"]["$gte"]
        assert abs((actual_7d - expected_7d).total_seconds()) < 1

        # Test 30 days
        filter_30d = analytics_service._get_time_filter(TimeRange.LAST_30_DAYS)
        expected_30d = now - timedelta(days=30)
        actual_30d = filter_30d["timestamp"]["$gte"]
        assert abs((actual_30d - expected_30d).total_seconds()) < 1

    def test_service_initialization(self, mock_db):
        """Test that the analytics service initializes correctly."""
        service = AnalyticsService(mock_db)
        assert service.db == mock_db

    def test_safe_float_with_decimal128_mock(self, analytics_service):
        """Test _safe_float with a proper Decimal128 mock."""
        mock_decimal = MagicMock()
        mock_decimal.to_decimal.return_value = "3.14"
        # The _safe_float method calls str(value) on Decimal128 objects
        mock_decimal.__str__ = MagicMock(return_value="3.14")

        # The mock needs to have the to_decimal method
        assert hasattr(mock_decimal, "to_decimal")

        result = analytics_service._safe_float(mock_decimal)
        assert result == 3.14

    @pytest.mark.asyncio
    async def test_resolve_session_id_objectid_not_found(
        self, analytics_service, mock_db
    ):
        """Test resolving session ID when ObjectId exists but session doesn't."""
        object_id = ObjectId()

        # Mock finding session by ObjectId returns None, then check by sessionId also returns None
        mock_db.sessions.find_one.side_effect = [None, None]

        result = await analytics_service._resolve_session_id(str(object_id))

        assert result is None
        # Should have been called twice - once for ObjectId, once for sessionId
        assert mock_db.sessions.find_one.call_count == 2

    def test_various_time_ranges(self, analytics_service):
        """Test all supported time ranges."""
        time_ranges = [
            TimeRange.LAST_24_HOURS,
            TimeRange.LAST_7_DAYS,
            TimeRange.LAST_30_DAYS,
            TimeRange.LAST_90_DAYS,
            TimeRange.LAST_YEAR,
            TimeRange.ALL_TIME,
        ]

        for time_range in time_ranges:
            time_filter = analytics_service._get_time_filter(time_range)

            if time_range == TimeRange.ALL_TIME:
                assert time_filter == {}
            else:
                assert "timestamp" in time_filter
                assert "$gte" in time_filter["timestamp"]
                assert isinstance(time_filter["timestamp"]["$gte"], datetime)


class TestAnalyticsTimeSeriesBasic:
    """Test analytics service time series functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.messages = AsyncMock()
        db.sessions = AsyncMock()
        return db

    @pytest.fixture
    def analytics_service(self, mock_db):
        """Create analytics service with mock database."""
        return AnalyticsService(mock_db)

    @pytest.mark.asyncio
    async def test_get_response_time_series_hourly(self, analytics_service, mock_db):
        """Test response time series aggregation by hour."""
        # Mock aggregation results
        mock_results = [
            {
                "_id": "2024-01-01 12:00:00",
                "durations": [100, 200, 150, 300],
                "count": 4,
            },
            {"_id": "2024-01-01 13:00:00", "durations": [250, 180, 220], "count": 3},
        ]

        # Mock the aggregate chain properly
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_results)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        # Create base filter
        base_filter = {"timestamp": {"$gte": datetime(2024, 1, 1)}}

        result = await analytics_service._get_response_time_series(base_filter, "hour")

        assert len(result) == 2

        # Check first data point
        first_point = result[0]
        assert first_point.timestamp == datetime(2024, 1, 1, 12, 0, 0)
        assert first_point.avg_duration_ms == 187.5  # (100+200+150+300)/4
        assert (
            first_point.p50 == 200.0
        )  # sorted [100, 150, 200, 300], p50_idx=int(0.5*4)=2 -> durations[2]=200
        assert first_point.p90 == 300.0  # p90_idx=int(0.9*4)=3 -> durations[3]=300
        assert first_point.message_count == 4

        # Check second data point
        second_point = result[1]
        assert second_point.timestamp == datetime(2024, 1, 1, 13, 0, 0)
        assert round(second_point.avg_duration_ms, 2) == 216.67  # (250+180+220)/3
        assert (
            second_point.p50 == 220.0
        )  # sorted [180, 220, 250], p50_idx=int(0.5*3)=1 -> durations[1]=220
        assert second_point.p90 == 250.0  # p90_idx=int(0.9*3)=2 -> durations[2]=250
        assert second_point.message_count == 3

    @pytest.mark.asyncio
    async def test_get_response_time_series_daily(self, analytics_service, mock_db):
        """Test response time series aggregation by day."""
        mock_results = [{"_id": "2024-01-01", "durations": [100, 200, 150], "count": 3}]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_results)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        base_filter = {"timestamp": {"$gte": datetime(2024, 1, 1)}}

        result = await analytics_service._get_response_time_series(base_filter, "day")

        assert len(result) == 1
        point = result[0]
        assert point.timestamp == datetime(2024, 1, 1)
        assert round(point.avg_duration_ms, 2) == 150.0
        assert point.p50 == 150.0
        assert point.p90 == 200.0

    @pytest.mark.asyncio
    async def test_get_response_time_series_by_model(self, analytics_service, mock_db):
        """Test response time series aggregation by model."""
        mock_results = [
            {"_id": "claude-3-sonnet", "durations": [100, 200], "count": 2},
            {"_id": "claude-3-haiku", "durations": [50, 75, 60], "count": 3},
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_results)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        base_filter = {}

        result = await analytics_service._get_response_time_series(base_filter, "model")

        assert len(result) == 2
        # Results should be ordered by _id (alphabetically)

        # Find claude-3-haiku result (should come first alphabetically)
        haiku_point = next(p for p in result if p.message_count == 3)
        assert round(haiku_point.avg_duration_ms, 2) == 61.67  # (50+75+60)/3
        assert haiku_point.p50 == 60.0
        assert haiku_point.p90 == 75.0

    @pytest.mark.asyncio
    async def test_get_token_time_series_hourly(self, analytics_service, mock_db):
        """Test token usage time series aggregation by hour."""
        mock_results = [
            {"_id": "2024-01-01 12:00:00", "tokens": [100, 200, 150, 300], "count": 4},
            {"_id": "2024-01-01 13:00:00", "tokens": [250, 180, 220], "count": 3},
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_results)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        base_filter = {"timestamp": {"$gte": datetime(2024, 1, 1)}}

        result = await analytics_service._get_token_time_series(base_filter, "hour")

        assert len(result) == 2

        # Check first data point
        first_point = result[0]
        assert first_point.timestamp == datetime(2024, 1, 1, 12, 0, 0)
        assert first_point.avg_tokens == 187.5  # (100+200+150+300)/4
        assert (
            first_point.p50 == 200.0
        )  # sorted [100, 150, 200, 300], p50_idx=int(0.5*4)=2 -> tokens[2]=200
        assert first_point.p90 == 300.0
        assert first_point.message_count == 4

    @pytest.mark.asyncio
    async def test_get_token_time_series_daily(self, analytics_service, mock_db):
        """Test token usage time series aggregation by day."""
        mock_results = [{"_id": "2024-01-01", "tokens": [500, 750, 600], "count": 3}]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_results)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        base_filter = {"timestamp": {"$gte": datetime(2024, 1, 1)}}

        result = await analytics_service._get_token_time_series(base_filter, "day")

        assert len(result) == 1
        point = result[0]
        assert point.timestamp == datetime(2024, 1, 1)
        assert round(point.avg_tokens, 2) == 616.67  # (500+750+600)/3
        assert point.p50 == 600.0
        assert point.p90 == 750.0

    @pytest.mark.asyncio
    async def test_get_token_time_series_by_model(self, analytics_service, mock_db):
        """Test token usage time series aggregation by model."""
        mock_results = [
            {"_id": "claude-3-sonnet", "tokens": [1000, 1200], "count": 2},
            {"_id": "claude-3-haiku", "tokens": [400, 500, 450], "count": 3},
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_results)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        base_filter = {}

        result = await analytics_service._get_token_time_series(base_filter, "model")

        assert len(result) == 2

        # Find haiku result
        haiku_point = next(p for p in result if p.message_count == 3)
        assert haiku_point.avg_tokens == 450.0  # (400+500+450)/3
        assert haiku_point.p50 == 450.0
        assert haiku_point.p90 == 500.0

    @pytest.mark.asyncio
    async def test_time_series_empty_results(self, analytics_service, mock_db):
        """Test time series functions with empty results."""
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[])
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        base_filter = {}

        # Test response time series
        result = await analytics_service._get_response_time_series(base_filter, "hour")
        assert result == []

        # Test token time series
        result = await analytics_service._get_token_time_series(base_filter, "hour")
        assert result == []

    @pytest.mark.asyncio
    async def test_time_series_zero_count_filtered(self, analytics_service, mock_db):
        """Test that time series filters out zero-count results."""
        mock_results = [
            {"_id": "2024-01-01 12:00:00", "durations": [], "count": 0},
            {"_id": "2024-01-01 13:00:00", "durations": [100, 200], "count": 2},
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_results)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        base_filter = {}

        result = await analytics_service._get_response_time_series(base_filter, "hour")

        # Should only return the non-empty result
        assert len(result) == 1
        assert result[0].message_count == 2

    @pytest.mark.asyncio
    async def test_time_series_percentile_edge_cases(self, analytics_service, mock_db):
        """Test percentile calculations with edge cases."""
        # Single data point
        mock_results = [
            {
                "_id": "2024-01-01 12:00:00",
                "durations": [150],  # Single value
                "count": 1,
            }
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_results)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        base_filter = {}

        result = await analytics_service._get_response_time_series(base_filter, "hour")

        assert len(result) == 1
        point = result[0]
        assert point.avg_duration_ms == 150.0
        assert point.p50 == 150.0  # Same value for all percentiles
        assert point.p90 == 150.0
        assert point.message_count == 1


class TestAnalyticsAggregationBasic:
    """Test analytics service aggregation functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.messages = AsyncMock()
        db.sessions = AsyncMock()
        return db

    @pytest.fixture
    def analytics_service(self, mock_db):
        """Create analytics service with mock database."""
        return AnalyticsService(mock_db)

    def test_calculate_trend_basic(self, analytics_service):
        """Test trend calculation with basic values."""
        # Test normal increase
        trend = analytics_service._calculate_trend(120.0, 100.0)
        assert trend == 20.0

        # Test decrease
        trend = analytics_service._calculate_trend(80.0, 100.0)
        assert trend == -20.0

        # Test no change
        trend = analytics_service._calculate_trend(100.0, 100.0)
        assert trend == 0.0

    def test_calculate_trend_edge_cases(self, analytics_service):
        """Test trend calculation with edge cases."""
        # Test zero previous value
        trend = analytics_service._calculate_trend(50.0, 0.0)
        assert trend == 100.0

        # Test zero previous, zero current
        trend = analytics_service._calculate_trend(0.0, 0.0)
        assert trend == 0.0

        # Test None values
        trend = analytics_service._calculate_trend(None, 100.0)
        assert trend == -100.0

        trend = analytics_service._calculate_trend(100.0, None)
        assert trend == 100.0

    def test_calculate_trend_decimal128_mock(self, analytics_service):
        """Test trend calculation with Decimal128 values."""
        # Mock Decimal128 objects
        mock_current = MagicMock()
        mock_current.to_decimal.return_value = "150.0"
        mock_current.__str__ = MagicMock(return_value="150.0")

        mock_previous = MagicMock()
        mock_previous.to_decimal.return_value = "100.0"
        mock_previous.__str__ = MagicMock(return_value="100.0")

        trend = analytics_service._calculate_trend(mock_current, mock_previous)
        assert trend == 50.0

    @pytest.mark.asyncio
    async def test_get_period_stats_basic(self, analytics_service, mock_db):
        """Test basic period statistics aggregation."""
        # Mock faceted aggregation result
        mock_result = [
            {
                "messageCostStats": [{"count": 150, "totalCost": 45.50}],
                "sessionStats": [{"count": 25}],
                "projectStats": [{"count": 5}],
            }
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        time_filter = {"timestamp": {"$gte": datetime(2024, 1, 1)}}

        result = await analytics_service._get_period_stats(time_filter)

        assert result["total_messages"] == 150
        assert result["total_sessions"] == 25
        assert result["total_projects"] == 5
        assert result["total_cost"] == 45.50

    @pytest.mark.asyncio
    async def test_get_period_stats_empty_result(self, analytics_service, mock_db):
        """Test period statistics with empty results."""
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[])
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        time_filter = {"timestamp": {"$gte": datetime(2024, 1, 1)}}

        result = await analytics_service._get_period_stats(time_filter)

        assert result["total_messages"] == 0
        assert result["total_sessions"] == 0
        assert result["total_projects"] == 0
        assert result["total_cost"] == 0.0

    @pytest.mark.asyncio
    async def test_get_period_stats_missing_facets(self, analytics_service, mock_db):
        """Test period statistics with missing facet results."""
        # Mock result with missing facets
        mock_result = [{"messageCostStats": [], "sessionStats": [], "projectStats": []}]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        time_filter = {}

        result = await analytics_service._get_period_stats(time_filter)

        assert result["total_messages"] == 0
        assert result["total_sessions"] == 0
        assert result["total_projects"] == 0
        assert result["total_cost"] == 0.0

    @pytest.mark.asyncio
    async def test_get_period_stats_decimal128_cost(self, analytics_service, mock_db):
        """Test period statistics with Decimal128 cost values."""
        # Mock Decimal128 cost
        mock_cost = MagicMock()
        mock_cost.to_decimal.return_value = "123.45"
        mock_cost.__str__ = MagicMock(return_value="123.45")

        mock_result = [
            {
                "messageCostStats": [{"count": 100, "totalCost": mock_cost}],
                "sessionStats": [{"count": 10}],
                "projectStats": [{"count": 2}],
            }
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        time_filter = {}

        result = await analytics_service._get_period_stats(time_filter)

        assert result["total_messages"] == 100
        assert result["total_cost"] == 123.45

    @pytest.mark.asyncio
    async def test_calculate_percentiles_basic(self, analytics_service, mock_db):
        """Test percentile calculation."""
        # Mock percentile aggregation result
        mock_result = [
            {"count": 100, "p50": 250.0, "p90": 800.0, "p95": 1200.0, "p99": 2000.0}
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        base_filter = {"timestamp": {"$gte": datetime(2024, 1, 1)}}
        percentiles = [50, 90, 95, 99]

        result = await analytics_service._calculate_percentiles(
            base_filter, percentiles
        )

        assert result.p50 == 250.0
        assert result.p90 == 800.0
        assert result.p95 == 1200.0
        assert result.p99 == 2000.0

    @pytest.mark.asyncio
    async def test_calculate_percentiles_empty_result(self, analytics_service, mock_db):
        """Test percentile calculation with empty result."""
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[])
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        base_filter = {}
        percentiles = [50, 90, 95, 99]

        result = await analytics_service._calculate_percentiles(
            base_filter, percentiles
        )

        assert result.p50 == 0
        assert result.p90 == 0
        assert result.p95 == 0
        assert result.p99 == 0

    @pytest.mark.asyncio
    async def test_calculate_percentiles_zero_count(self, analytics_service, mock_db):
        """Test percentile calculation with zero count."""
        mock_result = [{"count": 0}]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        base_filter = {}
        percentiles = [50, 90, 95, 99]

        result = await analytics_service._calculate_percentiles(
            base_filter, percentiles
        )

        assert result.p50 == 0
        assert result.p90 == 0
        assert result.p95 == 0
        assert result.p99 == 0

    def test_safe_float_aggregation_helper(self, analytics_service):
        """Test the _safe_float helper used in aggregations."""
        # Test with aggregation-like values
        assert analytics_service._safe_float(0) == 0.0
        assert analytics_service._safe_float(123.45) == 123.45
        assert analytics_service._safe_float("67.89") == 67.89

        # Test with None (common in aggregation results)
        assert analytics_service._safe_float(None) == 0.0


class TestAnalyticsPerformanceMetrics:
    """Test analytics service performance metrics functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.messages = AsyncMock()
        db.sessions = AsyncMock()
        return db

    @pytest.fixture
    def analytics_service(self, mock_db):
        """Create analytics service with mock database."""
        return AnalyticsService(mock_db)

    @pytest.mark.asyncio
    async def test_calculate_cost_efficiency_basic(self, analytics_service, mock_db):
        """Test cost efficiency calculation."""
        # Mock aggregation result
        mock_result = [
            {"total_cost": 10.0, "total_messages": 100, "successful_operations": 95}
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        message_filter = {"timestamp": {"$gte": datetime(2024, 1, 1)}}

        result = await analytics_service._calculate_cost_efficiency(message_filter)

        # 95 successful operations / $10 = 9.5 operations per dollar * 100 = 950.0
        assert result == 950.0

    @pytest.mark.asyncio
    async def test_calculate_cost_efficiency_zero_cost(
        self, analytics_service, mock_db
    ):
        """Test cost efficiency with zero cost."""
        mock_result = [
            {"total_cost": 0.0, "total_messages": 100, "successful_operations": 95}
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        message_filter = {}

        result = await analytics_service._calculate_cost_efficiency(message_filter)

        assert result == 0.0

    @pytest.mark.asyncio
    async def test_calculate_cost_efficiency_empty_result(
        self, analytics_service, mock_db
    ):
        """Test cost efficiency with empty result."""
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[])
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        message_filter = {}

        result = await analytics_service._calculate_cost_efficiency(message_filter)

        assert result == 0.0

    @pytest.mark.asyncio
    async def test_calculate_speed_score_basic(self, analytics_service, mock_db):
        """Test speed score calculation."""
        # Mock aggregation result - 1 second average response time
        mock_result = [{"avg_duration": 1000.0, "count": 50}]  # 1000ms = 1 second

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        message_filter = {"timestamp": {"$gte": datetime(2024, 1, 1)}}

        result = await analytics_service._calculate_speed_score(message_filter)

        # Speed score = 100 - log10(1) * 20 = 100 - 0 * 20 = 100.0
        assert result == 100.0

    @pytest.mark.asyncio
    async def test_calculate_speed_score_slow_response(
        self, analytics_service, mock_db
    ):
        """Test speed score with slow response times."""
        # Mock aggregation result - 10 seconds average response time
        mock_result = [{"avg_duration": 10000.0, "count": 50}]  # 10000ms = 10 seconds

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        message_filter = {}

        result = await analytics_service._calculate_speed_score(message_filter)

        # Speed score = 100 - log10(10) * 20 = 100 - 1 * 20 = 80.0
        assert result == 80.0

    @pytest.mark.asyncio
    async def test_calculate_speed_score_empty_result(self, analytics_service, mock_db):
        """Test speed score with empty result."""
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[])
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        message_filter = {}

        result = await analytics_service._calculate_speed_score(message_filter)

        assert result == 50.0  # Neutral score

    @pytest.mark.asyncio
    async def test_calculate_speed_score_zero_count(self, analytics_service, mock_db):
        """Test speed score with zero count."""
        mock_result = [{"count": 0}]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        message_filter = {}

        result = await analytics_service._calculate_speed_score(message_filter)

        assert result == 50.0  # Neutral score

    @pytest.mark.asyncio
    async def test_calculate_quality_score_perfect(self, analytics_service, mock_db):
        """Test quality score with no errors."""
        mock_result = [{"total_messages": 100, "error_messages": 0}]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        message_filter = {"timestamp": {"$gte": datetime(2024, 1, 1)}}

        result = await analytics_service._calculate_quality_score(message_filter)

        assert result == 100.0  # Perfect score

    @pytest.mark.asyncio
    async def test_calculate_quality_score_with_errors(
        self, analytics_service, mock_db
    ):
        """Test quality score with some errors."""
        mock_result = [{"total_messages": 100, "error_messages": 5}]  # 5% error rate

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        message_filter = {}

        result = await analytics_service._calculate_quality_score(message_filter)

        # Quality score = (1 - 0.05) * 100 = 95.0
        assert result == 95.0

    @pytest.mark.asyncio
    async def test_calculate_quality_score_empty_result(
        self, analytics_service, mock_db
    ):
        """Test quality score with empty result."""
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[])
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        message_filter = {}

        result = await analytics_service._calculate_quality_score(message_filter)

        assert result == 100.0  # Perfect score if no data

    @pytest.mark.asyncio
    async def test_calculate_productivity_score_basic(self, analytics_service, mock_db):
        """Test productivity score calculation."""
        mock_result = [
            {
                "avg_messages_per_session": 10.0,
                "avg_tools_per_session": 5.0,
                "session_count": 20,
            }
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        message_filter = {"timestamp": {"$gte": datetime(2024, 1, 1)}}

        result = await analytics_service._calculate_productivity_score(message_filter)

        # messages_score = min(100, 10 * 2) = 20
        # tools_score = min(100, 5 * 5) = 25
        # productivity = 20 * 0.6 + 25 * 0.4 = 12 + 10 = 22.0
        assert result == 22.0

    @pytest.mark.asyncio
    async def test_calculate_productivity_score_capped(
        self, analytics_service, mock_db
    ):
        """Test productivity score with values that hit the caps."""
        mock_result = [
            {
                "avg_messages_per_session": 60.0,  # Would be 120 * 2, capped at 100
                "avg_tools_per_session": 25.0,  # Would be 125 * 5, capped at 100
                "session_count": 5,
            }
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        message_filter = {}

        result = await analytics_service._calculate_productivity_score(message_filter)

        # Both scores capped at 100
        # productivity = 100 * 0.6 + 100 * 0.4 = 60 + 40 = 100.0
        assert result == 100.0

    @pytest.mark.asyncio
    async def test_calculate_productivity_score_empty_result(
        self, analytics_service, mock_db
    ):
        """Test productivity score with empty result."""
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[])
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        message_filter = {}

        result = await analytics_service._calculate_productivity_score(message_filter)

        assert result == 50.0  # Neutral score

    @pytest.mark.asyncio
    async def test_calculate_productivity_score_zero_sessions(
        self, analytics_service, mock_db
    ):
        """Test productivity score with zero sessions."""
        mock_result = [{"session_count": 0}]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=mock_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        message_filter = {}

        result = await analytics_service._calculate_productivity_score(message_filter)

        assert result == 50.0  # Neutral score
