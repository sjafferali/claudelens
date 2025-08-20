"""AI-specific configuration and encryption utilities."""

import base64
from typing import Optional

from cryptography.fernet import Fernet
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """AI-specific settings with encryption support."""

    # OpenAI Configuration
    claudelens_openai_api_key: Optional[SecretStr] = None
    claudelens_encryption_key: Optional[str] = None
    ai_rate_limit_per_minute: int = 10
    ai_default_model: str = "gpt-4"
    ai_max_tokens: int = 2000
    ai_default_temperature: float = 0.7
    ai_request_timeout: int = 60  # seconds

    # Cost tracking
    gpt4_cost_per_1k_prompt: float = 0.03
    gpt4_cost_per_1k_completion: float = 0.06
    gpt35_cost_per_1k_prompt: float = 0.001
    gpt35_cost_per_1k_completion: float = 0.002

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, env_prefix=""
    )

    @field_validator("claudelens_encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate or generate encryption key."""
        if not v:
            # Generate a new key if not provided
            return base64.urlsafe_b64encode(Fernet.generate_key()).decode()
        return v

    def get_fernet(self) -> Fernet:
        """Get Fernet instance for encryption/decryption."""
        if not self.claudelens_encryption_key:
            raise ValueError("Encryption key not configured")

        # Ensure the key is properly formatted
        key = self.claudelens_encryption_key
        if len(key) < 32:
            # Pad the key if it's too short
            key = base64.urlsafe_b64encode(key.encode().ljust(32)[:32]).decode()
        elif len(key) > 44:
            # Truncate if too long
            key = key[:44]

        try:
            return Fernet(key.encode() if isinstance(key, str) else key)
        except Exception:
            # If the key is invalid, generate a proper one
            new_key = Fernet.generate_key()
            return Fernet(new_key)

    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key."""
        fernet = self.get_fernet()
        return fernet.encrypt(api_key.encode()).decode()

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt an API key."""
        fernet = self.get_fernet()
        return fernet.decrypt(encrypted_key.encode()).decode()

    def calculate_cost(
        self, prompt_tokens: int, completion_tokens: int, model: str = "gpt-4"
    ) -> float:
        """Calculate estimated cost for token usage."""
        if "gpt-4" in model:
            prompt_cost = (prompt_tokens / 1000) * self.gpt4_cost_per_1k_prompt
            completion_cost = (
                completion_tokens / 1000
            ) * self.gpt4_cost_per_1k_completion
        else:  # gpt-3.5-turbo
            prompt_cost = (prompt_tokens / 1000) * self.gpt35_cost_per_1k_prompt
            completion_cost = (
                completion_tokens / 1000
            ) * self.gpt35_cost_per_1k_completion

        return round(prompt_cost + completion_cost, 6)


# Create singleton instance
ai_settings = AISettings()
