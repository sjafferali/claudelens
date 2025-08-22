# Compression Support Implementation Plan

## Overview
Add compression support for export files to reduce storage size and download times, with user-selectable compression formats.

## Technology Choices

### 1. **Zstandard (zstd)** - High Performance
- Better compression ratio than gzip (20-30% better)
- 3-5x faster compression/decompression than gzip
- Streaming support
- Python library: `zstandard` (already in pyproject.toml)
- Best for: Large exports, frequent downloads, API consumption

### 2. **tar.gz** - Universal Compatibility
- Universally supported (all browsers, OS tools, archive managers)
- Native browser decompression support
- Good for bundling multiple files
- Python libraries: `tarfile` + `gzip` (built-in)
- Best for: Maximum compatibility, manual inspection, multi-file exports

## Format Comparison

| Feature | zstd | tar.gz |
|---------|------|--------|
| Compression Ratio | Excellent (30-50%) | Good (25-40%) |
| Speed | Very Fast | Moderate |
| Browser Support | Limited* | Universal |
| OS Tool Support | Growing | Universal |
| Streaming | Excellent | Good |
| Multi-file | Via tar.zst | Native |
| File Extension | .zst or .tar.zst | .tar.gz or .tgz |

*Requires JavaScript decompression library or server-side decompression

## Implementation Steps

### Phase 1: Backend Compression Support

#### 1.1 Compression Enum and Types (Week 1)
```python
# backend/app/schemas/export.py

from enum import Enum

class CompressionFormat(str, Enum):
    NONE = "none"
    ZSTD = "zstd"
    TARGZ = "tar.gz"

class ExportOptions(BaseModel):
    includeMessages: bool = True
    includeMetadata: bool = True
    includeToolCalls: bool = True
    compressionFormat: CompressionFormat = CompressionFormat.NONE
    compressionLevel: int = 3  # 1-9 for gzip, 1-22 for zstd
```

#### 1.2 Update File Service (Week 1)
```python
# backend/app/services/file_service.py

import zstandard as zstd
import tarfile
import gzip
import io
from typing import AsyncGenerator, Dict, Any
import aiofiles

class FileService:
    async def save_export_file_compressed(
        self,
        job_id: str,
        content_generator: AsyncGenerator[bytes, None],
        format: str,
        compression_format: str = "none",
        compression_level: int = 3
    ) -> Dict[str, Any]:
        """Save export file with selected compression format."""

        # Collect content first for size calculation
        content_chunks = []
        original_size = 0
        async for chunk in content_generator:
            content_chunks.append(chunk)
            original_size += len(chunk)

        if compression_format == "zstd":
            file_info = await self._compress_zstd(
                job_id, content_chunks, format, compression_level, original_size
            )
        elif compression_format == "tar.gz":
            file_info = await self._compress_targz(
                job_id, content_chunks, format, compression_level, original_size
            )
        else:
            # No compression
            file_path = f"{self.export_dir}/{job_id}.{format}"
            async with aiofiles.open(file_path, 'wb') as f:
                for chunk in content_chunks:
                    await f.write(chunk)

            file_info = {
                "path": file_path,
                "size": original_size,
                "compressed_size": original_size,
                "compression_ratio": 1.0,
                "compression_format": "none",
            }

        return file_info

    async def _compress_zstd(
        self,
        job_id: str,
        content_chunks: List[bytes],
        format: str,
        compression_level: int,
        original_size: int
    ) -> Dict[str, Any]:
        """Compress using Zstandard."""
        cctx = zstd.ZstdCompressor(level=min(compression_level, 22))
        file_path = f"{self.export_dir}/{job_id}.{format}.zst"

        compressed_size = 0
        async with aiofiles.open(file_path, 'wb') as f:
            compressor = cctx.compressobj()
            for chunk in content_chunks:
                compressed_chunk = compressor.compress(chunk)
                if compressed_chunk:
                    await f.write(compressed_chunk)
                    compressed_size += len(compressed_chunk)

            # Write final chunk
            final_chunk = compressor.flush()
            if final_chunk:
                await f.write(final_chunk)
                compressed_size += len(final_chunk)

        return {
            "path": file_path,
            "size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": original_size / compressed_size if compressed_size > 0 else 1,
            "compression_format": "zstd",
            "compression_savings_percent": round((1 - compressed_size/original_size) * 100, 1),
        }

    async def _compress_targz(
        self,
        job_id: str,
        content_chunks: List[bytes],
        format: str,
        compression_level: int,
        original_size: int
    ) -> Dict[str, Any]:
        """Compress using tar.gz format."""
        file_path = f"{self.export_dir}/{job_id}.{format}.tar.gz"

        # Create tar.gz file
        async with aiofiles.open(file_path, 'wb') as f:
            # Create gzip wrapper
            gzip_buffer = io.BytesIO()

            with gzip.GzipFile(
                fileobj=gzip_buffer,
                mode='wb',
                compresslevel=min(compression_level, 9)
            ) as gz:
                # Create tar archive in memory
                tar_buffer = io.BytesIO()
                with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
                    # Create a file-like object from chunks
                    content = b''.join(content_chunks)
                    file_buffer = io.BytesIO(content)

                    # Add file to tar
                    tarinfo = tarfile.TarInfo(name=f"export_{job_id}.{format}")
                    tarinfo.size = len(content)
                    tarinfo.mtime = time.time()
                    file_buffer.seek(0)
                    tar.addfile(tarinfo, file_buffer)

                # Write tar to gzip
                tar_buffer.seek(0)
                gz.write(tar_buffer.read())

            # Write compressed data to file
            gzip_buffer.seek(0)
            await f.write(gzip_buffer.read())
            compressed_size = gzip_buffer.tell()

        return {
            "path": file_path,
            "size": original_size,
            "compressed_size": os.path.getsize(file_path),
            "compression_ratio": original_size / compressed_size if compressed_size > 0 else 1,
            "compression_format": "tar.gz",
            "compression_savings_percent": round((1 - compressed_size/original_size) * 100, 1),
        }
```

