#!/usr/bin/env python3
"""Script to investigate the data structure in the database."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Connection details
MONGODB_URL = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
DATABASE_NAME = "claudelens"


async def investigate_structure():
    """Investigate the actual structure of the data."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    try:
        print("=" * 60)
        print("INVESTIGATING DATA STRUCTURE")
        print("=" * 60)

        # Check projects structure
        print("\n1. PROJECTS COLLECTION:")
        projects = await db.projects.find({}).limit(2).to_list(2)
        if projects:
            print(f"Found {len(projects)} project(s)")
            for p in projects:
                print(f"  Project: {p}")
                print(f"    _id type: {type(p.get('_id'))}")
                print(f"    Fields: {list(p.keys())}")
        else:
            print("  No projects found")

        # Check sessions structure
        print("\n2. SESSIONS COLLECTION:")
        sessions = await db.sessions.find({}).limit(2).to_list(2)
        if sessions:
            print(f"Found {len(sessions)} session(s)")
            for s in sessions:
                print(f"  Session sample:")
                print(f"    _id: {s.get('_id')} (type: {type(s.get('_id'))})")
                print(f"    sessionId: {s.get('sessionId')} (type: {type(s.get('sessionId'))})")
                print(f"    projectId: {s.get('projectId')} (type: {type(s.get('projectId'))})")
                print(f"    project_id: {s.get('project_id')} (type: {type(s.get('project_id'))})")
                print(f"    Fields: {list(s.keys())}")
        else:
            print("  No sessions found")

        # Check messages structure
        print("\n3. MESSAGES COLLECTION:")
        messages = await db.messages.find({}).limit(2).to_list(2)
        if messages:
            print(f"Found {len(messages)} message(s)")
            for m in messages:
                print(f"  Message sample:")
                print(f"    _id: {m.get('_id')} (type: {type(m.get('_id'))})")
                print(f"    sessionId: {m.get('sessionId')} (type: {type(m.get('sessionId'))})")
                print(f"    session_id: {m.get('session_id')} (type: {type(m.get('session_id'))})")
                print(f"    Fields: {list(m.keys())}")
        else:
            print("  No messages found")

        # Check for field name variations
        print("\n4. CHECKING FIELD NAME VARIATIONS:")

        # Check sessions for different project field names
        session_with_projectId = await db.sessions.count_documents({"projectId": {"$exists": True}})
        session_with_project_id = await db.sessions.count_documents({"project_id": {"$exists": True}})
        print(f"  Sessions with 'projectId' field: {session_with_projectId}")
        print(f"  Sessions with 'project_id' field: {session_with_project_id}")

        # Check messages for different session field names
        messages_with_sessionId = await db.messages.count_documents({"sessionId": {"$exists": True}})
        messages_with_session_id = await db.messages.count_documents({"session_id": {"$exists": True}})
        print(f"  Messages with 'sessionId' field: {messages_with_sessionId}")
        print(f"  Messages with 'session_id' field: {messages_with_session_id}")

        # Check for null or missing values
        print("\n5. CHECKING FOR NULL/MISSING VALUES:")
        sessions_without_projectId = await db.sessions.count_documents({
            "$or": [
                {"projectId": {"$exists": False}},
                {"projectId": None},
                {"projectId": ""}
            ]
        })
        messages_without_sessionId = await db.messages.count_documents({
            "$or": [
                {"sessionId": {"$exists": False}},
                {"sessionId": None},
                {"sessionId": ""}
            ]
        })
        print(f"  Sessions without valid projectId: {sessions_without_projectId}")
        print(f"  Messages without valid sessionId: {messages_without_sessionId}")

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(investigate_structure())
