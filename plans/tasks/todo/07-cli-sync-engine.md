# Task 07: CLI Sync Engine Implementation

## Status
**Status:** TODO  
**Priority:** High  
**Estimated Time:** 4 hours

## Purpose
Implement the core sync engine that handles the actual synchronization of Claude conversation data from the local filesystem to the ClaudeLens backend. This includes file scanning, JSONL parsing, SQLite database reading, and batch uploading.

## Claude Data Types to Sync

1. **JSONL Conversation Files** (`projects/*/[session-uuid].jsonl`)
   - Each line is a complete JSON message
   - Files can be very large (100MB+)
   - Messages have parent-child relationships via UUID
   - Include user messages, assistant responses, and tool results

2. **SQLite Database** (`__store.db`)
   - Primary conversation storage (500MB+)
   - Contains normalized message data
   - Includes cost tracking and summaries
   - Foreign key relationships between tables

3. **Todo Lists** (`todos/[session-uuid]-agent-[session-uuid].json`)
   - JSON arrays of todo items
   - Linked to sessions via UUID

4. **Configuration Files** (`config.json`, `settings.json`)
   - User preferences and project settings
   - Large JSON files (config.json can be 70KB+)

## Current State
- CLI command structure exists
- No sync engine implementation
- No file watching capability
- No JSONL/SQLite parsing

## Target State
- Complete sync engine with incremental sync support
- Support for all Claude data types
- SQLite database reader
- Efficient JSONL streaming parser
- File watcher for continuous monitoring
- Batch upload with retry logic
- Progress tracking and error handling

## Implementation Details

### 1. Sync Engine Core

