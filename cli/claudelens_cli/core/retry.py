"""Retry logic and error handling utilities."""
import asyncio
import functools
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

import httpx
from rich.console import Console

console = Console()

T = TypeVar('T')


def with_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,)
):
    """Decorator for retry logic with exponential backoff."""
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff ** attempt)
                        console.print(
                            f"[yellow]Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {wait_time:.1f}s...[/yellow]"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        console.print(f"[red]All {max_attempts} attempts failed[/red]")
            
            if last_exception is not None:
                raise last_exception
            raise RuntimeError("Unexpected retry state")
        
        return wrapper
    return decorator


class RetryableHTTPClient:
    """HTTP client with built-in retry logic."""
    
    def __init__(
        self,
        base_url: str,
        headers: dict | None = None,
        max_retries: int = 3,
        timeout: float = 30.0
    ):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=timeout
        )
        self.max_retries = max_retries
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @with_retry(max_attempts=3, exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """POST request with retry."""
        response = await self.client.post(url, **kwargs)
        
        # Retry on 5xx errors
        if response.status_code >= 500:
            raise httpx.HTTPStatusError(
                f"Server error: {response.status_code}",
                request=response.request,
                response=response
            )
        
        return response
    
    @with_retry(max_attempts=3, exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """GET request with retry."""
        return await self.client.get(url, **kwargs)