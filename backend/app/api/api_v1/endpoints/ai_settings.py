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
from app.schemas.ai_settings import AISettingsResponse, AISettingsUpdate

router = APIRouter()


@router.get("/", response_model=AISettingsResponse)
async def get_ai_settings(db: CommonDeps) -> AISettingsResponse:
    """Get current AI settings."""
    from app.services.ai_service import AIService

    service = AIService(db)
    settings = await service.get_settings()

    if not settings:
        raise NotFoundError("AI Settings", "default")

    # Convert to response schema (never expose raw API key)
    settings_dict = settings.model_dump(by_alias=True)
    settings_dict["_id"] = str(settings_dict["_id"])
    settings_dict["api_key_configured"] = bool(settings.api_key_encrypted)

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

    # Update settings - the service handles encryption
    updated_settings = await service.update_settings(
        settings_update.model_dump(exclude_none=True)
    )

    if not updated_settings:
        raise HTTPException(status_code=500, detail="Failed to update AI settings")

    # Convert to response schema (never expose raw API key)
    settings_dict = updated_settings.model_dump(by_alias=True)
    settings_dict["_id"] = str(settings_dict["_id"])
    settings_dict["api_key_configured"] = bool(updated_settings.api_key_encrypted)

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
