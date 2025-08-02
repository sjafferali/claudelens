"""Database initialization and migration utilities."""
import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import errors

logger = logging.getLogger(__name__)


async def initialize_database(db: AsyncIOMotorDatabase) -> None:
    """Initialize database with collections, validators, and indexes."""
    logger.info("Starting database initialization...")

    # Create collections with validators
    await create_collections(db)

    # Create indexes
    await create_indexes(db)

    logger.info("Database initialization completed successfully")


async def create_collections(db: AsyncIOMotorDatabase) -> None:
    """Create collections with JSON schema validators."""
    collections = await db.list_collection_names()

    # Projects collection
    if "projects" not in collections:
        await db.create_collection(
            "projects",
            validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["name", "path", "createdAt"],
                    "properties": {
                        "name": {
                            "bsonType": "string",
                            "description": "Project name extracted from path",
                        },
                        "path": {
                            "bsonType": "string",
                            "description": "Full path to project directory",
                        },
                        "description": {
                            "bsonType": "string",
                            "description": "Optional project description",
                        },
                        "createdAt": {"bsonType": "date"},
                        "updatedAt": {"bsonType": "date"},
                    },
                }
            },
        )
        logger.info("Created 'projects' collection")

    # Sessions collection
    if "sessions" not in collections:
        await db.create_collection(
            "sessions",
            validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["sessionId", "projectId", "startedAt"],
                    "properties": {
                        "sessionId": {
                            "bsonType": "string",
                            "description": "Unique session identifier from Claude",
                        },
                        "projectId": {
                            "bsonType": "objectId",
                            "description": "Reference to project",
                        },
                        "summary": {
                            "bsonType": "string",
                            "description": "AI-generated session summary",
                        },
                        "startedAt": {"bsonType": "date"},
                        "endedAt": {"bsonType": "date"},
                        "messageCount": {"bsonType": "int"},
                        "totalCost": {"bsonType": "decimal"},
                        "metadata": {"bsonType": "object"},
                    },
                }
            },
        )
        logger.info("Created 'sessions' collection")

    # Messages collection - flexible schema
    if "messages" not in collections:
        await db.create_collection("messages")
        logger.info("Created 'messages' collection")

    # Sync state collection
    if "sync_state" not in collections:
        await db.create_collection(
            "sync_state",
            validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["projectPath", "lastSync"],
                    "properties": {
                        "projectPath": {"bsonType": "string"},
                        "lastSync": {"bsonType": "date"},
                        "lastFile": {"bsonType": "string"},
                        "lastLine": {"bsonType": "int"},
                        "syncedHashes": {
                            "bsonType": "array",
                            "items": {"bsonType": "string"},
                        },
                    },
                }
            },
        )
        logger.info("Created 'sync_state' collection")


async def create_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create indexes for all collections."""

    # Projects indexes
    projects = db.projects
    await create_index_if_not_exists(projects, [("path", 1)], unique=True)
    await create_index_if_not_exists(projects, [("name", "text")])

    # Sessions indexes
    sessions = db.sessions
    await create_index_if_not_exists(sessions, [("sessionId", 1)], unique=True)
    await create_index_if_not_exists(sessions, [("projectId", 1)])
    await create_index_if_not_exists(sessions, [("startedAt", -1)])
    await create_index_if_not_exists(sessions, [("summary", "text")])

    # Messages indexes
    messages = db.messages
    await create_index_if_not_exists(messages, [("sessionId", 1), ("timestamp", 1)])
    await create_index_if_not_exists(messages, [("uuid", 1)], unique=True)
    await create_index_if_not_exists(messages, [("parentUuid", 1)])
    await create_index_if_not_exists(
        messages, [("message.content", "text"), ("toolUseResult", "text")]
    )
    await create_index_if_not_exists(messages, [("type", 1)])
    await create_index_if_not_exists(messages, [("timestamp", -1)])
    await create_index_if_not_exists(messages, [("message.model", 1)])
    await create_index_if_not_exists(messages, [("costUsd", 1)])

    # Sync state indexes
    sync_state = db.sync_state
    await create_index_if_not_exists(sync_state, [("projectPath", 1)], unique=True)


async def create_index_if_not_exists(
    collection: Any, keys: list[tuple[str, Any]], unique: bool = False
) -> None:
    """Create an index if it doesn't already exist."""
    try:
        index_name = await collection.create_index(keys, unique=unique)
        logger.debug(f"Created index {index_name} on {collection.name}")
    except errors.OperationFailure as e:
        if "already exists" in str(e):
            logger.debug(f"Index already exists on {collection.name}")
        else:
            raise
