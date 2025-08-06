"""Custom APIRouter that handles both with and without trailing slashes."""

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter as FastAPIRouter
from fastapi.types import DecoratedCallable


class APIRouter(FastAPIRouter):
    """Custom APIRouter that automatically handles both URL patterns.

    This router registers each route twice - with and without trailing slash,
    preventing 307 redirects and handling both URL patterns transparently.
    """

    def api_route(
        self, path: str, *, include_in_schema: bool = True, **kwargs: Any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Override api_route to handle both trailing slash patterns."""
        # Remove trailing slash if present
        if path.endswith("/"):
            path = path[:-1]

        # Add route without trailing slash
        add_path = super().api_route(
            path, include_in_schema=include_in_schema, **kwargs
        )

        # Add alternate route with trailing slash (hidden from schema)
        alternate_path = path + "/"
        add_alternate_path = super().api_route(
            alternate_path, include_in_schema=False, **kwargs
        )

        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            # Register the function for both routes
            add_alternate_path(func)
            return add_path(func)

        return decorator
