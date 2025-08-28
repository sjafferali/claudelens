"""Test that middleware order fix properly attributes rate limits to authenticated users."""

import asyncio
from datetime import UTC, datetime

import httpx
from motor.motor_asyncio import AsyncIOMotorClient


async def test_middleware_fix():
    # API key for sjafferali user
    api_key = "sk-test-3luYd4uXbl6xs079v7sUAWfFTmV-3ejTc2RjYGJ6puY"

    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    # Get sjafferali user info
    user = await db.users.find_one({"username": "sjafferali"})
    if not user:
        print("ERROR: sjafferali user not found")
        client.close()
        return

    user_id = str(user["_id"])
    print(f"✓ Found sjafferali user with ID: {user_id}")

    # Record current time
    start_time = datetime.now(UTC)

    print("\n=== Making API requests with authentication ===")

    # Make several API requests
    async with httpx.AsyncClient(verify=False) as http_client:
        for i in range(10):
            response = await http_client.get(
                "https://claudecode.home.samir.network/api/v1/projects",
                headers={"X-API-Key": api_key},
            )
            print(f"  Request {i+1}: Status {response.status_code}")
            await asyncio.sleep(0.1)

    print("\n⏳ Waiting 65 seconds for rate limit data to be flushed...")
    await asyncio.sleep(65)

    # Check what was recorded
    print("\n=== Checking rate limit records ===")

    # Get records created after our test started
    records = await db.rate_limit_usage.find(
        {
            "timestamp": {"$gte": start_time},
            "user_id": user_id,  # Check for exact user ID
        }
    ).to_list(10)

    if records:
        print(f"✅ SUCCESS: Found {len(records)} records for sjafferali (ID: {user_id})")
        for record in records[:3]:  # Show first 3
            print(
                f"  - Type: {record['limit_type']}, Requests: {record['requests_made']}, Time: {record['timestamp']}"
            )
    else:
        print(f"❌ FAILED: No records found for sjafferali (ID: {user_id})")

        # Check what user_ids were recorded instead
        all_records = await db.rate_limit_usage.find(
            {"timestamp": {"$gte": start_time}}
        ).to_list(10)

        if all_records:
            print("\n  Records found with different user_ids:")
            unique_users = set(r["user_id"] for r in all_records)
            for uid in unique_users:
                count = sum(1 for r in all_records if r["user_id"] == uid)
                print(f"    - {uid}: {count} records")
        else:
            print("\n  No records found at all since test started")

    # Summary
    print("\n=== Summary ===")
    if records:
        print(
            "✅ Middleware fix is working: API key requests are properly attributed to authenticated user"
        )
    else:
        print(
            "❌ Middleware fix not working yet: API key requests not attributed to authenticated user"
        )
        print("   Note: The fix may need to be deployed to take effect")

    client.close()


if __name__ == "__main__":
    asyncio.run(test_middleware_fix())
