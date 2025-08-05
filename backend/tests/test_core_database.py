"""Tests for database utilities in app/core/database.py."""
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from pymongo import errors

from app.core.database import (
    MongoDB,
    close_mongodb_connection,
    connect_to_mongodb,
    get_database,
    get_messages_collection,
    get_projects_collection,
    get_sessions_collection,
    get_sync_state_collection,
)


@pytest.fixture
def mock_motor_client():
    """Create a mock AsyncIOMotorClient."""
    client = MagicMock(spec=AsyncIOMotorClient)

    # Mock admin commands
    admin_mock = MagicMock()
    admin_mock.command = AsyncMock(return_value={"ok": 1})
    client.admin = admin_mock

    # Mock database access
    db_mock = MagicMock(spec=AsyncIOMotorDatabase)
    client.__getitem__ = MagicMock(return_value=db_mock)

    # Mock collections
    db_mock.projects = MagicMock(spec=AsyncIOMotorCollection)
    db_mock.sessions = MagicMock(spec=AsyncIOMotorCollection)
    db_mock.messages = MagicMock(spec=AsyncIOMotorCollection)
    db_mock.sync_state = MagicMock(spec=AsyncIOMotorCollection)

    return client, db_mock


@pytest.fixture
def reset_db_state():
    """Reset the global db state before and after each test."""
    # Import the actual db object
    from app.core import database

    # Save original state
    original_client = database.db.client
    original_database = database.db.database

    # Reset state
    database.db.client = None
    database.db.database = None

    yield database.db

    # Restore original state
    database.db.client = original_client
    database.db.database = original_database


class TestMongoDBConnection:
    """Test cases for MongoDB connection management."""

    @pytest.mark.asyncio
    async def test_connect_to_mongodb_success(
        self, mock_motor_client, reset_db_state, caplog
    ):
        """Test successful MongoDB connection."""
        client_mock, db_mock = mock_motor_client

        with patch("app.core.database.AsyncIOMotorClient", return_value=client_mock):
            with patch(
                "app.core.database.get_testcontainer_mongodb_url", return_value=None
            ):
                with patch("app.core.database.settings") as mock_settings:
                    mock_settings.MONGODB_URL = "mongodb://localhost:27017"
                    mock_settings.DATABASE_NAME = "test_db"
                    mock_settings.MAX_CONNECTIONS_COUNT = 10
                    mock_settings.MIN_CONNECTIONS_COUNT = 5

                    with caplog.at_level(logging.INFO):
                        await connect_to_mongodb()

                    # Verify client was created with correct parameters
                    from app.core.database import AsyncIOMotorClient

                    AsyncIOMotorClient.assert_called_once_with(
                        "mongodb://localhost:27017", maxPoolSize=10, minPoolSize=5
                    )

                    # Verify database was set
                    assert reset_db_state.client == client_mock
                    assert reset_db_state.database == db_mock

                    # Verify ping was called
                    client_mock.admin.command.assert_called_once_with("ping")

                    # Verify logging
                    assert "Successfully connected to MongoDB" in caplog.text
                    assert "mongodb://localhost:27017" in caplog.text

    @pytest.mark.asyncio
    async def test_connect_to_mongodb_with_testcontainer(
        self, mock_motor_client, reset_db_state
    ):
        """Test MongoDB connection with testcontainer URL."""
        client_mock, db_mock = mock_motor_client

        with patch("app.core.database.AsyncIOMotorClient", return_value=client_mock):
            with patch(
                "app.core.database.get_testcontainer_mongodb_url",
                return_value="mongodb://testcontainer:27017",
            ):
                with patch("app.core.database.settings") as mock_settings:
                    mock_settings.MONGODB_URL = "mongodb://localhost:27017"
                    mock_settings.DATABASE_NAME = "test_db"
                    mock_settings.MAX_CONNECTIONS_COUNT = 10
                    mock_settings.MIN_CONNECTIONS_COUNT = 5

                    await connect_to_mongodb()

                    # Verify testcontainer URL was used instead of settings URL
                    from app.core.database import AsyncIOMotorClient

                    AsyncIOMotorClient.assert_called_once_with(
                        "mongodb://testcontainer:27017", maxPoolSize=10, minPoolSize=5
                    )

    @pytest.mark.asyncio
    async def test_connect_to_mongodb_connection_failure(self, reset_db_state, caplog):
        """Test MongoDB connection failure handling."""
        with patch("app.core.database.AsyncIOMotorClient") as mock_client_class:
            # Create a mock client that raises ConnectionFailure on ping
            mock_client = MagicMock()
            mock_admin = MagicMock()
            mock_admin.command = AsyncMock(
                side_effect=errors.ConnectionFailure("Connection failed")
            )
            mock_client.admin = mock_admin
            mock_client_class.return_value = mock_client

            with patch(
                "app.core.database.get_testcontainer_mongodb_url", return_value=None
            ):
                with patch("app.core.database.settings") as mock_settings:
                    mock_settings.MONGODB_URL = "mongodb://localhost:27017"
                    mock_settings.DATABASE_NAME = "test_db"
                    mock_settings.MAX_CONNECTIONS_COUNT = 10
                    mock_settings.MIN_CONNECTIONS_COUNT = 5

                    with caplog.at_level(logging.ERROR):
                        with pytest.raises(
                            errors.ConnectionFailure, match="Connection failed"
                        ):
                            await connect_to_mongodb()

                    # Verify error was logged
                    assert "Could not connect to MongoDB" in caplog.text
                    assert "Connection failed" in caplog.text

    @pytest.mark.asyncio
    async def test_close_mongodb_connection_with_client(self, reset_db_state, caplog):
        """Test closing MongoDB connection when client exists."""
        mock_client = MagicMock(spec=AsyncIOMotorClient)
        reset_db_state.client = mock_client

        with caplog.at_level(logging.INFO):
            await close_mongodb_connection()

        # Verify client.close() was called
        mock_client.close.assert_called_once()

        # Verify logging
        assert "Disconnected from MongoDB" in caplog.text

    @pytest.mark.asyncio
    async def test_close_mongodb_connection_without_client(
        self, reset_db_state, caplog
    ):
        """Test closing MongoDB connection when no client exists."""
        reset_db_state.client = None

        with caplog.at_level(logging.INFO):
            await close_mongodb_connection()

        # Verify no error occurs and no log message
        assert "Disconnected from MongoDB" not in caplog.text


