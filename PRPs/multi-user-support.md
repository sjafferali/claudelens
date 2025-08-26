name: "Multi-User Support with Admin Management"
description: |
  Complete implementation of multi-tenant user system with API key authentication,
  resource isolation, and admin management interface for ClaudeLens

---

## Goal

**Feature Goal**: Implement complete multi-user support where each user is identified by an API key, can only access their own resources, and admins can manage all users and their data

**Deliverable**:
- Backend: User management models, API key authentication middleware, tenant-isolated services, admin API endpoints
- Frontend: Admin dashboard with user management interface, statistics visualization, and bulk operations

**Success Definition**:
- Users can only access resources they own via API key authentication
- Admin users can view/manage all users and their data
- System tracks disk usage and resource counts per user
- All existing endpoints are tenant-aware

## User Persona

**Target User**:
1. **Regular Users**: API consumers who upload and manage their Claude conversation data
2. **Admin Users**: System administrators who manage users, monitor usage, and maintain the system

**Use Case**:
- Regular users authenticate via API key to upload/access their conversation data
- Admins access management interface to monitor usage, change roles, delete users

**User Journey**:
1. Regular User: Receives API key → Uses key in requests → Accesses only their data
2. Admin: Logs into admin dashboard → Views user statistics → Manages users → Monitors system

**Pain Points Addressed**:
- Currently no user isolation - anyone can access all data
- No way to track usage per user
- No administrative controls for user management

## Why

- **Business value**: Enable multi-tenant SaaS deployment of ClaudeLens
- **Security**: Proper data isolation ensures users cannot access each other's data
- **Scalability**: Track and limit resource usage per user
- **Compliance**: User data segregation for privacy regulations

## What

### Backend Requirements
- User model with API key management
- Tenant-aware middleware for all endpoints
- Admin endpoints for user management
- Storage metrics calculation per user

### Frontend Requirements
- Admin dashboard accessible at `/admin`
- User management table with sorting/filtering
- Usage statistics visualization
- Bulk operations interface

### Success Criteria

- [ ] API key authentication working for all endpoints
- [ ] Users can only access their own resources
- [ ] Admin dashboard displays all users with statistics
- [ ] Admins can create/update/delete users
- [ ] System tracks disk usage and resource counts
- [ ] All models have user_id field for tenant isolation

## All Needed Context

### Context Completeness Check

_Before writing this PRP, validate: "If someone knew nothing about this codebase, would they have everything needed to implement this successfully?"_

### Documentation & References

```yaml
# Authentication Patterns
- url: https://fastapi.tiangolo.com/tutorial/security/api-keys/
  why: FastAPI API key authentication patterns
  critical: Use Header() for API key extraction, Depends() for injection

- url: https://www.mongodb.com/docs/atlas/build-multi-tenant-arch/
  why: MongoDB multi-tenant architecture patterns
  critical: Always include tenant_id in queries, use compound indexes

- url: https://ui.shadcn.com/docs/components/data-table
  why: Data table implementation for admin dashboard
  critical: Use TanStack Table for server-side operations

# Existing Patterns in Codebase
- file: backend/app/core/security.py
  why: Existing API key verification pattern
  pattern: verify_api_key function structure
  gotcha: Currently uses single API key from settings

- file: backend/app/api/dependencies.py
  why: Dependency injection patterns
  pattern: verify_api_key_header and CommonDeps
  gotcha: Allows localhost without auth - preserve this

- file: backend/app/models/session.py
  why: Model structure pattern
  pattern: Pydantic BaseModel with MongoDB ObjectId handling
  gotcha: Use Field(alias="_id") for MongoDB _id mapping

- file: backend/app/services/session.py
  why: Service layer pattern
  pattern: Service class with db injection, async methods
  gotcha: Convert Decimal128 to float for costs

- file: frontend/src/pages/Settings.tsx
  why: Admin UI pattern location
  pattern: Page component structure, routing integration
  gotcha: Use existing UI components from components/ui/

# MongoDB Aggregation Documentation
- url: https://www.mongodb.com/docs/manual/reference/operator/aggregation/bsonSize/
  why: Calculate document sizes for disk usage
  critical: $bsonSize available in MongoDB 4.0+

- docfile: PRPs/ai_docs/multi-tenant-auth.md
  why: Comprehensive multi-tenant authentication patterns
  section: API Key Management
```

### Current Codebase tree

