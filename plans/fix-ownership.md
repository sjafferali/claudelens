# Data Ownership Security Fix Plan

## Executive Summary
This plan addresses the critical security vulnerability where uploaded data has no user ownership, resulting in a complete failure of data isolation. The plan includes immediate fixes, data migration, and simplification of the role system by removing the VIEWER role.

## Phase 1: Immediate Security Fixes

### 1.1 Update Ingestion Endpoint to Pass user_id

**File**: `backend/app/api/api_v1/endpoints/ingest.py`

#### Changes Required:

```python
# Line 25-30: Update function signature
@router.post("/batch", response_model=BatchIngestResponse)
async def ingest_batch(
    request: BatchIngestRequest,
    background_tasks: BackgroundTasks,
    db: CommonDeps,
    user_id: AuthDeps,  # Changed from api_key to user_id for clarity
) -> BatchIngestResponse:

# Line 47-53: Pass user_id to IngestService
    # Initialize service with user_id
    ingest_service = IngestService(db, user_id)  # MODIFIED

    try:
        # Process messages with overwrite mode if specified
        stats = await ingest_service.ingest_messages(
            request.messages,
            overwrite_mode=request.overwrite_mode
        )

# Line 74-76: Update single message endpoint similarly
@router.post("/message", response_model=BatchIngestResponse)
async def ingest_single(
    message: MessageIngest,
    db: CommonDeps,
    user_id: AuthDeps  # Changed from api_key
) -> BatchIngestResponse:

    # Line 82: Pass user_id to service
    ingest_service = IngestService(db, user_id)
```

### 1.2 Update IngestService to Accept and Use user_id

**File**: `backend/app/services/ingest.py`

#### Changes Required:

```python
# Line 24-27: Update constructor
class IngestService:
    """Service for ingesting Claude messages."""

    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id  # Store user_id
        self._project_cache: dict[str, ObjectId] = {}
        self._session_cache: dict[str, ObjectId] = {}

# Line 290-319: Update _ensure_project to set user_id
async def _ensure_project(self, project_path: str, project_name: str) -> ObjectId:
    """Ensure project exists, create if needed."""
    # Check cache first - include user_id in cache key
    cache_key = f"{self.user_id}:{project_path}"
    if cache_key in self._project_cache:
        return self._project_cache[cache_key]

    # Check database - filter by user_id
    existing = await self.db.projects.find_one({
        "path": project_path,
        "user_id": ObjectId(self.user_id)  # ADD THIS
    })
    if existing:
        self._project_cache[cache_key] = existing["_id"]
        project_id = existing["_id"]
        assert isinstance(project_id, ObjectId)
        return project_id

    # Create project with user_id
    project_doc = {
        "_id": ObjectId(),
        "user_id": ObjectId(self.user_id),  # ADD THIS
        "name": project_name,
        "path": project_path,
        "createdAt": datetime.now(UTC),
        "updatedAt": datetime.now(UTC),
        "stats": {"message_count": 0, "session_count": 0},
    }

    await self.db.projects.insert_one(project_doc)
    project_id = project_doc["_id"]
    assert isinstance(project_id, ObjectId)
    self._project_cache[cache_key] = project_id

    return project_id

# Line 224-288: Update _ensure_session to set user_id
async def _ensure_session(
    self, session_id: str, first_message: MessageIngest
) -> ObjectId | None:
    """Ensure session exists, create if needed."""
    # Check cache first - include user_id in cache key
    cache_key = f"{self.user_id}:{session_id}"
    if cache_key in self._session_cache:
        return None

    # Check database - filter by user_id
    existing = await self.db.sessions.find_one({
        "sessionId": session_id,
        "user_id": ObjectId(self.user_id)  # ADD THIS
    })
    if existing:
        self._session_cache[cache_key] = existing["_id"]
        return None

    # ... existing project logic ...

    # Create session with user_id
    session_doc = {
        "_id": ObjectId(),
        "user_id": ObjectId(self.user_id),  # ADD THIS
        "sessionId": session_id,
        "projectId": project_id,
        "startedAt": first_message.timestamp,
        "endedAt": first_message.timestamp,
        "messageCount": 0,
        "totalCost": Decimal128("0.0"),
        "createdAt": datetime.now(UTC),
        "updatedAt": datetime.now(UTC),
    }

    await self.db.sessions.insert_one(session_doc)
    session_id_obj = session_doc["_id"]
    assert isinstance(session_id_obj, ObjectId)
    self._session_cache[cache_key] = session_id_obj

    return session_id_obj

# Line 350+: Update _message_to_doc to include user_id
def _message_to_doc(self, message: MessageIngest, session_id: str) -> list[dict]:
    """Convert message to database document(s)."""

    docs = []

    # ... existing logic ...

    # For EVERY document created, add user_id
    main_doc = {
        "_id": ObjectId(),
        "user_id": ObjectId(self.user_id),  # ADD THIS
        "uuid": message.uuid,
        "sessionId": session_id,
        # ... rest of fields
    }

    # Same for tool_use and tool_result documents
    tool_doc = {
        "_id": ObjectId(),
        "user_id": ObjectId(self.user_id),  # ADD THIS
        "uuid": tool_uuid,
        # ... rest of fields
    }
```