**`cli/claudelens_cli/core/sync_engine.py`:**
```python
"""Core sync engine for ClaudeLens CLI."""
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, List, Set, Callable, AsyncIterator
from datetime import datetime
import httpx
from rich.console import Console
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
import aiofiles

from claudelens_cli.core.config import ConfigManager
from claudelens_cli.core.state import StateManager, ProjectState
from claudelens_cli.core.claude_parser import ClaudeMessageParser

console = Console()


class SyncStats:
    """Statistics for sync operations."""
    
    def __init__(self):
        self.projects_scanned = 0
        self.files_processed = 0
        self.messages_synced = 0
        self.messages_skipped = 0
        self.errors = 0
        self.start_time = datetime.utcnow()
    
    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "projects_scanned": self.projects_scanned,
            "files_processed": self.files_processed,
            "messages_synced": self.messages_synced,
            "messages_skipped": self.messages_skipped,
            "errors": self.errors,
            "duration": f"{self.duration:.2f}"
        }


class SyncEngine:
    """Main sync engine for Claude conversations."""
    
    def __init__(self, config: ConfigManager, state: StateManager):
        self.config = config
        self.state = state
        self.parser = ClaudeMessageParser()
        self.http_client = None
        self._observer = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if not self.http_client:
            self.http_client = httpx.AsyncClient(
                base_url=self.config.config.api_url,
                headers=self.config.get_headers(),
                timeout=30.0
            )
        return self.http_client
    
    async def _close_http_client(self):
        """Close HTTP client."""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
    
    def sync_once(
        self,
        project_filter: Optional[Path] = None,
        dry_run: bool = False,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict:
        """Perform a one-time sync."""
        return asyncio.run(self._async_sync_once(project_filter, dry_run, progress_callback))
    
    async def _async_sync_once(
        self,
        project_filter: Optional[Path] = None,
        dry_run: bool = False,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict:
        """Async implementation of one-time sync."""
        stats = SyncStats()
        
        try:
            # Find all projects
            projects = await self._find_projects(project_filter)
            stats.projects_scanned = len(projects)
            
            if progress_callback:
                progress_callback(f"Found {len(projects)} projects")
            
            # Process each project
            for project_path in projects:
                project_name = project_path.name
                if progress_callback:
                    progress_callback(f"Syncing {project_name}...")
                
                await self._sync_project(
                    project_path,
                    stats,
                    dry_run,
                    progress_callback
                )
            
            return stats.to_dict()
            
        finally:
            await self._close_http_client()
    
    async def _find_projects(self, project_filter: Optional[Path] = None) -> List[Path]:
        """Find all Claude projects."""
        if project_filter:
            return [project_filter]
        
        claude_dir = self.config.config.claude_dir
        projects_dir = claude_dir / "projects"
        
        if not projects_dir.exists():
            console.print(f"[yellow]Claude projects directory not found: {projects_dir}[/yellow]")
            return []
        
        # Find all project directories
        projects = []
        for item in projects_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                projects.append(item)
        
        return sorted(projects)
    
    async def _sync_project(
        self,
        project_path: Path,
        stats: SyncStats,
        dry_run: bool,
        progress_callback: Optional[Callable[[str], None]] = None
    ):
        """Sync a single project."""
        project_key = str(project_path)
        project_state = self.state.get_project_state(project_key)
        
        # Find JSONL files
        jsonl_files = sorted(project_path.glob("*.jsonl"))
        
        if not jsonl_files:
            return
        
        # Create or update project in backend
        if not dry_run:
            await self._ensure_project_exists(project_path)
        
        # Process each file
        for jsonl_file in jsonl_files:
            # Skip if file hasn't been modified since last sync
            if project_state and project_state.last_file == jsonl_file.name:
                file_mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)
                if file_mtime <= project_state.last_sync:
                    continue
            
            await self._sync_file(
                jsonl_file,
                project_key,
                project_state,
                stats,
                dry_run,
                progress_callback
            )
            stats.files_processed += 1
    
    async def _sync_file(
        self,
        file_path: Path,
        project_key: str,
        project_state: Optional[ProjectState],
        stats: SyncStats,
        dry_run: bool,
        progress_callback: Optional[Callable[[str], None]] = None
    ):
        """Sync a single JSONL file."""
        batch = []
        batch_hashes = set()
        line_number = 0
        
        # Determine starting line
        start_line = 0
        if project_state and project_state.last_file == file_path.name:
            start_line = project_state.last_line or 0
        
        async for message, line_num in self._read_jsonl_messages(file_path, start_line):
            line_number = line_num
            
            # Generate hash
            message_hash = self.state.hash_message(message)
            
            # Skip if already synced
            if self.state.is_message_synced(project_key, message_hash):
                stats.messages_skipped += 1
                continue
            
            # Add to batch
            batch.append(message)
            batch_hashes.add(message_hash)
            
            # Upload batch when it reaches configured size
            if len(batch) >= self.config.config.batch_size:
                if not dry_run:
                    await self._upload_batch(batch)
                stats.messages_synced += len(batch)
                
                # Update state
                self.state.update_project_state(
                    project_key,
                    last_file=file_path.name,
                    last_line=line_number,
                    new_hashes=batch_hashes
                )
                
                # Clear batch
                batch = []
                batch_hashes = set()
                
                if progress_callback:
                    progress_callback(f"Synced {stats.messages_synced} messages")
        
        # Upload remaining messages
        if batch:
            if not dry_run:
                await self._upload_batch(batch)
            stats.messages_synced += len(batch)
            
            self.state.update_project_state(
                project_key,
                last_file=file_path.name,
                last_line=line_number,
                new_hashes=batch_hashes
            )
    
    async def _read_jsonl_messages(
        self,
        file_path: Path,
        start_line: int = 0
    ) -> AsyncIterator[tuple[dict, int]]:
        """Read messages from JSONL file."""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            line_number = 0
            async for line in f:
                line_number += 1
                
                if line_number <= start_line:
                    continue
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    message = json.loads(line)
                    # Parse and validate message
                    parsed = self.parser.parse_message(message)
                    if parsed:
                        yield parsed, line_number
                except json.JSONDecodeError as e:
                    console.print(f"[red]Error parsing line {line_number} in {file_path}: {e}[/red]")
                except Exception as e:
                    console.print(f"[red]Error processing message: {e}[/red]")
    
    async def _ensure_project_exists(self, project_path: Path):
        """Ensure project exists in backend."""
        client = await self._get_http_client()
        
        project_data = {
            "name": project_path.name,
            "path": str(project_path),
            "description": f"Claude project: {project_path.name}"
        }
        
        try:
            response = await client.post("/api/v1/projects", json=project_data)
            if response.status_code not in (200, 201, 409):  # 409 = already exists
                console.print(f"[red]Failed to create project: {response.text}[/red]")
        except Exception as e:
            console.print(f"[red]Error creating project: {e}[/red]")
    
    async def _upload_batch(self, messages: List[dict], retry_count: int = 3):
        """Upload a batch of messages to the backend."""
        client = await self._get_http_client()
        
        for attempt in range(retry_count):
            try:
                response = await client.post(
                    "/api/v1/ingest/batch",
                    json={"messages": messages},
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    return
                elif response.status_code == 429:  # Rate limited
                    wait_time = int(response.headers.get("Retry-After", 5))
                    console.print(f"[yellow]Rate limited, waiting {wait_time}s...[/yellow]")
                    await asyncio.sleep(wait_time)
                else:
                    console.print(f"[red]Upload failed ({response.status_code}): {response.text}[/red]")
                    
            except httpx.TimeoutException:
                console.print(f"[yellow]Upload timeout, retrying... ({attempt + 1}/{retry_count})[/yellow]")
            except Exception as e:
                console.print(f"[red]Upload error: {e}[/red]")
            
            if attempt < retry_count - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception(f"Failed to upload batch after {retry_count} attempts")
    
    def watch(
        self,
        project_filter: Optional[Path] = None,
        dry_run: bool = False
    ):
        """Watch for changes and sync continuously."""
        # Initial sync
        console.print("[green]Performing initial sync...[/green]")
        stats = self.sync_once(project_filter, dry_run)
        _show_sync_stats(stats)
        
        # Set up file watcher
        event_handler = ClaudeFileHandler(self, project_filter, dry_run)
        self._observer = Observer()
        
        watch_path = project_filter or (self.config.config.claude_dir / "projects")
        self._observer.schedule(event_handler, str(watch_path), recursive=True)
        
        # Start watching
        self._observer.start()
        console.print(f"\n[green]Watching {watch_path} for changes...[/green]")
        
        try:
            while True:
                asyncio.run(asyncio.sleep(1))
        except KeyboardInterrupt:
            self._observer.stop()
        
        self._observer.join()


class ClaudeFileHandler(FileSystemEventHandler):
    """File system event handler for Claude files."""
    
    def __init__(self, sync_engine: SyncEngine, project_filter: Optional[Path], dry_run: bool):
        self.sync_engine = sync_engine
        self.project_filter = project_filter
        self.dry_run = dry_run
        self._pending_files = set()
        self._sync_task = None
    
    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only process JSONL files
        if file_path.suffix != '.jsonl':
            return
        
        # Add to pending files
        self._pending_files.add(file_path)
        
        # Schedule sync (debounced)
        if self._sync_task:
            self._sync_task.cancel()
        
        self._sync_task = asyncio.create_task(self._debounced_sync())
    
    async def _debounced_sync(self):
        """Sync after a delay to batch changes."""
        await asyncio.sleep(2)  # Wait 2 seconds for more changes
        
        if self._pending_files:
            console.print(f"\n[yellow]Changes detected in {len(self._pending_files)} files[/yellow]")
            
            # Sync changed files
            stats = await self.sync_engine._async_sync_once(
                self.project_filter,
                self.dry_run
            )
            
            console.print(f"[green]Sync completed: {stats['messages_synced']} new messages[/green]")
            self._pending_files.clear()


def _show_sync_stats(stats: dict):
    """Display sync statistics."""
    from claudelens_cli.commands.sync import _show_sync_stats as show_stats
    show_stats(stats)
```

