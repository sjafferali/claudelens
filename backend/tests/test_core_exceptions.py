"""Tests for custom exceptions."""

import pytest

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ClaudeLensException,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


class TestClaudeLensException:
    """Test cases for base ClaudeLensException."""

    def test_exception_creation_with_defaults(self):
        """Test creating exception with default parameters."""
        exception = ClaudeLensException("Something went wrong")

        assert str(exception) == "Something went wrong"
        assert exception.detail == "Something went wrong"
        assert exception.status_code == 500
        assert exception.error_type == "internal_error"

    def test_exception_creation_with_custom_parameters(self):
        """Test creating exception with custom parameters."""
        exception = ClaudeLensException(
            detail="Custom error message", status_code=418, error_type="teapot_error"
        )

        assert str(exception) == "Custom error message"
        assert exception.detail == "Custom error message"
        assert exception.status_code == 418
        assert exception.error_type == "teapot_error"

    def test_exception_inherits_from_exception(self):
        """Test that ClaudeLensException inherits from Exception."""
        exception = ClaudeLensException("Test error")

        assert isinstance(exception, Exception)
        assert isinstance(exception, ClaudeLensException)

    def test_exception_can_be_raised_and_caught(self):
        """Test that exception can be raised and caught."""
        with pytest.raises(ClaudeLensException) as exc_info:
            raise ClaudeLensException("Test error")

        assert exc_info.value.detail == "Test error"
        assert exc_info.value.status_code == 500
        assert exc_info.value.error_type == "internal_error"

    def test_exception_attributes_are_accessible(self):
        """Test that exception attributes are accessible after raising."""
        try:
            raise ClaudeLensException(
                "Test error", status_code=400, error_type="bad_request"
            )
        except ClaudeLensException as e:
            assert e.detail == "Test error"
            assert e.status_code == 400
            assert e.error_type == "bad_request"


class TestNotFoundError:
    """Test cases for NotFoundError."""

    def test_not_found_error_with_resource_only(self):
        """Test NotFoundError with only resource name."""
        error = NotFoundError("User")

        assert str(error) == "User not found"
        assert error.detail == "User not found"
        assert error.status_code == 404
        assert error.error_type == "not_found"

    def test_not_found_error_with_resource_and_id(self):
        """Test NotFoundError with resource name and ID."""
        error = NotFoundError("Project", "12345")

        assert str(error) == "Project with id '12345' not found"
        assert error.detail == "Project with id '12345' not found"
        assert error.status_code == 404
        assert error.error_type == "not_found"

    def test_not_found_error_with_empty_resource_id(self):
        """Test NotFoundError with empty resource ID."""
        error = NotFoundError("Session", "")

        # Empty string is falsy, so it acts like None
        assert str(error) == "Session not found"
        assert error.detail == "Session not found"

    def test_not_found_error_with_none_resource_id(self):
        """Test NotFoundError with None resource ID."""
        error = NotFoundError("Message", None)

        assert str(error) == "Message not found"
        assert error.detail == "Message not found"

    def test_not_found_error_inherits_from_claudelens_exception(self):
        """Test that NotFoundError inherits from ClaudeLensException."""
        error = NotFoundError("Item")

        assert isinstance(error, ClaudeLensException)
        assert isinstance(error, NotFoundError)
        assert isinstance(error, Exception)

    def test_not_found_error_can_be_raised(self):
        """Test that NotFoundError can be raised and caught."""
        with pytest.raises(NotFoundError) as exc_info:
            raise NotFoundError("Document", "doc123")

        assert exc_info.value.detail == "Document with id 'doc123' not found"

    def test_not_found_error_caught_as_base_exception(self):
        """Test that NotFoundError can be caught as base ClaudeLensException."""
        with pytest.raises(ClaudeLensException) as exc_info:
            raise NotFoundError("File", "file.txt")

        assert isinstance(exc_info.value, NotFoundError)
        assert exc_info.value.status_code == 404