class TestDatabaseAccessor:
    """Test cases for database accessor functions."""

    @pytest.mark.asyncio
    async def test_get_database_when_connected(self, mock_motor_client, reset_db_state):
        """Test get_database when already connected."""
        client_mock, db_mock = mock_motor_client
        reset_db_state.database = db_mock

        result = await get_database()

        assert result == db_mock

    @pytest.mark.asyncio
    async def test_get_database_when_not_connected(
        self, mock_motor_client, reset_db_state
    ):
        """Test get_database when not yet connected."""
        client_mock, db_mock = mock_motor_client
        reset_db_state.database = None

        with patch(
            "app.core.database.connect_to_mongodb", new_callable=AsyncMock
        ) as mock_connect:
            # Set up the database after connect is called
            async def setup_db():
                reset_db_state.database = db_mock

            mock_connect.side_effect = setup_db

            result = await get_database()

            # Verify connect was called
            mock_connect.assert_called_once()

            # Verify database was returned
            assert result == db_mock

    @pytest.mark.asyncio
    async def test_get_database_assertion_error(self, reset_db_state):
        """Test get_database raises assertion error if database is still None after connect."""
        reset_db_state.database = None

        with patch("app.core.database.connect_to_mongodb", new_callable=AsyncMock):
            # Don't set up database, leave it as None

            with pytest.raises(AssertionError):
                await get_database()


class TestCollectionAccessors:
    """Test cases for collection accessor functions."""

    @pytest.mark.asyncio
    async def test_get_projects_collection(self, mock_motor_client, reset_db_state):
        """Test getting projects collection."""
        client_mock, db_mock = mock_motor_client
        projects_collection = MagicMock(spec=AsyncIOMotorCollection)
        db_mock.projects = projects_collection

        with patch(
            "app.core.database.get_database",
            new_callable=AsyncMock,
            return_value=db_mock,
        ):
            result = await get_projects_collection()

            assert result == projects_collection

    @pytest.mark.asyncio
    async def test_get_sessions_collection(self, mock_motor_client, reset_db_state):
        """Test getting sessions collection."""
        client_mock, db_mock = mock_motor_client
        sessions_collection = MagicMock(spec=AsyncIOMotorCollection)
        db_mock.sessions = sessions_collection

        with patch(
            "app.core.database.get_database",
            new_callable=AsyncMock,
            return_value=db_mock,
        ):
            result = await get_sessions_collection()

            assert result == sessions_collection

    @pytest.mark.asyncio
    async def test_get_messages_collection(self, mock_motor_client, reset_db_state):
        """Test getting messages collection."""
        client_mock, db_mock = mock_motor_client
        messages_collection = MagicMock(spec=AsyncIOMotorCollection)
        db_mock.messages = messages_collection

        with patch(
            "app.core.database.get_database",
            new_callable=AsyncMock,
            return_value=db_mock,
        ):
            result = await get_messages_collection()

            assert result == messages_collection

    @pytest.mark.asyncio
    async def test_get_sync_state_collection(self, mock_motor_client, reset_db_state):
        """Test getting sync_state collection."""
        client_mock, db_mock = mock_motor_client
        sync_state_collection = MagicMock(spec=AsyncIOMotorCollection)
        db_mock.sync_state = sync_state_collection

        with patch(
            "app.core.database.get_database",
            new_callable=AsyncMock,
            return_value=db_mock,
        ):
            result = await get_sync_state_collection()

            assert result == sync_state_collection

    @pytest.mark.asyncio
    async def test_all_collection_accessors_use_same_database(
        self, mock_motor_client, reset_db_state
    ):
        """Test that all collection accessors use the same database instance."""
        client_mock, db_mock = mock_motor_client

        with patch(
            "app.core.database.get_database",
            new_callable=AsyncMock,
            return_value=db_mock,
        ) as mock_get_db:
            # Call all collection accessors
            await get_projects_collection()
            await get_sessions_collection()
            await get_messages_collection()
            await get_sync_state_collection()

            # Verify get_database was called 4 times
            assert mock_get_db.call_count == 4

            # All calls should return collections from the same database
            for call in mock_get_db.call_args_list:
                assert call == ((), {})  # No arguments passed


