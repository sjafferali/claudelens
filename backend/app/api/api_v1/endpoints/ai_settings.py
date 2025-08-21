"""API endpoints for AI configuration management."""

from fastapi import HTTPException

from app.api.dependencies import CommonDeps
from app.core.custom_router import APIRouter
from app.core.exceptions import NotFoundError
from app.schemas.ai_generation import (
    GenerationStatsResponse,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.schemas.ai_settings import (
    AISettingsResponse,
    AISettingsUpdate,
    ModelInfo,
    ModelsListResponse,
)

router = APIRouter()


@router.get("/", response_model=AISettingsResponse)
async def get_ai_settings(db: CommonDeps) -> AISettingsResponse:
    """Get current AI settings."""
    from datetime import datetime

    from app.services.ai_service import AIService

    service = AIService(db)
    settings = await service.get_settings()

    if not settings:
        # Return default settings when none exist
        now = datetime.utcnow()
        return AISettingsResponse(
            _id="default",
            model="gpt-4",
            endpoint=None,
            base_url=None,
            enabled=False,
            api_key_configured=False,
            max_tokens=4096,
            temperature=0.7,
            created_at=now,
            updated_at=now,
            usage_stats={},
        )

    # Convert to response schema (never expose raw API key)
    settings_dict = settings.model_dump(by_alias=True)
    settings_dict["_id"] = str(settings_dict["_id"])
    settings_dict["api_key_configured"] = bool(settings.api_key_encrypted)

    # Map base_url from endpoint if not present
    if "base_url" not in settings_dict and "endpoint" in settings_dict:
        settings_dict["base_url"] = settings_dict["endpoint"]

    # Ensure max_tokens and temperature are included
    if "max_tokens" not in settings_dict:
        settings_dict["max_tokens"] = 4096
    if "temperature" not in settings_dict:
        settings_dict["temperature"] = 0.7

    # Remove the actual API key from response
    if "api_key" in settings_dict:
        del settings_dict["api_key"]

    # Ensure datetime fields are serialized to ISO format strings
    if settings_dict.get("created_at"):
        settings_dict["created_at"] = settings_dict["created_at"].isoformat()
    if settings_dict.get("updated_at"):
        settings_dict["updated_at"] = settings_dict["updated_at"].isoformat()

    return AISettingsResponse(**settings_dict)


@router.put("/", response_model=AISettingsResponse)
async def update_ai_settings(
    settings_update: AISettingsUpdate, db: CommonDeps
) -> AISettingsResponse:
    """Update AI settings with encrypted API key storage."""
    from app.services.ai_service import AIService

    service = AIService(db)

    # Map base_url to endpoint for backward compatibility
    update_data = settings_update.model_dump(exclude_none=True)
    if "base_url" in update_data and update_data["base_url"]:
        update_data["endpoint"] = update_data["base_url"]
        # Keep base_url as well for storage

    # Update settings - the service handles encryption
    updated_settings = await service.update_settings(update_data)

    if not updated_settings:
        raise HTTPException(status_code=500, detail="Failed to update AI settings")

    # Convert to response schema (never expose raw API key)
    settings_dict = updated_settings.model_dump(by_alias=True)
    settings_dict["_id"] = str(settings_dict["_id"])
    settings_dict["api_key_configured"] = bool(updated_settings.api_key_encrypted)

    # Map base_url from endpoint if not present
    if "base_url" not in settings_dict and "endpoint" in settings_dict:
        settings_dict["base_url"] = settings_dict["endpoint"]

    # Ensure max_tokens and temperature are included
    if "max_tokens" not in settings_dict:
        settings_dict["max_tokens"] = 4096
    if "temperature" not in settings_dict:
        settings_dict["temperature"] = 0.7

    # Remove the actual API key from response
    if "api_key" in settings_dict:
        del settings_dict["api_key"]

    # Ensure datetime fields are serialized to ISO format strings
    if settings_dict.get("created_at"):
        settings_dict["created_at"] = settings_dict["created_at"].isoformat()
    if settings_dict.get("updated_at"):
        settings_dict["updated_at"] = settings_dict["updated_at"].isoformat()

    return AISettingsResponse(**settings_dict)


@router.post("/test", response_model=TestConnectionResponse)
async def test_ai_connection(
    request: TestConnectionRequest, db: CommonDeps
) -> TestConnectionResponse:
    """Test AI connection."""
    from app.services.ai_service import AIService

    service = AIService(db)

    try:
        result = await service.test_connection(request.test_prompt)
        return TestConnectionResponse(**result)
    except Exception as e:
        return TestConnectionResponse(
            success=False, message="Connection test failed", error=str(e)
        )


@router.get("/stats", response_model=GenerationStatsResponse)
async def get_generation_stats(db: CommonDeps) -> GenerationStatsResponse:
    """Get generation statistics."""
    from app.services.ai_service import AIService

    service = AIService(db)
    stats = await service.get_generation_stats()
    return GenerationStatsResponse(**stats)


@router.get("/models", response_model=ModelsListResponse)
async def get_available_models(db: CommonDeps) -> ModelsListResponse:
    """Get list of available AI models from OpenAI."""
    from app.services.ai_service import AIService

    service = AIService(db)

    try:
        models_data = await service.get_available_models()
        # Convert dict models to ModelInfo objects
        model_objects = [
            ModelInfo(**model) if isinstance(model, dict) else model
            for model in models_data
        ]
        return ModelsListResponse(models=model_objects)
    except Exception:
        # Return a fallback list if API call fails
        fallback_models = [
            ModelInfo(id="gpt-4", name="GPT-4", provider="openai"),
            ModelInfo(id="gpt-4-turbo", name="GPT-4 Turbo", provider="openai"),
            ModelInfo(id="gpt-3.5-turbo", name="GPT-3.5 Turbo", provider="openai"),
            ModelInfo(
                id="gpt-3.5-turbo-16k", name="GPT-3.5 Turbo 16K", provider="openai"
            ),
        ]
        return ModelsListResponse(models=fallback_models, is_fallback=True)


@router.delete("/", status_code=200)
async def clear_ai_settings(db: CommonDeps) -> dict:
    """Clear AI settings."""
    from app.services.ai_service import AIService

    service = AIService(db)

    try:
        deleted = await service.clear_settings()

        if not deleted:
            raise NotFoundError("AI Settings", "default")

        return {"message": "AI settings cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to clear AI settings: {str(e)}"
        )
