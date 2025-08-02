"""MongoDB database connection and utilities."""
from typing import Optional
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import errors
import logging
from app.core.config import settings
from app.core.testcontainers_db import get_testcontainer_mongodb_url

logger = logging.getLogger(__name__)


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None


db = MongoDB()


async def connect_to_mongodb() -> None:
    """Create database connection."""
    try:
        # Check if we should use testcontainers
        testcontainer_url = get_testcontainer_mongodb_url()
        mongodb_url = testcontainer_url or settings.MONGODB_URL
        
        db.client = AsyncIOMotorClient(
            mongodb_url,
            maxPoolSize=settings.MAX_CONNECTIONS_COUNT,
            minPoolSize=settings.MIN_CONNECTIONS_COUNT,
        )
        db.database = db.client[settings.DATABASE_NAME]
        
        # Verify connection
        await db.client.admin.command("ping")
        logger.info(f"Successfully connected to MongoDB at {mongodb_url}")
        
    except errors.ConnectionFailure as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise


async def close_mongodb_connection() -> None:
    """Close database connection."""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")
    
    # Testcontainer cleanup is handled by atexit in testcontainers_db.py


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    if db.database is None:
        await connect_to_mongodb()
    return db.database


# Collection accessors
async def get_projects_collection():
    """Get projects collection."""
    database = await get_database()
    return database.projects


async def get_sessions_collection():
    """Get sessions collection."""
    database = await get_database()
    return database.sessions


async def get_messages_collection():
    """Get messages collection."""
    database = await get_database()
    return database.messages


async def get_sync_state_collection():
    """Get sync state collection."""
    database = await get_database()
    return database.sync_state