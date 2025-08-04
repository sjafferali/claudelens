"""Cost calculation service using LiteLLM."""
from typing import Any, Dict, Optional

from litellm import cost_calculator


class CostCalculationService:
    """Service for calculating message costs using LiteLLM."""

    @staticmethod
    def calculate_message_cost(
        model: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        cache_creation_input_tokens: Optional[int] = None,
        cache_read_input_tokens: Optional[int] = None,
    ) -> Optional[float]:
        """Calculate cost for a message based on token usage.

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
            # Map model names to LiteLLM format
            mapped_model = CostCalculationService._map_model_name(model)

            # Create a mock completion object for cost calculation
            completion: Dict[str, Any] = {
                "model": mapped_model,
                "usage": {
                    "prompt_tokens": input_tokens or 0,
                    "completion_tokens": output_tokens or 0,
                },
            }

            # Add cache tokens if available
            if cache_creation_input_tokens:
                completion["usage"][
                    "cache_creation_input_tokens"
                ] = cache_creation_input_tokens
            if cache_read_input_tokens:
                completion["usage"]["cache_read_input_tokens"] = cache_read_input_tokens

            # Calculate cost using LiteLLM
            cost = cost_calculator.completion_cost(completion_response=completion)

            return cost
        except Exception as e:
            print(f"Error calculating cost for model {model}: {e}")
            return None

    @staticmethod
    def _map_model_name(model: str) -> str:
        """Map model names to LiteLLM format."""
        # Remove any provider prefix
        model = model.replace("anthropic/", "")

        # LiteLLM already has these model names directly, no need to map
        # Just return the model name as-is since LiteLLM recognizes them
        return model
