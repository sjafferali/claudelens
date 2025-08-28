"""Debug script to check rate limit usage data."""

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient


async def check_rate_limit_data():
    # Connect to MongoDB
    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    # Check rate_limit_usage collection
    print("=== Rate Limit Usage Data ===")

    # Get all unique user IDs
    user_ids = await db.rate_limit_usage.distinct("user_id")
    print(f"Found {len(user_ids)} unique user_ids in rate_limit_usage collection:")
    for uid in user_ids[:10]:  # Show first 10
        print(f"  - {uid}")
        # Count records for this user
        count = await db.rate_limit_usage.count_documents({"user_id": uid})
        print(f"    Records: {count}")

    # Check users collection
    print("\n=== Users Collection ===")
    users = await db.users.find({}).to_list(10)
    for user in users:
        print(f"User: {user.get('username', 'N/A')} (ID: {user['_id']})")
        # Check if this user has any rate limit records
        count = await db.rate_limit_usage.count_documents({"user_id": str(user["_id"])})
        print(f"  Rate limit records: {count}")

    client.close()


if __name__ == "__main__":
    asyncio.run(check_rate_limit_data())
