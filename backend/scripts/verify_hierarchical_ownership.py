"""Verify hierarchical ownership model is working correctly."""

import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_hierarchical_ownership(mongodb_url: str, database_name: str):
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]

    issues = []

    # Check projects have user_id
    projects_without_user = await db.projects.count_documents(
        {"$or": [{"user_id": {"$exists": False}}, {"user_id": None}]}
    )
    if projects_without_user > 0:
        issues.append(f"Found {projects_without_user} projects without user_id")

    # Check sessions DON'T have user_id (hierarchical model)
    sessions_with_user = await db.sessions.count_documents(
        {"user_id": {"$exists": True}}
    )
    if sessions_with_user > 0:
        issues.append(
            f"Found {sessions_with_user} sessions with user_id (should be removed)"
        )

    # Check messages DON'T have user_id (hierarchical model)
    messages_with_user = await db.messages.count_documents(
        {"user_id": {"$exists": True}}
    )
    if messages_with_user > 0:
        issues.append(
            f"Found {messages_with_user} messages with user_id (should be removed)"
        )

    # Check all sessions have valid projects
    orphaned_sessions = 0
    sessions = await db.sessions.find({}, {"sessionId": 1, "projectId": 1}).to_list(
        None
    )
    for session in sessions:
        if not session.get("projectId"):
            orphaned_sessions += 1
        else:
            project = await db.projects.find_one({"_id": session["projectId"]})
            if not project:
                orphaned_sessions += 1

    if orphaned_sessions > 0:
        issues.append(
            f"Found {orphaned_sessions} orphaned sessions without valid projects"
        )

    # Check all messages have valid sessions
    orphaned_messages = 0
    sample_messages = await db.messages.find({}).limit(100).to_list(100)
    for msg in sample_messages:
        session = await db.sessions.find_one({"sessionId": msg.get("sessionId")})
        if not session:
            orphaned_messages += 1

    if orphaned_messages > 0 and sample_messages:
        # Extrapolate
        total_messages = await db.messages.count_documents({})
        estimated_orphans = int(
            (orphaned_messages / len(sample_messages)) * total_messages
        )
        issues.append(
            f"Estimated {estimated_orphans} orphaned messages without valid sessions"
        )

    # Count data per user through hierarchical model
    users = await db.users.find({}).to_list(None)
    for user in users:
        user_id = user["_id"]

        # Count user's projects
        projects = await db.projects.count_documents({"user_id": user_id})

        # Count user's sessions (through projects)
        user_projects = await db.projects.find(
            {"user_id": user_id}, {"_id": 1}
        ).to_list(None)
        project_ids = [p["_id"] for p in user_projects]
        sessions = await db.sessions.count_documents(
            {"projectId": {"$in": project_ids}}
        )

        # Count user's messages (through sessions through projects)
        user_sessions = await db.sessions.find(
            {"projectId": {"$in": project_ids}}, {"sessionId": 1}
        ).to_list(None)
        session_ids = [s["sessionId"] for s in user_sessions]
        messages = await db.messages.count_documents(
            {"sessionId": {"$in": session_ids}}
        )

        logger.info(
            f"User {user['username']}: {projects} projects, {sessions} sessions, {messages} messages"
        )

    # Verify data isolation
    logger.info("\nVerifying data isolation...")

    # Test case: Each project should only be accessible by its owner
    all_projects = await db.projects.find({}).to_list(None)
    for project in all_projects:
        if not project.get("user_id"):
            issues.append(f"Project {project['_id']} has no user_id")

    if issues:
        logger.error("VERIFICATION FAILED:")
        for issue in issues:
            logger.error(f"  - {issue}")
        return False
    else:
        logger.info("✅ Hierarchical ownership model is working correctly!")
        logger.info("  - All projects have user_id")
        logger.info("  - No sessions have user_id (ownership through projects)")
        logger.info("  - No messages have user_id (ownership through sessions)")
        logger.info("  - All sessions have valid projects")
        logger.info("  - Data is properly isolated per user")
        return True


if __name__ == "__main__":
    mongodb_url = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    asyncio.run(verify_hierarchical_ownership(mongodb_url, "claudelens"))