class TestValidationError:
    """Test cases for ValidationError."""

    def test_validation_error_creation(self):
        """Test creating ValidationError."""
        error = ValidationError("Invalid input data")

        assert str(error) == "Invalid input data"
        assert error.detail == "Invalid input data"
        assert error.status_code == 422
        assert error.error_type == "validation_error"

    def test_validation_error_inherits_correctly(self):
        """Test ValidationError inheritance."""
        error = ValidationError("Field validation failed")

        assert isinstance(error, ClaudeLensException)
        assert isinstance(error, ValidationError)
        assert isinstance(error, Exception)

    def test_validation_error_can_be_raised(self):
        """Test that ValidationError can be raised and caught."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Email format is invalid")

        assert exc_info.value.detail == "Email format is invalid"
        assert exc_info.value.status_code == 422

    def test_validation_error_with_empty_detail(self):
        """Test ValidationError with empty detail."""
        error = ValidationError("")

        assert error.detail == ""
        assert error.status_code == 422
        assert error.error_type == "validation_error"

    def test_validation_error_with_long_detail(self):
        """Test ValidationError with long detail message."""
        long_message = "This is a very long validation error message " * 10
        error = ValidationError(long_message)

        assert error.detail == long_message
        assert error.status_code == 422


class TestAuthenticationError:
    """Test cases for AuthenticationError."""

    def test_authentication_error_with_default_message(self):
        """Test AuthenticationError with default message."""
        error = AuthenticationError()

        assert str(error) == "Authentication required"
        assert error.detail == "Authentication required"
        assert error.status_code == 401
        assert error.error_type == "authentication_error"

    def test_authentication_error_with_custom_message(self):
        """Test AuthenticationError with custom message."""
        error = AuthenticationError("Invalid credentials provided")

        assert str(error) == "Invalid credentials provided"
        assert error.detail == "Invalid credentials provided"
        assert error.status_code == 401
        assert error.error_type == "authentication_error"

    def test_authentication_error_inherits_correctly(self):
        """Test AuthenticationError inheritance."""
        error = AuthenticationError()

        assert isinstance(error, ClaudeLensException)
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, Exception)

    def test_authentication_error_can_be_raised(self):
        """Test that AuthenticationError can be raised and caught."""
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError("Token expired")

        assert exc_info.value.detail == "Token expired"
        assert exc_info.value.status_code == 401

    def test_authentication_error_with_empty_detail(self):
        """Test AuthenticationError with empty detail."""
        error = AuthenticationError("")

        assert error.detail == ""
        assert error.status_code == 401


class TestAuthorizationError:
    """Test cases for AuthorizationError."""

    def test_authorization_error_with_default_message(self):
        """Test AuthorizationError with default message."""
        error = AuthorizationError()

        assert str(error) == "Insufficient permissions"
        assert error.detail == "Insufficient permissions"
        assert error.status_code == 403
        assert error.error_type == "authorization_error"

    def test_authorization_error_with_custom_message(self):
        """Test AuthorizationError with custom message."""
        error = AuthorizationError("Access denied to this resource")

        assert str(error) == "Access denied to this resource"
        assert error.detail == "Access denied to this resource"
        assert error.status_code == 403
        assert error.error_type == "authorization_error"

    def test_authorization_error_inherits_correctly(self):
        """Test AuthorizationError inheritance."""
        error = AuthorizationError()

        assert isinstance(error, ClaudeLensException)
        assert isinstance(error, AuthorizationError)
        assert isinstance(error, Exception)

    def test_authorization_error_can_be_raised(self):
        """Test that AuthorizationError can be raised and caught."""
        with pytest.raises(AuthorizationError) as exc_info:
            raise AuthorizationError("Admin privileges required")

        assert exc_info.value.detail == "Admin privileges required"
        assert exc_info.value.status_code == 403

    def test_authorization_error_with_none_detail(self):
        """Test AuthorizationError with None detail falls back to default."""
        # This tests the default parameter behavior
        error = AuthorizationError()
        assert error.detail == "Insufficient permissions"


class TestRateLimitError:
    """Test cases for RateLimitError."""

    def test_rate_limit_error_with_default_message(self):
        """Test RateLimitError with default message."""
        error = RateLimitError()

        assert str(error) == "Rate limit exceeded"
        assert error.detail == "Rate limit exceeded"
        assert error.status_code == 429
        assert error.error_type == "rate_limit_error"

    def test_rate_limit_error_with_custom_message(self):
        """Test RateLimitError with custom message."""
        error = RateLimitError("Too many requests, please try again later")

        assert str(error) == "Too many requests, please try again later"
        assert error.detail == "Too many requests, please try again later"
        assert error.status_code == 429
        assert error.error_type == "rate_limit_error"

    def test_rate_limit_error_inherits_correctly(self):
        """Test RateLimitError inheritance."""
        error = RateLimitError()

        assert isinstance(error, ClaudeLensException)
        assert isinstance(error, RateLimitError)
        assert isinstance(error, Exception)

    def test_rate_limit_error_can_be_raised(self):
        """Test that RateLimitError can be raised and caught."""
        with pytest.raises(RateLimitError) as exc_info:
            raise RateLimitError("Request quota exceeded")

        assert exc_info.value.detail == "Request quota exceeded"
        assert exc_info.value.status_code == 429

    def test_rate_limit_error_with_empty_detail(self):
        """Test RateLimitError with empty detail."""
        error = RateLimitError("")

        assert error.detail == ""
        assert error.status_code == 429


class TestExceptionInteroperability:
    """Test cases for exception interoperability."""

    def test_all_exceptions_can_be_caught_as_base_exception(self):
        """Test that all custom exceptions can be caught as ClaudeLensException."""
        exceptions = [
            NotFoundError("Resource"),
            ValidationError("Invalid data"),
            AuthenticationError("Auth failed"),
            AuthorizationError("Not authorized"),
            RateLimitError("Rate limited"),
        ]

        for exc in exceptions:
            with pytest.raises(ClaudeLensException):
                raise exc

    def test_exception_type_checking(self):
        """Test exception type checking works correctly."""
        not_found = NotFoundError("Item")
        validation = ValidationError("Invalid")

        assert isinstance(not_found, NotFoundError)
        assert not isinstance(not_found, ValidationError)
        assert isinstance(validation, ValidationError)
        assert not isinstance(validation, NotFoundError)

    def test_exception_attributes_preserved_in_inheritance(self):
        """Test that attributes are preserved through inheritance chain."""
        error = NotFoundError("User", "123")

        # Can access as NotFoundError
        assert error.detail == "User with id '123' not found"

        # Can access as ClaudeLensException
        base_error: ClaudeLensException = error
        assert base_error.detail == "User with id '123' not found"
        assert base_error.status_code == 404
        assert base_error.error_type == "not_found"

    def test_multiple_exception_handling(self):
        """Test handling multiple exception types."""

        def raise_different_errors(error_type: str):
            if error_type == "not_found":
                raise NotFoundError("Item")
            elif error_type == "validation":
                raise ValidationError("Invalid input")
            elif error_type == "auth":
                raise AuthenticationError("Not authenticated")
            else:
                raise ClaudeLensException("Unknown error")

        # Test specific exception handling
        with pytest.raises(NotFoundError):
            raise_different_errors("not_found")

        with pytest.raises(ValidationError):
            raise_different_errors("validation")

        with pytest.raises(AuthenticationError):
            raise_different_errors("auth")

        # Test generic exception handling
        with pytest.raises(ClaudeLensException):
            raise_different_errors("unknown")

    def test_exception_chaining(self):
        """Test exception chaining works correctly."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise ValidationError("Validation failed") from e
        except ValidationError as ve:
            assert ve.detail == "Validation failed"
            assert isinstance(ve.__cause__, ValueError)
            assert str(ve.__cause__) == "Original error"
