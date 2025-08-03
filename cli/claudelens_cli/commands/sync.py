"""Sync command implementation."""
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from claudelens_cli.core.config import config_manager
from claudelens_cli.core.state import StateManager
from claudelens_cli.core.sync_engine import SyncEngine

console = Console()


@click.command()
@click.option(
    "--watch", "-w", is_flag=True, help="Watch for changes and sync continuously"
)
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Sync only a specific project",
)
@click.option(
    "--force", "-f", is_flag=True, help="Force full sync, ignoring previous state"
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be synced without actually syncing"
)
@click.option(
    "--claude-dir",
    "-d",
    multiple=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Claude data directory to sync from (can be specified multiple times)",
)
@click.option("--debug", is_flag=True, help="Enable debug output for troubleshooting")
def sync(
    watch: bool,
    project: Path,
    force: bool,
    dry_run: bool,
    claude_dir: tuple[Path],
    debug: bool,
):
    """Sync Claude conversations to ClaudeLens server.

    This command scans your local Claude directory for conversation files
    and syncs them to the ClaudeLens server for archival and analysis.
    """
    # Override claude_dirs if provided via CLI
    if claude_dir:
        # Temporarily update config with CLI-provided directories
        original_dirs = config_manager.config.claude_dirs.copy()
        config_manager.config.claude_dirs = list(claude_dir)

    # Initialize components
    state_manager = StateManager()
    sync_engine = SyncEngine(config_manager, state_manager, debug=debug)

    # Show current configuration
    console.print(f"[dim]API URL: {config_manager.config.api_url}[/dim]")
    if len(config_manager.config.claude_dirs) == 1:
        console.print(
            f"[dim]Claude directory: {config_manager.config.claude_dirs[0]}[/dim]"
        )
    else:
        console.print(
            f"[dim]Claude directories ({len(config_manager.config.claude_dirs)}):[/dim]"
        )
        for dir_path in config_manager.config.claude_dirs:
            console.print(f"[dim]  - {dir_path}[/dim]")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No data will be synced[/yellow]")

    if force:
        console.print(
            "[yellow]Force sync enabled - all data will be re-synced[/yellow]"
        )
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
                console=console,
            ) as progress:
                task = progress.add_task("Syncing conversations...", total=None)

                stats = sync_engine.sync_once(
                    project_filter=project,
                    dry_run=dry_run,
                    progress_callback=lambda msg: progress.update(
                        task, description=msg
                    ),
                )

                progress.update(task, completed=True, description="Sync completed!")

            # Show statistics
            _show_sync_stats(stats)

    except KeyboardInterrupt:
        console.print("\n[yellow]Sync cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Sync failed: {e}[/red]")
        raise click.ClickException(str(e))
    finally:
        # Restore original claude_dirs if they were overridden
        if claude_dir:
            config_manager.config.claude_dirs = original_dirs


def _show_sync_stats(stats: dict):
    """Display sync statistics."""
    console.print("\n[bold]Sync Statistics:[/bold]")
    console.print(f"  Projects scanned: {stats.get('projects_scanned', 0)}")
    console.print(f"  Files processed: {stats.get('files_processed', 0)}")
    console.print(f"  Messages synced: {stats.get('messages_synced', 0)}")
    console.print(f"  Messages skipped: {stats.get('messages_skipped', 0)}")
    console.print(f"  Errors: {stats.get('errors', 0)}")
    console.print(f"  Duration: {stats.get('duration', '0')}s")
