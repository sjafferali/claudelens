"""Import operation schemas."""

from typing import Any, Dict, List, Literal, Optional

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ValidateImportRequest(BaseModel):
    """Request schema for validating an import file."""

    file: UploadFile
    options: Optional[Dict[str, Any]] = Field(default_factory=lambda: {"dryRun": True})


class ValidateImportResponse(BaseModel):
    """Response schema for import file validation."""

    file_id: str = Field(alias="fileId")
    valid: bool
    format: str
    file_info: Dict[str, Any] = Field(alias="fileInfo")
    field_mapping: Dict[str, Any] = Field(alias="fieldMapping")
    validation_warnings: List[Dict[str, Any]] = Field(
        default_factory=list, alias="validationWarnings"
    )
    validation_errors: List[Dict[str, Any]] = Field(
        default_factory=list, alias="validationErrors"
    )

    model_config = ConfigDict(populate_by_name=True)


class CheckConflictsRequest(BaseModel):
    """Request schema for checking import conflicts."""

    file_id: str = Field(alias="fileId")
    field_mapping: Dict[str, str] = Field(alias="fieldMapping")

    model_config = ConfigDict(populate_by_name=True)


class ConflictItem(BaseModel):
    """Schema for a single conflict item."""

    existing_id: str = Field(alias="existingId")
    import_id: str = Field(alias="importId")
    title: str
    existing_data: Dict[str, Any] = Field(alias="existingData")
    import_data: Dict[str, Any] = Field(alias="importData")
    suggested_action: Literal["skip", "replace", "merge"] = Field(
        alias="suggestedAction"
    )

    model_config = ConfigDict(populate_by_name=True)


class ConflictsResponse(BaseModel):
    """Response schema for import conflicts check."""

    conflicts_count: int = Field(alias="conflictsCount")
    conflicts: List[ConflictItem]

    model_config = ConfigDict(populate_by_name=True)


class ExecuteImportRequest(BaseModel):
    """Request schema for executing an import."""

    file_id: str = Field(alias="fileId")
    field_mapping: Dict[str, str] = Field(alias="fieldMapping")
    conflict_resolution: Dict[str, Any] = Field(alias="conflictResolution")
    options: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "createBackup": True,
            "validateReferences": True,
            "calculateCosts": True,
        }
    )

    @field_validator("conflict_resolution", mode="before")
    @classmethod
    def validate_conflict_resolution(cls, v: Any) -> Dict[str, Any]:
        """Validate conflict resolution settings."""
        if not isinstance(v, dict):
            raise ValueError("conflict_resolution must be a dictionary")
        if "defaultStrategy" not in v:
            raise ValueError("defaultStrategy is required in conflict_resolution")
        if v["defaultStrategy"] not in ["skip", "replace", "merge"]:
            raise ValueError("defaultStrategy must be one of: skip, replace, merge")
        return v

    model_config = ConfigDict(populate_by_name=True)


class ExecuteImportResponse(BaseModel):
    """Response schema for import execution."""

    job_id: str = Field(alias="jobId")
    status: Literal["processing"]
    estimated_duration_seconds: int = Field(alias="estimatedDurationSeconds")

    model_config = ConfigDict(populate_by_name=True)


class ImportProgressResponse(BaseModel):
    """Response schema for import progress."""

    job_id: str = Field(alias="jobId")
    status: Literal["processing", "completed", "failed", "partial"]
    progress: Dict[str, Any]
    statistics: Dict[str, Any]
    errors: Optional[List[Dict[str, Any]]] = None
    completed_at: Optional[str] = Field(None, alias="completedAt")

    model_config = ConfigDict(populate_by_name=True)


class RollbackResponse(BaseModel):
    """Response schema for import rollback."""

    job_id: str = Field(alias="jobId")
    status: Literal["rolled_back"]
    items_reverted: int = Field(alias="itemsReverted")
    message: str

    model_config = ConfigDict(populate_by_name=True)


class ImportFileMetadata(BaseModel):
    """Metadata for an uploaded import file."""

    path: str
    size: int
    checksum: str
    filename: str
    format: Optional[str] = None
    uploaded_at: str = Field(alias="uploadedAt")
    expires_at: str = Field(alias="expiresAt")

    model_config = ConfigDict(populate_by_name=True)
