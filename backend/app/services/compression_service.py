"""Compression service for backup/restore operations using zstandard."""

import hashlib
from typing import Any, AsyncGenerator, Optional

from app.core.logging import get_logger

zstd: Optional[Any] = None
try:
    import zstandard as zstd
except ImportError:
    pass

logger = get_logger(__name__)


class StreamingCompressor:
    """Handle streaming compression with zstandard."""

    def __init__(self, compression_level: int = 3):
        """
        Initialize compressor.
        Level 1-3: Fast compression
        Level 4-9: Balanced
        Level 10-22: Maximum compression

        Default level 3 provides good balance as specified in PRP.
        """
        if zstd is None:
            raise ImportError(
                "zstandard library is not installed. Run: pip install zstandard"
            )

        self.compression_level = compression_level
        logger.info(f"Initialized compressor with level {compression_level}")

    async def compress_stream(
        self, data_generator: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[bytes, None]:
        """Compress data stream on the fly."""
        if zstd is None:
            raise RuntimeError("zstandard library not available")
        cctx = zstd.ZstdCompressor(level=self.compression_level)
        compressor = cctx.compressobj()

        bytes_processed = 0
        compressed_bytes = 0

        async for chunk in data_generator:
            bytes_processed += len(chunk)
            compressed = compressor.compress(chunk)
            if compressed:
                compressed_bytes += len(compressed)
                yield compressed

            # Log progress periodically
            if bytes_processed % (1024 * 1024 * 10) == 0:  # Every 10MB
                ratio = compressed_bytes / bytes_processed if bytes_processed > 0 else 0
                logger.debug(
                    f"Compression progress: {bytes_processed / (1024*1024):.1f}MB processed, "
                    f"ratio: {ratio:.2%}"
                )

        # CRITICAL: Always flush to get final compressed data
        final = compressor.flush()
        if final:
            compressed_bytes += len(final)
            yield final

        ratio = compressed_bytes / bytes_processed if bytes_processed > 0 else 0
        logger.info(
            f"Compression complete: {bytes_processed / (1024*1024):.1f}MB -> "
            f"{compressed_bytes / (1024*1024):.1f}MB (ratio: {ratio:.2%})"
        )

    async def decompress_stream(
        self, compressed_generator: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[bytes, None]:
        """Decompress data stream on the fly."""
        if zstd is None:
            raise RuntimeError("zstandard library not available")
        dctx = zstd.ZstdDecompressor()
        decompressor = dctx.decompressobj()

        compressed_bytes = 0
        decompressed_bytes = 0

        async for chunk in compressed_generator:
            compressed_bytes += len(chunk)
            decompressed = decompressor.decompress(chunk)
            if decompressed:
                decompressed_bytes += len(decompressed)
                yield decompressed

            # Log progress periodically
            if compressed_bytes % (1024 * 1024 * 10) == 0:  # Every 10MB
                logger.debug(
                    f"Decompression progress: {compressed_bytes / (1024*1024):.1f}MB processed"
                )

        logger.info(
            f"Decompression complete: {compressed_bytes / (1024*1024):.1f}MB -> "
            f"{decompressed_bytes / (1024*1024):.1f}MB"
        )


class ChecksumCalculator:
    """Calculate checksums for data integrity verification."""

    def __init__(self, algorithm: str = "sha256"):
        """Initialize checksum calculator."""
        self.algorithm = algorithm
        self.hasher = hashlib.new(algorithm)

    def update(self, data: bytes) -> None:
        """Update checksum with new data."""
        self.hasher.update(data)

    def hexdigest(self) -> str:
        """Get hexadecimal digest of checksum."""
        return self.hasher.hexdigest()

    @classmethod
    async def calculate_stream_checksum(
        cls, data_generator: AsyncGenerator[bytes, None], algorithm: str = "sha256"
    ) -> tuple[AsyncGenerator[bytes, None], str]:
        """
        Calculate checksum while streaming data.
        Returns generator that yields data and final checksum.
        """
        calculator = cls(algorithm)

        async def generate_with_checksum() -> AsyncGenerator[bytes, None]:
            async for chunk in data_generator:
                calculator.update(chunk)
                yield chunk

        gen = generate_with_checksum()
        # Process all data
        async for _ in gen:
            pass

        return gen, calculator.hexdigest()


class StreamingCompressorWithChecksum:
    """Combine compression with checksum calculation."""

    def __init__(self, compression_level: int = 3):
        """Initialize compressor with checksum."""
        self.compressor = StreamingCompressor(compression_level)
        self.checksum_calculator = ChecksumCalculator()

    async def compress_with_checksum(
        self, data_generator: AsyncGenerator[bytes, None]
    ) -> tuple[AsyncGenerator[bytes, None], str]:
        """
        Compress data and calculate checksum.
        Returns compressed data generator and checksum.
        """
        checksum = None

        async def compress_and_checksum() -> AsyncGenerator[bytes, None]:
            nonlocal checksum
            calculator = ChecksumCalculator()

            # First calculate checksum on uncompressed data
            buffered_data = []
            async for chunk in data_generator:
                calculator.update(chunk)
                buffered_data.append(chunk)

            checksum = calculator.hexdigest()

            # Then compress the buffered data
            async def replay_data() -> AsyncGenerator[bytes, None]:
                for chunk in buffered_data:
                    yield chunk

            async for compressed_chunk in self.compressor.compress_stream(
                replay_data()
            ):
                yield compressed_chunk

        return compress_and_checksum(), checksum or ""


# Utility functions for file compression
async def compress_file_to_stream(
    file_path: str, chunk_size: int = 8192, compression_level: int = 3
) -> AsyncGenerator[bytes, None]:
    """Compress a file and yield compressed chunks."""
    import aiofiles

    compressor = StreamingCompressor(compression_level)

    async def read_file_chunks() -> AsyncGenerator[bytes, None]:
        async with aiofiles.open(file_path, "rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    async for compressed_chunk in compressor.compress_stream(read_file_chunks()):
        yield compressed_chunk


async def decompress_stream_to_file(
    compressed_generator: AsyncGenerator[bytes, None],
    output_path: str,
) -> int:
    """Decompress stream and write to file, returning bytes written."""
    import aiofiles

    compressor = StreamingCompressor()
    bytes_written = 0

    async with aiofiles.open(output_path, "wb") as f:
        async for decompressed_chunk in compressor.decompress_stream(
            compressed_generator
        ):
            await f.write(decompressed_chunk)
            bytes_written += len(decompressed_chunk)

    return bytes_written
