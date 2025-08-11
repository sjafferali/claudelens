#!/usr/bin/env python3
"""Test cascade deletion via API."""

import asyncio
import json
from datetime import UTC, datetime
from uuid import uuid4

import httpx
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient


async def test_api_cascade_deletion():
    """Test that project deletion via API cascades properly."""
    # API configuration
    api_url = "http://c-rat.local.samir.systems:21855"
    api_key = "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"
    headers = {"X-API-Key": api_key}

    # Direct database connection for setup and verification
    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    print("=== Testing API Cascade Deletion ===\n")

    # 1. Create a test project directly in DB
    test_project_id = ObjectId()
    test_project = {
        "_id": test_project_id,
        "name": "API Test Project for Cascade",
        "path": f"/test/api/cascade/{uuid4()}",
        "description": "Testing API cascade deletion",
        "createdAt": datetime.now(UTC),
        "updatedAt": datetime.now(UTC),
    }

    await db.projects.insert_one(test_project)
    print(f"✓ Created test project: {test_project_id}")

    # 2. Create test sessions
    session_ids = []
    for i in range(2):
        session_id = str(uuid4())
        session_ids.append(session_id)
        session = {
            "_id": ObjectId(),
            "sessionId": session_id,
            "projectId": test_project_id,
            "startedAt": datetime.now(UTC),
            "endedAt": datetime.now(UTC),
            "title": f"API Test Session {i+1}",
        }
        await db.sessions.insert_one(session)

    print(f"✓ Created {len(session_ids)} test sessions")

    # 3. Create test messages
    message_count = 0
    for session_id in session_ids:
        for j in range(3):  # 3 messages per session
            message = {
                "_id": ObjectId(),
                "uuid": str(uuid4()),
                "sessionId": session_id,
                "type": "user" if j % 2 == 0 else "assistant",
                "timestamp": datetime.now(UTC),
                "content": f"API test message {j+1}",
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

    print("\nBefore API deletion:")
    print(f"  Projects: {project_count}")
    print(f"  Sessions: {session_count}")
    print(f"  Messages: {message_count}")

    # 5. Delete via API
    async with httpx.AsyncClient() as client_http:
        print(f"\nCalling DELETE /api/v1/projects/{test_project_id}")
        response = await client_http.delete(
            f"{api_url}/api/v1/projects/{test_project_id}",
            headers=headers,
            params={"cascade": "true"},
        )

        print(f"Response status: {response.status_code}")
        print(f"Response body: {json.dumps(response.json(), indent=2)}")

        if response.status_code != 200:
            print("❌ API deletion failed!")
            return False

    # 6. Wait a moment for async operations
    await asyncio.sleep(2)

    # 7. Verify cascade deletion
    project_count = await db.projects.count_documents({"_id": test_project_id})
    session_count = await db.sessions.count_documents({"projectId": test_project_id})
    message_count = await db.messages.count_documents(
        {"sessionId": {"$in": session_ids}}
    )

    print("\nAfter API deletion:")
    print(f"  Projects: {project_count}")
    print(f"  Sessions: {session_count}")
    print(f"  Messages: {message_count}")

    if project_count == 0 and session_count == 0 and message_count == 0:
        print("\n✅ API CASCADE DELETION WORKS CORRECTLY!")
        return True
    else:
        print("\n❌ API CASCADE DELETION FAILED!")
        print("Some data was not deleted properly.")
        return False


async def main():
    """Run the test."""
    try:
        success = await test_api_cascade_deletion()
        import sys

        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        import sys

        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