### 1.3 Update Session Generation for user_id

**File**: `backend/app/services/ingest.py`

```python
# Line 899-902: Pass user_id when generating summary
# Current code gets user_id from session - ensure it's there
session_service = SessionService(self.db)
# Use the user_id from self instead of from session
await session_service.generate_summary(
    self.user_id,  # Use instance user_id
    str(session["_id"])
)
```

## Phase 2: Data Migration

### 2.1 Create Migration Script

**New File**: `backend/migrations/fix_orphaned_data.py`

```python
"""
Migration script to fix orphaned data without user_id.

Strategy:
1. Find all unique API keys that have been used
2. Map data to users based on creation timestamps and API key usage
3. For unmappable data, assign to a system admin or delete
"""

import asyncio
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrphanedDataMigration:
    def __init__(self, mongodb_url: str, database_name: str):
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client[database_name]

    async def analyze_orphaned_data(self) -> Dict:
        """Analyze the scope of orphaned data."""
        stats = {
            "orphaned_projects": 0,
            "orphaned_sessions": 0,
            "orphaned_messages": 0,
            "users_found": 0,
            "api_keys_found": 0
        }

        # Count orphaned projects
        stats["orphaned_projects"] = await self.db.projects.count_documents({
            "user_id": {"$exists": False}
        })

        # Count orphaned sessions
        stats["orphaned_sessions"] = await self.db.sessions.count_documents({
            "user_id": {"$exists": False}
        })

        # Count orphaned messages
        stats["orphaned_messages"] = await self.db.messages.count_documents({
            "user_id": {"$exists": False}
        })

        # Count users
        stats["users_found"] = await self.db.users.count_documents({})

        # Count API keys
        users_with_keys = await self.db.users.count_documents({
            "api_keys": {"$exists": True, "$ne": []}
        })
        stats["api_keys_found"] = users_with_keys

        return stats

    asyncalistic_assignment(self) -> Dict[str, ObjectId]:
        """
        Try to map orphaned data to users based on:
        1. If only one user exists, assign all data to them
        2. If multiple users, use creation timestamps and activity patterns
        3. Fall back to admin user
        """
        mapping = {}

        # Get all users
        users = await self.db.users.find({}).to_list(None)

        if len(users) == 0:
            raise Exception("No users found! Cannot proceed with migration.")

        if len(users) == 1:
            # Simple case: only one user, assign everything to them
            user = users[0]
            logger.info(f"Only one user found ({user['username']}), assigning all orphaned data to them")

            # Get all orphaned projects
            orphaned_projects = await self.db.projects.find({
                "user_id": {"$exists": False}
            }).to_list(None)

            for project in orphaned_projects:
                mapping[str(project["_id"])] = user["_id"]

            return mapping, user["_id"]

        # Multiple users - need more complex logic
        # For now, find the admin user or the first user
        admin_user = None
        for user in users:
            if user.get("role") == "admin":
                admin_user = user
                break

        if not admin_user:
            admin_user = users[0]  # Fallback to first user

        logger.info(f"Multiple users found, assigning orphaned data to {admin_user['username']}")

        # Map all orphaned projects to admin
        orphaned_projects = await self.db.projects.find({
            "user_id": {"$exists": False}
        }).to_list(None)

        for project in orphaned_projects:
            mapping[str(project["_id"])] = admin_user["_id"]

        return mapping, admin_user["_id"]

    async def execute_migration(self, dry_run: bool = True):
        """Execute the migration."""
        logger.info(f"Starting migration (dry_run={dry_run})")

        # Analyze current state
        stats = await self.analyze_orphaned_data()
        logger.info(f"Current state: {stats}")

        if stats["orphaned_projects"] == 0 and stats["orphaned_sessions"] == 0 and stats["orphaned_messages"] == 0:
            logger.info("No orphaned data found, migration not needed")
            return

        # Get mapping
        project_mapping, default_user_id = await self.realistic_assignment()

        if dry_run:
            logger.info("DRY RUN - No changes will be made")
            logger.info(f"Would assign {len(project_mapping)} projects to users")
            logger.info(f"Default user for unmapped data: {default_user_id}")
            return

        # Update projects
        for project_id_str, user_id in project_mapping.items():
            result = await self.db.projects.update_one(
                {"_id": ObjectId(project_id_str)},
                {"$set": {"user_id": user_id}}
            )
            if result.modified_count > 0:
                logger.info(f"Updated project {project_id_str} with user_id {user_id}")

        # Update sessions - match by projectId
        for project_id_str, user_id in project_mapping.items():
            result = await self.db.sessions.update_many(
                {
                    "projectId": ObjectId(project_id_str),
                    "user_id": {"$exists": False}
                },
                {"$set": {"user_id": user_id}}
            )
            logger.info(f"Updated {result.modified_count} sessions for project {project_id_str}")

        # Update orphaned sessions without projects
        result = await self.db.sessions.update_many(
            {"user_id": {"$exists": False}},
            {"$set": {"user_id": default_user_id}}
        )
        logger.info(f"Updated {result.modified_count} orphaned sessions with default user")

        # Update messages - match by sessionId
        sessions = await self.db.sessions.find({}, {"sessionId": 1, "user_id": 1}).to_list(None)
        session_user_map = {s["sessionId"]: s["user_id"] for s in sessions}

        for session_id, user_id in session_user_map.items():
            result = await self.db.messages.update_many(
                {
                    "sessionId": session_id,
                    "user_id": {"$exists": False}
                },
                {"$set": {"user_id": user_id}}
            )
            logger.info(f"Updated {result.modified_count} messages for session {session_id}")

        # Update any remaining orphaned messages
        result = await self.db.messages.update_many(
            {"user_id": {"$exists": False}},
            {"$set": {"user_id": default_user_id}}
        )
        logger.info(f"Updated {result.modified_count} fully orphaned messages")

        # Final verification
        final_stats = await self.analyze_orphaned_data()
        logger.info(f"Migration complete. Final state: {final_stats}")

        if final_stats["orphaned_projects"] > 0 or final_stats["orphaned_sessions"] > 0 or final_stats["orphaned_messages"] > 0:
            logger.warning("Some orphaned data still remains!")
        else:
            logger.info("All orphaned data has been assigned to users")

async def main():
    # Configuration
    MONGODB_URL = "mongodb://localhost:27017/claudelens"  # Update as needed
    DATABASE_NAME = "claudelens"
    DRY_RUN = True  # Set to False to actually execute

    migration = OrphanedDataMigration(MONGODB_URL, DATABASE_NAME)
    await migration.execute_migration(dry_run=DRY_RUN)

if __name__ == "__main__":
    asyncio.run(main())
```

