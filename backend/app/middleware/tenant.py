"""Tenant isolation middleware."""

import hashlib
import logging
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import UserRole

logger = logging.getLogger(__name__)


class TenantContext:
    """Stores tenant context for the current request."""

    def __init__(self) -> None:
        self.user_id: Optional[str] = None
        self.user_role: Optional[UserRole] = None
        self.api_key_name: Optional[str] = None
        self.permissions: list = []


async def get_tenant_context(request: Request) -> TenantContext:
    """Get tenant context from request state."""
    if not hasattr(request.state, "tenant_context"):
        request.state.tenant_context = TenantContext()
    return request.state.tenant_context  # type: ignore


async def verify_tenant_from_api_key(
    api_key: str, db: AsyncIOMotorDatabase, request: Request
) -> str:
    """Verify tenant from API key and inject into request context."""
    # Hash the provided key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Look up the key in the database
    from datetime import UTC, datetime

    # MongoDB stores datetimes as UTC but returns them as naive datetimes
    # So we need to use a naive UTC datetime for comparison
    now_utc = datetime.now(UTC).replace(tzinfo=None)

    user = await db.users.find_one(
        {
            "api_keys": {
                "$elemMatch": {
                    "key_hash": key_hash,
                    "active": True,
                    "expires_at": {"$gt": now_utc},
                }
            }
        }
    )

    if not user:
        logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
        raise HTTPException(status_code=401, detail="Invalid or expired API key")

    # Update last_used timestamp (use naive UTC for MongoDB)
    await db.users.update_one(
        {"_id": user["_id"], "api_keys.key_hash": key_hash},
        {"$set": {"api_keys.$.last_used": datetime.now(UTC).replace(tzinfo=None)}},
    )

    # Inject tenant context into request
    context = await get_tenant_context(request)
    context.user_id = str(user["_id"])
    context.user_role = UserRole(user.get("role", "user"))
    context.permissions = user.get("permissions", [])

    # Find the API key name
    for key in user.get("api_keys", []):
        if key.get("key_hash") == key_hash:
            context.api_key_name = key.get("name")
            break

    return str(user["_id"])


class TenantAwareService:
    """Base service that automatically applies tenant filtering."""

    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = ObjectId(user_id) if user_id != "development" else None

    def _apply_tenant_filter(self, query: dict) -> dict:
        """Apply tenant filter to any query."""
        if self.user_id:
            query["user_id"] = self.user_id
        return query

    def _ensure_tenant_ownership(self, document: dict) -> dict:
        """Ensure document has tenant ownership."""
        if self.user_id:
            document["user_id"] = self.user_id
        return document

    async def find_one(self, collection_name: str, query: dict) -> Optional[dict]:
        """Find one document with automatic tenant filtering."""
        query = self._apply_tenant_filter(query)
        collection = self.db[collection_name]
        return await collection.find_one(query)

    async def find_many(
        self,
        collection_name: str,
        query: Optional[dict] = None,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[list] = None,
    ) -> list[dict]:
        """Find multiple documents with automatic tenant filtering."""
        query = self._apply_tenant_filter(query or {})
        collection = self.db[collection_name]

        cursor = collection.find(query)
        if sort:
            cursor = cursor.sort(sort)
        cursor = cursor.skip(skip).limit(limit)

        return await cursor.to_list(length=limit)

    async def create(self, collection_name: str, document: dict) -> str:
        """Create a document with automatic tenant assignment."""
        document = self._ensure_tenant_ownership(document)
        collection = self.db[collection_name]
        result = await collection.insert_one(document)
        return str(result.inserted_id)

    async def update(self, collection_name: str, query: dict, update: dict) -> bool:
        """Update documents with automatic tenant filtering."""
        query = self._apply_tenant_filter(query)
        collection = self.db[collection_name]
        result = await collection.update_many(query, update)
        return result.modified_count > 0

    async def delete(self, collection_name: str, query: dict) -> int:
        """Delete documents with automatic tenant filtering."""
        query = self._apply_tenant_filter(query)
        collection = self.db[collection_name]
        result = await collection.delete_many(query)
        return result.deleted_count
