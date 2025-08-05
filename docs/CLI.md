# ClaudeLens CLI Reference

The ClaudeLens CLI tool provides powerful automation for synchronizing your Claude conversations with the ClaudeLens server. This comprehensive reference covers installation, configuration, commands, and advanced usage patterns.

## Table of Contents
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Commands Reference](#commands-reference)
- [Usage Patterns](#usage-patterns)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

## Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Access to a running ClaudeLens server

### Install from PyPI
```bash
pip install claudelens-cli
```

### Verify Installation
```bash
claudelens version
```

### Development Installation
```bash
git clone https://github.com/sjafferali/claudelens.git
cd claudelens/cli
poetry install
poetry run claudelens --help
```

## Quick Start

### 1. Basic Configuration
```bash
# Set your ClaudeLens server URL
claudelens config set api_url http://localhost:8000

# Set your API key (if authentication is enabled)
claudelens config set api_key your-api-key-here

# Add your Claude directory
claudelens config add-claude-dir ~/.claude
```

### 2. Test Configuration
```bash
# Verify configuration
claudelens config show

# Test sync with dry run
claudelens sync --dry-run
```

### 3. Perform Initial Sync
```bash
# Sync all conversations
claudelens sync

# Check sync status
claudelens status
```

### 4. Enable Continuous Sync (Recommended)
```bash
# Start watching for changes
claudelens sync --watch
```

## Configuration

### Configuration Management

The CLI stores configuration in `~/.claudelens/config.json`. You can manage settings using the `config` command.

#### View Current Configuration
```bash
claudelens config show
```

#### Set Configuration Values
```bash
# Set API URL
claudelens config set api_url http://localhost:8000
claudelens config set api_url https://your-server.com

# Set API key for authentication
claudelens config set api_key your-secure-api-key

# Set default sync options
claudelens config set watch_mode true
claudelens config set dry_run false
claudelens config set overwrite false
```

#### Manage Claude Directories
```bash
# Add a Claude directory
claudelens config add-claude-dir ~/.claude
claudelens config add-claude-dir /path/to/project/.claude
claudelens config add-claude-dir "/path/with spaces/.claude"

# Remove a Claude directory
claudelens config remove-claude-dir ~/.claude

# List all configured directories
claudelens config show
```

#### Reset Configuration
```bash
# Reset all configuration to defaults
claudelens config reset
```

### Environment Variable Override

Configuration can be overridden using environment variables:

```bash
# Override API settings
export CLAUDELENS_API_URL=https://production-server.com
export CLAUDELENS_API_KEY=production-api-key

# Override Claude directories
export CLAUDE_DIRS="/path/to/claude1,/path/to/claude2"

# Override specific directory
export CLAUDE_DIR=~/.claude

# Run with environment overrides
claudelens sync
```

### Configuration File Format

The configuration file (`~/.claudelens/config.json`) structure:

```json
{
  "api_url": "http://localhost:8000",
  "api_key": "your-api-key",
  "claude_dirs": [
    "/Users/username/.claude",
    "/path/to/project/.claude"
  ],
  "sync_options": {
    "watch_mode": false,
    "dry_run": false,
    "overwrite": false,
    "debug": false
  },
  "created_at": "2025-08-05T10:30:00Z",
  "last_updated": "2025-08-05T12:15:00Z"
}
```

## Commands Reference

### `claudelens sync`

Synchronize Claude conversations with the ClaudeLens server.

**Usage:**
```bash
claudelens sync [OPTIONS]
```

**Options:**
- `--watch, -w` - Continuously monitor for changes and sync automatically
- `--project, -p PATH` - Sync only a specific project directory
- `--force, -f` - Force re-sync all conversations, ignoring timestamps
- `--dry-run` - Show what would be synced without actually syncing
- `--claude-dir, -d PATH` - Override configured Claude directory
- `--debug` - Enable verbose debug output
- `--overwrite` - Update existing messages on UUID conflicts
- `--api-key TEXT` - Override configured API key
- `--api-url TEXT` - Override configured API URL

**Examples:**
```bash
# Basic sync
claudelens sync

# Continuous monitoring (recommended for active development)
claudelens sync --watch

# Sync specific project only
claudelens sync --project /path/to/specific/project

# Debug sync issues
claudelens sync --debug --dry-run

# Force complete re-sync
claudelens sync --force

# Override API settings for one sync
claudelens sync --api-key prod-key --api-url https://prod-server.com

# Sync specific Claude directory
claudelens sync --claude-dir /custom/claude/path
```

### `claudelens status`

Display sync status and statistics.

**Usage:**
```bash
claudelens status [OPTIONS]
```

**Options:**
- `--detailed, -d` - Show detailed statistics and information

**Examples:**
```bash
# Basic status
claudelens status

# Detailed status with statistics
claudelens status --detailed
```

**Sample Output:**
```
ClaudeLens Sync Status
=====================

Configuration:
  API URL: http://localhost:8000
  API Key: ****-****-****-****
  Claude Directories: 2

Directory Status:
  ~/.claude: 1,234 conversations, last sync: 2 minutes ago
  /project/.claude: 456 conversations, last sync: 5 minutes ago

Last Sync:
  Status: Success
  Duration: 12.3 seconds
  Messages Synced: 89
  Errors: 0

Server Status:
  Connection: Healthy
  Response Time: 45ms
  Version: 0.1.0
```

### `claudelens config`

Manage CLI configuration settings.

**Usage:**
```bash
claudelens config SUBCOMMAND [OPTIONS]
```

**Subcommands:**

#### `show` - Display current configuration
```bash
claudelens config show
```

#### `set KEY VALUE` - Set a configuration value
```bash
claudelens config set api_url http://localhost:8000
claudelens config set api_key your-api-key
claudelens config set watch_mode true
claudelens config set debug false
```

#### `add-claude-dir PATH` - Add a Claude directory
```bash
claudelens config add-claude-dir ~/.claude
claudelens config add-claude-dir "/path/with spaces/.claude"
```

#### `remove-claude-dir PATH` - Remove a Claude directory
```bash
claudelens config remove-claude-dir ~/.claude
```

#### `reset` - Reset all configuration
```bash
claudelens config reset
```

### `claudelens version`

Display version information.

**Usage:**
```bash
claudelens version
```

**Sample Output:**
```
ClaudeLens CLI v0.1.0

Python: 3.11.5
Platform: macOS-14.0-arm64
Config Location: /Users/username/.claudelens/config.json
Installation: pip (package)

Dependencies:
  click: 8.2.0
  httpx: 0.28.0
  rich: 13.6.0
  watchdog: 6.0.0
```

## Usage Patterns

### First-time Setup Workflow

Complete setup for new installations:

```bash
# 1. Configure API connection
claudelens config set api_url http://localhost:8000
claudelens config set api_key your-api-key

# 2. Add Claude directories
claudelens config add-claude-dir ~/.claude

# 3. Test configuration
claudelens config show
claudelens status

# 4. Test sync (without actually syncing)
claudelens sync --dry-run

# 5. Perform initial sync
claudelens sync

# 6. Check results
claudelens status --detailed
```

### Daily Development Workflow

Typical daily usage for active development:

```bash
# Morning: Check status and sync new conversations
claudelens status
claudelens sync

# Start continuous monitoring for the day
claudelens sync --watch

# The CLI will now automatically sync new conversations as they're created
```

### Continuous Monitoring Workflow

Set up automatic synchronization:

```bash
# Start continuous sync in the background
nohup claudelens sync --watch > ~/.claudelens/sync.log 2>&1 &

# Check sync status periodically
claudelens status

# View sync logs
tail -f ~/.claudelens/sync.log
```

### Project-specific Workflow

Working on specific projects:

```bash
# Add project-specific Claude directory
claudelens config add-claude-dir /project/path/.claude

# Sync only specific project
claudelens sync --project /project/path

# Monitor only specific project
claudelens sync --watch --project /project/path

# Check project status
claudelens status --detailed
```

### Troubleshooting Workflow

Debug sync issues systematically:

```bash
# 1. Check configuration
claudelens config show

# 2. Test server connectivity
claudelens status

# 3. Debug sync process
claudelens sync --debug --dry-run

# 4. Check what would be synced
claudelens sync --dry-run

# 5. Force resync if needed
claudelens sync --force

# 6. Check detailed status
claudelens status --detailed
```

## Advanced Features

### Multiple Claude Directories

Support for complex development workflows:

```bash
# Add multiple directories
claudelens config add-claude-dir ~/.claude
claudelens config add-claude-dir /work/project1/.claude
claudelens config add-claude-dir /work/project2/.claude
claudelens config add-claude-dir "/projects/client work/.claude"

# Sync all directories
claudelens sync

# Sync specific directory only
claudelens sync --claude-dir /work/project1/.claude

# Use environment variable for batch operations
export CLAUDE_DIRS="/path1/.claude,/path2/.claude"
claudelens sync
```

### Watch Mode Features

Advanced continuous monitoring:

```bash
# Basic watch mode
claudelens sync --watch

# Watch with debug output
claudelens sync --watch --debug

# Watch specific project
claudelens sync --watch --project /path/to/project

# Watch with force refresh periodically
claudelens sync --watch --force
```

**Watch Mode Behavior:**
- Monitors file system changes in configured Claude directories
- Automatically syncs new conversation files as they're created
- Handles file modifications and updates existing conversations
- Provides real-time feedback on sync operations
- Gracefully handles temporary network issues with retry logic

### Batch Operations

Efficient handling of large datasets:

```bash
# Force sync all conversations (useful after server reset)
claudelens sync --force

# Sync with overwrite (update existing conversations)
claudelens sync --overwrite

# Debug batch sync issues
claudelens sync --debug --force

# Dry run for large batches
claudelens sync --dry-run --force
```

### Configuration Profiles

Multiple configuration support:

```bash
# Set up production profile
export CLAUDELENS_API_URL=https://prod-claudelens.company.com
export CLAUDELENS_API_KEY=prod-api-key
claudelens sync

# Set up development profile
export CLAUDELENS_API_URL=http://localhost:8000
export CLAUDELENS_API_KEY=dev-api-key
claudelens sync

# Create shell aliases for different environments
alias claudelens-prod="CLAUDELENS_API_URL=https://prod.com CLAUDELENS_API_KEY=prod-key claudelens"
alias claudelens-dev="CLAUDELENS_API_URL=http://localhost:8000 CLAUDELENS_API_KEY=dev-key claudelens"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. CLI sync fails with connection error

**Symptoms:**
```
Error: Connection failed - Could not connect to ClaudeLens server
```

**Solutions:**
```bash
# Check configuration
claudelens config show

# Verify server is running
curl http://localhost:8000/api/v1/health

# Test with explicit URL
claudelens sync --api-url http://localhost:8000

# Check network connectivity
ping localhost
```

#### 2. No conversations found during sync

**Symptoms:**
```
No conversations found in directory: ~/.claude
```

**Solutions:**
```bash
# Verify Claude directory exists and has content
ls -la ~/.claude
ls -la ~/.claude/conversations

# Check directory configuration
claudelens config show

# Add correct directory
claudelens config add-claude-dir /correct/path/to/.claude

# Use explicit directory
claudelens sync --claude-dir /path/to/claude
```

#### 3. Authentication errors

**Symptoms:**
```
Error: Authentication failed - Invalid API key
```

**Solutions:**
```bash
# Check API key configuration
claudelens config show

# Set correct API key
claudelens config set api_key your-correct-api-key

# Test with temporary key
claudelens sync --api-key test-key

# Verify server API key configuration
curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/health
```

#### 4. Permission errors

**Symptoms:**
```
Error: Permission denied accessing ~/.claude
```

**Solutions:**
```bash
# Check directory permissions
ls -la ~/.claude

# Fix permissions
chmod 755 ~/.claude
chmod 644 ~/.claude/*

# Run with sudo if necessary (not recommended)
sudo claudelens sync
```

#### 5. Sync shows duplicate messages

**Explanation:** This is normal behavior for forked conversations in Claude, where messages are shared across multiple conversation threads.

**Solutions:**
```bash
# Use overwrite mode to update existing messages
claudelens sync --overwrite

# Force resync to ensure consistency
claudelens sync --force --overwrite

# Check server for duplicate handling
claudelens status --detailed
```

### Debug Mode

Enable comprehensive debugging:

```bash
# Debug sync process
claudelens sync --debug

# Debug with dry run
claudelens sync --debug --dry-run

# Debug watch mode
claudelens sync --watch --debug

# Debug configuration
claudelens config show
claudelens status --detailed
```

**Debug Output Includes:**
- File system operations and directory scanning
- HTTP requests and responses to/from server
- Conversation parsing and validation
- Error details and stack traces
- Performance timing information

### Performance Troubleshooting

#### Slow sync performance

```bash
# Check directory size
du -sh ~/.claude

# Monitor sync progress with debug
claudelens sync --debug

# Sync specific smaller projects
claudelens sync --project /smaller/project

# Use watch mode for incremental updates
claudelens sync --watch
```

#### High memory usage

```bash
# Monitor memory usage
top -p $(pgrep -f claudelens)

# Sync smaller batches
claudelens sync --project /specific/project

# Restart CLI if long-running
pkill -f claudelens
claudelens sync --watch
```

### Log Files and Diagnostics

#### Log locations
```bash
# Default log location (if configured)
~/.claudelens/logs/claudelens.log

# Watch mode log (if run in background)
~/.claudelens/sync.log

# View recent logs
tail -f ~/.claudelens/logs/claudelens.log
```

#### Diagnostic information
```bash
# System information
claudelens version

# Configuration dump
claudelens config show

# Status with details
claudelens status --detailed

# Test connectivity
curl -v http://localhost:8000/api/v1/health
```

## Examples

### Complete Setup Example

```bash
#!/bin/bash
# setup-claudelens.sh - Complete ClaudeLens CLI setup script

echo "Setting up ClaudeLens CLI..."

# Install CLI
pip install claudelens-cli

# Configure API connection
claudelens config set api_url http://localhost:8000
claudelens config set api_key $(openssl rand -hex 16)

# Add Claude directories
claudelens config add-claude-dir ~/.claude
claudelens config add-claude-dir ~/.cursor/claude
claudelens config add-claude-dir ~/work/.claude

# Test configuration
echo "Testing configuration..."
claudelens config show
claudelens status

# Perform initial sync
echo "Performing initial sync..."
claudelens sync --dry-run
claudelens sync

# Start background sync
echo "Starting background sync..."
nohup claudelens sync --watch > ~/.claudelens/sync.log 2>&1 &

echo "Setup complete! Check status with: claudelens status"
```

### Monitoring Script Example

```bash
#!/bin/bash
# monitor-sync.sh - Monitor ClaudeLens sync status

while true; do
    clear
    echo "ClaudeLens Sync Monitor - $(date)"
    echo "=================================="

    claudelens status --detailed

    echo ""
    echo "Recent sync log:"
    tail -n 10 ~/.claudelens/sync.log 2>/dev/null || echo "No sync log found"

    sleep 30
done
```

### Multi-environment Example

```bash
#!/bin/bash
# multi-env-sync.sh - Sync across multiple environments

# Development environment
echo "Syncing development environment..."
CLAUDELENS_API_URL=http://localhost:8000 \
CLAUDELENS_API_KEY=dev-key \
claudelens sync

# Staging environment
echo "Syncing staging environment..."
CLAUDELENS_API_URL=https://staging-claudelens.company.com \
CLAUDELENS_API_KEY=staging-key \
claudelens sync

# Production environment
echo "Syncing production environment..."
CLAUDELENS_API_URL=https://claudelens.company.com \
CLAUDELENS_API_KEY=prod-key \
claudelens sync

echo "Multi-environment sync complete!"
```

---

For additional help and support, see the [main documentation](../README.md) or the [troubleshooting guide](../README.md#troubleshooting).
