"""Migrate existing viewer users to user role."""

import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_viewer_users(mongodb_url: str, database_name: str):
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]

    # Count viewers
    viewer_count = await db.users.count_documents({"role": "viewer"})
    logger.info(f"Found {viewer_count} users with VIEWER role")

    if viewer_count == 0:
        logger.info("No VIEWER users found, migration not needed")
        return

    # Update all viewers to users
    result = await db.users.update_many({"role": "viewer"}, {"$set": {"role": "user"}})

    logger.info(f"Updated {result.modified_count} users from VIEWER to USER role")

    # Update OIDC settings if default role is viewer
    oidc_settings = await db.oidc_settings.find_one({})
    if oidc_settings and oidc_settings.get("default_role") == "viewer":
        await db.oidc_settings.update_one(
            {"_id": oidc_settings["_id"]}, {"$set": {"default_role": "user"}}
        )
        logger.info("Updated OIDC default role from VIEWER to USER")


if __name__ == "__main__":
    mongodb_url = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    asyncio.run(migrate_viewer_users(mongodb_url, "claudelens"))
