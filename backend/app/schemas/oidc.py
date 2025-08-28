"""OIDC schemas for request/response models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OIDCSettingsBase(BaseModel):
    """Base OIDC settings schema."""

    enabled: bool = Field(False, description="Enable OIDC authentication")
    client_id: str = Field("", description="OIDC client ID")
    discovery_endpoint: str = Field("", description="OIDC discovery URL")
    redirect_uri: str = Field("", description="Callback URL")
    scopes: List[str] = Field(
        default_factory=lambda: ["openid", "email", "profile"],
        description="OIDC scopes to request",
    )
    auto_create_users: bool = Field(
        True, description="Auto-create users on first login"
    )
    default_role: str = Field("user", description="Default role for new users")

    @field_validator("discovery_endpoint", "redirect_uri")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Must be a valid HTTP(S) URL")
        return v


class OIDCSettingsCreate(OIDCSettingsBase):
    """Schema for creating OIDC settings."""

    client_secret: Optional[str] = Field(None, description="OIDC client secret")


class OIDCSettingsUpdate(OIDCSettingsBase):
    """Schema for updating OIDC settings."""

    client_secret: Optional[str] = Field(None, description="OIDC client secret")


class OIDCSettingsResponse(OIDCSettingsBase):
    """Schema for OIDC settings response."""

    id: str = Field(..., alias="_id")
    api_key_configured: bool = Field(
        False, description="Whether client secret is configured"
    )
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class OIDCTestConnectionRequest(BaseModel):
    """Request schema for testing OIDC connection."""

    discovery_endpoint: Optional[str] = Field(
        None, description="Override discovery endpoint for testing"
    )


class OIDCTestConnectionResponse(BaseModel):
    """Response schema for OIDC connection test."""

    success: bool
    message: str
    issuer: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    error: Optional[str] = None


class OIDCUserInfo(BaseModel):
    """OIDC user information from ID token or userinfo endpoint."""

    sub: str = Field(..., description="Subject identifier")
    email: Optional[str] = None
    email_verified: Optional[bool] = False
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    groups: Optional[List[str]] = Field(default_factory=list)
    # Standard OIDC claims that might contain username
    preferred_username: Optional[str] = None
    nickname: Optional[str] = None
    # Authelia might provide username in profile
    username: Optional[str] = None
