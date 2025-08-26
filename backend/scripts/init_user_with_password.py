#!/usr/bin/env python3
"""
Script to initialize a user with username/password authentication.
"""

import sys
from datetime import datetime, timezone

# Add backend directory to path before importing app modules
sys.path.append("/Users/sjafferali/github/personal/claudelens/backend")

from bson import ObjectId
from pymongo import MongoClient

from app.services.auth import AuthService


def main():
    # Configuration for remote deployment
    MONGO_URI = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    USERNAME = "admin"
    EMAIL = "admin@claudelens.local"
    PASSWORD = "admin123"  # You should change this to a secure password

    print("Connecting to MongoDB...")
    # Connect to MongoDB
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.claudelens

    # Check if user already exists
    existing_user = db.users.find_one(
        {"$or": [{"username": USERNAME}, {"email": EMAIL}]}
    )

    if existing_user:
        print(f"User '{USERNAME}' already exists with ID: {existing_user['_id']}")

        # Update the user with password hash
        password_hash = AuthService.hash_password(PASSWORD)
        result = db.users.update_one(
            {"_id": existing_user["_id"]},
            {
                "$set": {
                    "password_hash": password_hash,
                    "is_active": True,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        print(f"Updated password for user '{USERNAME}'")
    else:
        # Create new user with password
        password_hash = AuthService.hash_password(PASSWORD)

        user_doc = {
            "_id": ObjectId(),
            "email": EMAIL,
            "username": USERNAME,
            "password_hash": password_hash,
            "role": "admin",
            "permissions": ["*"],
            "api_keys": [],  # No API keys initially
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True,
            "project_count": 0,
            "session_count": 0,
            "message_count": 0,
            "total_disk_usage": 0,
        }

        result = db.users.insert_one(user_doc)
        print(f"Created user '{USERNAME}' with ID: {result.inserted_id}")

    print("\n✅ User configured successfully!")
    print("You can now login with:")
    print(f"  Username: {USERNAME}")
    print(f"  Password: {PASSWORD}")

    # Close connection
    client.close()


if __name__ == "__main__":
    main()
