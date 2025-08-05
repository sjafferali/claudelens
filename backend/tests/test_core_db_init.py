"""Tests for database initialization utilities."""
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pymongo import errors

from app.core.db_init import (
    create_collections,
    create_index_if_not_exists,
    create_indexes,
    initialize_database,
)


class TestDatabaseInitialization:
    """Test database initialization functionality."""

    @pytest.mark.asyncio
    async def test_initialize_database_success(self):
        """Test successful database initialization."""
        db = Mock()

        with patch("app.core.db_init.create_collections") as mock_collections, patch(
            "app.core.db_init.create_indexes"
        ) as mock_indexes:
            mock_collections.return_value = None
            mock_indexes.return_value = None

            await initialize_database(db)

            mock_collections.assert_called_once_with(db)
            mock_indexes.assert_called_once_with(db)

    @pytest.mark.asyncio
    async def test_initialize_database_collection_error(self):
        """Test database initialization with collection creation error."""
        db = Mock()

        with patch("app.core.db_init.create_collections") as mock_collections, patch(
            "app.core.db_init.create_indexes"
        ) as mock_indexes:
            mock_collections.side_effect = Exception("Collection creation failed")

            with pytest.raises(Exception, match="Collection creation failed"):
                await initialize_database(db)

            mock_indexes.assert_not_called()

    @pytest.mark.asyncio
    async def test_initialize_database_index_error(self):
        """Test database initialization with index creation error."""
        db = Mock()

        with patch("app.core.db_init.create_collections") as mock_collections, patch(
            "app.core.db_init.create_indexes"
        ) as mock_indexes:
            mock_collections.return_value = None
            mock_indexes.side_effect = Exception("Index creation failed")

            with pytest.raises(Exception, match="Index creation failed"):
                await initialize_database(db)


class TestCreateCollections:
    """Test collection creation functionality."""

    @pytest.mark.asyncio
    async def test_create_collections_all_new(self):
        """Test creating all collections when none exist."""
        db = Mock()
        db.list_collection_names = AsyncMock(return_value=[])
        db.create_collection = AsyncMock()

        await create_collections(db)

        # Should create 4 collections: projects, sessions, messages, sync_state
        assert db.create_collection.call_count == 4

        # Check each collection was created
        calls = [call[0][0] for call in db.create_collection.call_args_list]
        assert "projects" in calls
        assert "sessions" in calls
        assert "messages" in calls
        assert "sync_state" in calls

    @pytest.mark.asyncio
    async def test_create_collections_some_exist(self):
        """Test creating collections when some already exist."""
        db = Mock()
        db.list_collection_names = AsyncMock(return_value=["projects", "messages"])
        db.create_collection = AsyncMock()

        await create_collections(db)

        # Should only create 2 collections: sessions, sync_state
        assert db.create_collection.call_count == 2

        calls = [call[0][0] for call in db.create_collection.call_args_list]
        assert "sessions" in calls
        assert "sync_state" in calls
        assert "projects" not in calls
        assert "messages" not in calls

    @pytest.mark.asyncio
    async def test_create_collections_all_exist(self):
        """Test creating collections when all already exist."""
        db = Mock()
        db.list_collection_names = AsyncMock(
            return_value=["projects", "sessions", "messages", "sync_state"]
        )
        db.create_collection = AsyncMock()

        await create_collections(db)

        # Should not create any collections
        db.create_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_collections_projects_validator(self):
        """Test projects collection validator schema."""
        db = Mock()
        db.list_collection_names = AsyncMock(return_value=[])
        db.create_collection = AsyncMock()

        await create_collections(db)

        # Find the projects collection call
        projects_call = None
        for call in db.create_collection.call_args_list:
            if call[0][0] == "projects":
                projects_call = call
                break

        assert projects_call is not None
        validator = projects_call[1]["validator"]
        assert "$jsonSchema" in validator
        assert "required" in validator["$jsonSchema"]
        assert "name" in validator["$jsonSchema"]["required"]
        assert "path" in validator["$jsonSchema"]["required"]

    @pytest.mark.asyncio
    async def test_create_collections_sessions_validator(self):
        """Test sessions collection validator schema."""
        db = Mock()
        db.list_collection_names = AsyncMock(return_value=[])
        db.create_collection = AsyncMock()

        await create_collections(db)

        # Find the sessions collection call
        sessions_call = None
        for call in db.create_collection.call_args_list:
            if call[0][0] == "sessions":
                sessions_call = call
                break

        assert sessions_call is not None
        validator = sessions_call[1]["validator"]
        assert "$jsonSchema" in validator
        assert "sessionId" in validator["$jsonSchema"]["required"]
        assert "projectId" in validator["$jsonSchema"]["required"]

    @pytest.mark.asyncio
    async def test_create_collections_messages_no_validator(self):
        """Test messages collection created without validator."""
        db = Mock()
        db.list_collection_names = AsyncMock(return_value=[])
        db.create_collection = AsyncMock()

        await create_collections(db)

        # Find the messages collection call
        messages_call = None
        for call in db.create_collection.call_args_list:
            if call[0][0] == "messages":
                messages_call = call
                break

        assert messages_call is not None
        # Messages collection should have no validator (flexible schema)
        assert len(messages_call[0]) == 1  # Only collection name, no validator

    @pytest.mark.asyncio
    async def test_create_collections_sync_state_validator(self):
        """Test sync_state collection validator schema."""
        db = Mock()
        db.list_collection_names = AsyncMock(return_value=[])
        db.create_collection = AsyncMock()

        await create_collections(db)

        # Find the sync_state collection call
        sync_call = None
        for call in db.create_collection.call_args_list:
            if call[0][0] == "sync_state":
                sync_call = call
                break

        assert sync_call is not None
        validator = sync_call[1]["validator"]
        assert "projectPath" in validator["$jsonSchema"]["required"]
        assert "lastSync" in validator["$jsonSchema"]["required"]


