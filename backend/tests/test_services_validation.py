"""Tests for the message validation service."""

from app.services.validation import MessageValidator


class TestMessageValidator:
    """Test cases for MessageValidator."""

    def test_validate_valid_message(self):
        """Test validation of a complete valid message."""
        valid_message = {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "type": "user",
            "timestamp": "2025-01-01T00:00:00Z",
            "sessionId": "session-123",
            "message": {"content": "Hello"},
        }
        errors = MessageValidator.validate_message(valid_message)
        assert errors == []

    def test_validate_missing_uuid(self):
        """Test validation when uuid is missing."""
        message = {
            "type": "user",
            "timestamp": "2025-01-01T00:00:00Z",
            "sessionId": "session-123",
        }
        errors = MessageValidator.validate_message(message)
        assert "Missing required field: uuid" in errors

    def test_validate_invalid_uuid_format(self):
        """Test validation with invalid UUID format."""
        message = {
            "uuid": "invalid-uuid",
            "type": "user",
            "timestamp": "2025-01-01T00:00:00Z",
            "sessionId": "session-123",
        }
        errors = MessageValidator.validate_message(message)
        assert "Invalid UUID format" in errors

    def test_validate_missing_type(self):
        """Test validation when type is missing."""
        message = {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "timestamp": "2025-01-01T00:00:00Z",
            "sessionId": "session-123",
        }
        errors = MessageValidator.validate_message(message)
        assert "Missing required field: type" in errors

    def test_validate_invalid_type(self):
        """Test validation with invalid message type."""
        message = {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "type": "invalid_type",
            "timestamp": "2025-01-01T00:00:00Z",
            "sessionId": "session-123",
        }
        errors = MessageValidator.validate_message(message)
        assert any("Invalid message type" in error for error in errors)

    def test_validate_missing_timestamp(self):
        """Test validation when timestamp is missing."""
        message = {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "type": "user",
            "sessionId": "session-123",
        }
        errors = MessageValidator.validate_message(message)
        assert "Missing required field: timestamp" in errors

    def test_validate_missing_session_id(self):
        """Test validation when sessionId is missing."""
        message = {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "type": "user",
            "timestamp": "2025-01-01T00:00:00Z",
        }
        errors = MessageValidator.validate_message(message)
        assert "Missing required field: sessionId" in errors

    def test_validate_assistant_message_without_message_field(self):
        """Test validation of assistant message without message field."""
        message = {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "type": "assistant",
            "timestamp": "2025-01-01T00:00:00Z",
            "sessionId": "session-123",
        }
        errors = MessageValidator.validate_message(message)
        assert "Assistant messages must have 'message' field" in errors

    def test_validate_assistant_message_with_message_field(self):
        """Test validation of assistant message with message field."""
        message = {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "type": "assistant",
            "timestamp": "2025-01-01T00:00:00Z",
            "sessionId": "session-123",
            "message": {"content": "Response"},
        }
        errors = MessageValidator.validate_message(message)
        assert errors == []

    def test_validate_cost_valid(self):
        """Test validation with valid cost value."""
        message = {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "type": "user",
            "timestamp": "2025-01-01T00:00:00Z",
            "sessionId": "session-123",
            "costUsd": "0.005",
        }
        errors = MessageValidator.validate_message(message)
        assert errors == []

    def test_validate_cost_negative(self):
        """Test validation with negative cost value."""
        message = {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "type": "user",
            "timestamp": "2025-01-01T00:00:00Z",
            "sessionId": "session-123",
            "costUsd": -1,
        }
        errors = MessageValidator.validate_message(message)
        assert "Cost value out of reasonable range" in errors

    def test_validate_cost_too_high(self):
        """Test validation with excessively high cost value."""
        message = {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "type": "user",
            "timestamp": "2025-01-01T00:00:00Z",
            "sessionId": "session-123",
            "costUsd": 101,
        }
        errors = MessageValidator.validate_message(message)
        assert "Cost value out of reasonable range" in errors

    def test_validate_cost_invalid_type(self):
        """Test validation with invalid cost type."""
        message = {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "type": "user",
            "timestamp": "2025-01-01T00:00:00Z",
            "sessionId": "session-123",
            "costUsd": "invalid",
        }
        errors = MessageValidator.validate_message(message)
        assert "Invalid cost value" in errors

    def test_validate_all_valid_types(self):
        """Test that all valid message types are accepted."""
        base_message = {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "timestamp": "2025-01-01T00:00:00Z",
            "sessionId": "session-123",
        }

        for msg_type in MessageValidator.VALID_TYPES:
            message = {**base_message, "type": msg_type}
            if msg_type == "assistant":
                message["message"] = {"content": "Response"}
            errors = MessageValidator.validate_message(message)
            assert errors == [], f"Type {msg_type} should be valid"

    def test_sanitize_message_removes_script_tags(self):
        """Test that sanitize_message removes script tags."""
        message = {"message": {"content": "Hello <script>alert('xss')</script> World"}}
        sanitized = MessageValidator.sanitize_message(message)
        assert "<script>" not in sanitized["message"]["content"]
        assert "alert" not in sanitized["message"]["content"]
        assert "Hello  World" in sanitized["message"]["content"]

    def test_sanitize_message_case_insensitive(self):
        """Test that sanitize_message handles different case script tags."""
        message = {"message": {"content": "Test <SCRIPT>alert('xss')</SCRIPT> content"}}
        sanitized = MessageValidator.sanitize_message(message)
        assert "<SCRIPT>" not in sanitized["message"]["content"]
        assert "<script>" not in sanitized["message"]["content"]

    def test_sanitize_message_multiline_script(self):
        """Test sanitization of multiline script tags."""
        message = {
            "message": {
                "content": """Before <script>
                    alert('xss');
                    console.log('test');
                </script> After"""
            }
        }
        sanitized = MessageValidator.sanitize_message(message)
        assert "<script>" not in sanitized["message"]["content"]
        assert "alert" not in sanitized["message"]["content"]
        assert "Before" in sanitized["message"]["content"]
        assert "After" in sanitized["message"]["content"]

    def test_sanitize_message_no_content(self):
        """Test sanitization when message has no content field."""
        message = {"message": {"role": "user"}}
        sanitized = MessageValidator.sanitize_message(message)
        assert sanitized == message

    def test_sanitize_message_not_dict(self):
        """Test sanitization when message field is not a dict."""
        message = {"message": "Simple string message"}
        sanitized = MessageValidator.sanitize_message(message)
        assert sanitized == message

    def test_sanitize_preserves_other_fields(self):
        """Test that sanitization preserves other message fields."""
        message = {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "type": "user",
            "message": {"content": "Normal content", "role": "user"},
        }
        sanitized = MessageValidator.sanitize_message(message)
        assert sanitized["uuid"] == message["uuid"]
        assert sanitized["type"] == message["type"]
        assert sanitized["message"]["role"] == message["message"]["role"]
