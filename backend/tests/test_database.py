"""Test database connections and operations."""

import pytest

from app.core.database import close_mongodb_connection, connect_to_mongodb, get_database


@pytest.mark.skip(reason="Temporarily disabled")
@pytest.mark.asyncio()
async def test_mongodb_connection():
    """Test MongoDB connection."""
    await connect_to_mongodb()

    db = await get_database()
    assert db is not None

    # Test ping
    result = await db.client.admin.command("ping")
    assert result["ok"] == 1

    await close_mongodb_connection()


@pytest.mark.skip(reason="Temporarily disabled")
@pytest.mark.asyncio()
async def test_collections_exist():
    """Test that required collections exist."""
    await connect_to_mongodb()
    db = await get_database()

    # Create collections if they don't exist
    existing_collections = await db.list_collection_names()

    required_collections = ["projects", "sessions", "messages", "sync_state"]
    for collection_name in required_collections:
        if collection_name not in existing_collections:
            await db.create_collection(collection_name)

    # Now verify all collections exist
    collections = await db.list_collection_names()

    assert "projects" in collections
    assert "sessions" in collections
    assert "messages" in collections
    assert "sync_state" in collections

    await close_mongodb_connection()
