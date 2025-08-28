"""Test data ownership and isolation."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import UserRole
from app.schemas.ingest import MessageIngest
from app.services.ingest import IngestService


@pytest.fixture
def mock_db():
    """Create a mock database."""
    db = MagicMock()
    db.messages = MagicMock()
    db.sessions = MagicMock()
    return db


@pytest.fixture
def ingest_service(mock_db):
    """Create ingest service with mock database."""
    from app.services.ingest import IngestService
    from app.services.rolling_message_service import RollingMessageService

    service = IngestService(mock_db, user_id="test_user_id")
    service.rolling_service = MagicMock(spec=RollingMessageService)
    service.rolling_service.insert_message = AsyncMock(return_value=None)
    service.db = mock_db
    return service


@pytest.fixture
def rolling_service(mock_db):
    """Create rolling message service."""
    from unittest.mock import AsyncMock

    from app.services.rolling_message_service import RollingMessageService

    # Ensure mock_db has proper async methods for rolling service
    mock_db.list_collection_names = AsyncMock(return_value=[])

    service = RollingMessageService(mock_db)
    return service


def create_mock_db():
    """Create a mock database with necessary collections."""
    mock_db = MagicMock(spec=AsyncIOMotorDatabase)

    # Mock collections
    mock_db.users = MagicMock()
    mock_db.projects = MagicMock()
    mock_db.sessions = MagicMock()
    mock_db.messages = MagicMock()
    mock_db.ingestion_logs = MagicMock()

    # Storage for mock data
    mock_db._users = []
    mock_db._projects = []
    mock_db._sessions = []
    mock_db._messages = []
    mock_db._ingestion_logs = []

    # Mock list_collection_names for RollingMessageService
    mock_db.list_collection_names = AsyncMock(return_value=[])

    # Setup mock methods
    def mock_insert_one(collection_name):
        async def insert(doc):
            if collection_name == "users":
                mock_db._users.append(doc)
            elif collection_name == "projects":
                mock_db._projects.append(doc)
            elif collection_name == "sessions":
                mock_db._sessions.append(doc)
            elif collection_name == "messages":
                mock_db._messages.append(doc)
            elif collection_name == "ingestion_logs":
                mock_db._ingestion_logs.append(doc)
            result = MagicMock()
            result.inserted_id = doc.get("_id", ObjectId())
            return result

        return insert

    def mock_find_one(collection_name):
        async def find(filter_dict, *args, **kwargs):
            if collection_name == "users":
                for user in mock_db._users:
                    if all(user.get(k) == v for k, v in filter_dict.items()):
                        return user
            elif collection_name == "projects":
                for proj in mock_db._projects:
                    if all(proj.get(k) == v for k, v in filter_dict.items()):
                        return proj
            elif collection_name == "sessions":
                for sess in mock_db._sessions:
                    matches = True
                    for k, v in filter_dict.items():
                        if k not in sess or sess[k] != v:
                            matches = False
                            break
                    if matches:
                        return sess
            elif collection_name == "messages":
                for msg in mock_db._messages:
                    # For messages, check if the filter matches
                    matches = True
                    for k, v in filter_dict.items():
                        if k not in msg or msg[k] != v:
                            matches = False
                            break
                    if matches:
                        return msg
            return None

        return find

    mock_db.users.insert_one = mock_insert_one("users")
    mock_db.projects.insert_one = mock_insert_one("projects")
    mock_db.sessions.insert_one = mock_insert_one("sessions")
    mock_db.messages.insert_message = mock_insert_one("messages")
    mock_db.ingestion_logs.insert_one = mock_insert_one("ingestion_logs")

    async def mock_insert_many(docs):
        for doc in docs:
            mock_db._messages.append(doc)
        result = MagicMock()
        result.inserted_ids = [doc.get("_id", ObjectId()) for doc in docs]
        return result

    mock_db.messages.insert_many = mock_insert_many

    mock_db.users.find_one = mock_find_one("users")
    mock_db.projects.find_one = mock_find_one("projects")
    mock_db.sessions.find_one = mock_find_one("sessions")
    mock_db.messages.find_one = mock_find_one("messages")

    # Mock find().to_list()
    def mock_find(collection_name):
        def find(filter_dict, *args, **kwargs):
            result = MagicMock()

            async def to_list(length):
                data = []
                if collection_name == "projects":
                    data = [
                        p
                        for p in mock_db._projects
                        if all(p.get(k) == v for k, v in filter_dict.items())
                    ]
                elif collection_name == "sessions":
                    # Handle $in queries
                    if "projectId" in filter_dict and "$in" in filter_dict["projectId"]:
                        project_ids = filter_dict["projectId"]["$in"]
                        data = [
                            s
                            for s in mock_db._sessions
                            if s.get("projectId") in project_ids
                            and all(
                                s.get(k) == v
                                for k, v in filter_dict.items()
                                if k != "projectId"
                            )
                        ]
                    else:
                        data = [
                            s
                            for s in mock_db._sessions
                            if all(s.get(k) == v for k, v in filter_dict.items())
                        ]
                elif collection_name == "messages":
                    data = [
                        m
                        for m in mock_db._messages
                        if all(m.get(k) == v for k, v in filter_dict.items())
                    ]
                return data

            result.to_list = to_list
            return result

        return find

    mock_db.projects.find = mock_find("projects")
    mock_db.sessions.find = mock_find("sessions")
    mock_db.messages.find = mock_find("messages")

    # Mock update_one for sessions
    async def mock_update_one(doc_filter, update):
        # Find and update the session
        for sess in mock_db._sessions:
            if all(sess.get(k) == v for k, v in doc_filter.items()):
                if "$set" in update:
                    sess.update(update["$set"])
                elif "$inc" in update:
                    for k, v in update["$inc"].items():
                        sess[k] = sess.get(k, 0) + v
                result = MagicMock()
                result.modified_count = 1
                return result
        result = MagicMock()
        result.modified_count = 0
        return result

    mock_db.sessions.update_one = mock_update_one
    mock_db.projects.update_one = mock_update_one

    # Mock count_documents
    async def mock_count_documents(filter_dict):
        if "sessionId" in filter_dict:
            # Count messages for a session
            return len(
                [
                    m
                    for m in mock_db._messages
                    if m.get("sessionId") == filter_dict["sessionId"]
                ]
            )
        return 0

    # This will be set up in the test functions that use rolling_service
    mock_db.sessions.count_documents = mock_count_documents

    # Mock aggregate for token counting
    def mock_aggregate(pipeline):
        result = MagicMock()

        async def to_list(length):
            # Return empty aggregation results
            return []

        result.to_list = to_list
        return result

    mock_db.messages.aggregate = mock_aggregate
    mock_db.sessions.aggregate = mock_aggregate

    # Mock the websocket_manager that might be used
    mock_db.websocket_manager = None

    return mock_db


@pytest.mark.asyncio
async def test_ingestion_sets_user_id(ingest_service, rolling_service, mock_db):
    """Test that ingestion properly sets user_id on all created documents."""

    mock_db = create_mock_db()

    # Create test user manually
    test_user_id = ObjectId()
    test_user = {
        "_id": test_user_id,
        "email": "test@example.com",
        "username": "testuser",
        "role": UserRole.USER,
        "hashed_password": "hashed",
    }
    mock_db._users.append(test_user)

    # Create service with user_id
    service = IngestService(mock_db, str(test_user_id))

    # Mock the rolling_service methods to use the mock database
    async def mock_insert_message(message_data):
        message_data["_id"] = ObjectId()
        mock_db._messages.append(message_data)
        return str(message_data["_id"])

    async def mock_find_messages(filter_dict, skip=0, limit=100, sort_order="desc"):
        results = [
            msg
            for msg in mock_db._messages
            if all(msg.get(k) == v for k, v in filter_dict.items())
        ]
        return results[skip : skip + limit], len(results)

    async def mock_find_one(filter_dict):
        for msg in mock_db._messages:
            if all(msg.get(k) == v for k, v in filter_dict.items()):
                return msg
        return None

    service.rolling_service.insert_message = mock_insert_message
    service.rolling_service.find_messages = mock_find_messages
    service.rolling_service.find_one = mock_find_one

    # Create test message
    message = MessageIngest(
        uuid="test-uuid",
        sessionId="test-session",
        type="user",
        timestamp=datetime.now(UTC),
        message={"content": "test"},
        cwd="/test/project",
    )

    # Ingest message
    await service.ingest_messages([message])

    # Verify project has user_id
    project = await mock_db.projects.find_one({"path": "/test/project"})
    assert project is not None
    assert project["user_id"] == test_user_id

    # Verify session does NOT have user_id (hierarchical model)
    session = await mock_db.sessions.find_one({"sessionId": "test-session"})
    assert session is not None
    assert "user_id" not in session  # Hierarchical ownership
    assert session["projectId"] == project["_id"]

    # Verify message does NOT have user_id (hierarchical model)
    msg = await service.rolling_service.find_one({"uuid": "test-uuid"})
    assert msg is not None
    assert "user_id" not in msg  # Hierarchical ownership
    assert msg["sessionId"] == "test-session"


@pytest.mark.asyncio
async def test_data_isolation_between_users(ingest_service, rolling_service, mock_db):
    """Test that users cannot see each other's data."""

    mock_db = create_mock_db()

    # Create two test users manually
    test_user1_id = ObjectId()
    test_user1 = {
        "_id": test_user1_id,
        "email": "user1@example.com",
        "username": "user1",
        "role": UserRole.USER,
        "hashed_password": "hashed1",
    }
    mock_db._users.append(test_user1)

    test_user2_id = ObjectId()
    test_user2 = {
        "_id": test_user2_id,
        "email": "user2@example.com",
        "username": "user2",
        "role": UserRole.USER,
        "hashed_password": "hashed2",
    }
    mock_db._users.append(test_user2)

    # User 1 ingests data
    service1 = IngestService(mock_db, str(test_user1_id))

    # Mock rolling service for service1
    async def mock_insert_message1(message_data):
        message_data["_id"] = ObjectId()
        mock_db._messages.append(message_data)
        return str(message_data["_id"])

    async def mock_find_messages1(filter_dict, skip=0, limit=100, sort_order="desc"):
        results = [
            msg
            for msg in mock_db._messages
            if all(msg.get(k) == v for k, v in filter_dict.items())
        ]
        return results[skip : skip + limit], len(results)

    async def mock_find_one1(filter_dict):
        for msg in mock_db._messages:
            if all(msg.get(k) == v for k, v in filter_dict.items()):
                return msg
        return None

    service1.rolling_service.insert_message = mock_insert_message1
    service1.rolling_service.find_messages = mock_find_messages1
    service1.rolling_service.find_one = mock_find_one1

    message1 = MessageIngest(
        uuid="user1-msg",
        sessionId="user1-session",
        type="user",
        timestamp=datetime.now(UTC),
        message={"content": "user1 data"},
        cwd="/user1/project",
    )
    await service1.ingest_messages([message1])

    # User 2 ingests data
    service2 = IngestService(mock_db, str(test_user2_id))

    # Mock rolling service for service2
    service2.rolling_service.insert_message = mock_insert_message1
    service2.rolling_service.find_messages = mock_find_messages1
    service2.rolling_service.find_one = mock_find_one1
    message2 = MessageIngest(
        uuid="user2-msg",
        sessionId="user2-session",
        type="user",
        timestamp=datetime.now(UTC),
        message={"content": "user2 data"},
        cwd="/user2/project",
    )
    await service2.ingest_messages([message2])

    # User 1 should only see their project
    user1_projects = await mock_db.projects.find({"user_id": test_user1_id}).to_list(
        None
    )
    assert len(user1_projects) == 1
    assert user1_projects[0]["path"] == "/user1/project"

    # User 2 should only see their project
    user2_projects = await mock_db.projects.find({"user_id": test_user2_id}).to_list(
        None
    )
    assert len(user2_projects) == 1
    assert user2_projects[0]["path"] == "/user2/project"

    # Cross-check: User 1 cannot see User 2's data
    wrong_access = await mock_db.projects.find(
        {"user_id": test_user1_id, "path": "/user2/project"}
    ).to_list(None)
    assert len(wrong_access) == 0

    # Cross-check: User 2 cannot see User 1's data
    wrong_access = await mock_db.projects.find(
        {"user_id": test_user2_id, "path": "/user1/project"}
    ).to_list(None)
    assert len(wrong_access) == 0