### 2. Claude Message Parser

**`cli/claudelens_cli/core/claude_parser.py`:**
```python
"""Parser for Claude conversation messages."""
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import sqlite3


class ClaudeMessageParser:
    """Parses and validates Claude message format."""
    
    def parse_jsonl_message(self, raw_message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a raw message from JSONL files.
        
        Handles the following message types:
        - summary: Session summaries (stored separately)
        - user: User inputs with optional tool results
        - assistant: Claude responses with model info and costs
        
        Returns None if message should be skipped.
        """
        msg_type = raw_message.get("type")
        
        # Handle summary messages separately
        if msg_type == "summary":
            return {
                "type": "summary",
                "summary": raw_message.get("summary"),
                "leafUuid": raw_message.get("leafUuid"),
                "isSummary": True
            }
        
        # Basic validation
        required_fields = ["uuid", "type", "timestamp"]
        if not all(field in raw_message for field in required_fields):
            return None
        
        # Parse timestamp
        try:
            timestamp = self._parse_timestamp(raw_message["timestamp"])
        except Exception:
            return None
        
        # Build normalized message
        message = {
            "uuid": raw_message["uuid"],
            "type": raw_message["type"],
            "timestamp": timestamp.isoformat(),
            "sessionId": raw_message.get("sessionId"),
            "parentUuid": raw_message.get("parentUuid"),
            "isSidechain": raw_message.get("isSidechain", False),
            "userType": raw_message.get("userType", "external"),
            "cwd": raw_message.get("cwd"),
            "version": raw_message.get("version"),
            "gitBranch": raw_message.get("gitBranch"),
        }
        
        # Add message content based on type
        if "message" in raw_message:
            message["message"] = raw_message["message"]
            
        # Add type-specific fields
        if msg_type == "user":
            message.update(self._parse_user_message(raw_message))
        elif msg_type == "assistant":
            message.update(self._parse_assistant_message(raw_message))
        
        return message
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime."""
        # Handle different timestamp formats
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        
        return datetime.fromisoformat(timestamp_str)
    
    def _parse_user_message(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse user message fields."""
        result = {
            "userType": raw_message.get("userType", "external"),
            "cwd": raw_message.get("cwd"),
        }
        
        # Extract message content
        if "message" in raw_message:
            result["message"] = raw_message["message"]
        
        # Tool use results
        if "toolUseResult" in raw_message:
            result["toolUseResult"] = raw_message["toolUseResult"]
        
        return result
    
    def _parse_assistant_message(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse assistant message fields."""
        result = {}
        
        # Extract message content
        if "message" in raw_message:
            message = raw_message["message"]
            result["message"] = message
            
            # Extract model info
            if isinstance(message, dict):
                if "model" in message:
                    result["model"] = message["model"]
                if "usage" in message:
                    result["usage"] = message["usage"]
        
        # Cost and duration (from JSONL metadata)
        if "costUsd" in raw_message:
            result["costUsd"] = raw_message["costUsd"]
        if "durationMs" in raw_message:
            result["durationMs"] = raw_message["durationMs"]
        
        # Request ID
        if "requestId" in raw_message:
            result["requestId"] = raw_message["requestId"]
        
        return result


class ClaudeDatabaseReader:
    """Reads messages from Claude's SQLite database."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    async def read_messages(self, after_timestamp: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Read messages from SQLite database.
        
        Joins data from multiple tables to reconstruct full messages.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        try:
            query = """
            SELECT 
                b.uuid,
                b.parent_uuid,
                b.session_id,
                b.timestamp,
                b.message_type,
                b.cwd,
                b.user_type,
                b.version,
                b.isSidechain,
                u.message as user_message,
                u.tool_use_result,
                a.message as assistant_message,
                a.cost_usd,
                a.duration_ms,
                a.model,
                c.summary
            FROM base_messages b
            LEFT JOIN user_messages u ON b.uuid = u.uuid
            LEFT JOIN assistant_messages a ON b.uuid = a.uuid
            LEFT JOIN conversation_summaries c ON b.uuid = c.leaf_uuid
            """
            
            params = []
            if after_timestamp:
                query += " WHERE b.timestamp > ?"
                params.append(int(after_timestamp.timestamp() * 1000))
            
            query += " ORDER BY b.timestamp ASC"
            
            cursor = conn.execute(query, params)
            messages = []
            
            for row in cursor:
                message = self._row_to_message(dict(row))
                if message:
                    messages.append(message)
            
            return messages
            
        finally:
            conn.close()
    
    def _row_to_message(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert SQLite row to message format."""
        # Skip if no message type
        if not row.get("message_type"):
            return None
        
        # Base message structure
        message = {
            "uuid": row["uuid"],
            "type": row["message_type"],
            "parentUuid": row["parent_uuid"],
            "sessionId": row["session_id"],
            "timestamp": datetime.fromtimestamp(row["timestamp"] / 1000).isoformat(),
            "cwd": row["cwd"],
            "userType": row["user_type"],
            "version": row["version"],
            "isSidechain": bool(row["isSidechain"]),
        }
        
        # Add type-specific content
        if row["message_type"] == "user" and row["user_message"]:
            message["message"] = json.loads(row["user_message"])
            if row["tool_use_result"]:
                message["toolUseResult"] = json.loads(row["tool_use_result"])
                
        elif row["message_type"] == "assistant" and row["assistant_message"]:
            message["message"] = json.loads(row["assistant_message"])
            if row["cost_usd"]:
                message["costUsd"] = row["cost_usd"]
            if row["duration_ms"]:
                message["durationMs"] = row["duration_ms"]
            if row["model"]:
                message["model"] = row["model"]
        
        # Add summary if this is a summary node
        if row["summary"]:
            message["summary"] = row["summary"]
        
        return message
```

