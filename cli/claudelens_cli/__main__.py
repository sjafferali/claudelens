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