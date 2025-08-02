"""Status command implementation."""
from datetime import datetime
from pathlib import Path

import click
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from claudelens_cli.core.config import config_manager
from claudelens_cli.core.state import StateManager

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