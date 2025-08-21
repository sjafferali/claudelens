#!/usr/bin/env python3
"""Script to check and clean orphaned sessions and messages."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any

# Connection details
MONGODB_URL = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
DATABASE_NAME = "claudelens"


async def check_orphaned_data():
    """Check for orphaned sessions and messages."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    try:
        # Get all projects
        projects_collection = db["projects"]
        sessions_collection = db["sessions"]
        messages_collection = db["messages"]

        # Get all project IDs
        projects = await projects_collection.find({}).to_list(None)
        project_ids = [str(p.get("_id", "")) for p in projects]

        print(f"Found {len(projects)} projects")
        if projects:
            print(f"Project IDs: {project_ids}")

        # Find all sessions
        all_sessions = await sessions_collection.find({}).to_list(None)
        print(f"\nFound {len(all_sessions)} total sessions")

        # If there are no projects, ALL sessions are orphaned
        if len(projects) == 0 and len(all_sessions) > 0:
            orphaned_sessions = all_sessions
            print(f"No projects exist - ALL {len(orphaned_sessions)} sessions are orphaned!")
        else:
            # Find orphaned sessions (sessions without a valid project)
            orphaned_sessions = []
            for session in all_sessions:
                project_id = session.get("project_id", "")
                # Session is orphaned if it has no project_id or project_id not in valid projects
                if not project_id or str(project_id) not in project_ids:
                    orphaned_sessions.append(session)

            print(f"Found {len(orphaned_sessions)} orphaned sessions")

        if orphaned_sessions:
            print("\nOrphaned sessions:")
            for session in orphaned_sessions[:5]:  # Show first 5
                print(f"  - Session ID: {session.get('_id')}, Project ID: {session.get('project_id', 'None')}, Title: {session.get('title', 'N/A')}")
            if len(orphaned_sessions) > 5:
                print(f"  ... and {len(orphaned_sessions) - 5} more")

        # Get session IDs
        all_session_ids = [str(s.get("_id", "")) for s in all_sessions]
        orphaned_session_ids = [str(s.get("_id", "")) for s in orphaned_sessions]

        # Find all messages
        all_messages = await messages_collection.find({}).to_list(None)
        print(f"\nFound {len(all_messages)} total messages")

        # If there are no sessions, ALL messages are orphaned
        if len(all_sessions) == 0 and len(all_messages) > 0:
            orphaned_messages = all_messages
            print(f"No sessions exist - ALL {len(orphaned_messages)} messages are orphaned!")
        else:
            # Find orphaned messages (messages without a valid session)
            orphaned_messages = []
            for message in all_messages:
                session_id = message.get("session_id", "")
                # Message is orphaned if it has no session_id or session_id not in valid sessions
                if not session_id or str(session_id) not in all_session_ids:
                    orphaned_messages.append(message)

            print(f"Found {len(orphaned_messages)} orphaned messages")

        if orphaned_messages:
            print("\nOrphaned messages (showing first 5):")
            for message in orphaned_messages[:5]:  # Show first 5
                print(f"  - Message ID: {message.get('_id')}, Session ID: {message.get('session_id', 'None')}, Type: {message.get('type', 'N/A')}")
            if len(orphaned_messages) > 5:
                print(f"  ... and {len(orphaned_messages) - 5} more")

        # Find messages that belong to orphaned sessions
        messages_in_orphaned_sessions = []
        if orphaned_session_ids:
            for message in all_messages:
                session_id = str(message.get("session_id", ""))
                if session_id in orphaned_session_ids:
                    messages_in_orphaned_sessions.append(message)

            print(f"\nFound {len(messages_in_orphaned_sessions)} messages in orphaned sessions")

        return {
            "projects": len(projects),
            "sessions": len(all_sessions),
            "orphaned_sessions": orphaned_sessions,
            "messages": len(all_messages),
            "orphaned_messages": orphaned_messages,
            "messages_in_orphaned_sessions": messages_in_orphaned_sessions
        }

    finally:
        client.close()


async def delete_orphaned_data():
    """Delete orphaned sessions and messages."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    try:
        # Get all projects
        projects_collection = db["projects"]
        sessions_collection = db["sessions"]
        messages_collection = db["messages"]

        # Get all project IDs
        projects = await projects_collection.find({}).to_list(None)
        project_ids = [str(p.get("_id", "")) for p in projects]

        print(f"Found {len(projects)} projects")

        # If there are no projects, delete ALL sessions and messages
        if len(projects) == 0:
            print("No projects exist - deleting ALL sessions and messages")

            # Delete all messages
            messages_result = await messages_collection.delete_many({})
            print(f"Deleted {messages_result.deleted_count} messages")

            # Delete all sessions
            sessions_result = await sessions_collection.delete_many({})
            print(f"Deleted {sessions_result.deleted_count} sessions")
        else:
            # Find orphaned sessions
            all_sessions = await sessions_collection.find({}).to_list(None)
            orphaned_session_ids = []

            for session in all_sessions:
                project_id = session.get("project_id", "")
                # Session is orphaned if it has no project_id or project_id not in valid projects
                if not project_id or str(project_id) not in project_ids:
                    orphaned_session_ids.append(session.get("_id"))

            print(f"Found {len(orphaned_session_ids)} orphaned sessions to delete")

            # Delete orphaned sessions and their messages
            if orphaned_session_ids:
                # First delete messages belonging to orphaned sessions
                messages_result = await messages_collection.delete_many({
                    "session_id": {"$in": orphaned_session_ids}
                })
                print(f"Deleted {messages_result.deleted_count} messages from orphaned sessions")

                # Then delete the orphaned sessions
                sessions_result = await sessions_collection.delete_many({
                    "_id": {"$in": orphaned_session_ids}
                })
                print(f"Deleted {sessions_result.deleted_count} orphaned sessions")

            # Also delete any messages without valid sessions
            all_sessions_after = await sessions_collection.find({}).to_list(None)
            valid_session_ids = [str(s.get("_id", "")) for s in all_sessions_after]

            # Find and delete orphaned messages
            all_messages = await messages_collection.find({}).to_list(None)
            orphaned_message_ids = []

            for message in all_messages:
                session_id = message.get("session_id", "")
                # Message is orphaned if it has no session_id or session_id not in valid sessions
                if not session_id or str(session_id) not in valid_session_ids:
                    orphaned_message_ids.append(message.get("_id"))

            if orphaned_message_ids:
                result = await messages_collection.delete_many({
                    "_id": {"$in": orphaned_message_ids}
                })
                print(f"Deleted {result.deleted_count} additional orphaned messages")

        print("\nCleanup complete!")

    finally:
        client.close()


if __name__ == "__main__":
    print("Checking for orphaned data...")
    print("=" * 50)

    data = asyncio.run(check_orphaned_data())

    if data["orphaned_sessions"] or data["orphaned_messages"] or data["messages_in_orphaned_sessions"]:
        print("\n" + "=" * 50)
        print("Cleaning up orphaned data...")
        print("=" * 50)
        asyncio.run(delete_orphaned_data())

        print("\n" + "=" * 50)
        print("Verification after cleanup:")
        print("=" * 50)
        asyncio.run(check_orphaned_data())
    else:
        print("\nNo orphaned data found!")
