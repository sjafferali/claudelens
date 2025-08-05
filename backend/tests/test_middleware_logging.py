"""Tests for logging middleware."""
import logging
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, Response

from app.middleware.logging import LoggingMiddleware


@pytest.fixture
def mock_request():
    """Create a mock request."""
    request = MagicMock(spec=Request)
    request.method = "GET"
    request.url.path = "/test"
    request.client.host = "127.0.0.1"
    request.state = MagicMock()
    return request


@pytest.fixture
def mock_response():
    """Create a mock response."""
    response = MagicMock(spec=Response)
    response.status_code = 200
    response.headers = {}
    return response


@pytest.fixture
def logging_middleware():
    """Create logging middleware instance."""
    return LoggingMiddleware(app=MagicMock())


class TestLoggingMiddleware:
    """Test cases for LoggingMiddleware."""

    @pytest.mark.asyncio
    async def test_successful_request_logging(
        self, logging_middleware, mock_request, mock_response, caplog
    ):
        """Test logging of successful requests."""
        # Mock call_next to return successful response
        call_next = AsyncMock(return_value=mock_response)

        with caplog.at_level(logging.INFO):
            with patch("time.time") as mock_time:
                # Use a callable that can handle multiple calls
                times = iter([1000.0, 1000.5])
                mock_time.side_effect = lambda: next(
                    times, 1000.5
                )  # Default to end time if more calls
                with patch(
                    "uuid.uuid4",
                    return_value=uuid.UUID("12345678-1234-5678-9012-123456789012"),
                ):
                    result = await logging_middleware.dispatch(mock_request, call_next)

        # Verify response
        assert result == mock_response
        assert (
            mock_response.headers["X-Request-ID"]
            == "12345678-1234-5678-9012-123456789012"
        )
        assert mock_request.state.request_id == "12345678-1234-5678-9012-123456789012"

        # Verify logging
        assert len(caplog.records) == 2

        # Check request started log
        start_record = caplog.records[0]
        assert start_record.levelname == "INFO"
        assert start_record.getMessage() == "Request started"
        assert start_record.request_id == "12345678-1234-5678-9012-123456789012"
        assert start_record.method == "GET"
        assert start_record.path == "/test"
        assert start_record.client == "127.0.0.1"

        # Check request completed log
        end_record = caplog.records[1]
        assert end_record.levelname == "INFO"
        assert end_record.getMessage() == "Request completed"
        assert end_record.request_id == "12345678-1234-5678-9012-123456789012"
        assert end_record.method == "GET"
        assert end_record.path == "/test"
        assert end_record.status_code == 200
        assert end_record.duration == "0.500s"

    @pytest.mark.asyncio
    async def test_failed_request_logging(
        self, logging_middleware, mock_request, caplog
    ):
        """Test logging of failed requests."""
        # Mock call_next to raise an exception
        test_error = Exception("Test error")
        call_next = AsyncMock(side_effect=test_error)

        with caplog.at_level(logging.INFO):  # Capture INFO level to get both logs
            with patch("time.time") as mock_time:
                # Use a callable that can handle multiple calls
                times = iter([1000.0, 1000.3])
                mock_time.side_effect = lambda: next(
                    times, 1000.3
                )  # Default to error time if more calls
                with patch(
                    "uuid.uuid4",
                    return_value=uuid.UUID("12345678-1234-5678-9012-123456789012"),
                ):
                    with pytest.raises(Exception, match="Test error"):
                        await logging_middleware.dispatch(mock_request, call_next)

        # Verify request ID was set
        assert mock_request.state.request_id == "12345678-1234-5678-9012-123456789012"

        # Verify logging
        assert len(caplog.records) == 2

        # Check request started log
        start_record = caplog.records[0]
        assert start_record.levelname == "INFO"
        assert start_record.getMessage() == "Request started"

        # Check request failed log
        error_record = caplog.records[1]
        assert error_record.levelname == "ERROR"
        assert error_record.getMessage() == "Request failed"
        assert error_record.request_id == "12345678-1234-5678-9012-123456789012"
        assert error_record.method == "GET"
        assert error_record.path == "/test"
        assert error_record.duration == "0.300s"
        assert error_record.error == "Test error"
        assert error_record.exc_info is not None

    @pytest.mark.asyncio
    async def test_request_without_client(
        self, logging_middleware, mock_response, caplog
    ):
        """Test logging when request has no client info."""
        # Create request without client
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/test"
        request.client = None
        request.state = MagicMock()

        call_next = AsyncMock(return_value=mock_response)

        with caplog.at_level(logging.INFO):
            with patch("time.time") as mock_time:
                # Use a callable that can handle multiple calls
                times = iter([1000.0, 1000.1])
                mock_time.side_effect = lambda: next(
                    times, 1000.1
                )  # Default to end time if more calls
                with patch(
                    "uuid.uuid4",
                    return_value=uuid.UUID("87654321-4321-8765-2109-876543210987"),
                ):
                    await logging_middleware.dispatch(request, call_next)

        # Check that client is logged as None
        start_record = caplog.records[0]
        assert start_record.client is None

    @pytest.mark.asyncio
    async def test_duration_calculation_precision(
        self, logging_middleware, mock_request, mock_response, caplog
    ):
        """Test that duration is calculated and formatted correctly."""
        call_next = AsyncMock(return_value=mock_response)

        with caplog.at_level(logging.INFO):
            # Test very short duration
            with patch("time.time") as mock_time:
                # Use a callable that can handle multiple calls
                times = iter([1000.0, 1000.001])
                mock_time.side_effect = lambda: next(
                    times, 1000.001
                )  # Default to end time if more calls
                with patch(
                    "uuid.uuid4",
                    return_value=uuid.UUID("12345678-1234-5678-9012-123456789012"),
                ):
                    await logging_middleware.dispatch(mock_request, call_next)

        end_record = caplog.records[1]
        assert end_record.duration == "0.001s"

    @pytest.mark.asyncio
    async def test_unique_request_ids(
        self, logging_middleware, mock_request, mock_response
    ):
        """Test that each request gets a unique request ID."""
        call_next = AsyncMock(return_value=mock_response)

        # First request
        with patch("time.time") as mock_time:
            # Use a callable that can handle multiple calls
            times = iter([1000.0, 1000.1])
            mock_time.side_effect = lambda: next(
                times, 1000.1
            )  # Default to end time if more calls
            result1 = await logging_middleware.dispatch(mock_request, call_next)

        request_id_1 = result1.headers["X-Request-ID"]

        # Second request with fresh mock response
        mock_response_2 = MagicMock(spec=Response)
        mock_response_2.status_code = 200
        mock_response_2.headers = {}
        call_next.return_value = mock_response_2

        with patch("time.time") as mock_time3:
            # Use a callable that can handle multiple calls
            times = iter([2000.0, 2000.1])
            mock_time3.side_effect = lambda: next(
                times, 2000.1
            )  # Default to end time if more calls
            result2 = await logging_middleware.dispatch(mock_request, call_next)

        request_id_2 = result2.headers["X-Request-ID"]

        # Verify different IDs
        assert request_id_1 != request_id_2
        assert len(request_id_1) == 36  # UUID format
        assert len(request_id_2) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_exception_preserves_request_state(
        self, logging_middleware, mock_request
    ):
        """Test that exceptions don't prevent request state from being set."""
        call_next = AsyncMock(side_effect=ValueError("Processing error"))

        with patch(
            "uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-9012-123456789012")
        ):
            with pytest.raises(ValueError):
                await logging_middleware.dispatch(mock_request, call_next)

        # Verify request ID was still set despite the exception
        assert mock_request.state.request_id == "12345678-1234-5678-9012-123456789012"


class TestLoggingMiddlewareIntegration:
    """Integration tests for LoggingMiddleware."""

    @pytest.mark.asyncio
    async def test_middleware_call_chain(
        self, logging_middleware, mock_request, caplog
    ):
        """Test that middleware properly calls the next handler in chain."""

        # Mock a simple call_next that modifies the request state
        async def mock_call_next(request):
            request.state.processed = True
            response = MagicMock(spec=Response)
            response.status_code = 201
            response.headers = {}
            return response

        with caplog.at_level(logging.INFO):
            with patch("time.time") as mock_time:
                # Use a callable that can handle multiple calls
                times = iter([1000.0, 1000.1])
                mock_time.side_effect = lambda: next(
                    times, 1000.1
                )  # Default to end time if more calls
                result = await logging_middleware.dispatch(mock_request, mock_call_next)

        # Verify the call chain worked
        assert mock_request.state.processed is True
        assert result.status_code == 201
        assert len(caplog.records) == 2
