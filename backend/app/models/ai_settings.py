"""MongoDB models for AI settings and configuration."""

from datetime import datetime
from typing import Any, Dict, Optional

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


class AISettingsInDB(BaseModel):
    """AI settings model for database storage."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    api_key_encrypted: str  # Encrypted with app.core.security
    model: str = "gpt-4"
    endpoint: Optional[str] = None
    enabled: bool = False
    usage_stats: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


class GenerationTemplate(BaseModel):
    """Template model for AI generation patterns."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None
    system_prompt: str
    user_prompt_template: str
    variables: list[str] = Field(default_factory=list)
    is_default: bool = False
    category: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


class GenerationLog(BaseModel):
    """Log model for tracking AI generation usage."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    operation: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    request_data: Dict[str, Any]
    response_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }
