# Authlib FastAPI OpenID Connect Integration Patterns

## Overview
This document provides detailed implementation patterns for integrating OpenID Connect authentication in FastAPI applications using Authlib.

## Core Library: Authlib

### Installation
```bash
pip install authlib[httpx]
```

### Key Features
- Complete OAuth 2.0 and OpenID Connect 1.0 support
- Automatic OIDC discovery via `.well-known/openid-configuration`
- Built-in JWT validation with signature verification
- Session management and state handling
- PKCE support for enhanced security

## FastAPI Integration Pattern

### 1. Basic Configuration
```python
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
import secrets

# Configuration
config = Config('.env')
oauth = OAuth(config)

# OIDC Registration with Discovery
oauth.register(
    name='oidc_provider',
    server_metadata_url='https://provider.example.com/.well-known/openid-configuration',
    client_id=config('OIDC_CLIENT_ID'),
    client_secret=config('OIDC_CLIENT_SECRET'),
    client_kwargs={
        'scope': 'openid email profile',
        'token_endpoint_auth_method': 'client_secret_post'
    }
)
```

### 2. Session Middleware Setup
```python
from fastapi import FastAPI

app = FastAPI()

# Add session middleware for OIDC state management
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32),
    session_cookie="claudelens_session",
    https_only=True,  # Production setting
    same_site="lax"
)
```

### 3. Authentication Flow Implementation
```python
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

@app.get('/auth/login')
async def login(request: Request):
    """Initiate OIDC authentication flow."""
    redirect_uri = request.url_for('auth_callback')
    return await oauth.oidc_provider.authorize_redirect(
        request,
        redirect_uri,
        prompt='select_account'  # Optional: force account selection
    )

@app.get('/auth/callback')
async def auth_callback(request: Request):
    """Handle OIDC callback and create user session."""
    try:
        # Exchange authorization code for tokens
        token = await oauth.oidc_provider.authorize_access_token(request)

        # Parse ID token for user info
        user_info = token.get('userinfo')
        if not user_info:
            # Fetch from userinfo endpoint if not in token
            user_info = await oauth.oidc_provider.userinfo(token=token)

        # Store in session or create JWT
        request.session['user'] = dict(user_info)

        return RedirectResponse(url='/')
    except OAuthError as error:
        raise HTTPException(status_code=400, detail=str(error))
```

### 4. Token Validation Pattern
```python
from jose import jwt, JWTError
from typing import Optional

class OIDCTokenValidator:
    def __init__(self, issuer: str, audience: str, jwks_uri: str):
        self.issuer = issuer
        self.audience = audience
        self.jwks_uri = jwks_uri
        self._jwks_client = None

    async def validate_token(self, token: str) -> dict:
        """Validate OIDC ID token."""
        try:
            # Get JWKS for signature verification
            if not self._jwks_client:
                self._jwks_client = await self._fetch_jwks()

            # Decode and validate
            payload = jwt.decode(
                token,
                self._jwks_client,
                algorithms=['RS256'],
                audience=self.audience,
                issuer=self.issuer
            )

            return payload
        except JWTError as e:
            raise HTTPException(status_code=401, detail=str(e))
```

### 5. User Auto-Provisioning
```python
from typing import Optional
from datetime import datetime

async def get_or_create_user_from_oidc(claims: dict, db) -> UserInDB:
    """Auto-provision user from OIDC claims."""
    # Standard OIDC claims
    sub = claims.get('sub')  # Unique identifier
    email = claims.get('email')
    email_verified = claims.get('email_verified', False)
    name = claims.get('name')
    given_name = claims.get('given_name')
    family_name = claims.get('family_name')
    picture = claims.get('picture')

    # Check if user exists
    user = await db.users.find_one({'oidc_sub': sub})

    if not user:
        # Create new user from OIDC claims
        user_data = {
            'oidc_sub': sub,
            'email': email,
            'email_verified': email_verified,
            'username': email.split('@')[0] if email else f'user_{sub[:8]}',
            'full_name': name or f'{given_name} {family_name}'.strip(),
            'profile_picture': picture,
            'role': UserRole.USER,  # Default role
            'auth_method': 'oidc',
            'created_at': datetime.utcnow(),
            'last_login': datetime.utcnow(),
        }

        result = await db.users.insert_one(user_data)
        user = await db.users.find_one({'_id': result.inserted_id})
    else:
        # Update last login
        await db.users.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.utcnow()}}
        )

    return UserInDB(**user)
```

### 6. Dual Authentication Support
```python
from fastapi import Depends, Security
from fastapi.security import HTTPBearer, APIKeyHeader

# Multiple security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_token = HTTPBearer(auto_error=False)

async def get_current_user(
    api_key: Optional[str] = Security(api_key_header),
    bearer: Optional[str] = Security(bearer_token),
    session: Optional[dict] = Depends(get_session),
    db = Depends(get_db)
) -> UserInDB:
    """Support multiple authentication methods."""

    # Try OIDC session first
    if session and 'user' in session:
        return await get_or_create_user_from_oidc(session['user'], db)

    # Try Bearer token (JWT from OIDC)
    if bearer:
        claims = await validate_oidc_token(bearer.credentials)
        return await get_or_create_user_from_oidc(claims, db)

    # Try API key
    if api_key:
        user = await validate_api_key(api_key, db)
        if user:
            return user

    raise HTTPException(status_code=401, detail="Not authenticated")
```