```bash
backend/
├── app/
│   ├── api/
│   │   ├── api_v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── sessions.py
│   │   │   │   ├── messages.py
│   │   │   │   ├── projects.py
│   │   │   │   └── ...
│   │   │   └── api.py
│   │   └── dependencies.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── exceptions.py
│   ├── models/
│   │   ├── session.py
│   │   ├── message.py
│   │   ├── project.py
│   │   └── ...
│   ├── services/
│   │   ├── session.py
│   │   ├── message.py
│   │   ├── project.py
│   │   └── ...
│   └── main.py

frontend/
├── src/
│   ├── components/
│   │   ├── ui/
│   │   └── layout/
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Sessions.tsx
│   │   ├── Settings.tsx
│   │   └── ...
│   └── App.tsx
```

### Desired Codebase tree with files to be added

```bash
backend/
├── app/
│   ├── api/
│   │   ├── api_v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── users.py          # NEW: User management endpoints
│   │   │   │   ├── admin.py          # NEW: Admin-only endpoints
│   │   │   │   └── ...
│   ├── middleware/
│   │   └── tenant.py                  # NEW: Tenant isolation middleware
│   ├── models/
│   │   ├── user.py                    # NEW: User model with API keys
│   │   └── ...
│   ├── services/
│   │   ├── user.py                    # NEW: User service layer
│   │   ├── storage_metrics.py         # NEW: Disk usage calculation
│   │   └── ...

frontend/
├── src/
│   ├── components/
│   │   ├── admin/
│   │   │   ├── UserTable.tsx         # NEW: User management table
│   │   │   ├── UserStats.tsx         # NEW: Usage statistics
│   │   │   ├── UserActions.tsx       # NEW: Bulk operations
│   │   │   └── DiskUsageChart.tsx    # NEW: Storage visualization
│   ├── pages/
│   │   └── Admin.tsx                  # NEW: Admin dashboard page
│   ├── hooks/
│   │   └── useAuth.ts                 # NEW: Authentication hook
```

### Known Gotchas of our codebase & Library Quirks

```python
# CRITICAL: MongoDB ObjectId handling
# Always use ObjectId for _id fields, convert to string for API responses
from bson import ObjectId
# Pattern: Field(alias="_id") in Pydantic models

# CRITICAL: Decimal128 conversion
# MongoDB stores costs as Decimal128, always convert to float
from bson import Decimal128
if isinstance(total_cost, Decimal128):
    total_cost = float(total_cost.to_decimal())

# CRITICAL: Localhost authentication bypass
# Preserve localhost access without API key for frontend development
localhost_ips = {"127.0.0.1", "localhost", "::1"}

# CRITICAL: Async context
# All database operations must be async
# All service methods must be async
# FastAPI endpoints should be async
```

## Implementation Blueprint

### Data models and structure

```python
# backend/app/models/user.py
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class APIKey(BaseModel):
    """API Key associated with a user"""
    key_hash: str  # SHA256 hash of the actual key
    name: str
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    active: bool = True

class UserInDB(BaseModel):
    """User as stored in database"""
    id: ObjectId = Field(alias="_id")
    email: str
    username: str
    role: UserRole = UserRole.USER
    api_keys: List[APIKey] = []
    created_at: datetime
    updated_at: datetime

    # Usage statistics (denormalized for performance)
    project_count: int = 0
    session_count: int = 0
    message_count: int = 0
    total_disk_usage: int = 0  # in bytes

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

# Add user_id to existing models
# backend/app/models/session.py - ADD:
user_id: ObjectId  # Owner of this session

# backend/app/models/project.py - ADD:
user_id: ObjectId  # Owner of this project

# backend/app/models/message.py - ADD:
user_id: ObjectId  # Owner of this message
```

### Implementation Tasks (ordered by dependencies)

