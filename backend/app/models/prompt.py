"""Prompt and folder models for MongoDB."""

from datetime import UTC, datetime
from typing import Any, Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, GetCoreSchemaHandler
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    """Custom PyObjectId for MongoDB ObjectId validation."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
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
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)


class PromptVersionInDB(BaseModel):
    """Version history for prompts."""

    version: str  # Semantic version
    content: str
    variables: list[str]
    change_log: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), alias="createdAt"
    )
    created_by: str = Field(alias="createdBy")

    model_config = ConfigDict(populate_by_name=True)


class FolderInDB(BaseModel):
    """Folder for organizing prompts."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    parent_id: Optional[PyObjectId] = Field(None, alias="parentId")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), alias="createdAt"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), alias="updatedAt"
    )
    created_by: str = Field(alias="createdBy")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class PromptInDB(BaseModel):
    """Prompt template stored in database."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None
    content: str  # Template with {{variables}}
    variables: list[str] = []  # Extracted variable names
    tags: list[str] = []
    folder_id: Optional[PyObjectId] = Field(None, alias="folderId")
    version: str = "1.0.0"
    versions: list[PromptVersionInDB] = []

    # Sharing settings
    visibility: str = "private"  # private, team, public
    shared_with: list[str] = Field(default=[], alias="sharedWith")  # User IDs
    public_url: Optional[str] = Field(None, alias="publicUrl")

    # Statistics
    use_count: int = Field(0, alias="useCount")
    last_used_at: Optional[datetime] = Field(None, alias="lastUsedAt")
    avg_response_time: Optional[float] = Field(None, alias="avgResponseTime")
    success_rate: Optional[float] = Field(None, alias="successRate")

    # Metadata
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), alias="createdAt"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), alias="updatedAt"
    )
    created_by: str = Field(alias="createdBy")
    is_starred: bool = Field(False, alias="isStarred")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
