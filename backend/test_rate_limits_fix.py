#!/usr/bin/env python3
"""Test script to verify rate limit fixes and populate test data."""

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app.models.rate_limit_usage import RateLimitType
from app.services.rate_limit_usage_service import RateLimitUsageService


async def test_rate_limits():
    """Test rate limit functionality."""
    # Connect to the remote MongoDB
    connection_string = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    client = AsyncIOMotorClient(connection_string)
    db = client.claudelens

    print("Connected to MongoDB...")

    # Initialize service
    service = RateLimitUsageService(db)

    # Get a test user (admin user)
    admin_user = await db.users.find_one({"username": "admin"})
    if not admin_user:
        print("Admin user not found, creating one...")
        admin_user = {
            "_id": "test-admin-user",
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin",
        }
        await db.users.insert_one(admin_user)

    user_id = str(admin_user["_id"])
    print(f"Testing with user: {admin_user['username']} ({user_id})")

    # Record some test requests
    print("\n1. Recording test requests...")
    for limit_type in [
        RateLimitType.HTTP,
        RateLimitType.INGESTION,
        RateLimitType.AI,
        RateLimitType.SEARCH,
    ]:
        for i in range(10):
            allowed = i < 8  # 80% success rate
            await service.record_request(
                user_id=user_id,
                limit_type=limit_type,
                allowed=allowed,
                response_time_ms=50.0 + i * 10,
                bytes_transferred=1024 * (i + 1),
            )
            print(
                f"  Recorded {limit_type.value} request {i+1}: {'allowed' if allowed else 'blocked'}"
            )

    # Force flush metrics to database
    print("\n2. Flushing metrics to database...")
    await service._flush_metrics()
    print("  Metrics flushed successfully")

    # Test get_current_usage_snapshot
    print("\n3. Testing get_current_usage_snapshot...")
    snapshot = await service.get_current_usage_snapshot(user_id)

    print(f"  User ID: {snapshot.user_id}")
    print(f"  Total requests today: {snapshot.total_requests_today}")
    print(f"  Total blocked today: {snapshot.total_blocked_today}")

    # Check each usage type
    usage_fields = [
        "http_usage",
        "ingestion_usage",
        "ai_usage",
        "search_usage",
        "analytics_usage",
        "export_usage",
        "import_usage",
        "backup_usage",
        "restore_usage",
    ]

    print("\n4. Checking all usage fields:")
    for field in usage_fields:
        usage = getattr(snapshot, field)
        if isinstance(usage, dict):
            print(f"  {field}:")
            print(f"    - current: {usage.get('current', 'N/A')}")
            print(f"    - limit: {usage.get('limit', 'N/A')}")
            print(f"    - remaining: {usage.get('remaining', 'N/A')}")
            print(f"    - percentage_used: {usage.get('percentage_used', 0):.1f}%")
        else:
            print(f"  {field}: NOT A DICT - {type(usage)}")

    # Test get_top_users_by_usage
    print("\n5. Testing get_top_users_by_usage...")
    top_users = await service.get_top_users_by_usage(
        limit_type=None, limit=5, time_range_hours=24
    )

    if top_users:
        print(f"  Found {len(top_users)} top users:")
        for user_data in top_users:
            print(
                f"    - User {user_data['_id']}: {user_data['total_requests']} requests, "
                f"{user_data['total_blocked']} blocked, {user_data['avg_usage_rate']:.1f}% avg rate"
            )
    else:
        print("  No top users found (might need to wait for data to populate)")

    # Check rate_limit_usage collection directly
    print("\n6. Checking rate_limit_usage collection directly...")
    count = await db.rate_limit_usage.count_documents({})
    print(f"  Total documents in rate_limit_usage: {count}")

    if count > 0:
        sample = await db.rate_limit_usage.find_one({})
        print("  Sample document:")
        for key, value in sample.items():
            if key != "_id":
                print(f"    - {key}: {value}")

    print("\n✅ Test completed successfully!")

    # Clean up connection
    client.close()


if __name__ == "__main__":
    asyncio.run(test_rate_limits())