```yaml
Task 1: CREATE backend/app/models/user.py
  - IMPLEMENT: UserInDB, APIKey, UserRole models
  - FOLLOW pattern: backend/app/models/session.py (ObjectId handling, ConfigDict)
  - NAMING: UserInDB for database model, use Field(alias="_id")
  - PLACEMENT: Models directory with other domain models

Task 2: MODIFY existing models to add user_id
  - UPDATE: backend/app/models/session.py - add user_id field
  - UPDATE: backend/app/models/project.py - add user_id field
  - UPDATE: backend/app/models/message.py - add user_id field
  - PATTERN: user_id: ObjectId with proper imports
  - MIGRATION: Plan for existing data (default to admin user)

Task 3: CREATE backend/app/services/user.py
  - IMPLEMENT: UserService class with CRUD operations
  - FOLLOW pattern: backend/app/services/session.py (async methods, db injection)
  - METHODS: create_user, get_user_by_api_key, update_user_stats
  - SECURITY: Hash API keys with hashlib.sha256

Task 4: CREATE backend/app/middleware/tenant.py
  - IMPLEMENT: TenantMiddleware for request context injection
  - EXTRACT: user_id from API key, add to request.state
  - INTEGRATE: With existing verify_api_key_header dependency
  - PRESERVE: Localhost bypass for development

Task 5: CREATE backend/app/services/storage_metrics.py
  - IMPLEMENT: StorageMetricsService for disk usage calculation
  - USE: MongoDB $bsonSize aggregation operator
  - METHODS: calculate_user_storage, update_user_metrics
  - PATTERN: Aggregation pipelines with tenant filtering

Task 6: MODIFY backend/app/api/dependencies.py
  - UPDATE: verify_api_key_header to return user_id
  - LOOKUP: User from API key hash in database
  - ADD: get_current_user dependency
  - ADD: require_admin dependency for admin endpoints

Task 7: CREATE backend/app/api/api_v1/endpoints/users.py
  - IMPLEMENT: User CRUD endpoints
  - ENDPOINTS: GET /users (list), POST /users (create), DELETE /users/{id}
  - SECURITY: All endpoints require admin role
  - PATTERN: Follow backend/app/api/api_v1/endpoints/sessions.py

Task 8: CREATE backend/app/api/api_v1/endpoints/admin.py
  - IMPLEMENT: Admin dashboard API endpoints
  - ENDPOINTS: GET /admin/stats, GET /admin/users, POST /admin/users/{id}/reset-api-key
  - AGGREGATION: User statistics with disk usage
  - PATTERN: PaginatedResponse for user listing

Task 9: MODIFY all existing service methods
  - UPDATE: SessionService - filter by user_id
  - UPDATE: MessageService - filter by user_id
  - UPDATE: ProjectService - filter by user_id
  - PATTERN: Add user_id to all queries
  - ENSURE: No data leakage between tenants

Task 10: CREATE frontend/src/pages/Admin.tsx
  - IMPLEMENT: Admin dashboard main page
  - COMPONENTS: UserTable, UserStats, bulk operations
  - ROUTING: Add to App.tsx routes
  - AUTH: Check user role before display

Task 11: CREATE frontend/src/components/admin/UserTable.tsx
  - IMPLEMENT: Data table with TanStack Table
  - FEATURES: Sorting, filtering, pagination
  - ACTIONS: Edit role, delete user, reset API key
  - PATTERN: Use shadcn/ui data-table components

Task 12: CREATE frontend/src/components/admin/DiskUsageChart.tsx
  - IMPLEMENT: Recharts pie/bar chart for storage
  - DATA: User disk usage statistics
  - RESPONSIVE: Handle different screen sizes
  - PATTERN: Follow existing chart components

Task 13: CREATE frontend/src/hooks/useAuth.ts
  - IMPLEMENT: Authentication state management
  - METHODS: getCurrentUser, isAdmin, hasPermission
  - STORAGE: Use localStorage for API key
  - PATTERN: Custom React hook with context

Task 14: CREATE tests for all new components
  - TEST: backend/tests/test_services_user.py
  - TEST: backend/tests/test_middleware_tenant.py
  - TEST: backend/tests/test_endpoints_admin.py
  - PATTERN: Follow existing test patterns with pytest
  - COVERAGE: Happy path, error cases, edge cases
```

### Implementation Patterns & Key Details

```python
# Tenant isolation pattern for services
class TenantAwareService:
    async def list_resources(self, user_id: ObjectId, **filters):
        # CRITICAL: Always include user_id in query
        query = {"user_id": user_id, **filters}
        return await self.db.collection.find(query).to_list(None)

    async def get_resource(self, user_id: ObjectId, resource_id: str):
        # CRITICAL: Verify ownership before returning
        resource = await self.db.collection.find_one({
            "_id": ObjectId(resource_id),
            "user_id": user_id  # Ensures tenant isolation
        })
        if not resource:
            raise NotFoundError("Resource", resource_id)
        return resource

# API key generation and validation
import secrets
import hashlib

def generate_api_key() -> tuple[str, str]:
    """Generate API key and its hash"""
    # Generate secure random key
    api_key = f"cl_{secrets.token_urlsafe(32)}"
    # Store hash in database
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return api_key, key_hash

# Disk usage aggregation pipeline
async def calculate_user_storage(user_id: ObjectId):
    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": "$user_id",
                "total_size": {"$sum": {"$bsonSize": "$$ROOT"}},
                "document_count": {"$sum": 1}
            }
        }
    ]
    result = await db.messages.aggregate(pipeline).to_list(1)
    return result[0] if result else {"total_size": 0, "document_count": 0}

# Admin role check dependency
async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

### Integration Points

```yaml
DATABASE:
  - indexes:
    - "db.users.createIndex({'api_keys.key_hash': 1})"
    - "db.sessions.createIndex({'user_id': 1, 'startedAt': -1})"
    - "db.messages.createIndex({'user_id': 1, 'timestamp': -1})"
    - "db.projects.createIndex({'user_id': 1, 'createdAt': -1})"

