"""Test API authentication flow and check what gets stored."""

import asyncio
from datetime import UTC, datetime

import httpx
from motor.motor_asyncio import AsyncIOMotorClient


async def test_auth_flow():
    # API key for sjafferali user
    api_key = "sk-test-3luYd4uXbl6xs079v7sUAWfFTmV-3ejTc2RjYGJ6puY"

    print("=== Making authenticated request ===")

    # Clear recent data first (optional)
    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    # Record time before request
    before_time = datetime.now(UTC)

    # Make request with API key
    async with httpx.AsyncClient(verify=False) as http_client:
        response = await http_client.get(
            "https://claudecode.home.samir.network/api/v1/projects",
            headers={"X-API-Key": api_key},
        )
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")

    # Wait a bit for data to be flushed
    print("\nWaiting 2 seconds for data flush...")
    await asyncio.sleep(2)

    # Check what was recorded
    print("\n=== Checking rate limit records ===")

    # Get records created after our request
    records = await db.rate_limit_usage.find(
        {"timestamp": {"$gte": before_time}}
    ).to_list(10)

    print(f"Found {len(records)} new records")
    for record in records:
        print(f"  User ID: {record['user_id']}")
        print(f"  Limit Type: {record['limit_type']}")
        print(f"  Requests: {record.get('requests_made', 0)}")
        print(f"  Timestamp: {record['timestamp']}")
        print("  ---")

    # Check if sjafferali user ID appears
    sjafferali = await db.users.find_one({"username": "sjafferali"})
    if sjafferali:
        sjafferali_id = str(sjafferali["_id"])
        print(f"\nsjafferali user ID: {sjafferali_id}")

        # Check if this ID appears in recent records
        matching = [r for r in records if r.get("user_id") == sjafferali_id]
        print(f"Records matching sjafferali ID: {len(matching)}")

    client.close()


if __name__ == "__main__":
    asyncio.run(test_auth_flow())