### 2.2 Create Verification Script

**New File**: `backend/scripts/verify_ownership.py`

```python
"""Verify that all data has proper user ownership."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_ownership(mongodb_url: str, database_name: str):
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]

    issues = []

    # Check projects
    orphaned = await db.projects.count_documents({"user_id": {"$exists": False}})
    if orphaned > 0:
        issues.append(f"Found {orphaned} projects without user_id")

    null_user = await db.projects.count_documents({"user_id": None})
    if null_user > 0:
        issues.append(f"Found {null_user} projects with null user_id")

    # Check sessions
    orphaned = await db.sessions.count_documents({"user_id": {"$exists": False}})
    if orphaned > 0:
        issues.append(f"Found {orphaned} sessions without user_id")

    null_user = await db.sessions.count_documents({"user_id": None})
    if null_user > 0:
        issues.append(f"Found {null_user} sessions with null user_id")

    # Check messages
    orphaned = await db.messages.count_documents({"user_id": {"$exists": False}})
    if orphaned > 0:
        issues.append(f"Found {orphaned} messages without user_id")

    null_user = await db.messages.count_documents({"user_id": None})
    if null_user > 0:
        issues.append(f"Found {null_user} messages with null user_id")

    # Check data isolation
    users = await db.users.find({}).to_list(None)
    for user in users:
        user_id = user["_id"]

        # Count user's data
        projects = await db.projects.count_documents({"user_id": user_id})
        sessions = await db.sessions.count_documents({"user_id": user_id})
        messages = await db.messages.count_documents({"user_id": user_id})

        logger.info(f"User {user['username']}: {projects} projects, {sessions} sessions, {messages} messages")

    if issues:
        logger.error("VERIFICATION FAILED:")
        for issue in issues:
            logger.error(f"  - {issue}")
        return False
    else:
        logger.info("✅ All data has proper user ownership")
        return True

if __name__ == "__main__":
    asyncio.run(verify_ownership("mongodb://localhost:27017/claudelens", "claudelens"))
```

