"""Pydantic schemas for AI generation requests and responses."""

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator


class GenerationType(str, Enum):
    """Type of metadata to generate."""

    NAME = "name"
    DESCRIPTION = "description"
    BOTH = "both"


class ContentOperation(str, Enum):
    """Type of content operation."""

    CREATE = "create"
    REFACTOR = "refactor"
    ENHANCE = "enhance"


class GenerateMetadataRequest(BaseModel):
    """Request schema for generating prompt metadata."""

    context: str = Field(..., min_length=10, max_length=5000)
    type: GenerationType
    requirements: Optional[str] = Field(None, max_length=1000)
    template_id: Optional[str] = None

    @field_validator("context")
    @classmethod
    def validate_context(cls, v: str) -> str:
        """Validate context is not empty."""
        if not v.strip():
            raise ValueError("Context cannot be empty")
        return v.strip()


class GenerateMetadataResponse(BaseModel):
    """Response schema for generated metadata."""

    name: Optional[str] = None
    description: Optional[str] = None
    tokens_used: int
    estimated_cost: float


class GenerateContentRequest(BaseModel):
    """Request schema for generating prompt content."""

    operation: ContentOperation
    requirements: str = Field(..., min_length=10, max_length=5000)
    existing_content: Optional[str] = None
    preserve_variables: bool = True
    template_id: Optional[str] = None

    @field_validator("requirements")
    @classmethod
    def validate_requirements(cls, v: str) -> str:
        """Validate requirements is not empty."""
        if not v.strip():
            raise ValueError("Requirements cannot be empty")
        return v.strip()

    @field_validator("existing_content")
    @classmethod
    def validate_existing_content(cls, v: Optional[str]) -> Optional[str]:
        """Validate existing content for refactor/enhance operations."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class GenerateContentResponse(BaseModel):
    """Response schema for generated content."""

    content: str
    variables_detected: list[str] = Field(default_factory=list)
    tokens_used: int
    estimated_cost: float
    operation: ContentOperation


class TestConnectionRequest(BaseModel):
    """Request schema for testing AI connection."""

    test_prompt: str = "Hello, this is a test."


class TestConnectionResponse(BaseModel):
    """Response schema for connection test."""

    success: bool
    message: str
    model: Optional[str] = None
    error: Optional[str] = None


class TokenCountRequest(BaseModel):
    """Request schema for counting tokens."""

    text: str
    model: str = "gpt-4"


class TokenCountResponse(BaseModel):
    """Response schema for token count."""

    token_count: int
    estimated_cost: float
    model: str


class GenerationStatsResponse(BaseModel):
    """Response schema for generation statistics."""

    total_generations: int
    total_tokens_used: int
    total_cost: float
    generations_by_operation: Dict[str, int]
    average_tokens_per_generation: float
    most_used_model: str
