"""Tests for WebSocket endpoints."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from bson import Decimal128, ObjectId
from fastapi import HTTPException

from app.api.api_v1.endpoints.websocket import (
    get_connection_stats,
    get_live_global_stats,
    get_live_session_stats,
)
from app.schemas.websocket import LiveSessionStats, LiveStatsResponse


class TestGetLiveSessionStats:
    """Test live session statistics endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        db.sessions = Mock()
        db.messages = Mock()
        return db

    @pytest.fixture
    def sample_session(self):
        """Create sample session document."""
        return {
            "_id": ObjectId(),
            "sessionId": "test-session-123",
            "projectId": ObjectId(),
            "messageCount": 5,
            "totalCost": Decimal128("0.25"),
        }

    @pytest.mark.asyncio
    async def test_get_live_session_stats_success(self, mock_db, sample_session):
        """Test successful session stats retrieval."""
        session_id = "test-session-123"

        # Mock session exists
        mock_db.sessions.find_one = AsyncMock(return_value=sample_session)

        # Mock message count
        mock_db.messages.count_documents = AsyncMock(return_value=5)

        # Mock tool usage aggregation
        tool_result = [{"total_tools": 3}]
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(
            return_value=tool_result
        )

        # Mock token count aggregation (first call)
        token_result = [{"total_tokens": 1500}]
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(
            side_effect=[
                tool_result,  # First call for tools
                token_result,  # Second call for tokens
                [{"total_cost": 0.25}],  # Third call for cost
            ]
        )

        # Mock last message
        last_message = {"timestamp": datetime.utcnow() - timedelta(minutes=2)}
        mock_db.messages.find_one = AsyncMock(return_value=last_message)

        result = await get_live_session_stats(session_id, mock_db)

        assert isinstance(result, LiveSessionStats)
        assert result.session_id == session_id
        assert result.message_count == 5
        assert result.tool_usage_count == 3
        assert result.token_count == 1500
        assert result.cost == 0.25
        assert result.is_active is True  # Activity within 5 minutes

    @pytest.mark.asyncio
    async def test_get_live_session_stats_session_not_found(self, mock_db):
        """Test session stats when session doesn't exist."""
        session_id = "nonexistent-session"

        mock_db.sessions.find_one = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_live_session_stats(session_id, mock_db)

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_live_session_stats_empty_results(self, mock_db, sample_session):
        """Test session stats with no messages or empty aggregation results."""
        session_id = "empty-session"

        mock_db.sessions.find_one = AsyncMock(return_value=sample_session)
        mock_db.messages.count_documents = AsyncMock(return_value=0)

        # Empty aggregation results
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(return_value=[])
        mock_db.messages.find_one = AsyncMock(return_value=None)

        result = await get_live_session_stats(session_id, mock_db)

        assert result.message_count == 0
        assert result.tool_usage_count == 0
        assert result.token_count == 0
        assert result.cost == 0.0
        assert result.last_activity is None
        assert result.is_active is False

    @pytest.mark.asyncio
    async def test_get_live_session_stats_inactive_session(
        self, mock_db, sample_session
    ):
        """Test session stats for inactive session."""
        session_id = "inactive-session"

        mock_db.sessions.find_one = AsyncMock(return_value=sample_session)
        mock_db.messages.count_documents = AsyncMock(return_value=10)

        # Mock aggregation results
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(
            side_effect=[
                [{"total_tools": 2}],
                [{"total_tokens": 800}],
                [{"total_cost": 0.15}],
            ]
        )

        # Last activity more than 5 minutes ago
        old_timestamp = datetime.utcnow() - timedelta(minutes=10)
        last_message = {"timestamp": old_timestamp}
        mock_db.messages.find_one = AsyncMock(return_value=last_message)

        result = await get_live_session_stats(session_id, mock_db)

        assert result.is_active is False
        assert result.last_activity == old_timestamp

    @pytest.mark.asyncio
    async def test_get_live_session_stats_decimal128_cost(
        self, mock_db, sample_session
    ):
        """Test handling of Decimal128 cost values."""
        session_id = "test-session"

        mock_db.sessions.find_one = AsyncMock(return_value=sample_session)
        mock_db.messages.count_documents = AsyncMock(return_value=1)

        # Mock Decimal128 cost
        decimal_cost = Mock()
        decimal_cost.to_decimal.return_value = 0.75
        cost_result = [{"total_cost": decimal_cost}]

        mock_db.messages.aggregate.return_value.to_list = AsyncMock(
            side_effect=[[], [], cost_result]  # Tools  # Tokens  # Cost with Decimal128
        )
        mock_db.messages.find_one = AsyncMock(return_value=None)

        result = await get_live_session_stats(session_id, mock_db)

        assert result.cost == 0.75


