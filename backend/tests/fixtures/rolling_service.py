"""Shared fixtures for rolling message service mocking."""
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_rolling_service():
    """Create a mock rolling service with common methods."""
    service = MagicMock()
    service.insert_message = AsyncMock()
    service.find_messages = AsyncMock(return_value=([], 0))
    service.find_one = AsyncMock(return_value=None)
    service.update_one = AsyncMock(return_value=True)
    service.aggregate_across_collections = AsyncMock(return_value=[])
    service.count_documents = AsyncMock(return_value=0)
    service.get_collection_for_date = MagicMock()
    service.get_collections_in_range = MagicMock(return_value=["messages_2024_01"])
    service.get_storage_metrics = AsyncMock(return_value={})
    return service
