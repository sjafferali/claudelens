"""Import job model for tracking import operations."""

from datetime import UTC, datetime
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


class ImportJob(BaseModel):
    """Import job model for tracking import operations."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    status: Literal[
        "validating", "processing", "completed", "failed", "partial", "rolled_back"
    ] = "validating"
    file_id: str  # Reference to the uploaded file
    file_info: Dict[str, Any] = Field(default_factory=dict)
    field_mapping: Dict[str, str] = Field(default_factory=dict)
    conflict_resolution: Dict[str, Any] = Field(
        default_factory=lambda: {
            "default_strategy": "skip",
            "specific_resolutions": {},
        }
    )
    options: Dict[str, Any] = Field(
        default_factory=lambda: {
            "create_backup": True,
            "validate_references": True,
            "calculate_costs": True,
        }
    )
    progress: Dict[str, Any] = Field(
        default_factory=lambda: {
            "processed": 0,
            "total": 0,
            "percentage": 0,
            "current_item": None,
        }
    )
    statistics: Dict[str, Any] = Field(
        default_factory=lambda: {
            "imported": 0,
            "skipped": 0,
            "failed": 0,
            "merged": 0,
            "replaced": 0,
        }
    )
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    validation_warnings: List[Dict[str, Any]] = Field(default_factory=list)
    validation_errors: List[Dict[str, Any]] = Field(default_factory=list)
    backup_info: Optional[
        Dict[str, Any]
    ] = None  # Info about backup created before import
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration_seconds: Optional[int] = None

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