### 3. File Watcher Utilities

**`cli/claudelens_cli/core/watcher.py`:**
```python
"""File watching utilities for continuous sync."""
import asyncio
from pathlib import Path
from typing import Set, Optional, Callable
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
from rich.console import Console

console = Console()


class BatchedFileWatcher:
    """Watches files and batches changes for efficient processing."""
    
    def __init__(
        self,
        watch_paths: list[Path],
        callback: Callable[[Set[Path]], None],
        batch_delay: float = 2.0,
        file_pattern: str = "*.jsonl"
    ):
        self.watch_paths = watch_paths
        self.callback = callback
        self.batch_delay = batch_delay
        self.file_pattern = file_pattern
        
        self._observer = Observer()
        self._pending_files: Set[Path] = set()
        self._last_event_time: Optional[datetime] = None
        self._process_task: Optional[asyncio.Task] = None
    
    def start(self):
        """Start watching files."""
        handler = _FileChangeHandler(self._on_file_change, self.file_pattern)
        
        for path in self.watch_paths:
            if path.exists():
                self._observer.schedule(handler, str(path), recursive=True)
                console.print(f"[dim]Watching: {path}[/dim]")
        
        self._observer.start()
    
    def stop(self):
        """Stop watching files."""
        if self._observer.is_alive():
            self._observer.stop()
            self._observer.join()
        
        if self._process_task:
            self._process_task.cancel()
    
    def _on_file_change(self, file_path: Path):
        """Handle file change event."""
        self._pending_files.add(file_path)
        self._last_event_time = datetime.utcnow()
        
        # Schedule processing
        if self._process_task:
            self._process_task.cancel()
        
        self._process_task = asyncio.create_task(self._process_batch())
    
    async def _process_batch(self):
        """Process batch of file changes after delay."""
        await asyncio.sleep(self.batch_delay)
        
        # Check if more events came in
        if self._last_event_time and \
           datetime.utcnow() - self._last_event_time < timedelta(seconds=self.batch_delay):
            # More events might be coming, wait more
            await asyncio.sleep(self.batch_delay)
        
        # Process the batch
        if self._pending_files:
            files_to_process = self._pending_files.copy()
            self._pending_files.clear()
            
            try:
                await self.callback(files_to_process)
            except Exception as e:
                console.print(f"[red]Error processing file batch: {e}[/red]")


class _FileChangeHandler(FileSystemEventHandler):
    """Internal file change handler."""
    
    def __init__(self, callback: Callable[[Path], None], file_pattern: str):
        self.callback = callback
        self.file_pattern = file_pattern
    
    def _should_process(self, file_path: Path) -> bool:
        """Check if file should be processed."""
        return file_path.match(self.file_pattern) and file_path.is_file()
    
    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if self._should_process(file_path):
                self.callback(file_path)
    
    def on_created(self, event: FileCreatedEvent):
        """Handle file creation."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if self._should_process(file_path):
                self.callback(file_path)
```

