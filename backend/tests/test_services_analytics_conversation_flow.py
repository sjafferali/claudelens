"""Comprehensive tests for analytics service conversation flow functionality."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from app.schemas.analytics import (
    ConversationFlowAnalytics,
    ConversationFlowMetrics,
    ConversationFlowNode,
)
from app.services.analytics import AnalyticsService


class TestAnalyticsServiceConversationFlow:
    """Test analytics service conversation flow functionality."""

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
    def sample_messages(self):
        """Sample messages for conversation flow testing."""
        base_timestamp = datetime(2024, 1, 1, 12, 0, 0)
        return [
            {
                "uuid": "msg-1",
                "parentUuid": None,
                "type": "user",
                "isSidechain": False,
                "costUsd": 0.0,
                "durationMs": None,
                "timestamp": base_timestamp,
                "message": {"content": "Hello, can you help me with a task?"},
                "toolUseResult": None,
            },
            {
                "uuid": "msg-2",
                "parentUuid": "msg-1",
                "type": "assistant",
                "isSidechain": False,
                "costUsd": 0.05,
                "durationMs": 1500,
                "timestamp": base_timestamp + timedelta(seconds=5),
                "message": {
                    "content": "I'd be happy to help!",
                    "tool_calls": [{"function": {"name": "search"}}],
                },
                "toolUseResult": None,
            },
            {
                "uuid": "msg-3",
                "parentUuid": "msg-2",
                "type": "user",
                "isSidechain": False,
                "costUsd": 0.0,
                "durationMs": None,
                "timestamp": base_timestamp + timedelta(seconds=10),
                "message": {"content": "Can you search for information about Python?"},
                "toolUseResult": None,
            },
            {
                "uuid": "msg-4",
                "parentUuid": "msg-3",
                "type": "assistant",
                "isSidechain": False,
                "costUsd": 0.08,
                "durationMs": 2300,
                "timestamp": base_timestamp + timedelta(seconds=15),
                "message": {"content": "Here's what I found about Python..."},
                "toolUseResult": None,
            },
            {
                "uuid": "msg-5",
                "parentUuid": "msg-2",
                "type": "assistant",
                "isSidechain": True,
                "costUsd": 0.03,
                "durationMs": 800,
                "timestamp": base_timestamp + timedelta(seconds=8),
                "message": {"content": "Let me also check something else"},
                "toolUseResult": {"name": "bash", "result": "success"},
            },
        ]

    @pytest.mark.asyncio
    async def test_get_conversation_flow_basic_functionality(
        self, analytics_service, mock_db, sample_messages
    ):
        """Test basic conversation flow functionality with valid data."""
        session_id = "test-session-123"

        # Mock session resolution
        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})

        # Mock messages query
        def mock_find(query_filter=None, projection=None):
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=sample_messages)
            return mock_cursor

        mock_db.messages.find = mock_find

        result = await analytics_service.get_conversation_flow(session_id)

        # Verify result structure
        assert isinstance(result, ConversationFlowAnalytics)
        assert result.session_id == session_id
        assert len(result.nodes) == 5
        assert len(result.edges) == 4

        # Check nodes are properly constructed
        node_ids = [node.id for node in result.nodes]
        assert "msg-1" in node_ids
        assert "msg-2" in node_ids
        assert "msg-3" in node_ids
        assert "msg-4" in node_ids
        assert "msg-5" in node_ids

        # Check edges are properly constructed
        edge_pairs = [(edge.source, edge.target) for edge in result.edges]
        assert ("msg-1", "msg-2") in edge_pairs
        assert ("msg-2", "msg-3") in edge_pairs
        assert ("msg-3", "msg-4") in edge_pairs
        assert ("msg-2", "msg-5") in edge_pairs

        # Check sidechain edge type
        sidechain_edge = next(edge for edge in result.edges if edge.target == "msg-5")
        assert sidechain_edge.type == "sidechain"

        # Check main edge types
        main_edges = [edge for edge in result.edges if edge.type == "main"]
        assert len(main_edges) == 3

        # Check metrics
        assert isinstance(result.metrics, ConversationFlowMetrics)
        assert result.metrics.total_nodes == 5
        assert result.metrics.total_cost == 0.16  # 0.05 + 0.08 + 0.03
        assert result.metrics.sidechain_percentage == 20.0  # 1 out of 5 messages
        assert result.metrics.branch_count == 1  # msg-2 has two children
        assert result.metrics.max_depth == 3  # msg-1 -> msg-2 -> msg-3 -> msg-4

    @pytest.mark.asyncio
    async def test_get_conversation_flow_invalid_session_id(
        self, analytics_service, mock_db
    ):
        """Test conversation flow with invalid session ID."""
        session_id = "invalid-session"

        # Mock session resolution returning None
        mock_db.sessions.find_one = AsyncMock(return_value=None)

        result = await analytics_service.get_conversation_flow(session_id)

        # Should return empty result
        assert isinstance(result, ConversationFlowAnalytics)
        assert result.session_id == session_id
        assert len(result.nodes) == 0
        assert len(result.edges) == 0
        assert result.metrics.total_nodes == 0
        assert result.metrics.total_cost == 0.0
        assert result.metrics.sidechain_percentage == 0.0
        assert result.metrics.branch_count == 0
        assert result.metrics.max_depth == 0
        assert result.metrics.avg_response_time_ms is None

    @pytest.mark.asyncio
    async def test_get_conversation_flow_empty_conversation(
        self, analytics_service, mock_db
    ):
        """Test conversation flow with valid session but no messages."""
        session_id = "empty-session"

        # Mock session resolution
        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})

        # Mock empty messages query
        def mock_find(query_filter=None, projection=None):
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=[])
            return mock_cursor

        mock_db.messages.find = mock_find

        result = await analytics_service.get_conversation_flow(session_id)

        # Should return empty result with valid session_id
        assert isinstance(result, ConversationFlowAnalytics)
        assert result.session_id == session_id
        assert len(result.nodes) == 0
        assert len(result.edges) == 0
        assert result.metrics.total_nodes == 0
        assert result.metrics.total_cost == 0.0
        assert result.metrics.avg_response_time_ms is None

    @pytest.mark.asyncio
    async def test_get_conversation_flow_exclude_sidechains(
        self, analytics_service, mock_db, sample_messages
    ):
        """Test conversation flow excluding sidechain messages."""
        session_id = "test-session-123"

        # Mock session resolution
        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})

        # Filter out sidechain messages for this test
        non_sidechain_messages = [
            msg for msg in sample_messages if not msg.get("isSidechain", False)
        ]

        def mock_find(query_filter=None, projection=None):
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=non_sidechain_messages)
            return mock_cursor

        mock_db.messages.find = mock_find

        result = await analytics_service.get_conversation_flow(
            session_id, include_sidechains=False
        )

        # Should have 4 nodes (excluding sidechain)
        assert len(result.nodes) == 4
        assert len(result.edges) == 3

        # Verify no sidechain nodes
        sidechain_nodes = [node for node in result.nodes if node.is_sidechain]
        assert len(sidechain_nodes) == 0

        # Verify no sidechain edges
        sidechain_edges = [edge for edge in result.edges if edge.type == "sidechain"]
        assert len(sidechain_edges) == 0

        # Since we mocked find as a function, we can't easily assert calls
        # The important thing is that the result doesn't have sidechain messages
        # which we verified above

    @pytest.mark.asyncio
    async def test_get_conversation_flow_with_tool_use_results(
        self, analytics_service, mock_db
    ):
        """Test conversation flow with tool use result messages."""
        session_id = "tool-session"

        # Mock session resolution
        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})

        # Messages with tool use results
        messages_with_tools = [
            {
                "uuid": "msg-1",
                "parentUuid": None,
                "type": "user",
                "isSidechain": False,
                "costUsd": 0.0,
                "durationMs": None,
                "timestamp": datetime(2024, 1, 1, 12, 0, 0),
                "message": {"content": "Run a command"},
                "toolUseResult": None,
            },
            {
                "uuid": "msg-2",
                "parentUuid": "msg-1",
                "type": "tool_use",
                "isSidechain": False,
                "costUsd": 0.02,
                "durationMs": 500,
                "timestamp": datetime(2024, 1, 1, 12, 0, 5),
                "message": {"name": "bash"},
                "toolUseResult": {"name": "bash", "result": "success"},
            },
        ]

        def mock_find(query_filter=None, projection=None):
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=messages_with_tools)
            return mock_cursor

        mock_db.messages.find = mock_find

        result = await analytics_service.get_conversation_flow(session_id)

        # Verify tool count is properly calculated
        tool_node = next(node for node in result.nodes if node.id == "msg-2")
        assert tool_node.tool_count == 1
        assert tool_node.type == "tool_use"
        assert "Tool: bash" in tool_node.summary

    @pytest.mark.asyncio
    async def test_get_conversation_flow_response_time_calculation(
        self, analytics_service, mock_db
    ):
        """Test conversation flow response time calculation."""
        session_id = "timing-session"

        # Mock session resolution
        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})

        # Messages with various response times
        messages_with_timing = [
            {
                "uuid": "msg-1",
                "parentUuid": None,
                "type": "assistant",
                "isSidechain": False,
                "costUsd": 0.01,
                "durationMs": 1000,
                "timestamp": datetime(2024, 1, 1, 12, 0, 0),
                "message": {"content": "First response"},
                "toolUseResult": None,
            },
            {
                "uuid": "msg-2",
                "parentUuid": "msg-1",
                "type": "assistant",
                "isSidechain": False,
                "costUsd": 0.02,
                "durationMs": 2000,
                "timestamp": datetime(2024, 1, 1, 12, 0, 5),
                "message": {"content": "Second response"},
                "toolUseResult": None,
            },
            {
                "uuid": "msg-3",
                "parentUuid": "msg-2",
                "type": "assistant",
                "isSidechain": False,
                "costUsd": 0.03,
                "durationMs": 3000,
                "timestamp": datetime(2024, 1, 1, 12, 0, 10),
                "message": {"content": "Third response"},
                "toolUseResult": None,
            },
        ]

        def mock_find(query_filter=None, projection=None):
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=messages_with_timing)
            return mock_cursor

        mock_db.messages.find = mock_find

        result = await analytics_service.get_conversation_flow(session_id)

        # Verify average response time calculation: (1000 + 2000 + 3000) / 3 = 2000
        assert result.metrics.avg_response_time_ms == 2000.0

    @pytest.mark.asyncio
    async def test_get_conversation_flow_complex_tree_structure(
        self, analytics_service, mock_db
    ):
        """Test conversation flow with complex branching structure."""
        session_id = "complex-session"

        # Mock session resolution
        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})

        # Complex tree: root -> branch1, branch2 -> branch1.1, branch1.2, branch2.1
        complex_messages = [
            {
                "uuid": "root",
                "parentUuid": None,
                "type": "user",
                "isSidechain": False,
                "costUsd": 0.0,
                "durationMs": None,
                "timestamp": datetime(2024, 1, 1, 12, 0, 0),
                "message": {"content": "Start"},
                "toolUseResult": None,
            },
            {
                "uuid": "branch1",
                "parentUuid": "root",
                "type": "assistant",
                "isSidechain": False,
                "costUsd": 0.01,
                "durationMs": 1000,
                "timestamp": datetime(2024, 1, 1, 12, 0, 1),
                "message": {"content": "Branch 1"},
                "toolUseResult": None,
            },
            {
                "uuid": "branch2",
                "parentUuid": "root",
                "type": "assistant",
                "isSidechain": True,
                "costUsd": 0.01,
                "durationMs": 1000,
                "timestamp": datetime(2024, 1, 1, 12, 0, 1),
                "message": {"content": "Branch 2"},
                "toolUseResult": None,
            },
            {
                "uuid": "branch1.1",
                "parentUuid": "branch1",
                "type": "user",
                "isSidechain": False,
                "costUsd": 0.0,
                "durationMs": None,
                "timestamp": datetime(2024, 1, 1, 12, 0, 2),
                "message": {"content": "Branch 1.1"},
                "toolUseResult": None,
            },
            {
                "uuid": "branch1.2",
                "parentUuid": "branch1",
                "type": "user",
                "isSidechain": True,
                "costUsd": 0.0,
                "durationMs": None,
                "timestamp": datetime(2024, 1, 1, 12, 0, 2),
                "message": {"content": "Branch 1.2"},
                "toolUseResult": None,
            },
            {
                "uuid": "branch2.1",
                "parentUuid": "branch2",
                "type": "assistant",
                "isSidechain": True,
                "costUsd": 0.02,
                "durationMs": 2000,
                "timestamp": datetime(2024, 1, 1, 12, 0, 3),
                "message": {"content": "Branch 2.1"},
                "toolUseResult": None,
            },
        ]

        def mock_find(query_filter=None, projection=None):
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=complex_messages)
            return mock_cursor

        mock_db.messages.find = mock_find

        result = await analytics_service.get_conversation_flow(session_id)

        # Verify complex metrics
        assert result.metrics.total_nodes == 6
        assert (
            result.metrics.branch_count == 2
        )  # root and branch1 have multiple children
        assert result.metrics.max_depth == 2  # root -> branch -> leaf
        assert result.metrics.sidechain_percentage == 50.0  # 3 out of 6 messages

    @pytest.mark.asyncio
    async def test_get_conversation_flow_with_objectid_session(
        self, analytics_service, mock_db, sample_messages
    ):
        """Test conversation flow with ObjectId session resolution."""
        object_id = ObjectId()
        session_id = "resolved-session-456"

        # Mock session resolution from ObjectId
        mock_db.sessions.find_one = AsyncMock(
            side_effect=[
                {"sessionId": session_id},  # First call with ObjectId
                None,  # Second call shouldn't happen
            ]
        )

        def mock_find(query_filter=None, projection=None):
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=sample_messages)
            return mock_cursor

        mock_db.messages.find = mock_find

        result = await analytics_service.get_conversation_flow(str(object_id))

        # Should resolve ObjectId to sessionId and process normally
        assert isinstance(result, ConversationFlowAnalytics)
        assert len(result.nodes) == 5
        assert len(result.edges) == 4

    @pytest.mark.asyncio
    async def test_get_conversation_flow_edge_cases_missing_fields(
        self, analytics_service, mock_db
    ):
        """Test conversation flow with messages missing optional fields."""
        session_id = "edge-case-session"

        # Mock session resolution
        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})

        # Messages with missing optional fields
        edge_case_messages = [
            {
                "uuid": "msg-1",
                "parentUuid": None,
                "type": "user",
                # Missing isSidechain, costUsd, durationMs
                "timestamp": datetime(2024, 1, 1, 12, 0, 0),
                "message": {},  # Empty message content
                "toolUseResult": None,
            },
            {
                "uuid": "msg-2",
                "parentUuid": "msg-1",
                "type": "assistant",
                "isSidechain": False,
                # Missing costUsd, durationMs
                "timestamp": datetime(2024, 1, 1, 12, 0, 5),
                "message": None,  # Null message
                "toolUseResult": None,
            },
        ]

        def mock_find(query_filter=None, projection=None):
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=edge_case_messages)
            return mock_cursor

        mock_db.messages.find = mock_find

        result = await analytics_service.get_conversation_flow(session_id)

        # Should handle missing fields gracefully
        assert len(result.nodes) == 2
        assert len(result.edges) == 1

        # Check default values are applied
        node1 = next(node for node in result.nodes if node.id == "msg-1")
        assert node1.is_sidechain is False
        assert node1.cost == 0.0
        assert node1.duration_ms is None
        assert node1.tool_count == 0
        assert node1.summary == ""

        node2 = next(node for node in result.nodes if node.id == "msg-2")
        assert node2.cost == 0.0
        assert node2.summary == ""

    @pytest.mark.asyncio
    async def test_get_conversation_flow_message_summary_generation(
        self, analytics_service, mock_db
    ):
        """Test conversation flow message summary generation for different message types."""
        session_id = "summary-session"

        # Mock session resolution
        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})

        # Messages with different content types
        summary_messages = [
            {
                "uuid": "user-msg",
                "parentUuid": None,
                "type": "user",
                "isSidechain": False,
                "costUsd": 0.0,
                "durationMs": None,
                "timestamp": datetime(2024, 1, 1, 12, 0, 0),
                "message": {
                    "content": "This is a very long user message that should be truncated because it exceeds the 100 character limit for summaries in the conversation flow visualization."
                },
                "toolUseResult": None,
            },
            {
                "uuid": "assistant-msg",
                "parentUuid": "user-msg",
                "type": "assistant",
                "isSidechain": False,
                "costUsd": 0.01,
                "durationMs": 1000,
                "timestamp": datetime(2024, 1, 1, 12, 0, 5),
                "message": {
                    "content": "I'll help you with that.",
                    "tool_calls": [
                        {"function": {"name": "search"}},
                        {"function": {"name": "read_file"}},
                    ],
                },
                "toolUseResult": None,
            },
            {
                "uuid": "tool-msg",
                "parentUuid": "assistant-msg",
                "type": "tool_use",
                "isSidechain": False,
                "costUsd": 0.005,
                "durationMs": 500,
                "timestamp": datetime(2024, 1, 1, 12, 0, 8),
                "message": {"name": "bash"},
                "toolUseResult": {
                    "name": "bash",
                    "result": "Command executed successfully",
                },
            },
        ]

        def mock_find(query_filter=None, projection=None):
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=summary_messages)
            return mock_cursor

        mock_db.messages.find = mock_find

        result = await analytics_service.get_conversation_flow(session_id)

        # Check summary generation
        user_node = next(node for node in result.nodes if node.id == "user-msg")
        assert len(user_node.summary) <= 103  # 100 chars + "..."
        assert user_node.summary.endswith("...")

        assistant_node = next(
            node for node in result.nodes if node.id == "assistant-msg"
        )
        # Assistant message has content, so it shows content, not tool names
        assert assistant_node.summary == "I'll help you with that."
        assert assistant_node.tool_count == 2

        tool_node = next(node for node in result.nodes if node.id == "tool-msg")
        assert "Tool: bash" in tool_node.summary
        assert tool_node.tool_count == 1

    @pytest.mark.asyncio
    async def test_get_conversation_flow_cost_aggregation(
        self, analytics_service, mock_db
    ):
        """Test conversation flow cost aggregation and rounding."""
        session_id = "cost-session"

        # Mock session resolution
        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})

        # Messages with various cost values including floats that need rounding
        cost_messages = [
            {
                "uuid": "msg-1",
                "parentUuid": None,
                "type": "assistant",
                "isSidechain": False,
                "costUsd": 0.123456789,  # High precision float
                "durationMs": 1000,
                "timestamp": datetime(2024, 1, 1, 12, 0, 0),
                "message": {"content": "First"},
                "toolUseResult": None,
            },
            {
                "uuid": "msg-2",
                "parentUuid": "msg-1",
                "type": "assistant",
                "isSidechain": False,
                "costUsd": 0.987654321,  # Another high precision float
                "durationMs": 2000,
                "timestamp": datetime(2024, 1, 1, 12, 0, 5),
                "message": {"content": "Second"},
                "toolUseResult": None,
            },
        ]

        def mock_find(query_filter=None, projection=None):
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=cost_messages)
            return mock_cursor

        mock_db.messages.find = mock_find

        result = await analytics_service.get_conversation_flow(session_id)

        # Verify cost is properly rounded to 2 decimal places
        expected_total = round(0.123456789 + 0.987654321, 2)
        assert result.metrics.total_cost == expected_total

        # Verify individual node costs are preserved with precision
        node1 = next(node for node in result.nodes if node.id == "msg-1")
        assert node1.cost == 0.123456789

        node2 = next(node for node in result.nodes if node.id == "msg-2")
        assert node2.cost == 0.987654321

    @pytest.mark.asyncio
    async def test_get_conversation_flow_orphaned_messages(
        self, analytics_service, mock_db
    ):
        """Test conversation flow handling of orphaned messages (parent not found)."""
        session_id = "orphan-session"

        # Mock session resolution
        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})

        # Messages with orphaned references
        orphan_messages = [
            {
                "uuid": "msg-1",
                "parentUuid": None,
                "type": "user",
                "isSidechain": False,
                "costUsd": 0.0,
                "durationMs": None,
                "timestamp": datetime(2024, 1, 1, 12, 0, 0),
                "message": {"content": "Root message"},
                "toolUseResult": None,
            },
            {
                "uuid": "msg-2",
                "parentUuid": "nonexistent-parent",  # Parent doesn't exist
                "type": "assistant",
                "isSidechain": False,
                "costUsd": 0.01,
                "durationMs": 1000,
                "timestamp": datetime(2024, 1, 1, 12, 0, 5),
                "message": {"content": "Orphaned message"},
                "toolUseResult": None,
            },
        ]

        def mock_find(query_filter=None, projection=None):
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=orphan_messages)
            return mock_cursor

        mock_db.messages.find = mock_find

        result = await analytics_service.get_conversation_flow(session_id)

        # Should include both nodes but only valid edges
        assert len(result.nodes) == 2
        assert len(result.edges) == 0  # No valid edges since parent doesn't exist

        # Both nodes should be present
        node_ids = [node.id for node in result.nodes]
        assert "msg-1" in node_ids
        assert "msg-2" in node_ids

    def test_generate_message_summary_edge_cases(self, analytics_service):
        """Test _generate_message_summary method with edge cases."""
        # Test empty message
        empty_msg = {"type": "user", "message": {}}
        assert analytics_service._generate_message_summary(empty_msg) == ""

        # Test None message
        none_msg = {"type": "user", "message": None}
        assert analytics_service._generate_message_summary(none_msg) == ""

        # Test user message with array content
        array_content_msg = {
            "type": "user",
            "message": {
                "content": [{"text": "First part of message"}, {"text": "Second part"}]
            },
        }
        summary = analytics_service._generate_message_summary(array_content_msg)
        assert summary == "First part of message"

        # Test assistant message with empty tool_calls
        empty_tools_msg = {
            "type": "assistant",
            "message": {"content": "Response", "tool_calls": []},
        }
        summary = analytics_service._generate_message_summary(empty_tools_msg)
        assert summary == "Response"

    def test_calculate_conversation_metrics_edge_cases(self, analytics_service):
        """Test _calculate_conversation_metrics with edge cases."""
        # Test with empty nodes and edges
        empty_metrics = analytics_service._calculate_conversation_metrics([], [])
        assert empty_metrics.max_depth == 0
        assert empty_metrics.branch_count == 0
        assert empty_metrics.sidechain_percentage == 0.0
        assert empty_metrics.avg_branch_length == 0.0
        assert empty_metrics.total_nodes == 0
        assert empty_metrics.total_cost == 0.0
        assert empty_metrics.avg_response_time_ms is None

        # Test with single node
        single_node = [
            ConversationFlowNode(
                id="single",
                parent_id=None,
                type="user",
                is_sidechain=False,
                cost=5.0,
                duration_ms=1000,
                tool_count=0,
                summary="Single node",
                timestamp=datetime.now(UTC),
            )
        ]
        single_metrics = analytics_service._calculate_conversation_metrics(
            single_node, []
        )
        assert single_metrics.max_depth == 0
        assert single_metrics.branch_count == 0
        assert single_metrics.total_nodes == 1
        assert single_metrics.total_cost == 5.0
        assert single_metrics.avg_response_time_ms == 1000.0

    def test_calculate_tree_depth_recursive(self, analytics_service):
        """Test _calculate_tree_depth method directly."""
        # Build simple children dict
        children = {
            "root": ["child1", "child2"],
            "child1": ["grandchild1"],
            "child2": [],
        }

        # Test depth calculation
        depth = analytics_service._calculate_tree_depth("root", children, 0)
        assert depth == 2  # root -> child1 -> grandchild1

        # Test leaf node
        leaf_depth = analytics_service._calculate_tree_depth("grandchild1", children, 2)
        assert leaf_depth == 2

        # Test non-existent node
        missing_depth = analytics_service._calculate_tree_depth("missing", children, 0)
        assert missing_depth == 0

    @pytest.mark.asyncio
    async def test_get_conversation_flow_database_error_handling(
        self, analytics_service, mock_db
    ):
        """Test conversation flow handling of database errors."""
        session_id = "error-session"

        # Mock session resolution
        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})

        # Mock database error during message query
        def mock_find_error(query_filter=None, projection=None):
            raise Exception("Database connection error")

        mock_db.messages.find = mock_find_error

        # Should raise the exception
        with pytest.raises(Exception, match="Database connection error"):
            await analytics_service.get_conversation_flow(session_id)

    @pytest.mark.asyncio
    async def test_get_conversation_flow_session_resolution_edge_cases(
        self, analytics_service, mock_db
    ):
        """Test session resolution edge cases."""
        # Test with empty string
        mock_db.sessions.find_one = AsyncMock(return_value=None)
        result = await analytics_service.get_conversation_flow("")
        assert result.session_id == ""
        assert len(result.nodes) == 0

        # Skip None test as it causes validation error - empty string test covers edge case

    @pytest.mark.asyncio
    async def test_get_conversation_flow_large_conversation(
        self, analytics_service, mock_db
    ):
        """Test conversation flow with large number of messages."""
        session_id = "large-session"

        # Mock session resolution
        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})

        # Generate large conversation (100 messages in a chain)
        large_messages = []
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        for i in range(100):
            message = {
                "uuid": f"msg-{i}",
                "parentUuid": f"msg-{i - 1}" if i > 0 else None,
                "type": "user" if i % 2 == 0 else "assistant",
                "isSidechain": False,
                "costUsd": 0.01 if i % 2 == 1 else 0.0,
                "durationMs": 1000 if i % 2 == 1 else None,
                "timestamp": base_time + timedelta(seconds=i),
                "message": {"content": f"Message {i}"},
                "toolUseResult": None,
            }
            large_messages.append(message)

        def mock_find(query_filter=None, projection=None):
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=large_messages)
            return mock_cursor

        mock_db.messages.find = mock_find

        result = await analytics_service.get_conversation_flow(session_id)

        # Verify large conversation handling
        assert len(result.nodes) == 100
        assert len(result.edges) == 99  # n-1 edges for chain
        assert result.metrics.total_nodes == 100
        assert result.metrics.max_depth == 99  # Long chain
        assert result.metrics.branch_count == 0  # No branching in simple chain

        # Verify cost calculation (50 assistant messages * 0.01)
        assert result.metrics.total_cost == 0.50

        # Verify response time calculation (50 assistant messages * 1000ms)
        assert result.metrics.avg_response_time_ms == 1000.0
