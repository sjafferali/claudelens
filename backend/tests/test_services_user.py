"""Tests for user service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from app.models.user import UserCreate, UserRole, UserUpdate
from app.services.user import UserService


@pytest.fixture
def mock_db():
    """Create mock database."""
    db = MagicMock()
    db.users = MagicMock()
    db.projects = MagicMock()
    db.sessions = MagicMock()
    db.messages = MagicMock()
    return db


@pytest.fixture
def user_service(mock_db):
    """Create user service instance with mock database."""
    return UserService(mock_db)


@pytest.fixture
def test_user_data():
    """Create test user data."""
    return UserCreate(
        email="test@example.com",
        username="testuser",
        role=UserRole.USER,
    )


@pytest.fixture
def mock_user_doc():
    """Create mock user document."""
    api_key, key_hash = UserService.generate_api_key()
    return {
        "_id": ObjectId(),
        "email": "test@example.com",
        "username": "testuser",
        "role": "user",
        "api_keys": [
            {
                "key_hash": key_hash,
                "name": "Default",
                "created_at": datetime.now(UTC),
                "expires_at": datetime.now(UTC) + timedelta(days=365),
                "active": True,
            }
        ],
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "project_count": 0,
        "session_count": 0,
        "message_count": 0,
        "total_disk_usage": 0,
    }


@pytest.mark.asyncio
async def test_create_user(user_service, test_user_data, mock_db):
    """Test creating a new user."""
    # Mock database operations
    mock_db.users.find_one = AsyncMock(return_value=None)  # No existing user
    mock_db.users.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId()))

    user, api_key = await user_service.create_user(test_user_data)

    assert user.email == test_user_data.email
    assert user.username == test_user_data.username
    assert user.role == test_user_data.role
    assert len(user.api_keys) == 1
    assert api_key.startswith("cl_")

    # Verify database calls
    mock_db.users.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_id(user_service, mock_db, mock_user_doc):
    """Test getting user by ID."""
    user_id = str(mock_user_doc["_id"])
    mock_db.users.find_one = AsyncMock(return_value=mock_user_doc)

    retrieved_user = await user_service.get_user_by_id(user_id)

    assert retrieved_user is not None
    assert str(retrieved_user.id) == user_id
    assert retrieved_user.email == mock_user_doc["email"]

    # Verify database call
    mock_db.users.find_one.assert_called_once_with({"_id": ObjectId(user_id)})


@pytest.mark.asyncio
async def test_get_user_by_api_key(user_service, mock_db):
    """Test getting user by API key."""
    # Generate a real API key and hash
    api_key, key_hash = UserService.generate_api_key()

    mock_user_doc = {
        "_id": ObjectId(),
        "email": "test@example.com",
        "username": "testuser",
        "role": "user",
        "api_keys": [
            {
                "key_hash": key_hash,
                "name": "Default",
                "created_at": datetime.now(UTC),
                "expires_at": datetime.now(UTC) + timedelta(days=365),
                "active": True,
            }
        ],
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "project_count": 0,
        "session_count": 0,
        "message_count": 0,
        "total_disk_usage": 0,
    }

    # Mock find_one to return our user doc
    mock_db.users.find_one = AsyncMock(return_value=mock_user_doc)
    # Mock update_one for updating last_used timestamp
    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    retrieved_user = await user_service.get_user_by_api_key(api_key)

    assert retrieved_user is not None
    assert retrieved_user.email == mock_user_doc["email"]


@pytest.mark.asyncio
async def test_update_user(user_service, mock_db, mock_user_doc):
    """Test updating user details."""
    user_id = str(mock_user_doc["_id"])
    updated_doc = {**mock_user_doc, "role": "admin"}

    mock_db.users.find_one_and_update = AsyncMock(return_value=updated_doc)

    update_data = UserUpdate(role=UserRole.ADMIN)
    updated_user = await user_service.update_user(user_id, update_data)

    assert updated_user is not None
    assert updated_user.role == UserRole.ADMIN

    # Verify database call
    mock_db.users.find_one_and_update.assert_called_once()


@pytest.mark.asyncio
async def test_generate_new_api_key(user_service, mock_db):
    """Test generating a new API key."""
    user_id = str(ObjectId())

    # Mock update_one for adding new API key
    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    new_api_key = await user_service.generate_new_api_key(user_id, "Second API Key")

    assert new_api_key is not None
    assert new_api_key.startswith("cl_")

    # Verify database call
    mock_db.users.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_revoke_api_key(user_service, mock_db):
    """Test revoking an API key."""
    user_id = str(ObjectId())
    api_key, key_hash = UserService.generate_api_key()

    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    success = await user_service.revoke_api_key(user_id, key_hash)
    assert success is True

    # Verify database call
    mock_db.users.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_list_users(user_service, mock_db):
    """Test listing users."""
    mock_users = [
        {
            "_id": ObjectId(),
            "email": f"user{i}@example.com",
            "username": f"user{i}",
            "role": "user",
            "api_keys": [],
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "project_count": 0,
            "session_count": 0,
            "message_count": 0,
            "total_disk_usage": 0,
        }
        for i in range(3)
    ]

    # Mock count
    mock_db.users.count_documents = AsyncMock(return_value=3)

    # Mock find with cursor that supports chaining and async iteration
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor

    # Create proper async iterator
    async def async_generator():
        for user in mock_users:
            yield user

    mock_cursor.__aiter__ = lambda self: async_generator()
    mock_db.users.find.return_value = mock_cursor

    users, total = await user_service.list_users(skip=0, limit=10)

    assert total == 3
    assert len(users) == 3

    # Verify database calls
    mock_db.users.count_documents.assert_called_once()
    mock_db.users.find.assert_called_once()


@pytest.mark.asyncio
async def test_delete_user(user_service, mock_db):
    """Test deleting a user."""
    user_id = str(ObjectId())

    # Mock delete operations
    mock_db.users.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    mock_db.projects.delete_many = AsyncMock(return_value=MagicMock(deleted_count=2))
    mock_db.sessions.delete_many = AsyncMock(return_value=MagicMock(deleted_count=5))
    mock_db.messages.delete_many = AsyncMock(return_value=MagicMock(deleted_count=50))

    success = await user_service.delete_user(user_id)
    assert success is True

    # Verify delete operations were called
    mock_db.users.delete_one.assert_called_once_with({"_id": ObjectId(user_id)})
    mock_db.projects.delete_many.assert_called_once()
    mock_db.sessions.delete_many.assert_called_once()
    mock_db.messages.delete_many.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_stats(user_service, mock_db):
    """Test updating user statistics."""
    user_id = str(ObjectId())

    mock_db.users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    stats = {
        "project_count": 5,
        "session_count": 10,
        "message_count": 100,
        "total_disk_usage": 1024 * 1024,  # 1MB
    }

    success = await user_service.update_user_stats(user_id, stats)
    assert success is True

    # Verify database call
    mock_db.users.update_one.assert_called_once()
    call_args = mock_db.users.update_one.call_args
    assert call_args[0][0] == {"_id": ObjectId(user_id)}
    assert "$set" in call_args[0][1]


@pytest.mark.asyncio
async def test_api_key_verification(user_service):
    """Test API key verification."""
    api_key, key_hash = UserService.generate_api_key()

    # Test valid verification
    assert UserService.verify_api_key(api_key, key_hash) is True

    # Test invalid verification
    assert UserService.verify_api_key("wrong_key", key_hash) is False
    assert UserService.verify_api_key(api_key, "wrong_hash") is False


@pytest.mark.asyncio
async def test_duplicate_user_creation(user_service, test_user_data, mock_db):
    """Test that duplicate users cannot be created."""
    # First call returns None (user doesn't exist)
    # Second call returns existing user (duplicate)
    mock_db.users.find_one = AsyncMock(
        side_effect=[
            None,  # First check for email
            {"email": test_user_data.email},  # Second check shows duplicate
        ]
    )

    # Mock insert for first creation
    mock_db.users.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId()))

    # First creation should succeed
    user, api_key = await user_service.create_user(test_user_data)
    assert user is not None

    # Reset mock for duplicate check
    mock_db.users.find_one = AsyncMock(
        return_value={"email": test_user_data.email}  # User already exists
    )

    # Second creation should fail
    with pytest.raises(ValueError, match="already exists"):
        await user_service.create_user(test_user_data)