### 4. Retry and Error Handling

**`cli/claudelens_cli/core/retry.py`:**
```python
"""Retry logic and error handling utilities."""
import asyncio
import functools
from typing import TypeVar, Callable, Optional, Type, Tuple
import httpx
from rich.console import Console

console = Console()

T = TypeVar('T')


def with_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """Decorator for retry logic with exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff ** attempt)
                        console.print(
                            f"[yellow]Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {wait_time:.1f}s...[/yellow]"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        console.print(f"[red]All {max_attempts} attempts failed[/red]")
            
            raise last_exception
        
        return wrapper
    return decorator


class RetryableHTTPClient:
    """HTTP client with built-in retry logic."""
    
    def __init__(
        self,
        base_url: str,
        headers: Optional[dict] = None,
        max_retries: int = 3,
        timeout: float = 30.0
    ):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=timeout
        )
        self.max_retries = max_retries
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @with_retry(max_attempts=3, exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """POST request with retry."""
        response = await self.client.post(url, **kwargs)
        
        # Retry on 5xx errors
        if response.status_code >= 500:
            raise httpx.HTTPStatusError(
                f"Server error: {response.status_code}",
                request=response.request,
                response=response
            )
        
        return response
    
    @with_retry(max_attempts=3, exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """GET request with retry."""
        return await self.client.get(url, **kwargs)
```

### 5. Additional Data Type Handlers

