"""Integration tests for search functionality."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from app.schemas.search import SearchFilters, SearchResponse
from app.services.search import SearchService


@pytest.fixture
def mock_db():
    """Create a mock database for search testing."""
    db = MagicMock()

    # Mock collections with async methods
    db.messages = MagicMock()
    db.sessions = MagicMock()
    db.projects = MagicMock()
    db.search_logs = MagicMock()

    # Make collection methods async
    for collection in [db.messages, db.sessions, db.projects, db.search_logs]:
        collection.insert_one = AsyncMock()
        collection.find_one = AsyncMock(return_value=None)
        collection.update_one = AsyncMock()
        collection.aggregate = MagicMock()

    return db


@pytest.fixture
def search_service(mock_db):
    """Create SearchService with mock database."""
    return SearchService(mock_db)


@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
    return [
        {
            "_id": ObjectId(),
            "uuid": "msg_001",
            "type": "user",
            "sessionId": "session_001",
            "content": "How do I write a Python function?",
            "timestamp": datetime.now(UTC),
            "model": "claude-3-sonnet",
            "score": 1.5,
            "session_data": {
                "summary": "Python programming help",
                "projectPath": "/test/project",
            },
            "project_data": {"name": "Test Project", "description": "A test project"},
        },
        {
            "_id": ObjectId(),
            "uuid": "msg_002",
            "type": "assistant",
            "sessionId": "session_001",
            "content": "Here's how to write a Python function:\ndef hello():\n    print('Hello')",
            "timestamp": datetime.now(UTC),
            "model": "claude-3-sonnet",
            "score": 1.2,
            "session_data": {
                "summary": "Python programming help",
                "projectPath": "/test/project",
            },
            "project_data": {"name": "Test Project", "description": "A test project"},
        },
    ]


class TestSearchIntegration:
    """Integration tests for search functionality."""

    @pytest.mark.asyncio
    async def test_search_messages_basic(
        self, search_service, mock_db, sample_search_results
    ):
        """Test basic message search functionality."""
        # Mock aggregation pipeline results
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_search_results)
        mock_db.messages.aggregate.return_value = mock_cursor

        # Mock count results
        count_cursor = MagicMock()
        count_cursor.to_list = AsyncMock(return_value=[{"total": 2}])
        mock_db.messages.aggregate.side_effect = [mock_cursor, count_cursor]

        # Execute search
        response = await search_service.search_messages(
            query="Python function", filters=None, skip=0, limit=10, highlight=True
        )

        # Verify response structure
        assert isinstance(response, SearchResponse)
        assert response.query == "Python function"
        assert response.total == 2
        assert len(response.results) == 2
        assert response.took_ms >= 0

        # Verify aggregation was called
        assert mock_db.messages.aggregate.called
        assert mock_db.search_logs.insert_one.called

    @pytest.mark.asyncio
    async def test_search_with_filters(
        self, search_service, mock_db, sample_search_results
    ):
        """Test search with filters applied."""
        # Create search filters with valid ObjectId as project ID
        test_project_id = str(ObjectId())
        filters = SearchFilters(
            project_ids=[test_project_id],
            message_types=["user"],
            start_date=datetime.now(UTC),
            has_code=True,
        )

        # Mock aggregation results
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(
            return_value=sample_search_results[:1]
        )  # Only first result
        mock_db.messages.aggregate.return_value = mock_cursor

        count_cursor = MagicMock()
        count_cursor.to_list = AsyncMock(return_value=[{"total": 1}])
        mock_db.messages.aggregate.side_effect = [mock_cursor, count_cursor]

        # Execute filtered search
        response = await search_service.search_messages(
            query="Python", filters=filters, skip=0, limit=10, highlight=True
        )

        # Verify filtered response
        assert response.total == 1
        assert len(response.results) == 1
        assert "project_ids" in response.filters_applied
        assert response.filters_applied["project_ids"] == [test_project_id]

    @pytest.mark.asyncio
    async def test_search_code_functionality(
        self, search_service, mock_db, sample_search_results
    ):
        """Test code-specific search functionality."""
        # Mock aggregation results for code search
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(
            return_value=[sample_search_results[1]]
        )  # Code result
        mock_db.messages.aggregate.return_value = mock_cursor

        count_cursor = MagicMock()
        count_cursor.to_list = AsyncMock(return_value=[{"total": 1}])
        mock_db.messages.aggregate.side_effect = [mock_cursor, count_cursor]

        # Execute code search
        response = await search_service.search_code(
            query="function", filters=None, skip=0, limit=10
        )

        # Verify code search response
        assert response.total == 1
        assert len(response.results) == 1

        # Verify enhanced query was used (search_messages was called)
        assert mock_db.messages.aggregate.called

    @pytest.mark.asyncio
    async def test_search_pagination(
        self, search_service, mock_db, sample_search_results
    ):
        """Test search pagination."""
        # Mock first page
        mock_cursor1 = MagicMock()
        mock_cursor1.to_list = AsyncMock(return_value=[sample_search_results[0]])

        count_cursor1 = MagicMock()
        count_cursor1.to_list = AsyncMock(return_value=[{"total": 2}])

        mock_db.messages.aggregate.side_effect = [mock_cursor1, count_cursor1]

        # First page
        response1 = await search_service.search_messages(
            query="Python", filters=None, skip=0, limit=1, highlight=True
        )

        assert response1.total == 2
        assert len(response1.results) == 1
        assert response1.skip == 0
        assert response1.limit == 1

        # Reset mock for second page
        mock_cursor2 = MagicMock()
        mock_cursor2.to_list = AsyncMock(return_value=[sample_search_results[1]])

        count_cursor2 = MagicMock()
        count_cursor2.to_list = AsyncMock(return_value=[{"total": 2}])

        mock_db.messages.aggregate.side_effect = [mock_cursor2, count_cursor2]

        # Second page
        response2 = await search_service.search_messages(
            query="Python", filters=None, skip=1, limit=1, highlight=True
        )

        assert response2.total == 2
        assert len(response2.results) == 1
        assert response2.skip == 1
        assert response2.limit == 1

    @pytest.mark.asyncio
    async def test_search_empty_results(self, search_service, mock_db):
        """Test search with no results."""
        # Mock empty results
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[])

        count_cursor = MagicMock()
        count_cursor.to_list = AsyncMock(return_value=[])  # No count result

        mock_db.messages.aggregate.side_effect = [mock_cursor, count_cursor]

        # Execute search with no results
        response = await search_service.search_messages(
            query="nonexistent query", filters=None, skip=0, limit=10, highlight=True
        )

        # Verify empty response
        assert response.total == 0
        assert len(response.results) == 0
        assert response.query == "nonexistent query"

    @pytest.mark.asyncio
    async def test_search_error_handling(self, search_service, mock_db):
        """Test search error handling."""
        # Mock database error
        mock_db.messages.aggregate.side_effect = Exception("Database error")

        # Search should handle the error gracefully
        with pytest.raises(Exception, match="Database error"):
            await search_service.search_messages(
                query="test", filters=None, skip=0, limit=10, highlight=True
            )

    @pytest.mark.asyncio
    async def test_search_service_initialization(self, mock_db):
        """Test SearchService initialization."""
        service = SearchService(mock_db)
        assert service.db == mock_db

    @pytest.mark.asyncio
    async def test_search_integration_flow(
        self, search_service, mock_db, sample_search_results
    ):
        """Test complete search integration flow."""
        # Mock successful search flow
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_search_results)

        count_cursor = MagicMock()
        count_cursor.to_list = AsyncMock(return_value=[{"total": 2}])

        mock_db.messages.aggregate.side_effect = [mock_cursor, count_cursor]

        # Execute complete flow
        filters = SearchFilters(message_types=["user", "assistant"])
        response = await search_service.search_messages(
            query="Python programming",
            filters=filters,
            skip=0,
            limit=20,
            highlight=True,
        )

        # Verify complete integration
        assert isinstance(response, SearchResponse)
        assert response.total > 0
        assert len(response.results) > 0
        assert "message_types" in response.filters_applied

        # Verify database operations were called
        assert mock_db.messages.aggregate.called
        assert mock_db.search_logs.insert_one.called
