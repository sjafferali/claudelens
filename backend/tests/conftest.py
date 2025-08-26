"""Test configuration and fixtures."""

import asyncio
import os
from typing import AsyncGenerator

import pytest
from motor.motor_asyncio import AsyncIOMotorClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator:
    """Create a test database connection."""
    # Use a test database
    mongo_url = os.getenv("MONGODB_TEST_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client["claudelens_test"]

    # Try to clear collections, skip if authentication required
    try:
        for collection_name in await db.list_collection_names():
            await db[collection_name].delete_many({})
    except Exception:
        # Skip if authentication required or database doesn't exist
        pass

    yield db

    # Cleanup after tests (best effort)
    try:
        for collection_name in await db.list_collection_names():
            await db[collection_name].delete_many({})
    except Exception:
        pass

    client.close()
