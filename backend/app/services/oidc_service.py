"""OIDC authentication service."""

import secrets
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.ai_config import ai_settings
from app.models.oidc_settings import OIDCSettingsInDB
from app.models.user import UserInDB, UserRole
from app.schemas.oidc import OIDCUserInfo


class OIDCService:
    """Service for OIDC authentication operations."""

    def __init__(self) -> None:
        """Initialize OIDC service."""
        self.oauth = OAuth()
        self._configured = False
        self._settings: Optional[OIDCSettingsInDB] = None

    async def load_settings(
        self, db: AsyncIOMotorDatabase
    ) -> Optional[OIDCSettingsInDB]:
        """Load OIDC settings from database."""
        settings_doc = await db.oidc_settings.find_one()
        if settings_doc:
            self._settings = OIDCSettingsInDB(**settings_doc)
            if self._settings.enabled and self._settings.client_id:
                await self.configure_provider(self._settings)
            return self._settings
        return None

    async def save_settings(
        self, db: AsyncIOMotorDatabase, settings: OIDCSettingsInDB
    ) -> OIDCSettingsInDB:
        """Save OIDC settings to database."""
        settings.updated_at = datetime.utcnow()

        # Check if settings exist
        existing = await db.oidc_settings.find_one()
        if existing:
            # Update existing settings
            await db.oidc_settings.replace_one(
                {"_id": existing["_id"]},
                settings.model_dump(by_alias=True, exclude={"id"}),
            )
            settings.id = existing["_id"]
        else:
            # Create new settings
            result = await db.oidc_settings.insert_one(
                settings.model_dump(by_alias=True, exclude={"id"})
            )
            settings.id = result.inserted_id

        self._settings = settings
        if settings.enabled and settings.client_id:
            await self.configure_provider(settings)
        return settings

    async def configure_provider(self, settings: OIDCSettingsInDB) -> None:
        """Configure OIDC provider from settings."""
        if not settings.enabled or not settings.client_id:
            self._configured = False
            return

        # Decrypt client secret
        client_secret = ""
        if settings.client_secret_encrypted:
            try:
                client_secret = ai_settings.decrypt_api_key(
                    settings.client_secret_encrypted
                )
            except Exception:
                # If decryption fails, treat as empty
                client_secret = ""

        # Register OIDC provider with discovery
        try:
            self.oauth.register(
                name="oidc_provider",
                server_metadata_url=settings.discovery_endpoint,
                client_id=settings.client_id,
                client_secret=client_secret,
                client_kwargs={"scope": " ".join(settings.scopes)},
            )
            self._configured = True
        except Exception as e:
            self._configured = False
            raise HTTPException(
                status_code=500, detail=f"Failed to configure OIDC provider: {str(e)}"
            )

    def encrypt_client_secret(self, client_secret: str) -> str:
        """Encrypt client secret for storage."""
        if not client_secret:
            return ""
        return ai_settings.encrypt_api_key(client_secret)

    async def test_connection(
        self, discovery_endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Test OIDC provider connectivity."""
        endpoint = discovery_endpoint or (
            self._settings.discovery_endpoint if self._settings else None
        )

        if not endpoint:
            return {
                "success": False,
                "message": "No discovery endpoint configured",
                "error": "Missing discovery endpoint",
            }

        try:
            # Fetch discovery document
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                discovery = response.json()

            return {
                "success": True,
                "message": "Successfully connected to OIDC provider",
                "issuer": discovery.get("issuer"),
                "authorization_endpoint": discovery.get("authorization_endpoint"),
                "token_endpoint": discovery.get("token_endpoint"),
                "userinfo_endpoint": discovery.get("userinfo_endpoint"),
                "jwks_uri": discovery.get("jwks_uri"),
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "message": f"HTTP error: {e.response.status_code}",
                "error": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "message": "Failed to connect to OIDC provider",
                "error": str(e),
            }

    async def initiate_login(self, request: Request, redirect_uri: str) -> str:
        """Initiate OIDC authentication flow."""
        if not self._configured:
            raise HTTPException(status_code=503, detail="OIDC not configured")

        # Generate state for CSRF protection
        request.session["oidc_state"] = secrets.token_urlsafe(32)

        # Get authorization URL
        client = self.oauth.oidc_provider
        authorization_url = await client.authorize_redirect(
            request,
            redirect_uri,
            state=request.session["oidc_state"],
            prompt="select_account",  # Force account selection
        )
        return (
            str(authorization_url.url)
            if hasattr(authorization_url, "url")
            else str(authorization_url)
        )

    async def handle_callback(
        self, request: Request, db: AsyncIOMotorDatabase
    ) -> UserInDB:
        """Handle OIDC callback and create/update user."""
        if not self._configured:
            raise HTTPException(status_code=503, detail="OIDC not configured")

        # Validate state parameter for CSRF protection
        state_param = request.query_params.get("state")
        session_state = request.session.get("oidc_state")
        if not state_param or not session_state or state_param != session_state:
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        try:
            # Exchange authorization code for tokens
            client = self.oauth.oidc_provider
            token = await client.authorize_access_token(request)

            # Parse ID token for user info
            user_info = token.get("userinfo")
            if not user_info:
                # Fetch from userinfo endpoint if not in token
                user_info = await client.userinfo(token=token)

            # Convert to OIDCUserInfo
            oidc_user_info = OIDCUserInfo(**user_info)

            # Get or create user
            user = await self.get_or_create_user(db, oidc_user_info)

            # Store user in session
            request.session["user"] = user.model_dump(mode="json")
            request.session["oidc_token"] = token

            # Clear state
            request.session.pop("oidc_state", None)

            return user

        except OAuthError as error:
            raise HTTPException(status_code=400, detail=str(error))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Authentication failed: {str(e)}"
            )

    async def get_or_create_user(
        self, db: AsyncIOMotorDatabase, user_info: OIDCUserInfo
    ) -> UserInDB:
        """Get or create user from OIDC claims."""
        # Check if user exists
        user = await db.users.find_one({"oidc_sub": user_info.sub})

        if not user:
            if not self._settings or not self._settings.auto_create_users:
                raise HTTPException(
                    status_code=403, detail="User auto-creation disabled"
                )

            # Create new user from OIDC claims
            username = (
                user_info.email.split("@")[0]
                if user_info.email
                else f"user_{user_info.sub[:8]}"
            )

            # Check if username already exists and make it unique
            existing = await db.users.find_one({"username": username})
            if existing:
                username = f"{username}_{user_info.sub[:6]}"

            user_data: Dict[str, Any] = {
                "oidc_sub": user_info.sub,
                "oidc_provider": self._settings.discovery_endpoint,
                "email": user_info.email or f"{username}@oidc.local",
                "email_verified": user_info.email_verified,
                "username": username,
                "full_name": user_info.name
                or f"{user_info.given_name or ''} {user_info.family_name or ''}".strip(),
                "role": UserRole(self._settings.default_role),
                "auth_method": "oidc",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
                "is_active": True,
                "api_keys": [],
                "project_count": 0,
                "session_count": 0,
                "message_count": 0,
                "total_disk_usage": 0,
            }

            result = await db.users.insert_one(user_data)
            user = await db.users.find_one({"_id": result.inserted_id})
        else:
            # Update last login
            await db.users.update_one(
                {"_id": user["_id"]}, {"$set": {"last_login": datetime.utcnow()}}
            )

        return UserInDB(**user) if user else UserInDB(**{})  # type: ignore

    async def logout(self, request: Request) -> None:
        """Logout user from OIDC session."""
        # Clear session data
        request.session.clear()

    def is_configured(self) -> bool:
        """Check if OIDC is configured and enabled."""
        return (
            self._configured and self._settings is not None and self._settings.enabled
        )


# Singleton instance
oidc_service = OIDCService()
