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