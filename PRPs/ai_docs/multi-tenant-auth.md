# Multi-Tenant Authentication Patterns Documentation

## API Key Management

### Secure API Key Generation and Storage

```python
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Tuple, Optional

class APIKeyManager:
    """Manages API key generation, validation, and rotation"""

    KEY_PREFIX = "cl_"  # ClaudeLens prefix for keys
    KEY_LENGTH = 32

    @staticmethod
    def generate_api_key() -> Tuple[str, str]:
        """
        Generate a new API key and its hash.

        Returns:
            Tuple of (api_key, key_hash)
            - api_key: The actual key to give to the user (only shown once)
            - key_hash: The hash to store in the database
        """
        # Generate cryptographically secure random key
        random_bytes = secrets.token_urlsafe(APIKeyManager.KEY_LENGTH)
        api_key = f"{APIKeyManager.KEY_PREFIX}{random_bytes}"

        # Create SHA256 hash for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        return api_key, key_hash

    @staticmethod
    def verify_api_key(provided_key: str, stored_hash: str) -> bool:
        """
        Verify an API key against its stored hash.

        Args:
            provided_key: The API key provided by the user
            stored_hash: The hash stored in the database

        Returns:
            True if the key is valid, False otherwise
        """
        provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
        # Use constant-time comparison to prevent timing attacks
        import hmac
        return hmac.compare_digest(provided_hash, stored_hash)
```

### Database Schema for API Keys

```python
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta

class APIKeyRepository:
    """Repository for API key database operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.api_keys

        # Ensure indexes for performance
        self.collection.create_index("key_hash", unique=True)
        self.collection.create_index("user_id")
        self.collection.create_index("expires_at")

    async def create_api_key(self, user_id: str, name: str, expires_in_days: int = 365):
        """Create a new API key for a user"""
        api_key, key_hash = APIKeyManager.generate_api_key()

        document = {
            "user_id": user_id,
            "name": name,
            "key_hash": key_hash,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=expires_in_days),
            "last_used": None,
            "active": True,
            "permissions": [],  # Can be extended for fine-grained permissions
            "usage_count": 0,
            "rate_limit": {
                "requests_per_minute": 60,
                "requests_per_hour": 1000
            }
        }

        await self.collection.insert_one(document)
        return api_key  # Return the actual key (only shown once)

    async def validate_and_update_usage(self, key_hash: str):
        """Validate API key and update usage statistics"""
        key_doc = await self.collection.find_one_and_update(
            {
                "key_hash": key_hash,
                "active": True,
                "expires_at": {"$gt": datetime.utcnow()}
            },
            {
                "$set": {"last_used": datetime.utcnow()},
                "$inc": {"usage_count": 1}
            }
        )

        if not key_doc:
            return None

        return key_doc["user_id"]
```

## Tenant Isolation Middleware

### FastAPI Middleware Implementation

```python
from fastapi import Request, HTTPException, Depends
from fastapi.security import APIKeyHeader
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TenantContext:
    """Stores tenant context for the current request"""

    def __init__(self):
        self.user_id: Optional[str] = None
        self.user_role: Optional[str] = None
        self.api_key_name: Optional[str] = None
        self.permissions: list = []

# Create a request-scoped tenant context
async def get_tenant_context(request: Request) -> TenantContext:
    """Get tenant context from request state"""
    if not hasattr(request.state, "tenant_context"):
        request.state.tenant_context = TenantContext()
    return request.state.tenant_context

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_tenant(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> str:
    """
    Verify tenant from API key and inject into request context.

    Returns:
        user_id: The authenticated user's ID

    Raises:
        HTTPException: If authentication fails
    """
    # Allow localhost without authentication (for development)
    if request.client and request.client.host in ["127.0.0.1", "localhost"]:
        # Create a default development user context
        context = await get_tenant_context(request)
        context.user_id = "development"
        context.user_role = "admin"
        return "development"

    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    # Hash the provided key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Look up the key in the database
    api_key_repo = APIKeyRepository(db)
    user_id = await api_key_repo.validate_and_update_usage(key_hash)

    if not user_id:
        logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
        raise HTTPException(status_code=401, detail="Invalid or expired API key")

    # Get user details
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Inject tenant context into request
    context = await get_tenant_context(request)
    context.user_id = str(user_id)
    context.user_role = user.get("role", "user")
    context.permissions = user.get("permissions", [])

    return str(user_id)

# Dependency for routes that require authentication
AuthRequired = Depends(verify_tenant)

# Dependency for admin-only routes
async def admin_required(
    user_id: str = AuthRequired,
    request: Request = None
) -> str:
    """Require admin role for access"""
    context = await get_tenant_context(request)
    if context.user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id
```

