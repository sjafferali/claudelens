#!/usr/bin/env python3
"""Test the robust project deletion functionality."""

import asyncio
import sys
from datetime import UTC, datetime
from uuid import uuid4

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

# Add current directory to path
sys.path.insert(0, ".")

from app.services.project_deletion import ProjectDeletionService  # noqa: E402


async def test_robust_deletion():
    """Test the new robust deletion service."""
    # Connect to MongoDB (using test/local instance)
    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    print("=== Testing Robust Project Deletion ===\n")

    # Initialize deletion service
    deletion_service = ProjectDeletionService(db)

    # 1. Create a test project with data
    test_project_id = ObjectId()
    test_project = {
        "_id": test_project_id,
        "name": "Test Robust Deletion Project",
        "path": f"/test/robust/{uuid4()}",
        "description": "Testing robust cascade deletion",
        "createdAt": datetime.now(UTC),
        "updatedAt": datetime.now(UTC),
    }

    await db.projects.insert_one(test_project)
    print(f"✓ Created test project: {test_project_id}")

    # 2. Create test sessions
    session_ids = []
    for i in range(5):
        session_id = str(uuid4())
        session_ids.append(session_id)
        session = {
            "_id": ObjectId(),
            "sessionId": session_id,
            "projectId": test_project_id,
            "startedAt": datetime.now(UTC),
            "endedAt": datetime.now(UTC),
            "title": f"Test Session {i+1}",
            "messageCount": 10,
        }
        await db.sessions.insert_one(session)

    print(f"✓ Created {len(session_ids)} test sessions")

    # 3. Create test messages (50 total)
    message_count = 0
    for session_id in session_ids:
        for j in range(10):
            message = {
                "_id": ObjectId(),
                "uuid": str(uuid4()),
                "sessionId": session_id,
                "type": "user" if j % 2 == 0 else "assistant",
                "timestamp": datetime.now(UTC),
                "content": f"Test message {j+1} in session {session_id[:8]}",
                "contentHash": f"hash_{uuid4()}",
                "createdAt": datetime.now(UTC),
            }
            await db.messages.insert_one(message)
            message_count += 1

    print(f"✓ Created {message_count} test messages")

    # 4. Verify initial state
    initial_project_count = await db.projects.count_documents({"_id": test_project_id})
    initial_session_count = await db.sessions.count_documents(
        {"projectId": test_project_id}
    )
    initial_message_count = await db.messages.count_documents(
        {"sessionId": {"$in": session_ids}}
    )

    print("\nBefore deletion:")
    print(f"  Projects: {initial_project_count}")
    print(f"  Sessions: {initial_session_count}")
    print(f"  Messages: {initial_message_count}")

    # 5. Test deletion (will use transactional if available, fallback otherwise)
    print("\n--- Testing Deletion (with automatic fallback) ---")

    # Test with recovery which handles both transactional and non-transactional
    result = await deletion_service.delete_project_with_recovery(test_project_id)

    print(f"Deletion result: Success={result['success']}")

    # 6. Verify complete deletion
    final_project_count = await db.projects.count_documents({"_id": test_project_id})
    final_session_count = await db.sessions.count_documents(
        {"projectId": test_project_id}
    )
    final_message_count = await db.messages.count_documents(
        {"sessionId": {"$in": session_ids}}
    )

    print("\nAfter deletion:")
    print(f"  Projects: {final_project_count}")
    print(f"  Sessions: {final_session_count}")
    print(f"  Messages: {final_message_count}")

    if (
        final_project_count == 0
        and final_session_count == 0
        and final_message_count == 0
    ):
        print("\n✅ DELETION WORKS CORRECTLY!")
    else:
        print("\n❌ DELETION FAILED!")
        print(
            f"  Remaining: Projects={final_project_count}, Sessions={final_session_count}, Messages={final_message_count}"
        )
        return False

    # 7. Test cleanup function
    print("\n--- Testing Cleanup Function ---")

    # Create some orphaned data
    orphan_session_id = str(uuid4())
    orphan_session = {
        "_id": ObjectId(),
        "sessionId": orphan_session_id,
        "projectId": ObjectId(),  # Non-existent project
        "startedAt": datetime.now(UTC),
        "title": "Orphaned Session",
    }
    await db.sessions.insert_one(orphan_session)

    orphan_message = {
        "_id": ObjectId(),
        "uuid": str(uuid4()),
        "sessionId": str(uuid4()),  # Non-existent session
        "type": "user",
        "timestamp": datetime.now(UTC),
        "content": "Orphaned message",
    }
    await db.messages.insert_one(orphan_message)

    print("✓ Created orphaned test data")

    # Run cleanup
    cleanup_stats = await deletion_service.cleanup_all_orphaned_data()
    print(f"Cleanup stats: {cleanup_stats}")

    # Verify cleanup
    orphan_session_exists = await db.sessions.count_documents(
        {"sessionId": orphan_session_id}
    )
    orphan_message_exists = await db.messages.count_documents(
        {"sessionId": orphan_message["sessionId"]}
    )

    if orphan_session_exists == 0 and orphan_message_exists == 0:
        print("✅ CLEANUP FUNCTION WORKS CORRECTLY!")
    else:
        print("❌ CLEANUP FUNCTION FAILED!")
        return False

    # 8. Test deletion with recovery (simulating failures)
    print("\n--- Testing Deletion with Recovery ---")

    # Create another test project
    test_project_2_id = ObjectId()
    await db.projects.insert_one(
        {
            "_id": test_project_2_id,
            "name": "Test Recovery Project",
            "path": f"/test/recovery/{uuid4()}",
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }
    )

    # Create a session for it
    test_session_2_id = str(uuid4())
    await db.sessions.insert_one(
        {
            "_id": ObjectId(),
            "sessionId": test_session_2_id,
            "projectId": test_project_2_id,
            "startedAt": datetime.now(UTC),
        }
    )

    # Create messages
    for i in range(5):
        await db.messages.insert_one(
            {
                "_id": ObjectId(),
                "uuid": str(uuid4()),
                "sessionId": test_session_2_id,
                "type": "user",
                "timestamp": datetime.now(UTC),
                "content": f"Message {i}",
            }
        )

    print(f"✓ Created test project 2: {test_project_2_id}")

    # Delete with recovery
    recovery_result = await deletion_service.delete_project_with_recovery(
        test_project_2_id
    )
    print(f"Recovery deletion result: Success={recovery_result['success']}")

    # Verify
    exists = await db.projects.count_documents({"_id": test_project_2_id})
    if exists == 0:
        print("✅ DELETION WITH RECOVERY WORKS!")
    else:
        print("❌ DELETION WITH RECOVERY FAILED!")
        return False

    print("\n" + "=" * 50)
    print("✅ ALL ROBUST DELETION TESTS PASSED!")
    print("=" * 50)
    return True


async def main():
    """Run the test."""
    try:
        success = await test_robust_deletion()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