## Phase 3: Remove VIEWER Role

### 3.1 Update User Model

**File**: `backend/app/models/user.py`

```python
# Line 11-17: Remove VIEWER from enum
class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    USER = "user"
    # REMOVED: VIEWER = "viewer"
```

### 3.2 Update OIDC Settings Default Role

**File**: `backend/app/services/oidc_service.py`

```python
# Line 513: Change default role if it was viewer
"role": UserRole(self._settings.default_role if self._settings.default_role != "viewer" else "user"),
```

### 3.3 Create Migration for Existing Viewer Users

**New File**: `backend/migrations/remove_viewer_role.py`

```python
"""Migrate existing viewer users to user role."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_viewer_users(mongodb_url: str, database_name: str):
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]

    # Count viewers
    viewer_count = await db.users.count_documents({"role": "viewer"})
    logger.info(f"Found {viewer_count} users with VIEWER role")

    if viewer_count == 0:
        logger.info("No VIEWER users found, migration not needed")
        return

    # Update all viewers to users
    result = await db.users.update_many(
        {"role": "viewer"},
        {"$set": {"role": "user"}}
    )

    logger.info(f"Updated {result.modified_count} users from VIEWER to USER role")

    # Update OIDC settings if default role is viewer
    oidc_settings = await db.oidc_settings.find_one({})
    if oidc_settings and oidc_settings.get("default_role") == "viewer":
        await db.oidc_settings.update_one(
            {"_id": oidc_settings["_id"]},
            {"$set": {"default_role": "user"}}
        )
        logger.info("Updated OIDC default role from VIEWER to USER")

if __name__ == "__main__":
    asyncio.run(migrate_viewer_users("mongodb://localhost:27017/claudelens", "claudelens"))
```

### 3.4 Update Frontend Role References

**File**: `frontend/src/types/user.ts`

```typescript
export enum UserRole {
  Admin = 'admin',
  User = 'user',
  // REMOVED: Viewer = 'viewer',
}
```

**Files to check for viewer references**:
- `frontend/src/components/admin/UserManagement.tsx`
- `frontend/src/pages/AdminDashboard.tsx`
- Any other files with role checks

## Phase 4: Testing Plan

### 4.1 Unit Tests

**New File**: `backend/tests/test_data_ownership.py`

