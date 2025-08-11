#!/usr/bin/env python3
"""Test cascade deletion functionality."""

import asyncio
import sys
from datetime import UTC, datetime
from uuid import uuid4

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient


async def test_cascade_deletion():
    """Test that project deletion cascades properly."""
    # Connect to MongoDB
    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    print("=== Testing Cascade Deletion ===\n")

    # 1. Create a test project
    test_project_id = ObjectId()
    test_project = {
        "_id": test_project_id,
        "name": "Test Project for Cascade",
        "path": f"/test/cascade/{uuid4()}",
        "description": "Testing cascade deletion",
        "createdAt": datetime.now(UTC),
        "updatedAt": datetime.now(UTC),
    }

    await db.projects.insert_one(test_project)
    print(f"✓ Created test project: {test_project_id}")

    # 2. Create test sessions
    session_ids = []
    for i in range(3):
        session_id = str(uuid4())
        session_ids.append(session_id)
        session = {
            "_id": ObjectId(),
            "sessionId": session_id,
            "projectId": test_project_id,
            "startedAt": datetime.now(UTC),
            "endedAt": datetime.now(UTC),
            "title": f"Test Session {i+1}",
        }
        await db.sessions.insert_one(session)

    print(f"✓ Created {len(session_ids)} test sessions")

    # 3. Create test messages
    message_count = 0
    for session_id in session_ids:
        for j in range(5):  # 5 messages per session
            message = {
                "_id": ObjectId(),
                "uuid": str(uuid4()),
                "sessionId": session_id,
                "type": "user" if j % 2 == 0 else "assistant",
                "timestamp": datetime.now(UTC),
                "content": f"Test message {j+1} in session {session_id[:8]}",
            }
            await db.messages.insert_one(message)
            message_count += 1

    print(f"✓ Created {message_count} test messages")

    # 4. Verify data exists
    project_count = await db.projects.count_documents({"_id": test_project_id})
    session_count = await db.sessions.count_documents({"projectId": test_project_id})
    message_count = await db.messages.count_documents(
        {"sessionId": {"$in": session_ids}}
    )

    print("\nBefore deletion:")
    print(f"  Projects: {project_count}")
    print(f"  Sessions: {session_count}")
    print(f"  Messages: {message_count}")

    if project_count != 1 or session_count != 3 or message_count != 15:
        print("❌ Initial data creation failed!")
        return False

    # 5. Delete the project using the service
    import sys

    sys.path.insert(0, ".")
    from app.services.project import ProjectService

    service = ProjectService(db)
    deleted = await service.delete_project(test_project_id, cascade=True)

    if not deleted:
        print("❌ Project deletion failed!")
        return False

    print("\n✓ Project deleted successfully")

    # 6. Verify cascade deletion
    project_count = await db.projects.count_documents({"_id": test_project_id})
    session_count = await db.sessions.count_documents({"projectId": test_project_id})
    message_count = await db.messages.count_documents(
        {"sessionId": {"$in": session_ids}}
    )

    print("\nAfter deletion:")
    print(f"  Projects: {project_count}")
    print(f"  Sessions: {session_count}")
    print(f"  Messages: {message_count}")

    if project_count == 0 and session_count == 0 and message_count == 0:
        print("\n✅ CASCADE DELETION WORKS CORRECTLY!")
        return True
    else:
        print("\n❌ CASCADE DELETION FAILED!")
        print("Some data was not deleted properly.")
        return False


async def main():
    """Run the test."""
    try:
        success = await test_cascade_deletion()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
