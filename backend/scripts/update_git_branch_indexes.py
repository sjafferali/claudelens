#!/usr/bin/env python3
"""Script to update MongoDB indexes for git branch analytics optimization."""

import asyncio
import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_indexes():
    """Update indexes for git branch analytics optimization."""
    # Get MongoDB URL from environment or use default
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/claudelens")

    # Connect to MongoDB
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_database()

    logger.info(f"Connected to MongoDB: {mongo_url}")

    # Get messages collection
    messages = db.messages

    # Drop old incorrect index if it exists
    try:
        await messages.drop_index([("createdAt", DESCENDING), ("branch", ASCENDING)])
        logger.info("Dropped old index on ('createdAt', 'branch')")
    except Exception:
        logger.info("Old index on ('createdAt', 'branch') not found")

    # Create new indexes for git branch analytics
    indexes_to_create = [
        (
            [("createdAt", DESCENDING), ("gitBranch", ASCENDING)],
            "createdAt_-1_gitBranch_1",
        ),
        (
            [("timestamp", DESCENDING), ("gitBranch", ASCENDING)],
            "timestamp_-1_gitBranch_1",
        ),
        (
            [("gitBranch", ASCENDING), ("timestamp", DESCENDING)],
            "gitBranch_1_timestamp_-1",
        ),
        (
            [
                ("sessionId", ASCENDING),
                ("timestamp", DESCENDING),
                ("gitBranch", ASCENDING),
            ],
            "sessionId_1_timestamp_-1_gitBranch_1",
        ),
    ]

    for keys, name in indexes_to_create:
        try:
            await messages.create_index(keys, name=name)
            logger.info(f"Created index: {name}")
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"Index {name} already exists")
            else:
                logger.error(f"Failed to create index {name}: {e}")

    # Get index statistics
    indexes = await messages.list_indexes().to_list(None)
    logger.info(f"\nTotal indexes on messages collection: {len(indexes)}")

    # List all indexes related to gitBranch
    git_branch_indexes = [
        idx
        for idx in indexes
        if any("gitBranch" in str(key) for key in idx.get("key", {}).keys())
    ]
    logger.info("\nGit branch related indexes:")
    for idx in git_branch_indexes:
        logger.info(f"  - {idx['name']}: {dict(idx['key'])}")

    # Close connection
    client.close()
    logger.info("\nIndex update completed successfully!")


if __name__ == "__main__":
    asyncio.run(update_indexes())
