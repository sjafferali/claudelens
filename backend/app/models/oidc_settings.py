"""MongoDB models for OIDC settings."""

from datetime import datetime
from typing import Any, List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    """Custom ObjectId for Pydantic models."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        """Get Pydantic core schema for PyObjectId."""
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema(
                    [
                        core_schema.str_schema(),
                        core_schema.no_info_plain_validator_function(cls.validate),
                    ]
                ),
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x),
                return_schema=core_schema.str_schema(),
            ),
        )

    @classmethod
    def validate(cls, v: Any) -> ObjectId:
        """Validate ObjectId."""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")


class OIDCSettingsInDB(BaseModel):
    """OIDC provider configuration stored in database."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    enabled: bool = Field(False, description="Enable OIDC authentication")
    client_id: str = Field("", description="OIDC client ID")
    client_secret_encrypted: str = Field("", description="Encrypted client secret")
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }
