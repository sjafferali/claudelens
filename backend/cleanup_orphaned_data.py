#!/usr/bin/env python3
import asyncio

from motor.motor_asyncio import AsyncIOMotorClient


async def cleanup_orphaned_data():
    # Connect to MongoDB
    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    print("=== Cleaning up orphaned data ===\n")

    # Get all projects
    projects = await db.projects.find().to_list(None)
    print(f"Total projects: {len(projects)}")
    project_ids = {p["_id"] for p in projects}

    # Get all sessions
    sessions = await db.sessions.find().to_list(None)
    print(f"Total sessions: {len(sessions)}")
    session_ids = {s["_id"] for s in sessions}

    # Clean up orphaned messages (no corresponding session)
    orphaned_messages_filter = (
        {"sessionId": {"$nin": list(session_ids)}} if session_ids else {}
    )

    # Count messages to delete
    orphaned_messages_count = await db.messages.count_documents(
        orphaned_messages_filter
    )
    print(f"\nOrphaned messages to delete: {orphaned_messages_count}")

    if orphaned_messages_count > 0:
        # Delete orphaned messages
        result = await db.messages.delete_many(orphaned_messages_filter)
        print(f"Deleted {result.deleted_count} orphaned messages")

    # Clean up orphaned sessions (no corresponding project)
    if not project_ids:
        # No projects, delete all sessions
        sessions_count = await db.sessions.count_documents({})
        if sessions_count > 0:
            result = await db.sessions.delete_many({})
            print(
                f"Deleted {result.deleted_count} orphaned sessions (no projects exist)"
            )
    else:
        # Delete sessions with non-existent project IDs
        orphaned_sessions_filter = {"projectId": {"$nin": list(project_ids)}}
        orphaned_sessions_count = await db.sessions.count_documents(
            orphaned_sessions_filter
        )
        print(f"\nOrphaned sessions to delete: {orphaned_sessions_count}")

        if orphaned_sessions_count > 0:
            result = await db.sessions.delete_many(orphaned_sessions_filter)
            print(f"Deleted {result.deleted_count} orphaned sessions")

    print("\n=== Cleanup complete ===")

    # Verify final state
    final_projects = await db.projects.count_documents({})
    final_sessions = await db.sessions.count_documents({})
    final_messages = await db.messages.count_documents({})

    print("\nFinal counts:")
    print(f"  Projects: {final_projects}")
    print(f"  Sessions: {final_sessions}")
    print(f"  Messages: {final_messages}")


if __name__ == "__main__":
    asyncio.run(cleanup_orphaned_data())
