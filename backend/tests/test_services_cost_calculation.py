"""Tests for cost calculation service."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.cost_calculation import CostCalculationService


class TestCostCalculationService:
    """Test cost calculation service functionality."""

    def setup_method(self):
        """Reset pricing cache before each test."""
        CostCalculationService._pricing_cache = None

    @pytest.mark.asyncio
    async def test_fetch_pricing_data_success(self):
        """Test successful pricing data fetch."""
        mock_pricing_data = {
            "claude-3-5-sonnet-20241022": {
                "input_cost_per_token": 0.000003,
                "output_cost_per_token": 0.000015,
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_pricing_data
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            result = await CostCalculationService.fetch_pricing_data()

            assert result == mock_pricing_data
            assert CostCalculationService._pricing_cache == mock_pricing_data

    @pytest.mark.asyncio
    async def test_fetch_pricing_data_cached(self):
        """Test that pricing data is cached on subsequent calls."""
        cached_data = {"test": "data"}
        CostCalculationService._pricing_cache = cached_data

        result = await CostCalculationService.fetch_pricing_data()

        assert result == cached_data

    @pytest.mark.asyncio
    async def test_fetch_pricing_data_failure(self):
        """Test graceful handling of pricing data fetch failure."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = (
                httpx.RequestError("Network error")
            )

            result = await CostCalculationService.fetch_pricing_data()

            assert result == {}

    def test_calculate_message_cost_basic(self):
        """Test basic cost calculation."""
        result = CostCalculationService.calculate_message_cost(
            model="claude-3-5-sonnet-20241022", input_tokens=1000, output_tokens=500
        )

        # Using default Sonnet pricing: $3/million input, $15/million output
        expected_cost = (1000 * 0.000003) + (500 * 0.000015)
        assert result == expected_cost
        assert result == 0.0105  # $0.0105

    def test_calculate_message_cost_opus(self):
        """Test cost calculation for Opus model."""
        result = CostCalculationService.calculate_message_cost(
            model="claude-3-opus-20240229", input_tokens=1000, output_tokens=500
        )

        # Using Opus pricing: $15/million input, $75/million output
        expected_cost = (1000 * 0.000015) + (500 * 0.000075)
        assert result == expected_cost
        assert result == 0.0525  # $0.0525

    def test_calculate_message_cost_with_cache_tokens(self):
        """Test cost calculation including cache tokens."""
        result = CostCalculationService.calculate_message_cost(
            model="claude-3-5-sonnet-20241022",
            input_tokens=1000,
            output_tokens=500,
            cache_creation_input_tokens=200,
            cache_read_input_tokens=100,
        )

        # Using default Sonnet pricing
        expected_cost = (
            (1000 * 0.000003)
            + (500 * 0.000015)  # input tokens
            + (200 * 0.00000375)  # output tokens
            + (100 * 0.0000003)  # cache creation  # cache read
        )
        assert result == expected_cost

    def test_calculate_message_cost_no_model(self):
        """Test cost calculation with no model."""
        result = CostCalculationService.calculate_message_cost(
            model="", input_tokens=1000, output_tokens=500
        )

        assert result is None

    def test_calculate_message_cost_no_tokens(self):
        """Test cost calculation with no tokens."""
        result = CostCalculationService.calculate_message_cost(
            model="claude-3-5-sonnet-20241022"
        )

        assert result is None

    def test_calculate_message_cost_input_only(self):
        """Test cost calculation with input tokens only."""
        result = CostCalculationService.calculate_message_cost(
            model="claude-3-5-sonnet-20241022", input_tokens=1000
        )

        expected_cost = 1000 * 0.000003
        assert result == expected_cost

    def test_calculate_message_cost_output_only(self):
        """Test cost calculation with output tokens only."""
        result = CostCalculationService.calculate_message_cost(
            model="claude-3-5-sonnet-20241022", output_tokens=500
        )

        expected_cost = 500 * 0.000015
        assert result == expected_cost

    def test_calculate_message_cost_with_exception(self):
        """Test cost calculation handles exceptions gracefully."""
        with patch.object(
            CostCalculationService,
            "_get_model_pricing",
            side_effect=Exception("Test error"),
        ):
            result = CostCalculationService.calculate_message_cost(
                model="claude-3-5-sonnet-20241022", input_tokens=1000, output_tokens=500
            )

            assert result is None

    def test_map_model_name_with_prefix(self):
        """Test model name mapping removes anthropic prefix."""
        result = CostCalculationService._map_model_name(
            "anthropic/claude-3-5-sonnet-20241022"
        )
        assert result == "claude-3-5-sonnet-20241022"

    def test_map_model_name_without_prefix(self):
        """Test model name mapping without prefix."""
        result = CostCalculationService._map_model_name("claude-3-5-sonnet-20241022")
        assert result == "claude-3-5-sonnet-20241022"

    def test_get_model_pricing_opus(self):
        """Test getting pricing for Opus model."""
        result = CostCalculationService._get_model_pricing("claude-3-opus-20240229")

        expected_pricing = {
            "input_cost_per_token": 0.000015,
            "output_cost_per_token": 0.000075,
            "cache_creation_input_token_cost": 0.00001875,
            "cache_read_input_token_cost": 0.000001875,
        }
        assert result == expected_pricing

    def test_get_model_pricing_sonnet(self):
        """Test getting pricing for Sonnet model (default)."""
        result = CostCalculationService._get_model_pricing("claude-3-5-sonnet-20241022")

        expected_pricing = {
            "input_cost_per_token": 0.000003,
            "output_cost_per_token": 0.000015,
            "cache_creation_input_token_cost": 0.00000375,
            "cache_read_input_token_cost": 0.0000003,
        }
        assert result == expected_pricing

    def test_get_model_pricing_unknown_model(self):
        """Test getting pricing for unknown model (defaults to Sonnet)."""
        result = CostCalculationService._get_model_pricing("unknown-model")

        expected_pricing = {
            "input_cost_per_token": 0.000003,
            "output_cost_per_token": 0.000015,
            "cache_creation_input_token_cost": 0.00000375,
            "cache_read_input_token_cost": 0.0000003,
        }
        assert result == expected_pricing

    @pytest.mark.asyncio
    async def test_get_model_pricing_async_with_fetched_data(self):
        """Test async pricing with fetched data."""
        mock_pricing_data = {
            "claude-3-5-sonnet-20241022": {
                "input_cost_per_token": 0.000004,
                "output_cost_per_token": 0.000016,
                "cache_creation_input_token_cost": 0.000005,
                "cache_read_input_token_cost": 0.0000005,
            }
        }

        with patch.object(
            CostCalculationService, "fetch_pricing_data", return_value=mock_pricing_data
        ) as mock_fetch:
            result = await CostCalculationService.get_model_pricing_async(
                "claude-3-5-sonnet-20241022"
            )

            mock_fetch.assert_called_once()
            assert result == mock_pricing_data["claude-3-5-sonnet-20241022"]

    @pytest.mark.asyncio
    async def test_get_model_pricing_async_fallback_to_default(self):
        """Test async pricing falls back to default when model not found."""
        mock_pricing_data = {}

        with patch.object(
            CostCalculationService, "fetch_pricing_data", return_value=mock_pricing_data
        ):
            result = await CostCalculationService.get_model_pricing_async(
                "claude-3-5-sonnet-20241022"
            )

            expected_pricing = {
                "input_cost_per_token": 0.000003,
                "output_cost_per_token": 0.000015,
                "cache_creation_input_token_cost": 0.00000375,
                "cache_read_input_token_cost": 0.0000003,
            }
            assert result == expected_pricing

    @pytest.mark.asyncio
    async def test_get_model_pricing_async_incomplete_fetched_data(self):
        """Test async pricing falls back when fetched data is incomplete."""
        mock_pricing_data = {
            "claude-3-5-sonnet-20241022": {
                "input_cost_per_token": 0.000004,
                # Missing output_cost_per_token
            }
        }

        with patch.object(
            CostCalculationService, "fetch_pricing_data", return_value=mock_pricing_data
        ):
            result = await CostCalculationService.get_model_pricing_async(
                "claude-3-5-sonnet-20241022"
            )

            # Should fall back to default pricing
            expected_pricing = {
                "input_cost_per_token": 0.000003,
                "output_cost_per_token": 0.000015,
                "cache_creation_input_token_cost": 0.00000375,
                "cache_read_input_token_cost": 0.0000003,
            }
            assert result == expected_pricing

    @pytest.mark.asyncio
    async def test_get_model_pricing_async_with_anthropic_prefix(self):
        """Test async pricing with anthropic/ prefix."""
        mock_pricing_data = {
            "claude-3-5-sonnet-20241022": {
                "input_cost_per_token": 0.000004,
                "output_cost_per_token": 0.000016,
            }
        }

        with patch.object(
            CostCalculationService, "fetch_pricing_data", return_value=mock_pricing_data
        ):
            result = await CostCalculationService.get_model_pricing_async(
                "anthropic/claude-3-5-sonnet-20241022"
            )

            assert result == mock_pricing_data["claude-3-5-sonnet-20241022"]

    def test_calculate_message_cost_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        result = CostCalculationService.calculate_message_cost(
            model="claude-3-5-sonnet-20241022", input_tokens=0, output_tokens=0
        )

        # When both input and output tokens are 0, should return None (no cost to calculate)
        assert result is None

    def test_calculate_message_cost_one_zero_token_type(self):
        """Test cost calculation when one token type is 0 but other has value."""
        # Test with input_tokens=0 but output_tokens>0
        result1 = CostCalculationService.calculate_message_cost(
            model="claude-3-5-sonnet-20241022", input_tokens=0, output_tokens=500
        )
        expected_cost1 = 500 * 0.000015
        assert result1 == expected_cost1

        # Test with output_tokens=0 but input_tokens>0
        result2 = CostCalculationService.calculate_message_cost(
            model="claude-3-5-sonnet-20241022", input_tokens=1000, output_tokens=0
        )
        expected_cost2 = 1000 * 0.000003
        assert result2 == expected_cost2

    def test_calculate_message_cost_large_numbers(self):
        """Test cost calculation with large token numbers."""
        result = CostCalculationService.calculate_message_cost(
            model="claude-3-5-sonnet-20241022",
            input_tokens=1000000,  # 1 million tokens
            output_tokens=500000,  # 500k tokens
        )

        # Using default Sonnet pricing: $3/million input, $15/million output
        expected_cost = (1000000 * 0.000003) + (500000 * 0.000015)
        assert result == expected_cost
        assert result == 10.5  # $10.50

    def test_opus_detection_case_insensitive(self):
        """Test that Opus detection is case insensitive."""
        result1 = CostCalculationService.calculate_message_cost(
            model="CLAUDE-3-OPUS-20240229", input_tokens=1000, output_tokens=500
        )

        result2 = CostCalculationService.calculate_message_cost(
            model="claude-3-opus-20240229", input_tokens=1000, output_tokens=500
        )

        assert result1 == result2
        # Should use Opus pricing
        expected_cost = (1000 * 0.000015) + (500 * 0.000075)
        assert result1 == expected_cost
