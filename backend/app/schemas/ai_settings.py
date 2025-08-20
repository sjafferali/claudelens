"""Pydantic schemas for AI settings requests and responses."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, SecretStr, field_validator


class AISettingsUpdate(BaseModel):
    """Request schema for updating AI settings."""

    api_key: Optional[SecretStr] = None
    model: Optional[str] = Field(None, pattern="^gpt-[34].*")
    endpoint: Optional[str] = None
    enabled: Optional[bool] = None

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: Optional[str]) -> Optional[str]:
        """Validate model name."""
        if v is not None:
            allowed_models = [
                "gpt-4",
                "gpt-4-turbo",
                "gpt-4-turbo-preview",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
            ]
            if v not in allowed_models:
                raise ValueError(f"Model must be one of: {', '.join(allowed_models)}")
        return v

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v: Optional[str]) -> Optional[str]:
        """Validate endpoint URL."""
        if v is not None and v.strip():
            if not v.startswith(("http://", "https://")):
                raise ValueError("Endpoint must be a valid HTTP(S) URL")
        return v


class AISettingsResponse(BaseModel):
    """Response schema for AI settings."""

    id: str = Field(alias="_id")
    model: str
    endpoint: Optional[str] = None
    enabled: bool
    api_key_configured: bool  # Never expose the actual key
    created_at: datetime
    updated_at: datetime
    usage_stats: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class GenerationTemplateCreate(BaseModel):
    """Request schema for creating a generation template."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    system_prompt: str = Field(..., min_length=10, max_length=2000)
    user_prompt_template: str = Field(..., min_length=10, max_length=2000)
    variables: list[str] = Field(default_factory=list)
    is_default: bool = False
    category: Optional[str] = Field(None, max_length=50)
    max_tokens: int = Field(2000, ge=100, le=4000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)

    @field_validator("variables")
    @classmethod
    def validate_variables(cls, v: list[str]) -> list[str]:
        """Validate variable names."""
        for var in v:
            if not var.isidentifier():
                raise ValueError(f"Variable '{var}' is not a valid identifier")
        return v


class GenerationTemplateUpdate(BaseModel):
    """Request schema for updating a generation template."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    system_prompt: Optional[str] = Field(None, min_length=10, max_length=2000)
    user_prompt_template: Optional[str] = Field(None, min_length=10, max_length=2000)
    variables: Optional[list[str]] = None
    is_default: Optional[bool] = None
    category: Optional[str] = Field(None, max_length=50)
    max_tokens: Optional[int] = Field(None, ge=100, le=4000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)


class GenerationTemplateResponse(BaseModel):
    """Response schema for generation template."""

    id: str = Field(alias="_id")
    name: str
    description: Optional[str] = None
    system_prompt: str
    user_prompt_template: str
    variables: list[str]
    is_default: bool
    category: Optional[str] = None
    max_tokens: int
    temperature: float
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}
