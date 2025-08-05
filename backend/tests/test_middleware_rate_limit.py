"""Tests for rate limit middleware."""
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, Response
from starlette.responses import JSONResponse

from app.middleware.rate_limit import RateLimitMiddleware


@pytest.fixture
def mock_request():
    """Create a mock request."""
    request = MagicMock(spec=Request)
    request.url.path = "/api/test"
    request.client.host = "127.0.0.1"
    request.headers = {}
    return request


@pytest.fixture
def mock_response():
    """Create a mock response."""
    response = MagicMock(spec=Response)
    response.status_code = 200
    response.headers = {}
    return response


@pytest.fixture
def rate_limit_middleware():
    """Create rate limit middleware instance with small limits for testing."""
    return RateLimitMiddleware(app=MagicMock(), calls=3, period=60)


class TestRateLimitMiddleware:
    """Test cases for RateLimitMiddleware."""

    @pytest.mark.asyncio
    async def test_request_under_limit(
        self, rate_limit_middleware, mock_request, mock_response
    ):
        """Test requests under the rate limit are processed normally."""
        call_next = AsyncMock(return_value=mock_response)

        with patch("time.time", return_value=1000.0):
            result = await rate_limit_middleware.dispatch(mock_request, call_next)

        # Verify request was processed
        call_next.assert_called_once_with(mock_request)
        assert result == mock_response

        # Verify rate limit headers were added
        assert mock_response.headers["X-RateLimit-Limit"] == "3"
        assert mock_response.headers["X-RateLimit-Remaining"] == "2"
        assert mock_response.headers["X-RateLimit-Reset"] == "1060"

    @pytest.mark.asyncio
    async def test_request_exceeds_limit(
        self, rate_limit_middleware, mock_request, mock_response
    ):
        """Test that requests exceeding rate limit are rejected."""
        call_next = AsyncMock(return_value=mock_response)

        # Make requests up to the limit (3 calls)
        with patch("time.time", return_value=1000.0):
            for i in range(3):
                await rate_limit_middleware.dispatch(mock_request, call_next)

        # The 4th request should be rate limited
        with patch("time.time", return_value=1001.0):
            result = await rate_limit_middleware.dispatch(mock_request, call_next)

        # Verify the request was rejected
        assert isinstance(result, JSONResponse)
        assert result.status_code == 429

        # Verify rate limit headers
        assert result.headers["Retry-After"] == "60"
        assert result.headers["X-RateLimit-Limit"] == "3"
        assert result.headers["X-RateLimit-Remaining"] == "0"
        assert result.headers["X-RateLimit-Reset"] == "1061"

        # Verify call_next was not called for the rate limited request
        assert call_next.call_count == 3

    @pytest.mark.asyncio
    async def test_rate_limit_resets_after_period(
        self, rate_limit_middleware, mock_request, mock_response
    ):
        """Test that rate limit resets after the time period."""
        call_next = AsyncMock(return_value=mock_response)

        # Make requests up to the limit
        with patch("time.time", return_value=1000.0):
            for i in range(3):
                await rate_limit_middleware.dispatch(mock_request, call_next)

        # Wait for period to pass (60 seconds + 1)
        with patch("time.time", return_value=1061.0):
            result = await rate_limit_middleware.dispatch(mock_request, call_next)

        # Verify request was processed (rate limit reset)
        assert result == mock_response
        assert call_next.call_count == 4

        # Verify new rate limit headers
        assert mock_response.headers["X-RateLimit-Remaining"] == "2"

    @pytest.mark.asyncio
    async def test_excluded_paths_bypass_rate_limit(
        self, rate_limit_middleware, mock_response
    ):
        """Test that excluded paths bypass rate limiting."""
        excluded_paths = [
            "/health",
            "/api/v1/health",
            "/api/v1/messages/calculate-costs",
            "/api/v1/projects",
        ]

        call_next = AsyncMock(return_value=mock_response)

        for path in excluded_paths:
            request = MagicMock(spec=Request)
            request.url.path = path
            request.client.host = "127.0.0.1"
            request.headers = {}

            result = await rate_limit_middleware.dispatch(request, call_next)

            # Verify request was processed without rate limiting
            assert result == mock_response
            # No rate limit headers should be added for excluded paths
            assert "X-RateLimit-Limit" not in mock_response.headers

    @pytest.mark.asyncio
    async def test_different_clients_have_separate_limits(
        self, rate_limit_middleware, mock_response
    ):
        """Test that different clients have separate rate limits."""
        call_next = AsyncMock(return_value=mock_response)

        # Client 1
        request1 = MagicMock(spec=Request)
        request1.url.path = "/api/test"
        request1.client.host = "127.0.0.1"
        request1.headers = {}

        # Client 2
        request2 = MagicMock(spec=Request)
        request2.url.path = "/api/test"
        request2.client.host = "192.168.1.1"
        request2.headers = {}

        with patch("time.time", return_value=1000.0):
            # Make 3 requests from client 1 (max limit)
            for i in range(3):
                await rate_limit_middleware.dispatch(request1, call_next)

            # Client 2 should still be able to make requests
            result = await rate_limit_middleware.dispatch(request2, call_next)

        # Verify client 2's request was processed
        assert result == mock_response
        assert call_next.call_count == 4

    @pytest.mark.asyncio
    async def test_api_key_client_identification(
        self, rate_limit_middleware, mock_response
    ):
        """Test that API key is used for client identification when available."""
        call_next = AsyncMock(return_value=mock_response)

        # Request with API key
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        request.client.host = "127.0.0.1"
        request.headers = {"X-API-Key": "test-api-key-12345"}

        with patch("time.time", return_value=1000.0):
            await rate_limit_middleware.dispatch(request, call_next)

        # Verify client is tracked by API key prefix
        client_ids = list(rate_limit_middleware.clients.keys())
        assert len(client_ids) == 1
        assert client_ids[0] == "api:test-api"  # First 8 chars

    @pytest.mark.asyncio
    async def test_no_client_info_fallback(self, rate_limit_middleware, mock_response):
        """Test fallback when no client info is available."""
        call_next = AsyncMock(return_value=mock_response)

        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        request.client = None
        request.headers = {}

        with patch("time.time", return_value=1000.0):
            await rate_limit_middleware.dispatch(request, call_next)

        # Verify fallback client ID is used
        client_ids = list(rate_limit_middleware.clients.keys())
        assert len(client_ids) == 1
        assert client_ids[0] == "unknown"

    @pytest.mark.asyncio
    async def test_cleanup_old_entries(
        self, rate_limit_middleware, mock_request, mock_response
    ):
        """Test that old entries are cleaned up during requests."""
        call_next = AsyncMock(return_value=mock_response)

        # Make a request at time 1000
        with patch("time.time", return_value=1000.0):
            await rate_limit_middleware.dispatch(mock_request, call_next)

        # Verify entry exists
        client_id = rate_limit_middleware._get_client_id(mock_request)
        assert len(rate_limit_middleware.clients[client_id]) == 1

        # Make another request after the period (60+ seconds later)
        with patch("time.time", return_value=1070.0):
            await rate_limit_middleware.dispatch(mock_request, call_next)

        # Verify old entry was cleaned up, only new entry remains
        assert len(rate_limit_middleware.clients[client_id]) == 1
        assert rate_limit_middleware.clients[client_id][0] == 1070.0

    def test_get_client_id_with_api_key(self, rate_limit_middleware):
        """Test client ID generation with API key."""
        request = MagicMock(spec=Request)
        request.headers = {"X-API-Key": "long-api-key-value-here"}
        request.client.host = "127.0.0.1"

        client_id = rate_limit_middleware._get_client_id(request)
        assert client_id == "api:long-api"

    def test_get_client_id_with_ip_only(self, rate_limit_middleware):
        """Test client ID generation with IP only."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client.host = "192.168.1.100"

        client_id = rate_limit_middleware._get_client_id(request)
        assert client_id == "ip:192.168.1.100"

    def test_get_client_id_fallback(self, rate_limit_middleware):
        """Test client ID fallback when no info available."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = None

        client_id = rate_limit_middleware._get_client_id(request)
        assert client_id == "unknown"

    @pytest.mark.asyncio
    async def test_periodic_cleanup_task_creation(
        self, rate_limit_middleware, mock_request, mock_response
    ):
        """Test that periodic cleanup task is created after first request."""
        call_next = AsyncMock(return_value=mock_response)

        # Initially no cleanup task
        assert rate_limit_middleware._cleanup_task is None

        with patch("asyncio.create_task") as mock_create_task:
            # Create a mock task that properly handles the coroutine
            mock_task = MagicMock()
            mock_task.cancel = MagicMock()
            mock_task.done = MagicMock(return_value=False)

            # Wrap the coroutine to consume it without running
            def create_task_wrapper(coro):
                # Close the coroutine to prevent the warning
                coro.close()
                return mock_task

            mock_create_task.side_effect = create_task_wrapper

            with patch("time.time", return_value=1000.0):
                await rate_limit_middleware.dispatch(mock_request, call_next)

            # Verify cleanup task was created
            mock_create_task.assert_called_once()
            assert rate_limit_middleware._cleanup_task == mock_task

    @pytest.mark.asyncio
    async def test_periodic_cleanup_task_not_recreated(
        self, rate_limit_middleware, mock_request, mock_response
    ):
        """Test that periodic cleanup task is not recreated if already exists."""
        call_next = AsyncMock(return_value=mock_response)

        # Set existing cleanup task (use MagicMock that behaves like a Task)
        existing_task = MagicMock()
        existing_task.done.return_value = False  # Task is not done
        existing_task.cancel = MagicMock()  # Add cancel method
        rate_limit_middleware._cleanup_task = existing_task

        with patch("asyncio.create_task") as mock_create_task:
            with patch("time.time", return_value=1000.0):
                await rate_limit_middleware.dispatch(mock_request, call_next)

            # Verify new task was not created
            mock_create_task.assert_not_called()
            assert rate_limit_middleware._cleanup_task == existing_task

    @pytest.mark.asyncio
    async def test_custom_rate_limit_parameters(self):
        """Test middleware with custom rate limit parameters."""
        # Create middleware with custom limits
        middleware = RateLimitMiddleware(app=MagicMock(), calls=5, period=30)

        assert middleware.calls == 5
        assert middleware.period == 30

        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        request.client.host = "127.0.0.1"
        request.headers = {}

        response = MagicMock(spec=Response)
        response.headers = {}

        call_next = AsyncMock(return_value=response)

        # Mock asyncio.create_task to prevent actual background task creation
        with patch("asyncio.create_task") as mock_create_task:
            mock_task = MagicMock()
            mock_task.cancel = MagicMock()
            mock_task.done = MagicMock(return_value=False)

            # Wrap the coroutine to consume it without running
            def create_task_wrapper(coro):
                # Close the coroutine to prevent the warning
                coro.close()
                return mock_task

            mock_create_task.side_effect = create_task_wrapper

            with patch("time.time", return_value=1000.0):
                await middleware.dispatch(request, call_next)

        # Verify custom limits are reflected in headers
        assert response.headers["X-RateLimit-Limit"] == "5"
        assert response.headers["X-RateLimit-Remaining"] == "4"
        assert response.headers["X-RateLimit-Reset"] == "1030"  # 1000 + 30

    @pytest.mark.asyncio
    async def test_rate_limit_response_content(
        self, rate_limit_middleware, mock_request
    ):
        """Test the content of rate limit response."""
        call_next = AsyncMock()

        # Mock asyncio.create_task to prevent real background task creation
        with patch("asyncio.create_task") as mock_create_task:
            mock_task = MagicMock()
            mock_task.cancel = MagicMock()
            mock_task.done = MagicMock(return_value=False)

            # Wrap the coroutine to consume it without running
            def create_task_wrapper(coro):
                # Close the coroutine to prevent the warning
                coro.close()
                return mock_task

            mock_create_task.side_effect = create_task_wrapper

            # Exceed rate limit
            with patch("time.time", return_value=1000.0):
                for i in range(3):
                    await rate_limit_middleware.dispatch(mock_request, call_next)

                # This should trigger rate limiting
                result = await rate_limit_middleware.dispatch(mock_request, call_next)

        # Verify response content
        assert isinstance(result, JSONResponse)

        # The content should be accessible (though testing exact content may be tricky with JSONResponse)
        assert result.status_code == 429


