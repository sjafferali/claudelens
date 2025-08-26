name: "OpenID Connect Authentication Integration for ClaudeLens"
description: |
  Complete implementation of external OpenID Connect authentication with Authelia compatibility,
  supporting dual authentication modes (API keys and OIDC), admin dashboard configuration,
  and automatic user provisioning.

---

## Goal

**Feature Goal**: Implement external OpenID Connect 1.0 authentication that seamlessly integrates with the existing authentication system, allowing users to authenticate via OIDC providers (like Authelia) while maintaining API key support for programmatic access.

**Deliverable**: Complete OIDC authentication system with admin configuration UI, dual authentication support, automatic user provisioning, and full Authelia compatibility.

**Success Definition**: Users can authenticate via OIDC or existing methods, admins can configure OIDC providers through the dashboard, API keys continue working for automation, and new users are automatically created from OIDC claims.

## User Persona

**Target User**:
- **Administrators**: Configure and manage OIDC providers
- **End Users**: Authenticate using enterprise SSO
- **Developers**: Continue using API keys for automation

**Use Case**: Enterprise deployment where users authenticate through centralized identity provider (Authelia, Keycloak, Auth0) while maintaining API access for CI/CD and automation tools.

**User Journey**:
1. Admin enables OIDC in dashboard and configures provider settings
2. User clicks "Login with SSO" on login page
3. User authenticates with identity provider
4. User is redirected back and automatically logged in
5. New users are auto-provisioned with appropriate roles

**Pain Points Addressed**:
- Eliminate password management for enterprise users
- Centralize authentication across multiple applications
- Maintain programmatic access without SSO complexity
- Reduce onboarding friction with auto-provisioning

## Why

- **Enterprise Integration**: Enables deployment in enterprise environments with existing identity infrastructure
- **Security Enhancement**: Leverages enterprise-grade authentication with MFA, session management
- **User Experience**: Single sign-on across multiple applications
- **Compliance**: Meets enterprise security requirements for centralized access control
- **Flexibility**: Supports multiple authentication methods for different use cases

## What

### Functional Requirements
- Support OpenID Connect 1.0 authentication flow
- Maintain existing API key authentication
- Admin UI for OIDC configuration
- Automatic user provisioning from OIDC claims
- Support both OIDC and password authentication when enabled
- Test connection functionality for OIDC providers
- Authelia compatibility as baseline

### Technical Requirements
- Authorization Code flow with PKCE
- JWT token validation with signature verification
- OIDC discovery endpoint support
- Encrypted storage of client secrets
- Session management for web authentication
- Graceful fallback for authentication methods

### Success Criteria

- [ ] OIDC authentication works with Authelia
- [ ] API keys continue functioning unchanged
- [ ] Admin can enable/disable OIDC via dashboard
- [ ] Users auto-provision on first OIDC login
- [ ] Test connection validates OIDC configuration
- [ ] Dual authentication methods work simultaneously
- [ ] Client secrets are encrypted in database
- [ ] OIDC settings included in backup/restore

## All Needed Context

### Context Completeness Check

_This PRP provides complete implementation details for OIDC integration including specific file paths, patterns to follow, library configurations, and security considerations._

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- url: https://docs.authlib.org/en/latest/client/fastapi.html
  why: Complete Authlib FastAPI integration guide
  critical: OAuth client setup, session middleware configuration, token handling

- url: https://www.authelia.com/integration/openid-connect/introduction/
  why: Authelia OIDC implementation specifics
  critical: Endpoint paths, supported flows, configuration requirements

- file: backend/app/services/auth.py
  why: Current JWT authentication implementation to extend
  pattern: AuthService class structure, token creation/validation methods
  gotcha: Must maintain backward compatibility with existing JWT tokens

- file: backend/app/api/dependencies.py
  why: Authentication dependency injection patterns
  pattern: verify_api_key_or_jwt() multi-method authentication
  gotcha: Order matters - check OIDC before API keys

- file: backend/app/models/ai_settings.py
  why: Configuration model pattern for OIDC settings
  pattern: Encrypted field storage, enabled flag, settings structure
  gotcha: Use same encryption approach for client secret

