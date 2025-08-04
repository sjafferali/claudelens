"""Cost calculation service using direct pricing data."""
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

# LiteLLM pricing URL (same as ccusage uses)
LITELLM_PRICING_URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"


class CostCalculationService:
    """Service for calculating message costs using direct pricing data.

    This implementation follows ccusage's approach:
    - Fetches pricing data directly from LiteLLM's JSON
    - Calculates costs manually without using cost_calculator
    - Avoids the negative cost bug entirely
    """

    _pricing_cache: Optional[Dict[str, Any]] = None

    @classmethod
    async def fetch_pricing_data(cls) -> Dict[str, Any]:
        """Fetch pricing data from LiteLLM, with caching."""
        if cls._pricing_cache is not None:
            return cls._pricing_cache

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(LITELLM_PRICING_URL)
                response.raise_for_status()
                cls._pricing_cache = response.json()
                logger.info(
                    f"Fetched pricing data for {len(cls._pricing_cache)} models"
                )
                return cls._pricing_cache
        except Exception as e:
            logger.error(f"Failed to fetch LiteLLM pricing data: {e}")
            # Return empty dict so calculations can fall back to defaults
            return {}

    @staticmethod
    def calculate_message_cost(
        model: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        cache_creation_input_tokens: Optional[int] = None,
        cache_read_input_tokens: Optional[int] = None,
    ) -> Optional[float]:
        """Calculate cost for a message based on token usage.

        This implementation follows ccusage's approach:
        - Direct calculation without LiteLLM's cost_calculator
        - No negative costs bug
        - Simple sum of all token costs

        Args:
            model: The model name (e.g., 'claude-3-5-sonnet-20241022')
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_creation_input_tokens: Number of cache creation tokens
            cache_read_input_tokens: Number of cache read tokens

        Returns:
            Cost in USD or None if calculation fails
        """
        if not model or (not input_tokens and not output_tokens):
            return None

        try:
            # Map model names to match LiteLLM format
            mapped_model = CostCalculationService._map_model_name(model)

            # Get pricing rates for this model
            pricing = CostCalculationService._get_model_pricing(mapped_model)

            # Calculate cost as simple sum of all components
            cost = 0.0

            # Input tokens
            if input_tokens and pricing.get("input_cost_per_token"):
                cost += input_tokens * pricing["input_cost_per_token"]

            # Output tokens
            if output_tokens and pricing.get("output_cost_per_token"):
                cost += output_tokens * pricing["output_cost_per_token"]

            # Cache creation tokens
            if cache_creation_input_tokens and pricing.get(
                "cache_creation_input_token_cost"
            ):
                cost += (
                    cache_creation_input_tokens
                    * pricing["cache_creation_input_token_cost"]
                )

            # Cache read tokens
            if cache_read_input_tokens and pricing.get("cache_read_input_token_cost"):
                cost += cache_read_input_tokens * pricing["cache_read_input_token_cost"]

            return cost

        except Exception as e:
            logger.error(f"Error calculating cost for model {model}: {e}")
            return None

    @staticmethod
    def _map_model_name(model: str) -> str:
        """Map model names to LiteLLM format."""
        # Remove any provider prefix
        model = model.replace("anthropic/", "")

        # LiteLLM uses specific naming patterns
        # No need for complex mapping - LiteLLM recognizes most variations
        return model

    @staticmethod
    def _get_model_pricing(model: str) -> Dict[str, float]:
        """Get pricing rates for a specific model.

        Returns pricing in cost per token (not per million).
        Falls back to default rates if model not found.
        """
        # Default pricing based on model type
        if "opus" in model.lower():
            # Claude Opus pricing (per token, not per million)
            return {
                "input_cost_per_token": 0.000015,  # $15 per million
                "output_cost_per_token": 0.000075,  # $75 per million
                "cache_creation_input_token_cost": 0.00001875,  # $18.75 per million
                "cache_read_input_token_cost": 0.000001875,  # $1.875 per million
            }
        else:
            # Default to Sonnet pricing (per token, not per million)
            return {
                "input_cost_per_token": 0.000003,  # $3 per million
                "output_cost_per_token": 0.000015,  # $15 per million
                "cache_creation_input_token_cost": 0.00000375,  # $3.75 per million
                "cache_read_input_token_cost": 0.0000003,  # $0.30 per million
            }

    @classmethod
    async def get_model_pricing_async(cls, model: str) -> Dict[str, float]:
        """Get pricing for a model, attempting to use fetched data first.

        This async version tries to use real pricing data from LiteLLM's JSON,
        falling back to defaults if not available.
        """
        mapped_model = cls._map_model_name(model)

        # Try to get pricing from fetched data
        pricing_data = await cls.fetch_pricing_data()

        if mapped_model in pricing_data:
            model_data = pricing_data[mapped_model]
            # Convert from the format in LiteLLM's JSON to our format
            pricing = {}

            # Standard fields
            if "input_cost_per_token" in model_data:
                pricing["input_cost_per_token"] = model_data["input_cost_per_token"]
            if "output_cost_per_token" in model_data:
                pricing["output_cost_per_token"] = model_data["output_cost_per_token"]

            # Cache fields (may have different names in the JSON)
            if "cache_creation_input_token_cost" in model_data:
                pricing["cache_creation_input_token_cost"] = model_data[
                    "cache_creation_input_token_cost"
                ]
            if "cache_read_input_token_cost" in model_data:
                pricing["cache_read_input_token_cost"] = model_data[
                    "cache_read_input_token_cost"
                ]

            # Only return if we have at least basic pricing
            if pricing.get("input_cost_per_token") and pricing.get(
                "output_cost_per_token"
            ):
                logger.debug(f"Using fetched pricing for model {mapped_model}")
                return pricing

        # Fall back to default pricing
        logger.debug(f"Using default pricing for model {mapped_model}")
        return cls._get_model_pricing(mapped_model)
