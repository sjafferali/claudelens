"""Middleware to handle X-Forwarded headers for proper HTTPS detection."""

from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class ForwardedHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle X-Forwarded headers for proper scheme detection.

    This ensures that when the application is behind a reverse proxy (like nginx),
    it correctly identifies HTTPS requests and generates proper redirect URLs.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the request and handle forwarded headers."""
        # Get the forwarded headers
        forwarded_proto = request.headers.get("x-forwarded-proto")
        forwarded_host = request.headers.get("x-forwarded-host")
        forwarded_for = request.headers.get("x-forwarded-for")

        # Update the request scope directly if forwarded headers exist
        if forwarded_proto or forwarded_host or forwarded_for:
            # Update the scheme if X-Forwarded-Proto is present
            if forwarded_proto:
                request.scope["scheme"] = forwarded_proto.split(",")[0].strip()

            # Update the host if X-Forwarded-Host is present
            if forwarded_host:
                host = forwarded_host.split(",")[0].strip()
                # Parse host and port
                if ":" in host:
                    hostname, port = host.rsplit(":", 1)
                    request.scope["server"] = (hostname, int(port))
                else:
                    # Use default ports based on scheme
                    default_port = 443 if request.scope.get("scheme") == "https" else 80
                    request.scope["server"] = (host, default_port)

            # Update client if X-Forwarded-For is present
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
                request.scope["client"] = (client_ip, 0)  # Port is typically not known

        # Process the request
        response = await call_next(request)

        return response
