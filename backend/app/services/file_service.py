"""File service for handling import/export file operations."""

import gzip
import hashlib
import io
import os
import tarfile
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, AsyncIterator, Dict, List, Optional

import aiofiles
import aiofiles.os
from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Configuration
MAX_UPLOAD_SIZE = getattr(
    settings, "MAX_UPLOAD_SIZE", 100 * 1024 * 1024
)  # 100MB default
TEMP_DIR = getattr(settings, "TEMP_DIR", tempfile.gettempdir())
EXPORT_DIR = os.path.join(TEMP_DIR, "claudelens", "exports")
IMPORT_DIR = os.path.join(TEMP_DIR, "claudelens", "imports")
CHUNK_SIZE = 8192  # 8KB chunks for file I/O

# Ensure directories exist
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(IMPORT_DIR, exist_ok=True)


class FileService:
    """Service for handling file operations with streaming support."""

    def __init__(self) -> None:
        """Initialize the file service."""
        self.export_dir = EXPORT_DIR
        self.import_dir = IMPORT_DIR
        self.chunk_size = CHUNK_SIZE

    async def validate_and_save_upload(
        self,
        file: UploadFile,
        max_size: int = MAX_UPLOAD_SIZE,
        allowed_extensions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Validate and save uploaded file with streaming to avoid memory issues.

        Args:
            file: The uploaded file
            max_size: Maximum allowed file size in bytes
            allowed_extensions: List of allowed file extensions (with dots), defaults to common formats

        Returns:
            Dictionary with file metadata

        Raises:
            HTTPException: If file validation fails
        """
        # Check file extension
        if allowed_extensions is None:
            allowed_extensions = [".json", ".csv", ".md", ".jsonl"]
        allowed_extensions_set = set(allowed_extensions)
        if file.filename is None:
            raise HTTPException(status_code=400, detail="File must have a filename")
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions_set:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Supported: {', '.join(allowed_extensions_set)}",
            )

        # Generate unique file path
        file_id = str(uuid.uuid4())
        temp_path = os.path.join(self.import_dir, f"{file_id}{file_ext}")

        size = 0
        hasher = hashlib.sha256()

        try:
            # Stream file to disk while validating size and calculating hash
            async with aiofiles.open(temp_path, "wb") as f:
                while chunk := await file.read(self.chunk_size):
                    size += len(chunk)
                    if size > max_size:
                        # Clean up partial file
                        await aiofiles.os.remove(temp_path)
                        raise HTTPException(
                            status_code=413,
                            detail=f"File too large. Max size: {max_size / (1024 * 1024):.1f}MB",
                        )

                    hasher.update(chunk)
                    await f.write(chunk)

            logger.info(f"Saved upload file: {temp_path}, size: {size} bytes")

            return {
                "file_id": file_id,
                "path": temp_path,
                "size": size,
                "checksum": hasher.hexdigest(),
                "filename": file.filename,
                "format": file_ext[1:],  # Remove the dot
            }

        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_path):
                try:
                    await aiofiles.os.remove(temp_path)
                except Exception:
                    pass

            if not isinstance(e, HTTPException):
                logger.error(f"Error saving upload: {e}")
                raise HTTPException(
                    status_code=500, detail="Failed to save uploaded file"
                )
            raise

    async def save_export_file(
        self,
        job_id: str,
        content_generator: AsyncGenerator[bytes, None],
        format: str,
    ) -> Dict[str, Any]:
        """
        Save export content from an async generator to a file.

        Args:
            job_id: Export job ID
            content_generator: Async generator yielding file content
            format: Export format (json, csv, markdown, pdf)

        Returns:
            Dictionary with file metadata
        """
        if format == "markdown":
            file_ext = "md"
        elif format == "pdf":
            file_ext = "html"  # Generate HTML that can be printed to PDF
        else:
            file_ext = format
        file_path = os.path.join(self.export_dir, f"{job_id}.{file_ext}")

        size = 0
        hasher = hashlib.sha256()

        try:
            async with aiofiles.open(file_path, "wb") as f:
                async for chunk in content_generator:
                    size += len(chunk)
                    hasher.update(chunk)
                    await f.write(chunk)

            logger.info(f"Saved export file: {file_path}, size: {size} bytes")

            return {
                "path": file_path,
                "size": size,
                "checksum": hasher.hexdigest(),
                "format": format,
            }

        except Exception as e:
            # Clean up on error
            if os.path.exists(file_path):
                try:
                    await aiofiles.os.remove(file_path)
                except Exception:
                    pass

            logger.error(f"Error saving export: {e}")
            raise

    async def save_export_file_compressed(
        self,
        job_id: str,
        content_generator: AsyncGenerator[bytes, None],
        format: str,
        compression_format: str = "none",
        compression_level: int = 3,
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
            # No compression - use original save method
            if format == "markdown":
                file_ext = "md"
            elif format == "pdf":
                file_ext = "html"
            else:
                file_ext = format
            file_path = os.path.join(self.export_dir, f"{job_id}.{file_ext}")

            async with aiofiles.open(file_path, "wb") as f:
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
        original_size: int,
    ) -> Dict[str, Any]:
        """Compress using Zstandard."""
        try:
            import zstandard as zstd
        except ImportError:
            logger.warning("zstandard library not installed, falling back to gzip")
            return await self._compress_targz(
                job_id, content_chunks, format, compression_level, original_size
            )

        if format == "markdown":
            file_ext = "md"
        elif format == "pdf":
            file_ext = "html"
        else:
            file_ext = format

        cctx = zstd.ZstdCompressor(level=min(compression_level, 22))
        file_path = os.path.join(self.export_dir, f"{job_id}.{file_ext}.zst")

        compressed_size = 0
        async with aiofiles.open(file_path, "wb") as f:
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
            "compression_ratio": (
                original_size / compressed_size if compressed_size > 0 else 1
            ),
            "compression_format": "zstd",
            "compression_savings_percent": (
                round((1 - compressed_size / original_size) * 100, 1)
                if original_size > 0
                else 0
            ),
        }

    async def _compress_targz(
        self,
        job_id: str,
        content_chunks: List[bytes],
        format: str,
        compression_level: int,
        original_size: int,
    ) -> Dict[str, Any]:
        """Compress using tar.gz format."""
        if format == "markdown":
            file_ext = "md"
        elif format == "pdf":
            file_ext = "html"
        else:
            file_ext = format

        file_path = os.path.join(self.export_dir, f"{job_id}.{file_ext}.tar.gz")

        # Create tar.gz file
        async with aiofiles.open(file_path, "wb") as f:
            # Create gzip wrapper
            gzip_buffer = io.BytesIO()

            with gzip.GzipFile(
                fileobj=gzip_buffer, mode="wb", compresslevel=min(compression_level, 9)
            ) as gz:
                # Create tar archive in memory
                tar_buffer = io.BytesIO()
                with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
                    # Create a file-like object from chunks
                    content = b"".join(content_chunks)
                    file_buffer = io.BytesIO(content)

                    # Add file to tar
                    tarinfo = tarfile.TarInfo(name=f"export_{job_id}.{file_ext}")
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

        # Get actual file size
        actual_size = os.path.getsize(file_path)

        return {
            "path": file_path,
            "size": original_size,
            "compressed_size": actual_size,
            "compression_ratio": original_size / actual_size if actual_size > 0 else 1,
            "compression_format": "tar.gz",
            "compression_savings_percent": (
                round((1 - actual_size / original_size) * 100, 1)
                if original_size > 0
                else 0
            ),
        }

    async def stream_file(
        self,
        file_path: str,
        chunk_size: Optional[int] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream a file from disk in chunks.

        Args:
            file_path: Path to the file to stream
            chunk_size: Size of chunks to yield (default: self.chunk_size)

        Yields:
            File content in chunks
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        chunk_size = chunk_size or self.chunk_size

        async with aiofiles.open(file_path, "rb") as f:
            while chunk := await f.read(chunk_size):
                yield chunk

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from disk.

        Args:
            file_path: Path to the file to delete

        Returns:
            True if file was deleted, False if it didn't exist
        """
        try:
            if os.path.exists(file_path):
                await aiofiles.os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False

    async def cleanup_old_files(
        self, directory: str, max_age_seconds: int = 86400
    ) -> int:
        """
        Clean up old files from a directory.

        Args:
            directory: Directory to clean
            max_age_seconds: Maximum age of files to keep (default: 24 hours)

        Returns:
            Number of files deleted
        """
        import time

        deleted_count = 0
        current_time = time.time()

        try:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        try:
                            await aiofiles.os.remove(file_path)
                            deleted_count += 1
                            logger.debug(f"Deleted old file: {file_path}")
                        except Exception as e:
                            logger.warning(
                                f"Failed to delete old file {file_path}: {e}"
                            )

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old files from {directory}")

            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old files in {directory}: {e}")
            return deleted_count

    @asynccontextmanager
    async def temporary_file(self, suffix: str = ".tmp") -> AsyncIterator[str]:
        """
        Async context manager for temporary files with automatic cleanup.

        Args:
            suffix: File suffix

        Yields:
            Path to temporary file
        """
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.import_dir)
        os.close(fd)  # Close the file descriptor

        try:
            yield path
        finally:
            # Ensure cleanup even if exception occurs
            try:
                if os.path.exists(path):
                    await aiofiles.os.remove(path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary file {path}: {e}")

    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about a file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file information
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = os.stat(file_path)

        return {
            "path": file_path,
            "size": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
            "filename": os.path.basename(file_path),
        }

    async def validate_json_file(self, file_path: str) -> bool:
        """
        Validate that a file contains valid JSON.

        Args:
            file_path: Path to the JSON file

        Returns:
            True if valid JSON, False otherwise
        """
        import json

        try:
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()
                json.loads(content)
                return True
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Invalid JSON in file {file_path}: {e}")
            return False

    async def validate_csv_file(self, file_path: str) -> bool:
        """
        Validate that a file contains valid CSV.

        Args:
            file_path: Path to the CSV file

        Returns:
            True if valid CSV, False otherwise
        """
        import csv

        try:
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()
                # Try to parse CSV
                csv.DictReader(content.splitlines())
                return True
        except Exception as e:
            logger.warning(f"Invalid CSV in file {file_path}: {e}")
            return False