CONFIG:
  - add to: backend/app/core/config.py
  - settings: "DEFAULT_ADMIN_EMAIL", "API_KEY_LENGTH"

ROUTES:
  - add to: backend/app/api/api_v1/api.py
  - pattern: "api_router.include_router(users.router, prefix='/users', tags=['users'])"
  - pattern: "api_router.include_router(admin.router, prefix='/admin', tags=['admin'])"

FRONTEND_ROUTES:
  - add to: frontend/src/App.tsx
  - pattern: "<Route path='/admin' element={<Admin />} />"
  - protection: "Check user role before rendering"
```

## Validation Loop

### Level 1: Syntax & Style (Immediate Feedback)

```bash
# Backend validation
cd backend
poetry run ruff check app/ --fix
poetry run mypy app/
poetry run ruff format app/

# Frontend validation
cd frontend
npm run lint
npm run type-check
npm run format:check

# Expected: Zero errors
```

### Level 2: Unit Tests (Component Validation)

```bash
# Backend tests
cd backend
poetry run pytest tests/test_services_user.py -v
poetry run pytest tests/test_middleware_tenant.py -v
poetry run pytest tests/test_endpoints_admin.py -v

# Integration tests
poetry run pytest tests/test_integration_multi_tenant.py -v

# Frontend tests
cd frontend
npm run test:coverage
npm run test:unit

# Expected: All tests pass with >80% coverage
```

### Level 3: Integration Testing (System Validation)

```bash
# Start backend with user authentication
cd backend
poetry run uvicorn app.main:app --reload &

# Test user creation and API key generation
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin-key" \
  -d '{"email": "test@example.com", "username": "testuser", "role": "user"}'

# Test tenant isolation
curl -X GET http://localhost:8000/api/v1/sessions \
  -H "X-API-Key: user-api-key-1"

# Should not see other user's data
curl -X GET http://localhost:8000/api/v1/sessions \
  -H "X-API-Key: user-api-key-2"

# Test admin endpoints
curl -X GET http://localhost:8000/api/v1/admin/stats \
  -H "X-API-Key: admin-api-key"

# Expected: Proper data isolation, admin access working
```

### Level 4: Creative & Domain-Specific Validation

```bash
# Test storage metrics calculation
python -c "
from app.services.storage_metrics import calculate_user_storage
import asyncio
# Verify storage calculation accuracy
"

# Load test with multiple users
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/ingest \
    -H "X-API-Key: user-key-$i" \
    -d @sample_data.json &
done
wait

# Verify tenant isolation under load
# Check that each user sees only their data

# Test admin dashboard performance
curl -X GET "http://localhost:8000/api/v1/admin/users?limit=100" \
  -H "X-API-Key: admin-key" \
  -w "\nTime: %{time_total}s\n"

# Expected: <500ms response time for 100 users
```

## Final Validation Checklist

### Technical Validation

- [ ] All validation levels completed successfully
- [ ] Backend tests pass: `poetry run pytest`
- [ ] Frontend tests pass: `npm test`
- [ ] No linting errors in backend or frontend
- [ ] API documentation updated with new endpoints

### Feature Validation

- [ ] Users can only access their own resources
- [ ] Admin can view all users and statistics
- [ ] Disk usage correctly calculated per user
- [ ] API key generation and validation working
- [ ] Bulk user operations functioning
- [ ] Frontend admin dashboard responsive and functional

### Code Quality Validation

- [ ] Follows existing codebase patterns
- [ ] Tenant isolation verified in all services
- [ ] No hardcoded credentials or keys
- [ ] Proper error handling with meaningful messages
- [ ] Database indexes created for performance

### Documentation & Deployment

- [ ] API key usage documented
- [ ] Admin interface documented
- [ ] Migration plan for existing data
- [ ] Environment variables documented

---

## Anti-Patterns to Avoid

- ❌ Don't query without user_id filter (data leakage)
- ❌ Don't store plain text API keys (security risk)
- ❌ Don't skip tenant validation (security vulnerability)
- ❌ Don't calculate disk usage on every request (performance)
- ❌ Don't allow non-admin users to access admin endpoints
- ❌ Don't forget to test with multiple concurrent users
- ❌ Don't hardcode admin credentials
