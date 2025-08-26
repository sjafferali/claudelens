#!/usr/bin/env python3
"""
Script to reset user password for ClaudeLens.
"""

import getpass
import sys
from datetime import datetime, timezone

# Add backend directory to path before importing app modules
sys.path.append("/Users/sjafferali/github/personal/claudelens/backend")

from pymongo import MongoClient

from app.services.auth import AuthService


def main():
    # Configuration for remote deployment
    MONGO_URI = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"

    print("🔐 ClaudeLens Password Reset Tool")
    print("=" * 40)

    # Get username or email
    identifier = input("Enter username or email: ").strip()
    if not identifier:
        print("❌ Username or email is required")
        return

    # Get new password (hidden input)
    password = getpass.getpass("Enter new password: ").strip()
    if not password:
        print("❌ Password is required")
        return

    # Confirm password
    confirm_password = getpass.getpass("Confirm new password: ").strip()
    if password != confirm_password:
        print("❌ Passwords do not match")
        return

    print("\nConnecting to MongoDB...")
    # Connect to MongoDB
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client.claudelens

        # Try to connect
        client.server_info()
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return

    # Find user by username or email
    user = db.users.find_one({"$or": [{"username": identifier}, {"email": identifier}]})

    if not user:
        print(f"❌ User '{identifier}' not found")
        client.close()
        return

    # Update the user with new password hash
    password_hash = AuthService.hash_password(password)
    result = db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_hash": password_hash,
                "is_active": True,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    if result.modified_count > 0:
        print("\n✅ Password successfully reset for user:")
        print(f"   Username: {user.get('username', 'N/A')}")
        print(f"   Email: {user.get('email', 'N/A')}")
        print(f"   Role: {user.get('role', 'user')}")
        print("\nYou can now login with the new password.")
    else:
        print("❌ Failed to update password")

    # Close connection
    client.close()


if __name__ == "__main__":
    main()
