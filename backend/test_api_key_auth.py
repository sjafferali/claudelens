"""Test API key authentication and rate limit tracking."""

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient


async def test_api_key_auth():
    # Connect to MongoDB
    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    # Find a user with an API key
    print("=== Finding user with API key ===")
    user = await db.users.find_one({"api_keys": {"$exists": True, "$ne": []}})

    if not user:
        print("No user with API key found")
        client.close()
        return

    print(f"Found user: {user.get('username')} (ID: {user['_id']})")

    # Get the API key (we'll need to use a known key since we can't decrypt the hash)
    # For testing, let's check if there's a known API key we can use
    api_key = user.get("api_keys", [{}])[0].get("key", None)

    if not api_key:
        print("Note: API key is hashed, cannot retrieve original value")
        print("You'll need to use a known API key for testing")
        # For now, let's check what's in the rate limit usage

        print("\n=== Checking rate limit usage for this user ===")
        count = await db.rate_limit_usage.count_documents({"user_id": str(user["_id"])})
        print(f"Rate limit records for user {user['_id']}: {count}")

        # Check for any records with partial matches
        partial_records = await db.rate_limit_usage.find(
            {"user_id": {"$regex": "^api"}}
        ).to_list(5)

        print("\n=== Records starting with 'api' ===")
        for record in partial_records:
            print(
                f"  user_id: {record['user_id']}, timestamp: {record.get('timestamp')}"
            )

    client.close()


if __name__ == "__main__":
    asyncio.run(test_api_key_auth())