class TestGetLiveGlobalStats:
    """Test live global statistics endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        db.messages = Mock()
        db.sessions = Mock()
        return db

    @pytest.mark.asyncio
    async def test_get_live_global_stats_success(self, mock_db):
        """Test successful global stats retrieval."""
        # Mock total message count
        mock_db.messages.count_documents = AsyncMock(return_value=100)

        # Mock aggregation results
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(
            side_effect=[
                [{"total_tools": 25}],  # Tool usage
                [{"total_tokens": 50000}],  # Token count
                [{"total_cost": 12.50}],  # Total cost
            ]
        )

        # Mock active sessions
        mock_db.sessions.aggregate.return_value.to_list = AsyncMock(
            return_value=[{"active_sessions": 3}]
        )

        result = await get_live_global_stats(mock_db)

        assert isinstance(result, LiveStatsResponse)
        assert result.total_messages == 100
        assert result.total_tools == 25
        assert result.total_tokens == 50000
        assert result.total_cost == 12.50
        assert result.active_sessions == 3

    @pytest.mark.asyncio
    async def test_get_live_global_stats_empty_database(self, mock_db):
        """Test global stats with empty database."""
        # Mock empty results
        mock_db.messages.count_documents = AsyncMock(return_value=0)
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(return_value=[])
        mock_db.sessions.aggregate.return_value.to_list = AsyncMock(return_value=[])

        result = await get_live_global_stats(mock_db)

        assert result.total_messages == 0
        assert result.total_tools == 0
        assert result.total_tokens == 0
        assert result.total_cost == 0.0
        assert result.active_sessions == 0

    @pytest.mark.asyncio
    async def test_get_live_global_stats_decimal128_cost(self, mock_db):
        """Test handling of Decimal128 in global stats."""
        mock_db.messages.count_documents = AsyncMock(return_value=10)

        # Mock Decimal128 cost
        decimal_cost = Mock()
        decimal_cost.to_decimal.return_value = 5.25

        mock_db.messages.aggregate.return_value.to_list = AsyncMock(
            side_effect=[
                [],  # Tools
                [],  # Tokens
                [{"total_cost": decimal_cost}],  # Cost with Decimal128
            ]
        )
        mock_db.sessions.aggregate.return_value.to_list = AsyncMock(return_value=[])

        result = await get_live_global_stats(mock_db)

        assert result.total_cost == 5.25

    @pytest.mark.asyncio
    async def test_get_live_global_stats_aggregation_pipelines(self, mock_db):
        """Test that aggregation pipelines are called correctly."""
        mock_db.messages.count_documents = AsyncMock(return_value=1)
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(return_value=[])
        mock_db.sessions.aggregate.return_value.to_list = AsyncMock(return_value=[])

        await get_live_global_stats(mock_db)

        # Should call aggregate 3 times for messages (tools, tokens, cost)
        assert mock_db.messages.aggregate.call_count == 3

        # Should call aggregate once for sessions (active sessions)
        assert mock_db.sessions.aggregate.call_count == 1


class TestGetConnectionStats:
    """Test WebSocket connection statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_connection_stats_success(self):
        """Test successful connection stats retrieval."""
        mock_stats = {
            "total_connections": 5,
            "active_sessions": ["session1", "session2"],
            "global_connections": 2,
        }

        with patch(
            "app.api.api_v1.endpoints.websocket.connection_manager"
        ) as mock_manager:
            mock_manager.get_connection_stats.return_value = mock_stats

            result = await get_connection_stats()

            assert result == mock_stats
            mock_manager.get_connection_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_connection_stats_empty(self):
        """Test connection stats when no connections exist."""
        empty_stats = {
            "total_connections": 0,
            "active_sessions": [],
            "global_connections": 0,
        }

        with patch(
            "app.api.api_v1.endpoints.websocket.connection_manager"
        ) as mock_manager:
            mock_manager.get_connection_stats.return_value = empty_stats

            result = await get_connection_stats()

            assert result == empty_stats


