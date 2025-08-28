"""Check recent rate limit records."""

import asyncio
from datetime import UTC, datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorClient


async def check_recent_rate_limits():
    # Connect to MongoDB
    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    # Get records from the last 5 minutes
    five_mins_ago = datetime.now(UTC) - timedelta(minutes=5)

    print("=== Rate Limit Records (Last 5 Minutes) ===")
    cursor = (
        db.rate_limit_usage.find({"timestamp": {"$gte": five_mins_ago}})
        .sort("timestamp", -1)
        .limit(10)
    )

    records = await cursor.to_list(10)

    for record in records:
        user_id = record.get("user_id")
        timestamp = record.get("timestamp")
        limit_type = record.get("limit_type")
        requests_made = record.get("requests_made")

        # Try to find the user
        user = None
        if user_id and ":" not in user_id and len(user_id) == 24:
            try:
                from bson import ObjectId

                user = await db.users.find_one({"_id": ObjectId(user_id)})
            except Exception:
                pass

        username = user.get("username") if user else f"Unknown ({user_id})"

        print(
            f"Time: {timestamp.strftime('%H:%M:%S')}, User: {username}, Type: {limit_type}, Requests: {requests_made}"
        )

    print("\n=== User ID Summary ===")
    # Get distinct user_ids from recent records
    user_ids = await db.rate_limit_usage.distinct(
        "user_id", {"timestamp": {"$gte": five_mins_ago}}
    )

    for uid in user_ids:
        count = await db.rate_limit_usage.count_documents(
            {"user_id": uid, "timestamp": {"$gte": five_mins_ago}}
        )

        # Try to identify the user
        user = None
        if uid and ":" not in uid and "_" not in uid and len(uid) == 24:
            try:
                from bson import ObjectId

                user = await db.users.find_one({"_id": ObjectId(uid)})
            except Exception:
                pass

        username = user.get("username") if user else f"Unknown ({uid})"
        print(f"  {username}: {count} records")

    client.close()


if __name__ == "__main__":
    asyncio.run(check_recent_rate_limits())
