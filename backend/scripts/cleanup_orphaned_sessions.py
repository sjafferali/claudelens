"""Clean up orphaned sessions without projects."""

import asyncio
import logging

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_orphaned_sessions(
    mongodb_url: str, database_name: str, dry_run: bool = True
):
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]

    # Find orphaned sessions
    orphaned_sessions = []
    sessions = await db.sessions.find(
        {}, {"_id": 1, "sessionId": 1, "projectId": 1}
    ).to_list(None)

    for session in sessions:
        project_id = session.get("projectId")
        if project_id:
            project = await db.projects.find_one({"_id": project_id})
            if not project:
                orphaned_sessions.append(session)
        else:
            # No project ID at all
            orphaned_sessions.append(session)

    logger.info(f"Found {len(orphaned_sessions)} orphaned sessions")

    if orphaned_sessions:
        # Try to create missing projects if we can determine ownership
        admin_user = await db.users.find_one({"role": "admin"})
        if not admin_user:
            admin_user = await db.users.find_one({})

        if admin_user:
            if dry_run:
                logger.info(
                    f"DRY RUN: Would create projects for {len(orphaned_sessions)} orphaned sessions"
                )
                for session in orphaned_sessions[:5]:  # Show first 5
                    logger.info(
                        f"  Session: {session['sessionId']} (ID: {session['_id']})"
                    )
            else:
                for session in orphaned_sessions:
                    # Create a project for this orphaned session
                    project_doc = {
                        "_id": ObjectId(),
                        "user_id": admin_user["_id"],
                        "name": f"Recovered Project for {session['sessionId']}",
                        "path": f"/recovered/{session['sessionId']}",
                        "createdAt": session.get(
                            "createdAt", session["_id"].generation_time
                        ),
                        "updatedAt": session.get(
                            "updatedAt", session["_id"].generation_time
                        ),
                        "stats": {"message_count": 0, "session_count": 1},
                    }

                    await db.projects.insert_one(project_doc)

                    # Update session to point to new project
                    await db.sessions.update_one(
                        {"_id": session["_id"]},
                        {"$set": {"projectId": project_doc["_id"]}},
                    )

                    logger.info(
                        f"Created project for orphaned session {session['sessionId']}"
                    )
        else:
            logger.error("No users found to assign orphaned sessions to")
    else:
        logger.info("No orphaned sessions found")


async def main():
    mongodb_url = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    database_name = "claudelens"
    dry_run = False  # Set to False to actually create projects

    await cleanup_orphaned_sessions(mongodb_url, database_name, dry_run)


if __name__ == "__main__":
    asyncio.run(main())