```python
"""Test data ownership and isolation."""

import pytest
from bson import ObjectId
from datetime import datetime

from app.services.ingest import IngestService
from app.schemas.ingest import MessageIngest

@pytest.mark.asyncio
async def test_ingestion_sets_user_id(db, test_user):
    """Test that ingestion properly sets user_id on all created documents."""

    # Create service with user_id
    service = IngestService(db, str(test_user.id))

    # Create test message
    message = MessageIngest(
        uuid="test-uuid",
        sessionId="test-session",
        type="user",
        timestamp=datetime.utcnow(),
        message={"content": "test"},
        cwd="/test/project"
    )

    # Ingest message
    stats = await service.ingest_messages([message])

    # Verify project has user_id
    project = await db.projects.find_one({"path": "/test/project"})
    assert project is not None
    assert project["user_id"] == test_user.id

    # Verify session has user_id
    session = await db.sessions.find_one({"sessionId": "test-session"})
    assert session is not None
    assert session["user_id"] == test_user.id

    # Verify message has user_id
    msg = await db.messages.find_one({"uuid": "test-uuid"})
    assert msg is not None
    assert msg["user_id"] == test_user.id

@pytest.mark.asyncio
async def test_data_isolation_between_users(db, test_user, test_user2):
    """Test that users cannot see each other's data."""

    # User 1 ingests data
    service1 = IngestService(db, str(test_user.id))
    message1 = MessageIngest(
        uuid="user1-msg",
        sessionId="user1-session",
        type="user",
        timestamp=datetime.utcnow(),
        message={"content": "user1 data"},
        cwd="/user1/project"
    )
    await service1.ingest_messages([message1])

    # User 2 ingests data
    service2 = IngestService(db, str(test_user2.id))
    message2 = MessageIngest(
        uuid="user2-msg",
        sessionId="user2-session",
        type="user",
        timestamp=datetime.utcnow(),
        message={"content": "user2 data"},
        cwd="/user2/project"
    )
    await service2.ingest_messages([message2])

    # User 1 should only see their project
    user1_projects = await db.projects.find({"user_id": test_user.id}).to_list(None)
    assert len(user1_projects) == 1
    assert user1_projects[0]["path"] == "/user1/project"

    # User 2 should only see their project
    user2_projects = await db.projects.find({"user_id": test_user2.id}).to_list(None)
    assert len(user2_projects) == 1
    assert user2_projects[0]["path"] == "/user2/project"

    # Cross-check: User 1 cannot see User 2's data
    wrong_access = await db.projects.find({"user_id": test_user.id, "path": "/user2/project"}).to_list(None)
    assert len(wrong_access) == 0

@pytest.mark.asyncio
async def test_no_viewer_role_allowed(db):
    """Test that viewer role is no longer accepted."""
    from app.models.user import UserRole

    # Should not have VIEWER in enum
    assert not hasattr(UserRole, 'VIEWER')

    # Should only have ADMIN and USER
    assert UserRole.ADMIN == "admin"
    assert UserRole.USER == "user"
```

### 4.2 Integration Tests

**New File**: `backend/tests/test_api_data_isolation.py`

```python
"""Test API-level data isolation."""

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_api_data_isolation(client: AsyncClient, test_api_key_1, test_api_key_2):
    """Test that API endpoints properly isolate data between users."""

    # User 1 uploads data
    response1 = await client.post(
        "/api/v1/ingest/batch",
        headers={"X-API-Key": test_api_key_1},
        json={
            "messages": [{
                "uuid": "user1-msg",
                "sessionId": "user1-session",
                "type": "user",
                "timestamp": "2024-01-01T00:00:00Z",
                "message": {"content": "user1 data"},
                "cwd": "/user1/project"
            }]
        }
    )
    assert response1.status_code == 200

    # User 2 uploads data
    response2 = await client.post(
        "/api/v1/ingest/batch",
        headers={"X-API-Key": test_api_key_2},
        json={
            "messages": [{
                "uuid": "user2-msg",
                "sessionId": "user2-session",
                "type": "user",
                "timestamp": "2024-01-01T00:00:00Z",
                "message": {"content": "user2 data"},
                "cwd": "/user2/project"
            }]
        }
    )
    assert response2.status_code == 200

    # User 1 lists projects - should only see their own
    projects1 = await client.get(
        "/api/v1/projects/",
        headers={"X-API-Key": test_api_key_1}
    )
    assert projects1.status_code == 200
    data1 = projects1.json()
    assert data1["total"] == 1
    assert data1["items"][0]["path"] == "/user1/project"

    # User 2 lists projects - should only see their own
    projects2 = await client.get(
        "/api/v1/projects/",
        headers={"X-API-Key": test_api_key_2}
    )
    assert projects2.status_code == 200
    data2 = projects2.json()
    assert data2["total"] == 1
    assert data2["items"][0]["path"] == "/user2/project"

    # User 1 cannot access User 2's project
    # Get User 2's project ID
    user2_project_id = data2["items"][0]["_id"]

    # Try to access it as User 1
    forbidden = await client.get(
        f"/api/v1/projects/{user2_project_id}",
        headers={"X-API-Key": test_api_key_1}
    )
    assert forbidden.status_code == 404  # Should not find it due to user_id filtering
```

