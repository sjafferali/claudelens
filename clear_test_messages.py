#!/usr/bin/env python3
"""Clear test messages from the database"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def clear_test_messages():
    """Remove test messages to verify fresh sync behavior"""

    # Connect to MongoDB
    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    # Count messages before
    count_before = await db.messages.count_documents({})
    print(f"Messages before cleanup: {count_before}")

    # Remove test messages
    result = await db.messages.delete_many({
        "uuid": {"$in": ["test-uuid-1", "test-uuid-2", "test-uuid-3"]}
    })
    print(f"Deleted {result.deleted_count} test messages")

    # Also remove the test session if it exists
    session_result = await db.sessions.delete_many({
        "sessionId": "test-session-1"
    })
    print(f"Deleted {session_result.deleted_count} test sessions")

    # Count messages after
    count_after = await db.messages.count_documents({})
    print(f"Messages after cleanup: {count_after}")

    # Optional: Clear ALL messages for a completely fresh test
    # Uncomment the following lines if you want to start fresh
    # print("\nClearing ALL messages for fresh test...")
    # result = await db.messages.delete_many({})
    # print(f"Deleted {result.deleted_count} messages")
    # session_result = await db.sessions.delete_many({})
    # print(f"Deleted {session_result.deleted_count} sessions")

    client.close()

if __name__ == "__main__":
    asyncio.run(clear_test_messages())