class TestCreateIndexes:
    """Test index creation functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database with collections."""
        db = Mock()
        db.projects = Mock()
        db.sessions = Mock()
        db.messages = Mock()
        db.sync_state = Mock()
        return db

    @pytest.mark.asyncio
    async def test_create_indexes_success(self, mock_db):
        """Test successful index creation."""
        with patch("app.core.db_init.create_index_if_not_exists") as mock_create:
            mock_create.return_value = None

            await create_indexes(mock_db)

            # Should create many indexes
            assert mock_create.call_count > 10

            # Check some key indexes were created
            calls = mock_create.call_args_list
            call_args = [(call[0][1], call[1].get("unique", False)) for call in calls]

            # Projects indexes
            assert ([("path", 1)], True) in call_args
            assert ([("name", "text")], False) in call_args

            # Sessions indexes
            assert ([("sessionId", 1)], True) in call_args
            assert ([("projectId", 1)], False) in call_args

    @pytest.mark.asyncio
    async def test_create_indexes_calls_all_collections(self, mock_db):
        """Test that indexes are created for all collections."""
        with patch("app.core.db_init.create_index_if_not_exists") as mock_create:
            mock_create.return_value = None

            await create_indexes(mock_db)

            calls = mock_create.call_args_list
            collections_called = {call[0][0] for call in calls}

            assert mock_db.projects in collections_called
            assert mock_db.sessions in collections_called
            assert mock_db.messages in collections_called
            assert mock_db.sync_state in collections_called


class TestCreateIndexIfNotExists:
    """Test index creation with existence checking."""

    @pytest.fixture
    def mock_collection(self):
        """Create mock collection."""
        collection = Mock()
        collection.name = "test_collection"
        return collection

    @pytest.mark.asyncio
    async def test_create_index_if_not_exists_success(self, mock_collection):
        """Test successful index creation."""
        mock_collection.create_index = AsyncMock(return_value="test_index_name")

        await create_index_if_not_exists(mock_collection, [("field", 1)])

        mock_collection.create_index.assert_called_once_with(
            [("field", 1)], unique=False
        )

    @pytest.mark.asyncio
    async def test_create_index_if_not_exists_unique(self, mock_collection):
        """Test unique index creation."""
        mock_collection.create_index = AsyncMock(return_value="unique_index")

        await create_index_if_not_exists(mock_collection, [("field", 1)], unique=True)

        mock_collection.create_index.assert_called_once_with(
            [("field", 1)], unique=True
        )

    @pytest.mark.asyncio
    async def test_create_index_if_not_exists_already_exists(self, mock_collection):
        """Test handling when index already exists."""
        error = errors.OperationFailure("Index already exists")
        mock_collection.create_index = AsyncMock(side_effect=error)

        # Should not raise exception
        await create_index_if_not_exists(mock_collection, [("field", 1)])

        mock_collection.create_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_index_if_not_exists_other_error(self, mock_collection):
        """Test handling of other operation failures."""
        error = errors.OperationFailure("Some other error")
        mock_collection.create_index = AsyncMock(side_effect=error)

        with pytest.raises(errors.OperationFailure, match="Some other error"):
            await create_index_if_not_exists(mock_collection, [("field", 1)])

    @pytest.mark.asyncio
    async def test_create_index_if_not_exists_compound_index(self, mock_collection):
        """Test creating compound indexes."""
        mock_collection.create_index = AsyncMock(return_value="compound_index")

        compound_keys = [("field1", 1), ("field2", -1), ("field3", "text")]
        await create_index_if_not_exists(mock_collection, compound_keys)

        mock_collection.create_index.assert_called_once_with(
            compound_keys, unique=False
        )


