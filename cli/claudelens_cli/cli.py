"""Main CLI interface for ClaudeLens."""
import sys

import click
from rich.console import Console
from rich.panel import Panel

from claudelens_cli import __version__
from claudelens_cli.commands import config as config_cmd
from claudelens_cli.commands import status, sync

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
cli.add_command(sync.sync)  # type: ignore[has-type]
cli.add_command(status.status)  # type: ignore[has-type]
cli.add_command(config_cmd.config)  # type: ignore[has-type]


@cli.command()
def version():
    """Show detailed version information."""
    console.print(
        Panel.fit(
            f"[bold blue]ClaudeLens CLI[/bold blue]\n"
            f"Version: {__version__}\n"
            f"Python: {sys.version.split()[0]}",
            title="Version Info",
        )
    )


if __name__ == "__main__":
    cli()
