"""Cost calculation service using LiteLLM."""
import logging
from typing import Any, Dict, Optional

from litellm import cost_calculator

logger = logging.getLogger(__name__)


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

            # Calculate total tokens
            prompt_tokens = input_tokens or 0
            completion_tokens = output_tokens or 0
            total_tokens = prompt_tokens + completion_tokens

            # Create a mock completion object for cost calculation
            completion: Dict[str, Any] = {
                "model": mapped_model,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
            }

            # Add cache tokens if available
            if cache_creation_input_tokens:
                completion["usage"][
                    "cache_creation_input_tokens"
                ] = cache_creation_input_tokens
                # Add cache creation tokens to total
                total_tokens += cache_creation_input_tokens
            if cache_read_input_tokens:
                completion["usage"]["cache_read_input_tokens"] = cache_read_input_tokens
                # Add cache read tokens to total
                total_tokens += cache_read_input_tokens

            # Update total_tokens with all token types
            completion["usage"]["total_tokens"] = total_tokens

            # Calculate cost using LiteLLM
            cost = cost_calculator.completion_cost(completion_response=completion)

            # LiteLLM sometimes returns negative costs when cache tokens are involved
            # This appears to be a bug where it subtracts the "savings" from caching
            # Ensure cost is never negative by recalculating manually
            if cost < 0:
                logger.warning(
                    f"LiteLLM returned negative cost ({cost:.6f}) for model {mapped_model} "
                    f"with cache tokens. Recalculating manually."
                )
                # Following ccusage's approach: calculate cost as sum of all token types
                # without any "savings" subtraction

                # Get model-specific pricing or use defaults
                # Default pricing based on Claude-3/4 models (per token, not per million)
                if "opus" in mapped_model.lower():
                    # Claude Opus pricing
                    input_rate = 0.000015  # $15 per million tokens
                    output_rate = 0.000075  # $75 per million tokens
                    cache_creation_rate = (
                        0.00001875  # $18.75 per million (25% more than input)
                    )
                    cache_read_rate = (
                        0.000001875  # $1.875 per million (90% less than input)
                    )
                else:
                    # Default to Sonnet pricing (cheaper)
                    input_rate = 0.000003  # $3 per million tokens
                    output_rate = 0.000015  # $15 per million tokens
                    cache_creation_rate = (
                        0.00000375  # $3.75 per million (25% more than input)
                    )
                    cache_read_rate = (
                        0.0000003  # $0.30 per million (90% less than input)
                    )

                # Calculate each component
                input_cost = (input_tokens or 0) * input_rate
                output_cost = (output_tokens or 0) * output_rate
                cache_write_cost = (
                    cache_creation_input_tokens or 0
                ) * cache_creation_rate
                cache_read_cost = (cache_read_input_tokens or 0) * cache_read_rate

                # Total cost is the sum of all components (no subtraction)
                cost = input_cost + output_cost + cache_write_cost + cache_read_cost

            return cost
        except Exception as e:
            logger.error(f"Error calculating cost for model {model}: {e}")
            return None

    @staticmethod
    def _map_model_name(model: str) -> str:
        """Map model names to LiteLLM format."""
        # Remove any provider prefix
        model = model.replace("anthropic/", "")

        # LiteLLM already has these model names directly, no need to map
        # Just return the model name as-is since LiteLLM recognizes them
        return model