class TestMongoDBClass:
    """Test cases for MongoDB class."""

    def test_mongodb_class_initialization(self):
        """Test MongoDB class initializes with None values."""
        db_instance = MongoDB()

        assert db_instance.client is None
        assert db_instance.database is None

    def test_global_db_instance(self):
        """Test global db instance is created."""
        from app.core.database import db

        assert isinstance(db, MongoDB)
        # The global instance might have values set from other tests,
        # so we just verify it exists and is the right type


class TestIntegrationScenarios:
    """Test integration scenarios for database module."""

    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, mock_motor_client, reset_db_state):
        """Test complete connection lifecycle."""
        client_mock, db_mock = mock_motor_client

        # Initially, no connection
        assert reset_db_state.client is None
        assert reset_db_state.database is None

        # Connect
        with patch("app.core.database.AsyncIOMotorClient", return_value=client_mock):
            with patch(
                "app.core.database.get_testcontainer_mongodb_url", return_value=None
            ):
                with patch("app.core.database.settings") as mock_settings:
                    mock_settings.MONGODB_URL = "mongodb://localhost:27017"
                    mock_settings.DATABASE_NAME = "test_db"
                    mock_settings.MAX_CONNECTIONS_COUNT = 10
                    mock_settings.MIN_CONNECTIONS_COUNT = 5

                    await connect_to_mongodb()

        # After connection
        assert reset_db_state.client == client_mock
        assert reset_db_state.database == db_mock

        # Access collections
        projects = await get_projects_collection()
        assert projects == db_mock.projects

        # Close connection
        await close_mongodb_connection()
        client_mock.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_reconnection_after_failure(self, reset_db_state):
        """Test reconnection after initial failure."""
        # First connection attempt fails
        with patch("app.core.database.AsyncIOMotorClient") as mock_client_class:
            mock_client = MagicMock()
            mock_admin = MagicMock()
            mock_admin.command = AsyncMock(
                side_effect=errors.ConnectionFailure("First attempt failed")
            )
            mock_client.admin = mock_admin
            mock_client_class.return_value = mock_client

            with patch(
                "app.core.database.get_testcontainer_mongodb_url", return_value=None
            ):
                with patch("app.core.database.settings") as mock_settings:
                    mock_settings.MONGODB_URL = "mongodb://localhost:27017"
                    mock_settings.DATABASE_NAME = "test_db"
                    mock_settings.MAX_CONNECTIONS_COUNT = 10
                    mock_settings.MIN_CONNECTIONS_COUNT = 5

                    with pytest.raises(errors.ConnectionFailure):
                        await connect_to_mongodb()

        # Second connection attempt succeeds
        with patch("app.core.database.AsyncIOMotorClient") as mock_client_class:
            mock_client = MagicMock()
            mock_admin = MagicMock()
            mock_admin.command = AsyncMock(return_value={"ok": 1})
            mock_client.admin = mock_admin
            mock_db = MagicMock(spec=AsyncIOMotorDatabase)
            mock_client.__getitem__ = MagicMock(return_value=mock_db)
            mock_client_class.return_value = mock_client

            with patch(
                "app.core.database.get_testcontainer_mongodb_url", return_value=None
            ):
                with patch("app.core.database.settings") as mock_settings:
                    mock_settings.MONGODB_URL = "mongodb://localhost:27017"
                    mock_settings.DATABASE_NAME = "test_db"
                    mock_settings.MAX_CONNECTIONS_COUNT = 10
                    mock_settings.MIN_CONNECTIONS_COUNT = 5

                    await connect_to_mongodb()

                    # Verify connection succeeded
                    assert reset_db_state.client == mock_client
                    assert reset_db_state.database == mock_db