@pytest.mark.asyncio
async def test_no_viewer_role_allowed():
    """Test that viewer role is no longer accepted."""
    from app.models.user import UserRole

    # Should not have VIEWER in enum
    assert not hasattr(UserRole, "VIEWER")

    # Should only have ADMIN and USER
    assert UserRole.ADMIN == "admin"
    assert UserRole.USER == "user"

    # Verify enum values
    valid_roles = list(UserRole)
    assert len(valid_roles) == 2
    assert UserRole.ADMIN in valid_roles
    assert UserRole.USER in valid_roles


@pytest.mark.asyncio
async def test_same_session_different_users_isolated(
    ingest_service, rolling_service, mock_db
):
    """Test that same session ID from different users remains isolated."""

    mock_db = create_mock_db()

    # Create two test users manually
    test_user1_id = ObjectId()
    test_user1 = {
        "_id": test_user1_id,
        "email": "user1@example.com",
        "username": "user1",
        "role": UserRole.USER,
        "hashed_password": "hashed1",
    }
    mock_db._users.append(test_user1)

    test_user2_id = ObjectId()
    test_user2 = {
        "_id": test_user2_id,
        "email": "user2@example.com",
        "username": "user2",
        "role": UserRole.USER,
        "hashed_password": "hashed2",
    }
    mock_db._users.append(test_user2)

    # Both users ingest data with SAME session ID
    shared_session_id = "shared-session-123"

    # User 1 ingests data
    service1 = IngestService(mock_db, str(test_user1_id))

    # Mock rolling service for service1
    async def mock_insert_message_shared(message_data):
        message_data["_id"] = ObjectId()
        mock_db._messages.append(message_data)
        return str(message_data["_id"])

    async def mock_find_messages_shared(
        filter_dict, skip=0, limit=100, sort_order="desc"
    ):
        results = [
            msg
            for msg in mock_db._messages
            if all(msg.get(k) == v for k, v in filter_dict.items())
        ]
        return results[skip : skip + limit], len(results)

    async def mock_find_one_shared(filter_dict):
        for msg in mock_db._messages:
            if all(msg.get(k) == v for k, v in filter_dict.items()):
                return msg
        return None

    service1.rolling_service.insert_message = mock_insert_message_shared
    service1.rolling_service.find_messages = mock_find_messages_shared
    service1.rolling_service.find_one = mock_find_one_shared

    message1 = MessageIngest(
        uuid="user1-msg-1",
        sessionId=shared_session_id,
        type="user",
        timestamp=datetime.now(UTC),
        message={"content": "user1 data"},
        cwd="/user1/project",
    )
    await service1.ingest_messages([message1])

    # User 2 ingests data with same session ID
    service2 = IngestService(mock_db, str(test_user2_id))

    # Mock rolling service for service2 (use same mock to share storage)
    service2.rolling_service.insert_message = mock_insert_message_shared
    service2.rolling_service.find_messages = mock_find_messages_shared
    service2.rolling_service.find_one = mock_find_one_shared

    message2 = MessageIngest(
        uuid="user2-msg-1",
        sessionId=shared_session_id,
        type="user",
        timestamp=datetime.now(UTC),
        message={"content": "user2 data"},
        cwd="/user2/project",
    )
    await service2.ingest_messages([message2])

    # Get user's projects to find their sessions
    user1_projects = await mock_db.projects.find({"user_id": test_user1_id}).to_list(
        None
    )
    user1_project_ids = [p["_id"] for p in user1_projects]

    user2_projects = await mock_db.projects.find({"user_id": test_user2_id}).to_list(
        None
    )
    user2_project_ids = [p["_id"] for p in user2_projects]

    # Each user should have their own session with that ID (through project ownership)
    user1_sessions = await mock_db.sessions.find(
        {"projectId": {"$in": user1_project_ids}, "sessionId": shared_session_id}
    ).to_list(None)
    assert len(user1_sessions) == 1
    assert user1_sessions[0]["sessionId"] == shared_session_id

    user2_sessions = await mock_db.sessions.find(
        {"projectId": {"$in": user2_project_ids}, "sessionId": shared_session_id}
    ).to_list(None)
    assert len(user2_sessions) == 1
    assert user2_sessions[0]["sessionId"] == shared_session_id

    # Total sessions with that ID should be 2 (one per user)
    all_sessions = await mock_db.sessions.find(
        {"sessionId": shared_session_id}
    ).to_list(None)
    assert len(all_sessions) == 2

    # Messages should be properly isolated (messages don't have user_id in hierarchical model)
    all_messages = await mock_db.messages.find(
        {"sessionId": shared_session_id}
    ).to_list(None)
    # Check that messages belong to the correct session based on uuid
    user1_msg = [m for m in all_messages if m["uuid"] == "user1-msg-1"]
    assert len(user1_msg) == 1

    user2_msg = [m for m in all_messages if m["uuid"] == "user2-msg-1"]
    assert len(user2_msg) == 1
