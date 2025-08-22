# Streaming and Compression Patterns for Backup/Restore

## FastAPI Streaming Response Patterns

### Basic Streaming for Large Files

```python
from fastapi import Response
from fastapi.responses import StreamingResponse
import aiofiles
from typing import AsyncGenerator

async def stream_file_chunks(
    file_path: str,
    chunk_size: int = 8192  # 8KB chunks
) -> AsyncGenerator[bytes, None]:
    """Stream file in chunks to avoid loading entire file in memory."""
    async with aiofiles.open(file_path, 'rb') as file:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            yield chunk

@router.get("/backup/{backup_id}/download")
async def download_backup(backup_id: str):
    """Stream large backup file to client."""
    file_path = f"/backups/{backup_id}.tar.gz"

    # Get file size for Content-Length header
    import os
    file_size = os.path.getsize(file_path)

    return StreamingResponse(
        stream_file_chunks(file_path),
        media_type="application/gzip",
        headers={
            "Content-Disposition": f"attachment; filename=backup_{backup_id}.tar.gz",
            "Content-Length": str(file_size),
            "Cache-Control": "no-cache",
        }
    )
```

### Progressive JSON Streaming

For streaming JSON data progressively:

```python
import json
from typing import AsyncGenerator, Dict, Any

async def stream_json_array(
    data_generator: AsyncGenerator[Dict[str, Any], None]
) -> AsyncGenerator[str, None]:
    """Stream JSON array progressively."""
    first = True
    yield '['  # Start array

    async for item in data_generator:
        if not first:
            yield ','
        else:
            first = False

        # Stream each item as JSON
        yield json.dumps(item, ensure_ascii=False)

    yield ']'  # End array

@router.get("/export/stream")
async def stream_export():
    """Stream export data as JSON array."""
    async def generate_data():
        # Simulate data generation
        for i in range(10000):
            yield {"id": i, "data": f"item_{i}"}

    return StreamingResponse(
        stream_json_array(generate_data()),
        media_type="application/json",
        headers={
            "Content-Disposition": "attachment; filename=export.json",
            "X-Content-Type-Options": "nosniff",
        }
    )
```

## Zstandard Compression Integration

### Installation and Setup

```toml
# pyproject.toml
[tool.poetry.dependencies]
zstandard = "^0.22.0"  # Best compression/speed balance
```

### Streaming Compression

```python
import zstandard as zstd
from typing import AsyncGenerator
import asyncio

class StreamingCompressor:
    """Handle streaming compression with zstandard."""

    def __init__(self, compression_level: int = 3):
        """
        Initialize compressor.
        Level 1-3: Fast compression
        Level 4-9: Balanced
        Level 10-22: Maximum compression
        """
        self.compression_level = compression_level

    async def compress_stream(
        self,
        data_generator: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[bytes, None]:
        """Compress data stream on the fly."""
        cctx = zstd.ZstdCompressor(level=self.compression_level)
        compressor = cctx.compressobj()

        async for chunk in data_generator:
            compressed = compressor.compress(chunk)
            if compressed:
                yield compressed

        # Flush remaining data
        final = compressor.flush()
        if final:
            yield final

    async def decompress_stream(
        self,
        compressed_generator: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[bytes, None]:
        """Decompress data stream on the fly."""
        dctx = zstd.ZstdDecompressor()
        decompressor = dctx.decompressobj()

        async for chunk in compressed_generator:
            decompressed = decompressor.decompress(chunk)
            if decompressed:
                yield decompressed
```

### Compression with Progress Tracking

```python
from typing import Callable, Optional

class ProgressCompressor:
    """Compression with progress callback."""

    def __init__(
        self,
        compression_level: int = 3,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        self.compression_level = compression_level
        self.progress_callback = progress_callback
        self.bytes_processed = 0
        self.bytes_compressed = 0

    async def compress_with_progress(
        self,
        data_generator: AsyncGenerator[bytes, None],
        total_size: Optional[int] = None
    ) -> AsyncGenerator[bytes, None]:
        """Compress with progress updates."""
        cctx = zstd.ZstdCompressor(level=self.compression_level)
        compressor = cctx.compressobj()

        async for chunk in data_generator:
            self.bytes_processed += len(chunk)

            compressed = compressor.compress(chunk)
            if compressed:
                self.bytes_compressed += len(compressed)
                yield compressed

            # Report progress
            if self.progress_callback and total_size:
                self.progress_callback(self.bytes_processed, total_size)

        # Flush and report final progress
        final = compressor.flush()
        if final:
            self.bytes_compressed += len(final)
            yield final

        if self.progress_callback and total_size:
            self.progress_callback(total_size, total_size)
```

