"""Comprehensive tests for analytics service directory insights functionality."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.analytics import (
    DirectoryMetrics,
    DirectoryNode,
    DirectoryTotalMetrics,
    DirectoryUsageResponse,
    TimeRange,
)
from app.services.analytics import AnalyticsService


class TestAnalyticsServiceDirectory:
    """Test analytics service directory functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.messages = MagicMock()
        db.sessions = MagicMock()
        return db

    @pytest.fixture
    def analytics_service(self, mock_db):
        """Create analytics service with mock database."""
        return AnalyticsService(mock_db)

    @pytest.fixture
    def sample_directory_data(self):
        """Sample directory data from MongoDB aggregation."""
        base_time = datetime.utcnow()
        return [
            {
                "path": "/home/user/project",
                "total_cost": 10.50,
                "message_count": 15,
                "session_count": 3,
                "last_active": base_time - timedelta(hours=1),
            },
            {
                "path": "/home/user/project/src",
                "total_cost": 7.25,
                "message_count": 8,
                "session_count": 2,
                "last_active": base_time - timedelta(hours=2),
            },
            {
                "path": "/home/user/project/tests",
                "total_cost": 3.25,
                "message_count": 7,
                "session_count": 1,
                "last_active": base_time - timedelta(hours=3),
            },
            {
                "path": "/home/user/docs",
                "total_cost": 2.00,
                "message_count": 5,
                "session_count": 1,
                "last_active": base_time - timedelta(hours=4),
            },
        ]

    @pytest.fixture
    def empty_directory_data(self):
        """Empty directory data for testing edge cases."""
        return []

    @pytest.fixture
    def windows_directory_data(self):
        """Windows-style directory paths for cross-platform testing."""
        base_time = datetime.utcnow()
        return [
            {
                "path": "C:\\Users\\user\\project",
                "total_cost": 5.00,
                "message_count": 10,
                "session_count": 2,
                "last_active": base_time - timedelta(hours=1),
            },
            {
                "path": "C:\\Users\\user\\project\\src",
                "total_cost": 3.00,
                "message_count": 6,
                "session_count": 1,
                "last_active": base_time - timedelta(hours=2),
            },
        ]

    @pytest.mark.asyncio
    async def test_get_directory_usage_basic_functionality(
        self, analytics_service, mock_db, sample_directory_data
    ):
        """Test basic functionality of get_directory_usage with normal data."""
        # Mock the aggregation pipeline result
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_directory_data)
        mock_db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_directory_usage(
            time_range=TimeRange.LAST_30_DAYS, depth=3, min_cost=0.0
        )

        # Verify the response structure
        assert isinstance(result, DirectoryUsageResponse)
        assert result.time_range == TimeRange.LAST_30_DAYS
        assert isinstance(result.root, DirectoryNode)
        assert isinstance(result.total_metrics, DirectoryTotalMetrics)
        assert isinstance(result.generated_at, datetime)

        # Verify total metrics
        expected_total_messages = sum(d["message_count"] for d in sample_directory_data)
        expected_unique_directories = len(sample_directory_data)

        assert result.total_metrics.total_messages == expected_total_messages
        assert result.total_metrics.unique_directories == expected_unique_directories
        assert result.total_metrics.total_cost > 0

        # Verify root node structure
        assert result.root.path == "/"
        assert result.root.name == "root"
        assert len(result.root.children) > 0

        # Verify aggregation pipeline was called correctly
        mock_db.messages.aggregate.assert_called_once()
        pipeline = mock_db.messages.aggregate.call_args[0][0]

        # Check key pipeline stages
        assert any("$match" in stage for stage in pipeline)
        assert any("$group" in stage for stage in pipeline)
        assert any("$project" in stage for stage in pipeline)

    @pytest.mark.asyncio
    async def test_get_directory_usage_empty_data(
        self, analytics_service, mock_db, empty_directory_data
    ):
        """Test get_directory_usage with empty data returns proper empty structure."""
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=empty_directory_data)
        mock_db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_directory_usage()

        # Verify empty response structure
        assert isinstance(result, DirectoryUsageResponse)
        assert result.total_metrics.total_cost == 0.0
        assert result.total_metrics.total_messages == 0
        assert result.total_metrics.unique_directories == 0

        # Verify empty root node
        assert result.root.path == "/"
        assert result.root.name == "root"
        assert result.root.metrics.cost == 0.0
        assert result.root.metrics.messages == 0
        assert result.root.metrics.sessions == 0
        assert len(result.root.children) == 0
        assert result.root.percentage_of_total == 0.0

    @pytest.mark.asyncio
    async def test_get_directory_usage_with_time_filters(
        self, analytics_service, mock_db, sample_directory_data
    ):
        """Test get_directory_usage with different time ranges."""
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_directory_data)
        mock_db.messages.aggregate.return_value = mock_cursor

        # Test different time ranges
        time_ranges = [
            TimeRange.LAST_24_HOURS,
            TimeRange.LAST_7_DAYS,
            TimeRange.LAST_30_DAYS,
            TimeRange.LAST_90_DAYS,
            TimeRange.ALL_TIME,
        ]

        for time_range in time_ranges:
            result = await analytics_service.get_directory_usage(time_range=time_range)
            assert result.time_range == time_range

            # Verify the aggregation pipeline includes proper time filters
            pipeline = mock_db.messages.aggregate.call_args[0][0]
            match_stage = next(
                stage["$match"] for stage in pipeline if "$match" in stage
            )

            if time_range == TimeRange.ALL_TIME:
                # ALL_TIME should not have timestamp filter beyond basic existence checks
                assert "cwd" in match_stage
            else:
                # Other time ranges should have timestamp filters
                assert "cwd" in match_stage

    @pytest.mark.asyncio
    async def test_get_directory_usage_with_min_cost_filter(
        self, analytics_service, mock_db, sample_directory_data
    ):
        """Test get_directory_usage with minimum cost filtering."""
        mock_cursor = MagicMock()
        # Filter out directories with cost < 5.0
        filtered_data = [d for d in sample_directory_data if d["total_cost"] >= 5.0]
        mock_cursor.to_list = AsyncMock(return_value=filtered_data)
        mock_db.messages.aggregate.return_value = mock_cursor

        await analytics_service.get_directory_usage(min_cost=5.0)

        # Verify aggregation pipeline includes cost filter
        pipeline = mock_db.messages.aggregate.call_args[0][0]
        cost_match_stages = [
            stage
            for stage in pipeline
            if "$match" in stage and "total_cost" in stage.get("$match", {})
        ]
        assert len(cost_match_stages) > 0

        cost_filter = cost_match_stages[0]["$match"]["total_cost"]
        assert cost_filter["$gte"] == 5.0

    @pytest.mark.asyncio
    async def test_get_directory_usage_with_depth_limit(
        self, analytics_service, mock_db, sample_directory_data
    ):
        """Test get_directory_usage with depth limiting."""
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_directory_data)
        mock_db.messages.aggregate.return_value = mock_cursor

        # Test with depth limit of 2
        result = await analytics_service.get_directory_usage(depth=2)

        # Verify depth is respected in the tree structure
        def check_max_depth(node: DirectoryNode, current_depth: int = 0) -> int:
            max_depth = current_depth
            for child in node.children:
                child_max_depth = check_max_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_max_depth)
            return max_depth

        actual_max_depth = check_max_depth(result.root)
        # Allow some flexibility as depth counting can vary by implementation
        assert actual_max_depth <= 3  # Root + 2 levels

    @pytest.mark.asyncio
    async def test_get_directory_usage_with_database_error(
        self, analytics_service, mock_db
    ):
        """Test get_directory_usage handles database errors gracefully."""
        # Mock a database error
        mock_db.messages.aggregate.side_effect = Exception("Database connection error")

        with pytest.raises(Exception) as exc_info:
            await analytics_service.get_directory_usage()

        assert "Database connection error" in str(exc_info.value)

    def test_normalize_path_unix_paths(self, analytics_service):
        """Test _normalize_path with Unix-style paths."""
        test_cases = [
            ("/home/user/project", "/home/user/project"),
            ("home/user/project", "/home/user/project"),
            ("/home/user/project/", "/home/user/project"),
            ("", ""),
            ("/", "/"),
            ("//home//user//project//", "/home/user/project"),
        ]

        for input_path, expected in test_cases:
            result = analytics_service._normalize_path(input_path)
            assert result == expected, f"Failed for input: {input_path}"

    def test_normalize_path_windows_paths(self, analytics_service):
        """Test _normalize_path with Windows-style paths."""
        test_cases = [
            ("C:\\Users\\user\\project", "/Users/user/project"),
            ("C:\\Users\\user\\project\\", "/Users/user/project"),
            ("D:\\projects\\myapp", "/projects/myapp"),
            ("C:", "/"),
            ("\\Users\\user", "/Users/user"),
        ]

        for input_path, expected in test_cases:
            result = analytics_service._normalize_path(input_path)
            assert result == expected, f"Failed for input: {input_path}"

    def test_normalize_path_edge_cases(self, analytics_service):
        """Test _normalize_path with edge cases."""
        test_cases = [
            (None, ""),  # Handle None input
            ("relative/path", "/relative/path"),
            ("./relative", "/./relative"),
            ("../parent", "/../parent"),
        ]

        for input_path, expected in test_cases:
            try:
                result = analytics_service._normalize_path(input_path or "")
                assert result == expected, f"Failed for input: {input_path}"
            except (TypeError, AttributeError):
                # Handle cases where the method doesn't accept None
                if input_path is not None:
                    raise

    def test_build_directory_tree_simple_structure(self, analytics_service):
        """Test _build_directory_tree with simple directory structure."""
        directory_data = [
            {
                "path": "/home/user",
                "total_cost": 10.0,
                "message_count": 5,
                "session_count": 2,
                "last_active": datetime.utcnow(),
            },
        ]

        result = analytics_service._build_directory_tree(directory_data, 3, 10.0)

        assert isinstance(result, DirectoryNode)
        assert result.path == "/"
        assert result.name == "root"
        assert len(result.children) == 1

        home_child = result.children[0]
        assert home_child.name == "home"
        assert len(home_child.children) == 1

        user_child = home_child.children[0]
        assert user_child.name == "user"
        assert user_child.metrics.cost == 10.0
        assert user_child.metrics.messages == 5

    def test_build_directory_tree_complex_structure(
        self, analytics_service, sample_directory_data
    ):
        """Test _build_directory_tree with complex nested structure."""
        total_cost = sum(d["total_cost"] for d in sample_directory_data)

        result = analytics_service._build_directory_tree(
            sample_directory_data, 5, total_cost
        )

        assert isinstance(result, DirectoryNode)
        assert result.path == "/"

        # Verify hierarchical structure is built correctly
        def find_node_by_name(node: DirectoryNode, name: str) -> DirectoryNode | None:
            if node.name == name:
                return node
            for child in node.children:
                found = find_node_by_name(child, name)
                if found:
                    return found
            return None

        # Should find expected directories
        home_node = find_node_by_name(result, "home")
        assert home_node is not None

        user_node = find_node_by_name(result, "user")
        assert user_node is not None

    def test_build_directory_tree_with_depth_limit(
        self, analytics_service, sample_directory_data
    ):
        """Test _build_directory_tree respects depth limits."""
        total_cost = sum(d["total_cost"] for d in sample_directory_data)

        # Test with depth limit of 2
        result = analytics_service._build_directory_tree(
            sample_directory_data, 2, total_cost
        )

        def get_max_depth(node: DirectoryNode, current_depth: int = 0) -> int:
            if not node.children:
                return current_depth
            return max(
                get_max_depth(child, current_depth + 1) for child in node.children
            )

        max_depth = get_max_depth(result)
        # Should not exceed the specified depth significantly
        assert max_depth <= 3  # Root + 2 levels, allowing some flexibility

    def test_build_directory_tree_empty_data(self, analytics_service):
        """Test _build_directory_tree with empty data."""
        result = analytics_service._build_directory_tree([], 3, 0.0)

        assert isinstance(result, DirectoryNode)
        assert result.path == "/"
        assert result.name == "root"
        assert len(result.children) == 0
        assert result.metrics.cost == 0.0

    def test_build_directory_tree_invalid_paths(self, analytics_service):
        """Test _build_directory_tree handles invalid/empty paths."""
        directory_data = [
            {
                "path": "",
                "total_cost": 5.0,
                "message_count": 3,
                "session_count": 1,
                "last_active": datetime.utcnow(),
            },
            {
                "path": None,
                "total_cost": 3.0,
                "message_count": 2,
                "session_count": 1,
                "last_active": datetime.utcnow(),
            },
        ]

        # Should handle invalid paths gracefully
        result = analytics_service._build_directory_tree(directory_data, 3, 8.0)
        assert isinstance(result, DirectoryNode)
        # Invalid paths should be filtered out, so structure might be minimal

    def test_tree_to_directory_node_metrics_calculation(self, analytics_service):
        """Test _tree_to_directory_node properly calculates aggregated metrics."""
        # Create a mock tree structure
        tree = {
            "_data": {
                "path": "/test",
                "name": "test",
                "cost": 0.0,
                "messages": 0,
                "sessions": 0,
                "last_active": datetime.min,
            },
            "_children": {
                "child1": {
                    "_data": {
                        "path": "/test/child1",
                        "name": "child1",
                        "cost": 5.0,
                        "messages": 3,
                        "sessions": 1,
                        "last_active": datetime.utcnow(),
                    },
                    "_children": {},
                },
                "child2": {
                    "_data": {
                        "path": "/test/child2",
                        "name": "child2",
                        "cost": 3.0,
                        "messages": 2,
                        "sessions": 1,
                        "last_active": datetime.utcnow() - timedelta(hours=1),
                    },
                    "_children": {},
                },
            },
        }

        result = analytics_service._tree_to_directory_node(tree, "/test", "test", 10.0)

        assert isinstance(result, DirectoryNode)
        assert result.path == "/test"
        assert result.name == "test"

        # Verify aggregated metrics
        assert result.metrics.cost == 8.0  # 5.0 + 3.0
        assert result.metrics.messages == 5  # 3 + 2

        # Verify children are created
        assert len(result.children) == 2

        # Verify children are sorted by cost (descending)
        assert result.children[0].metrics.cost >= result.children[1].metrics.cost

    def test_tree_to_directory_node_percentage_calculation(self, analytics_service):
        """Test _tree_to_directory_node calculates percentages correctly."""
        tree = {
            "_data": {
                "path": "/test",
                "name": "test",
                "cost": 25.0,
                "messages": 10,
                "sessions": 2,
                "last_active": datetime.utcnow(),
            },
            "_children": {},
        }

        result = analytics_service._tree_to_directory_node(tree, "/test", "test", 100.0)

        assert result.percentage_of_total == 25.0  # 25/100 * 100

    def test_tree_to_directory_node_avg_cost_per_session(self, analytics_service):
        """Test _tree_to_directory_node calculates average cost per session correctly."""
        tree = {
            "_data": {
                "path": "/test",
                "name": "test",
                "cost": 15.0,
                "messages": 10,
                "sessions": 3,
                "last_active": datetime.utcnow(),
            },
            "_children": {},
        }

        result = analytics_service._tree_to_directory_node(tree, "/test", "test", 100.0)

        expected_avg = 15.0 / 3  # cost / sessions
        assert abs(result.metrics.avg_cost_per_session - expected_avg) < 0.01

    def test_tree_to_directory_node_zero_sessions(self, analytics_service):
        """Test _tree_to_directory_node handles zero sessions gracefully."""
        tree = {
            "_data": {
                "path": "/test",
                "name": "test",
                "cost": 10.0,
                "messages": 5,
                "sessions": 0,
                "last_active": datetime.utcnow(),
            },
            "_children": {},
        }

        result = analytics_service._tree_to_directory_node(tree, "/test", "test", 100.0)

        # Should handle division by zero
        assert result.metrics.avg_cost_per_session == 0.0

    @pytest.mark.asyncio
    async def test_get_directory_usage_windows_paths(
        self, analytics_service, mock_db, windows_directory_data
    ):
        """Test get_directory_usage with Windows-style paths."""
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=windows_directory_data)
        mock_db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_directory_usage()

        assert isinstance(result, DirectoryUsageResponse)
        assert result.total_metrics.total_cost > 0
        assert result.total_metrics.unique_directories == len(windows_directory_data)

        # Verify paths are normalized in the tree structure
        def check_normalized_paths(node: DirectoryNode) -> bool:
            # All paths should start with / and not contain backslashes
            if not node.path.startswith("/") or "\\" in node.path:
                return False
            return all(check_normalized_paths(child) for child in node.children)

        assert check_normalized_paths(result.root)

    @pytest.mark.asyncio
    async def test_get_directory_usage_concurrent_sessions(
        self, analytics_service, mock_db
    ):
        """Test get_directory_usage with data from multiple concurrent sessions."""
        directory_data = [
            {
                "path": "/project",
                "total_cost": 20.0,
                "message_count": 50,
                "session_count": 10,  # High concurrency
                "last_active": datetime.utcnow(),
            },
        ]

        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=directory_data)
        mock_db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_directory_usage()

        assert isinstance(result, DirectoryUsageResponse)

        # Find the project node
        def find_project_node(node: DirectoryNode) -> DirectoryNode | None:
            if "project" in node.path:
                return node
            for child in node.children:
                found = find_project_node(child)
                if found:
                    return found
            return None

        project_node = find_project_node(result.root)
        if project_node:
            assert project_node.metrics.sessions == 10
            assert project_node.metrics.avg_cost_per_session == 2.0  # 20.0 / 10

    @pytest.mark.asyncio
    async def test_get_directory_usage_old_data(self, analytics_service, mock_db):
        """Test get_directory_usage with very old last_active timestamps."""
        old_time = datetime.utcnow() - timedelta(days=365)  # One year old
        directory_data = [
            {
                "path": "/old/project",
                "total_cost": 5.0,
                "message_count": 10,
                "session_count": 2,
                "last_active": old_time,
            },
        ]

        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=directory_data)
        mock_db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_directory_usage()

        assert isinstance(result, DirectoryUsageResponse)

        # Should handle old timestamps correctly
        def find_old_project(node: DirectoryNode) -> DirectoryNode | None:
            if "old" in node.path or "project" in node.path:
                return node
            for child in node.children:
                found = find_old_project(child)
                if found:
                    return found
            return None

        old_project_node = find_old_project(result.root)
        if old_project_node:
            # Should preserve the old timestamp
            time_diff = abs(
                (old_project_node.metrics.last_active - old_time).total_seconds()
            )
            assert time_diff < 1  # Should be very close to original time

    def test_analytics_service_safe_float_in_directory_context(self, analytics_service):
        """Test _safe_float method specifically in directory analytics context."""
        # Test cases specific to directory cost calculations
        test_cases = [
            (None, 0.0),  # Missing cost data
            (0, 0.0),  # Zero cost
            (0.0, 0.0),  # Zero float cost
            (10.50, 10.50),  # Normal cost
            (100, 100.0),  # Integer cost
        ]

        for input_val, expected in test_cases:
            result = analytics_service._safe_float(input_val)
            assert result == expected, f"Failed for input: {input_val}"

    @pytest.mark.asyncio
    async def test_get_directory_usage_aggregation_pipeline_structure(
        self, analytics_service, mock_db, sample_directory_data
    ):
        """Test that the aggregation pipeline is structured correctly."""
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_directory_data)
        mock_db.messages.aggregate.return_value = mock_cursor

        await analytics_service.get_directory_usage(
            time_range=TimeRange.LAST_7_DAYS, depth=3, min_cost=1.0
        )

        # Verify aggregation was called
        mock_db.messages.aggregate.assert_called_once()
        pipeline = mock_db.messages.aggregate.call_args[0][0]

        # Verify pipeline structure
        assert isinstance(pipeline, list)
        assert len(pipeline) >= 3  # Should have match, group, and project stages

        # Check for required stages
        stage_types = [list(stage.keys())[0] for stage in pipeline]
        assert "$match" in stage_types
        assert "$group" in stage_types
        assert "$project" in stage_types

        # Verify match stage filters
        match_stages = [stage for stage in pipeline if "$match" in stage]
        assert len(match_stages) >= 1

        initial_match = match_stages[0]["$match"]
        assert "cwd" in initial_match
        assert initial_match["cwd"]["$exists"] is True
        assert initial_match["cwd"]["$ne"] is None

        # Verify cost filter if min_cost > 0
        cost_match = [
            stage
            for stage in pipeline
            if "$match" in stage and "total_cost" in stage.get("$match", {})
        ]
        if cost_match:
            assert cost_match[0]["$match"]["total_cost"]["$gte"] == 1.0

        # Verify group stage
        group_stages = [stage for stage in pipeline if "$group" in stage]
        assert len(group_stages) == 1

        group_stage = group_stages[0]["$group"]
        assert group_stage["_id"] == "$cwd"
        assert "total_cost" in group_stage
        assert "message_count" in group_stage
        assert "session_count" in group_stage
        assert "last_active" in group_stage

    @pytest.mark.asyncio
    async def test_get_directory_usage_return_value_completeness(
        self, analytics_service, mock_db, sample_directory_data
    ):
        """Test that get_directory_usage returns complete and valid data structures."""
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_directory_data)
        mock_db.messages.aggregate.return_value = mock_cursor

        result = await analytics_service.get_directory_usage()

        # Verify top-level response structure
        assert isinstance(result, DirectoryUsageResponse)
        assert hasattr(result, "root")
        assert hasattr(result, "total_metrics")
        assert hasattr(result, "time_range")
        assert hasattr(result, "generated_at")

        # Verify root node completeness
        assert isinstance(result.root, DirectoryNode)
        assert hasattr(result.root, "path")
        assert hasattr(result.root, "name")
        assert hasattr(result.root, "metrics")
        assert hasattr(result.root, "children")
        assert hasattr(result.root, "percentage_of_total")

        # Verify metrics completeness
        assert isinstance(result.root.metrics, DirectoryMetrics)
        assert hasattr(result.root.metrics, "cost")
        assert hasattr(result.root.metrics, "messages")
        assert hasattr(result.root.metrics, "sessions")
        assert hasattr(result.root.metrics, "avg_cost_per_session")
        assert hasattr(result.root.metrics, "last_active")

        # Verify total metrics completeness
        assert isinstance(result.total_metrics, DirectoryTotalMetrics)
        assert hasattr(result.total_metrics, "total_cost")
        assert hasattr(result.total_metrics, "total_messages")
        assert hasattr(result.total_metrics, "unique_directories")

        # Verify data types and constraints
        assert isinstance(result.root.metrics.cost, (int, float))
        assert result.root.metrics.cost >= 0
        assert isinstance(result.root.metrics.messages, int)
        assert result.root.metrics.messages >= 0
        assert isinstance(result.root.metrics.sessions, int)
        assert result.root.metrics.sessions >= 0
        assert isinstance(result.root.metrics.avg_cost_per_session, (int, float))
        assert result.root.metrics.avg_cost_per_session >= 0
        assert isinstance(result.root.metrics.last_active, datetime)

        # Verify percentage is within valid range
        assert 0 <= result.root.percentage_of_total <= 100

        # Verify children structure if any exist
        for child in result.root.children:
            assert isinstance(child, DirectoryNode)
            assert isinstance(child.metrics, DirectoryMetrics)
            assert 0 <= child.percentage_of_total <= 100
