"""Fix timezone issue in API key expiration dates."""

import asyncio
import hashlib
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient


async def fix_timezone():
    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    api_key = "sk-test-3luYd4uXbl6xs079v7sUAWfFTmV-3ejTc2RjYGJ6puY"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    print(f"Fixing timezone for API key: {api_key[:12]}...{api_key[-4:]}")

    # Find the user with this API key
    user = await db.users.find_one({"api_keys.key_hash": key_hash})

    if not user:
        print("User not found")
        client.close()
        return

    print(f'Found user: {user.get("username")} (ID: {user["_id"]})')

    # Fix the timezone for all API keys of this user
    updated_keys = []
    for key in user.get("api_keys", []):
        if key.get("key_hash") == key_hash:
            print(f'\nFixing key: {key.get("name")}')
            print(
                f'  Old expires_at: {key.get("expires_at")} (type: {type(key.get("expires_at"))})'
            )

            # Convert naive datetime to UTC aware datetime
            if key.get("expires_at"):
                if key["expires_at"].tzinfo is None:
                    # It's naive, make it UTC aware by creating a new datetime
                    old_dt = key["expires_at"]
                    key["expires_at"] = datetime(
                        old_dt.year,
                        old_dt.month,
                        old_dt.day,
                        old_dt.hour,
                        old_dt.minute,
                        old_dt.second,
                        old_dt.microsecond,
                        tzinfo=timezone.utc,
                    )
                    print(
                        f'  New expires_at: {key["expires_at"]} (type: {type(key["expires_at"])})'
                    )
                else:
                    print(f'  Already has timezone: {key["expires_at"].tzinfo}')

            # Also fix created_at if needed
            if key.get("created_at") and key["created_at"].tzinfo is None:
                old_dt = key["created_at"]
                key["created_at"] = datetime(
                    old_dt.year,
                    old_dt.month,
                    old_dt.day,
                    old_dt.hour,
                    old_dt.minute,
                    old_dt.second,
                    old_dt.microsecond,
                    tzinfo=timezone.utc,
                )
                print(f'  Fixed created_at: {key["created_at"]}')

            # Fix last_used if it exists and is naive
            if key.get("last_used") and key["last_used"].tzinfo is None:
                old_dt = key["last_used"]
                key["last_used"] = datetime(
                    old_dt.year,
                    old_dt.month,
                    old_dt.day,
                    old_dt.hour,
                    old_dt.minute,
                    old_dt.second,
                    old_dt.microsecond,
                    tzinfo=timezone.utc,
                )
                print(f'  Fixed last_used: {key["last_used"]}')

        updated_keys.append(key)

    # Update the user's API keys
    result = await db.users.update_one(
        {"_id": user["_id"]}, {"$set": {"api_keys": updated_keys}}
    )

    if result.modified_count > 0:
        print("\n✅ Successfully fixed timezone issues")

        # Verify the fix
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
            print(
                "✅ Verification successful: User can now be found with timezone-aware query"
            )
        else:
            print("❌ Verification failed: User still cannot be found")
    else:
        print("\n⚠️ No changes made")

    client.close()


asyncio.run(fix_timezone())
