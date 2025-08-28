"""Verify that all data has proper user ownership."""

import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_ownership(mongodb_url: str, database_name: str):
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]

    issues = []

    # Check projects
    orphaned = await db.projects.count_documents({"user_id": {"$exists": False}})
    if orphaned > 0:
        issues.append(f"Found {orphaned} projects without user_id")

    null_user = await db.projects.count_documents({"user_id": None})
    if null_user > 0:
        issues.append(f"Found {null_user} projects with null user_id")

    # Check sessions
    orphaned = await db.sessions.count_documents({"user_id": {"$exists": False}})
    if orphaned > 0:
        issues.append(f"Found {orphaned} sessions without user_id")

    null_user = await db.sessions.count_documents({"user_id": None})
    if null_user > 0:
        issues.append(f"Found {null_user} sessions with null user_id")

    # Check messages
    orphaned = await db.messages.count_documents({"user_id": {"$exists": False}})
    if orphaned > 0:
        issues.append(f"Found {orphaned} messages without user_id")

    null_user = await db.messages.count_documents({"user_id": None})
    if null_user > 0:
        issues.append(f"Found {null_user} messages with null user_id")

    # Check data isolation
    users = await db.users.find({}).to_list(None)
    for user in users:
        user_id = user["_id"]

        # Count user's data
        projects = await db.projects.count_documents({"user_id": user_id})
        sessions = await db.sessions.count_documents({"user_id": user_id})
        messages = await db.messages.count_documents({"user_id": user_id})

        logger.info(
            f"User {user['username']}: {projects} projects, {sessions} sessions, {messages} messages"
        )

    if issues:
        logger.error("VERIFICATION FAILED:")
        for issue in issues:
            logger.error(f"  - {issue}")
        return False
    else:
        logger.info("✅ All data has proper user ownership")
        return True


if __name__ == "__main__":
    # Use remote MongoDB connection
    mongodb_url = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    asyncio.run(verify_ownership(mongodb_url, "claudelens"))