**`cli/claudelens_cli/core/data_handlers.py`:**
```python
"""Handlers for various Claude data types."""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiofiles


class TodoHandler:
    """Handles Claude todo list files."""
    
    async def read_todo_file(self, file_path: Path) -> Dict[str, Any]:
        """Read and parse a todo file."""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            todos = json.loads(content)
            
            # Extract session ID from filename
            # Format: [session-uuid]-agent-[session-uuid].json
            filename = file_path.name
            session_id = filename.split('-agent-')[0]
            
            return {
                "sessionId": session_id,
                "filename": filename,
                "todos": todos,
                "todoCount": len(todos)
            }


class ConfigHandler:
    """Handles Claude configuration files."""
    
    async def read_config(self, claude_dir: Path) -> Dict[str, Any]:
        """Read Claude configuration files."""
        config = {}
        
        # Read config.json
        config_path = claude_dir / "config.json"
        if config_path.exists():
            async with aiofiles.open(config_path, 'r', encoding='utf-8') as f:
                config["config"] = json.loads(await f.read())
        
        # Read settings.json
        settings_path = claude_dir / "settings.json"
        if settings_path.exists():
            async with aiofiles.open(settings_path, 'r', encoding='utf-8') as f:
                config["settings"] = json.loads(await f.read())
        
        return config


class ProjectScanner:
    """Scans for Claude projects and sessions."""
    
    def find_projects(self, claude_dir: Path) -> List[Dict[str, Any]]:
        """Find all projects in Claude directory."""
        projects_dir = claude_dir / "projects"
        if not projects_dir.exists():
            return []
        
        projects = []
        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('.'):
                # Convert directory name back to path
                # Format: -Users-username-path-to-project
                path_parts = project_dir.name.split('-')
                if path_parts[0] == '':  # Leading dash
                    path_parts[0] = '/'
                project_path = '/'.join(path_parts).replace('//', '/')
                
                # Count sessions
                jsonl_files = list(project_dir.glob("*.jsonl"))
                
                projects.append({
                    "name": project_dir.name,
                    "path": project_path,
                    "directory": str(project_dir),
                    "sessionCount": len(jsonl_files),
                    "sessions": [f.stem for f in jsonl_files]
                })
        
        return projects
```

### 6. Update CLI Package Exports

**Update `cli/claudelens_cli/commands/__init__.py`:**
```python
"""CLI commands package."""
from claudelens_cli.commands import sync, status, config

__all__ = ["sync", "status", "config"]
```

**Update `cli/claudelens_cli/core/__init__.py`:**
```python
"""Core functionality package."""
from claudelens_cli.core.config import ConfigManager, config_manager
from claudelens_cli.core.state import StateManager
from claudelens_cli.core.sync_engine import SyncEngine
from claudelens_cli.core.claude_parser import ClaudeMessageParser, ClaudeDatabaseReader
from claudelens_cli.core.data_handlers import TodoHandler, ConfigHandler, ProjectScanner

__all__ = [
    "ConfigManager", "config_manager", "StateManager", "SyncEngine",
    "ClaudeMessageParser", "ClaudeDatabaseReader", 
    "TodoHandler", "ConfigHandler", "ProjectScanner"
]
```

## Required Technologies
- asyncio for async operations
- httpx for HTTP requests
- watchdog for file monitoring
- aiofiles for async file I/O
- sqlite3 for reading Claude's database
- json for parsing JSONL and JSON files

## Success Criteria
- [ ] Sync engine can scan Claude directory structure
- [ ] JSONL files parsed correctly with all message types
- [ ] SQLite database messages extracted successfully
- [ ] Todo files synced with session associations
- [ ] Configuration files captured for user preferences
- [ ] Incremental sync works (only new messages)
- [ ] Batch upload implemented with retry logic
- [ ] File watcher detects changes in real-time
- [ ] Progress feedback during sync
- [ ] Error handling and recovery
- [ ] Deduplication prevents duplicate uploads
- [ ] State properly tracked and persisted

## Notes
- Use async/await throughout for better performance
- Handle large files (config.json can be 70KB+, __store.db can be 500MB+)
- SQLite database has foreign key relationships between tables
- JSONL files grow incrementally as conversations progress
- Project directories use dash-separated paths
- Todo files are linked to sessions via filename
- Batch uploads to reduce API calls
- Implement exponential backoff for retries
- File watcher should debounce rapid changes