## Phase 5: Implementation Timeline

### Day 1: Critical Security Fix
1. **Morning**:
   - Implement Phase 1.1 and 1.2 (update ingest endpoints and service)
   - Create and test migration script

2. **Afternoon**:
   - Deploy fix to staging
   - Run migration in dry-run mode
   - Test data isolation

### Day 2: Data Migration
1. **Morning**:
   - Backup production database
   - Run migration script on production (with monitoring)
   - Verify ownership assignment

2. **Afternoon**:
   - Monitor for any issues
   - Run verification scripts
   - Address any edge cases

### Day 3: Role System Cleanup
1. **Morning**:
   - Remove VIEWER role from codebase
   - Migrate existing viewer users to USER role
   - Update frontend

2. **Afternoon**:
   - Deploy role changes
   - Update documentation
   - Communicate changes to users

## Phase 6: Communication Plan

### 6.1 Security Advisory

```markdown
# Security Update: Data Access Control Enhancement

We've identified and fixed an issue with data access control in ClaudeLens.

## What Happened
- Uploaded data was not properly associated with user accounts
- This could potentially allow unauthorized data access

## What We've Done
- Implemented proper data ownership assignment
- Migrated all existing data to appropriate owners
- Enhanced access control verification
- Simplified the role system for clarity

## Impact on You
- Your data is now properly isolated and secure
- The VIEWER role has been removed (all viewers are now USERS)
- No action required on your part

## Timeline
- Fix deployed: [DATE]
- Migration completed: [DATE]
- Verification completed: [DATE]

We take security seriously and apologize for any concern this may have caused.
```

### 6.2 Technical Documentation Update

Update README and API documentation to reflect:
- Proper data isolation is enforced
- Only two roles exist: ADMIN and USER
- Each user only sees their own data
- Admins have system administration capabilities, not data access

## Phase 7: Monitoring and Verification

### 7.1 Add Database Indexes

```javascript
// Add indexes to improve performance with user_id filtering
db.projects.createIndex({ "user_id": 1, "path": 1 })
db.sessions.createIndex({ "user_id": 1, "sessionId": 1 })
db.messages.createIndex({ "user_id": 1, "sessionId": 1 })
```

### 7.2 Create Monitoring Dashboard

Add metrics to track:
- Number of orphaned documents (should be 0)
- Data distribution per user
- Failed access attempts (404s on resources)
- API key usage patterns

### 7.3 Regular Audits

Create a scheduled job to verify:
- All new data has user_id
- No cross-user data access
- Role assignments are correct

## Rollback Plan

If issues arise:

1. **Immediate Rollback**:
   - Revert code changes
   - Restore from database backup

2. **Partial Rollback**:
   - Keep security fixes
   - Revert only role changes if needed

3. **Data Recovery**:
   - Migration script can be modified to reverse changes
   - All changes are logged for audit trail

## Success Criteria

The implementation is successful when:
1. ✅ All data has user_id assigned
2. ✅ Users can only see their own data
3. ✅ No viewer role exists in the system
4. ✅ All tests pass
5. ✅ No orphaned data in production
6. ✅ Performance is not degraded
7. ✅ Zero security incidents related to data access

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Migration fails | Low | High | Backup, dry-run, rollback plan |
| Performance degradation | Medium | Medium | Indexes, monitoring, optimization |
| User confusion | Low | Low | Clear communication, documentation |
| Data loss | Very Low | Critical | Multiple backups, verification |

## Conclusion

This plan addresses the critical security vulnerability while simplifying the system. The removal of the VIEWER role reduces complexity and makes the security model clearer: users see only their own data, period.

Estimated total implementation time: 3 days
Estimated downtime: None (rolling updates)
Risk level: Medium (due to data migration)
Priority: CRITICAL - Implement immediately