## Multipart Upload Handling

### Streaming Multipart File Upload

```python
from fastapi import UploadFile, File, HTTPException
import tempfile
import hashlib

class StreamingUploadHandler:
    """Handle large file uploads with streaming."""

    def __init__(self, max_file_size: int = 10 * 1024 * 1024 * 1024):  # 10GB
        self.max_file_size = max_file_size

    async def handle_upload(
        self,
        file: UploadFile,
        chunk_size: int = 1024 * 1024  # 1MB chunks
    ) -> Dict[str, Any]:
        """Stream upload to temporary file with validation."""
        temp_file = None
        bytes_written = 0
        hasher = hashlib.sha256()

        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.upload')

            # Stream file in chunks
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break

                # Check file size limit
                bytes_written += len(chunk)
                if bytes_written > self.max_file_size:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {self.max_file_size} bytes"
                    )

                # Write chunk and update hash
                temp_file.write(chunk)
                hasher.update(chunk)

            temp_file.close()

            return {
                'temp_path': temp_file.name,
                'size': bytes_written,
                'checksum': hasher.hexdigest(),
                'filename': file.filename
            }

        except Exception as e:
            # Clean up on error
            if temp_file:
                temp_file.close()
                os.unlink(temp_file.name)
            raise e

@router.post("/backup/upload")
async def upload_backup(
    file: UploadFile = File(...),
    handler: StreamingUploadHandler = Depends()
):
    """Handle large backup file upload."""
    # Validate file type
    if not file.filename.endswith(('.tar.gz', '.zst', '.json')):
        raise HTTPException(400, "Invalid file type")

    # Stream upload to temporary file
    upload_info = await handler.handle_upload(file)

    # Process the uploaded file
    # ... validation and processing logic ...

    return {
        "message": "Upload successful",
        "file_size": upload_info['size'],
        "checksum": upload_info['checksum']
    }
```

## Memory-Efficient Data Processing

### Batch Processing Pattern

```python
from typing import List, TypeVar, AsyncGenerator
import asyncio

T = TypeVar('T')

class BatchProcessor:
    """Process data in batches to manage memory."""

    @staticmethod
    async def process_in_batches(
        items: AsyncGenerator[T, None],
        batch_size: int,
        process_func: Callable[[List[T]], Awaitable[None]]
    ):
        """Process items in batches."""
        batch = []

        async for item in items:
            batch.append(item)

            if len(batch) >= batch_size:
                await process_func(batch)
                batch = []

        # Process remaining items
        if batch:
            await process_func(batch)

    @staticmethod
    async def parallel_batch_processing(
        items: AsyncGenerator[T, None],
        batch_size: int,
        process_func: Callable[[List[T]], Awaitable[None]],
        max_concurrent: int = 3
    ):
        """Process batches in parallel with concurrency limit."""
        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = []

        async def process_with_limit(batch):
            async with semaphore:
                await process_func(batch)

        batch = []
        async for item in items:
            batch.append(item)

            if len(batch) >= batch_size:
                task = asyncio.create_task(process_with_limit(batch))
                tasks.append(task)
                batch = []

        # Process remaining items
        if batch:
            task = asyncio.create_task(process_with_limit(batch))
            tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
```

### Pipeline Pattern for Data Transformation

```python
from typing import AsyncGenerator, Callable, Any

class DataPipeline:
    """Chain data transformations efficiently."""

    def __init__(self):
        self.stages = []

    def add_stage(
        self,
        transform: Callable[[AsyncGenerator], AsyncGenerator]
    ):
        """Add transformation stage to pipeline."""
        self.stages.append(transform)
        return self

    async def execute(
        self,
        source: AsyncGenerator[Any, None]
    ) -> AsyncGenerator[Any, None]:
        """Execute pipeline stages."""
        result = source

        for stage in self.stages:
            result = stage(result)

        async for item in result:
            yield item

# Example usage
async def compression_stage(data_gen: AsyncGenerator[bytes, None]):
    """Compression pipeline stage."""
    compressor = zstd.ZstdCompressor(level=3)
    async for chunk in data_gen:
        compressed = compressor.compress(chunk)
        if compressed:
            yield compressed

async def encryption_stage(data_gen: AsyncGenerator[bytes, None]):
    """Encryption pipeline stage."""
    # Implement encryption logic
    async for chunk in data_gen:
        encrypted = encrypt_chunk(chunk)  # Your encryption function
        yield encrypted

# Build pipeline
pipeline = DataPipeline()
pipeline.add_stage(compression_stage).add_stage(encryption_stage)

# Execute pipeline
async for processed_chunk in pipeline.execute(source_data):
    # Write to file or stream to client
    pass
```

