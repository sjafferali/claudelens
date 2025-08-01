"""Test database connections and operations."""
import pytest
from app.core.database import connect_to_mongodb, get_database, close_mongodb_connection


@pytest.mark.asyncio
async def test_mongodb_connection():
    """Test MongoDB connection."""
    await connect_to_mongodb()
    
    db = await get_database()
    assert db is not None
    
    # Test ping
    result = await db.client.admin.command("ping")
    assert result["ok"] == 1
    
    await close_mongodb_connection()


@pytest.mark.asyncio
async def test_collections_exist():
    """Test that required collections exist."""
    await connect_to_mongodb()
    db = await get_database()
    
    collections = await db.list_collection_names()
    
    assert "projects" in collections
    assert "sessions" in collections
    assert "messages" in collections
    assert "sync_state" in collections
    
    await close_mongodb_connection()