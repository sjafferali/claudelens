"""AI service for OpenAI integration and prompt generation."""

import json
import re
import time
from typing import Any, Dict, List, Optional

import tiktoken
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.ai_config import ai_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.ai_settings import AISettingsInDB, GenerationLog
from app.schemas.ai_generation import (
    ContentOperation,
    GenerateContentRequest,
    GenerateContentResponse,
    GenerateMetadataRequest,
    GenerateMetadataResponse,
    GenerationType,
)


class AIService:
    """Service for AI-powered prompt generation and refinement."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize AI service."""
        self.db = db
        self.settings_collection = db.ai_settings
        self.logs_collection = db.generation_logs
        self.templates_collection = db.generation_templates

    def _calculate_cost(
        self, prompt_tokens: int, completion_tokens: int, model: str = "gpt-4"
    ) -> float:
        """Calculate estimated cost for token usage."""
        if "gpt-4" in model:
            prompt_cost = (prompt_tokens / 1000) * 0.03  # $0.03 per 1K tokens
            completion_cost = (completion_tokens / 1000) * 0.06  # $0.06 per 1K tokens
        else:  # gpt-3.5-turbo
            prompt_cost = (prompt_tokens / 1000) * 0.001  # $0.001 per 1K tokens
            completion_cost = (completion_tokens / 1000) * 0.002  # $0.002 per 1K tokens

        return round(prompt_cost + completion_cost, 6)

    async def _get_ai_settings(self) -> AISettingsInDB:
        """Get AI settings from database."""
        settings_doc = await self.settings_collection.find_one()
        if not settings_doc:
            raise NotFoundError("AI settings not configured")

        settings = AISettingsInDB(**settings_doc)
        if not settings.enabled:
            raise ValidationError("AI features are disabled")

        return settings

    async def _get_client(self) -> AsyncOpenAI:
        """Get configured OpenAI client with decrypted API key."""
        settings = await self._get_ai_settings()

        if not settings.api_key_encrypted:
            raise ValidationError("API key not configured")

        # Decrypt API key
        try:
            api_key = ai_settings.decrypt_api_key(settings.api_key_encrypted)
        except Exception:
            # If decryption fails, it's likely due to a changed encryption key
            raise ValidationError(
                "Failed to decrypt API key. This usually happens when the encryption key has changed. "
                "Please reconfigure your API key in the AI settings."
            )

        # Create client with optional custom endpoint
        if settings.endpoint or settings.base_url:
            base_url = settings.base_url or settings.endpoint
            return AsyncOpenAI(api_key=api_key, base_url=base_url)
        else:
            return AsyncOpenAI(api_key=api_key)

    def _count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens in text for the specified model."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding for unknown models
            encoding = tiktoken.get_encoding("cl100k_base")

        return len(encoding.encode(text))

    def _extract_variables(self, content: str) -> list[str]:
        """Extract variables from prompt content using {{variable}} syntax."""
        pattern = r"\{\{(\w+)\}\}"
        matches = re.findall(pattern, content)
        return list(set(matches))  # Return unique variables

    def _preserve_variables(self, original: str, generated: str) -> str:
        """Preserve variables from original content in generated content."""
        # Extract variables from original
        variables = self._extract_variables(original)

        # For each variable, ensure it exists in generated content
        for var in variables:
            var_pattern = f"{{{{{var}}}}}"
            if var_pattern not in generated:
                # Try to intelligently place the variable
                # This is a simple approach - could be enhanced
                generated = generated.replace(
                    f"{var}", var_pattern, 1
                )  # Replace first occurrence

        return generated

    async def _log_usage(
        self,
        operation: str,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        request_data: Dict[str, Any],
        response_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: int = 0,
    ) -> None:
        """Log AI generation usage for tracking and analytics."""
        total_tokens = prompt_tokens + completion_tokens
        estimated_cost = self._calculate_cost(prompt_tokens, completion_tokens, model)

        log = GenerationLog(
            operation=operation,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            request_data=request_data,
            response_data=response_data,
            error=error,
            duration_ms=duration_ms,
        )

        await self.logs_collection.insert_one(log.model_dump(by_alias=True))

        # Update usage stats in settings
        await self.settings_collection.update_one(
            {},
            {
                "$inc": {
                    "usage_stats.total_generations": 1,
                    "usage_stats.total_tokens": total_tokens,
                    "usage_stats.total_cost": estimated_cost,
                }
            },
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def generate_metadata(
        self, request: GenerateMetadataRequest
    ) -> GenerateMetadataResponse:
        """Generate prompt metadata (name and/or description) using AI."""
        start_time = time.time()
        settings = await self._get_ai_settings()

        # Check token limits
        prompt_tokens = self._count_tokens(request.context, settings.model)
        if prompt_tokens > 4000:
            raise ValidationError(
                f"Context too long: {prompt_tokens} tokens (max 4000)"
            )

        # Get template if specified
        template = None
        if request.template_id:
            template = await self.templates_collection.find_one(
                {"_id": ObjectId(request.template_id)}
            )

        # Prepare system prompt
        system_prompt = (
            template["system_prompt"]
            if template
            else """You are an expert at creating clear, concise metadata for prompts.
            Generate professional names and descriptions based on the provided context.
            Names should be 2-5 words, descriptions should be 1-2 sentences.
            Return valid JSON with 'name' and/or 'description' fields as requested."""
        )

        # Prepare user prompt
        user_prompt = f"Context: {request.context}"
        if request.requirements:
            user_prompt += f"\n\nAdditional requirements: {request.requirements}"

        if request.type == GenerationType.NAME:
            user_prompt += "\n\nGenerate only a 'name' field."
        elif request.type == GenerationType.DESCRIPTION:
            user_prompt += "\n\nGenerate only a 'description' field."
        else:  # BOTH
            user_prompt += "\n\nGenerate both 'name' and 'description' fields."

        try:
            client = await self._get_client()
            response = await client.chat.completions.create(
                model=settings.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=ai_settings.ai_default_temperature,
                max_tokens=500,
            )

            # Parse response
            message_content = response.choices[0].message.content or "{}"
            result = json.loads(message_content)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log usage
            usage = response.usage
            if usage:
                await self._log_usage(
                    operation="generate_metadata",
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    model=settings.model,
                    request_data=request.model_dump(),
                    response_data=result,
                    duration_ms=duration_ms,
                )

            # Calculate cost
            if usage:
                estimated_cost = ai_settings.calculate_cost(
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    settings.model,
                )
            else:
                estimated_cost = 0.0

            return GenerateMetadataResponse(
                name=result.get("name"),
                description=result.get("description"),
                tokens_used=usage.total_tokens if usage else 0,
                estimated_cost=estimated_cost,
            )

        except Exception as e:
            # Log error
            duration_ms = int((time.time() - start_time) * 1000)
            await self._log_usage(
                operation="generate_metadata",
                prompt_tokens=prompt_tokens,
                completion_tokens=0,
                model=settings.model,
                request_data=request.model_dump(),
                error=str(e),
                duration_ms=duration_ms,
            )
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def generate_content(
        self, request: GenerateContentRequest
    ) -> GenerateContentResponse:
        """Generate or refine prompt content using AI."""
        start_time = time.time()
        settings = await self._get_ai_settings()

        # Count tokens
        base_tokens = self._count_tokens(request.requirements, settings.model)
        if request.existing_content:
            base_tokens += self._count_tokens(request.existing_content, settings.model)

        if base_tokens > 6000:
            raise ValidationError(f"Input too long: {base_tokens} tokens (max 6000)")

        # Get template if specified
        template = None
        if request.template_id:
            template = await self.templates_collection.find_one(
                {"_id": ObjectId(request.template_id)}
            )

        # Prepare system prompt based on operation
        if request.operation == ContentOperation.CREATE:
            system_prompt = (
                template["system_prompt"]
                if template
                else """You are an expert prompt engineer. Create clear, effective prompts
                that guide AI models to produce high-quality outputs. Use {{variable}} syntax
                for any placeholders that users should fill in."""
            )
        elif request.operation == ContentOperation.REFACTOR:
            system_prompt = """You are an expert at refactoring prompts. Improve clarity,
            structure, and effectiveness while preserving the original intent.
            IMPORTANT: Maintain all {{variable}} placeholders exactly as they appear."""
        else:  # ENHANCE
            system_prompt = """You are an expert at enhancing prompts. Add detail,
            context, and improvements while preserving the core functionality.
            IMPORTANT: Maintain all {{variable}} placeholders exactly as they appear."""

        # Prepare user prompt
        user_prompt = f"Requirements: {request.requirements}"
        if request.existing_content:
            user_prompt += f"\n\nExisting content to {request.operation}:\n{request.existing_content}"
            if request.preserve_variables:
                variables = self._extract_variables(request.existing_content)
                if variables:
                    user_prompt += f"\n\nIMPORTANT: Preserve these variables: {', '.join(variables)}"

        try:
            client = await self._get_client()
            response = await client.chat.completions.create(
                model=settings.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=template["temperature"]
                if template
                else ai_settings.ai_default_temperature,
                max_tokens=template["max_tokens"]
                if template
                else ai_settings.ai_max_tokens,
            )

            generated_content = response.choices[0].message.content or ""

            # Preserve variables if requested and there was existing content
            if (
                request.preserve_variables
                and request.existing_content
                and request.operation != ContentOperation.CREATE
            ):
                generated_content = self._preserve_variables(
                    request.existing_content, generated_content
                )

            # Extract variables from final content
            variables_detected = self._extract_variables(generated_content)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log usage
            usage = response.usage
            if usage:
                await self._log_usage(
                    operation=f"generate_content_{request.operation}",
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    model=settings.model,
                    request_data=request.model_dump(),
                    response_data={"content": generated_content},
                    duration_ms=duration_ms,
                )

            # Calculate cost
            if usage:
                estimated_cost = ai_settings.calculate_cost(
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    settings.model,
                )
            else:
                estimated_cost = 0.0

            return GenerateContentResponse(
                content=generated_content,
                variables_detected=variables_detected,
                tokens_used=usage.total_tokens if usage else 0,
                estimated_cost=estimated_cost,
                operation=request.operation,
            )

        except Exception as e:
            # Log error
            duration_ms = int((time.time() - start_time) * 1000)
            await self._log_usage(
                operation=f"generate_content_{request.operation}",
                prompt_tokens=base_tokens,
                completion_tokens=0,
                model=settings.model,
                request_data=request.model_dump(),
                error=str(e),
                duration_ms=duration_ms,
            )
            raise

    async def test_connection(self, test_prompt: str = "Hello") -> Dict[str, Any]:
        """Test the AI connection and configuration."""
        try:
            settings = await self._get_ai_settings()

            # Check if API key is encrypted
            if not settings.api_key_encrypted:
                return {
                    "success": False,
                    "message": "API key not configured",
                    "error": "Please configure your API key in the AI settings",
                }

            # Try to get the client (which will decrypt the API key)
            try:
                client = await self._get_client()
            except ValidationError as ve:
                # Handle decryption failures specifically
                if "decrypt" in str(ve).lower():
                    return {
                        "success": False,
                        "message": "API key decryption failed",
                        "error": "The saved API key cannot be decrypted. Please reconfigure your API key in the AI settings.",
                    }
                raise

            # Make a simple test request
            response = await client.chat.completions.create(
                model=settings.model,
                messages=[{"role": "user", "content": test_prompt}],
                max_tokens=10,
            )

            return {
                "success": True,
                "message": "Connection successful",
                "model": settings.model,
                "response": response.choices[0].message.content,
            }

        except NotFoundError:
            return {
                "success": False,
                "message": "AI settings not configured",
                "error": "Please configure AI settings first",
            }
        except ValidationError as e:
            return {
                "success": False,
                "message": "Configuration error",
                "error": str(e),
            }
        except Exception as e:
            # Check if it's an API key error
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "unauthorized" in error_msg.lower():
                return {
                    "success": False,
                    "message": "Invalid API key",
                    "error": "The API key appears to be invalid. Please check your API key.",
                }
            return {
                "success": False,
                "message": "Connection failed",
                "error": error_msg,
            }

    async def count_tokens(self, text: str, model: str = "gpt-4") -> Dict[str, Any]:
        """Count tokens in text and estimate cost."""
        token_count = self._count_tokens(text, model)
        # Estimate as if it's all prompt tokens
        estimated_cost = self._calculate_cost(token_count, 0, model)

        return {
            "token_count": token_count,
            "estimated_cost": estimated_cost,
            "model": model,
        }

    async def get_settings(self) -> Optional[AISettingsInDB]:
        """Get AI settings from database."""
        settings_doc = await self.settings_collection.find_one()
        if settings_doc:
            return AISettingsInDB(**settings_doc)
        return None

    async def update_settings(
        self, settings_update: Dict[str, Any]
    ) -> Optional[AISettingsInDB]:
        """Update AI settings in database."""
        from datetime import UTC, datetime

        # Get existing settings or create new
        existing = await self.settings_collection.find_one()

        # Prepare update data
        update_data = {**settings_update, "updated_at": datetime.now(UTC)}

        # Handle API key encryption if provided
        if "api_key" in update_data and update_data["api_key"]:
            # Get the actual value from SecretStr if it's one
            api_key = update_data["api_key"]
            if hasattr(api_key, "get_secret_value"):
                api_key = api_key.get_secret_value()
            # Encrypt the API key
            update_data["api_key_encrypted"] = ai_settings.encrypt_api_key(api_key)
            del update_data["api_key"]  # Remove plain API key

        if existing:
            # Update existing
            await self.settings_collection.update_one(
                {"_id": existing["_id"]}, {"$set": update_data}
            )
            # Return updated document
            updated = await self.settings_collection.find_one({"_id": existing["_id"]})
        else:
            # Create new
            from datetime import UTC, datetime

            update_data["created_at"] = datetime.now(UTC)
            update_data["usage_stats"] = {}
            result = await self.settings_collection.insert_one(update_data)
            updated = await self.settings_collection.find_one(
                {"_id": result.inserted_id}
            )

        if updated:
            return AISettingsInDB(**updated)
        return None

    async def clear_settings(self) -> bool:
        """Clear AI settings from database."""
        result = await self.settings_collection.delete_many({})
        return result.deleted_count > 0

    async def get_generation_stats(self) -> Dict[str, Any]:
        """Get generation statistics."""
        # Aggregate stats from logs
        pipeline: List[Dict[str, Any]] = [
            {
                "$group": {
                    "_id": None,
                    "total_generations": {"$sum": 1},
                    "total_tokens": {"$sum": "$total_tokens"},
                    "total_cost": {"$sum": "$estimated_cost"},
                    "avg_tokens": {"$avg": "$total_tokens"},
                }
            }
        ]

        stats = await self.logs_collection.aggregate(pipeline).to_list(1)
        if not stats:
            return {
                "total_generations": 0,
                "total_tokens_used": 0,
                "total_cost": 0.0,
                "average_tokens_per_generation": 0.0,
                "generations_by_operation": {},
                "most_used_model": "gpt-4",
            }

        # Get operations breakdown
        ops_pipeline: List[Dict[str, Any]] = [
            {"$group": {"_id": "$operation", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        ops_stats = await self.logs_collection.aggregate(ops_pipeline).to_list(10)
        operations = {op["_id"]: op["count"] for op in ops_stats}

        # Get most used model
        model_pipeline: List[Dict[str, Any]] = [
            {"$group": {"_id": "$model", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1},
        ]
        model_stats = await self.logs_collection.aggregate(model_pipeline).to_list(1)
        most_used_model = model_stats[0]["_id"] if model_stats else "gpt-4"

        return {
            "total_generations": stats[0]["total_generations"],
            "total_tokens_used": stats[0]["total_tokens"],
            "total_cost": round(stats[0]["total_cost"], 4),
            "generations_by_operation": operations,
            "average_tokens_per_generation": round(stats[0]["avg_tokens"], 2),
            "most_used_model": most_used_model,
        }

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from OpenAI API."""
        try:
            client = await self._get_client()
            models_response = await client.models.list()

            # Filter and format models for chat/completion use
            chat_models = []
            for model in models_response.data:
                # Only include chat/completion models
                if any(
                    keyword in model.id
                    for keyword in ["gpt", "claude", "llama", "mistral"]
                ):
                    model_info = {
                        "id": model.id,
                        "name": self._format_model_name(model.id),
                        "provider": "openai",
                        "created": model.created,
                    }

                    # Add model-specific metadata
                    if "gpt-4" in model.id:
                        model_info["context_window"] = (
                            128000 if "turbo" in model.id else 8192
                        )
                        model_info["supports_vision"] = "vision" in model.id
                    elif "gpt-3.5" in model.id:
                        model_info["context_window"] = (
                            16385 if "16k" in model.id else 4096
                        )

                    chat_models.append(model_info)

            # Sort by name for consistent ordering
            chat_models.sort(key=lambda x: str(x.get("name", "")))
            return chat_models

        except Exception:
            # Return empty list on error - endpoint will provide fallback
            return []

    def _format_model_name(self, model_id: str) -> str:
        """Format model ID into a readable name."""
        # Keep the original model ID for clarity
        # This ensures each model can be uniquely identified in the dropdown
        return model_id