### 7. OIDC Configuration Model
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class OIDCSettings(BaseModel):
    """OIDC provider configuration."""
    enabled: bool = Field(False, description="Enable OIDC authentication")
    client_id: str = Field(..., description="OIDC client ID")
    client_secret_encrypted: str = Field(..., description="Encrypted client secret")
    discovery_endpoint: str = Field(..., description="OIDC discovery URL")
    redirect_uri: str = Field(..., description="Callback URL")
    scopes: List[str] = Field(
        default=['openid', 'email', 'profile'],
        description="OIDC scopes to request"
    )
    user_claim_mapping: dict = Field(
        default={
            'sub': 'oidc_sub',
            'email': 'email',
            'name': 'full_name',
            'given_name': 'first_name',
            'family_name': 'last_name',
        },
        description="Map OIDC claims to user fields"
    )
    auto_create_users: bool = Field(True, description="Auto-create users on first login")
    default_role: str = Field('user', description="Default role for new users")
```

## Security Best Practices

### 1. State Parameter Validation
```python
# Authlib handles state automatically, but for manual validation:
import secrets

def generate_state():
    """Generate secure state parameter."""
    return secrets.token_urlsafe(32)

def validate_state(request_state: str, session_state: str):
    """Validate state to prevent CSRF."""
    if not secrets.compare_digest(request_state, session_state):
        raise HTTPException(status_code=400, detail="Invalid state parameter")
```

### 2. PKCE Implementation
```python
# Authlib supports PKCE automatically when configured:
oauth.register(
    name='oidc_provider',
    # ... other config
    client_kwargs={
        'code_challenge_method': 'S256',  # Enable PKCE
    }
)
```

### 3. Nonce Validation
```python
def validate_nonce(id_token: dict, session_nonce: str):
    """Validate nonce to prevent replay attacks."""
    token_nonce = id_token.get('nonce')
    if not token_nonce or token_nonce != session_nonce:
        raise HTTPException(status_code=400, detail="Invalid nonce")
```

### 4. Token Refresh Pattern
```python
async def refresh_access_token(refresh_token: str):
    """Refresh expired access token."""
    try:
        new_token = await oauth.oidc_provider.refresh_token(
            refresh_token=refresh_token
        )
        return new_token
    except OAuthError:
        # Refresh failed, require re-authentication
        raise HTTPException(status_code=401, detail="Token refresh failed")
```

## Authelia-Specific Considerations

### Discovery Endpoint
```python
# Authelia's discovery endpoint
AUTHELIA_DISCOVERY = "https://auth.example.com/.well-known/openid-configuration"

# Endpoints exposed by Authelia:
# - Authorization: /api/oidc/authorization
# - Token: /api/oidc/token
# - UserInfo: /api/oidc/userinfo
# - Introspection: /api/oidc/introspection
# - Revocation: /api/oidc/revocation
```

### Supported Flows
- Authorization Code Flow (recommended)
- Authorization Code Flow with PKCE
- Implicit Flow (not recommended)
- Hybrid Flow
- Client Credentials Flow
- Device Authorization Flow

### Claims and Scopes
```python
# Standard scopes supported by Authelia
AUTHELIA_SCOPES = [
    'openid',      # Required for OIDC
    'email',       # Email address
    'profile',     # Profile information
    'groups',      # Group membership
    'offline_access'  # Refresh tokens
]

# Custom claims configuration in Authelia
# Configure in authelia configuration.yml
```

## Testing Implementation

### Test Connection Function
```python
async def test_oidc_connection(settings: OIDCSettings) -> dict:
    """Test OIDC provider connectivity."""
    try:
        # Fetch discovery document
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.discovery_endpoint)
            discovery = response.json()

        return {
            'success': True,
            'issuer': discovery.get('issuer'),
            'authorization_endpoint': discovery.get('authorization_endpoint'),
            'token_endpoint': discovery.get('token_endpoint'),
            'userinfo_endpoint': discovery.get('userinfo_endpoint'),
            'jwks_uri': discovery.get('jwks_uri'),
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
```

## Migration Path

### Supporting Both Authentication Methods
1. Keep existing API key authentication intact
2. Add OIDC as optional authentication method
3. Use dependency injection to try methods in order
4. Migrate users gradually with dual support period
5. Eventually deprecate password auth if desired

### Database Schema Updates
```python
# Add OIDC fields to user model
class UserOIDCFields:
    oidc_sub: Optional[str] = None  # OIDC subject identifier
    oidc_provider: Optional[str] = None  # Provider name
    auth_method: str = 'local'  # 'local', 'oidc', 'api_key'
    linked_accounts: List[dict] = []  # Multiple OIDC providers
```

## Environment Configuration

### Required Environment Variables
```bash
# OIDC Configuration
OIDC_ENABLED=true
OIDC_CLIENT_ID=your-client-id
OIDC_CLIENT_SECRET=your-client-secret
OIDC_DISCOVERY_URL=https://auth.example.com/.well-known/openid-configuration
OIDC_REDIRECT_URI=https://app.example.com/auth/callback

# Session Configuration
SESSION_SECRET_KEY=generate-with-openssl-rand-hex-32
SESSION_COOKIE_SECURE=true  # Use HTTPS in production
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=lax

# Encryption for storing secrets
ENCRYPTION_KEY=generate-with-fernet-generate-key
```

This implementation provides a secure, scalable foundation for OIDC authentication that integrates smoothly with existing ClaudeLens patterns.
