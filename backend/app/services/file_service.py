"""File service for handling import/export file operations."""

import hashlib
import os
import tempfile
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, AsyncIterator, Dict, Optional

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
    ) -> Dict[str, Any]:
        """
        Validate and save uploaded file with streaming to avoid memory issues.

        Args:
            file: The uploaded file
            max_size: Maximum allowed file size in bytes

        Returns:
            Dictionary with file metadata

        Raises:
            HTTPException: If file validation fails
        """
        # Check file extension
        allowed_extensions = {".json", ".csv", ".md", ".jsonl"}
        if file.filename is None:
            raise HTTPException(status_code=400, detail="File must have a filename")
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Supported: {', '.join(allowed_extensions)}",
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
        file_ext = format if format != "markdown" else "md"
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
