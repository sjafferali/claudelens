#!/usr/bin/env python3
import asyncio

from motor.motor_asyncio import AsyncIOMotorClient


async def check_orphaned_data():
    # Connect to MongoDB
    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    print("=== Checking for orphaned data ===\n")

    # Get all projects
    projects = await db.projects.find().to_list(None)
    print(f"Total projects: {len(projects)}")
    project_ids = {p["_id"] for p in projects}
    if projects:
        print("Project IDs:", [str(pid) for pid in project_ids])

    # Get all sessions
    sessions = await db.sessions.find().to_list(None)
    print(f"\nTotal sessions: {len(sessions)}")

    # Check for orphaned sessions
    orphaned_sessions = []
    for session in sessions:
        project_id = session.get("projectId")
        if project_id and project_id not in project_ids:
            orphaned_sessions.append(session)
            print(f"  Orphaned session: {session['_id']} (project: {project_id})")

    print(f"\nOrphaned sessions: {len(orphaned_sessions)}")

    # Get all messages
    messages = await db.messages.find().to_list(None)
    print(f"\nTotal messages: {len(messages)}")

    # Get session IDs
    session_ids = {s["_id"] for s in sessions}

    # Check for orphaned messages
    orphaned_messages = []
    for message in messages:
        session_id = message.get("sessionId")
        if session_id and session_id not in session_ids:
            orphaned_messages.append(message)
            print(f"  Orphaned message: {message['_id']} (session: {session_id})")

    print(f"\nOrphaned messages: {len(orphaned_messages)}")

    # Show sample of sessions with their project IDs
    if sessions:
        print("\n=== Sample Sessions ===")
        for session in sessions[:5]:
            print(
                f"Session {session['_id']}: projectId={session.get('projectId', 'None')}"
            )

    # Return orphaned data for cleanup
    return orphaned_sessions, orphaned_messages


if __name__ == "__main__":
    orphaned_sessions, orphaned_messages = asyncio.run(check_orphaned_data())