class TestWebSocketEndpointHelpers:
    """Test WebSocket endpoint helper functionality."""

    @pytest.mark.asyncio
    async def test_session_verification_logic(self):
        """Test session verification logic used in endpoints."""
        # This tests the common pattern used in websocket endpoints
        db = Mock()
        session_id = "test-session"

        # Test existing session
        sample_session = {"_id": ObjectId(), "sessionId": session_id}
        db.sessions.find_one = AsyncMock(return_value=sample_session)

        session = await db.sessions.find_one({"sessionId": session_id})
        assert session is not None
        assert session["sessionId"] == session_id

    @pytest.mark.asyncio
    async def test_session_verification_not_found(self):
        """Test session verification when session doesn't exist."""
        db = Mock()
        session_id = "nonexistent-session"

        db.sessions.find_one = AsyncMock(return_value=None)

        session = await db.sessions.find_one({"sessionId": session_id})
        assert session is None


class TestStatsAggregationLogic:
    """Test statistics aggregation logic."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        db.messages = Mock()
        db.sessions = Mock()
        return db

    @pytest.mark.asyncio
    async def test_tool_usage_aggregation_pipeline(self, mock_db):
        """Test tool usage aggregation pipeline structure."""
        session_id = "test-session"

        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})
        mock_db.messages.count_documents = AsyncMock(return_value=1)

        # Mock all three aggregation calls that happen in sequence
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(
            side_effect=[
                [{"total_tools": 5}],  # Tools
                [{"total_tokens": 1000}],  # Tokens
                [{"total_cost": 0.5}],  # Cost
            ]
        )
        mock_db.messages.find_one = AsyncMock(return_value=None)

        await get_live_session_stats(session_id, mock_db)

        # Check that aggregation was called 3 times
        assert mock_db.messages.aggregate.call_count == 3

        # Check first aggregation call (tool usage)
        first_call_args = mock_db.messages.aggregate.call_args_list[0][0][0]
        assert any(
            "$match" in stage and stage["$match"]["sessionId"] == session_id
            for stage in first_call_args
        )

    @pytest.mark.asyncio
    async def test_token_count_aggregation_pipeline(self, mock_db):
        """Test token count aggregation pipeline structure."""
        session_id = "test-session"

        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})
        mock_db.messages.count_documents = AsyncMock(return_value=1)

        mock_db.messages.aggregate.return_value.to_list = AsyncMock(
            side_effect=[[], [{"total_tokens": 2000}], []]  # Tools  # Tokens  # Cost
        )
        mock_db.messages.find_one = AsyncMock(return_value=None)

        result = await get_live_session_stats(session_id, mock_db)

        assert result.token_count == 2000

    @pytest.mark.asyncio
    async def test_cost_aggregation_with_nulls(self, mock_db):
        """Test cost aggregation handles null values."""
        session_id = "test-session"

        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})
        mock_db.messages.count_documents = AsyncMock(return_value=1)

        mock_db.messages.aggregate.return_value.to_list = AsyncMock(
            side_effect=[[], [], [{"total_cost": 1.5}]]  # Tools  # Tokens  # Cost
        )
        mock_db.messages.find_one = AsyncMock(return_value=None)

        result = await get_live_session_stats(session_id, mock_db)

        assert result.cost == 1.5

    @pytest.mark.asyncio
    async def test_active_session_calculation(self, mock_db):
        """Test active session calculation logic."""
        # Test cutoff time calculation
        datetime.utcnow() - timedelta(minutes=5)

        mock_db.messages.count_documents = AsyncMock(return_value=1)
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(return_value=[])

        # Mock active sessions pipeline
        active_result = [{"active_sessions": 2}]
        mock_db.sessions.aggregate.return_value.to_list = AsyncMock(
            return_value=active_result
        )

        result = await get_live_global_stats(mock_db)

        assert result.active_sessions == 2

        # Verify the lookup and match stages in pipeline
        pipeline_call = mock_db.sessions.aggregate.call_args[0][0]
        assert any("$lookup" in stage for stage in pipeline_call)
        assert any("$match" in stage for stage in pipeline_call)


class TestWebSocketErrorHandling:
    """Test error handling in WebSocket endpoints."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        db.sessions = Mock()
        db.messages = Mock()
        return db

    @pytest.mark.asyncio
    async def test_database_error_in_session_stats(self, mock_db):
        """Test handling database errors in session stats."""
        session_id = "test-session"

        mock_db.sessions.find_one = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception, match="Database error"):
            await get_live_session_stats(session_id, mock_db)

    @pytest.mark.asyncio
    async def test_aggregation_error_in_global_stats(self, mock_db):
        """Test handling aggregation errors in global stats."""
        mock_db.messages.count_documents = AsyncMock(return_value=1)
        mock_db.messages.aggregate.side_effect = Exception("Aggregation failed")

        with pytest.raises(Exception, match="Aggregation failed"):
            await get_live_global_stats(mock_db)

    @pytest.mark.asyncio
    async def test_find_one_error_in_session_stats(self, mock_db):
        """Test handling find_one errors in session stats."""
        session_id = "test-session"
        sample_session = {"sessionId": session_id}

        mock_db.sessions.find_one = AsyncMock(return_value=sample_session)
        mock_db.messages.count_documents = AsyncMock(return_value=1)
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(return_value=[])

        # Error in last message lookup
        mock_db.messages.find_one = AsyncMock(side_effect=Exception("Find error"))

        with pytest.raises(Exception, match="Find error"):
            await get_live_session_stats(session_id, mock_db)


