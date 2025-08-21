"""AI-specific configuration and encryption utilities."""

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
        """Validate encryption key."""
        if not v:
            raise ValueError(
                "CLAUDELENS_ENCRYPTION_KEY not configured in environment. "
                "Please add CLAUDELENS_ENCRYPTION_KEY to your .env file. "
                "You can generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        return v

    def get_fernet(self) -> Fernet:
        """Get Fernet instance for encryption/decryption."""
        if not self.claudelens_encryption_key:
            raise ValueError("Encryption key not configured")

        key = self.claudelens_encryption_key

        # Fernet keys must be exactly 32 url-safe base64-encoded bytes
        # which results in a 44-character string
        try:
            # Try to use the key as-is if it's already valid
            return Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            raise ValueError(
                f"Invalid encryption key format. Key must be a valid Fernet key. "
                f"Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'. "
                f"Error: {str(e)}"
            )

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
