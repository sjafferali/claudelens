"""Config command implementation."""
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from claudelens_cli.core.config import config_manager

console = Console()


@click.group()
def config():
    """Manage ClaudeLens CLI configuration."""


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
        parsed_value: Any = value
        if key == "claude_dir":
            parsed_value = Path(value)
        elif key in ["sync_interval", "batch_size"]:
            parsed_value = int(value)
        elif key == "sync_types":
            parsed_value = value.split(",") if isinstance(value, str) else value
        elif key == "exclude_projects":
            parsed_value = value.split(",") if isinstance(value, str) else value
        
        config_manager.update(**{key: parsed_value})
        console.print(f"[green]✓[/green] Set {key} = {parsed_value}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to set {key}: {e}")


@config.command()
def reset():
    """Reset configuration to defaults."""
    if Confirm.ask("Are you sure you want to reset all configuration?"):
        config_manager.config = type(config_manager.config)()
        config_manager.save()
        console.print("[green]Configuration reset to defaults[/green]")