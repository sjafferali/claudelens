#!/usr/bin/env python3
"""Check available fields in messages collection."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection string
MONGO_URI = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"

async def main():
    """Check fields in messages collection."""
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.claudelens

    # Get a sample document
    sample = await db.messages.find_one({"type": "assistant"})

    if sample:
        print("Sample assistant message fields:")
        for key in sorted(sample.keys()):
            value = sample[key]
            if value is not None:
                print(f"  {key}: {type(value).__name__} = {str(value)[:50]}...")

    # Check for response time related fields
    print("\nChecking for response time fields...")

    # Check durationMs
    count_duration = await db.messages.count_documents({
        "type": "assistant",
        "durationMs": {"$exists": True, "$ne": None, "$gt": 0}
    })
    print(f"Messages with durationMs: {count_duration}")

    # Check responseTime
    count_response = await db.messages.count_documents({
        "type": "assistant",
        "responseTime": {"$exists": True, "$ne": None, "$gt": 0}
    })
    print(f"Messages with responseTime: {count_response}")

    # Get a sample with durationMs
    sample_duration = await db.messages.find_one({
        "type": "assistant",
        "durationMs": {"$exists": True, "$ne": None, "$gt": 0}
    })

    if sample_duration:
        print(f"\nSample durationMs value: {sample_duration.get('durationMs')}")

    client.close()

if __name__ == "__main__":
    asyncio.run(main())
