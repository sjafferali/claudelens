# Cost Calculations

This document explains how ClaudeLens calculates usage costs for Claude conversations and provides guidelines for adding support for new Claude models.

## Overview

ClaudeLens calculates costs for Claude API usage based on token consumption across different token types:
- **Input tokens**: Regular prompt tokens
- **Output tokens**: Response/completion tokens
- **Cache creation tokens**: Tokens written to the prompt cache
- **Cache read tokens**: Tokens read from the prompt cache

## Cost Calculation Flow

### 1. Data Source
Claude's JSONL export files contain token usage data but **do not include pre-calculated costs**. Each message includes a `usage` object with token counts:

```json
{
  "message": {
    "usage": {
      "input_tokens": 1000,
      "output_tokens": 500,
      "cache_creation_input_tokens": 200,
      "cache_read_input_tokens": 300
    }
  }
}
```

### 2. Cost Calculation During Ingestion

When syncing data, the backend automatically calculates costs:

1. **Checks for existing `costUsd` field**: If present (from manual calculation), uses it
2. **Calculates from token usage**: If no `costUsd`, calculates based on model and token counts
3. **Stores calculated cost**: Saves the cost in MongoDB as a `Decimal128` field

### 3. Calculation Method

The cost calculation follows the same approach as [ccusage](https://github.com/ryoppippi/ccusage):

```python
# Direct calculation without LiteLLM's cost_calculator
cost = (
    input_tokens * input_cost_per_token +
    output_tokens * output_cost_per_token +
    cache_creation_tokens * cache_creation_cost_per_token +
    cache_read_tokens * cache_read_cost_per_token
)
```

This approach:
- Fetches pricing data directly from [LiteLLM's pricing JSON](https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json)
- Calculates costs manually as a simple sum of tokens × rates
- Avoids the negative cost bug entirely (no subtraction of "savings")
- Provides complete control over the calculation
- Caches pricing data for performance

### 4. Pricing Rates

Current Claude model pricing (per million tokens):

#### Claude Opus Models
- Input: $15.00
- Output: $75.00
- Cache write: $18.75 (25% more than input)
- Cache read: $1.875 (90% less than input)

#### Claude Sonnet Models
- Input: $3.00
- Output: $15.00
- Cache write: $3.75 (25% more than input)
- Cache read: $0.30 (90% less than input)

## Implementation Details

### Why We Don't Use LiteLLM's cost_calculator
While LiteLLM provides a `cost_calculator.completion_cost()` function, it has a known bug where it returns negative costs when cache tokens are present. This appears to be because it subtracts "savings" from using cached tokens.

Instead, we follow ccusage's approach of fetching pricing data directly and calculating costs manually. This completely avoids the negative cost bug and gives us full control over the calculation.

## Adding Support for New Claude Models

When Anthropic releases new Claude models, follow these steps:

### 1. Verify Pricing Data Availability

First, check if LiteLLM has pricing data for the new model:

```bash
# Check LiteLLM's model pricing database
curl https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json | jq 'keys[] | select(contains("claude"))'
```

If the model isn't listed, you'll need to add default pricing in the fallback method (see step 3).

### 2. Update Model Name Mapping

Edit `backend/app/services/cost_calculation.py` in the `_map_model_name` method:

```python
@staticmethod
def _map_model_name(model: str) -> str:
    """Map model names to LiteLLM format."""
    # Remove any provider prefix
    model = model.replace("anthropic/", "")

    # Add any new model name mappings here
    # Example: Map "claude-3.5-sonnet" to "claude-3-5-sonnet"

    return model
```

### 3. Add Pricing Fallback

If LiteLLM doesn't have the model in their pricing JSON yet, add default pricing in the `_get_model_pricing` method:

```python
@staticmethod
def _get_model_pricing(model: str) -> Dict[str, float]:
    """Get pricing rates for a specific model."""
    if "opus" in model.lower():
        # Opus pricing (per token)
        return {
            "input_cost_per_token": 0.000015,  # $15 per million
            "output_cost_per_token": 0.000075,  # $75 per million
            "cache_creation_input_token_cost": 0.00001875,  # $18.75 per million
            "cache_read_input_token_cost": 0.000001875,  # $1.875 per million
        }
    elif "your-new-model" in model.lower():
        # New model pricing (example)
        return {
            "input_cost_per_token": 0.000010,  # $10 per million
            "output_cost_per_token": 0.000050,  # $50 per million
            "cache_creation_input_token_cost": 0.0000125,  # 25% more than input
            "cache_read_input_token_cost": 0.000001,  # 90% less than input
        }
    else:
        # Default to Sonnet pricing
        return {
            "input_cost_per_token": 0.000003,  # $3 per million
            "output_cost_per_token": 0.000015,  # $15 per million
            "cache_creation_input_token_cost": 0.00000375,  # $3.75 per million
            "cache_read_input_token_cost": 0.0000003,  # $0.30 per million
        }
```

### 4. Test the New Model

Create a test to verify cost calculation:

```python
def test_new_model_cost():
    cost_service = CostCalculationService()

    cost = cost_service.calculate_message_cost(
        model="claude-new-model-name",
        input_tokens=1000,
        output_tokens=500,
        cache_creation_input_tokens=200,
        cache_read_input_tokens=300
    )

    # Verify cost is positive and reasonable
    assert cost > 0
    assert cost < 1.0  # Should be less than $1 for this usage
```

### 5. Update Frontend Display (if needed)

The frontend automatically displays costs from the backend, but you may want to add model-specific formatting or icons in:
- `frontend/src/components/messages/MessageHeader.tsx`
- `frontend/src/components/session/SessionCard.tsx`

### 6. Document the Update

Update this documentation with:
- New model name and pricing
- Any special considerations
- Test results

## Recalculating Costs

If you need to recalculate costs for existing messages (e.g., after adding a new model):

### Option 1: API Endpoint
```bash
# Recalculate all costs
curl -X POST http://your-server/api/v1/messages/calculate-costs \
  -H "X-API-Key: your-api-key"

# Recalculate for specific session
curl -X POST http://your-server/api/v1/messages/calculate-costs \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session-uuid"}'
```

### Option 2: Force Resync
```bash
# Force resync with --force flag to recalculate all costs
poetry run claudelens sync -d ~/.claude_personal/ --force --overwrite
```

## Monitoring Costs

To monitor cost calculation issues:

1. **Check logs** for pricing data fetches:
   ```
   grep "Fetched pricing data" /path/to/logs
   ```

2. **Database query** to find messages without costs:
   ```javascript
   db.messages.count({
     type: "assistant",
     costUsd: { $exists: false }
   })
   ```

3. **Verify cost accuracy** by comparing with Claude's billing dashboard

## Future Improvements

1. **Automatic model detection**: Detect new models and fetch pricing from Anthropic's API
2. **Pricing data refresh**: Implement periodic refresh of cached pricing data
3. **Historical pricing**: Track pricing changes over time for accurate historical cost data
4. **Bulk recalculation**: Optimize the recalculation endpoint for large datasets
