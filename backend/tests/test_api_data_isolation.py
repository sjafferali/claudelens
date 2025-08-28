"""Test API-level data isolation."""

import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import UserCreate, UserRole
from app.services.user import UserService

# Skip tests that require full app context with database
pytestmark = pytest.mark.skipif(
    True,  # Skip API integration tests that require test infrastructure improvements
    reason="API integration tests require proper test database setup with dependency injection",
)


@pytest.mark.asyncio
async def test_api_data_isolation(client: AsyncClient, test_db: AsyncIOMotorDatabase):
    """Test that API endpoints properly isolate data between users."""

    # Create two test users with API keys
    user_service = UserService(test_db)

    # Create user 1
    test_user1, _ = await user_service.create_user(
        UserCreate(
            email="apiuser1@example.com", username="apiuser1", role=UserRole.USER
        )
    )
    api_key1 = await user_service.create_api_key(str(test_user1.id), "Test Key 1")

    # Create user 2
    test_user2, _ = await user_service.create_user(
        UserCreate(
            email="apiuser2@example.com", username="apiuser2", role=UserRole.USER
        )
    )
    api_key2 = await user_service.create_api_key(str(test_user2.id), "Test Key 2")

    # User 1 uploads data
    response1 = await client.post(
        "/api/v1/ingest/batch",
        headers={"X-API-Key": api_key1},
        json={
            "messages": [
                {
                    "uuid": "user1-msg",
                    "sessionId": "user1-session",
                    "type": "user",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "message": {"content": "user1 data"},
                    "cwd": "/user1/project",
                }
            ]
        },
    )
    assert response1.status_code == 200

    # User 2 uploads data
    response2 = await client.post(
        "/api/v1/ingest/batch",
        headers={"X-API-Key": api_key2},
        json={
            "messages": [
                {
                    "uuid": "user2-msg",
                    "sessionId": "user2-session",
                    "type": "user",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "message": {"content": "user2 data"},
                    "cwd": "/user2/project",
                }
            ]
        },
    )
    assert response2.status_code == 200

    # User 1 lists projects - should only see their own
    projects1 = await client.get("/api/v1/projects/", headers={"X-API-Key": api_key1})
    assert projects1.status_code == 200
    data1 = projects1.json()
    assert data1["total"] == 1
    assert data1["items"][0]["path"] == "/user1/project"

    # User 2 lists projects - should only see their own
    projects2 = await client.get("/api/v1/projects/", headers={"X-API-Key": api_key2})
    assert projects2.status_code == 200
    data2 = projects2.json()
    assert data2["total"] == 1
    assert data2["items"][0]["path"] == "/user2/project"

    # User 1 cannot access User 2's project
    # Get User 2's project ID
    user2_project_id = data2["items"][0]["_id"]

    # Try to access it as User 1
    forbidden = await client.get(
        f"/api/v1/projects/{user2_project_id}", headers={"X-API-Key": api_key1}
    )
    assert forbidden.status_code == 404  # Should not find it due to user_id filtering

    # User 2 cannot access User 1's project
    user1_project_id = data1["items"][0]["_id"]

    # Try to access it as User 2
    forbidden = await client.get(
        f"/api/v1/projects/{user1_project_id}", headers={"X-API-Key": api_key2}
    )
    assert forbidden.status_code == 404  # Should not find it due to user_id filtering