## Service Layer Tenant Filtering

### Base Service with Automatic Tenant Filtering

```python
from abc import ABC, abstractmethod
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Optional, List, Dict, Any

class TenantAwareService(ABC):
    """Base service that automatically applies tenant filtering"""

    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = ObjectId(user_id) if user_id != "development" else None

    def _apply_tenant_filter(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Apply tenant filter to any query"""
        if self.user_id:
            query["user_id"] = self.user_id
        return query

    def _ensure_tenant_ownership(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure document has tenant ownership"""
        if self.user_id:
            document["user_id"] = self.user_id
        return document

    @abstractmethod
    def get_collection_name(self) -> str:
        """Return the collection name for this service"""
        pass

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document with automatic tenant filtering"""
        query = self._apply_tenant_filter(query)
        collection = self.db[self.get_collection_name()]
        return await collection.find_one(query)

    async def find_many(
        self,
        query: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        sort: List[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Find multiple documents with automatic tenant filtering"""
        query = self._apply_tenant_filter(query or {})
        collection = self.db[self.get_collection_name()]

        cursor = collection.find(query)
        if sort:
            cursor = cursor.sort(sort)
        cursor = cursor.skip(skip).limit(limit)

        return await cursor.to_list(length=limit)

    async def create(self, document: Dict[str, Any]) -> str:
        """Create a document with automatic tenant assignment"""
        document = self._ensure_tenant_ownership(document)
        collection = self.db[self.get_collection_name()]
        result = await collection.insert_one(document)
        return str(result.inserted_id)

    async def update(self, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        """Update documents with automatic tenant filtering"""
        query = self._apply_tenant_filter(query)
        collection = self.db[self.get_collection_name()]
        result = await collection.update_many(query, update)
        return result.modified_count > 0

    async def delete(self, query: Dict[str, Any]) -> int:
        """Delete documents with automatic tenant filtering"""
        query = self._apply_tenant_filter(query)
        collection = self.db[self.get_collection_name()]
        result = await collection.delete_many(query)
        return result.deleted_count
```

### Example Implementation for Sessions

```python
class SessionService(TenantAwareService):
    """Session service with automatic tenant isolation"""

    def get_collection_name(self) -> str:
        return "sessions"

    async def get_user_sessions(
        self,
        project_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get sessions for the current user"""
        query = {}
        if project_id:
            query["projectId"] = ObjectId(project_id)

        # Tenant filter is automatically applied
        return await self.find_many(query, skip, limit, [("startedAt", -1)])

    async def get_session_with_messages(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session with its messages (tenant-safe)"""
        # First get the session (with tenant check)
        session = await self.find_one({"_id": ObjectId(session_id)})
        if not session:
            return None

        # Get messages for this session (also tenant-filtered)
        messages_service = MessageService(self.db, str(self.user_id))
        messages = await messages_service.find_many(
            {"sessionId": session["sessionId"]},
            sort=[("timestamp", 1)]
        )

        session["messages"] = messages
        return session
```

## Storage Metrics Calculation

### Efficient Disk Usage Calculation

