"""User service layer."""

import asyncio
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import List, Optional, Tuple

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import APIKey, UserCreate, UserInDB, UserRole, UserUpdate


class UserService:
    """Service for user operations."""

    KEY_PREFIX = "cl_"
    KEY_LENGTH = 32

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    @staticmethod
    def generate_api_key() -> Tuple[str, str]:
        """Generate API key and its hash."""
        random_bytes = secrets.token_urlsafe(UserService.KEY_LENGTH)
        api_key = f"{UserService.KEY_PREFIX}{random_bytes}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return api_key, key_hash

    @staticmethod
    def verify_api_key(provided_key: str, stored_hash: str) -> bool:
        """Verify an API key against its stored hash."""
        provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
        return hmac.compare_digest(provided_hash, stored_hash)

    async def create_user(self, user_data: UserCreate) -> Tuple[UserInDB, str]:
        """Create a new user with an initial API key."""
        # Check if user already exists
        existing = await self.db.users.find_one(
            {"$or": [{"email": user_data.email}, {"username": user_data.username}]}
        )
        if existing:
            raise ValueError("User with this email or username already exists")

        # Generate initial API key
        api_key, key_hash = self.generate_api_key()
        initial_key = APIKey(
            key_hash=key_hash,
            name="Default API Key",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=365),
            active=True,
        )

        # Create user document
        user_doc = {
            "email": user_data.email,
            "username": user_data.username,
            "role": user_data.role,
            "api_keys": [initial_key.model_dump()],
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "project_count": 0,
            "session_count": 0,
            "message_count": 0,
            "total_disk_usage": 0,
        }

        result = await self.db.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id

        from typing import cast

        user = UserInDB(
            _id=cast(ObjectId, user_doc["_id"]),
            email=cast(str, user_doc["email"]),
            username=cast(str, user_doc["username"]),
            role=cast(UserRole, user_doc["role"]),
            api_keys=cast(list[APIKey], user_doc["api_keys"]),
            created_at=cast(datetime, user_doc["created_at"]),
            updated_at=cast(datetime, user_doc["updated_at"]),
            project_count=cast(int, user_doc["project_count"]),
            session_count=cast(int, user_doc["session_count"]),
            message_count=cast(int, user_doc["message_count"]),
            total_disk_usage=cast(int, user_doc["total_disk_usage"]),
        )

        return user, api_key

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID."""
        if not ObjectId.is_valid(user_id):
            return None

        user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            return None

        return UserInDB(**user_doc)

    async def get_user_by_api_key(self, api_key: str) -> Optional[UserInDB]:
        """Get user by API key."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Find user with this API key hash
        user_doc = await self.db.users.find_one(
            {
                "api_keys": {
                    "$elemMatch": {
                        "key_hash": key_hash,
                        "active": True,
                        "expires_at": {"$gt": datetime.now(UTC)},
                    }
                }
            }
        )

        if not user_doc:
            return None

        # Update last_used timestamp
        await self.db.users.update_one(
            {
                "_id": user_doc["_id"],
                "api_keys.key_hash": key_hash,
            },
            {"$set": {"api_keys.$.last_used": datetime.now(UTC)}},
        )

        return UserInDB(**user_doc)

    async def update_user(
        self, user_id: str, user_update: UserUpdate
    ) -> Optional[UserInDB]:
        """Update user details."""
        if not ObjectId.is_valid(user_id):
            return None

        update_data = user_update.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_user_by_id(user_id)

        update_data["updated_at"] = datetime.now(UTC)

        result = await self.db.users.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_data},
            return_document=True,
        )

        if not result:
            return None

        return UserInDB(**result)

    async def delete_user(self, user_id: str) -> bool:
        """Delete user and all associated data."""
        if not ObjectId.is_valid(user_id):
            return False

        user_oid = ObjectId(user_id)

        # Delete all user data in parallel
        delete_tasks = [
            self.db.messages.delete_many({"user_id": user_oid}),
            self.db.sessions.delete_many({"user_id": user_oid}),
            self.db.projects.delete_many({"user_id": user_oid}),
            self.db.users.delete_one({"_id": user_oid}),
        ]

        results = await asyncio.gather(*delete_tasks)
        return results[3].deleted_count > 0

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
    ) -> Tuple[List[UserInDB], int]:
        """List users with pagination."""
        query = {}
        if role:
            query["role"] = role

        total = await self.db.users.count_documents(query)
        cursor = (
            self.db.users.find(query).sort("created_at", -1).skip(skip).limit(limit)
        )

        users = []
        async for user_doc in cursor:
            users.append(UserInDB(**user_doc))

        return users, total

    async def generate_new_api_key(self, user_id: str, key_name: str) -> Optional[str]:
        """Generate a new API key for a user."""
        if not ObjectId.is_valid(user_id):
            return None

        api_key, key_hash = self.generate_api_key()
        new_key = APIKey(
            key_hash=key_hash,
            name=key_name,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=365),
            active=True,
        )

        result = await self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$push": {"api_keys": new_key.model_dump()},
                "$set": {"updated_at": datetime.now(UTC)},
            },
        )

        if result.modified_count > 0:
            return api_key
        return None

    async def revoke_api_key(self, user_id: str, key_hash: str) -> bool:
        """Revoke an API key."""
        if not ObjectId.is_valid(user_id):
            return False

        result = await self.db.users.update_one(
            {"_id": ObjectId(user_id), "api_keys.key_hash": key_hash},
            {
                "$set": {
                    "api_keys.$.active": False,
                    "updated_at": datetime.now(UTC),
                }
            },
        )

        return result.modified_count > 0

    async def update_user_stats(self, user_id: str, stats: dict) -> bool:
        """Update user statistics."""
        if not ObjectId.is_valid(user_id):
            return False

        stats["updated_at"] = datetime.now(UTC)
        result = await self.db.users.update_one(
            {"_id": ObjectId(user_id)}, {"$set": stats}
        )

        return result.modified_count > 0
