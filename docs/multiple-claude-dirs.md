# Multiple Claude Directories Support

ClaudeLens CLI now supports syncing from multiple Claude directories. This is useful when you have Claude installations in different locations or want to sync data from multiple users/profiles.

## Configuration Methods

### 1. Command Line Flags

Use the `--claude-dir` flag multiple times to specify multiple directories:

```bash
claudelens sync --claude-dir /path/to/claude1 --claude-dir /path/to/claude2
```

Short form:
```bash
claudelens sync -d /path/to/claude1 -d /path/to/claude2
```

### 2. Environment Variables

Set the `CLAUDE_DIR` environment variable with comma-separated paths:

```bash
export CLAUDE_DIR="/path/to/claude1,/path/to/claude2,/path/to/claude3"
claudelens sync
```

Or use the alternative `CLAUDE_DIRS` variable:
```bash
export CLAUDE_DIRS="/path/to/claude1,/path/to/claude2"
claudelens sync
```

### 3. Configuration File

Update your configuration to use multiple directories:

```bash
# Set multiple directories
claudelens config set claude_dirs "/path/to/claude1,/path/to/claude2"

# Add a directory to the list
claudelens config add-claude-dir /path/to/claude3

# Remove a directory from the list
claudelens config remove-claude-dir /path/to/claude1

# View current configuration
claudelens config show
```

### 4. Config File Format

The configuration is stored in `~/.claudelens/config.json`:

```json
{
  "api_url": "http://localhost:8000",
  "claude_dirs": [
    "/Users/alice/.claude",
    "/Users/bob/.claude",
    "/opt/claude"
  ]
}
```

## Features

### Duplicate Project Detection

When syncing from multiple directories, ClaudeLens will detect and warn about duplicate project names:

```
[yellow]Warning: Duplicate project 'my-project' found in /Users/bob/.claude[/yellow]
```

Both instances will be synced, but you'll be notified of the duplication.

### Watch Mode

Watch mode monitors all configured directories for changes:

```bash
claudelens sync --watch
```

Output:
```
[green]Watching /Users/alice/.claude/projects[/green]
[green]Watching /Users/bob/.claude/projects[/green]
[green]Watching for changes...[/green]
```

### Priority Order

When multiple directories are specified through different methods, they are combined with this priority:

1. CLI flags (`--claude-dir`) override all other settings
2. Environment variables (`CLAUDE_DIR` or `CLAUDE_DIRS`)
3. Configuration file settings
4. Default directory (`~/.claude`)

## Migration from Single Directory

If you're upgrading from a version that only supported a single `claude_dir`:

1. Your existing `claude_dir` setting will automatically work with the new `claude_dirs` list
2. The `claude_dir` config key is deprecated but still supported for backward compatibility
3. Setting `claude_dir` will update `claude_dirs` with a single-item list

## Examples

### Sync from multiple user profiles
```bash
claudelens sync -d /Users/alice/.claude -d /Users/bob/.claude
```

### Sync from production and development Claude instances
```bash
export CLAUDE_DIRS="/opt/claude/prod,/opt/claude/dev"
claudelens sync
```

### Add a temporary directory for one-time sync
```bash
claudelens sync --claude-dir /tmp/claude-backup --dry-run
```

## Troubleshooting

### Directory not found warnings

If a configured directory doesn't exist, you'll see a warning but sync will continue with other directories:

```
[yellow]Claude projects directory not found: /path/to/missing/.claude/projects[/yellow]
```

### Performance considerations

- Each directory is scanned independently
- Large numbers of directories may increase initial scan time
- Watch mode creates file system watchers for each directory