"""Configuration management for ClaudeLens CLI."""
import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError
from rich.console import Console

from claudelens_cli import __version__

console = Console()


class CLIConfig(BaseModel):
    """CLI configuration model."""
    
    api_url: str = Field(
        default="http://localhost:8000",
        description="ClaudeLens API URL"
    )
    api_key: str | None = Field(
        default=None,
        description="API key for authentication"
    )
    claude_dirs: list[Path] = Field(
        default_factory=lambda: [Path.home() / ".claude"],
        description="Claude data directories to sync from"
    )
    sync_interval: int = Field(
        default=300,
        description="Sync interval in seconds for watch mode"
    )
    batch_size: int = Field(
        default=100,
        description="Number of messages to sync in one batch"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    sync_types: list[str] = Field(
        default=["projects", "todos", "database"],
        description="Data types to sync"
    )
    exclude_projects: list[str] = Field(
        default_factory=list,
        description="Project paths to exclude from sync"
    )
    
    class Config:
        validate_assignment = True
    
    @property
    def claude_dir(self) -> Path:
        """Backward compatibility property for single claude_dir."""
        return self.claude_dirs[0] if self.claude_dirs else Path.home() / ".claude"


class ConfigManager:
    """Manages CLI configuration."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".claudelens"
        self.config_file = self.config_dir / "config.json"
        self.config: CLIConfig = self._load_config()
    
    def _load_config(self) -> CLIConfig:
        """Load configuration from file or create default."""
        # First, try environment variables
        env_config: dict[str, Any] = {}
        if api_url := os.getenv("CLAUDELENS_API_URL"):
            env_config["api_url"] = api_url
        if api_key := os.getenv("CLAUDELENS_API_KEY"):
            env_config["api_key"] = api_key
        if claude_dir := os.getenv("CLAUDE_DIR"):
            # Support comma-separated paths for multiple directories
            if "," in claude_dir:
                env_config["claude_dirs"] = [Path(d.strip()) for d in claude_dir.split(",")]
            else:
                env_config["claude_dirs"] = [Path(claude_dir.strip())]
        elif claude_dirs := os.getenv("CLAUDE_DIRS"):
            # Alternative env var for multiple directories
            env_config["claude_dirs"] = [Path(d.strip()) for d in claude_dirs.split(",")]
        
        # Then, load from file
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    file_config = json.load(f)
                # Environment variables override file config
                file_config.update(env_config)
                return CLIConfig(**file_config)
            except (json.JSONDecodeError, ValidationError) as e:
                console.print(f"[yellow]Warning: Invalid config file: {e}[/yellow]")
        
        # Create default config with env overrides
        return CLIConfig(**env_config)
    
    def save(self) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(
                self.config.model_dump(mode="json"),
                f,
                indent=2,
                default=str
            )
        console.print(f"[green]Configuration saved to {self.config_file}[/green]")
    
    def update(self, **kwargs) -> None:
        """Update configuration values."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save()
    
    def get_headers(self) -> dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {"User-Agent": f"ClaudeLens-CLI/{__version__}"}
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key
        return headers


# Global config instance
config_manager = ConfigManager()