class TestCollectionValidatorSchemas:
    """Test collection validator schema details."""

    @pytest.mark.asyncio
    async def test_projects_collection_validator_properties(self):
        """Test projects collection validator has all required properties."""
        db = Mock()
        db.list_collection_names = AsyncMock(return_value=[])
        db.create_collection = AsyncMock()

        await create_collections(db)

        # Find projects validator
        projects_call = None
        for call in db.create_collection.call_args_list:
            if call[0][0] == "projects":
                projects_call = call
                break

        validator = projects_call[1]["validator"]["$jsonSchema"]
        properties = validator["properties"]

        assert "name" in properties
        assert "path" in properties
        assert "createdAt" in properties
        assert "updatedAt" in properties
        assert properties["name"]["bsonType"] == "string"
        assert properties["path"]["bsonType"] == "string"

    @pytest.mark.asyncio
    async def test_sessions_collection_validator_properties(self):
        """Test sessions collection validator has all required properties."""
        db = Mock()
        db.list_collection_names = AsyncMock(return_value=[])
        db.create_collection = AsyncMock()

        await create_collections(db)

        # Find sessions validator
        sessions_call = None
        for call in db.create_collection.call_args_list:
            if call[0][0] == "sessions":
                sessions_call = call
                break

        validator = sessions_call[1]["validator"]["$jsonSchema"]
        properties = validator["properties"]

        assert "sessionId" in properties
        assert "projectId" in properties
        assert "startedAt" in properties
        assert "endedAt" in properties
        assert "messageCount" in properties
        assert properties["projectId"]["bsonType"] == "objectId"
        assert properties["sessionId"]["bsonType"] == "string"

    @pytest.mark.asyncio
    async def test_sync_state_collection_validator_properties(self):
        """Test sync_state collection validator has all required properties."""
        db = Mock()
        db.list_collection_names = AsyncMock(return_value=[])
        db.create_collection = AsyncMock()

        await create_collections(db)

        # Find sync_state validator
        sync_call = None
        for call in db.create_collection.call_args_list:
            if call[0][0] == "sync_state":
                sync_call = call
                break

        validator = sync_call[1]["validator"]["$jsonSchema"]
        properties = validator["properties"]

        assert "projectPath" in properties
        assert "lastSync" in properties
        assert "lastFile" in properties
        assert "syncedHashes" in properties
        assert properties["syncedHashes"]["bsonType"] == "array"


