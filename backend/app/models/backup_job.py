"""Backup job model for tracking backup operations."""

from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Literal, Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, GetCoreSchemaHandler
from pydantic_core import core_schema


class PyObjectId(ObjectId):
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


class BackupJob(BaseModel):
    """Backup job model for tracking backup operations."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    backup_id: Optional[str] = None  # Reference to backup once created
    user_id: str
    status: Literal[
        "queued", "processing", "completed", "failed", "cancelled"
    ] = "queued"
    type: Literal["full", "selective"]
    filters: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)
    progress: Dict[str, Any] = Field(
        default_factory=lambda: {
            "current": 0,
            "total": 0,
            "percentage": 0,
            "current_item": None,
            "message": "",
        }
    )
    statistics: Dict[str, Any] = Field(default_factory=dict)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC) + timedelta(days=30)
    )
    estimated_size_bytes: Optional[int] = None
    estimated_duration_seconds: Optional[int] = None

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class RestoreJob(BaseModel):
    """Restore job model for tracking restore operations."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    backup_id: str  # Reference to backup being restored
    user_id: str
    status: Literal[
        "queued", "validating", "processing", "completed", "failed", "cancelled"
    ] = "queued"
    mode: Literal["full", "selective", "merge"]
    target: Optional[Dict[str, Any]] = None
    options: Dict[str, Any] = Field(default_factory=dict)
    selections: Optional[Dict[str, Any]] = None
    conflict_resolution: Literal["skip", "overwrite", "rename", "merge"] = "skip"
    progress: Dict[str, Any] = Field(
        default_factory=lambda: {
            "current": 0,
            "total": 0,
            "percentage": 0,
            "current_collection": None,
            "message": "",
        }
    )
    validation_result: Optional[Dict[str, Any]] = None
    statistics: Dict[str, Any] = Field(default_factory=dict)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rollback_available: bool = False
    rollback_data: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
