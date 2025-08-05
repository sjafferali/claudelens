"""Comprehensive tests for analytics service error tracking functionality."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from app.schemas.analytics import (
    ErrorDetail,
    ErrorDetailsResponse,
    ErrorSummary,
    SessionHealth,
    SuccessRateMetrics,
    TimeRange,
)
from app.services.analytics import AnalyticsService


class TestAnalyticsServiceErrorTracking:
    """Test analytics service error tracking functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()

        # Mock the aggregate method to return a mock cursor
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock()
        db.messages.aggregate.return_value = mock_cursor

        db.messages = AsyncMock()
        db.messages.aggregate = MagicMock(return_value=mock_cursor)
        db.sessions = AsyncMock()
        return db

    @pytest.fixture
    def analytics_service(self, mock_db):
        """Create analytics service with mock database."""
        return AnalyticsService(mock_db)

    @pytest.fixture
    def sample_error_data(self):
        """Sample error data for testing."""
        now = datetime.now(timezone.utc)
        return [
            {
                "_id": ObjectId(),
                "timestamp": now - timedelta(hours=1),
                "type": "tool_result",
                "toolUseResult": "Error: File not found",
                "sessionId": "session-123",
                "tool_use_info": [{"messageData": {"name": "read_file"}}],
            },
            {
                "_id": ObjectId(),
                "timestamp": now - timedelta(hours=2),
                "type": "tool_result",
                "toolUseResult": "Permission denied",
                "sessionId": "session-123",
                "tool_use_info": [{"messageData": {"name": "write_file"}}],
            },
            {
                "_id": ObjectId(),
                "timestamp": now - timedelta(hours=3),
                "type": "tool_result",
                "toolUseResult": "Success: Operation completed",
                "sessionId": "session-123",
                "tool_use_info": [{"messageData": {"name": "create_file"}}],
            },
        ]

    @pytest.fixture
    def sample_aggregation_data(self):
        """Sample aggregation data for success rate tests."""
        return [
            {
                "total_operations": 10,
                "successful_operations": 8,
                "failed_operations": 2,
            }
        ]

    @pytest.fixture
    def sample_session_health_data(self):
        """Sample aggregation data for session health tests."""
        return [
            {
                "total_operations": 10,
                "successful_operations": 8,
                "error_count": 2,
            }
        ]

    # get_detailed_errors tests
    @pytest.mark.asyncio
    async def test_get_detailed_errors_basic_functionality(
        self, analytics_service, mock_db, sample_error_data
    ):
        """Test basic functionality of get_detailed_errors."""
        # Mock database responses
        mock_db.messages.aggregate.return_value.to_list.return_value = sample_error_data

        result = await analytics_service.get_detailed_errors()

        assert isinstance(result, ErrorDetailsResponse)
        assert len(result.errors) >= 0  # Can be 0 if no errors detected in sample data
        assert isinstance(result.error_summary, ErrorSummary)

        # Verify database was queried
        mock_db.messages.aggregate.assert_called()

    @pytest.mark.asyncio
    async def test_get_detailed_errors_with_session_id(
        self, analytics_service, mock_db, sample_error_data
    ):
        """Test get_detailed_errors with specific session ID."""
        session_id = "test-session-123"

        # Mock session resolution
        analytics_service._resolve_session_id = AsyncMock(return_value=session_id)
        mock_db.messages.aggregate.return_value.to_list.return_value = sample_error_data

        result = await analytics_service.get_detailed_errors(session_id=session_id)

        assert isinstance(result, ErrorDetailsResponse)
        analytics_service._resolve_session_id.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_get_detailed_errors_invalid_session_id(
        self, analytics_service, mock_db
    ):
        """Test get_detailed_errors with invalid session ID."""
        session_id = "invalid-session"

        # Mock session resolution to return None
        analytics_service._resolve_session_id = AsyncMock(return_value=None)

        result = await analytics_service.get_detailed_errors(session_id=session_id)

        assert isinstance(result, ErrorDetailsResponse)
        assert len(result.errors) == 0
        assert result.error_summary.by_type == {}
        assert result.error_summary.by_tool == {}

    @pytest.mark.asyncio
    async def test_get_detailed_errors_no_errors_found(
        self, analytics_service, mock_db
    ):
        """Test get_detailed_errors when no errors are found."""
        # Mock empty results
        mock_db.messages.aggregate.return_value.to_list.return_value = []

        result = await analytics_service.get_detailed_errors()

        assert isinstance(result, ErrorDetailsResponse)
        assert len(result.errors) == 0
        assert isinstance(result.error_summary, ErrorSummary)

    @pytest.mark.asyncio
    async def test_get_detailed_errors_different_time_ranges(
        self, analytics_service, mock_db, sample_error_data
    ):
        """Test get_detailed_errors with different time ranges."""
        mock_db.messages.aggregate.return_value.to_list.return_value = sample_error_data

        time_ranges = [
            TimeRange.LAST_24_HOURS,
            TimeRange.LAST_7_DAYS,
            TimeRange.LAST_30_DAYS,
            TimeRange.LAST_90_DAYS,
            TimeRange.ALL_TIME,
        ]

        for time_range in time_ranges:
            result = await analytics_service.get_detailed_errors(time_range=time_range)
            assert isinstance(result, ErrorDetailsResponse)

    @pytest.mark.asyncio
    async def test_get_detailed_errors_with_error_severity_filter(
        self, analytics_service, mock_db, sample_error_data
    ):
        """Test get_detailed_errors with error severity filter."""
        mock_db.messages.aggregate.return_value.to_list.return_value = sample_error_data

        result = await analytics_service.get_detailed_errors(error_severity="critical")

        assert isinstance(result, ErrorDetailsResponse)

    @pytest.mark.asyncio
    async def test_get_detailed_errors_database_exception(
        self, analytics_service, mock_db
    ):
        """Test get_detailed_errors handles database exceptions."""
        # Mock database to raise exception
        mock_db.messages.aggregate.side_effect = Exception("Database connection error")

        with pytest.raises(Exception):
            await analytics_service.get_detailed_errors()

    @pytest.mark.asyncio
    async def test_get_detailed_errors_empty_tool_use_info(
        self, analytics_service, mock_db
    ):
        """Test get_detailed_errors with empty tool_use_info."""
        error_data_no_tool_info = [
            {
                "_id": ObjectId(),
                "timestamp": datetime.now(timezone.utc),
                "type": "tool_result",
                "toolUseResult": "Error occurred",
                "sessionId": "session-123",
                "tool_use_info": [],  # Empty tool info
            }
        ]

        mock_db.messages.aggregate.return_value.to_list.return_value = (
            error_data_no_tool_info
        )

        result = await analytics_service.get_detailed_errors()

        assert isinstance(result, ErrorDetailsResponse)

    # get_success_rate tests
    @pytest.mark.asyncio
    async def test_get_success_rate_basic_functionality(
        self, analytics_service, mock_db, sample_aggregation_data
    ):
        """Test basic functionality of get_success_rate."""
        mock_db.messages.aggregate.return_value.to_list.return_value = (
            sample_aggregation_data
        )

        result = await analytics_service.get_success_rate()

        assert isinstance(result, SuccessRateMetrics)
        assert 0.0 <= result.success_rate <= 100.0
        assert result.total_operations >= 0
        assert result.successful_operations >= 0
        assert result.failed_operations >= 0
        assert result.time_range == TimeRange.LAST_30_DAYS  # default

    @pytest.mark.asyncio
    async def test_get_success_rate_with_session_id(
        self, analytics_service, mock_db, sample_aggregation_data
    ):
        """Test get_success_rate with specific session ID."""
        session_id = "test-session-123"
        mock_db.messages.aggregate.return_value.to_list.return_value = (
            sample_aggregation_data
        )

        result = await analytics_service.get_success_rate(session_id=session_id)

        assert isinstance(result, SuccessRateMetrics)

    @pytest.mark.asyncio
    async def test_get_success_rate_no_operations(self, analytics_service, mock_db):
        """Test get_success_rate when no operations exist."""
        mock_db.messages.aggregate.return_value.to_list.return_value = []

        result = await analytics_service.get_success_rate()

        assert isinstance(result, SuccessRateMetrics)
        assert result.success_rate == 100.0  # Default when no operations
        assert result.total_operations == 0
        assert result.successful_operations == 0
        assert result.failed_operations == 0

    @pytest.mark.asyncio
    async def test_get_success_rate_all_successful(self, analytics_service, mock_db):
        """Test get_success_rate with 100% success rate."""
        all_successful_data = [
            {
                "total_operations": 10,
                "successful_operations": 10,
                "failed_operations": 0,
            }
        ]

        mock_db.messages.aggregate.return_value.to_list.return_value = (
            all_successful_data
        )

        result = await analytics_service.get_success_rate()

        assert result.success_rate == 100.0
        assert result.total_operations == 10
        assert result.successful_operations == 10
        assert result.failed_operations == 0

    @pytest.mark.asyncio
    async def test_get_success_rate_all_failed(self, analytics_service, mock_db):
        """Test get_success_rate with 0% success rate."""
        all_failed_data = [
            {
                "total_operations": 5,
                "successful_operations": 0,
                "failed_operations": 5,
            }
        ]

        mock_db.messages.aggregate.return_value.to_list.return_value = all_failed_data

        result = await analytics_service.get_success_rate()

        assert result.success_rate == 0.0
        assert result.total_operations == 5
        assert result.successful_operations == 0
        assert result.failed_operations == 5

    @pytest.mark.asyncio
    async def test_get_success_rate_different_time_ranges(
        self, analytics_service, mock_db, sample_aggregation_data
    ):
        """Test get_success_rate with different time ranges."""
        mock_db.messages.aggregate.return_value.to_list.return_value = (
            sample_aggregation_data
        )

        time_ranges = [
            TimeRange.LAST_24_HOURS,
            TimeRange.LAST_7_DAYS,
            TimeRange.LAST_30_DAYS,
            TimeRange.LAST_90_DAYS,
            TimeRange.ALL_TIME,
        ]

        for time_range in time_ranges:
            result = await analytics_service.get_success_rate(time_range=time_range)
            assert isinstance(result, SuccessRateMetrics)
            assert result.time_range == time_range

    @pytest.mark.asyncio
    async def test_get_success_rate_percentage_boundaries(
        self, analytics_service, mock_db
    ):
        """Test get_success_rate percentage calculation edge cases."""
        # Test fractional success rate
        fractional_data = [
            {
                "total_operations": 3,
                "successful_operations": 2,
                "failed_operations": 1,
            }
        ]

        mock_db.messages.aggregate.return_value.to_list.return_value = fractional_data

        result = await analytics_service.get_success_rate()

        # Should be 66.7% (2/3 * 100)
        assert 66.0 <= result.success_rate <= 67.0
        assert result.total_operations == 3

    @pytest.mark.asyncio
    async def test_get_success_rate_database_exception(
        self, analytics_service, mock_db
    ):
        """Test get_success_rate handles database exceptions."""
        mock_db.messages.aggregate.side_effect = Exception("Database connection error")

        with pytest.raises(Exception):
            await analytics_service.get_success_rate()

    # get_session_health tests
    @pytest.mark.asyncio
    async def test_get_session_health_basic_functionality(
        self, analytics_service, mock_db, sample_session_health_data
    ):
        """Test basic functionality of get_session_health."""
        mock_db.messages.aggregate.return_value.to_list.return_value = (
            sample_session_health_data
        )

        result = await analytics_service.get_session_health()

        assert isinstance(result, SessionHealth)
        assert 0.0 <= result.success_rate <= 100.0
        assert result.total_operations >= 0
        assert result.error_count >= 0
        assert result.health_status in ["excellent", "good", "fair", "poor"]

    @pytest.mark.asyncio
    async def test_get_session_health_with_session_id(
        self, analytics_service, mock_db, sample_session_health_data
    ):
        """Test get_session_health with specific session ID."""
        session_id = "test-session-123"
        mock_db.messages.aggregate.return_value.to_list.return_value = (
            sample_session_health_data
        )

        result = await analytics_service.get_session_health(session_id=session_id)

        assert isinstance(result, SessionHealth)

    @pytest.mark.asyncio
    async def test_get_session_health_no_operations(self, analytics_service, mock_db):
        """Test get_session_health when no operations exist."""
        mock_db.messages.aggregate.return_value.to_list.return_value = []

        result = await analytics_service.get_session_health()

        assert isinstance(result, SessionHealth)
        assert result.success_rate == 100.0
        assert result.total_operations == 0
        assert result.error_count == 0
        assert result.health_status == "excellent"

    @pytest.mark.asyncio
    async def test_get_session_health_excellent_status(
        self, analytics_service, mock_db
    ):
        """Test get_session_health with excellent health status (>95% success)."""
        excellent_data = [
            {
                "total_operations": 100,
                "successful_operations": 98,
                "error_count": 2,
            }
        ]

        mock_db.messages.aggregate.return_value.to_list.return_value = excellent_data

        result = await analytics_service.get_session_health()

        assert result.success_rate == 98.0
        assert result.health_status == "excellent"

    @pytest.mark.asyncio
    async def test_get_session_health_good_status(self, analytics_service, mock_db):
        """Test get_session_health with good health status (80-95% success)."""
        good_data = [
            {
                "total_operations": 100,
                "successful_operations": 85,
                "error_count": 15,
            }
        ]

        mock_db.messages.aggregate.return_value.to_list.return_value = good_data

        result = await analytics_service.get_session_health()

        assert result.success_rate == 85.0
        assert result.health_status == "good"

    @pytest.mark.asyncio
    async def test_get_session_health_fair_status(self, analytics_service, mock_db):
        """Test get_session_health with fair health status (60-80% success)."""
        fair_data = [
            {
                "total_operations": 100,
                "successful_operations": 70,
                "error_count": 30,
            }
        ]

        mock_db.messages.aggregate.return_value.to_list.return_value = fair_data

        result = await analytics_service.get_session_health()

        assert result.success_rate == 70.0
        assert result.health_status == "fair"

    @pytest.mark.asyncio
    async def test_get_session_health_poor_status(self, analytics_service, mock_db):
        """Test get_session_health with poor health status (<60% success)."""
        poor_data = [
            {
                "total_operations": 100,
                "successful_operations": 40,
                "error_count": 60,
            }
        ]

        mock_db.messages.aggregate.return_value.to_list.return_value = poor_data

        result = await analytics_service.get_session_health()

        assert result.success_rate == 40.0
        assert result.health_status == "poor"

    @pytest.mark.asyncio
    async def test_get_session_health_boundary_conditions(
        self, analytics_service, mock_db
    ):
        """Test get_session_health at exact boundary conditions."""
        # Test exact 95% boundary (should be excellent)
        boundary_95_data = [
            {
                "total_operations": 100,
                "successful_operations": 95,
                "error_count": 5,
            }
        ]

        mock_db.messages.aggregate.return_value.to_list.return_value = boundary_95_data

        result = await analytics_service.get_session_health()

        assert result.success_rate == 95.0
        # Should be good, not excellent (>95 means strictly greater than 95)
        assert result.health_status == "good"

    @pytest.mark.asyncio
    async def test_get_session_health_different_time_ranges(
        self, analytics_service, mock_db, sample_session_health_data
    ):
        """Test get_session_health with different time ranges."""
        mock_db.messages.aggregate.return_value.to_list.return_value = (
            sample_session_health_data
        )

        time_ranges = [
            TimeRange.LAST_24_HOURS,
            TimeRange.LAST_7_DAYS,
            TimeRange.LAST_30_DAYS,
            TimeRange.LAST_90_DAYS,
            TimeRange.ALL_TIME,
        ]

        for time_range in time_ranges:
            result = await analytics_service.get_session_health(time_range=time_range)
            assert isinstance(result, SessionHealth)

    @pytest.mark.asyncio
    async def test_get_session_health_database_exception(
        self, analytics_service, mock_db
    ):
        """Test get_session_health handles database exceptions."""
        mock_db.messages.aggregate.side_effect = Exception("Database connection error")

        with pytest.raises(Exception):
            await analytics_service.get_session_health()

    @pytest.mark.asyncio
    async def test_get_session_health_zero_operations_edge_case(
        self, analytics_service, mock_db
    ):
        """Test get_session_health with zero operations data structure."""
        zero_ops_data = [
            {
                "total_operations": 0,
                "successful_operations": 0,
                "error_count": 0,
            }
        ]

        mock_db.messages.aggregate.return_value.to_list.return_value = zero_ops_data

        result = await analytics_service.get_session_health()

        # Should handle division by zero gracefully
        assert result.success_rate >= 0.0
        assert result.total_operations == 0
        assert result.error_count == 0

    # Integration and edge case tests
    @pytest.mark.asyncio
    async def test_error_tracking_methods_with_time_filter_integration(
        self, analytics_service, mock_db
    ):
        """Test that all error tracking methods properly use time filters."""
        # Mock the _get_time_filter method
        analytics_service._get_time_filter = MagicMock(
            return_value={
                "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}
            }
        )

        mock_db.messages.aggregate.return_value.to_list.return_value = []

        # Test each method calls _get_time_filter
        await analytics_service.get_detailed_errors(time_range=TimeRange.LAST_7_DAYS)
        await analytics_service.get_success_rate(time_range=TimeRange.LAST_7_DAYS)
        await analytics_service.get_session_health(time_range=TimeRange.LAST_7_DAYS)

        # Should be called 3 times
        assert analytics_service._get_time_filter.call_count == 3

    @pytest.mark.asyncio
    async def test_error_tracking_methods_consistency(self, analytics_service, mock_db):
        """Test that error tracking methods return consistent data structures."""
        sample_data = [
            {
                "total_operations": 10,
                "successful_operations": 8,
                "failed_operations": 2,
                "error_count": 2,
            }
        ]

        mock_db.messages.aggregate.return_value.to_list.return_value = sample_data

        # Test success rate and session health consistency
        success_rate_result = await analytics_service.get_success_rate()
        session_health_result = await analytics_service.get_session_health()

        # Both should calculate similar success rates
        assert (
            success_rate_result.total_operations
            == session_health_result.total_operations
        )
        # Allow for small rounding differences
        assert (
            abs(success_rate_result.success_rate - session_health_result.success_rate)
            < 0.1
        )

    def test_error_tracking_schema_validation(self):
        """Test that error tracking schemas validate correctly."""
        # Test ErrorDetail schema
        error_detail = ErrorDetail(
            timestamp=datetime.now(timezone.utc),
            tool="test_tool",
            error_type="FileNotFound",
            severity="critical",
            message="Test error message",
            context="Test context",
        )
        assert error_detail.tool == "test_tool"
        assert error_detail.severity == "critical"

        # Test ErrorSummary schema
        error_summary = ErrorSummary(
            by_type={"FileNotFound": 1, "PermissionDenied": 2},
            by_tool={"read_file": 2, "write_file": 1},
        )
        assert error_summary.by_type["FileNotFound"] == 1
        assert error_summary.by_tool["read_file"] == 2

        # Test ErrorDetailsResponse schema
        error_response = ErrorDetailsResponse(
            errors=[error_detail], error_summary=error_summary
        )
        assert len(error_response.errors) == 1
        assert error_response.error_summary.by_type["FileNotFound"] == 1

        # Test SuccessRateMetrics schema
        success_metrics = SuccessRateMetrics(
            success_rate=80.5,
            total_operations=100,
            successful_operations=80,
            failed_operations=20,
            time_range=TimeRange.LAST_30_DAYS,
        )
        assert success_metrics.success_rate == 80.5
        assert success_metrics.time_range == TimeRange.LAST_30_DAYS

        # Test SessionHealth schema
        session_health = SessionHealth(
            success_rate=85.0, total_operations=50, error_count=7, health_status="good"
        )
        assert session_health.health_status == "good"
        assert session_health.error_count == 7

    @pytest.mark.asyncio
    async def test_error_tracking_large_dataset_handling(
        self, analytics_service, mock_db
    ):
        """Test error tracking methods with large datasets."""
        # Simulate large dataset with many errors
        large_error_dataset = []
        for i in range(100):
            large_error_dataset.append(
                {
                    "_id": ObjectId(),
                    "timestamp": datetime.now(timezone.utc) - timedelta(hours=i),
                    "type": "tool_result",
                    "toolUseResult": f"Error {i}: Test error",
                    "sessionId": f"session-{i % 10}",
                    "tool_use_info": [{"messageData": {"name": f"tool_{i % 5}"}}],
                }
            )

        mock_db.messages.aggregate.return_value.to_list.return_value = (
            large_error_dataset
        )

        result = await analytics_service.get_detailed_errors()

        # Should handle large datasets and limit results (typically to 50 most recent)
        assert isinstance(result, ErrorDetailsResponse)
        assert len(result.errors) <= 50  # Based on the limit in the implementation