- file: backend/app/core/ai_config.py
  why: Encryption/decryption implementation
  pattern: Fernet encryption for sensitive data
  gotcha: Encryption key must be configured in environment

- file: frontend/src/components/settings/AISettingsPanel.tsx
  why: Settings UI pattern for OIDC configuration
  pattern: Form state, toggle switches, test connection UI
  gotcha: Mask sensitive data, show/hide functionality

- docfile: PRPs/ai_docs/authlib-fastapi-oidc-patterns.md
  why: Detailed Authlib implementation patterns and code examples
  section: All sections for complete OIDC implementation
```

### Current Codebase Tree

```bash
backend/
├── app/
│   ├── api/
│   │   ├── api_v1/
│   │   │   └── endpoints/
│   │   │       ├── admin.py         # Admin endpoints
│   │   │       ├── auth.py          # Auth endpoints
│   │   │       └── ai_settings.py   # Settings pattern
│   │   └── dependencies.py          # Auth dependencies
│   ├── core/
│   │   ├── security.py              # Security utilities
│   │   └── ai_config.py             # Encryption utilities
│   ├── models/
│   │   ├── user.py                  # User model
│   │   └── ai_settings.py           # Settings model pattern
│   ├── services/
│   │   ├── auth.py                  # Auth service
│   │   └── user.py                  # User service
│   └── middleware/
│       └── tenant.py                 # Tenant context

frontend/
├── src/
│   ├── pages/
│   │   ├── Admin.tsx                # Admin dashboard
│   │   └── Login.tsx                # Login page
│   ├── components/
│   │   ├── admin/                   # Admin components
│   │   └── settings/                # Settings components
│   └── api/
│       └── authApi.ts               # Auth API client
```

### Desired Codebase Tree with Files to be Added

```bash
backend/
├── app/
│   ├── api/
│   │   └── api_v1/
│   │       └── endpoints/
│   │           └── oidc.py          # NEW: OIDC auth endpoints
│   ├── models/
│   │   └── oidc_settings.py         # NEW: OIDC configuration model
│   ├── schemas/
│   │   └── oidc.py                  # NEW: OIDC schemas
│   └── services/
│       └── oidc_service.py          # NEW: OIDC service logic

frontend/
├── src/
│   ├── components/
│   │   └── settings/
│   │       └── OIDCSettingsPanel.tsx # NEW: OIDC settings UI
│   └── api/
│       └── oidcApi.ts                # NEW: OIDC API client
```

### Known Gotchas of our Codebase & Library Quirks

```python
# CRITICAL: Authlib requires session middleware for state management
# Must add SessionMiddleware to FastAPI app before OAuth initialization

# CRITICAL: ClaudeLens uses SHA-256 for API key hashing
# Don't confuse with bcrypt used for passwords

# CRITICAL: Encryption key must be set in environment
# Generate with: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())

# CRITICAL: Frontend uses React Query for state management
# Must invalidate auth queries on login/logout

# CRITICAL: MongoDB ObjectId serialization
# Use PyObjectId for proper BSON handling
```

## Implementation Blueprint

### Data Models and Structure

```python
# backend/app/models/oidc_settings.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from backend.app.models.common import PyObjectId

