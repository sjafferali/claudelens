#!/usr/bin/env python3
"""
Initialize API key for remote deployment.
Usage: python init_api_key.py --api-key YOUR_API_KEY --mongo-uri YOUR_MONGO_URI
"""

import argparse
import asyncio
import hashlib
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient


async def create_user_with_api_key(mongo_uri: str, api_key: str):
    """Create a default admin user with the provided API key."""
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongo_uri)
    db = client.claudelens

    # Hash the API key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Check if user already exists
    existing_user = await db.users.find_one({"username": "admin"})

    if existing_user:
        print(f"Admin user already exists with ID: {existing_user['_id']}")

        # Update the API key
        result = await db.users.update_one(
            {"_id": existing_user["_id"]},
            {
                "$set": {
                    "api_keys": [
                        {
                            "name": "Default API Key",
                            "key_hash": key_hash,
                            "created_at": datetime.now(timezone.utc),
                            "expires_at": datetime.now(timezone.utc)
                            + timedelta(days=365),
                            "last_used": None,
                            "active": True,
                        }
                    ],
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        print("Updated API key for admin user")
    else:
        # Create new admin user
        user_doc = {
            "_id": ObjectId(),
            "email": "admin@claudelens.local",
            "username": "admin",
            "role": "admin",
            "permissions": ["*"],
            "api_keys": [
                {
                    "name": "Default API Key",
                    "key_hash": key_hash,
                    "created_at": datetime.now(timezone.utc),
                    "expires_at": datetime.now(timezone.utc) + timedelta(days=365),
                    "last_used": None,
                    "active": True,
                }
            ],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True,
            "storage_used": 0,
            "storage_limit": None,  # Unlimited for admin
            "rate_limits": {"requests_per_minute": 1000, "requests_per_hour": 10000},
        }

        result = await db.users.insert_one(user_doc)
        print(f"Created admin user with ID: {result.inserted_id}")

    print("API Key configured successfully!")
    print(f"You can now login with the API key: {api_key}")

    # Close connection
    client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Initialize API key for ClaudeLens deployment"
    )
    parser.add_argument("--api-key", required=True, help="The API key to configure")
    parser.add_argument("--mongo-uri", required=True, help="MongoDB connection URI")

    args = parser.parse_args()

    # Run the async function
    asyncio.run(create_user_with_api_key(args.mongo_uri, args.api_key))


if __name__ == "__main__":
    main()
