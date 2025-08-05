#!/usr/bin/env python3
"""Check MongoDB version."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection string
MONGO_URI = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"

async def main():
    """Check MongoDB version."""
    client = AsyncIOMotorClient(MONGO_URI)

    # Get server info
    server_info = await client.server_info()
    version = server_info.get('version', 'Unknown')

    print(f"MongoDB Version: {version}")

    # Parse version
    major, minor = map(int, version.split('.')[:2])
    print(f"Major: {major}, Minor: {minor}")

    # Check if $percentile is available (MongoDB 7.0+)
    if major >= 7:
        print("✓ $percentile operator is available")
    else:
        print("✗ $percentile operator is NOT available (requires MongoDB 7.0+)")
        print("  Will use sampling approach for percentile calculations")

    client.close()

if __name__ == "__main__":
    asyncio.run(main())