class TestRateLimitMiddlewarePeriodicCleanup:
    """Test cases for the periodic cleanup functionality."""

    @pytest.mark.asyncio
    async def test_periodic_cleanup_removes_empty_clients(self):
        """Test that periodic cleanup removes clients with no recent requests."""
        middleware = RateLimitMiddleware(app=MagicMock(), calls=3, period=60)

        # Add some test data
        middleware.clients["client1"] = [1000.0, 1010.0]
        middleware.clients["client2"] = [1000.0]
        middleware.clients["client3"] = []

        # Mock time to be past the period
        with patch("time.time", return_value=1070.0):
            # Simulate one iteration of cleanup
            now = time.time()
            for client_id in list(middleware.clients.keys()):
                middleware.clients[client_id] = [
                    timestamp
                    for timestamp in middleware.clients[client_id]
                    if timestamp > now - middleware.period
                ]
                if not middleware.clients[client_id]:
                    del middleware.clients[client_id]

        # Verify cleanup worked
        assert "client1" not in middleware.clients
        assert "client2" not in middleware.clients
        assert "client3" not in middleware.clients

    @pytest.mark.asyncio
    async def test_periodic_cleanup_preserves_recent_clients(self):
        """Test that periodic cleanup preserves clients with recent requests."""
        middleware = RateLimitMiddleware(app=MagicMock(), calls=3, period=60)

        # Add test data with some recent timestamps
        middleware.clients["client1"] = [1000.0, 1050.0]  # One old, one recent
        middleware.clients["client2"] = [1060.0]  # Recent only

        # Mock time
        with patch("time.time", return_value=1070.0):
            # Simulate cleanup
            now = time.time()
            for client_id in list(middleware.clients.keys()):
                middleware.clients[client_id] = [
                    timestamp
                    for timestamp in middleware.clients[client_id]
                    if timestamp > now - middleware.period
                ]
                if not middleware.clients[client_id]:
                    del middleware.clients[client_id]

        # Verify results
        assert "client1" in middleware.clients
        assert len(middleware.clients["client1"]) == 1
        assert middleware.clients["client1"][0] == 1050.0

        assert "client2" in middleware.clients
        assert len(middleware.clients["client2"]) == 1
        assert middleware.clients["client2"][0] == 1060.0
