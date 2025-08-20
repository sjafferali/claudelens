"""MongoDB models for generation templates."""

from datetime import datetime
from typing import Any, Optional

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


class GenerationTemplateInDB(BaseModel):
    """Generation template model for database storage."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None
    system_prompt: str
    user_prompt_template: str
    variables: list[str] = Field(default_factory=list)
    is_default: bool = False
    category: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.7
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }
