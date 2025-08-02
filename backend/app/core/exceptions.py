"""Custom exceptions."""


class ClaudeLensException(Exception):
    """Base exception for ClaudeLens."""

    def __init__(
        self, detail: str, status_code: int = 500, error_type: str = "internal_error"
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_type = error_type
        super().__init__(detail)


class NotFoundError(ClaudeLensException):
    """Resource not found error."""

    def __init__(self, resource: str, resource_id: str | None = None):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with id '{resource_id}' not found"
        super().__init__(detail, status_code=404, error_type="not_found")


class ValidationError(ClaudeLensException):
    """Validation error."""

    def __init__(self, detail: str):
        super().__init__(detail, status_code=422, error_type="validation_error")


class AuthenticationError(ClaudeLensException):
    """Authentication error."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(detail, status_code=401, error_type="authentication_error")


class AuthorizationError(ClaudeLensException):
    """Authorization error."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(detail, status_code=403, error_type="authorization_error")


class RateLimitError(ClaudeLensException):
    """Rate limit error."""

    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(detail, status_code=429, error_type="rate_limit_error")