#### 1.3 Update Export Service (Week 1)
```python
# backend/app/services/export_service.py

async def process_export(self, job_id: str, progress_callback: Optional[Callable] = None):
    # Get compression settings from options
    compression_format = export_job.get("options", {}).get("compressionFormat", "none")
    compression_level = export_job.get("options", {}).get("compressionLevel", 3)

    # Save with selected compression
    file_info = await self.file_service.save_export_file_compressed(
        job_id,
        content_generator,
        export_job["format"],
        compression_format=compression_format,
        compression_level=compression_level
    )

    # Update job with compression info
    await self.db.export_jobs.update_one(
        {"_id": ObjectId(job_id)},
        {
            "$set": {
                "file_info": file_info,
                "compression_format": compression_format,
                "compression_savings": file_info.get("compression_savings_percent", 0),
            }
        }
    )
```

#### 1.4 Update Download Endpoint (Week 1)
```python
# backend/app/api/api_v1/endpoints/import_export.py

@router.get("/export/{job_id}/download")
async def download_export(
    job_id: str,
    db: CommonDeps,
    decompress: bool = Query(False, description="Decompress file server-side")
):
    """Download export with optional server-side decompression."""

    # Get export job
    export_job = await db.export_jobs.find_one({"_id": ObjectId(job_id)})
    file_path = export_job["file_info"]["path"]
    compression_format = export_job.get("compression_format", "none")

    # Determine file handling based on compression and decompress flag
    if compression_format == "zstd":
        if decompress:
            # Server-side decompression for browsers that don't support zstd
            return await stream_decompressed_zstd(file_path)
        else:
            # Send compressed with appropriate headers
            return FileResponse(
                file_path,
                media_type="application/zstd",
                headers={
                    "Content-Encoding": "zstd",
                    "Content-Disposition": f'attachment; filename="{filename}.zst"'
                }
            )

    elif compression_format == "tar.gz":
        # tar.gz is universally supported, no server-side decompression needed
        return FileResponse(
            file_path,
            media_type="application/gzip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}.tar.gz"'
            }
        )

    else:
        # Uncompressed file
        return FileResponse(
            file_path,
            media_type=get_media_type(export_job["format"]),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

async def stream_decompressed_zstd(file_path: str) -> StreamingResponse:
    """Stream decompressed zstd content."""
    async def generate():
        dctx = zstd.ZstdDecompressor()
        async with aiofiles.open(file_path, 'rb') as f:
            decompressor = dctx.decompressobj()
            while True:
                chunk = await f.read(8192)
                if not chunk:
                    break
                decompressed = decompressor.decompress(chunk)
                if decompressed:
                    yield decompressed

    return StreamingResponse(
        generate(),
        media_type="application/json",  # Or appropriate type
    )
```