class TestIndexCreationDetails:
    """Test specific index creation scenarios."""

    @pytest.fixture
    def mock_db_with_collections(self):
        """Create mock database with all collections."""
        db = Mock()
        for collection_name in ["projects", "sessions", "messages", "sync_state"]:
            collection = Mock()
            collection.name = collection_name
            setattr(db, collection_name, collection)
        return db

    @pytest.mark.asyncio
    async def test_projects_indexes_created(self, mock_db_with_collections):
        """Test that all projects indexes are created."""
        with patch("app.core.db_init.create_index_if_not_exists") as mock_create:
            mock_create.return_value = None

            await create_indexes(mock_db_with_collections)

            # Check projects-specific indexes
            projects_calls = [
                call
                for call in mock_create.call_args_list
                if call[0][0] == mock_db_with_collections.projects
            ]

            assert len(projects_calls) >= 2  # At least path and name indexes

            # Check for path unique index
            path_unique_found = any(
                call[0][1] == [("path", 1)] and call[1].get("unique", False)
                for call in projects_calls
            )
            assert path_unique_found

    @pytest.mark.asyncio
    async def test_messages_indexes_created(self, mock_db_with_collections):
        """Test that all messages indexes are created."""
        with patch("app.core.db_init.create_index_if_not_exists") as mock_create:
            mock_create.return_value = None

            await create_indexes(mock_db_with_collections)

            # Check messages-specific indexes
            messages_calls = [
                call
                for call in mock_create.call_args_list
                if call[0][0] == mock_db_with_collections.messages
            ]

            assert len(messages_calls) >= 10  # Many analytics indexes

            # Check for uuid unique index
            uuid_unique_found = any(
                call[0][1] == [("uuid", 1)] and call[1].get("unique", False)
                for call in messages_calls
            )
            assert uuid_unique_found

    @pytest.mark.asyncio
    async def test_sessions_indexes_created(self, mock_db_with_collections):
        """Test that all sessions indexes are created."""
        with patch("app.core.db_init.create_index_if_not_exists") as mock_create:
            mock_create.return_value = None

            await create_indexes(mock_db_with_collections)

            # Check sessions-specific indexes
            sessions_calls = [
                call
                for call in mock_create.call_args_list
                if call[0][0] == mock_db_with_collections.sessions
            ]

            assert len(sessions_calls) >= 5  # Multiple session indexes

            # Check for sessionId unique index
            session_unique_found = any(
                call[0][1] == [("sessionId", 1)] and call[1].get("unique", False)
                for call in sessions_calls
            )
            assert session_unique_found

    @pytest.mark.asyncio
    async def test_analytics_indexes_created(self, mock_db_with_collections):
        """Test that analytics-specific indexes are created."""
        with patch("app.core.db_init.create_index_if_not_exists") as mock_create:
            mock_create.return_value = None

            await create_indexes(mock_db_with_collections)

            # Check for analytics-specific indexes
            messages_calls = [
                call
                for call in mock_create.call_args_list
                if call[0][0] == mock_db_with_collections.messages
            ]

            # Check for createdAt indexes for time-series analytics
            created_at_indexes = [
                call
                for call in messages_calls
                if any("createdAt" in key[0] for key in call[0][1])
            ]
            assert len(created_at_indexes) >= 3

            # Check for git branch analytics indexes
            git_branch_indexes = [
                call
                for call in messages_calls
                if any("gitBranch" in key[0] for key in call[0][1])
            ]
            assert len(git_branch_indexes) >= 2


class TestErrorHandling:
    """Test error handling in database initialization."""

    @pytest.mark.asyncio
    async def test_collection_creation_failure(self):
        """Test handling of collection creation failure."""
        db = Mock()
        db.list_collection_names = AsyncMock(return_value=[])
        db.create_collection = AsyncMock(
            side_effect=Exception("Collection creation failed")
        )

        with pytest.raises(Exception, match="Collection creation failed"):
            await create_collections(db)

    @pytest.mark.asyncio
    async def test_list_collections_failure(self):
        """Test handling of list collections failure."""
        db = Mock()
        db.list_collection_names = AsyncMock(side_effect=Exception("List failed"))

        with pytest.raises(Exception, match="List failed"):
            await create_collections(db)

    @pytest.mark.asyncio
    async def test_index_creation_general_failure(self):
        """Test general index creation failure handling."""
        collection = Mock()
        collection.name = "test_collection"
        collection.create_index = AsyncMock(side_effect=Exception("General failure"))

        with pytest.raises(Exception, match="General failure"):
            await create_index_if_not_exists(collection, [("field", 1)])


class TestIndexCreationEdgeCases:
    """Test edge cases in index creation."""

    @pytest.mark.asyncio
    async def test_create_index_empty_keys(self):
        """Test creating index with empty keys."""
        collection = Mock()
        collection.name = "test_collection"
        collection.create_index = AsyncMock(return_value="empty_index")

        await create_index_if_not_exists(collection, [])

        collection.create_index.assert_called_once_with([], unique=False)

    @pytest.mark.asyncio
    async def test_create_index_complex_compound(self):
        """Test creating complex compound index."""
        collection = Mock()
        collection.name = "test_collection"
        collection.create_index = AsyncMock(return_value="complex_index")

        complex_keys = [
            ("field1", 1),
            ("field2", -1),
            ("field3", "text"),
            ("field4", "2dsphere"),
        ]
        await create_index_if_not_exists(collection, complex_keys, unique=True)

        collection.create_index.assert_called_once_with(complex_keys, unique=True)
