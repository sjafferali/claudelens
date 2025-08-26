"""Comprehensive tests for analytics service session depth analysis functionality."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from app.schemas.analytics import (
    ConversationPattern,
    DepthCorrelations,
    DepthDistribution,
    DepthRecommendations,
    SessionDepthAnalytics,
    TimeRange,
)
from app.services.analytics import AnalyticsService


class TestAnalyticsServiceSessionDepth:
    """Test analytics service session depth analysis functionality."""

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
    def sample_messages_simple(self):
        """Sample messages for a simple conversation tree."""
        base_time = datetime.now(UTC)
        return [
            {
                "uuid": "msg1",
                "sessionId": "session1",
                "parentUuid": None,
                "isSidechain": False,
                "costUsd": 0.01,
                "durationMs": 1000,
                "timestamp": base_time,
                "type": "user",
            },
            {
                "uuid": "msg2",
                "sessionId": "session1",
                "parentUuid": "msg1",
                "isSidechain": False,
                "costUsd": 0.02,
                "durationMs": 2000,
                "timestamp": base_time + timedelta(seconds=1),
                "type": "assistant",
            },
            {
                "uuid": "msg3",
                "sessionId": "session1",
                "parentUuid": "msg2",
                "isSidechain": False,
                "costUsd": 0.01,
                "durationMs": 1500,
                "timestamp": base_time + timedelta(seconds=2),
                "type": "user",
            },
            {
                "uuid": "msg4",
                "sessionId": "session1",
                "parentUuid": "msg3",
                "isSidechain": False,
                "costUsd": 0.03,
                "durationMs": 2500,
                "timestamp": base_time + timedelta(seconds=3),
                "type": "assistant",
            },
        ]

    @pytest.fixture
    def sample_messages_with_branches(self):
        """Sample messages with branching conversation."""
        base_time = datetime.now(UTC)
        return [
            # Main thread
            {
                "uuid": "msg1",
                "sessionId": "session2",
                "parentUuid": None,
                "isSidechain": False,
                "costUsd": 0.01,
                "durationMs": 1000,
                "timestamp": base_time,
                "type": "user",
            },
            {
                "uuid": "msg2",
                "sessionId": "session2",
                "parentUuid": "msg1",
                "isSidechain": False,
                "costUsd": 0.02,
                "durationMs": 2000,
                "timestamp": base_time + timedelta(seconds=1),
                "type": "assistant",
            },
            # Branch 1 from msg2
            {
                "uuid": "msg3",
                "sessionId": "session2",
                "parentUuid": "msg2",
                "isSidechain": False,
                "costUsd": 0.015,
                "durationMs": 1500,
                "timestamp": base_time + timedelta(seconds=2),
                "type": "user",
            },
            {
                "uuid": "msg4",
                "sessionId": "session2",
                "parentUuid": "msg3",
                "isSidechain": False,
                "costUsd": 0.025,
                "durationMs": 2200,
                "timestamp": base_time + timedelta(seconds=3),
                "type": "assistant",
            },
            # Branch 2 from msg2 (alternative exploration)
            {
                "uuid": "msg5",
                "sessionId": "session2",
                "parentUuid": "msg2",
                "isSidechain": False,
                "costUsd": 0.012,
                "durationMs": 1200,
                "timestamp": base_time + timedelta(seconds=4),
                "type": "user",
            },
            # Deep continuation from msg4
            {
                "uuid": "msg6",
                "sessionId": "session2",
                "parentUuid": "msg4",
                "isSidechain": False,
                "costUsd": 0.018,
                "durationMs": 1800,
                "timestamp": base_time + timedelta(seconds=5),
                "type": "user",
            },
            {
                "uuid": "msg7",
                "sessionId": "session2",
                "parentUuid": "msg6",
                "isSidechain": False,
                "costUsd": 0.035,
                "durationMs": 3000,
                "timestamp": base_time + timedelta(seconds=6),
                "type": "assistant",
            },
        ]

    @pytest.fixture
    def sample_messages_with_sidechains(self):
        """Sample messages with sidechain conversations."""
        base_time = datetime.now(UTC)
        return [
            # Main thread
            {
                "uuid": "msg1",
                "sessionId": "session3",
                "parentUuid": None,
                "isSidechain": False,
                "costUsd": 0.01,
                "durationMs": 1000,
                "timestamp": base_time,
                "type": "user",
            },
            {
                "uuid": "msg2",
                "sessionId": "session3",
                "parentUuid": "msg1",
                "isSidechain": False,
                "costUsd": 0.02,
                "durationMs": 2000,
                "timestamp": base_time + timedelta(seconds=1),
                "type": "assistant",
            },
            # Sidechain from msg2
            {
                "uuid": "msg3",
                "sessionId": "session3",
                "parentUuid": "msg2",
                "isSidechain": True,
                "costUsd": 0.005,
                "durationMs": 500,
                "timestamp": base_time + timedelta(seconds=2),
                "type": "user",
            },
            {
                "uuid": "msg4",
                "sessionId": "session3",
                "parentUuid": "msg3",
                "isSidechain": True,
                "costUsd": 0.008,
                "durationMs": 800,
                "timestamp": base_time + timedelta(seconds=3),
                "type": "assistant",
            },
            # Continue main thread
            {
                "uuid": "msg5",
                "sessionId": "session3",
                "parentUuid": "msg2",
                "isSidechain": False,
                "costUsd": 0.015,
                "durationMs": 1500,
                "timestamp": base_time + timedelta(seconds=4),
                "type": "user",
            },
        ]

    @pytest.fixture
    def sample_multi_session_messages(self):
        """Sample messages from multiple sessions for distribution testing."""
        base_time = datetime.now(UTC)
        messages = []

        # Session 1: shallow (depth 2)
        for i in range(2):
            messages.append(
                {
                    "uuid": f"s1_msg{i + 1}",
                    "sessionId": "session1",
                    "parentUuid": f"s1_msg{i}" if i > 0 else None,
                    "isSidechain": False,
                    "costUsd": 0.01 * (i + 1),
                    "durationMs": 1000 * (i + 1),
                    "timestamp": base_time + timedelta(seconds=i),
                    "type": "assistant" if i % 2 == 1 else "user",
                }
            )

        # Session 2: medium depth (depth 4)
        for i in range(4):
            messages.append(
                {
                    "uuid": f"s2_msg{i + 1}",
                    "sessionId": "session2",
                    "parentUuid": f"s2_msg{i}" if i > 0 else None,
                    "isSidechain": False,
                    "costUsd": 0.02 * (i + 1),
                    "durationMs": 1500 * (i + 1),
                    "timestamp": base_time + timedelta(minutes=1, seconds=i),
                    "type": "assistant" if i % 2 == 1 else "user",
                }
            )

        # Session 3: deep (depth 8)
        for i in range(8):
            messages.append(
                {
                    "uuid": f"s3_msg{i + 1}",
                    "sessionId": "session3",
                    "parentUuid": f"s3_msg{i}" if i > 0 else None,
                    "isSidechain": False,
                    "costUsd": 0.03 * (i + 1),
                    "durationMs": 2000 * (i + 1),
                    "timestamp": base_time + timedelta(minutes=2, seconds=i),
                    "type": "assistant" if i % 2 == 1 else "user",
                }
            )

        return messages

    @pytest.mark.asyncio
    async def test_get_session_depth_analytics_basic(
        self, analytics_service, sample_messages_simple
    ):
        """Test basic session depth analytics functionality."""
        # Mock database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_messages_simple)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_session_depth_analytics(
            TimeRange.LAST_7_DAYS
        )

        # Verify result structure
        assert isinstance(result, SessionDepthAnalytics)
        assert isinstance(result.depth_distribution, list)
        assert isinstance(result.depth_correlations, DepthCorrelations)
        assert isinstance(result.patterns, list)
        assert isinstance(result.recommendations, DepthRecommendations)
        assert result.time_range == TimeRange.LAST_7_DAYS

        # Verify depth distribution has data
        assert len(result.depth_distribution) > 0
        depth_dist = result.depth_distribution[0]
        assert depth_dist.depth == 4  # Simple linear conversation has depth 4
        assert depth_dist.session_count == 1
        assert depth_dist.percentage == 100.0

    @pytest.mark.asyncio
    async def test_get_session_depth_analytics_with_project_filter(
        self, analytics_service, sample_messages_simple
    ):
        """Test session depth analytics with project ID filter."""
        test_project_id = str(ObjectId())

        # Mock sessions query for project
        class MockAsyncCursor:
            def __init__(self, data):
                self.data = data

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.data:
                    return self.data.pop(0)
                raise StopAsyncIteration

        mock_sessions_cursor = MockAsyncCursor([{"sessionId": "session1"}])
        analytics_service.db.sessions.find.return_value = mock_sessions_cursor

        # Mock messages aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_messages_simple)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_session_depth_analytics(
            TimeRange.LAST_7_DAYS, project_id=test_project_id
        )

        # Verify result
        assert isinstance(result, SessionDepthAnalytics)
        assert len(result.depth_distribution) > 0

        # Verify sessions query was called correctly
        analytics_service.db.sessions.find.assert_called_once_with(
            {"projectId": ObjectId(test_project_id)}
        )

    @pytest.mark.asyncio
    async def test_get_session_depth_analytics_no_project_sessions(
        self, analytics_service
    ):
        """Test session depth analytics when no sessions found for project."""
        test_project_id = str(ObjectId())

        # Mock empty sessions result
        class MockAsyncCursor:
            def __init__(self, data):
                self.data = data

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.data:
                    return self.data.pop(0)
                raise StopAsyncIteration

        mock_sessions_cursor = MockAsyncCursor([])  # Empty list
        analytics_service.db.sessions.find.return_value = mock_sessions_cursor

        # Call the method
        result = await analytics_service.get_session_depth_analytics(
            TimeRange.LAST_7_DAYS, project_id=test_project_id
        )

        # Verify empty result
        assert isinstance(result, SessionDepthAnalytics)
        assert result.depth_distribution == []
        assert result.depth_correlations.depth_vs_cost == 0.0
        assert result.depth_correlations.depth_vs_duration == 0.0
        assert result.depth_correlations.depth_vs_success == 0.0
        assert result.patterns == []
        assert result.recommendations.optimal_depth_range == (0, 0)
        assert result.recommendations.warning_threshold == 0
        assert "No data available for this project" in result.recommendations.tips

    @pytest.mark.asyncio
    async def test_get_session_depth_analytics_empty_data(self, analytics_service):
        """Test session depth analytics with no matching messages."""
        # Mock empty messages result
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_session_depth_analytics(
            TimeRange.LAST_7_DAYS
        )

        # Verify empty result
        assert isinstance(result, SessionDepthAnalytics)
        assert result.depth_distribution == []
        assert result.depth_correlations.depth_vs_cost == 0.0
        assert result.patterns == []
        assert (
            "No conversations found matching the specified criteria"
            in result.recommendations.tips
        )

    @pytest.mark.asyncio
    async def test_get_session_depth_analytics_with_min_depth_filter(
        self, analytics_service, sample_multi_session_messages
    ):
        """Test session depth analytics with minimum depth filter."""
        # Mock database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_multi_session_messages)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call with min_depth=5 (should only include session3 with depth 8)
        result = await analytics_service.get_session_depth_analytics(
            TimeRange.LAST_7_DAYS, min_depth=5
        )

        # Verify only deep sessions are included
        assert isinstance(result, SessionDepthAnalytics)
        assert len(result.depth_distribution) == 1
        assert result.depth_distribution[0].depth == 8
        assert result.depth_distribution[0].session_count == 1

    @pytest.mark.asyncio
    async def test_get_session_depth_analytics_exclude_sidechains(
        self, analytics_service, sample_messages_with_sidechains
    ):
        """Test session depth analytics excluding sidechains."""
        # Mock database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_messages_with_sidechains)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call with include_sidechains=False
        result = await analytics_service.get_session_depth_analytics(
            TimeRange.LAST_7_DAYS, include_sidechains=False
        )

        # Verify result (should only count main thread, depth=3)
        assert isinstance(result, SessionDepthAnalytics)
        assert len(result.depth_distribution) > 0
        # Main thread: msg1 -> msg2 -> msg5 = depth 3
        assert result.depth_distribution[0].depth == 3

    @pytest.mark.asyncio
    async def test_get_session_depth_analytics_include_sidechains(
        self, analytics_service, sample_messages_with_sidechains
    ):
        """Test session depth analytics including sidechains."""
        # Mock database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_messages_with_sidechains)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call with include_sidechains=True
        result = await analytics_service.get_session_depth_analytics(
            TimeRange.LAST_7_DAYS, include_sidechains=True
        )

        # Verify result includes sidechain depths
        assert isinstance(result, SessionDepthAnalytics)
        assert len(result.depth_distribution) > 0
        # Should include sidechain depth (msg1 -> msg2 -> msg3 -> msg4 = depth 4)
        # Or main thread depth (msg1 -> msg2 -> msg5 = depth 3)
        # Max should be 4
        max_depth = max(dist.depth for dist in result.depth_distribution)
        assert max_depth == 4

    @pytest.mark.asyncio
    async def test_get_session_depth_analytics_correlations(
        self, analytics_service, sample_multi_session_messages
    ):
        """Test depth correlation calculations."""
        # Mock database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_multi_session_messages)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_session_depth_analytics(
            TimeRange.LAST_7_DAYS
        )

        # Verify correlations
        assert isinstance(result.depth_correlations, DepthCorrelations)
        assert -1.0 <= result.depth_correlations.depth_vs_cost <= 1.0
        assert -1.0 <= result.depth_correlations.depth_vs_duration <= 1.0
        assert -1.0 <= result.depth_correlations.depth_vs_success <= 1.0

        # With our test data, deeper sessions have higher costs, so correlation should be positive
        assert result.depth_correlations.depth_vs_cost > 0

    @pytest.mark.asyncio
    async def test_get_session_depth_analytics_patterns(
        self, analytics_service, sample_messages_with_branches
    ):
        """Test conversation pattern identification."""
        # Mock database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_messages_with_branches)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_session_depth_analytics(
            TimeRange.LAST_7_DAYS
        )

        # Verify patterns
        assert isinstance(result.patterns, list)
        assert len(result.patterns) > 0

        for pattern in result.patterns:
            assert isinstance(pattern, ConversationPattern)
            assert pattern.pattern_name in [
                "shallow-wide",
                "deep-narrow",
                "balanced",
                "linear",
            ]
            assert pattern.frequency > 0
            assert pattern.avg_cost >= 0
            assert len(pattern.typical_use_case) > 0

    @pytest.mark.asyncio
    async def test_get_session_depth_analytics_recommendations(
        self, analytics_service, sample_multi_session_messages
    ):
        """Test depth recommendations generation."""
        # Mock database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_multi_session_messages)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_session_depth_analytics(
            TimeRange.LAST_7_DAYS
        )

        # Verify recommendations
        assert isinstance(result.recommendations, DepthRecommendations)
        assert len(result.recommendations.optimal_depth_range) == 2
        assert (
            result.recommendations.optimal_depth_range[0]
            <= result.recommendations.optimal_depth_range[1]
        )
        assert result.recommendations.warning_threshold > 0
        assert len(result.recommendations.tips) > 0

    def test_calculate_conversation_depths_simple(
        self, analytics_service, sample_messages_simple
    ):
        """Test conversation depth calculation for simple linear conversation."""
        depths = analytics_service._calculate_conversation_depths(
            sample_messages_simple, True
        )

        # Verify depths
        assert len(depths) == 4
        assert depths["msg1"] == 1  # Root message
        assert depths["msg2"] == 2  # Child of msg1
        assert depths["msg3"] == 3  # Child of msg2
        assert depths["msg4"] == 4  # Child of msg3

    def test_calculate_conversation_depths_with_branches(
        self, analytics_service, sample_messages_with_branches
    ):
        """Test conversation depth calculation with branching."""
        depths = analytics_service._calculate_conversation_depths(
            sample_messages_with_branches, True
        )

        # Verify depths for branching conversation
        assert depths["msg1"] == 1  # Root
        assert depths["msg2"] == 2  # Child of msg1
        assert depths["msg3"] == 3  # Child of msg2 (branch 1)
        assert depths["msg4"] == 4  # Child of msg3 (branch 1 continues)
        assert depths["msg5"] == 3  # Child of msg2 (branch 2)
        assert depths["msg6"] == 5  # Child of msg4 (deeper continuation)
        assert depths["msg7"] == 6  # Child of msg6 (deepest)

    def test_calculate_conversation_depths_exclude_sidechains(
        self, analytics_service, sample_messages_with_sidechains
    ):
        """Test conversation depth calculation excluding sidechains."""
        depths = analytics_service._calculate_conversation_depths(
            sample_messages_with_sidechains, False
        )

        # Verify sidechain messages have depth 0
        assert depths["msg1"] == 1
        assert depths["msg2"] == 2
        assert depths["msg3"] == 0  # Sidechain excluded
        assert depths["msg4"] == 0  # Sidechain excluded
        assert depths["msg5"] == 3  # Main thread continues

    def test_calculate_conversation_depths_include_sidechains(
        self, analytics_service, sample_messages_with_sidechains
    ):
        """Test conversation depth calculation including sidechains."""
        depths = analytics_service._calculate_conversation_depths(
            sample_messages_with_sidechains, True
        )

        # Verify sidechain messages have proper depths
        assert depths["msg1"] == 1
        assert depths["msg2"] == 2
        assert depths["msg3"] == 3  # Sidechain included
        assert depths["msg4"] == 4  # Sidechain included
        assert depths["msg5"] == 3  # Main thread continues

    def test_calculate_conversation_depths_orphaned_messages(self, analytics_service):
        """Test conversation depth calculation with orphaned messages."""
        messages = [
            {
                "uuid": "msg1",
                "sessionId": "session1",
                "parentUuid": None,
                "isSidechain": False,
            },
            {
                "uuid": "msg2",
                "sessionId": "session1",
                "parentUuid": "nonexistent",  # Parent doesn't exist
                "isSidechain": False,
            },
        ]

        depths = analytics_service._calculate_conversation_depths(messages, True)

        # Root message should have depth 1
        assert depths["msg1"] == 1
        # Orphaned message gets depth = parent_depth + 1 = 0 + 1 = 1 (since parent doesn't exist, returns 0)
        assert depths["msg2"] == 1

    def test_calculate_depth_distribution(self, analytics_service):
        """Test depth distribution calculation."""
        depth_stats = [
            {"max_depth": 2, "cost": 0.10, "message_count": 5},
            {"max_depth": 2, "cost": 0.15, "message_count": 6},
            {"max_depth": 4, "cost": 0.25, "message_count": 8},
            {"max_depth": 6, "cost": 0.40, "message_count": 12},
        ]

        distribution = analytics_service._calculate_depth_distribution(depth_stats)

        # Verify distribution
        assert len(distribution) == 3  # Depths 2, 4, 6

        # Check depth 2 (2 sessions)
        depth_2 = next(d for d in distribution if d.depth == 2)
        assert depth_2.session_count == 2
        assert depth_2.avg_cost == 0.125  # (0.10 + 0.15) / 2
        assert depth_2.avg_messages == 5  # (5 + 6) / 2 = 5.5, rounded to int
        assert depth_2.percentage == 50.0  # 2/4 * 100

        # Check depth 4 (1 session)
        depth_4 = next(d for d in distribution if d.depth == 4)
        assert depth_4.session_count == 1
        assert depth_4.avg_cost == 0.25
        assert depth_4.percentage == 25.0  # 1/4 * 100

    def test_calculate_depth_correlations_sufficient_data(self, analytics_service):
        """Test depth correlation calculation with sufficient data."""
        depth_stats = [
            {"max_depth": 2, "cost": 0.10, "duration": 1000, "success_rate": 90.0},
            {"max_depth": 4, "cost": 0.20, "duration": 2000, "success_rate": 85.0},
            {"max_depth": 6, "cost": 0.30, "duration": 3000, "success_rate": 80.0},
            {"max_depth": 8, "cost": 0.40, "duration": 4000, "success_rate": 75.0},
        ]

        correlations = analytics_service._calculate_depth_correlations(depth_stats)

        # Verify correlations
        assert isinstance(correlations, DepthCorrelations)
        assert -1.0 <= correlations.depth_vs_cost <= 1.0
        assert -1.0 <= correlations.depth_vs_duration <= 1.0
        assert -1.0 <= correlations.depth_vs_success <= 1.0

        # Perfect positive correlation for cost and duration
        assert correlations.depth_vs_cost == 1.0
        assert correlations.depth_vs_duration == 1.0

        # Perfect negative correlation for success
        assert correlations.depth_vs_success == -1.0

    def test_calculate_depth_correlations_insufficient_data(self, analytics_service):
        """Test depth correlation calculation with insufficient data."""
        depth_stats = [
            {"max_depth": 2, "cost": 0.10, "duration": 1000, "success_rate": 90.0}
        ]

        correlations = analytics_service._calculate_depth_correlations(depth_stats)

        # Should return zero correlations
        assert correlations.depth_vs_cost == 0.0
        assert correlations.depth_vs_duration == 0.0
        assert correlations.depth_vs_success == 0.0

    def test_calculate_depth_correlations_missing_duration_data(
        self, analytics_service
    ):
        """Test depth correlation calculation with missing duration data."""
        depth_stats = [
            {"max_depth": 2, "cost": 0.10, "duration": 0, "success_rate": 90.0},
            {"max_depth": 4, "cost": 0.20, "duration": 0, "success_rate": 85.0},
        ]

        correlations = analytics_service._calculate_depth_correlations(depth_stats)

        # Duration correlation should be 0 due to no valid duration data
        assert correlations.depth_vs_duration == 0.0
        # Other correlations should still work
        assert correlations.depth_vs_cost == 1.0
        assert correlations.depth_vs_success == -1.0

    def test_identify_conversation_patterns(self, analytics_service):
        """Test conversation pattern identification."""
        depth_stats = [
            # Shallow-wide: depth <= 3 and branch_count >= 2
            {"max_depth": 3, "branch_count": 3, "cost": 0.15},
            {"max_depth": 2, "branch_count": 2, "cost": 0.12},
            # Deep-narrow: depth > 6 and branch_count <= 1
            {"max_depth": 8, "branch_count": 1, "cost": 0.45},
            {"max_depth": 10, "branch_count": 0, "cost": 0.50},
            # Balanced: 3 < depth <= 6 and branch_count >= 1
            {"max_depth": 5, "branch_count": 2, "cost": 0.30},
            {"max_depth": 4, "branch_count": 1, "cost": 0.25},
            # Linear: branch_count == 0
            {"max_depth": 3, "branch_count": 0, "cost": 0.18},
        ]

        patterns = analytics_service._identify_conversation_patterns(depth_stats)

        # Verify patterns
        pattern_names = [p.pattern_name for p in patterns]
        assert "shallow-wide" in pattern_names
        assert "deep-narrow" in pattern_names
        assert "balanced" in pattern_names
        assert "linear" in pattern_names

        # Check shallow-wide pattern
        shallow_wide = next(p for p in patterns if p.pattern_name == "shallow-wide")
        assert shallow_wide.frequency == 2
        assert shallow_wide.avg_cost == 0.135  # (0.15 + 0.12) / 2

        # Check deep-narrow pattern
        deep_narrow = next(p for p in patterns if p.pattern_name == "deep-narrow")
        assert deep_narrow.frequency == 2
        assert deep_narrow.avg_cost == 0.475  # (0.45 + 0.50) / 2

        # Check linear pattern (includes sessions with branch_count == 0)
        linear = next(p for p in patterns if p.pattern_name == "linear")
        assert linear.frequency == 2  # One deep-narrow + one standalone linear

    def test_identify_conversation_patterns_empty_data(self, analytics_service):
        """Test conversation pattern identification with empty data."""
        patterns = analytics_service._identify_conversation_patterns([])
        assert patterns == []

    def test_generate_depth_recommendations_basic(self, analytics_service):
        """Test depth recommendations generation."""
        depth_stats = [
            {"max_depth": 2, "cost": 0.10, "branch_count": 1},
            {"max_depth": 4, "cost": 0.15, "branch_count": 2},
            {"max_depth": 6, "cost": 0.25, "branch_count": 1},
            {"max_depth": 8, "cost": 0.40, "branch_count": 0},
        ]

        distribution = [
            DepthDistribution(
                depth=2, session_count=1, avg_cost=0.10, avg_messages=5, percentage=25.0
            ),
            DepthDistribution(
                depth=4, session_count=1, avg_cost=0.15, avg_messages=8, percentage=25.0
            ),
            DepthDistribution(
                depth=6,
                session_count=1,
                avg_cost=0.25,
                avg_messages=12,
                percentage=25.0,
            ),
            DepthDistribution(
                depth=8,
                session_count=1,
                avg_cost=0.40,
                avg_messages=16,
                percentage=25.0,
            ),
        ]

        recommendations = analytics_service._generate_depth_recommendations(
            depth_stats, distribution
        )

        # Verify recommendations
        assert isinstance(recommendations, DepthRecommendations)
        assert len(recommendations.optimal_depth_range) == 2
        assert (
            recommendations.optimal_depth_range[0]
            <= recommendations.optimal_depth_range[1]
        )
        assert (
            recommendations.warning_threshold >= recommendations.optimal_depth_range[1]
        )
        assert len(recommendations.tips) > 0

        # With average cost = 0.225, efficient depths should be 2 and 4 (below average)
        assert recommendations.optimal_depth_range == (2, 4)

    def test_generate_depth_recommendations_high_costs(self, analytics_service):
        """Test depth recommendations with high-cost sessions."""
        depth_stats = [
            {"max_depth": 4, "cost": 1.5, "branch_count": 1},  # High cost session
            {"max_depth": 6, "cost": 2.0, "branch_count": 2},  # High cost session
            {"max_depth": 8, "cost": 0.5, "branch_count": 0},  # Normal cost session
        ]

        distribution = [
            DepthDistribution(
                depth=4, session_count=1, avg_cost=1.5, avg_messages=8, percentage=33.3
            ),
            DepthDistribution(
                depth=6, session_count=1, avg_cost=2.0, avg_messages=12, percentage=33.3
            ),
            DepthDistribution(
                depth=8, session_count=1, avg_cost=0.5, avg_messages=16, percentage=33.3
            ),
        ]

        recommendations = analytics_service._generate_depth_recommendations(
            depth_stats, distribution
        )

        # Should recommend optimizing high-cost sessions
        tips = " ".join(recommendations.tips)
        assert "High-cost sessions detected" in tips or "conversation structure" in tips

    def test_generate_depth_recommendations_very_deep_conversations(
        self, analytics_service
    ):
        """Test depth recommendations with very deep conversations."""
        depth_stats = [
            {
                "max_depth": 20,
                "cost": 0.50,
                "branch_count": 0,
            },  # Very deep conversation
            {"max_depth": 12, "cost": 0.30, "branch_count": 1},  # Deep conversation
            {"max_depth": 4, "cost": 0.10, "branch_count": 2},  # Normal conversation
        ]

        distribution = [
            DepthDistribution(
                depth=4, session_count=1, avg_cost=0.10, avg_messages=8, percentage=33.3
            ),
            DepthDistribution(
                depth=12,
                session_count=1,
                avg_cost=0.30,
                avg_messages=24,
                percentage=33.3,
            ),
            DepthDistribution(
                depth=20,
                session_count=1,
                avg_cost=0.50,
                avg_messages=40,
                percentage=33.3,
            ),
        ]

        recommendations = analytics_service._generate_depth_recommendations(
            depth_stats, distribution
        )

        # Should recommend breaking up complex conversations
        tips = " ".join(recommendations.tips)
        assert (
            "Very deep conversations detected" in tips
            or "breaking complex conversations" in tips
            or "all iterations were necessary" in tips
        )

    def test_generate_depth_recommendations_linear_conversations(
        self, analytics_service
    ):
        """Test depth recommendations with mostly linear conversations."""
        depth_stats = [
            {"max_depth": 4, "cost": 0.20, "branch_count": 0},  # Linear
            {"max_depth": 6, "cost": 0.30, "branch_count": 0},  # Linear
            {"max_depth": 8, "cost": 0.40, "branch_count": 0},  # Linear
            {"max_depth": 3, "cost": 0.15, "branch_count": 1},  # Has branches
        ]

        distribution = [
            DepthDistribution(
                depth=3, session_count=1, avg_cost=0.15, avg_messages=6, percentage=25.0
            ),
            DepthDistribution(
                depth=4, session_count=1, avg_cost=0.20, avg_messages=8, percentage=25.0
            ),
            DepthDistribution(
                depth=6,
                session_count=1,
                avg_cost=0.30,
                avg_messages=12,
                percentage=25.0,
            ),
            DepthDistribution(
                depth=8,
                session_count=1,
                avg_cost=0.40,
                avg_messages=16,
                percentage=25.0,
            ),
        ]

        recommendations = analytics_service._generate_depth_recommendations(
            depth_stats, distribution
        )

        # Should recommend exploring alternatives when stuck
        tips = " ".join(recommendations.tips)
        assert "linear" in tips or "alternative approaches" in tips

    def test_generate_depth_recommendations_empty_data(self, analytics_service):
        """Test depth recommendations with empty data."""
        recommendations = analytics_service._generate_depth_recommendations([], [])

        assert recommendations.optimal_depth_range == (0, 0)
        assert recommendations.warning_threshold == 0
        assert "No data available for recommendations" in recommendations.tips

    def test_generate_depth_recommendations_healthy_patterns(self, analytics_service):
        """Test depth recommendations with healthy conversation patterns."""
        depth_stats = [
            {"max_depth": 3, "cost": 0.15, "branch_count": 1},
            {"max_depth": 4, "cost": 0.20, "branch_count": 2},
            {"max_depth": 5, "cost": 0.25, "branch_count": 1},
        ]

        distribution = [
            DepthDistribution(
                depth=3, session_count=1, avg_cost=0.15, avg_messages=6, percentage=33.3
            ),
            DepthDistribution(
                depth=4, session_count=1, avg_cost=0.20, avg_messages=8, percentage=33.3
            ),
            DepthDistribution(
                depth=5,
                session_count=1,
                avg_cost=0.25,
                avg_messages=10,
                percentage=33.3,
            ),
        ]

        recommendations = analytics_service._generate_depth_recommendations(
            depth_stats, distribution
        )

        # Should indicate healthy patterns
        tips = " ".join(recommendations.tips)
        assert "healthy" in tips

    @pytest.mark.asyncio
    async def test_get_session_depth_analytics_database_error(self, analytics_service):
        """Test error handling when database operations fail."""
        # Mock database aggregation to raise an exception
        analytics_service.db.messages.aggregate.side_effect = Exception(
            "Database connection error"
        )

        # Test that exception is propagated
        with pytest.raises(Exception, match="Database connection error"):
            await analytics_service.get_session_depth_analytics(TimeRange.LAST_7_DAYS)

    @pytest.mark.asyncio
    async def test_get_session_depth_analytics_all_time_range(
        self, analytics_service, sample_messages_simple
    ):
        """Test session depth analytics with ALL_TIME range."""
        # Mock database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_messages_simple)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call with ALL_TIME range
        result = await analytics_service.get_session_depth_analytics(TimeRange.ALL_TIME)

        # Verify time filter was applied correctly (ALL_TIME should result in empty filter)
        assert isinstance(result, SessionDepthAnalytics)
        assert result.time_range == TimeRange.ALL_TIME

        # Verify aggregation pipeline was called
        analytics_service.db.messages.aggregate.assert_called_once()
        pipeline = analytics_service.db.messages.aggregate.call_args[0][0]

        # First stage should be $match with minimal filter for ALL_TIME
        match_stage = pipeline[0]["$match"]
        # For ALL_TIME, there should be no timestamp filter or it should be empty
        assert "timestamp" not in match_stage or not match_stage.get("timestamp")

    @pytest.mark.asyncio
    async def test_get_session_depth_analytics_complex_scenario(
        self, analytics_service
    ):
        """Test session depth analytics with complex realistic scenario."""
        # Create a complex dataset with mixed patterns
        complex_messages = []
        base_time = datetime.now(UTC)

        # Session 1: Shallow exploration (depth 3) with branches
        session1_msgs = [
            {
                "uuid": "s1_1",
                "sessionId": "session1",
                "parentUuid": None,
                "isSidechain": False,
                "costUsd": 0.01,
                "durationMs": 1000,
                "timestamp": base_time,
                "type": "user",
            },
            {
                "uuid": "s1_2",
                "sessionId": "session1",
                "parentUuid": "s1_1",
                "isSidechain": False,
                "costUsd": 0.02,
                "durationMs": 1500,
                "timestamp": base_time + timedelta(seconds=1),
                "type": "assistant",
            },
            {
                "uuid": "s1_3a",
                "sessionId": "session1",
                "parentUuid": "s1_2",
                "isSidechain": False,
                "costUsd": 0.015,
                "durationMs": 1200,
                "timestamp": base_time + timedelta(seconds=2),
                "type": "user",
            },
            {
                "uuid": "s1_3b",
                "sessionId": "session1",
                "parentUuid": "s1_2",
                "isSidechain": False,
                "costUsd": 0.018,
                "durationMs": 1300,
                "timestamp": base_time + timedelta(seconds=3),
                "type": "user",
            },
        ]

        # Session 2: Deep linear conversation (depth 7)
        session2_msgs = []
        for i in range(7):
            session2_msgs.append(
                {
                    "uuid": f"s2_{i + 1}",
                    "sessionId": "session2",
                    "parentUuid": f"s2_{i}" if i > 0 else None,
                    "isSidechain": False,
                    "costUsd": 0.02 + (i * 0.005),
                    "durationMs": 1500 + (i * 200),
                    "timestamp": base_time + timedelta(minutes=5, seconds=i),
                    "type": "assistant" if i % 2 == 1 else "user",
                }
            )

        # Session 3: Medium depth with sidechains (depth 5 main, 3 sidechain)
        session3_msgs = [
            {
                "uuid": "s3_1",
                "sessionId": "session3",
                "parentUuid": None,
                "isSidechain": False,
                "costUsd": 0.01,
                "durationMs": 1000,
                "timestamp": base_time + timedelta(minutes=10),
                "type": "user",
            },
            {
                "uuid": "s3_2",
                "sessionId": "session3",
                "parentUuid": "s3_1",
                "isSidechain": False,
                "costUsd": 0.02,
                "durationMs": 1500,
                "timestamp": base_time + timedelta(minutes=10, seconds=1),
                "type": "assistant",
            },
            {
                "uuid": "s3_3",
                "sessionId": "session3",
                "parentUuid": "s3_2",
                "isSidechain": False,
                "costUsd": 0.015,
                "durationMs": 1200,
                "timestamp": base_time + timedelta(minutes=10, seconds=2),
                "type": "user",
            },
            # Sidechain
            {
                "uuid": "s3_side1",
                "sessionId": "session3",
                "parentUuid": "s3_2",
                "isSidechain": True,
                "costUsd": 0.008,
                "durationMs": 800,
                "timestamp": base_time + timedelta(minutes=10, seconds=3),
                "type": "user",
            },
            {
                "uuid": "s3_side2",
                "sessionId": "session3",
                "parentUuid": "s3_side1",
                "isSidechain": True,
                "costUsd": 0.012,
                "durationMs": 900,
                "timestamp": base_time + timedelta(minutes=10, seconds=4),
                "type": "assistant",
            },
            {
                "uuid": "s3_side3",
                "sessionId": "session3",
                "parentUuid": "s3_side2",
                "isSidechain": True,
                "costUsd": 0.010,
                "durationMs": 850,
                "timestamp": base_time + timedelta(minutes=10, seconds=5),
                "type": "user",
            },
            # Continue main thread
            {
                "uuid": "s3_4",
                "sessionId": "session3",
                "parentUuid": "s3_3",
                "isSidechain": False,
                "costUsd": 0.025,
                "durationMs": 2000,
                "timestamp": base_time + timedelta(minutes=10, seconds=6),
                "type": "assistant",
            },
            {
                "uuid": "s3_5",
                "sessionId": "session3",
                "parentUuid": "s3_4",
                "isSidechain": False,
                "costUsd": 0.020,
                "durationMs": 1800,
                "timestamp": base_time + timedelta(minutes=10, seconds=7),
                "type": "user",
            },
        ]

        complex_messages = session1_msgs + session2_msgs + session3_msgs

        # Mock database aggregation
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=complex_messages)
        analytics_service.db.messages.aggregate.return_value = mock_cursor

        # Call the method
        result = await analytics_service.get_session_depth_analytics(
            TimeRange.LAST_7_DAYS, include_sidechains=True
        )

        # Verify comprehensive result
        assert isinstance(result, SessionDepthAnalytics)

        # Should have multiple depth levels
        assert len(result.depth_distribution) >= 2

        # Should identify multiple patterns
        assert len(result.patterns) >= 2

        # Should have meaningful correlations
        assert (
            abs(result.depth_correlations.depth_vs_cost) > 0
            or abs(result.depth_correlations.depth_vs_duration) > 0
        )

        # Should have practical recommendations
        assert len(result.recommendations.tips) > 0
        assert result.recommendations.optimal_depth_range[0] > 0
        assert (
            result.recommendations.warning_threshold
            > result.recommendations.optimal_depth_range[1]
        )