### Phase 2: Frontend Support (Week 2)

#### 2.1 Update Export Panel with Compression Options
```typescript
// frontend/src/components/import-export/ExportPanel.tsx

interface CompressionOptions {
  enabled: boolean;
  format: 'none' | 'zstd' | 'tar.gz';
  level: number;
}

const [compressionOptions, setCompressionOptions] = useState<CompressionOptions>({
  enabled: false,
  format: 'none',
  level: 3,
});

// In the render:
<div className="space-y-4">
  <div className="flex items-center space-x-2">
    <input
      type="checkbox"
      checked={compressionOptions.enabled}
      onChange={(e) => setCompressionOptions(prev => ({
        ...prev,
        enabled: e.target.checked,
        format: e.target.checked ? 'tar.gz' : 'none'  // Default to tar.gz
      }))}
      className="rounded border-gray-300"
    />
    <label className="text-sm font-medium">Enable Compression</label>
  </div>

  {compressionOptions.enabled && (
    <>
      {/* Compression Format Selection */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Compression Format
        </label>
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => setCompressionOptions(prev => ({ ...prev, format: 'tar.gz' }))}
            className={cn(
              'p-3 rounded-lg border-2 transition-all text-sm',
              compressionOptions.format === 'tar.gz'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            )}
          >
            <div className="font-medium">tar.gz</div>
            <div className="text-xs text-gray-600 mt-1">
              Universal compatibility, works everywhere
            </div>
          </button>

          <button
            onClick={() => setCompressionOptions(prev => ({ ...prev, format: 'zstd' }))}
            className={cn(
              'p-3 rounded-lg border-2 transition-all text-sm',
              compressionOptions.format === 'zstd'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            )}
          >
            <div className="font-medium">zstd</div>
            <div className="text-xs text-gray-600 mt-1">
              Better compression, faster (requires tool)
            </div>
          </button>
        </div>
      </div>

      {/* Compression Level */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Compression Level: {compressionOptions.level}
        </label>
        <div className="flex items-center space-x-4">
          <span className="text-xs text-gray-500">Faster</span>
          <input
            type="range"
            min="1"
            max={compressionOptions.format === 'zstd' ? "9" : "9"}  // zstd supports up to 22 but 9 is reasonable max
            value={compressionOptions.level}
            onChange={(e) => setCompressionOptions(prev => ({
              ...prev,
              level: parseInt(e.target.value)
            }))}
            className="flex-1"
          />
          <span className="text-xs text-gray-500">Smaller</span>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {compressionOptions.level <= 3 && "Fast compression, larger file"}
          {compressionOptions.level > 3 && compressionOptions.level <= 6 && "Balanced speed and size"}
          {compressionOptions.level > 6 && "Maximum compression, slower"}
        </p>
      </div>

      {/* Format Recommendation */}
      <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
        <p className="text-xs text-blue-700 dark:text-blue-300">
          {compressionOptions.format === 'tar.gz' && (
            <>
              <strong>tar.gz recommended for:</strong> Manual downloads, sharing with others,
              archival storage. Works with all operating systems and tools.
            </>
          )}
          {compressionOptions.format === 'zstd' && (
            <>
              <strong>zstd recommended for:</strong> API consumption, automated processing,
              frequent downloads. 30% better compression than gzip.
            </>
          )}
        </p>
      </div>
    </>
  )}
</div>

// In handleExport function:
const exportRequest: CreateExportRequest = {
  format,
  filters: Object.keys(filters).length > 0 ? filters : undefined,
  options: {
    includeMessages: options.includeMessages,
    includeMetadata: options.includeMetadata,
    includeToolCalls: options.includeToolCalls,
    compressionFormat: compressionOptions.enabled ? compressionOptions.format : 'none',
    compressionLevel: compressionOptions.level,
  },
};
```

