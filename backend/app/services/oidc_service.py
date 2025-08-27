"""OIDC authentication service."""

import logging
import secrets
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from authlib.integrations.starlette_client import OAuth, OAuthError  # type: ignore
from bson import ObjectId
from fastapi import HTTPException, Request
from jose import jwt  # type: ignore
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.ai_config import ai_settings
from app.models.oidc_settings import OIDCSettingsInDB
from app.models.user import UserInDB, UserRole
from app.schemas.oidc import OIDCUserInfo

logger = logging.getLogger(__name__)


class OIDCService:
    """Service for OIDC authentication operations."""

    def __init__(self) -> None:
        """Initialize OIDC service."""
        self.oauth = OAuth()
        self._configured = False
        self._settings: Optional[OIDCSettingsInDB] = None

    def _serialize_user_for_session(self, user: UserInDB) -> Dict[str, Any]:
        """Convert user model to JSON-serializable dict for session storage."""
        user_dict: Dict[str, Any] = {}

        # Manually convert each field to ensure proper serialization
        for field_name, field_value in user.__dict__.items():
            if isinstance(field_value, ObjectId):
                user_dict[field_name] = str(field_value)
            elif isinstance(field_value, datetime):
                user_dict[field_name] = field_value.isoformat()
            elif isinstance(field_value, list):
                # Handle list structures - convert datetime/ObjectId in nested objects
                serialized_list = []
                for item in field_value:
                    if hasattr(item, "model_dump"):
                        serialized_list.append(item.model_dump(mode="json"))
                    else:
                        serialized_list.append(item)
                user_dict[field_name] = serialized_list
            elif isinstance(field_value, dict):
                # Handle dict structures
                user_dict[field_name] = field_value
            elif hasattr(field_value, "value"):  # Handle Enums
                user_dict[field_name] = field_value.value
            else:
                user_dict[field_name] = field_value

        # Handle the _id field specifically
        if hasattr(user, "id"):
            user_dict["_id"] = str(user.id)
            user_dict["id"] = str(user.id)

        return user_dict

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
            logger.info(
                f"Configuring OIDC provider with discovery endpoint: {settings.discovery_endpoint}"
            )
            self.oauth.register(
                name="oidc_provider",
                server_metadata_url=settings.discovery_endpoint,
                client_id=settings.client_id,
                client_secret=client_secret,
                client_kwargs={"scope": " ".join(settings.scopes)},
            )
            self._configured = True
            logger.info("OIDC provider configured successfully")
        except Exception as e:
            self._configured = False
            logger.error(f"Failed to configure OIDC provider: {e}", exc_info=True)
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
            logger.error("OIDC not configured when attempting to initiate login")
            raise HTTPException(status_code=503, detail="OIDC not configured")

        # Generate state for CSRF protection
        state_token = secrets.token_urlsafe(32)
        request.session["oidc_state"] = state_token
        logger.info(f"Initiating OIDC login with state token: {state_token[:8]}...")
        logger.debug(f"Redirect URI: {redirect_uri}")

        # Get authorization URL
        try:
            client = self.oauth.oidc_provider
            authorization_response = await client.authorize_redirect(
                request,
                redirect_uri,
                state=request.session["oidc_state"],
                prompt="select_account",  # Force account selection
            )

            # Extract URL from response
            if hasattr(authorization_response, "headers"):
                # It's a RedirectResponse object
                location = authorization_response.headers.get("location")
                if location:
                    logger.info(f"Generated authorization URL: {location[:100]}...")
                    return str(location)
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="No location header in redirect response",
                    )
            elif hasattr(authorization_response, "url"):
                auth_url: str = str(authorization_response.url)
                logger.info(f"Generated authorization URL: {auth_url[:100]}...")
                return auth_url
            else:
                final_url: str = str(authorization_response)
                logger.info(f"Generated authorization URL: {final_url[:100]}...")
                return final_url
        except Exception as e:
            logger.error(f"Failed to initiate OIDC login: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Failed to initiate OIDC login: {str(e)}"
            )

    async def exchange_code_for_token(
        self,
        code: str,
        state: str,
        redirect_uri: str,
        request: Request,
        db: AsyncIOMotorDatabase,
    ) -> UserInDB:
        """Exchange authorization code for token and create/update user.

        This is called by the frontend after receiving the authorization code.
        """
        if not self._configured:
            logger.error("OIDC not configured when exchanging code")
            raise HTTPException(status_code=503, detail="OIDC not configured")

        logger.info("Exchanging authorization code for token")
        logger.debug(
            f"Code: {code[:8]}..., State: {state[:8]}..., Redirect URI: {redirect_uri}"
        )

        # Note: State validation should be done by the frontend since it manages the session
        # The frontend should store the state before redirecting and validate it when handling callback

        try:
            # Exchange authorization code for tokens directly
            client = self.oauth.oidc_provider

            # Get the token endpoint from the provider metadata
            metadata = await client.load_server_metadata()
            token_endpoint = metadata.get("token_endpoint")

            if not token_endpoint:
                logger.error("Token endpoint not found in provider metadata")
                raise HTTPException(
                    status_code=500,
                    detail="Token endpoint not found in provider metadata",
                )

            logger.info(f"Exchanging code at token endpoint: {token_endpoint}")

            # Check settings is not None
            if not self._settings:
                logger.error("Settings not loaded")
                raise HTTPException(status_code=503, detail="OIDC settings not loaded")

            # Prepare token request
            token_data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self._settings.client_id,
            }

            # Add client secret if configured
            if self._settings.client_secret_encrypted:
                try:
                    client_secret = ai_settings.decrypt_api_key(
                        self._settings.client_secret_encrypted
                    )
                    token_data["client_secret"] = client_secret
                except Exception:
                    logger.warning("Failed to decrypt client secret")

            # Exchange code for token
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    token_endpoint,
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
                token = response.json()

            logger.info("Successfully obtained access token")
            logger.debug(f"Token response keys: {list(token.keys())}")

            # Parse ID token or fetch user info
            user_info = None

            # First try to decode the ID token if present
            if "id_token" in token:
                try:
                    # Parse ID token (note: in production, this should verify the signature)
                    id_token_data = jwt.decode(
                        token["id_token"], options={"verify_signature": False}
                    )
                    user_info = id_token_data
                    logger.info("Parsed user info from ID token")
                except Exception as e:
                    logger.warning(f"Failed to parse ID token: {e}")

            # If no user info from ID token, fetch from userinfo endpoint
            if not user_info and "access_token" in token:
                userinfo_endpoint = metadata.get("userinfo_endpoint")
                if userinfo_endpoint:
                    logger.info(
                        f"Fetching user info from endpoint: {userinfo_endpoint}"
                    )
                    async with httpx.AsyncClient() as http_client:
                        userinfo_response = await http_client.get(
                            userinfo_endpoint,
                            headers={
                                "Authorization": f"Bearer {token['access_token']}"
                            },
                        )
                        userinfo_response.raise_for_status()
                        user_info = userinfo_response.json()
                        logger.info("Successfully fetched user info")

            if not user_info:
                logger.error("No user info available from token or userinfo endpoint")
                raise HTTPException(
                    status_code=500, detail="Failed to get user information"
                )

            logger.info(f"Got user info for sub: {user_info.get('sub')}")

            # Convert to OIDCUserInfo
            oidc_user_info = OIDCUserInfo(**user_info)

            # Get or create user
            user = await self.get_or_create_user(db, oidc_user_info)

            # Store token in session if needed
            request.session["oidc_token"] = token
            # Convert user to JSON-serializable dict for session storage
            user_dict = self._serialize_user_for_session(user)
            request.session["user"] = user_dict

            return user

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error during token exchange: {e.response.status_code} - {e.response.text}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange authorization code: {e.response.text}",
            )
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Authentication failed: {str(e)}"
            )

    async def handle_callback(
        self, request: Request, db: AsyncIOMotorDatabase
    ) -> UserInDB:
        """Handle OIDC callback and create/update user."""
        if not self._configured:
            logger.error("OIDC not configured when handling callback")
            raise HTTPException(status_code=503, detail="OIDC not configured")

        # Log callback parameters
        logger.info("Handling OIDC callback")
        logger.debug(f"Query params: {dict(request.query_params)}")
        logger.debug(f"Session keys: {list(request.session.keys())}")

        # Validate state parameter for CSRF protection
        state_param = request.query_params.get("state")
        session_state = request.session.get("oidc_state")
        logger.debug(f"State param: {state_param[:8] if state_param else None}...")
        logger.debug(
            f"Session state: {session_state[:8] if session_state else None}..."
        )

        if not state_param or not session_state or state_param != session_state:
            logger.error(
                f"State mismatch - param: {state_param[:8] if state_param else 'None'}..., "
                f"session: {session_state[:8] if session_state else 'None'}..."
            )
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        try:
            # Exchange authorization code for tokens
            logger.info("Exchanging authorization code for tokens")
            client = self.oauth.oidc_provider
            token = await client.authorize_access_token(request)
            logger.info("Successfully obtained access token")
            logger.debug(f"Token keys: {list(token.keys())}")

            # Parse ID token for user info
            user_info = token.get("userinfo")
            if not user_info:
                # Fetch from userinfo endpoint if not in token
                logger.info("Fetching user info from userinfo endpoint")
                user_info = await client.userinfo(token=token)
            logger.info(f"Got user info for sub: {user_info.get('sub')}")

            # Convert to OIDCUserInfo
            oidc_user_info = OIDCUserInfo(**user_info)

            # Get or create user
            user = await self.get_or_create_user(db, oidc_user_info)

            # Store user in session
            # Convert user to JSON-serializable dict for session storage
            user_dict = self._serialize_user_for_session(user)
            request.session["user"] = user_dict
            request.session["oidc_token"] = token

            # Clear state
            request.session.pop("oidc_state", None)

            return user

        except OAuthError as error:
            logger.error(f"OAuth error during callback: {error}", exc_info=True)
            raise HTTPException(status_code=400, detail=str(error))
        except Exception as e:
            logger.error(f"Unexpected error during callback: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Authentication failed: {str(e)}"
            )

    async def get_or_create_user(
        self, db: AsyncIOMotorDatabase, user_info: OIDCUserInfo
    ) -> UserInDB:
        """Get or create user from OIDC claims."""
        logger.info(f"Getting or creating user for OIDC sub: {user_info.sub}")

        # Check if user exists
        user = await db.users.find_one({"oidc_sub": user_info.sub})

        if not user:
            if not self._settings or not self._settings.auto_create_users:
                logger.warning(
                    f"User not found for sub {user_info.sub} and auto-creation disabled"
                )
                raise HTTPException(
                    status_code=403, detail="User auto-creation disabled"
                )

            logger.info(f"Creating new user for sub: {user_info.sub}")

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
            logger.info(f"Created new user: {username}")
        else:
            # Update last login
            logger.info(f"Updating last login for user: {user.get('username')}")
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
