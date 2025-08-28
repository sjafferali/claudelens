#!/usr/bin/env python3
"""Test project stats calculation."""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_database  # noqa: E402


async def check_data_structure():
    """Check database structure and relationships."""
    db = await get_database()
    print("=" * 50)
    print("CHECKING DATABASE STRUCTURE")
    print("=" * 50)

    # Check a sample session
    session = await db.sessions.find_one()
    if session:
        print("\n1. SAMPLE SESSION:")
        print("   Fields:", list(session.keys()))
        print("   Has projectId:", "projectId" in session)
        if "projectId" in session:
            print("   projectId type:", type(session["projectId"]))
            print("   projectId value:", session["projectId"])
    else:
        print("\n1. No sessions found in database")

    # Check a sample project
    project = await db.projects.find_one()
    if project:
        print("\n2. SAMPLE PROJECT:")
        print("   Fields:", list(project.keys()))
        print("   Project _id:", project["_id"])
        print("   Project user_id:", project.get("user_id"))

        # Count sessions for this project
        if session and "projectId" in session:
            count = await db.sessions.count_documents({"projectId": project["_id"]})
            print(f"\n3. SESSIONS FOR PROJECT {project['_id']}: {count}")

            # Check if session's projectId matches
            if session["projectId"] == project["_id"]:
                print("   ✓ Sample session belongs to sample project")
            else:
                print("   ✗ Sample session does NOT belong to sample project")
                print(f"     Session projectId: {session['projectId']}")
                print(f"     Project _id: {project['_id']}")
    else:
        print("\n2. No projects found in database")

    # Check all projects and their session counts
    print("\n4. ALL PROJECTS AND THEIR SESSION COUNTS:")
    async for proj in db.projects.find().limit(5):
        session_count = await db.sessions.count_documents({"projectId": proj["_id"]})
        message_count = 0

        # Get session IDs for this project
        session_ids = await db.sessions.distinct(
            "sessionId", {"projectId": proj["_id"]}
        )
        if session_ids:
            message_count = await db.messages.count_documents(
                {"sessionId": {"$in": session_ids}}
            )

        print(f"   Project: {proj.get('name', 'unnamed')} (ID: {proj['_id']})")
        print(f"     - Sessions: {session_count}")
        print(f"     - Messages: {message_count}")
        print(f"     - User ID: {proj.get('user_id')}")


if __name__ == "__main__":
    asyncio.run(check_data_structure())