#### 2.2 Update Export History to Show Compression Info
```typescript
// frontend/src/components/import-export/ExportHistory.tsx

// In the table row for each export:
<td className="px-4 py-2">
  <div className="text-sm">
    <div className="font-medium">
      {formatFileSize(job.fileInfo?.size || 0)}
    </div>
    {job.compressionFormat && job.compressionFormat !== 'none' && (
      <div className="text-xs text-gray-500">
        <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-green-100 text-green-700">
          {job.compressionFormat}
        </span>
        <span className="ml-1">
          {formatFileSize(job.fileInfo?.compressedSize || 0)}
          ({job.compressionSavings}% smaller)
        </span>
      </div>
    )}
  </div>
</td>

// Download button with decompression option for zstd:
{job.compressionFormat === 'zstd' && (
  <div className="flex items-center space-x-2">
    <Button
      size="sm"
      onClick={() => handleDownload(job.jobId, false)}
      title="Download compressed (.zst)"
    >
      <Download className="w-4 h-4" />
      .zst
    </Button>
    <Button
      size="sm"
      variant="outline"
      onClick={() => handleDownload(job.jobId, true)}
      title="Download decompressed"
    >
      <Download className="w-4 h-4" />
      Original
    </Button>
  </div>
)}
{job.compressionFormat !== 'zstd' && (
  <Button
    size="sm"
    onClick={() => handleDownload(job.jobId)}
  >
    <Download className="w-4 h-4" />
    Download
  </Button>
)}
```

#### 2.3 Update API Types
```typescript
// frontend/src/api/import-export.ts

export interface CreateExportRequest {
  // ... existing fields ...
  options?: {
    includeMessages?: boolean;
    includeMetadata?: boolean;
    includeToolCalls?: boolean;
    compressionFormat?: 'none' | 'zstd' | 'tar.gz';
    compressionLevel?: number;  // 1-9 for gzip, 1-22 for zstd
  };
}

// Update download function to support decompression flag:
downloadExport: async (jobId: string, decompress: boolean = false): Promise<void> => {
  const url = decompress
    ? `/export/${jobId}/download?decompress=true`
    : `/export/${jobId}/download`;

  const blob = await apiClient.get<Blob>(url, {
    responseType: 'blob',
  });
  // ... rest of download logic
}
```

### Phase 3: Multi-File Export Support (Week 3)

#### 3.1 Bundle Multiple Formats in Single Archive
```python
# backend/app/services/export_service.py

async def create_multi_format_archive(
    self,
    job_id: str,
    formats: List[str],  # ['json', 'csv', 'markdown']
    sessions: List[Dict],
    compression_format: str
) -> Dict[str, Any]:
    """Create archive with multiple export formats."""

    if compression_format == "tar.gz":
        # Perfect for multiple files
        return await self._create_targz_multi(job_id, formats, sessions)
    elif compression_format == "zstd":
        # Create tar first, then compress with zstd
        return await self._create_tar_zst_multi(job_id, formats, sessions)
    else:
        # Create uncompressed tar for multiple files
        return await self._create_tar_multi(job_id, formats, sessions)

async def _create_targz_multi(self, job_id: str, formats: List[str], sessions: List[Dict]):
    """Create tar.gz with multiple format exports."""
    file_path = f"{self.export_dir}/{job_id}_multi.tar.gz"

    with tarfile.open(file_path, 'w:gz', compresslevel=3) as tar:
        for format in formats:
            # Generate content for each format
            content = await self.generate_format_content(sessions, format)

            # Add to tar
            info = tarfile.TarInfo(name=f"export_{job_id}.{format}")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))

    return {"path": file_path, "formats": formats}
```

### Phase 4: Progress Tracking and WebSocket Updates

#### 4.1 Enhanced Progress Messages
```python
# backend/app/services/websocket_manager.py

async def broadcast_compression_progress(
    self,
    job_id: str,
    stage: str,  # 'preparing', 'compressing', 'finalizing'
    progress: float,
    compression_format: str,
    estimated_savings: float
) -> None:
    """Broadcast compression progress updates."""
    await self.broadcast({
        "type": "compression_progress",
        "job_id": job_id,
        "stage": stage,
        "progress": progress,
        "compression_format": compression_format,
        "estimated_savings": estimated_savings,
        "message": f"Compressing with {compression_format}... {progress:.0f}%"
    })
```

