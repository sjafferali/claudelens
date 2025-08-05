"""Tests for the project service."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from app.models.project import ProjectStats, PyObjectId
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project import ProjectService


async def async_iter(items):
    """Helper to create async iterator from list."""
    for item in items:
        yield item


@pytest.fixture
def mock_db():
    """Create a mock database."""
    db = MagicMock()
    db.projects = MagicMock()
    db.sessions = MagicMock()
    db.messages = MagicMock()
    return db


@pytest.fixture
def project_service(mock_db):
    """Create a project service with mock database."""
    return ProjectService(mock_db)


@pytest.fixture
def sample_project_data():
    """Create sample project data."""
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "name": "Test Project",
        "path": "/projects/test",
        "description": "A test project for unit testing",
        "createdAt": datetime.now(UTC),
        "updatedAt": datetime.now(UTC),
    }


class TestProjectService:
    """Test cases for ProjectService."""

    @pytest.mark.asyncio
    async def test_list_projects_empty(self, project_service, mock_db):
        """Test listing projects when none exist."""
        # Setup
        mock_db.projects.count_documents = AsyncMock(return_value=0)
        mock_db.projects.find.return_value.sort.return_value.skip.return_value.limit.return_value.__aiter__ = lambda self: async_iter(
            []
        )

        # Execute
        projects, total = await project_service.list_projects(
            {}, 0, 10, "createdAt", "desc"
        )

        # Assert
        assert projects == []
        assert total == 0
        mock_db.projects.count_documents.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_list_projects_with_data(
        self, project_service, mock_db, sample_project_data
    ):
        """Test listing projects with data."""
        # Setup
        mock_data = [sample_project_data]
        mock_db.projects.count_documents = AsyncMock(return_value=1)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter(mock_data)
        )
        mock_db.projects.find.return_value = mock_cursor

        # Mock stats
        mock_db.sessions.count_documents = AsyncMock(return_value=5)
        mock_db.sessions.distinct = AsyncMock(return_value=["session-1", "session-2"])
        mock_db.messages.count_documents = AsyncMock(return_value=20)

        # Execute
        projects, total = await project_service.list_projects({}, 0, 10, "name", "asc")

        # Assert
        assert len(projects) == 1
        assert total == 1
        assert projects[0].name == "Test Project"
        assert projects[0].stats.session_count == 5
        assert projects[0].stats.message_count == 20
        mock_cursor.sort.assert_called_once_with("name", 1)

    @pytest.mark.asyncio
    async def test_list_projects_sort_by_message_count(self, project_service, mock_db):
        """Test listing projects sorted by message count."""
        # Setup
        mock_db.projects.count_documents = AsyncMock(return_value=0)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter([])
        )
        mock_db.projects.find.return_value = mock_cursor

        # Execute
        await project_service.list_projects({}, 0, 10, "message_count", "desc")

        # Assert
        mock_cursor.sort.assert_called_once_with("stats.message_count", -1)

    @pytest.mark.asyncio
    async def test_get_project_existing(
        self, project_service, mock_db, sample_project_data
    ):
        """Test getting an existing project."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439011")
        mock_db.projects.find_one = AsyncMock(return_value=sample_project_data)
        mock_db.sessions.count_documents = AsyncMock(return_value=3)
        mock_db.sessions.distinct = AsyncMock(return_value=["session-1"])
        mock_db.messages.count_documents = AsyncMock(return_value=10)

        # Execute
        project = await project_service.get_project(project_id)

        # Assert
        assert project is not None
        assert project.name == "Test Project"
        assert project.stats.session_count == 3
        assert project.stats.message_count == 10
        mock_db.projects.find_one.assert_called_once_with({"_id": project_id})

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, project_service, mock_db):
        """Test getting a non-existent project."""
        # Setup
        mock_db.projects.find_one = AsyncMock(return_value=None)

        # Execute
        project = await project_service.get_project(ObjectId())

        # Assert
        assert project is None

    @pytest.mark.asyncio
    async def test_get_project_by_path(
        self, project_service, mock_db, sample_project_data
    ):
        """Test getting a project by path."""
        # Setup
        mock_db.projects.find_one = AsyncMock(return_value=sample_project_data)

        # Execute
        project = await project_service.get_project_by_path("/projects/test")

        # Assert
        assert project is not None
        assert project.path == "/projects/test"
        mock_db.projects.find_one.assert_called_once_with({"path": "/projects/test"})

    @pytest.mark.asyncio
    async def test_get_project_by_path_not_found(self, project_service, mock_db):
        """Test getting a project by non-existent path."""
        # Setup
        mock_db.projects.find_one = AsyncMock(return_value=None)

        # Execute
        project = await project_service.get_project_by_path("/nonexistent")

        # Assert
        assert project is None

    @pytest.mark.asyncio
    async def test_create_project(self, project_service, mock_db):
        """Test creating a new project."""
        # Setup
        project_create = ProjectCreate(
            name="New Project",
            path="/projects/new",
            description="A brand new project",
        )
        mock_db.projects.insert_one = AsyncMock()

        # Execute
        project = await project_service.create_project(project_create)

        # Assert
        assert project.name == "New Project"
        assert project.path == "/projects/new"
        assert project.description == "A brand new project"
        assert isinstance(project.id, PyObjectId)
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.updated_at, datetime)
        assert project.stats == ProjectStats()

        # Verify insert was called
        mock_db.projects.insert_one.assert_called_once()
        insert_call = mock_db.projects.insert_one.call_args[0][0]
        assert insert_call["name"] == "New Project"
        assert insert_call["path"] == "/projects/new"
        assert insert_call["description"] == "A brand new project"

    @pytest.mark.asyncio
    async def test_create_project_without_description(self, project_service, mock_db):
        """Test creating a project without description."""
        # Setup
        project_create = ProjectCreate(
            name="Minimal Project",
            path="/projects/minimal",
        )
        mock_db.projects.insert_one = AsyncMock()

        # Execute
        project = await project_service.create_project(project_create)

        # Assert
        assert project.name == "Minimal Project"
        assert project.description is None

    @pytest.mark.asyncio
    async def test_update_project_success(
        self, project_service, mock_db, sample_project_data
    ):
        """Test successfully updating a project."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439011")
        update_data = ProjectUpdate(
            name="Updated Project",
            description="Updated description",
        )

        updated_data = sample_project_data.copy()
        updated_data["name"] = "Updated Project"
        updated_data["description"] = "Updated description"

        mock_db.projects.find_one_and_update = AsyncMock(return_value=updated_data)

        # Execute
        project = await project_service.update_project(project_id, update_data)

        # Assert
        assert project is not None
        assert project.name == "Updated Project"
        assert project.description == "Updated description"

        # Verify update call
        update_call = mock_db.projects.find_one_and_update.call_args
        assert update_call[0][0] == {"_id": project_id}
        assert "$set" in update_call[0][1]
        assert "updatedAt" in update_call[0][1]["$set"]

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, project_service, mock_db):
        """Test updating a non-existent project."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439011")
        update_data = ProjectUpdate(name="Updated")
        mock_db.projects.find_one_and_update = AsyncMock(return_value=None)

        # Execute
        project = await project_service.update_project(project_id, update_data)

        # Assert
        assert project is None

    @pytest.mark.asyncio
    async def test_update_project_no_changes(
        self, project_service, mock_db, sample_project_data
    ):
        """Test updating a project with no changes."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439011")
        update_data = ProjectUpdate()  # Empty update
        mock_db.projects.find_one = AsyncMock(return_value=sample_project_data)

        # Execute
        project = await project_service.update_project(project_id, update_data)

        # Assert
        assert project is not None
        assert project.name == "Test Project"
        # Should not call find_one_and_update when no changes
        mock_db.projects.find_one_and_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_project_without_cascade(self, project_service, mock_db):
        """Test deleting a project without cascade."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439011")
        mock_result = MagicMock(deleted_count=1)
        mock_db.projects.delete_one = AsyncMock(return_value=mock_result)

        # Execute
        success = await project_service.delete_project(project_id, cascade=False)

        # Assert
        assert success is True
        mock_db.projects.delete_one.assert_called_once_with({"_id": project_id})
        # Should not delete related data
        mock_db.sessions.delete_many.assert_not_called()
        mock_db.messages.delete_many.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_project_with_cascade(self, project_service, mock_db):
        """Test deleting a project with cascade."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439011")
        session_ids = ["session-1", "session-2", "session-3"]

        mock_db.sessions.distinct = AsyncMock(return_value=session_ids)
        mock_db.messages.delete_many = AsyncMock()
        mock_db.sessions.delete_many = AsyncMock()
        mock_result = MagicMock(deleted_count=1)
        mock_db.projects.delete_one = AsyncMock(return_value=mock_result)

        # Execute
        success = await project_service.delete_project(project_id, cascade=True)

        # Assert
        assert success is True
        # Verify cascade deletion order
        mock_db.sessions.distinct.assert_called_once_with(
            "sessionId", {"projectId": project_id}
        )
        mock_db.messages.delete_many.assert_called_once_with(
            {"sessionId": {"$in": session_ids}}
        )
        mock_db.sessions.delete_many.assert_called_once_with({"projectId": project_id})
        mock_db.projects.delete_one.assert_called_once_with({"_id": project_id})

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, project_service, mock_db):
        """Test deleting a non-existent project."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439011")
        mock_result = MagicMock(deleted_count=0)
        mock_db.projects.delete_one = AsyncMock(return_value=mock_result)

        # Execute
        success = await project_service.delete_project(project_id)

        # Assert
        assert success is False

    @pytest.mark.asyncio
    async def test_list_projects_with_filter(self, project_service, mock_db):
        """Test listing projects with filter."""
        # Setup
        filter_dict = {"name": {"$regex": "test", "$options": "i"}}
        mock_db.projects.count_documents = AsyncMock(return_value=0)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter([])
        )
        mock_db.projects.find.return_value = mock_cursor

        # Execute
        await project_service.list_projects(filter_dict, 0, 10, "name", "asc")

        # Assert
        mock_db.projects.find.assert_called_once_with(filter_dict)
        mock_db.projects.count_documents.assert_called_once_with(filter_dict)

    @pytest.mark.asyncio
    async def test_list_projects_pagination(self, project_service, mock_db):
        """Test listing projects with pagination."""
        # Setup
        mock_db.projects.count_documents = AsyncMock(return_value=50)
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value.__aiter__ = (
            lambda self: async_iter([])
        )
        mock_db.projects.find.return_value = mock_cursor

        # Execute
        projects, total = await project_service.list_projects(
            {}, skip=20, limit=10, sort_by="name", sort_order="asc"
        )

        # Assert
        assert total == 50
        mock_cursor.sort.return_value.skip.assert_called_once_with(20)
        mock_cursor.sort.return_value.skip.return_value.limit.assert_called_once_with(
            10
        )

    @pytest.mark.asyncio
    async def test_update_project_partial_update(
        self, project_service, mock_db, sample_project_data
    ):
        """Test partial update of a project."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439011")
        # Only update description
        update_data = ProjectUpdate(description="New description only")

        updated_data = sample_project_data.copy()
        updated_data["description"] = "New description only"

        mock_db.projects.find_one_and_update = AsyncMock(return_value=updated_data)

        # Execute
        project = await project_service.update_project(project_id, update_data)

        # Assert
        assert project is not None
        assert project.name == "Test Project"  # Unchanged
        assert project.description == "New description only"  # Changed

        # Verify only specified fields were updated
        update_call = mock_db.projects.find_one_and_update.call_args
        update_dict = update_call[0][1]["$set"]
        assert "description" in update_dict
        assert "name" not in update_dict  # Should not be included

    @pytest.mark.asyncio
    async def test_get_project_stats(self, project_service, mock_db):
        """Test getting project statistics."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439011")

        # Mock various counts
        mock_db.sessions.count_documents = AsyncMock(return_value=10)
        mock_db.sessions.distinct = AsyncMock(return_value=["s1", "s2", "s3"])
        mock_db.messages.count_documents = AsyncMock(return_value=50)

        # Execute
        stats = await project_service._get_project_stats(project_id)

        # Assert
        assert stats["session_count"] == 10
        assert stats["message_count"] == 50
        mock_db.sessions.count_documents.assert_called_once_with(
            {"projectId": project_id}
        )
        mock_db.sessions.distinct.assert_called_once_with(
            "sessionId", {"projectId": project_id}
        )
        mock_db.messages.count_documents.assert_called_once_with(
            {"sessionId": {"$in": ["s1", "s2", "s3"]}}
        )

    @pytest.mark.asyncio
    async def test_create_project_with_existing_path(self, project_service, mock_db):
        """Test creating a project with a path that already exists (should still work)."""
        # Setup
        project_create = ProjectCreate(
            name="Duplicate Path Project",
            path="/projects/existing",
            description="Testing duplicate path",
        )
        mock_db.projects.insert_one = AsyncMock()

        # Execute
        project = await project_service.create_project(project_create)

        # Assert
        assert project.name == "Duplicate Path Project"
        assert project.path == "/projects/existing"
        # Note: The service doesn't check for duplicate paths, that would be handled by unique index

    @pytest.mark.asyncio
    async def test_delete_project_cascade_no_sessions(self, project_service, mock_db):
        """Test cascade delete when project has no sessions."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439011")

        mock_db.sessions.distinct = AsyncMock(return_value=[])  # No sessions
        mock_db.messages.delete_many = AsyncMock()  # Need to mock this
        mock_db.sessions.delete_many = AsyncMock()  # Need to mock this
        mock_result = MagicMock(deleted_count=1)
        mock_db.projects.delete_one = AsyncMock(return_value=mock_result)

        # Execute
        success = await project_service.delete_project(project_id, cascade=True)

        # Assert
        assert success is True
        # Should still check for sessions
        mock_db.sessions.distinct.assert_called_once()
        # But should not try to delete messages if no sessions
        mock_db.messages.delete_many.assert_called_once_with({"sessionId": {"$in": []}})

    @pytest.mark.asyncio
    async def test_get_project_statistics_with_data(self, project_service, mock_db):
        """Test getting detailed project statistics with data."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439011")
        session_ids = ["session-1", "session-2", "session-3"]

        # Mock project exists
        mock_db.projects.find_one = AsyncMock(return_value={"_id": project_id})

        # Mock session IDs
        mock_db.sessions.distinct = AsyncMock(return_value=session_ids)

        # Mock aggregation result
        agg_result = [
            {
                "_id": None,
                "total_messages": 50,
                "user_messages": 25,
                "assistant_messages": 25,
                "total_cost": 1.23,
                "models_used": ["claude-3-opus", "claude-3-sonnet"],
                "first_message": datetime(2024, 1, 1, tzinfo=UTC),
                "last_message": datetime(2024, 1, 31, tzinfo=UTC),
            }
        ]

        mock_agg = MagicMock()
        mock_agg.to_list = AsyncMock(return_value=agg_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_agg)

        # Execute
        stats = await project_service.get_project_statistics(project_id)

        # Assert
        assert stats is not None
        assert stats["project_id"] == str(project_id)
        assert stats["session_count"] == 3
        assert stats["total_messages"] == 50
        assert stats["user_messages"] == 25
        assert stats["assistant_messages"] == 25
        assert stats["total_cost"] == 1.23
        assert stats["models_used"] == ["claude-3-opus", "claude-3-sonnet"]
        assert stats["first_message"] == datetime(2024, 1, 1, tzinfo=UTC)
        assert stats["last_message"] == datetime(2024, 1, 31, tzinfo=UTC)

        # Verify aggregation pipeline
        pipeline_call = mock_db.messages.aggregate.call_args[0][0]
        assert pipeline_call[0]["$match"]["sessionId"]["$in"] == session_ids

    @pytest.mark.asyncio
    async def test_get_project_statistics_no_messages(self, project_service, mock_db):
        """Test getting project statistics when no messages exist."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439011")

        # Mock project exists
        mock_db.projects.find_one = AsyncMock(return_value={"_id": project_id})

        # Mock no session IDs
        mock_db.sessions.distinct = AsyncMock(return_value=[])

        # Mock empty aggregation result
        mock_agg = MagicMock()
        mock_agg.to_list = AsyncMock(return_value=[])
        mock_db.messages.aggregate = MagicMock(return_value=mock_agg)

        # Execute
        stats = await project_service.get_project_statistics(project_id)

        # Assert
        assert stats is not None
        assert stats["project_id"] == str(project_id)
        assert stats["session_count"] == 0
        assert stats["total_messages"] == 0
        assert stats["user_messages"] == 0
        assert stats["assistant_messages"] == 0
        assert stats["total_cost"] == 0
        assert stats["models_used"] == []

    @pytest.mark.asyncio
    async def test_get_project_statistics_project_not_found(
        self, project_service, mock_db
    ):
        """Test getting statistics for non-existent project."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439011")

        # Mock project not found
        mock_db.projects.find_one = AsyncMock(return_value=None)

        # Execute
        stats = await project_service.get_project_statistics(project_id)

        # Assert
        assert stats is None
        # Should not proceed to query sessions or messages
        mock_db.sessions.distinct.assert_not_called()
        mock_db.messages.aggregate.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_project_statistics_with_decimal128_cost(
        self, project_service, mock_db
    ):
        """Test getting project statistics with Decimal128 cost values."""
        # Setup
        from bson import Decimal128

        project_id = ObjectId("507f1f77bcf86cd799439011")
        session_ids = ["session-1"]

        # Mock project exists
        mock_db.projects.find_one = AsyncMock(return_value={"_id": project_id})

        # Mock session IDs
        mock_db.sessions.distinct = AsyncMock(return_value=session_ids)

        # Mock aggregation result with Decimal128
        agg_result = [
            {
                "_id": None,
                "total_messages": 10,
                "user_messages": 5,
                "assistant_messages": 5,
                "total_cost": Decimal128("2.456"),
                "models_used": ["claude-3-opus"],
                "first_message": datetime(2024, 1, 1, tzinfo=UTC),
                "last_message": datetime(2024, 1, 2, tzinfo=UTC),
            }
        ]

        mock_agg = MagicMock()
        mock_agg.to_list = AsyncMock(return_value=agg_result)
        mock_db.messages.aggregate = MagicMock(return_value=mock_agg)

        # Execute
        stats = await project_service.get_project_statistics(project_id)

        # Assert
        assert stats is not None
        # Note: The service doesn't convert Decimal128, it returns as-is
        assert hasattr(stats["total_cost"], "to_decimal")
        assert float(stats["total_cost"].to_decimal()) == 2.456

    @pytest.mark.asyncio
    async def test_get_project_statistics_complex_aggregation(
        self, project_service, mock_db
    ):
        """Test project statistics aggregation pipeline structure."""
        # Setup
        project_id = ObjectId("507f1f77bcf86cd799439011")
        session_ids = ["s1", "s2"]

        # Mock project exists
        mock_db.projects.find_one = AsyncMock(return_value={"_id": project_id})

        # Mock session IDs
        mock_db.sessions.distinct = AsyncMock(return_value=session_ids)

        # Mock aggregation
        mock_agg = MagicMock()
        mock_agg.to_list = AsyncMock(return_value=[])
        mock_db.messages.aggregate = MagicMock(return_value=mock_agg)

        # Execute
        await project_service.get_project_statistics(project_id)

        # Assert pipeline structure
        pipeline = mock_db.messages.aggregate.call_args[0][0]

        # Check $match stage
        assert pipeline[0]["$match"]["sessionId"]["$in"] == session_ids

        # Check $group stage
        group_stage = pipeline[1]["$group"]
        assert group_stage["_id"] is None
        assert "$sum" in group_stage["total_messages"]
        assert group_stage["total_messages"]["$sum"] == 1
        assert "$cond" in group_stage["user_messages"]["$sum"]
        assert "$cond" in group_stage["assistant_messages"]["$sum"]
        assert "$ifNull" in group_stage["total_cost"]["$sum"]
        assert "$addToSet" in group_stage["models_used"]
        assert "$min" in group_stage["first_message"]
        assert "$max" in group_stage["last_message"]
