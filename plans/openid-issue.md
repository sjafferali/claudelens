# OIDC Authentication 502 Error Issue

## Issue Description
- **Problem**: OIDC authentication with Authelia results in 502 Bad Gateway errors
- **Environment**: Production deployment at https://claudecode.home.samir.network
- **Auth Provider**: Authelia at https://auth.samir.network
- **Key Observation**: A new user IS created in the database, but the authentication still fails with 502

## Authelia Configuration
```yaml
- client_id: 'claudelens'
  client_name: 'Claudelens'
  client_secret: 'ENCRYPTED_SECRET'
  public: false
  authorization_policy: 'one_factor'
  require_pkce: false
  redirect_uris:
    - 'https://claudecode.home.samir.network/auth/oidc/callback'
  scopes:
    - 'openid'
    - 'profile'
    - 'email'
  token_endpoint_auth_method: 'client_secret_basic'
```

## Authentication Flow Analysis

### Working Parts:
1. ✅ OIDC provider discovery and metadata fetching
2. ✅ Authorization redirect to Authelia
3. ✅ User login and consent at Authelia
4. ✅ Callback redirect with authorization code
5. ✅ Token exchange (authorization code → access token)
6. ✅ User info retrieval
7. ✅ User creation in database

### Failing Part:
8. ❌ Response to frontend after user creation (502 error)

## Root Cause Analysis

### Initial Hypotheses:
1. **Timeout during metadata fetch** - authlib fetching metadata synchronously
2. **Provider re-registration** - OAuth provider being re-registered on each callback
3. **Long timeout chains** - 30s timeouts causing proxy timeouts

### Current Status:
- User IS being created successfully in the database
- The 502 error occurs AFTER user creation
- This suggests the issue is in:
  - Session storage
  - Response serialization
  - Return path to the frontend

## Changes Attempted

### Attempt 1: Add Timeout Handling
```python
# Added timeout and error handling to HTTP requests
timeout = httpx.Timeout(30.0, connect=10.0)
async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as http_client:
    # Exchange code for token
```
**Result**: ❌ Still getting 502 errors

### Attempt 2: Implement Metadata Caching
```python
# Cache metadata for 1 hour to avoid repeated fetches
async def _get_cached_metadata(self) -> Optional[Dict[str, Any]]:
    if self._cached_metadata and self._metadata_cache_time:
        if (datetime.utcnow() - self._metadata_cache_time).total_seconds() < 3600:
            return self._cached_metadata
    # Fetch fresh metadata...
```
**Result**: ❌ Still getting 502 errors

### Attempt 3: Direct Token Exchange
```python
# Bypass authlib OAuth client for more control
async def exchange_code_for_token_direct(...):
    # Direct HTTP calls with httpx
    # Shorter timeouts (10s)
    # Better error handling
```
**Result**: ❌ Still getting 502 errors

### Attempt 4: Skip Provider Re-registration
```python
# Avoid re-registering OAuth provider during callback
async def load_settings(self, db, skip_configure: bool = False):
    if self._settings and skip_configure:
        return self._settings
```
**Result**: ❌ Still getting 502 errors

### Attempt 5: Fix AISettings Configuration
```python
# Allow extra environment variables
model_config = SettingsConfigDict(
    env_file=".env", case_sensitive=False, env_prefix="", extra="ignore"
)
```
**Result**: ✅ Fixed import errors, but 502 persists

## Latest Discovery
**Critical Finding**: The user IS being created in the database, which means:
1. The entire OIDC flow is working up to user creation
2. The 502 error happens AFTER successful authentication
3. The issue is likely in the response path back to the frontend

## Potential Issues After User Creation

### 1. Session Storage Issue
- Session data might be too large
- Session serialization might be failing
- Session middleware timeout

### 2. Response Serialization
- User object might have non-serializable fields
- JSON encoding might be failing
- Response size might be too large

### 3. Network/Proxy Issues
- Reverse proxy timeout after long processing
- Keep-alive timeout
- Response buffering issues

## Next Investigation Steps

1. **Check Logs at User Creation Point**
   - Look for errors after "User authenticated" log
   - Check for serialization errors
   - Look for session storage errors

2. **Test Response Path**
   - Verify JWT token creation works
   - Check response JSON structure
   - Validate all fields are serializable

3. **Simplify Response**
   - Return minimal user data
   - Remove session storage temporarily
   - Test with simple success response

4. **Add Detailed Logging**
   - Log before/after each step after user creation
   - Add try/catch around response serialization
   - Log response size and content

## Current Code State

### Backend: `/backend/app/services/oidc_service.py`
- Using `exchange_code_for_token_direct()` method
- Metadata caching implemented
- Session serialization helper added

### Backend: `/backend/app/api/api_v1/endpoints/oidc.py`
- Using `skip_configure=True` during callback
- Timing logs added
- Response structure defined

### Frontend: `/frontend/src/pages/OIDCCallback.tsx`
- Handles authorization code
- Makes POST to backend callback endpoint
- Expects JWT token in response

## Database Connection
```
mongodb://admin:PASSWORD@c-rat.local.samir.systems:27017/claudelens?authSource=admin
```

## Test Credentials
- Username: sjafferali
- Password: sj555555

## Status
🔴 **ACTIVE INVESTIGATION** - User creation works but response fails with 502
