# Task 06: CLI Core Structure and Base Implementation

## Status
**Status:** TODO  
**Priority:** High  
**Estimated Time:** 3 hours

## Purpose
Build the foundation of the ClaudeLens CLI tool that will monitor the local Claude directory and sync conversations to the backend. This includes the core command structure, configuration management, and state tracking.

## Claude Directory Structure

The CLI needs to handle the following Claude data structure:

```
~/.claude/
├── __store.db                  # SQLite database (502MB+)
├── config.json                 # User configuration
├── settings.json               # Application settings
├── projects/                   # Conversation JSONL files
│   ├── -Users-username-project-path/
│   │   └── [session-uuid].jsonl
├── todos/                      # Todo lists
│   └── [session-uuid]-agent-[session-uuid].json
├── shell-snapshots/            # Shell environment captures
├── statsig/                    # Feature flags/analytics
└── commands/                   # Command templates
```

## Current State
- Basic CLI project initialized with Poetry
- No command structure
- No configuration management
- No state tracking implementation

## Target State
- Complete CLI command structure using Click
- Configuration file management for Claude directory path
- State tracking for incremental syncs of JSONL files
- Rich terminal output with progress indicators
- Proper error handling and logging
- Support for multiple Claude data types

## Implementation Details

### 1. CLI Main Entry Point

**`cli/claudelens_cli/__main__.py`:**
```python
"""ClaudeLens CLI main entry point."""
import sys
from claudelens_cli.cli import cli


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### 2. CLI Command Structure

**`cli/claudelens_cli/cli.py`:**
```python
"""Main CLI interface for ClaudeLens."""
import click
from rich.console import Console
from rich.panel import Panel
from claudelens_cli import __version__
from claudelens_cli.commands import sync, status, config as config_cmd

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="claudelens")
@click.pass_context
def cli(ctx):
    """ClaudeLens - Archive and sync your Claude conversations.
    
    A CLI tool to sync your local Claude conversation history to ClaudeLens server
    for archival, search, and visualization.
    """
    ctx.ensure_object(dict)


# Register commands
cli.add_command(sync.sync)
cli.add_command(status.status)
cli.add_command(config_cmd.config)


@cli.command()
def version():
    """Show detailed version information."""
    console.print(Panel.fit(
        f"[bold blue]ClaudeLens CLI[/bold blue]\n"
        f"Version: {__version__}\n"
        f"Python: {sys.version.split()[0]}",
        title="Version Info"
    ))


if __name__ == "__main__":
    cli()
```

### 3. Configuration Management

**`cli/claudelens_cli/core/config.py`:**
```python
"""Configuration management for ClaudeLens CLI."""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
from pydantic import BaseModel, Field, ValidationError
from rich.console import Console

console = Console()


