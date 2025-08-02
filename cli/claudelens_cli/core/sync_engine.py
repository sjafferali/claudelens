"""Core sync engine for ClaudeLens CLI."""
import asyncio
import json
from collections.abc import AsyncIterator, Callable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import httpx
from rich.console import Console
from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from claudelens_cli.core.claude_parser import ClaudeMessageParser
from claudelens_cli.core.config import ConfigManager
from claudelens_cli.core.state import ProjectState, StateManager

if TYPE_CHECKING:
    from watchdog.observers.api import BaseObserver

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
    
    def to_dict(self) -> dict:
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
        self.http_client: httpx.AsyncClient | None = None
        self._observer: BaseObserver | None = None
    
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
        project_filter: Path | None = None,
        dry_run: bool = False,
        progress_callback: Callable[[str], None] | None = None
    ) -> dict:
        """Perform a one-time sync."""
        return asyncio.run(self._async_sync_once(project_filter, dry_run, progress_callback))
    
    async def _async_sync_once(
        self,
        project_filter: Path | None = None,
        dry_run: bool = False,
        progress_callback: Callable[[str], None] | None = None
    ) -> dict:
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
    
    async def _find_projects(self, project_filter: Path | None = None) -> list[Path]:
        """Find all Claude projects across all configured directories."""
        if project_filter:
            return [project_filter]
        
        all_projects = []
        seen_projects = set()  # Track project names to handle duplicates
        
        # Iterate over all configured claude directories
        for claude_dir in self.config.config.claude_dirs:
            projects_dir = claude_dir / "projects"
            
            if not projects_dir.exists():
                console.print(f"[yellow]Claude projects directory not found: {projects_dir}[/yellow]")
                continue
            
            # Find all project directories
            for item in projects_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Check for duplicate project names across directories
                    if item.name in seen_projects:
                        console.print(f"[yellow]Warning: Duplicate project '{item.name}' found in {claude_dir}[/yellow]")
                    else:
                        seen_projects.add(item.name)
                    all_projects.append(item)
        
        return sorted(all_projects)
    
    async def _sync_project(
        self,
        project_path: Path,
        stats: SyncStats,
        dry_run: bool,
        progress_callback: Callable[[str], None] | None = None
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
        project_state: ProjectState | None,
        stats: SyncStats,
        dry_run: bool,
        progress_callback: Callable[[str], None] | None = None
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
                    new_messages=batch_hashes
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
                new_messages=batch_hashes
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
                    parsed = self.parser.parse_jsonl_message(message)
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
    
    async def _upload_batch(self, messages: list[dict], retry_count: int = 3):
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
        project_filter: Path | None = None,
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
        
        # Determine paths to watch
        if project_filter:
            watch_paths = [project_filter]
        else:
            watch_paths = [claude_dir / "projects" for claude_dir in self.config.config.claude_dirs]
        
        # Schedule observer for each path
        for watch_path in watch_paths:
            if watch_path.exists():
                self._observer.schedule(event_handler, str(watch_path), recursive=True)
                console.print(f"[green]Watching {watch_path}[/green]")
            else:
                console.print(f"[yellow]Warning: Watch path does not exist: {watch_path}[/yellow]")
        
        # Start watching
        self._observer.start()
        console.print(f"\n[green]Watching for changes...[/green]")
        
        try:
            while True:
                asyncio.run(asyncio.sleep(1))
        except KeyboardInterrupt:
            self._observer.stop()
        
        self._observer.join()


class ClaudeFileHandler(FileSystemEventHandler):
    """File system event handler for Claude files."""
    
    def __init__(self, sync_engine: SyncEngine, project_filter: Path | None, dry_run: bool):
        self.sync_engine = sync_engine
        self.project_filter = project_filter
        self.dry_run = dry_run
        self._pending_files: set[Path] = set()
        self._sync_task: asyncio.Task[None] | None = None
    
    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        file_path = Path(str(event.src_path))
        
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