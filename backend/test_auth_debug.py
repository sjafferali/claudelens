"""Debug authentication issue with API key."""

import asyncio
import hashlib
from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorClient


async def debug_auth():
    client = AsyncIOMotorClient(
        "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    )
    db = client.claudelens

    api_key = "sk-test-3luYd4uXbl6xs079v7sUAWfFTmV-3ejTc2RjYGJ6puY"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    print(f"API Key: {api_key[:12]}...{api_key[-4:]}")
    print(f"Key Hash: {key_hash}")

    # Try the exact query used in verify_tenant_from_api_key
    now = datetime.now(UTC)
    print(f"\nCurrent UTC time: {now}")

    query = {
        "api_keys": {
            "$elemMatch": {
                "key_hash": key_hash,
                "active": True,
                "expires_at": {"$gt": now},
            }
        }
    }

    print(f"\nRunning query: {query}")

    user = await db.users.find_one(query)

    if user:
        print(f'\n✓ Found user: {user.get("username")} (ID: {user["_id"]})')

        # Check the API key details
        for key in user.get("api_keys", []):
            if key.get("key_hash") == key_hash:
                print("\nAPI Key Details:")
                print(f'  Name: {key.get("name")}')
                print(f'  Active: {key.get("active")}')
                print(f'  Created: {key.get("created_at")}')
                print(f'  Expires: {key.get("expires_at")}')
                print(f'  Last Used: {key.get("last_used")}')

                # Check expiration
                expires = key.get("expires_at")
                if expires:
                    if expires > now:
                        print(
                            f"  ✓ Key is not expired (expires in {(expires - now).days} days)"
                        )
                    else:
                        print("  ✗ Key is expired!")
                else:
                    print("  ⚠️ No expiration date set")
                break
    else:
        print("\n✗ No user found with query")

        # Try without expiration check
        user2 = await db.users.find_one(
            {"api_keys": {"$elemMatch": {"key_hash": key_hash, "active": True}}}
        )

        if user2:
            print(f'\n⚠️ Found user WITHOUT expiration check: {user2.get("username")}')
            for key in user2.get("api_keys", []):
                if key.get("key_hash") == key_hash:
                    print(f'  Expires at: {key.get("expires_at")}')
                    print(
                        f'  Is expired: {key.get("expires_at") <= now if key.get("expires_at") else "No expiry"}'
                    )

    client.close()


asyncio.run(debug_auth())