## WebSocket Progress Updates

### Real-time Progress Broadcasting

```python
from fastapi import WebSocket
from typing import Dict, Set
import asyncio

class ProgressBroadcaster:
    """Broadcast progress updates via WebSocket."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.job_progress: Dict[str, Dict] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        """Connect client to job progress updates."""
        await websocket.accept()

        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()

        self.active_connections[job_id].add(websocket)

        # Send current progress if available
        if job_id in self.job_progress:
            await websocket.send_json(self.job_progress[job_id])

    def disconnect(self, job_id: str, websocket: WebSocket):
        """Disconnect client from updates."""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)

            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def update_progress(
        self,
        job_id: str,
        current: int,
        total: int,
        message: str = "",
        extra_data: Dict = None
    ):
        """Broadcast progress update to connected clients."""
        progress_data = {
            'job_id': job_id,
            'current': current,
            'total': total,
            'percentage': round((current / total) * 100, 2) if total > 0 else 0,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            **(extra_data or {})
        }

        self.job_progress[job_id] = progress_data

        # Broadcast to all connected clients
        if job_id in self.active_connections:
            disconnected = set()

            for websocket in self.active_connections[job_id]:
                try:
                    await websocket.send_json(progress_data)
                except:
                    disconnected.add(websocket)

            # Clean up disconnected clients
            for ws in disconnected:
                self.disconnect(job_id, ws)

# Global instance
progress_broadcaster = ProgressBroadcaster()

@router.websocket("/ws/backup/{job_id}")
async def websocket_backup_progress(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for backup progress."""
    await progress_broadcaster.connect(job_id, websocket)

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except:
        progress_broadcaster.disconnect(job_id, websocket)
```

## Performance Benchmarks and Recommendations

### Compression Algorithm Comparison

| Algorithm | Compression Ratio | Speed (MB/s) | CPU Usage | Use Case |
|-----------|------------------|--------------|-----------|----------|
| **zstd -3** | 3.5x | 500 | Low | **Recommended default** |
| zstd -1 | 2.8x | 800 | Very Low | Real-time streaming |
| zstd -9 | 4.2x | 150 | Medium | Storage optimization |
| gzip -6 | 3.2x | 100 | Medium | Legacy compatibility |
| lz4 | 2.1x | 3000 | Very Low | Speed critical |
| brotli -4 | 4.8x | 50 | High | Maximum compression |

### Chunk Size Recommendations

| Data Type | Recommended Chunk Size | Rationale |
|-----------|----------------------|-----------|
| JSON Documents | 100-500 items | Balance between memory and network overhead |
| Binary Files | 1-8 MB | Optimal for streaming and progress updates |
| Database Records | 100-1000 records | Prevents connection pool exhaustion |
| Compressed Data | 64-256 KB | Matches compression block sizes |

### Memory Usage Guidelines

```python
# Memory-efficient configuration
STREAMING_CONFIG = {
    'max_memory_mb': 100,  # Maximum memory per operation
    'chunk_size_bytes': 1024 * 1024,  # 1MB chunks
    'batch_size': 100,  # Documents per batch
    'compression_level': 3,  # Balanced compression
    'parallel_tasks': 3,  # Concurrent operations
}
```

## Error Recovery Patterns

```python
class StreamingErrorHandler:
    """Handle errors in streaming operations gracefully."""

    @staticmethod
    async def resilient_stream(
        data_generator: AsyncGenerator,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> AsyncGenerator:
        """Stream with automatic retry on errors."""
        retry_count = 0

        while retry_count < max_retries:
            try:
                async for item in data_generator:
                    yield item
                break  # Success

            except asyncio.CancelledError:
                raise  # Don't retry on cancellation

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise Exception(f"Stream failed after {max_retries} retries: {e}")

                await asyncio.sleep(retry_delay * retry_count)
                # Recreate generator for retry
                data_generator = create_new_generator()  # Your function
```
