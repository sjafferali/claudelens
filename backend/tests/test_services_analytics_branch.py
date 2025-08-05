"""Tests for analytics service branch-related functionality."""

from datetime import datetime, timedelta
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
        now = datetime.utcnow()
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

        time_filter = {"timestamp": {"$gte": datetime.utcnow() - timedelta(days=7)}}
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
        now = datetime.utcnow()
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
        now = datetime.utcnow()
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
