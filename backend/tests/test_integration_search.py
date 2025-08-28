"""Integration tests for search functionality."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

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
    with patch("app.services.search.RollingMessageService"):
        service = SearchService(mock_db)
        # Mock the rolling service methods
        service.rolling_service.get_collections_for_range = AsyncMock(
            return_value=["messages_2025_01"]
        )
        return service


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
        # Mock collection
        mock_collection = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_search_results)

        # Mock count results
        count_cursor = AsyncMock()
        count_cursor.to_list = AsyncMock(return_value=[{"total": 2}])

        # Set up aggregation to return different results for search and count
        mock_collection.aggregate = MagicMock(side_effect=[mock_cursor, count_cursor])

        # Mock database collection access
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Mock rolling service
        search_service.rolling_service.get_collections_for_range = AsyncMock(
            return_value=["messages_2025_01"]
        )

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
        assert mock_collection.aggregate.called
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

        # Mock collection
        mock_collection = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(
            return_value=sample_search_results[:1]
        )  # Only first result

        count_cursor = AsyncMock()
        count_cursor.to_list = AsyncMock(return_value=[{"total": 1}])

        mock_collection.aggregate = MagicMock(side_effect=[mock_cursor, count_cursor])
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Mock rolling service
        search_service.rolling_service.get_collections_for_range = AsyncMock(
            return_value=["messages_2025_01"]
        )

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
        # Mock collection
        mock_collection = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(
            return_value=[sample_search_results[1]]
        )  # Code result

        count_cursor = AsyncMock()
        count_cursor.to_list = AsyncMock(return_value=[{"total": 1}])

        mock_collection.aggregate = MagicMock(side_effect=[mock_cursor, count_cursor])
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Mock rolling service
        search_service.rolling_service.get_collections_for_range = AsyncMock(
            return_value=["messages_2025_01"]
        )

        # Execute code search
        response = await search_service.search_code(
            query="function", filters=None, skip=0, limit=10
        )

        # Verify code search response
        assert response.total == 1
        assert len(response.results) == 1

        # Verify aggregation was called
        assert mock_collection.aggregate.called

    @pytest.mark.asyncio
    async def test_search_pagination(
        self, search_service, mock_db, sample_search_results
    ):
        """Test search pagination."""
        # Mock collection that returns both results
        mock_collection = MagicMock()

        # For the first request (skip=0, limit=1), return both results
        # The service will paginate them internally
        mock_cursor1 = AsyncMock()
        mock_cursor1.to_list = AsyncMock(
            return_value=sample_search_results
        )  # Return all results

        count_cursor1 = AsyncMock()
        count_cursor1.to_list = AsyncMock(return_value=[{"total": 2}])

        mock_collection.aggregate = MagicMock(side_effect=[mock_cursor1, count_cursor1])
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Mock rolling service
        search_service.rolling_service.get_collections_for_range = AsyncMock(
            return_value=["messages_2025_01"]
        )

        # First page
        response1 = await search_service.search_messages(
            query="Python", filters=None, skip=0, limit=1, highlight=True
        )

        assert response1.total == 2
        assert len(response1.results) == 1
        assert response1.skip == 0
        assert response1.limit == 1

        # For second page request, mock returns all results again
        # Service will apply skip=1 internally
        mock_cursor2 = AsyncMock()
        mock_cursor2.to_list = AsyncMock(
            return_value=sample_search_results
        )  # Return all results

        count_cursor2 = AsyncMock()
        count_cursor2.to_list = AsyncMock(return_value=[{"total": 2}])

        mock_collection.aggregate = MagicMock(side_effect=[mock_cursor2, count_cursor2])

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
        # Mock collection with empty results
        mock_collection = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])

        count_cursor = AsyncMock()
        count_cursor.to_list = AsyncMock(return_value=[])  # No count result

        mock_collection.aggregate = MagicMock(side_effect=[mock_cursor, count_cursor])
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Mock rolling service
        search_service.rolling_service.get_collections_for_range = AsyncMock(
            return_value=["messages_2025_01"]
        )

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
        # Mock collection that raises error
        mock_collection = MagicMock()
        mock_collection.aggregate.side_effect = Exception("Database error")
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Mock rolling service
        search_service.rolling_service.get_collections_for_range = AsyncMock(
            return_value=["messages_2025_01"]
        )

        # Search should handle the error gracefully
        with pytest.raises(Exception, match="Database error"):
            await search_service.search_messages(
                query="test", filters=None, skip=0, limit=10, highlight=True
            )

    @pytest.mark.asyncio
    async def test_search_service_initialization(self, mock_db):
        """Test SearchService initialization."""
        with patch("app.services.search.RollingMessageService"):
            service = SearchService(mock_db)
            assert service.db == mock_db

    @pytest.mark.asyncio
    async def test_search_integration_flow(
        self, search_service, mock_db, sample_search_results
    ):
        """Test complete search integration flow."""
        # Mock collection for search flow
        mock_collection = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_search_results)

        count_cursor = AsyncMock()
        count_cursor.to_list = AsyncMock(return_value=[{"total": 2}])

        mock_collection.aggregate = MagicMock(side_effect=[mock_cursor, count_cursor])
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Mock rolling service
        search_service.rolling_service.get_collections_for_range = AsyncMock(
            return_value=["messages_2025_01"]
        )

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
        assert mock_collection.aggregate.called
        assert mock_db.search_logs.insert_one.called
