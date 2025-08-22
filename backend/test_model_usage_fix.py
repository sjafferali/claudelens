#!/usr/bin/env python3
"""Test script to verify the model usage analytics fix."""

import asyncio
import sys
from datetime import datetime

sys.path.insert(0, ".")

from app.database import get_db  # noqa: E402
from app.schemas.analytics import TimeRange  # noqa: E402
from app.services.analytics import AnalyticsService  # noqa: E402


async def test_model_usage_with_null_models():
    """Test that model usage analytics handles null model values correctly."""
    print("Testing model usage analytics with null model values...")

    async for db in get_db():
        # Create test data with some null model values
        test_messages = [
            {
                "sessionId": "test-session-analytics",
                "type": "assistant",
                "model": "claude-3-opus-20240229",  # Valid model
                "costUsd": 0.01,
                "durationMs": 1000,
                "tokensInput": 100,
                "tokensOutput": 200,
                "timestamp": datetime.utcnow().isoformat(),
            },
            {
                "sessionId": "test-session-analytics",
                "type": "assistant",
                "model": None,  # Null model
                "costUsd": 0.02,
                "durationMs": 2000,
                "tokensInput": 150,
                "tokensOutput": 250,
                "timestamp": datetime.utcnow().isoformat(),
            },
            {
                "sessionId": "test-session-analytics",
                "type": "assistant",
                "model": "gpt-4",  # Valid model
                "costUsd": 0.03,
                "durationMs": 1500,
                "tokensInput": 200,
                "tokensOutput": 300,
                "timestamp": datetime.utcnow().isoformat(),
            },
            {
                "sessionId": "test-session-analytics",
                "type": "user",  # User message without model
                "content": "Test prompt",
                "timestamp": datetime.utcnow().isoformat(),
            },
        ]

        # Insert test data
        print("Inserting test data...")
        await db.messages.insert_many(test_messages)

        try:
            # Test the analytics service
            analytics_service = AnalyticsService(db)

            print("Getting model usage statistics...")
            result = await analytics_service.get_model_usage(TimeRange.ALL_TIME)

            print("\nResults:")
            print(f"Total models found: {result.total_models}")
            print(f"Most used model: {result.most_used}")

            # Verify that only valid models are included
            for model_usage in result.models:
                print(f"  - Model: {model_usage.model}")
                print(f"    Message count: {model_usage.message_count}")
                print(f"    Total cost: ${model_usage.total_cost}")

                # This should not be None
                assert model_usage.model is not None, "Model should not be None"
                assert isinstance(model_usage.model, str), "Model should be a string"

            # Verify we only have 2 valid models (claude and gpt-4)
            assert (
                result.total_models == 2
            ), f"Expected 2 models, got {result.total_models}"

            model_names = [m.model for m in result.models]
            assert (
                "claude-3-opus-20240229" in model_names
            ), "Claude model should be included"
            assert "gpt-4" in model_names, "GPT-4 model should be included"

            print("\n✅ Test passed! Null model values are properly filtered out.")

        finally:
            # Clean up test data
            print("\nCleaning up test data...")
            await db.messages.delete_many({"sessionId": "test-session-analytics"})

        break


if __name__ == "__main__":
    asyncio.run(test_model_usage_with_null_models())