```python
class StorageMetricsService:
    """Calculate and cache storage metrics per tenant"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def calculate_user_metrics(self, user_id: str) -> Dict[str, Any]:
        """Calculate comprehensive storage metrics for a user"""
        user_oid = ObjectId(user_id)

        # Parallel aggregation pipelines for different collections
        tasks = [
            self._calculate_collection_metrics("sessions", user_oid),
            self._calculate_collection_metrics("messages", user_oid),
            self._calculate_collection_metrics("projects", user_oid),
        ]

        results = await asyncio.gather(*tasks)

        # Combine results
        total_size = sum(r["total_size"] for r in results)
        total_count = sum(r["document_count"] for r in results)

        return {
            "user_id": user_id,
            "sessions": results[0],
            "messages": results[1],
            "projects": results[2],
            "total_disk_usage": total_size,
            "total_document_count": total_count,
            "breakdown": {
                "sessions_bytes": results[0]["total_size"],
                "messages_bytes": results[1]["total_size"],
                "projects_bytes": results[2]["total_size"]
            }
        }

    async def _calculate_collection_metrics(
        self,
        collection_name: str,
        user_id: ObjectId
    ) -> Dict[str, Any]:
        """Calculate metrics for a specific collection"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": None,
                    "total_size": {"$sum": {"$bsonSize": "$$ROOT"}},
                    "document_count": {"$sum": 1},
                    "avg_size": {"$avg": {"$bsonSize": "$$ROOT"}},
                    "max_size": {"$max": {"$bsonSize": "$$ROOT"}}
                }
            }
        ]

        result = await self.db[collection_name].aggregate(pipeline).to_list(1)

        if result:
            return result[0]
        return {
            "total_size": 0,
            "document_count": 0,
            "avg_size": 0,
            "max_size": 0
        }

    async def update_user_storage_cache(self, user_id: str):
        """Update cached storage metrics for a user"""
        metrics = await self.calculate_user_metrics(user_id)

        # Update user document with denormalized metrics
        await self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "project_count": metrics["projects"]["document_count"],
                    "session_count": metrics["sessions"]["document_count"],
                    "message_count": metrics["messages"]["document_count"],
                    "total_disk_usage": metrics["total_disk_usage"],
                    "storage_updated_at": datetime.utcnow()
                }
            }
        )

        return metrics
```

## Admin Dashboard API Patterns

### Admin Statistics Endpoint

```python
from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any

router = APIRouter()

@router.get("/admin/stats")
async def get_admin_statistics(
    db: AsyncIOMotorDatabase = Depends(get_database),
    _: str = Depends(admin_required)
) -> Dict[str, Any]:
    """Get system-wide statistics for admin dashboard"""

    # Aggregate user statistics
    user_stats_pipeline = [
        {
            "$group": {
                "_id": "$role",
                "count": {"$sum": 1},
                "total_storage": {"$sum": "$total_disk_usage"},
                "avg_storage": {"$avg": "$total_disk_usage"}
            }
        }
    ]

    # Get top users by storage
    top_users_pipeline = [
        {"$sort": {"total_disk_usage": -1}},
        {"$limit": 10},
        {
            "$project": {
                "username": 1,
                "email": 1,
                "total_disk_usage": 1,
                "session_count": 1,
                "message_count": 1
            }
        }
    ]

    # Run aggregations in parallel
    user_stats_task = db.users.aggregate(user_stats_pipeline).to_list(None)
    top_users_task = db.users.aggregate(top_users_pipeline).to_list(None)
    total_users_task = db.users.count_documents({})

    user_stats, top_users, total_users = await asyncio.gather(
        user_stats_task, top_users_task, total_users_task
    )

    return {
        "total_users": total_users,
        "users_by_role": user_stats,
        "top_users_by_storage": top_users,
        "system_totals": {
            "total_storage_bytes": sum(u["total_storage"] for u in user_stats),
            "total_sessions": await db.sessions.count_documents({}),
            "total_messages": await db.messages.count_documents({})
        }
    }

@router.delete("/admin/users/{user_id}/cascade")
async def delete_user_cascade(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    _: str = Depends(admin_required)
) -> Dict[str, Any]:
    """Delete a user and all their data (cascade delete)"""

    user_oid = ObjectId(user_id)

    # Delete in order of dependencies
    delete_tasks = [
        db.messages.delete_many({"user_id": user_oid}),
        db.sessions.delete_many({"user_id": user_oid}),
        db.projects.delete_many({"user_id": user_oid}),
        db.api_keys.delete_many({"user_id": user_oid})
    ]

    results = await asyncio.gather(*delete_tasks)

    # Finally delete the user
    await db.users.delete_one({"_id": user_oid})

    return {
        "deleted": {
            "messages": results[0].deleted_count,
            "sessions": results[1].deleted_count,
            "projects": results[2].deleted_count,
            "api_keys": results[3].deleted_count,
            "user": 1
        }
    }
```