### Testing Requirements

#### 1. Unit Tests
```python
# backend/tests/test_compression.py

@pytest.mark.asyncio
async def test_zstd_compression():
    """Test zstd compression and decompression."""
    content = b"test content" * 1000
    compressed = await compress_zstd(content, level=3)
    decompressed = await decompress_zstd(compressed)
    assert content == decompressed
    assert len(compressed) < len(content)

@pytest.mark.asyncio
async def test_targz_compression():
    """Test tar.gz compression."""
    files = {"file1.json": b"content1", "file2.csv": b"content2"}
    archive = await create_targz(files)
    extracted = await extract_targz(archive)
    assert files == extracted

@pytest.mark.asyncio
async def test_compression_format_selection():
    """Test correct format is applied."""
    for format in ['none', 'zstd', 'tar.gz']:
        result = await export_with_compression(format=format)
        assert result['compression_format'] == format
```

#### 2. Integration Tests
- Export 10MB+ files with each compression format
- Verify downloads work correctly
- Test browser compatibility with tar.gz
- Test zstd decompression fallback

#### 3. Performance Benchmarks
```python
# Compression ratio benchmarks (JSON data, 10MB)
# Format    | Ratio | Speed  | Decompress Speed
# ----------|-------|--------|------------------
# none      | 1.0x  | N/A    | N/A
# tar.gz    | 3.8x  | 15MB/s | 45MB/s
# zstd -3   | 4.2x  | 95MB/s | 280MB/s
# zstd -9   | 4.8x  | 25MB/s | 280MB/s
```

## Implementation Decision Guide

### When to Use tar.gz
- **User downloads** - Works in all browsers
- **File sharing** - Universal tool support
- **Archival storage** - Long-term compatibility
- **Multi-file exports** - Native bundling support
- **Cross-platform** - Works on Windows/Mac/Linux without tools

### When to Use zstd
- **API endpoints** - Better compression and speed
- **Internal storage** - Save 30% more space
- **Frequent access** - 3-5x faster decompression
- **Large datasets** - Better streaming performance
- **Modern infrastructure** - Where tools are available

### When to Use No Compression
- **Small exports** (<1MB) - Overhead not worth it
- **Real-time access** - No decompression delay
- **Text search** - Direct file inspection needed
- **Development** - Easier debugging

## Benefits

| Metric | tar.gz | zstd |
|--------|--------|------|
| Size Reduction | 60-75% | 70-80% |
| Compression Speed | 1x baseline | 3-5x faster |
| Decompression Speed | 1x baseline | 3-5x faster |
| Storage Cost Savings | 60-75% | 70-80% |
| Bandwidth Savings | 60-75% | 70-80% |
| Tool Availability | Universal | Growing |

## Estimated Timeline
- **Week 1**: Backend implementation for both formats
- **Week 2**: Frontend UI and integration
- **Week 3**: Multi-file support and testing
- **Total**: 3 weeks

## Risks & Mitigations

### Risk: zstd Browser Support
- **Impact**: Users can't decompress zstd files
- **Mitigation**:
  - Provide server-side decompression option
  - Show clear download options (compressed vs decompressed)
  - Default to tar.gz for maximum compatibility

### Risk: Large File Memory Usage
- **Impact**: Server runs out of memory during compression
- **Mitigation**:
  - Stream compression for large files
  - Set maximum file size limits
  - Use compression level 3 as default (balanced)

### Risk: User Confusion with Multiple Formats
- **Impact**: Users unsure which format to choose
- **Mitigation**:
  - Clear recommendations in UI
  - Smart defaults (tar.gz for downloads)
  - Tooltips explaining each format

## Future Enhancements

1. **Format Auto-Selection**
   - Detect user's environment
   - Recommend best format based on use case

2. **Incremental Compression**
   - Compress in chunks as data is generated
   - Better progress tracking

3. **Dictionary Compression**
   - Use shared dictionaries for better compression
   - Especially effective for similar exports

4. **Client-Side Decompression**
   - JavaScript zstd decompressor
   - Transparent decompression in browser
