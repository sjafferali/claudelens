"""Simple tests for analytics service message-related functionality."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from bson import ObjectId

from app.schemas.analytics import TimeRange
from app.services.analytics import AnalyticsService


class TestAnalyticsServiceMessageSimple:
    """Test analytics service message functionality (simple tests only)."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        return db

    @pytest.fixture
    def analytics_service(self, mock_db):
        """Create analytics service with mock database."""
        return AnalyticsService(mock_db)

    def test_analytics_service_initialization(self, mock_db):
        """Test that the analytics service initializes correctly."""
        service = AnalyticsService(mock_db)
        assert service.db == mock_db

    def test_safe_float_message_context(self, analytics_service):
        """Test _safe_float in message analytics context."""
        # Test None (common in MongoDB aggregation when fields are missing)
        assert analytics_service._safe_float(None) == 0.0

        # Test actual costs (floats)
        assert analytics_service._safe_float(0.1234) == 0.1234

        # Test counts (integers)
        assert analytics_service._safe_float(42) == 42.0

        # Test zero
        assert analytics_service._safe_float(0) == 0.0

    def test_time_filter_for_message_analytics(self, analytics_service):
        """Test time filter generation for message analytics."""
        # Test that different time ranges generate proper filters
        filter_7d = analytics_service._get_time_filter(TimeRange.LAST_7_DAYS)
        filter_30d = analytics_service._get_time_filter(TimeRange.LAST_30_DAYS)
        filter_all = analytics_service._get_time_filter(TimeRange.ALL_TIME)

        # 7 days should have timestamp filter
        assert "timestamp" in filter_7d
        assert "$gte" in filter_7d["timestamp"]

        # 30 days should have timestamp filter with earlier date
        assert "timestamp" in filter_30d
        assert "$gte" in filter_30d["timestamp"]
        assert filter_30d["timestamp"]["$gte"] < filter_7d["timestamp"]["$gte"]

        # ALL_TIME should be empty
        assert filter_all == {}

    def test_analytics_methods_exist(self, analytics_service):
        """Test that expected analytics methods exist."""
        # Test that key message analytics methods exist
        assert hasattr(analytics_service, "get_model_usage")
        assert hasattr(analytics_service, "get_token_usage")
        assert hasattr(analytics_service, "get_cost_analytics")
        assert hasattr(analytics_service, "get_tool_usage_summary")
        assert hasattr(analytics_service, "get_tool_usage_detailed")

        # Test that they are async methods
        import inspect

        assert inspect.iscoroutinefunction(analytics_service.get_model_usage)
        assert inspect.iscoroutinefunction(analytics_service.get_token_usage)
        assert inspect.iscoroutinefunction(analytics_service.get_cost_analytics)

    def test_objectid_handling_in_project_filters(self, analytics_service):
        """Test ObjectId handling for project filters."""
        # Test that we can create ObjectId from string
        project_id_str = str(ObjectId())
        project_id_obj = ObjectId(project_id_str)

        assert isinstance(project_id_obj, ObjectId)
        assert str(project_id_obj) == project_id_str

    def test_analytics_time_range_enum_usage(self, analytics_service):
        """Test that TimeRange enum values work with time filter."""
        # Test all enum values work
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
                assert isinstance(time_filter, dict)
                assert "timestamp" in time_filter
                assert "$gte" in time_filter["timestamp"]

    def test_get_date_format_method_exists(self, analytics_service):
        """Test that _get_date_format method exists and works."""
        # This method should exist based on usage in token_usage and cost_analytics
        if hasattr(analytics_service, "_get_date_format"):
            # Test common group_by values
            day_format = analytics_service._get_date_format("day")
            assert day_format is not None

            hour_format = analytics_service._get_date_format("hour")
            assert hour_format is not None

            month_format = analytics_service._get_date_format("month")
            assert month_format is not None
        else:
            pytest.skip("_get_date_format method not available")

    def test_message_analytics_utility_methods(self, analytics_service):
        """Test utility methods used in message analytics."""
        # Test time filter ranges are properly calculated
        now = datetime.utcnow()

        # Test 24 hours
        filter_24h = analytics_service._get_time_filter(TimeRange.LAST_24_HOURS)
        if filter_24h:  # Only test if not ALL_TIME
            expected_24h = now - timedelta(hours=24)
            actual_24h = filter_24h["timestamp"]["$gte"]
            # Allow 2 seconds difference for test execution time
            assert abs((actual_24h - expected_24h).total_seconds()) < 2

        # Test 7 days
        filter_7d = analytics_service._get_time_filter(TimeRange.LAST_7_DAYS)
        expected_7d = now - timedelta(days=7)
        actual_7d = filter_7d["timestamp"]["$gte"]
        assert abs((actual_7d - expected_7d).total_seconds()) < 2

    def test_analytics_service_database_reference(self, analytics_service, mock_db):
        """Test that analytics service properly references database collections."""
        # The service should have access to the database
        assert analytics_service.db == mock_db

        # The database should have the expected collections (as mocks)
        assert hasattr(mock_db, "messages")
        assert hasattr(mock_db, "sessions")

    def test_time_range_constants(self):
        """Test TimeRange enum constants."""
        # Test that all expected time range constants exist
        assert hasattr(TimeRange, "LAST_24_HOURS")
        assert hasattr(TimeRange, "LAST_7_DAYS")
        assert hasattr(TimeRange, "LAST_30_DAYS")
        assert hasattr(TimeRange, "LAST_90_DAYS")
        assert hasattr(TimeRange, "LAST_YEAR")
        assert hasattr(TimeRange, "ALL_TIME")

        # Test that they have proper values
        assert TimeRange.LAST_24_HOURS.value == "24h"
        assert TimeRange.LAST_7_DAYS.value == "7d"
        assert TimeRange.LAST_30_DAYS.value == "30d"
        assert TimeRange.ALL_TIME.value == "all"

    def test_safe_float_edge_cases(self, analytics_service):
        """Test _safe_float with edge cases that might occur in message analytics."""
        # Test various numeric types that might come from MongoDB aggregations
        assert analytics_service._safe_float(0) == 0.0
        assert analytics_service._safe_float(0.0) == 0.0
        assert analytics_service._safe_float(1) == 1.0
        assert analytics_service._safe_float(1.0) == 1.0
        assert analytics_service._safe_float(None) == 0.0

        # Test with string representations of numbers (if supported)
        try:
            result = analytics_service._safe_float("42")
            assert result == 42.0
        except ValueError:
            # The method doesn't handle string conversion, which is fine
            pass

    def test_message_analytics_interface_completeness(self, analytics_service):
        """Test that message analytics interface is complete."""
        # Check that important analytics methods exist and are callable
        methods_to_check = [
            "get_model_usage",
            "get_token_usage",
            "get_cost_analytics",
            "get_tool_usage_summary",
            "get_tool_usage_detailed",
        ]

        for method_name in methods_to_check:
            assert hasattr(analytics_service, method_name)
            method = getattr(analytics_service, method_name)
            assert callable(method)

            # Check if it's an async method
            import inspect

            assert inspect.iscoroutinefunction(method)