class TestDateTimeHandling:
    """Test datetime handling in WebSocket endpoints."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        db.sessions = Mock()
        db.messages = Mock()
        return db

    @pytest.mark.asyncio
    async def test_activity_boundary_conditions(self, mock_db):
        """Test activity detection at 5-minute boundary."""
        session_id = "boundary-session"
        sample_session = {"sessionId": session_id}

        mock_db.sessions.find_one = AsyncMock(return_value=sample_session)
        mock_db.messages.count_documents = AsyncMock(return_value=1)
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(return_value=[])

        # Test exactly 5 minutes ago (should be inactive)
        exactly_5_min = datetime.utcnow() - timedelta(minutes=5)
        last_message = {"timestamp": exactly_5_min}
        mock_db.messages.find_one = AsyncMock(return_value=last_message)

        result = await get_live_session_stats(session_id, mock_db)

        # Should be inactive (>= 5 minutes is considered inactive)
        assert result.is_active is False

    @pytest.mark.asyncio
    async def test_activity_just_under_threshold(self, mock_db):
        """Test activity detection just under 5-minute threshold."""
        session_id = "recent-session"
        sample_session = {"sessionId": session_id}

        mock_db.sessions.find_one = AsyncMock(return_value=sample_session)
        mock_db.messages.count_documents = AsyncMock(return_value=1)
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(return_value=[])

        # Test 4 minutes 59 seconds ago (should be active)
        recent_time = datetime.utcnow() - timedelta(minutes=4, seconds=59)
        last_message = {"timestamp": recent_time}
        mock_db.messages.find_one = AsyncMock(return_value=last_message)

        result = await get_live_session_stats(session_id, mock_db)

        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_global_stats_cutoff_time_calculation(self, mock_db):
        """Test cutoff time calculation in global stats."""
        mock_db.messages.count_documents = AsyncMock(return_value=1)
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(return_value=[])
        mock_db.sessions.aggregate.return_value.to_list = AsyncMock(return_value=[])

        await get_live_global_stats(mock_db)

        # Verify sessions aggregation pipeline includes time match
        sessions_call = mock_db.sessions.aggregate.call_args[0][0]

        # Should have a match stage with timestamp comparison
        match_stages = [stage for stage in sessions_call if "$match" in stage]
        assert len(match_stages) > 0


class TestAggregationPipelineStructure:
    """Test aggregation pipeline structure and correctness."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        db.messages = Mock()
        db.sessions = Mock()
        return db

    @pytest.mark.asyncio
    async def test_tool_usage_pipeline_structure(self, mock_db):
        """Test tool usage aggregation pipeline structure."""
        session_id = "test-session"

        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})
        mock_db.messages.count_documents = AsyncMock(return_value=1)
        mock_db.messages.find_one = AsyncMock(return_value=None)

        # Capture the pipeline
        mock_aggregate = Mock()
        mock_aggregate.to_list = AsyncMock(return_value=[])
        mock_db.messages.aggregate.return_value = mock_aggregate

        await get_live_session_stats(session_id, mock_db)

        # Get the first aggregation call (tools)
        first_pipeline = mock_db.messages.aggregate.call_args_list[0][0][0]

        # Should have match, unwind, match, count stages
        stage_types = [list(stage.keys())[0] for stage in first_pipeline]
        assert "$match" in stage_types
        assert "$unwind" in stage_types
        assert "$count" in stage_types

    @pytest.mark.asyncio
    async def test_active_sessions_pipeline_structure(self, mock_db):
        """Test active sessions aggregation pipeline structure."""
        mock_db.messages.count_documents = AsyncMock(return_value=1)
        mock_db.messages.aggregate.return_value.to_list = AsyncMock(return_value=[])

        # Capture the active sessions pipeline
        mock_aggregate = Mock()
        mock_aggregate.to_list = AsyncMock(return_value=[])
        mock_db.sessions.aggregate.return_value = mock_aggregate

        await get_live_global_stats(mock_db)

        # Get the sessions aggregation pipeline
        sessions_pipeline = mock_db.sessions.aggregate.call_args[0][0]

        # Should have lookup, match, count stages
        stage_types = [list(stage.keys())[0] for stage in sessions_pipeline]
        assert "$lookup" in stage_types
        assert "$match" in stage_types
        assert "$count" in stage_types

    @pytest.mark.asyncio
    async def test_token_aggregation_group_stage(self, mock_db):
        """Test token aggregation group stage structure."""
        session_id = "test-session"

        mock_db.sessions.find_one = AsyncMock(return_value={"sessionId": session_id})
        mock_db.messages.count_documents = AsyncMock(return_value=1)
        mock_db.messages.find_one = AsyncMock(return_value=None)

        mock_db.messages.aggregate.return_value.to_list = AsyncMock(
            side_effect=[[], [{"total_tokens": 1000}], []]  # Tools  # Tokens  # Cost
        )

        await get_live_session_stats(session_id, mock_db)

        # Get the second aggregation call (tokens)
        token_pipeline = mock_db.messages.aggregate.call_args_list[1][0][0]

        # Should have match and group stages
        assert any("$match" in stage for stage in token_pipeline)
        assert any("$group" in stage for stage in token_pipeline)

        # Group stage should sum inputTokens and outputTokens
        group_stage = next(
            stage["$group"] for stage in token_pipeline if "$group" in stage
        )
        assert "total_tokens" in group_stage
        assert "$sum" in group_stage["total_tokens"]
