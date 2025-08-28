"""Force fix timezone issue by updating API keys directly."""

import asyncio
import hashlib
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient


async def force_fix():
    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    # Direct update using MongoDB update operators
    api_key = "sk-test-3luYd4uXbl6xs079v7sUAWfFTmV-3ejTc2RjYGJ6puY"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Find the sjafferali user
    user = await db.users.find_one({"username": "sjafferali"})
    if not user:
        print("User not found")
        client.close()
        return

    print(f'Found user: {user.get("username")} (ID: {user["_id"]})')

    # Remove the old API key
    result1 = await db.users.update_one(
        {"_id": user["_id"]}, {"$pull": {"api_keys": {"key_hash": key_hash}}}
    )
    print(f"Removed old key: {result1.modified_count} document(s) modified")

    # Add a new API key with proper timezone
    new_key = {
        "name": "Test Key for Debugging (Fixed)",
        "key_hash": key_hash,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc).replace(month=9, day=27),  # Sept 27
        "last_used": datetime.now(timezone.utc),
        "active": True,
    }

    result2 = await db.users.update_one(
        {"_id": user["_id"]}, {"$push": {"api_keys": new_key}}
    )
    print(f"Added new key: {result2.modified_count} document(s) modified")

    # Verify the fix
    print("\n=== Verification ===")
    user = await db.users.find_one(
        {
            "api_keys": {
                "$elemMatch": {
                    "key_hash": key_hash,
                    "active": True,
                    "expires_at": {"$gt": datetime.now(timezone.utc)},
                }
            }
        }
    )

    if user:
        print(f"✅ User found with timezone-aware query: {user.get('username')}")
        for key in user.get("api_keys", []):
            if key.get("key_hash") == key_hash:
                print(f"  Key name: {key.get('name')}")
                print(f"  Expires: {key.get('expires_at')}")
                print(
                    f"  Timezone: {key.get('expires_at').tzinfo if key.get('expires_at') else 'None'}"
                )
    else:
        print("❌ User still cannot be found")

    client.close()


asyncio.run(force_fix())
