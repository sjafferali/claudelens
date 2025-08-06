#!/usr/bin/env python3
"""Script to update text index for search functionality."""

import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_text_index():
    """Drop and recreate text index with all content fields."""
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        # Drop existing text indexes
        logger.info("Dropping existing text indexes...")
        indexes = await db.messages.list_indexes().to_list(None)
        for index in indexes:
            if index.get("textIndexVersion"):
                await db.messages.drop_index(index["name"])
                logger.info(f"Dropped text index: {index['name']}")

        # Create new comprehensive text index
        logger.info("Creating new text index...")
        await db.messages.create_index(
            [
                ("message.content", "text"),
                ("content", "text"),
                ("toolUseResult", "text"),
            ]
        )
        logger.info("Text index created successfully")

        # Verify index creation
        indexes = await db.messages.list_indexes().to_list(None)
        text_indexes = [idx for idx in indexes if idx.get("textIndexVersion")]
        logger.info(f"Text indexes: {text_indexes}")

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(update_text_index())
