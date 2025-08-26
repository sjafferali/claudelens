"""Tests for analytics service branch-related functionality."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.analytics import (
    BranchAnalytics,
    BranchComparison,
    BranchMetrics,
    BranchTopOperation,
    BranchType,
    GitBranchAnalyticsResponse,
    TimeRange,
)
from app.services.analytics import AnalyticsService


class TestAnalyticsServiceBranchAnalytics:
    """Test analytics service branch analytics functionality."""

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

    @pytest.fixture
    def sample_branch_data(self):
        """Sample branch data for testing."""
        now = datetime.now(UTC)
        return [
            {
                "branch": "main",
                "cost": 25.50,
                "messages": 150,
                "sessions": 2,
                "first_activity": now - timedelta(days=5),
                "last_activity": now,
                "active_days": 5,
            },
            {
                "branch": "feature/user-auth",
                "cost": 15.75,
                "messages": 80,
                "sessions": 1,
                "first_activity": now - timedelta(days=3),
                "last_activity": now,
                "active_days": 3,
            },
            {
                "branch": "hotfix/login-bug",
                "cost": 8.25,
                "messages": 45,
                "sessions": 1,
                "first_activity": now - timedelta(days=1),
                "last_activity": now,
                "active_days": 1,
            },
            {
                "branch": "release/v1.2.0",
                "cost": 12.00,
                "messages": 60,
                "sessions": 1,
                "first_activity": now - timedelta(days=2),
                "last_activity": now,
                "active_days": 2,
            },
        ]

    @pytest.fixture
    def sample_tool_usage(self):
        """Sample tool usage data for testing."""
        return {
            "main": {"bash": 50, "read": 30, "write": 25, "grep": 20, "edit": 15},
            "feature/user-auth": {"edit": 25, "write": 20, "read": 15, "bash": 10},
            "hotfix/login-bug": {"edit": 15, "read": 10, "bash": 8},
            "release/v1.2.0": {"write": 20, "edit": 18, "read": 12},
        }

    @pytest.mark.asyncio
    async def test_get_git_branch_analytics_basic(
        self, analytics_service, mock_db, sample_branch_data, sample_tool_usage
    ):
        """Test basic git branch analytics functionality."""
        # Mock the aggregation pipeline properly
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=sample_branch_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        # Mock the tool usage method
        analytics_service._get_tool_usage_by_branch = AsyncMock(
            return_value=sample_tool_usage
        )

        result = await analytics_service.get_git_branch_analytics(
            time_range=TimeRange.LAST_7_DAYS
        )

        assert isinstance(result, GitBranchAnalyticsResponse)
        assert len(result.branches) == 4
        assert result.time_range == TimeRange.LAST_7_DAYS

        # Check that branches are sorted by cost descending
        costs = [branch.metrics.cost for branch in result.branches]
        assert costs == sorted(costs, reverse=True)

        # Verify main branch
        main_branch = next(b for b in result.branches if b.name == "main")
        assert main_branch.type == BranchType.MAIN
        assert main_branch.metrics.cost == 25.50
        assert main_branch.metrics.messages == 150

    @pytest.mark.asyncio
    async def test_get_git_branch_analytics_with_filters(
        self, analytics_service, mock_db, sample_branch_data, sample_tool_usage
    ):
        """Test git branch analytics with include/exclude patterns."""
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=sample_branch_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)
        analytics_service._get_tool_usage_by_branch = AsyncMock(
            return_value=sample_tool_usage
        )

        # Test include pattern - only feature branches
        result = await analytics_service.get_git_branch_analytics(
            time_range=TimeRange.LAST_7_DAYS, include_pattern=r"feature/.*"
        )

        assert len(result.branches) == 1
        assert result.branches[0].name == "feature/user-auth"
        assert result.branches[0].type == BranchType.FEATURE

    @pytest.mark.asyncio
    async def test_get_git_branch_analytics_empty_data(
        self, analytics_service, mock_db
    ):
        """Test git branch analytics with no data."""
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=[])
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)
        analytics_service._get_tool_usage_by_branch = AsyncMock(return_value={})

        result = await analytics_service.get_git_branch_analytics(
            time_range=TimeRange.LAST_7_DAYS
        )

        assert isinstance(result, GitBranchAnalyticsResponse)
        assert len(result.branches) == 0
        assert result.branch_comparisons.main_vs_feature_cost_ratio == 0.0

    @pytest.mark.asyncio
    async def test_get_tool_usage_by_branch(self, analytics_service, mock_db):
        """Test getting tool usage by branch."""
        # Mock tool usage aggregation data
        tool_usage_data = [
            {
                "_id": "main",
                "tools": [
                    {"tool": "bash", "count": 50},
                    {"tool": "read", "count": 30},
                    {"tool": "write", "count": 25},
                ],
            },
            {
                "_id": "feature/auth",
                "tools": [
                    {"tool": "edit", "count": 25},
                    {"tool": "write", "count": 20},
                ],
            },
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=tool_usage_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        time_filter = {"timestamp": {"$gte": datetime.now(UTC) - timedelta(days=7)}}
        result = await analytics_service._get_tool_usage_by_branch(time_filter)

        assert "main" in result
        assert "feature/auth" in result
        assert result["main"]["bash"] == 50
        assert result["feature/auth"]["edit"] == 25

    def test_normalize_branch_name(self, analytics_service):
        """Test branch name normalization."""
        # Test empty/None cases
        assert analytics_service._normalize_branch_name(None) == ""
        assert analytics_service._normalize_branch_name("") == ""

        # Test normal branch names
        assert analytics_service._normalize_branch_name("main") == "main"
        assert (
            analytics_service._normalize_branch_name("feature/auth") == "feature/auth"
        )

        # Test remote prefixes
        assert (
            analytics_service._normalize_branch_name("refs/remotes/origin/main")
            == "main"
        )
        assert (
            analytics_service._normalize_branch_name("refs/remotes/upstream/develop")
            == "develop"
        )
        assert (
            analytics_service._normalize_branch_name("origin/feature/auth")
            == "feature/auth"
        )

    def test_detect_branch_type(self, analytics_service):
        """Test branch type detection."""
        # Test main branches
        assert analytics_service._detect_branch_type("main") == BranchType.MAIN
        assert analytics_service._detect_branch_type("master") == BranchType.MAIN
        assert analytics_service._detect_branch_type("develop") == BranchType.MAIN
        assert analytics_service._detect_branch_type("dev") == BranchType.MAIN

        # Test feature branches
        assert (
            analytics_service._detect_branch_type("feature/user-auth")
            == BranchType.FEATURE
        )
        assert (
            analytics_service._detect_branch_type("feat/new-ui") == BranchType.FEATURE
        )
        assert (
            analytics_service._detect_branch_type("feature-payment")
            == BranchType.FEATURE
        )

        # Test hotfix branches
        assert (
            analytics_service._detect_branch_type("hotfix/login-bug")
            == BranchType.HOTFIX
        )
        assert (
            analytics_service._detect_branch_type("fix/security") == BranchType.HOTFIX
        )
        assert (
            analytics_service._detect_branch_type("bugfix/crash") == BranchType.HOTFIX
        )

        # Test release branches
        assert (
            analytics_service._detect_branch_type("release/v1.2.0")
            == BranchType.RELEASE
        )
        assert analytics_service._detect_branch_type("rel/1.0") == BranchType.RELEASE

        # Test other branches
        assert analytics_service._detect_branch_type("experiment") == BranchType.OTHER
        assert analytics_service._detect_branch_type("") == BranchType.OTHER

    def test_calculate_branch_comparisons(self, analytics_service):
        """Test branch comparison calculations."""
        # Create sample branch analytics
        now = datetime.now(UTC)
        branches = [
            BranchAnalytics(
                name="main",
                type=BranchType.MAIN,
                metrics=BranchMetrics(
                    cost=30.0,
                    messages=100,
                    sessions=3,
                    avg_session_cost=10.0,
                    first_activity=now - timedelta(days=10),
                    last_activity=now,
                    active_days=10,
                ),
                top_operations=[],
                cost_trend=0.0,
            ),
            BranchAnalytics(
                name="feature/auth",
                type=BranchType.FEATURE,
                metrics=BranchMetrics(
                    cost=15.0,
                    messages=50,
                    sessions=1,
                    avg_session_cost=15.0,
                    first_activity=now - timedelta(days=5),
                    last_activity=now,
                    active_days=5,
                ),
                top_operations=[],
                cost_trend=0.0,
            ),
            BranchAnalytics(
                name="feature/ui",
                type=BranchType.FEATURE,
                metrics=BranchMetrics(
                    cost=10.0,
                    messages=30,
                    sessions=1,
                    avg_session_cost=10.0,
                    first_activity=now - timedelta(days=3),
                    last_activity=now,
                    active_days=3,
                ),
                top_operations=[],
                cost_trend=0.0,
            ),
            BranchAnalytics(
                name="hotfix/bug",
                type=BranchType.HOTFIX,
                metrics=BranchMetrics(
                    cost=5.0,
                    messages=20,
                    sessions=1,
                    avg_session_cost=5.0,
                    first_activity=now - timedelta(days=1),
                    last_activity=now,
                    active_days=1,
                ),
                top_operations=[],
                cost_trend=0.0,
            ),
        ]

        result = analytics_service._calculate_branch_comparisons(branches)

        assert isinstance(result, BranchComparison)
        # Main cost (30) vs Feature cost (25) = 1.2
        assert result.main_vs_feature_cost_ratio == 1.2
        # Average feature lifetime: (5 + 3) / 2 = 4.0
        assert result.avg_feature_branch_lifetime_days == 4.0
        # Main branch has highest cost
        assert result.most_expensive_branch_type == BranchType.MAIN

    def test_calculate_branch_comparisons_empty(self, analytics_service):
        """Test branch comparison calculations with empty data."""
        result = analytics_service._calculate_branch_comparisons([])

        assert isinstance(result, BranchComparison)
        assert result.main_vs_feature_cost_ratio == 0.0
        assert result.avg_feature_branch_lifetime_days == 0.0
        assert result.most_expensive_branch_type == BranchType.OTHER

    def test_calculate_branch_comparisons_no_feature_cost(self, analytics_service):
        """Test branch comparison calculations with no feature branches."""
        now = datetime.now(UTC)
        branches = [
            BranchAnalytics(
                name="main",
                type=BranchType.MAIN,
                metrics=BranchMetrics(
                    cost=30.0,
                    messages=100,
                    sessions=3,
                    avg_session_cost=10.0,
                    first_activity=now - timedelta(days=10),
                    last_activity=now,
                    active_days=10,
                ),
                top_operations=[],
                cost_trend=0.0,
            )
        ]

        result = analytics_service._calculate_branch_comparisons(branches)

        # Should be 0 when no feature cost to compare against
        assert result.main_vs_feature_cost_ratio == 0.0
        assert result.avg_feature_branch_lifetime_days == 0.0
        assert result.most_expensive_branch_type == BranchType.MAIN

    @pytest.mark.asyncio
    async def test_branch_analytics_top_operations(
        self, analytics_service, mock_db, sample_branch_data, sample_tool_usage
    ):
        """Test that top operations are correctly calculated and limited."""
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=sample_branch_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)
        analytics_service._get_tool_usage_by_branch = AsyncMock(
            return_value=sample_tool_usage
        )

        result = await analytics_service.get_git_branch_analytics(
            time_range=TimeRange.LAST_7_DAYS
        )

        main_branch = next(b for b in result.branches if b.name == "main")

        # Should have top 5 operations
        assert len(main_branch.top_operations) == 5

        # Should be sorted by count descending
        operations = main_branch.top_operations
        assert operations[0].operation == "bash"
        assert operations[0].count == 50
        assert operations[1].operation == "read"
        assert operations[1].count == 30

        # Verify all are BranchTopOperation instances
        for op in operations:
            assert isinstance(op, BranchTopOperation)
            assert op.count > 0

    @pytest.mark.asyncio
    async def test_get_git_branch_analytics_with_project_filter(
        self, analytics_service, mock_db, sample_branch_data, sample_tool_usage
    ):
        """Test git branch analytics with project_id filter."""
        from bson import ObjectId

        project_id = str(ObjectId())

        # Mock sessions query for project filter
        mock_sessions_cursor = AsyncMock()
        mock_sessions_cursor.to_list = AsyncMock(
            return_value=[{"sessionId": "session1"}, {"sessionId": "session2"}]
        )
        mock_db.sessions.find = MagicMock(return_value=mock_sessions_cursor)

        # Mock the main aggregation
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=sample_branch_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        analytics_service._get_tool_usage_by_branch = AsyncMock(
            return_value=sample_tool_usage
        )

        result = await analytics_service.get_git_branch_analytics(
            time_range=TimeRange.LAST_7_DAYS, project_id=project_id
        )

        # Verify sessions query was called with correct project filter
        mock_db.sessions.find.assert_called_once()
        sessions_call_args = mock_db.sessions.find.call_args[0]
        assert sessions_call_args[0]["projectId"] == ObjectId(project_id)

        # Verify the aggregation was called with session filter
        mock_db.messages.aggregate.assert_called_once()
        pipeline = mock_db.messages.aggregate.call_args[0][0]
        match_stage = pipeline[0]["$match"]
        assert "sessionId" in match_stage
        assert match_stage["sessionId"]["$in"] == ["session1", "session2"]

        assert isinstance(result, GitBranchAnalyticsResponse)
        assert len(result.branches) == 4

    @pytest.mark.asyncio
    async def test_get_git_branch_analytics_database_error(
        self, analytics_service, mock_db
    ):
        """Test git branch analytics handles database errors gracefully."""
        # Mock database error - the error should occur when calling to_list
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(
            side_effect=Exception("Database connection error")
        )
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        with pytest.raises(Exception) as exc_info:
            await analytics_service.get_git_branch_analytics(
                time_range=TimeRange.LAST_7_DAYS
            )

        assert "Database connection error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_git_branch_analytics_aggregation_timeout(
        self, analytics_service, mock_db
    ):
        """Test git branch analytics handles aggregation timeout."""
        from pymongo.errors import ExecutionTimeout

        # Mock aggregation timeout - the error should occur when calling to_list
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(
            side_effect=ExecutionTimeout("Aggregation timeout")
        )
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        with pytest.raises(ExecutionTimeout):
            await analytics_service.get_git_branch_analytics(
                time_range=TimeRange.LAST_7_DAYS
            )

    @pytest.mark.asyncio
    async def test_get_git_branch_analytics_exclude_pattern(
        self, analytics_service, mock_db, sample_branch_data, sample_tool_usage
    ):
        """Test git branch analytics with exclude pattern."""
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=sample_branch_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)
        analytics_service._get_tool_usage_by_branch = AsyncMock(
            return_value=sample_tool_usage
        )

        # Test exclude pattern - exclude hotfix branches
        result = await analytics_service.get_git_branch_analytics(
            time_range=TimeRange.LAST_7_DAYS, exclude_pattern=r"hotfix/.*"
        )

        # Should exclude hotfix/login-bug branch
        branch_names = [b.name for b in result.branches]
        assert "hotfix/login-bug" not in branch_names
        assert len(result.branches) == 3  # All except hotfix
        assert "main" in branch_names
        assert "feature/user-auth" in branch_names

    @pytest.mark.asyncio
    async def test_get_git_branch_analytics_both_include_exclude_patterns(
        self, analytics_service, mock_db, sample_branch_data, sample_tool_usage
    ):
        """Test git branch analytics with both include and exclude patterns."""
        # Add more diverse branch data
        extended_branch_data = sample_branch_data + [
            {
                "branch": "feature/payment-system",
                "cost": 20.0,
                "messages": 90,
                "sessions": 2,
                "first_activity": datetime.now(UTC) - timedelta(days=4),
                "last_activity": datetime.now(UTC),
                "active_days": 4,
            },
            {
                "branch": "feature/auth-refactor",
                "cost": 18.0,
                "messages": 85,
                "sessions": 1,
                "first_activity": datetime.now(UTC) - timedelta(days=6),
                "last_activity": datetime.now(UTC),
                "active_days": 6,
            },
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=extended_branch_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        extended_tool_usage = {
            **sample_tool_usage,
            "feature/payment-system": {"edit": 30, "write": 25},
            "feature/auth-refactor": {"edit": 28, "read": 20},
        }
        analytics_service._get_tool_usage_by_branch = AsyncMock(
            return_value=extended_tool_usage
        )

        # Include feature branches but exclude auth-related ones
        result = await analytics_service.get_git_branch_analytics(
            time_range=TimeRange.LAST_7_DAYS,
            include_pattern=r"feature/.*",
            exclude_pattern=r".*auth.*",
        )

        branch_names = [b.name for b in result.branches]
        assert len(result.branches) == 1  # Only feature/payment-system should match
        assert "feature/payment-system" in branch_names
        assert "feature/user-auth" not in branch_names  # Excluded by pattern
        assert "feature/auth-refactor" not in branch_names  # Excluded by pattern

    @pytest.mark.asyncio
    async def test_get_git_branch_analytics_null_branch_data(
        self, analytics_service, mock_db, sample_tool_usage
    ):
        """Test git branch analytics with null/None branch names."""
        null_branch_data = [
            {
                "branch": None,
                "cost": 5.0,
                "messages": 25,
                "sessions": 1,
                "first_activity": datetime.now(UTC) - timedelta(days=1),
                "last_activity": datetime.now(UTC),
                "active_days": 1,
            },
            {
                "branch": "",
                "cost": 3.0,
                "messages": 15,
                "sessions": 1,
                "first_activity": datetime.now(UTC) - timedelta(days=1),
                "last_activity": datetime.now(UTC),
                "active_days": 1,
            },
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=null_branch_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        tool_usage_with_nulls = {
            None: {"edit": 10, "read": 8},
            "": {"write": 5, "edit": 3},
        }
        analytics_service._get_tool_usage_by_branch = AsyncMock(
            return_value=tool_usage_with_nulls
        )

        result = await analytics_service.get_git_branch_analytics(
            time_range=TimeRange.LAST_7_DAYS
        )

        assert len(result.branches) == 2
        # Both null and empty should be displayed as "No Branch"
        branch_names = [b.name for b in result.branches]
        assert all(name == "No Branch" for name in branch_names)

        # Both should be classified as OTHER type
        branch_types = [b.type for b in result.branches]
        assert all(branch_type == BranchType.OTHER for branch_type in branch_types)

    @pytest.mark.asyncio
    async def test_get_git_branch_analytics_remote_branch_normalization(
        self, analytics_service, mock_db, sample_tool_usage
    ):
        """Test git branch analytics properly normalizes remote branch names."""
        remote_branch_data = [
            {
                "branch": "refs/remotes/origin/main",
                "cost": 25.0,
                "messages": 100,
                "sessions": 2,
                "first_activity": datetime.now(UTC) - timedelta(days=5),
                "last_activity": datetime.now(UTC),
                "active_days": 5,
            },
            {
                "branch": "origin/feature/new-ui",
                "cost": 15.0,
                "messages": 60,
                "sessions": 1,
                "first_activity": datetime.now(UTC) - timedelta(days=3),
                "last_activity": datetime.now(UTC),
                "active_days": 3,
            },
            {
                "branch": "refs/heads/hotfix/critical-bug",
                "cost": 8.0,
                "messages": 30,
                "sessions": 1,
                "first_activity": datetime.now(UTC) - timedelta(days=1),
                "last_activity": datetime.now(UTC),
                "active_days": 1,
            },
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=remote_branch_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        normalized_tool_usage = {
            "main": {"bash": 40, "edit": 30},
            "feature/new-ui": {"write": 25, "edit": 20},
            "hotfix/critical-bug": {"edit": 15, "read": 10},
        }
        analytics_service._get_tool_usage_by_branch = AsyncMock(
            return_value=normalized_tool_usage
        )

        result = await analytics_service.get_git_branch_analytics(
            time_range=TimeRange.LAST_7_DAYS
        )

        # Check normalized branch names
        branch_names = [b.name for b in result.branches]
        assert "main" in branch_names
        assert "feature/new-ui" in branch_names
        assert "hotfix/critical-bug" in branch_names

        # Verify original remote names are not present
        assert "refs/remotes/origin/main" not in branch_names
        assert "origin/feature/new-ui" not in branch_names
        assert "refs/heads/hotfix/critical-bug" not in branch_names

        # Check branch types are detected correctly after normalization
        main_branch = next(b for b in result.branches if b.name == "main")
        feature_branch = next(b for b in result.branches if b.name == "feature/new-ui")
        hotfix_branch = next(
            b for b in result.branches if b.name == "hotfix/critical-bug"
        )

        assert main_branch.type == BranchType.MAIN
        assert feature_branch.type == BranchType.FEATURE
        assert hotfix_branch.type == BranchType.HOTFIX

    @pytest.mark.asyncio
    async def test_get_git_branch_analytics_zero_cost_branches(
        self, analytics_service, mock_db, sample_tool_usage
    ):
        """Test git branch analytics with zero-cost branches."""
        zero_cost_data = [
            {
                "branch": "experimental/test",
                "cost": 0.0,
                "messages": 10,
                "sessions": 1,
                "first_activity": datetime.now(UTC) - timedelta(days=1),
                "last_activity": datetime.now(UTC),
                "active_days": 1,
            },
            {
                "branch": "main",
                "cost": 25.0,
                "messages": 100,
                "sessions": 2,
                "first_activity": datetime.now(UTC) - timedelta(days=5),
                "last_activity": datetime.now(UTC),
                "active_days": 5,
            },
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=zero_cost_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        zero_cost_tool_usage = {
            "experimental/test": {"read": 5, "edit": 3},
            "main": {"bash": 40, "edit": 30},
        }
        analytics_service._get_tool_usage_by_branch = AsyncMock(
            return_value=zero_cost_tool_usage
        )

        result = await analytics_service.get_git_branch_analytics(
            time_range=TimeRange.LAST_7_DAYS
        )

        # Should be sorted by cost, so main should be first
        assert result.branches[0].name == "main"
        assert result.branches[1].name == "experimental/test"

        zero_cost_branch = result.branches[1]
        assert zero_cost_branch.metrics.cost == 0.0
        assert zero_cost_branch.metrics.avg_session_cost == 0.0
        assert zero_cost_branch.metrics.messages == 10

    @pytest.mark.asyncio
    async def test_get_git_branch_analytics_single_session_branch(
        self, analytics_service, mock_db
    ):
        """Test git branch analytics with branches having single sessions."""
        single_session_data = [
            {
                "branch": "feature/quick-fix",
                "cost": 5.0,
                "messages": 10,
                "sessions": 1,
                "first_activity": datetime.now(UTC) - timedelta(hours=2),
                "last_activity": datetime.now(UTC),
                "active_days": 1,  # Should be minimum 1 day
            }
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=single_session_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        analytics_service._get_tool_usage_by_branch = AsyncMock(
            return_value={"feature/quick-fix": {"edit": 8, "read": 2}}
        )

        result = await analytics_service.get_git_branch_analytics(
            time_range=TimeRange.LAST_7_DAYS
        )

        assert len(result.branches) == 1
        branch = result.branches[0]
        assert branch.metrics.sessions == 1
        assert branch.metrics.avg_session_cost == 5.0  # cost / sessions
        assert branch.metrics.active_days == 1  # Should enforce minimum of 1 day

    @pytest.mark.asyncio
    async def test_get_tool_usage_by_branch_empty_tool_results(
        self, analytics_service, mock_db
    ):
        """Test _get_tool_usage_by_branch with empty or missing tool results."""
        empty_tool_data = []

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=empty_tool_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        time_filter = {"timestamp": {"$gte": datetime.now(UTC) - timedelta(days=7)}}
        result = await analytics_service._get_tool_usage_by_branch(time_filter)

        assert result == {}

        # Verify the aggregation pipeline includes proper filters
        mock_db.messages.aggregate.assert_called_once()
        pipeline = mock_db.messages.aggregate.call_args[0][0]
        match_stage = pipeline[0]["$match"]
        assert "toolUseResult" in match_stage
        assert match_stage["toolUseResult"]["$exists"] is True
        assert match_stage["toolUseResult"]["$ne"] is None

    @pytest.mark.asyncio
    async def test_get_tool_usage_by_branch_malformed_data(
        self, analytics_service, mock_db
    ):
        """Test _get_tool_usage_by_branch handles malformed data gracefully."""
        malformed_tool_data = [
            {
                "_id": "main",
                "tools": [
                    {"tool": "bash", "count": 10},
                    {"tool": None, "count": 5},  # Malformed tool name
                    {"tool": "edit", "count": "invalid"},  # Invalid count
                ],
            }
        ]

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=malformed_tool_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)

        time_filter = {"timestamp": {"$gte": datetime.now(UTC) - timedelta(days=7)}}
        result = await analytics_service._get_tool_usage_by_branch(time_filter)

        # Should still process valid data
        assert "main" in result
        assert result["main"]["bash"] == 10
        # Should handle malformed data gracefully (exact behavior depends on implementation)

    def test_normalize_branch_name_edge_cases(self, analytics_service):
        """Test branch name normalization with edge cases."""
        # Test multiple prefixes
        assert (
            analytics_service._normalize_branch_name(
                "refs/remotes/upstream/feature/auth"
            )
            == "feature/auth"
        )

        # Test case sensitivity
        assert (
            analytics_service._normalize_branch_name("Origin/main") == "Origin/main"
        )  # Should not match case-sensitive prefix

        # Test partial matches
        assert (
            analytics_service._normalize_branch_name("not-origin/main")
            == "not-origin/main"
        )  # Should not match partial prefix

        # Test whitespace
        assert analytics_service._normalize_branch_name("  ") == "  "

        # Test very long branch names
        long_branch = "a" * 1000
        assert analytics_service._normalize_branch_name(long_branch) == long_branch

    def test_detect_branch_type_complex_patterns(self, analytics_service):
        """Test branch type detection with complex naming patterns."""
        # Test case variations
        assert analytics_service._detect_branch_type("MAIN") == BranchType.MAIN
        assert (
            analytics_service._detect_branch_type("Feature/Auth") == BranchType.FEATURE
        )
        assert analytics_service._detect_branch_type("HOTFIX/Bug") == BranchType.HOTFIX

        # Test multiple pattern matches (should match first applicable)
        assert (
            analytics_service._detect_branch_type("feature/hotfix-something")
            == BranchType.FEATURE
        )  # "feature/" comes first in the patterns

        # Test edge cases
        assert (
            analytics_service._detect_branch_type("feature") == BranchType.OTHER
        )  # No slash
        assert analytics_service._detect_branch_type("main-backup") == BranchType.OTHER
        assert (
            analytics_service._detect_branch_type("feat") == BranchType.OTHER
        )  # Need slash

        # Test numbers and special characters
        assert (
            analytics_service._detect_branch_type("feature/user-auth-v2.1")
            == BranchType.FEATURE
        )
        assert (
            analytics_service._detect_branch_type("release/v1.0.0-rc.1")
            == BranchType.RELEASE
        )

    def test_calculate_branch_comparisons_edge_cases(self, analytics_service):
        """Test branch comparison calculations with edge cases."""
        now = datetime.now(UTC)

        # Test with only feature branches (no main)
        feature_only_branches = [
            BranchAnalytics(
                name="feature/auth",
                type=BranchType.FEATURE,
                metrics=BranchMetrics(
                    cost=15.0,
                    messages=50,
                    sessions=1,
                    avg_session_cost=15.0,
                    first_activity=now - timedelta(days=5),
                    last_activity=now,
                    active_days=5,
                ),
                top_operations=[],
                cost_trend=0.0,
            ),
            BranchAnalytics(
                name="feature/ui",
                type=BranchType.FEATURE,
                metrics=BranchMetrics(
                    cost=10.0,
                    messages=30,
                    sessions=1,
                    avg_session_cost=10.0,
                    first_activity=now - timedelta(days=3),
                    last_activity=now,
                    active_days=3,
                ),
                top_operations=[],
                cost_trend=0.0,
            ),
        ]

        result = analytics_service._calculate_branch_comparisons(feature_only_branches)

        # Main vs feature ratio should be 0 when no main branch
        assert result.main_vs_feature_cost_ratio == 0.0
        # Should still calculate feature lifetime average
        assert result.avg_feature_branch_lifetime_days == 4.0  # (5+3)/2
        # Most expensive should be feature type
        assert result.most_expensive_branch_type == BranchType.FEATURE

        # Test with zero-cost branches
        zero_cost_branches = [
            BranchAnalytics(
                name="experimental",
                type=BranchType.OTHER,
                metrics=BranchMetrics(
                    cost=0.0,
                    messages=10,
                    sessions=1,
                    avg_session_cost=0.0,
                    first_activity=now - timedelta(days=1),
                    last_activity=now,
                    active_days=1,
                ),
                top_operations=[],
                cost_trend=0.0,
            )
        ]

        result = analytics_service._calculate_branch_comparisons(zero_cost_branches)
        assert (
            result.most_expensive_branch_type == BranchType.OTHER
        )  # Only type present

    @pytest.mark.asyncio
    async def test_get_git_branch_analytics_different_time_ranges(
        self, analytics_service, mock_db, sample_branch_data, sample_tool_usage
    ):
        """Test git branch analytics with different time ranges."""
        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=sample_branch_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)
        analytics_service._get_tool_usage_by_branch = AsyncMock(
            return_value=sample_tool_usage
        )

        # Test all time ranges
        time_ranges = [
            TimeRange.LAST_24_HOURS,
            TimeRange.LAST_7_DAYS,
            TimeRange.LAST_30_DAYS,
            TimeRange.LAST_90_DAYS,
        ]

        for time_range in time_ranges:
            result = await analytics_service.get_git_branch_analytics(
                time_range=time_range
            )

            assert result.time_range == time_range
            assert isinstance(result, GitBranchAnalyticsResponse)

            # Verify the aggregation was called with time filter
            mock_db.messages.aggregate.assert_called()
            pipeline = mock_db.messages.aggregate.call_args[0][0]
            match_stage = pipeline[0]["$match"]
            assert "timestamp" in match_stage

    @pytest.mark.asyncio
    async def test_get_git_branch_analytics_performance_large_dataset(
        self, analytics_service, mock_db
    ):
        """Test git branch analytics performance with large dataset simulation."""
        # Simulate large dataset
        large_branch_data = []
        large_tool_usage = {}

        for i in range(100):  # 100 branches
            branch_name = f"feature/branch-{i}"
            large_branch_data.append(
                {
                    "branch": branch_name,
                    "cost": float(i * 0.5),
                    "messages": i * 10,
                    "sessions": max(1, i // 10),
                    "first_activity": datetime.now(UTC) - timedelta(days=i % 30),
                    "last_activity": datetime.now(UTC),
                    "active_days": max(1, i % 30),
                }
            )
            large_tool_usage[branch_name] = {
                f"tool_{j}": i + j for j in range(5)  # 5 tools per branch
            }

        mock_aggregate = MagicMock()
        mock_aggregate.to_list = AsyncMock(return_value=large_branch_data)
        mock_db.messages.aggregate = MagicMock(return_value=mock_aggregate)
        analytics_service._get_tool_usage_by_branch = AsyncMock(
            return_value=large_tool_usage
        )

        result = await analytics_service.get_git_branch_analytics(
            time_range=TimeRange.LAST_30_DAYS
        )

        # Verify all branches are processed
        assert len(result.branches) == 100

        # Verify sorting by cost (descending)
        costs = [b.metrics.cost for b in result.branches]
        assert costs == sorted(costs, reverse=True)

        # Verify top operations are limited to 5 per branch
        for branch in result.branches:
            assert len(branch.top_operations) <= 5

        # Verify branch comparisons are calculated
        assert isinstance(result.branch_comparisons, BranchComparison)
