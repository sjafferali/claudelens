"""Comprehensive tests for analytics service token efficiency functionality."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.analytics import (
    TimeRange,
    TokenBreakdown,
    TokenEfficiencyDetailed,
    TokenEfficiencyMetrics,
    TokenEfficiencySummary,
    TokenFormattedValues,
)
from app.services.analytics import AnalyticsService


class TestAnalyticsServiceTokenEfficiency:
    """Test analytics service token efficiency functionality."""

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
    def sample_token_data(self):
        """Sample token aggregation results with comprehensive data."""
        return [
            {
                "_id": None,
                "total_input": 15000,
                "total_output": 8000,
                "total_cost": 0.75,
                "message_count": 25,
                "cache_creation": 3000,
                "cache_read": 2000,
                "cache_tokens": 5000,
            }
        ]

    @pytest.fixture
    def high_usage_token_data(self):
        """Sample token data with high usage for formatting tests."""
        return [
            {
                "_id": None,
                "total_input": 1500000,  # 1.5M
                "total_output": 800000,  # 800K
                "total_cost": 25.50,
                "message_count": 100,
                "cache_creation": 250000,  # 250K
                "cache_read": 180000,  # 180K
                "cache_tokens": 430000,  # 430K
            }
        ]

    @pytest.fixture
    def zero_token_data(self):
        """Sample token data with zero usage."""
        return [
            {
                "_id": None,
                "total_input": 0,
                "total_output": 0,
                "total_cost": 0.0,
                "message_count": 0,
                "cache_creation": 0,
                "cache_read": 0,
                "cache_tokens": 0,
            }
        ]

    @pytest.fixture
    def no_cache_token_data(self):
        """Sample token data without cache metrics."""
        return [
            {
                "_id": None,
                "total_input": 12000,
                "total_output": 6000,
                "total_cost": 0.60,
                "message_count": 20,
                "cache_creation": 0,
                "cache_read": 0,
                "cache_tokens": 0,
            }
        ]

    @pytest.fixture
    def mixed_cache_token_data(self):
        """Sample token data with varied cache usage patterns."""
        return [
            {
                "_id": None,
                "total_input": 20000,
                "total_output": 10000,
                "total_cost": 1.25,
                "message_count": 30,
                "cache_creation": 8000,
                "cache_read": 1000,  # Low cache hit rate
                "cache_tokens": 9000,
            }
        ]

    # Tests for get_token_efficiency_summary

    @pytest.mark.asyncio
    async def test_get_token_efficiency_summary_basic(
        self, analytics_service, sample_token_data
    ):
        """Test basic functionality of get_token_efficiency_summary."""
        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_token_efficiency_summary()

        # Verify result structure
        assert isinstance(result, TokenEfficiencySummary)
        assert result.total_tokens == 23000  # 15000 + 8000
        assert result.formatted_total == "23K"
        assert result.cost_estimate == 0.75
        assert result.trend == "stable"

        # Verify database was called correctly
        analytics_service.db.messages.aggregate.assert_called_once()
        call_args = analytics_service.db.messages.aggregate.call_args[0][0]

        # Verify pipeline structure
        assert isinstance(call_args, list)
        assert len(call_args) >= 2  # Should have $match and $group stages
        assert "$match" in call_args[0]
        assert "$group" in call_args[1]

    @pytest.mark.asyncio
    async def test_get_token_efficiency_summary_with_session_id(
        self, analytics_service, sample_token_data
    ):
        """Test get_token_efficiency_summary with session_id filter."""
        test_session_id = "test-session-123"

        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_token_efficiency_summary(
            session_id=test_session_id
        )

        # Verify result
        assert isinstance(result, TokenEfficiencySummary)
        assert result.total_tokens == 23000
        assert result.formatted_total == "23K"
        assert result.cost_estimate == 0.75

        # Verify session filter was applied in aggregation pipeline
        call_args = analytics_service.db.messages.aggregate.call_args[0][0]
        match_stage = call_args[0]["$match"]
        assert "sessionId" in match_stage

    @pytest.mark.asyncio
    async def test_get_token_efficiency_summary_with_time_range(
        self, analytics_service, sample_token_data
    ):
        """Test get_token_efficiency_summary with different time ranges."""
        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Test different time ranges
        time_ranges = [
            TimeRange.LAST_24_HOURS,
            TimeRange.LAST_7_DAYS,
            TimeRange.LAST_30_DAYS,
            TimeRange.LAST_90_DAYS,
            TimeRange.ALL_TIME,
        ]

        for time_range in time_ranges:
            analytics_service.db.messages.aggregate.reset_mock()
            analytics_service.db.messages.aggregate.return_value = mock_cursor

            result = await analytics_service.get_token_efficiency_summary(
                time_range=time_range
            )

            # Verify result
            assert isinstance(result, TokenEfficiencySummary)
            assert result.total_tokens == 23000

            # Verify time filter was applied
            call_args = analytics_service.db.messages.aggregate.call_args[0][0]
            match_stage = call_args[0]["$match"]

            if time_range == TimeRange.ALL_TIME:
                # ALL_TIME should not have timestamp filter
                assert "timestamp" not in match_stage or not match_stage.get(
                    "timestamp"
                )
            else:
                # Other ranges should have timestamp filter
                assert "timestamp" in match_stage
                assert "$gte" in match_stage["timestamp"]

    @pytest.mark.asyncio
    async def test_get_token_efficiency_summary_empty_data(self, analytics_service):
        """Test get_token_efficiency_summary with no data."""
        # Mock empty result
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_token_efficiency_summary()

        # Verify empty result
        assert isinstance(result, TokenEfficiencySummary)
        assert result.total_tokens == 0
        assert result.formatted_total == "0"
        assert result.cost_estimate == 0.0
        assert result.trend == "stable"

    @pytest.mark.asyncio
    async def test_get_token_efficiency_summary_high_usage_formatting(
        self, analytics_service, high_usage_token_data
    ):
        """Test token formatting with high usage numbers."""
        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=high_usage_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_token_efficiency_summary()

        # Verify formatting
        assert result.total_tokens == 2300000  # 1.5M + 800K
        assert result.formatted_total == "2.3M"
        assert result.cost_estimate == 25.50

    @pytest.mark.asyncio
    async def test_get_token_efficiency_summary_without_cache_metrics(
        self, analytics_service, sample_token_data
    ):
        """Test get_token_efficiency_summary with cache metrics disabled."""
        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method with cache metrics disabled
        result = await analytics_service.get_token_efficiency_summary(
            include_cache_metrics=False
        )

        # Verify result (cache metrics shouldn't affect summary)
        assert isinstance(result, TokenEfficiencySummary)
        assert result.total_tokens == 23000
        assert result.formatted_total == "23K"
        assert result.cost_estimate == 0.75

    # Tests for get_token_efficiency_detailed

    @pytest.mark.asyncio
    async def test_get_token_efficiency_detailed_basic(
        self, analytics_service, sample_token_data
    ):
        """Test basic functionality of get_token_efficiency_detailed."""
        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_token_efficiency_detailed()

        # Verify result structure
        assert isinstance(result, TokenEfficiencyDetailed)

        # Verify token breakdown
        assert isinstance(result.token_breakdown, TokenBreakdown)
        assert result.token_breakdown.input_tokens == 15000
        assert result.token_breakdown.output_tokens == 8000
        assert result.token_breakdown.cache_creation == 3000
        assert result.token_breakdown.cache_read == 2000
        assert result.token_breakdown.total == 23000

        # Verify efficiency metrics
        assert isinstance(result.efficiency_metrics, TokenEfficiencyMetrics)
        # Cache hit rate: cache_read / (cache_creation + cache_read) * 100 = 40%
        assert result.efficiency_metrics.cache_hit_rate == 40.0
        # Input/output ratio: input / output = 1.875 -> 1.88
        assert result.efficiency_metrics.input_output_ratio == 1.88
        # Avg tokens per message: total / message_count = 920
        assert result.efficiency_metrics.avg_tokens_per_message == 920.0
        # Cost per token: total_cost / total_tokens = ~0.000033
        assert abs(result.efficiency_metrics.cost_per_token - 0.000033) < 0.000001

        # Verify formatted values
        assert isinstance(result.formatted_values, TokenFormattedValues)
        assert result.formatted_values.total == "23K"
        assert result.formatted_values.input == "15K"
        assert result.formatted_values.output == "8K"
        assert result.formatted_values.cache_creation == "3K"
        assert result.formatted_values.cache_read == "2K"

        # Verify metadata
        assert result.session_id is None
        assert result.time_range == TimeRange.LAST_30_DAYS
        assert isinstance(result.generated_at, datetime)

    @pytest.mark.asyncio
    async def test_get_token_efficiency_detailed_with_session_id(
        self, analytics_service, sample_token_data
    ):
        """Test get_token_efficiency_detailed with session_id filter."""
        test_session_id = "test-session-123"
        resolved_session_id = "resolved-uuid-456"

        # Mock session resolution
        analytics_service._resolve_session_id = AsyncMock(
            return_value=resolved_session_id
        )

        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_token_efficiency_detailed(
            session_id=test_session_id, time_range=TimeRange.LAST_7_DAYS
        )

        # Verify session resolution was called
        analytics_service._resolve_session_id.assert_called_once_with(test_session_id)

        # Verify result
        assert isinstance(result, TokenEfficiencyDetailed)
        assert result.session_id == test_session_id
        assert result.time_range == TimeRange.LAST_7_DAYS
        assert result.token_breakdown.total == 23000

    @pytest.mark.asyncio
    async def test_get_token_efficiency_detailed_session_not_found(
        self, analytics_service
    ):
        """Test get_token_efficiency_detailed when session is not found."""
        test_session_id = "nonexistent-session"

        # Mock session resolution to return None
        analytics_service._resolve_session_id = AsyncMock(return_value=None)

        # Call the method
        result = await analytics_service.get_token_efficiency_detailed(
            session_id=test_session_id
        )

        # Verify session resolution was called
        analytics_service._resolve_session_id.assert_called_once_with(test_session_id)

        # Verify empty result is returned
        assert isinstance(result, TokenEfficiencyDetailed)
        assert result.session_id == test_session_id
        assert result.token_breakdown.total == 0
        assert result.efficiency_metrics.cache_hit_rate == 0.0
        assert result.efficiency_metrics.input_output_ratio == 0.0
        assert result.efficiency_metrics.avg_tokens_per_message == 0.0
        assert result.efficiency_metrics.cost_per_token == 0.0
        assert result.formatted_values.total == "0"

        # Verify database aggregation was not called
        analytics_service.db.messages.aggregate.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_token_efficiency_detailed_empty_data(self, analytics_service):
        """Test get_token_efficiency_detailed with no data."""
        # Mock empty result
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_token_efficiency_detailed()

        # Verify empty result structure
        assert isinstance(result, TokenEfficiencyDetailed)
        assert result.token_breakdown.total == 0
        assert result.efficiency_metrics.cache_hit_rate == 0.0
        assert result.efficiency_metrics.input_output_ratio == 0.0
        assert result.efficiency_metrics.avg_tokens_per_message == 0.0
        assert result.efficiency_metrics.cost_per_token == 0.0
        assert all(
            val == "0"
            for val in [
                result.formatted_values.total,
                result.formatted_values.input,
                result.formatted_values.output,
                result.formatted_values.cache_creation,
                result.formatted_values.cache_read,
            ]
        )

    @pytest.mark.asyncio
    async def test_get_token_efficiency_detailed_zero_token_usage(
        self, analytics_service, zero_token_data
    ):
        """Test get_token_efficiency_detailed with zero token usage."""
        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=zero_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_token_efficiency_detailed()

        # Verify result handles zero division gracefully
        assert isinstance(result, TokenEfficiencyDetailed)
        assert result.token_breakdown.total == 0
        assert result.efficiency_metrics.cache_hit_rate == 0.0
        assert (
            result.efficiency_metrics.input_output_ratio == 0.0
        )  # Should handle division by zero
        assert (
            result.efficiency_metrics.cost_per_token == 0.0
        )  # Should handle division by zero

    @pytest.mark.asyncio
    async def test_get_token_efficiency_detailed_no_cache_data(
        self, analytics_service, no_cache_token_data
    ):
        """Test get_token_efficiency_detailed with no cache usage."""
        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=no_cache_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_token_efficiency_detailed()

        # Verify cache metrics are handled correctly
        assert isinstance(result, TokenEfficiencyDetailed)
        assert result.token_breakdown.cache_creation == 0
        assert result.token_breakdown.cache_read == 0
        assert result.efficiency_metrics.cache_hit_rate == 0.0  # No cache usage
        assert result.formatted_values.cache_creation == "0"
        assert result.formatted_values.cache_read == "0"

        # Other metrics should still be calculated
        assert result.token_breakdown.total == 18000  # 12000 + 6000
        assert result.efficiency_metrics.input_output_ratio == 2.0  # 12000 / 6000
        assert result.efficiency_metrics.avg_tokens_per_message == 900.0  # 18000 / 20

    @pytest.mark.asyncio
    async def test_get_token_efficiency_detailed_mixed_cache_usage(
        self, analytics_service, mixed_cache_token_data
    ):
        """Test get_token_efficiency_detailed with varied cache usage patterns."""
        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=mixed_cache_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_token_efficiency_detailed()

        # Verify cache hit rate calculation with low hit rate
        # cache_read / (cache_creation + cache_read) * 100 = ~11.1%
        assert abs(result.efficiency_metrics.cache_hit_rate - 11.1) < 0.1

        # Verify other metrics
        assert result.token_breakdown.total == 30000
        assert result.efficiency_metrics.input_output_ratio == 2.0  # 20000 / 10000
        assert result.efficiency_metrics.avg_tokens_per_message == 1000.0  # 30000 / 30

    @pytest.mark.asyncio
    async def test_get_token_efficiency_detailed_without_cache_metrics(
        self, analytics_service, sample_token_data
    ):
        """Test get_token_efficiency_detailed with cache metrics disabled."""
        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method with cache metrics disabled
        result = await analytics_service.get_token_efficiency_detailed(
            include_cache_metrics=False
        )

        # Verify cache metrics are set to 0 when disabled
        assert isinstance(result, TokenEfficiencyDetailed)
        assert result.token_breakdown.cache_creation == 0
        assert result.token_breakdown.cache_read == 0
        assert result.efficiency_metrics.cache_hit_rate == 0.0
        assert result.formatted_values.cache_creation == "0"
        assert result.formatted_values.cache_read == "0"

        # Other metrics should still be calculated normally
        assert result.token_breakdown.total == 23000
        assert result.efficiency_metrics.input_output_ratio == 1.88

    @pytest.mark.asyncio
    async def test_get_token_efficiency_detailed_high_usage_formatting(
        self, analytics_service, high_usage_token_data
    ):
        """Test detailed token efficiency with high usage for formatting."""
        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=high_usage_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_token_efficiency_detailed()

        # Verify high usage formatting
        assert result.formatted_values.total == "2.3M"  # 2,300,000
        assert result.formatted_values.input == "1.5M"  # 1,500,000
        assert result.formatted_values.output == "800K"  # 800,000
        assert result.formatted_values.cache_creation == "250K"  # 250,000
        assert result.formatted_values.cache_read == "180K"  # 180,000

        # Verify metrics calculations with large numbers
        assert (
            result.efficiency_metrics.cache_hit_rate == 41.9
        )  # 180000 / (250000 + 180000) * 100
        assert result.efficiency_metrics.input_output_ratio == 1.88  # 1500000 / 800000
        assert (
            result.efficiency_metrics.avg_tokens_per_message == 23000.0
        )  # 2300000 / 100

    # Tests for edge cases and error handling

    @pytest.mark.asyncio
    async def test_token_efficiency_aggregation_pipeline_structure(
        self, analytics_service, sample_token_data
    ):
        """Test that aggregation pipelines have expected structure."""
        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call both methods to test pipeline structure
        await analytics_service.get_token_efficiency_summary()
        await analytics_service.get_token_efficiency_detailed()

        # Verify aggregation was called twice
        assert analytics_service.db.messages.aggregate.call_count == 2

        # Check pipeline structure for both calls
        for call in analytics_service.db.messages.aggregate.call_args_list:
            pipeline = call[0][0]
            assert isinstance(pipeline, list)
            assert len(pipeline) >= 2

            # Verify first stage is always $match
            assert "$match" in pipeline[0]

            # Verify second stage is $group
            assert "$group" in pipeline[1]

            # Verify group stage has expected fields
            group_stage = pipeline[1]["$group"]
            assert "_id" in group_stage
            assert "total_input" in group_stage
            assert "total_output" in group_stage
            assert "total_cost" in group_stage
            assert "message_count" in group_stage

    @pytest.mark.asyncio
    async def test_token_efficiency_error_handling(self, analytics_service):
        """Test error handling in token efficiency methods."""
        # Mock database aggregation to raise an exception
        analytics_service.db.messages.aggregate.side_effect = Exception(
            "Database error"
        )

        # Test that exceptions are propagated
        with pytest.raises(Exception, match="Database error"):
            await analytics_service.get_token_efficiency_summary()

        with pytest.raises(Exception, match="Database error"):
            await analytics_service.get_token_efficiency_detailed()

    @pytest.mark.asyncio
    async def test_token_efficiency_with_null_values(self, analytics_service):
        """Test handling of null/missing values in aggregation results."""
        # Sample data with null/missing values
        sample_data_with_nulls = [
            {
                "_id": None,
                "total_input": None,  # Null input
                "total_output": 5000,
                "total_cost": None,  # Null cost
                "message_count": 10,
                "cache_creation": None,  # Null cache
                "cache_read": 0,
                "cache_tokens": None,
            }
        ]

        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_data_with_nulls)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Test summary (should handle nulls gracefully via _safe_float)
        summary_result = await analytics_service.get_token_efficiency_summary()
        assert summary_result.total_tokens == 5000  # Only output tokens counted
        assert summary_result.cost_estimate == 0.0  # Null cost becomes 0

        # Reset mock for detailed test
        analytics_service.db.messages.aggregate.reset_mock()
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Test detailed (should handle nulls gracefully)
        detailed_result = await analytics_service.get_token_efficiency_detailed()
        assert detailed_result.token_breakdown.input_tokens == 0  # Null becomes 0
        assert detailed_result.token_breakdown.output_tokens == 5000
        assert detailed_result.token_breakdown.cache_creation == 0  # Null becomes 0
        assert detailed_result.efficiency_metrics.input_output_ratio == 0.0  # 0 / 5000

    @pytest.mark.asyncio
    async def test_cache_hit_rate_edge_cases(self, analytics_service):
        """Test cache hit rate calculations with edge cases."""
        test_cases = [
            # (cache_creation, cache_read, expected_hit_rate)
            (0, 0, 0.0),  # No cache usage
            (1000, 0, 0.0),  # Only creation, no reads
            (0, 1000, 100.0),  # Only reads (edge case)
            (1000, 1000, 50.0),  # Equal creation and reads
            (100, 900, 90.0),  # High hit rate
            (9000, 1000, 10.0),  # Low hit rate
        ]

        for cache_creation, cache_read, expected_hit_rate in test_cases:
            sample_data = [
                {
                    "_id": None,
                    "total_input": 10000,
                    "total_output": 5000,
                    "total_cost": 0.5,
                    "message_count": 10,
                    "cache_creation": cache_creation,
                    "cache_read": cache_read,
                    "cache_tokens": cache_creation + cache_read,
                }
            ]

            # Mock the database aggregation
            mock_cursor = AsyncMock()
            mock_cursor.to_list = AsyncMock(return_value=sample_data)
            analytics_service.db.messages.aggregate.return_value = mock_cursor

            # Call the method
            result = await analytics_service.get_token_efficiency_detailed()

            # Verify cache hit rate
            assert (
                abs(result.efficiency_metrics.cache_hit_rate - expected_hit_rate) < 0.1
            ), (
                f"Expected {expected_hit_rate}% but got {result.efficiency_metrics.cache_hit_rate}% "
                f"for creation={cache_creation}, read={cache_read}"
            )

            # Verify cache hit rate is within valid bounds
            assert 0.0 <= result.efficiency_metrics.cache_hit_rate <= 100.0

    def test_format_token_count_functionality(self, analytics_service):
        """Test the _format_token_count method with various values."""
        # Test small numbers (under 1K)
        assert analytics_service._format_token_count(0) == "0"
        assert analytics_service._format_token_count(42) == "42"
        assert analytics_service._format_token_count(999) == "999"

        # Test K formatting (1K to 999K)
        assert analytics_service._format_token_count(1000) == "1K"
        assert analytics_service._format_token_count(1500) == "1K"  # Integer division
        assert analytics_service._format_token_count(45000) == "45K"
        assert analytics_service._format_token_count(999999) == "999K"

        # Test M formatting (1M and above)
        assert analytics_service._format_token_count(1000000) == "1.0M"
        assert analytics_service._format_token_count(1500000) == "1.5M"
        assert analytics_service._format_token_count(2300000) == "2.3M"
        assert analytics_service._format_token_count(10000000) == "10.0M"

    @pytest.mark.asyncio
    async def test_token_efficiency_time_range_filters(
        self, analytics_service, sample_token_data
    ):
        """Test that time range filters are properly applied to aggregation pipelines."""
        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Test each time range
        time_ranges_with_expected_filters = [
            (TimeRange.LAST_24_HOURS, True),
            (TimeRange.LAST_7_DAYS, True),
            (TimeRange.LAST_30_DAYS, True),
            (TimeRange.LAST_90_DAYS, True),
            (TimeRange.LAST_YEAR, True),
            (TimeRange.ALL_TIME, False),  # Should not have timestamp filter
        ]

        for time_range, should_have_timestamp in time_ranges_with_expected_filters:
            analytics_service.db.messages.aggregate.reset_mock()
            analytics_service.db.messages.aggregate.return_value = mock_cursor

            # Test both summary and detailed methods
            await analytics_service.get_token_efficiency_summary(time_range=time_range)
            await analytics_service.get_token_efficiency_detailed(time_range=time_range)

            # Verify both calls have appropriate filters
            assert analytics_service.db.messages.aggregate.call_count == 2

            for call in analytics_service.db.messages.aggregate.call_args_list:
                pipeline = call[0][0]
                match_stage = pipeline[0]["$match"]

                if should_have_timestamp:
                    assert "timestamp" in match_stage
                    assert "$gte" in match_stage["timestamp"]
                    assert isinstance(match_stage["timestamp"]["$gte"], datetime)
                else:
                    # ALL_TIME should not have timestamp filter or it should be empty
                    assert "timestamp" not in match_stage or not match_stage.get(
                        "timestamp"
                    )

    @pytest.mark.asyncio
    async def test_token_efficiency_precision_and_rounding(self, analytics_service):
        """Test precision and rounding in efficiency calculations."""
        # Sample data designed to test rounding precision
        sample_data = [
            {
                "_id": None,
                "total_input": 7777,
                "total_output": 3333,
                "total_cost": 0.123456789,
                "message_count": 13,
                "cache_creation": 1111,
                "cache_read": 2222,
                "cache_tokens": 3333,
            }
        ]

        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_token_efficiency_detailed()

        # Verify rounding precision
        # Cache hit rate should be rounded to 1 decimal place
        expected_cache_hit_rate = (2222 / (1111 + 2222)) * 100  # ~66.66...%
        assert (
            abs(
                result.efficiency_metrics.cache_hit_rate
                - round(expected_cache_hit_rate, 1)
            )
            < 0.01
        )

        # Input/output ratio should be rounded to 2 decimal places
        expected_ratio = 7777 / 3333  # ~2.333...
        assert (
            abs(result.efficiency_metrics.input_output_ratio - round(expected_ratio, 2))
            < 0.01
        )

        # Avg tokens per message should be rounded to 1 decimal place
        expected_avg = 11110 / 13  # ~854.6...
        assert (
            abs(
                result.efficiency_metrics.avg_tokens_per_message
                - round(expected_avg, 1)
            )
            < 0.01
        )

        # Cost per token should be rounded to 6 decimal places
        expected_cost_per_token = 0.123456789 / 11110  # Very small number
        assert (
            abs(
                result.efficiency_metrics.cost_per_token
                - round(expected_cost_per_token, 6)
            )
            < 0.0000001
        )

    @pytest.mark.asyncio
    async def test_token_efficiency_integration_with_project_filters(
        self, analytics_service, sample_token_data
    ):
        """Test integration scenarios that might include project filtering (via session resolution)."""
        test_session_id = "project-session-123"
        resolved_session_id = "resolved-project-uuid"

        # Mock session resolution (simulating project-based session lookup)
        analytics_service._resolve_session_id = AsyncMock(
            return_value=resolved_session_id
        )

        # Mock the database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_token_data)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Test both methods with session (which might be project-related)
        summary_result = await analytics_service.get_token_efficiency_summary(
            session_id=test_session_id, time_range=TimeRange.LAST_7_DAYS
        )

        detailed_result = await analytics_service.get_token_efficiency_detailed(
            session_id=test_session_id,
            time_range=TimeRange.LAST_7_DAYS,
            include_cache_metrics=True,
        )

        # Verify session resolution was called only for detailed method (summary uses session_id directly)
        assert analytics_service._resolve_session_id.call_count == 1

        # Verify results are consistent between summary and detailed
        assert summary_result.total_tokens == detailed_result.token_breakdown.total
        assert summary_result.cost_estimate == 0.75
        assert detailed_result.session_id == test_session_id
        assert detailed_result.time_range == TimeRange.LAST_7_DAYS

        # Verify aggregation pipelines included session filter
        call_args_list = analytics_service.db.messages.aggregate.call_args_list
        assert len(call_args_list) == 2

        # First call is from summary method - should use original session_id
        summary_pipeline = call_args_list[0][0][0]
        summary_match_stage = summary_pipeline[0]["$match"]
        assert "sessionId" in summary_match_stage
        assert summary_match_stage["sessionId"] == test_session_id

        # Second call is from detailed method - should use resolved session_id
        detailed_pipeline = call_args_list[1][0][0]
        detailed_match_stage = detailed_pipeline[0]["$match"]
        assert "sessionId" in detailed_match_stage
        assert detailed_match_stage["sessionId"] == resolved_session_id
