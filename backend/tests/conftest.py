"""Pytest configuration and fixtures."""
import asyncio
import os
from collections.abc import Generator

import pytest


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Enable testcontainers for tests
    os.environ["USE_TEST_DB"] = "true"
    
    # Set other test environment variables if needed
    os.environ["ENVIRONMENT"] = "test"
    
    
    # Cleanup is handled by atexit in testcontainers_db.py