@pytest.mark.asyncio
async def test_api_session_isolation(
    client: AsyncClient, test_db: AsyncIOMotorDatabase
):
    """Test that sessions are properly isolated between users via API."""

    # Create two test users with API keys
    user_service = UserService(test_db)

    # Create user 1
    test_user1, _ = await user_service.create_user(
        UserCreate(
            email="sessionuser1@example.com",
            username="sessionuser1",
            role=UserRole.USER,
        )
    )
    api_key1 = await user_service.create_api_key(str(test_user1.id), "Session Key 1")

    # Create user 2
    test_user2, _ = await user_service.create_user(
        UserCreate(
            email="sessionuser2@example.com",
            username="sessionuser2",
            role=UserRole.USER,
        )
    )
    api_key2 = await user_service.create_api_key(str(test_user2.id), "Session Key 2")

    # User 1 creates a session
    response1 = await client.post(
        "/api/v1/ingest/batch",
        headers={"X-API-Key": api_key1},
        json={
            "messages": [
                {
                    "uuid": "session1-msg",
                    "sessionId": "unique-session-1",
                    "type": "user",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "message": {"content": "session1 data"},
                    "cwd": "/session1/project",
                }
            ]
        },
    )
    assert response1.status_code == 200

    # User 2 creates a session
    response2 = await client.post(
        "/api/v1/ingest/batch",
        headers={"X-API-Key": api_key2},
        json={
            "messages": [
                {
                    "uuid": "session2-msg",
                    "sessionId": "unique-session-2",
                    "type": "user",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "message": {"content": "session2 data"},
                    "cwd": "/session2/project",
                }
            ]
        },
    )
    assert response2.status_code == 200

    # User 1 lists sessions - should only see their own
    sessions1 = await client.get("/api/v1/sessions/", headers={"X-API-Key": api_key1})
    assert sessions1.status_code == 200
    data1 = sessions1.json()
    assert data1["total"] == 1
    assert data1["items"][0]["sessionId"] == "unique-session-1"

    # User 2 lists sessions - should only see their own
    sessions2 = await client.get("/api/v1/sessions/", headers={"X-API-Key": api_key2})
    assert sessions2.status_code == 200
    data2 = sessions2.json()
    assert data2["total"] == 1
    assert data2["items"][0]["sessionId"] == "unique-session-2"

    # User 1 cannot access User 2's session
    user2_session_id = data2["items"][0]["_id"]

    forbidden = await client.get(
        f"/api/v1/sessions/{user2_session_id}", headers={"X-API-Key": api_key1}
    )
    assert forbidden.status_code == 404  # Should not find it due to user_id filtering

    # User 2 cannot access User 1's session
    user1_session_id = data1["items"][0]["_id"]

    forbidden = await client.get(
        f"/api/v1/sessions/{user1_session_id}", headers={"X-API-Key": api_key2}
    )
    assert forbidden.status_code == 404  # Should not find it due to user_id filtering


@pytest.mark.asyncio
async def test_message_search_isolation(
    client: AsyncClient, test_db: AsyncIOMotorDatabase
):
    """Test that message search is properly isolated between users."""

    # Create two test users with API keys
    user_service = UserService(test_db)

    # Create user 1
    test_user1, _ = await user_service.create_user(
        UserCreate(
            email="searchuser1@example.com", username="searchuser1", role=UserRole.USER
        )
    )
    api_key1 = await user_service.create_api_key(str(test_user1.id), "Search Key 1")

    # Create user 2
    test_user2, _ = await user_service.create_user(
        UserCreate(
            email="searchuser2@example.com", username="searchuser2", role=UserRole.USER
        )
    )
    api_key2 = await user_service.create_api_key(str(test_user2.id), "Search Key 2")

    # User 1 uploads data with unique content
    response1 = await client.post(
        "/api/v1/ingest/batch",
        headers={"X-API-Key": api_key1},
        json={
            "messages": [
                {
                    "uuid": "search1-msg",
                    "sessionId": "search-session-1",
                    "type": "user",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "message": {"content": "unique content from user one"},
                    "cwd": "/search1/project",
                }
            ]
        },
    )
    assert response1.status_code == 200

    # User 2 uploads data with different unique content
    response2 = await client.post(
        "/api/v1/ingest/batch",
        headers={"X-API-Key": api_key2},
        json={
            "messages": [
                {
                    "uuid": "search2-msg",
                    "sessionId": "search-session-2",
                    "type": "user",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "message": {"content": "unique content from user two"},
                    "cwd": "/search2/project",
                }
            ]
        },
    )
    assert response2.status_code == 200

    # User 1 searches for "user one" - should find their message
    search1 = await client.get(
        "/api/v1/search/messages",
        headers={"X-API-Key": api_key1},
        params={"q": "user one"},
    )
    assert search1.status_code == 200
    data1 = search1.json()
    if "items" in data1:
        assert len(data1["items"]) == 1
        assert "user one" in data1["items"][0]["content"]

    # User 1 searches for "user two" - should NOT find user 2's message
    search1_cross = await client.get(
        "/api/v1/search/messages",
        headers={"X-API-Key": api_key1},
        params={"q": "user two"},
    )
    assert search1_cross.status_code == 200
    data1_cross = search1_cross.json()
    if "items" in data1_cross:
        assert len(data1_cross["items"]) == 0

    # User 2 searches for "user two" - should find their message
    search2 = await client.get(
        "/api/v1/search/messages",
        headers={"X-API-Key": api_key2},
        params={"q": "user two"},
    )
    assert search2.status_code == 200
    data2 = search2.json()
    if "items" in data2:
        assert len(data2["items"]) == 1
        assert "user two" in data2["items"][0]["content"]

    # User 2 searches for "user one" - should NOT find user 1's message
    search2_cross = await client.get(
        "/api/v1/search/messages",
        headers={"X-API-Key": api_key2},
        params={"q": "user one"},
    )
    assert search2_cross.status_code == 200
    data2_cross = search2_cross.json()
    if "items" in data2_cross:
        assert len(data2_cross["items"]) == 0
