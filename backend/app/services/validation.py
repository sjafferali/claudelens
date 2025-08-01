"""Message validation service."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from app.core.exceptions import ValidationError


class MessageValidator:
    """Validates Claude messages."""
    
    # Valid message types
    VALID_TYPES = {"user", "assistant", "system", "tool", "summary"}
    
    # UUID pattern
    UUID_PATTERN = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    @classmethod
    def validate_message(cls, message: Dict[str, Any]) -> List[str]:
        """Validate a message and return list of errors."""
        errors = []
        
        # Required fields
        if "uuid" not in message:
            errors.append("Missing required field: uuid")
        elif not cls.UUID_PATTERN.match(str(message["uuid"])):
            errors.append("Invalid UUID format")
        
        if "type" not in message:
            errors.append("Missing required field: type")
        elif message["type"] not in cls.VALID_TYPES:
            errors.append(f"Invalid message type: {message['type']}")
        
        if "timestamp" not in message:
            errors.append("Missing required field: timestamp")
        
        if "sessionId" not in message:
            errors.append("Missing required field: sessionId")
        
        # Type-specific validation
        if message.get("type") == "assistant":
            if "message" not in message:
                errors.append("Assistant messages must have 'message' field")
        
        # Cost validation
        if "costUsd" in message:
            try:
                cost = float(message["costUsd"])
                if cost < 0 or cost > 100:  # Sanity check
                    errors.append("Cost value out of reasonable range")
            except (TypeError, ValueError):
                errors.append("Invalid cost value")
        
        return errors
    
    @classmethod
    def sanitize_message(cls, message: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize message content."""
        # Remove any potential XSS or injection attempts
        if "message" in message and isinstance(message["message"], dict):
            if "content" in message["message"]:
                # Basic sanitization - in production use a proper library
                content = str(message["message"]["content"])
                # Remove script tags
                content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
                message["message"]["content"] = content
        
        return message