## Performance Optimization

### Indexes for Multi-Tenant Queries

```javascript
// MongoDB index creation script
// Run these in MongoDB shell or during application startup

// User collection indexes
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "username": 1 }, { unique: true })
db.users.createIndex({ "api_keys.key_hash": 1 })
db.users.createIndex({ "total_disk_usage": -1 })  // For sorting by storage

// API keys collection (if separate)
db.api_keys.createIndex({ "key_hash": 1 }, { unique: true })
db.api_keys.createIndex({ "user_id": 1, "active": 1 })
db.api_keys.createIndex({ "expires_at": 1 })

// Tenant-aware indexes for all collections
db.sessions.createIndex({ "user_id": 1, "startedAt": -1 })
db.messages.createIndex({ "user_id": 1, "timestamp": -1 })
db.projects.createIndex({ "user_id": 1, "createdAt": -1 })

// Compound indexes for common queries
db.sessions.createIndex({ "user_id": 1, "projectId": 1, "startedAt": -1 })
db.messages.createIndex({ "user_id": 1, "sessionId": 1, "timestamp": 1 })

// Text search with tenant filtering
db.sessions.createIndex({ "user_id": 1, "summary": "text" })
db.messages.createIndex({ "user_id": 1, "content": "text" })
```

## Security Best Practices

### API Key Security Checklist

1. **Never store plain text API keys** - Always hash with SHA256 or better
2. **Use constant-time comparison** - Prevent timing attacks with hmac.compare_digest
3. **Implement key rotation** - Allow users to rotate keys regularly
4. **Set expiration dates** - API keys should expire after a reasonable period
5. **Rate limiting per key** - Prevent abuse with per-key rate limits
6. **Audit logging** - Log all API key usage for security monitoring
7. **Secure transmission** - Always require HTTPS for API key transmission
8. **Key scope/permissions** - Implement granular permissions per key
9. **Revocation mechanism** - Ability to instantly revoke compromised keys
10. **Separate admin keys** - Admin operations should use separate, more secure keys

### Tenant Isolation Verification

```python
# Test to verify tenant isolation
async def test_tenant_isolation():
    """Verify that users cannot access each other's data"""

    # Create two test users
    user1_id = await create_test_user("user1")
    user2_id = await create_test_user("user2")

    # Create data for user1
    service1 = SessionService(db, user1_id)
    session1_id = await service1.create({"name": "User1 Session"})

    # Try to access user1's data as user2
    service2 = SessionService(db, user2_id)
    stolen_session = await service2.find_one({"_id": ObjectId(session1_id)})

    # This should return None due to tenant filtering
    assert stolen_session is None, "Tenant isolation breach detected!"

    # Verify user2 cannot update user1's data
    updated = await service2.update(
        {"_id": ObjectId(session1_id)},
        {"$set": {"name": "Hacked!"}}
    )
    assert not updated, "User was able to modify another user's data!"

    print("✅ Tenant isolation verified successfully")
```
