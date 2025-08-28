"""Create a test API key for debugging."""

import asyncio
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorClient


async def create_test_api_key():
    # Connect to MongoDB
    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    # Generate a new API key
    api_key = f"sk-test-{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Find the sjafferali user
    user = await db.users.find_one({"username": "sjafferali"})

    if not user:
        print("User sjafferali not found")
        client.close()
        return

    print(f"Found user: {user.get('username')} (ID: {user['_id']})")

    # Add API key to user
    api_key_doc = {
        "name": "Test Key for Debugging",
        "key_hash": key_hash,
        "created_at": datetime.now(UTC),
        "expires_at": datetime.now(UTC) + timedelta(days=30),
        "last_used": None,
        "active": True,
    }

    # Update user with new API key
    result = await db.users.update_one(
        {"_id": user["_id"]}, {"$push": {"api_keys": api_key_doc}}
    )

    if result.modified_count > 0:
        print("\n✅ API key created successfully!")
        print(f"User: {user['username']}")
        print(f"User ID: {user['_id']}")
        print(f"API Key: {api_key}")
        print("\nUse this API key to test:")
        print(
            f'curl -H "X-API-Key: {api_key}" http://claudecode.home.samir.network/api/v1/projects'
        )
    else:
        print("Failed to create API key")

    client.close()


if __name__ == "__main__":
    asyncio.run(create_test_api_key())