class CLIConfig(BaseModel):
    """CLI configuration model."""
    
    api_url: str = Field(
        default="http://localhost:8000",
        description="ClaudeLens API URL"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication"
    )
    claude_dir: Path = Field(
        default_factory=lambda: Path.home() / ".claude",
        description="Claude data directory"
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
    sync_types: List[str] = Field(
        default=["projects", "todos", "database"],
        description="Data types to sync"
    )
    exclude_projects: List[str] = Field(
        default_factory=list,
        description="Project paths to exclude from sync"
    )
    
    class Config:
        validate_assignment = True


class ConfigManager:
    """Manages CLI configuration."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".claudelens"
        self.config_file = self.config_dir / "config.json"
        self.config: CLIConfig = self._load_config()
    
    def _load_config(self) -> CLIConfig:
        """Load configuration from file or create default."""
        # First, try environment variables
        env_config = {}
        if api_url := os.getenv("CLAUDELENS_API_URL"):
            env_config["api_url"] = api_url
        if api_key := os.getenv("CLAUDELENS_API_KEY"):
            env_config["api_key"] = api_key
        if claude_dir := os.getenv("CLAUDE_DIR"):
            env_config["claude_dir"] = Path(claude_dir)
        
        # Then, load from file
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
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
    
    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {"User-Agent": f"ClaudeLens-CLI/{__version__}"}
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key
        return headers


# Global config instance
config_manager = ConfigManager()
```

### 4. State Management

**`cli/claudelens_cli/core/state.py`:**
```python
"""State management for sync operations."""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Optional, List
from pydantic import BaseModel, Field
import hashlib
from rich.console import Console

console = Console()


class ProjectState(BaseModel):
    """State for a single project."""
    
    last_sync: datetime
    last_file: Optional[str] = None
    last_line: Optional[int] = None
    synced_sessions: Set[str] = Field(default_factory=set)  # Session UUIDs
    synced_messages: Set[str] = Field(default_factory=set)  # Message UUIDs
    message_count: int = 0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            set: lambda v: list(v)
        }


class DatabaseState(BaseModel):
    """State for SQLite database sync."""
    
    last_sync: datetime
    last_message_timestamp: Optional[datetime] = None
    synced_message_count: int = 0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SyncState(BaseModel):
    """Overall sync state."""
    
    version: str = "1.0.0"
    last_sync: Optional[datetime] = None
    projects: Dict[str, ProjectState] = Field(default_factory=dict)
    database_state: Optional[DatabaseState] = None
    synced_todos: Set[str] = Field(default_factory=set)  # Todo file names
    synced_snapshots: Set[str] = Field(default_factory=set)  # Shell snapshot files
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            set: lambda v: list(v)
        }


class StateManager:
    """Manages sync state."""
    
    def __init__(self, state_dir: Optional[Path] = None):
        self.state_dir = state_dir or (Path.home() / ".claudelens")
        self.state_file = self.state_dir / "sync_state.json"
        self.state = self._load_state()
    
    def _load_state(self) -> SyncState:
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                # Convert ISO strings back to datetime
                if data.get("last_sync"):
                    data["last_sync"] = datetime.fromisoformat(data["last_sync"])
                for project_data in data.get("projects", {}).values():
                    project_data["last_sync"] = datetime.fromisoformat(project_data["last_sync"])
                    project_data["synced_hashes"] = set(project_data.get("synced_hashes", []))
                return SyncState(**data)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load state: {e}[/yellow]")
        return SyncState()
    
    def save(self) -> None:
        """Save state to file."""
        self.state_dir.mkdir(exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.state.model_dump(mode="json"), f, indent=2)
    
    def get_project_state(self, project_path: str) -> Optional[ProjectState]:
        """Get state for a specific project."""
        return self.state.projects.get(project_path)
    
    def update_project_state(
        self,
        project_path: str,
        last_file: Optional[str] = None,
        last_line: Optional[int] = None,
        new_hashes: Optional[Set[str]] = None
    ) -> None:
        """Update state for a project."""
        if project_path not in self.state.projects:
            self.state.projects[project_path] = ProjectState(
                last_sync=datetime.utcnow()
            )
        
        project_state = self.state.projects[project_path]
        project_state.last_sync = datetime.utcnow()
        
        if last_file is not None:
            project_state.last_file = last_file
        if last_line is not None:
            project_state.last_line = last_line
        if new_hashes:
            project_state.synced_hashes.update(new_hashes)
            project_state.message_count = len(project_state.synced_hashes)
        
        self.state.last_sync = datetime.utcnow()
        self.save()
    
    def is_message_synced(self, project_path: str, message_hash: str) -> bool:
        """Check if a message has already been synced."""
        project_state = self.get_project_state(project_path)
        if project_state:
            return message_hash in project_state.synced_hashes
        return False
    
    def clear_project(self, project_path: str) -> None:
        """Clear state for a project."""
        if project_path in self.state.projects:
            del self.state.projects[project_path]
            self.save()
    
    @staticmethod
    def hash_message(message: dict) -> str:
        """Generate a hash for a message."""
        # Create a deterministic string representation
        content = json.dumps(message, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content.encode()).hexdigest()
```

### 5. Sync Command Implementation

**`cli/claudelens_cli/commands/sync.py`:**
```python
"""Sync command implementation."""
import click
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from claudelens_cli.core.config import config_manager
from claudelens_cli.core.state import StateManager
from claudelens_cli.core.sync_engine import SyncEngine

console = Console()


@click.command()
@click.option(
    "--watch", "-w",
    is_flag=True,
    help="Watch for changes and sync continuously"
)
@click.option(
    "--project", "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Sync only a specific project"
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Force full sync, ignoring previous state"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be synced without actually syncing"
)
def sync(watch: bool, project: Path, force: bool, dry_run: bool):
    """Sync Claude conversations to ClaudeLens server.
    
    This command scans your local Claude directory for conversation files
    and syncs them to the ClaudeLens server for archival and analysis.
    """
    # Initialize components
    state_manager = StateManager()
    sync_engine = SyncEngine(config_manager, state_manager)
    
    # Show current configuration
    console.print(f"[dim]API URL: {config_manager.config.api_url}[/dim]")
    console.print(f"[dim]Claude directory: {config_manager.config.claude_dir}[/dim]")
    
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No data will be synced[/yellow]")
    
    if force:
        console.print("[yellow]Force sync enabled - all data will be re-synced[/yellow]")
        if project:
            state_manager.clear_project(str(project))
        else:
            state_manager.state.projects.clear()
            state_manager.save()
    
    try:
        if watch:
            # Watch mode
            console.print("[green]Starting watch mode...[/green]")
            console.print("[dim]Press Ctrl+C to stop[/dim]")
            sync_engine.watch(project_filter=project, dry_run=dry_run)
        else:
            # One-time sync
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Syncing conversations...", total=None)
                
                stats = sync_engine.sync_once(
                    project_filter=project,
                    dry_run=dry_run,
                    progress_callback=lambda msg: progress.update(task, description=msg)
                )
                
                progress.update(task, completed=True, description="Sync completed!")
            
            # Show statistics
            _show_sync_stats(stats)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Sync cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Sync failed: {e}[/red]")
        raise click.ClickException(str(e))


def _show_sync_stats(stats: dict):
    """Display sync statistics."""
    console.print("\n[bold]Sync Statistics:[/bold]")
    console.print(f"  Projects scanned: {stats.get('projects_scanned', 0)}")
    console.print(f"  Files processed: {stats.get('files_processed', 0)}")
    console.print(f"  Messages synced: {stats.get('messages_synced', 0)}")
    console.print(f"  Messages skipped: {stats.get('messages_skipped', 0)}")
    console.print(f"  Errors: {stats.get('errors', 0)}")
    console.print(f"  Duration: {stats.get('duration', '0')}s")
```

### 6. Status Command

**`cli/claudelens_cli/commands/status.py`:**
```python
"""Status command implementation."""
import click
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from claudelens_cli.core.config import config_manager
from claudelens_cli.core.state import StateManager
import httpx

console = Console()


@click.command()
@click.option(
    "--detailed", "-d",
    is_flag=True,
    help="Show detailed project-level statistics"
)
def status(detailed: bool):
    """Show sync status and statistics.
    
    Displays information about the last sync, number of synced messages,
    and connection status to the ClaudeLens server.
    """
    state_manager = StateManager()
    
    # Check server connection
    server_status = _check_server_status()
    
    # Create status panel
    status_info = []
    
    # Server status
    if server_status["connected"]:
        status_info.append(f"[green]✓[/green] Server: Connected ({config_manager.config.api_url})")
        status_info.append(f"  Version: {server_status.get('version', 'Unknown')}")
    else:
        status_info.append(f"[red]✗[/red] Server: {server_status.get('error', 'Not connected')}")
    
    # Sync status
    if state_manager.state.last_sync:
        time_since = datetime.utcnow() - state_manager.state.last_sync
        status_info.append(f"\nLast sync: {_format_time_ago(time_since)} ago")
    else:
        status_info.append("\nLast sync: Never")
    
    # Overall statistics
    total_projects = len(state_manager.state.projects)
    total_messages = sum(p.message_count for p in state_manager.state.projects.values())
    status_info.append(f"Projects tracked: {total_projects}")
    status_info.append(f"Total messages synced: {total_messages:,}")
    
    console.print(Panel("\n".join(status_info), title="ClaudeLens Status"))
    
    # Detailed project table
    if detailed and state_manager.state.projects:
        table = Table(title="Project Details")
        table.add_column("Project", style="cyan")
        table.add_column("Last Sync", style="green")
        table.add_column("Messages", justify="right")
        table.add_column("Last File")
        
        for project_path, project_state in state_manager.state.projects.items():
            project_name = Path(project_path).name
            time_since = datetime.utcnow() - project_state.last_sync
            
            table.add_row(
                project_name,
                _format_time_ago(time_since) + " ago",
                str(project_state.message_count),
                project_state.last_file or "N/A"
            )
        
        console.print("\n")
        console.print(table)


def _check_server_status() -> dict:
    """Check connection to ClaudeLens server."""
    try:
        response = httpx.get(
            f"{config_manager.config.api_url}/api/v1/health",
            headers=config_manager.get_headers(),
            timeout=5.0
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "connected": True,
                "version": data.get("version", "Unknown")
            }
        else:
            return {
                "connected": False,
                "error": f"Server returned {response.status_code}"
            }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }


def _format_time_ago(delta) -> str:
    """Format timedelta as human-readable time ago."""
    seconds = int(delta.total_seconds())
    
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''}"
```

### 7. Config Command

**`cli/claudelens_cli/commands/config.py`:**
```python
"""Config command implementation."""
import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from claudelens_cli.core.config import config_manager
from pathlib import Path

console = Console()


@click.group()
def config():
    """Manage ClaudeLens CLI configuration."""
    pass


@config.command()
def show():
    """Show current configuration."""
    table = Table(title="ClaudeLens Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Description", style="dim")
    
    config_dict = config_manager.config.model_dump()
    fields = config_manager.config.model_fields
    
    for key, value in config_dict.items():
        field_info = fields.get(key)
        description = field_info.description if field_info else ""
        
        # Mask API key
        if key == "api_key" and value:
            display_value = value[:8] + "..." + value[-4:]
        else:
            display_value = str(value)
        
        table.add_row(key, display_value, description)
    
    console.print(table)
    console.print(f"\n[dim]Config file: {config_manager.config_file}[/dim]")


@config.command()
@click.argument("key", required=False)
@click.argument("value", required=False)
def set(key: str, value: str):
    """Set a configuration value.
    
    If KEY and VALUE are not provided, enter interactive mode.
    """
    if not key:
        # Interactive mode
        key = Prompt.ask(
            "Configuration key",
            choices=list(config_manager.config.model_fields.keys())
        )
    
    if not value:
        current_value = getattr(config_manager.config, key, None)
        
        if key == "api_key":
            value = Prompt.ask(
                f"Enter {key}",
                password=True,
                default=current_value or ""
            )
        elif key == "claude_dir":
            value = Prompt.ask(
                f"Enter {key}",
                default=str(current_value) if current_value else str(Path.home() / ".claude")
            )
        else:
            value = Prompt.ask(
                f"Enter {key}",
                default=str(current_value) if current_value else ""
            )
    
    # Validate and set
    try:
        if key == "claude_dir":
            value = Path(value)
        elif key in ["sync_interval", "batch_size"]:
            value = int(value)
        
        config_manager.update(**{key: value})
        console.print(f"[green]✓[/green] Set {key} = {value}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to set {key}: {e}")


@config.command()
def reset():
    """Reset configuration to defaults."""
    if Confirm.ask("Are you sure you want to reset all configuration?"):
        config_manager.config = type(config_manager.config)()
        config_manager.save()
        console.print("[green]Configuration reset to defaults[/green]")
```

### 8. Package Initialization

**`cli/claudelens_cli/__init__.py`:**
```python
"""ClaudeLens CLI - Sync your Claude conversations."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from claudelens_cli.cli import cli

__all__ = ["cli", "__version__"]
```

### 9. Update pyproject.toml

**Update `cli/pyproject.toml`:**
```toml
[tool.poetry]
name = "claudelens-cli"
version = "0.1.0"
description = "CLI tool for syncing Claude conversations to ClaudeLens"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
packages = [{include = "claudelens_cli"}]

[tool.poetry.dependencies]
python = "^3.11"
click = "^8.1.0"
httpx = "^0.25.0"
rich = "^13.6.0"
watchdog = "^3.0.0"
pydantic = "^2.4.0"
aiofiles = "^23.2.0"
python-dotenv = "^1.0.0"

[tool.poetry.scripts]
claudelens = "claudelens_cli.__main__:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

## Required Technologies
- Click (CLI framework)
- Rich (terminal formatting)
- Pydantic (data validation)
- httpx (HTTP client)

## Success Criteria
- [ ] CLI entry point working
- [ ] Command structure implemented (sync, status, config)
- [ ] Configuration management with file and env support
- [ ] State tracking for incremental syncs
- [ ] Rich terminal output with progress indication
- [ ] All commands have help text
- [ ] Error handling implemented
- [ ] Can be installed with `pip install -e .`

## Notes
- Use Click for command structure
- Rich provides beautiful terminal output
- State is stored in ~/.claudelens/sync_state.json
- Configuration supports both file and environment variables
- All paths should work cross-platform