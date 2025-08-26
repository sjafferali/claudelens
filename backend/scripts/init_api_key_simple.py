#!/usr/bin/env python3
"""
Simple script to initialize API key for remote deployment.
"""

import hashlib
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from pymongo import MongoClient


def main():
    # Configuration
    API_KEY = "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"
    MONGO_URI = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"

    print("Connecting to MongoDB...")
    # Connect to MongoDB
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.claudelens

    # Hash the API key
    key_hash = hashlib.sha256(API_KEY.encode()).hexdigest()
    print(f"API key hash: {key_hash[:10]}...")

    # Check if user already exists
    existing_user = db.users.find_one({"username": "admin"})

    if existing_user:
        print(f"Admin user already exists with ID: {existing_user['_id']}")

        # Update the API key
        result = db.users.update_one(
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

        result = db.users.insert_one(user_doc)
        print(f"Created admin user with ID: {result.inserted_id}")

    print("\n✅ API Key configured successfully!")
    print(f"You can now login with the API key: {API_KEY}")

    # Close connection
    client.close()


if __name__ == "__main__":
    main()
