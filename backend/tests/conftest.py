"""Test configuration and fixtures."""

import asyncio
import os
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
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
    # Try to use testcontainers if available, otherwise use local MongoDB
    try:
        from app.core.testcontainers_db import get_test_database

        db = await get_test_database()
        yield db
    except ImportError:
        # Fallback to local MongoDB if testcontainers not available
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


@pytest.fixture
async def client(test_db) -> AsyncGenerator:
    """Create an async test client for the FastAPI app."""
    from app.core.database import get_database
    from app.main import app

    # Override the database dependency
    async def override_get_database():
        return test_db

    app.dependency_overrides[get_database] = override_get_database

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clear dependency overrides after test
    app.dependency_overrides.clear()
