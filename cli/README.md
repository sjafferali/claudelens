# ClaudeLens CLI

CLI tool for syncing Claude conversations to ClaudeLens server.

## Installation

```bash
pip install claudelens-cli
```

## Usage

```bash
# Show status
claudelens status

# Configure API settings
claudelens config set api_url http://localhost:8000
claudelens config set api_key your-api-key

# Sync conversations
claudelens sync

# Watch for changes
claudelens sync --watch
```

## Development

```bash
# Install dependencies
poetry install

# Run the CLI
poetry run claudelens --help
```