class OIDCSettingsInDB(BaseModel):
    """OIDC provider configuration stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    enabled: bool = Field(False, description="Enable OIDC authentication")
    client_id: str = Field(..., description="OIDC client ID")
    client_secret_encrypted: str = Field(..., description="Encrypted client secret")
    discovery_endpoint: str = Field(..., description="OIDC discovery URL")
    redirect_uri: str = Field(..., description="Callback URL")
    scopes: List[str] = Field(
        default=['openid', 'email', 'profile'],
        description="OIDC scopes to request"
    )
    auto_create_users: bool = Field(True, description="Auto-create users on first login")
    default_role: str = Field('user', description="Default role for new users")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None

# Extend existing User model
# backend/app/models/user.py - ADD these fields
class UserOIDCFields:
    oidc_sub: Optional[str] = None  # OIDC subject identifier
    oidc_provider: Optional[str] = None  # Provider name
    auth_method: str = 'local'  # 'local', 'oidc', 'api_key'
```

### Implementation Tasks (ordered by dependencies)

```yaml
Task 1: CREATE backend/app/models/oidc_settings.py
  - IMPLEMENT: OIDCSettingsInDB model with encrypted client secret
  - FOLLOW pattern: backend/app/models/ai_settings.py structure
  - NAMING: OIDCSettingsInDB, same pattern as AISettingsInDB
  - PLACEMENT: Models directory with other settings models

Task 2: CREATE backend/app/schemas/oidc.py
  - IMPLEMENT: Request/response schemas for OIDC settings
  - FOLLOW pattern: backend/app/schemas/ai_settings.py
  - SCHEMAS: OIDCSettingsCreate, OIDCSettingsUpdate, OIDCSettingsResponse
  - VALIDATION: Ensure URL validation for discovery endpoint

Task 3: CREATE backend/app/services/oidc_service.py
  - IMPLEMENT: OIDCService class with Authlib integration
  - FOLLOW pattern: backend/app/services/auth.py service structure
  - METHODS: configure_provider(), test_connection(), get_or_create_user()
  - DEPENDENCIES: Authlib OAuth client, encryption from ai_config.py
  - CRITICAL: Initialize OAuth client with discovery URL

Task 4: MODIFY backend/app/models/user.py
  - ADD: OIDC fields (oidc_sub, oidc_provider, auth_method)
  - MAINTAIN: Backward compatibility with existing users
  - DEFAULT: auth_method='local' for existing users
  - INDEX: Create index on oidc_sub for fast lookups

Task 5: CREATE backend/app/api/api_v1/endpoints/oidc.py
  - IMPLEMENT: OIDC authentication endpoints
  - ENDPOINTS: /auth/oidc/login, /auth/oidc/callback, /auth/oidc/logout
  - FOLLOW pattern: backend/app/api/api_v1/endpoints/auth.py
  - DEPENDENCIES: OIDCService, session management
  - SECURITY: CSRF protection via state parameter

Task 6: MODIFY backend/app/api/api_v1/endpoints/admin.py
  - ADD: OIDC settings management endpoints
  - ENDPOINTS: GET/PUT/DELETE /admin/oidc-settings, POST /admin/oidc-settings/test
  - FOLLOW pattern: AI settings endpoints in same file
  - PERMISSIONS: Require admin role

Task 7: MODIFY backend/app/api/dependencies.py
  - EXTEND: verify_api_key_or_jwt() to check OIDC session
  - ORDER: Check OIDC session, then JWT, then API key
  - MAINTAIN: Backward compatibility
  - ADD: get_oidc_user() dependency function

Task 8: MODIFY backend/app/main.py
  - ADD: SessionMiddleware for OIDC state management
  - CONFIGURE: OAuth client initialization
  - REGISTER: OIDC endpoints router
  - CRITICAL: Middleware must be added before OAuth init

Task 9: CREATE frontend/src/api/oidcApi.ts
  - IMPLEMENT: OIDC API client functions
  - FOLLOW pattern: frontend/src/api/authApi.ts
  - FUNCTIONS: getOIDCSettings(), updateOIDCSettings(), testOIDCConnection()
  - TYPES: Define TypeScript interfaces for OIDC data

Task 10: CREATE frontend/src/components/settings/OIDCSettingsPanel.tsx
  - IMPLEMENT: OIDC configuration UI component
  - FOLLOW pattern: frontend/src/components/settings/AISettingsPanel.tsx
  - FEATURES: Enable toggle, form fields, test connection, save/reset
  - SECURITY: Mask client secret, show/hide functionality

Task 11: MODIFY frontend/src/pages/Login.tsx
  - ADD: "Login with SSO" button when OIDC enabled
  - CONDITIONAL: Show based on OIDC settings
  - REDIRECT: To /auth/oidc/login endpoint
  - MAINTAIN: Existing username/password form

Task 12: MODIFY frontend/src/pages/Admin.tsx
  - ADD: OIDC settings section in admin dashboard
  - INTEGRATE: OIDCSettingsPanel component
  - PERMISSIONS: Only show to admin users
  - STATISTICS: Add OIDC vs local auth metrics

Task 13: CREATE backend/app/api/api_v1/endpoints/tests/test_oidc.py
  - IMPLEMENT: Unit tests for OIDC endpoints
  - FOLLOW pattern: backend/tests/test_endpoints_auth.py
  - COVERAGE: Login flow, callback, user creation, error cases
  - MOCK: OAuth client, OIDC provider responses

Task 14: MODIFY backend/app/services/backup_service.py
  - ADD: Include OIDC settings in backup
  - ENCRYPT: Maintain encryption for client secret
  - RESTORE: Handle OIDC settings restoration
  - TEST: Backup/restore with OIDC configured
```

### Implementation Patterns & Key Details

```python
# OIDC Service initialization pattern
from authlib.integrations.starlette_client import OAuth
from backend.app.core.config import settings

class OIDCService:
    def __init__(self):
        self.oauth = OAuth()
        self._configured = False

    async def configure_provider(self, settings: OIDCSettingsInDB):
        """Configure OIDC provider from settings."""
        if not settings.enabled:
            return

        # Decrypt client secret
        client_secret = self.decrypt_secret(settings.client_secret_encrypted)

        # Register OIDC provider
        self.oauth.register(
            name='oidc_provider',
            server_metadata_url=settings.discovery_endpoint,
            client_id=settings.client_id,
            client_secret=client_secret,
            client_kwargs={'scope': ' '.join(settings.scopes)}
        )
        self._configured = True

# Authentication dependency pattern
async def get_current_user(
    request: Request,
    api_key: Optional[str] = Security(api_key_header),
    bearer: Optional[str] = Security(bearer_token),
    db = Depends(get_db)
) -> UserInDB:
    """Support OIDC, JWT, and API key authentication."""

    # Check OIDC session first
    if hasattr(request.state, 'user') and request.state.user:
        return request.state.user

    # Try existing JWT/API key methods
    return await verify_api_key_or_jwt(api_key, bearer, db)

# User auto-provisioning pattern
async def get_or_create_user_from_oidc(claims: dict, db) -> UserInDB:
    """Create or update user from OIDC claims."""
    sub = claims.get('sub')

    # Check existing user
    user = await db.users.find_one({'oidc_sub': sub})

    if not user:
        # Auto-provision new user
        user_data = {
            'oidc_sub': sub,
            'email': claims.get('email'),
            'username': claims.get('preferred_username') or claims.get('email').split('@')[0],
            'full_name': claims.get('name'),
            'role': UserRole.USER,  # Default role
            'auth_method': 'oidc',
            'created_at': datetime.utcnow(),
        }
        result = await db.users.insert_one(user_data)
        user = await db.users.find_one({'_id': result.inserted_id})

    return UserInDB(**user)
```

### Integration Points

```yaml
DATABASE:
  - collection: "oidc_settings"
  - migration: "Add oidc_sub, auth_method to users collection"
  - index: "CREATE INDEX idx_oidc_sub ON users(oidc_sub)"

CONFIG:
  - add to: backend/app/core/config.py
  - variables: |
      SESSION_SECRET_KEY = os.getenv('SESSION_SECRET_KEY', secrets.token_urlsafe(32))
      SESSION_COOKIE_NAME = 'claudelens_session'
      SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'

ROUTES:
  - add to: backend/app/api/api_v1/api.py
  - code: |
      from backend.app.api.api_v1.endpoints import oidc
      api_router.include_router(oidc.router, prefix="/auth/oidc", tags=["oidc"])

MIDDLEWARE:
  - add to: backend/app/main.py
  - code: |
      from starlette.middleware.sessions import SessionMiddleware
      app.add_middleware(
          SessionMiddleware,
          secret_key=settings.SESSION_SECRET_KEY,
          session_cookie=settings.SESSION_COOKIE_NAME,
      )
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
npm run format

# Expected: Zero errors. Fix any issues before proceeding.
```

### Level 2: Unit Tests (Component Validation)

```bash
# Backend tests
cd backend
poetry run pytest app/api/api_v1/endpoints/tests/test_oidc.py -v
poetry run pytest app/services/tests/test_oidc_service.py -v

# Test with coverage
poetry run pytest --cov=app.api.api_v1.endpoints.oidc --cov=app.services.oidc_service

# Frontend tests
cd frontend
npm run test -- --run OIDCSettingsPanel
npm run test -- --run oidcApi

# Expected: All tests pass with >80% coverage
```

### Level 3: Integration Testing (System Validation)

```bash
# Start services
docker-compose up -d mongodb
cd backend && poetry run uvicorn app.main:app --reload &
cd frontend && npm run dev &

# Test OIDC settings API
curl -X GET http://localhost:8000/api/v1/admin/oidc-settings \
  -H "X-API-Key: ${API_KEY}"

# Test OIDC connection
curl -X POST http://localhost:8000/api/v1/admin/oidc-settings/test \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "discovery_endpoint": "https://auth.example.com/.well-known/openid-configuration"
  }'

# Test login flow
curl -X GET http://localhost:8000/api/v1/auth/oidc/login

# Verify session creation
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Cookie: claudelens_session=${SESSION_COOKIE}"

# Expected: Proper redirects, session creation, user provisioning
```

### Level 4: Creative & Domain-Specific Validation

```bash
# Test with real Authelia instance
# Set up test Authelia container
docker run -d --name authelia \
  -v ./authelia:/config \
  authelia/authelia:latest

# Configure test OIDC client in Authelia
# Test full authentication flow

# Security validation
# Check encrypted storage
mongo claudelens --eval "db.oidc_settings.find().pretty()"
# Verify client_secret is encrypted

# Test dual authentication
# 1. Login with OIDC
# 2. Generate API key
# 3. Test API key works
# 4. Test OIDC session works

# Performance testing
# Measure OIDC login time
time curl -w "@curl-format.txt" -o /dev/null -s \
  http://localhost:8000/api/v1/auth/oidc/callback?code=test

# Backup/restore validation
# Create backup with OIDC configured
curl -X POST http://localhost:8000/api/v1/backup/create
# Restore and verify OIDC settings preserved

# Expected: All security checks pass, dual auth works, performance acceptable
```

## Final Validation Checklist

### Technical Validation

- [ ] All 4 validation levels completed successfully
- [ ] Backend tests pass: `poetry run pytest`
- [ ] Frontend tests pass: `npm run test`
- [ ] No linting errors: `ruff check` and `npm run lint`
- [ ] No type errors: `mypy` and `npm run type-check`
- [ ] Encryption verified for client secrets

### Feature Validation

- [ ] OIDC login works with Authelia
- [ ] Users auto-provision on first login
- [ ] API keys continue working
- [ ] Admin can configure OIDC settings
- [ ] Test connection validates provider
- [ ] Dual authentication works (OIDC + API keys)
- [ ] OIDC can be enabled/disabled
- [ ] Settings included in backup/restore

### Code Quality Validation

- [ ] Follows existing ClaudeLens patterns
- [ ] Proper error handling implemented
- [ ] Security best practices followed
- [ ] No hardcoded secrets
- [ ] Proper session management
- [ ] CSRF protection via state parameter

### Documentation & Deployment

- [ ] Environment variables documented
- [ ] Docker compose updated if needed
- [ ] Admin guide for OIDC configuration
- [ ] User guide for SSO login

---

## Anti-Patterns to Avoid

- ❌ Don't store client secrets in plaintext
- ❌ Don't skip state parameter validation
- ❌ Don't trust ID tokens without signature verification
- ❌ Don't create duplicate authentication flows
- ❌ Don't break existing API key authentication
- ❌ Don't hardcode OIDC provider URLs
- ❌ Don't skip session middleware configuration
- ❌ Don't ignore token expiration validation
