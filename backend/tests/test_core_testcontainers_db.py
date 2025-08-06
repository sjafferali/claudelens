"""Tests for testcontainers MongoDB integration."""

import os
from unittest.mock import Mock, mock_open, patch

from app.core.testcontainers_db import (
    get_testcontainer_mongodb_url,
    is_testcontainer_active,
    stop_testcontainer_mongodb,
)


class TestGetTestcontainerMongoDBURL:
    """Test testcontainer MongoDB URL generation."""

    def test_get_url_testcontainers_disabled(self):
        """Test when testcontainers is disabled."""
        with patch.dict(os.environ, {"USE_TEST_DB": "false"}, clear=False):
            result = get_testcontainer_mongodb_url()
            assert result is None

    def test_get_url_testcontainers_not_set(self):
        """Test when USE_TEST_DB is not set."""
        with patch.dict(os.environ, {}, clear=False):
            if "USE_TEST_DB" in os.environ:
                del os.environ["USE_TEST_DB"]
            result = get_testcontainer_mongodb_url()
            assert result is None

    def test_get_url_existing_env_url(self):
        """Test using existing testcontainer URL from environment."""
        test_url = "mongodb://test:test@localhost:27017/claudelens?authSource=admin"
        with patch.dict(
            os.environ,
            {"USE_TEST_DB": "true", "TESTCONTAINER_MONGODB_URL": test_url},
            clear=False,
        ):
            result = get_testcontainer_mongodb_url()
            assert result == test_url

    def test_get_url_existing_container(self):
        """Test using existing active container."""
        mock_container = Mock()
        mock_container.get_connection_url.return_value = (
            "mongodb://test:test@localhost:27017/test"
        )

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", mock_container),
        ):
            result = get_testcontainer_mongodb_url()
            expected = "mongodb://test:test@localhost:27017/claudelens?authSource=admin"
            assert result == expected

    @patch("testcontainers.mongodb.MongoDbContainer")
    @patch("app.core.testcontainers_db.atexit.register")
    def test_get_url_create_new_container(self, mock_atexit, mock_container_class):
        """Test creating new testcontainer."""
        mock_container = Mock()
        mock_container.get_connection_url.return_value = (
            "mongodb://test:test@localhost:27017"
        )
        mock_container_class.return_value = mock_container

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", None),
            patch("builtins.open", mock_open()),
        ):
            result = get_testcontainer_mongodb_url()

            expected = "mongodb://test:test@localhost:27017/claudelens?authSource=admin"
            assert result == expected

            # Check container was created and started
            mock_container_class.assert_called_once_with("mongo:7.0")
            mock_container.start.assert_called_once()

            # Check atexit was registered (when not in test env)
            # atexit.register can be called multiple times due to imports
            assert mock_atexit.called

    @patch("testcontainers.mongodb.MongoDbContainer")
    def test_get_url_create_container_in_test_env(self, mock_container_class):
        """Test creating container in test environment."""
        mock_container = Mock()
        mock_container.get_connection_url.return_value = (
            "mongodb://test:test@localhost:27017"
        )
        mock_container_class.return_value = mock_container

        with (
            patch.dict(
                os.environ, {"USE_TEST_DB": "true", "ENVIRONMENT": "test"}, clear=False
            ),
            patch("app.core.testcontainers_db._mongo_container", None),
            patch("builtins.open", mock_open()),
            patch("app.core.testcontainers_db.atexit.register") as mock_atexit,
        ):
            result = get_testcontainer_mongodb_url()

            assert result is not None
            # Should not register atexit in test environment
            mock_atexit.assert_not_called()

    @patch("testcontainers.mongodb.MongoDbContainer")
    def test_get_url_container_start_failure(self, mock_container_class):
        """Test handling container start failure."""
        mock_container_class.side_effect = Exception("Container start failed")

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", None),
        ):
            result = get_testcontainer_mongodb_url()
            assert result is None

    @patch("testcontainers.mongodb.MongoDbContainer")
    def test_get_url_file_write_failure(self, mock_container_class):
        """Test handling temp file write failure."""
        mock_container = Mock()
        mock_container.get_connection_url.return_value = (
            "mongodb://test:test@localhost:27017"
        )
        mock_container_class.return_value = mock_container

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", None),
            patch("builtins.open", side_effect=IOError("Write failed")),
        ):
            # Should still return URL even if file write fails
            result = get_testcontainer_mongodb_url()
            assert result is not None
            assert "claudelens" in result


class TestURLParsing:
    """Test URL parsing and transformation logic."""

    @patch("testcontainers.mongodb.MongoDbContainer")
    def test_url_parsing_simple_url(self, mock_container_class):
        """Test parsing simple MongoDB URL."""
        mock_container = Mock()
        mock_container.get_connection_url.return_value = (
            "mongodb://test:test@localhost:27017"
        )
        mock_container_class.return_value = mock_container

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", None),
            patch("builtins.open", mock_open()),
        ):
            result = get_testcontainer_mongodb_url()
            expected = "mongodb://test:test@localhost:27017/claudelens?authSource=admin"
            assert result == expected

    @patch("testcontainers.mongodb.MongoDbContainer")
    def test_url_parsing_with_existing_database(self, mock_container_class):
        """Test parsing URL that already has a database name."""
        mock_container = Mock()
        mock_container.get_connection_url.return_value = (
            "mongodb://test:test@localhost:27017/test"
        )
        mock_container_class.return_value = mock_container

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", None),
            patch("builtins.open", mock_open()),
        ):
            result = get_testcontainer_mongodb_url()
            expected = "mongodb://test:test@localhost:27017/claudelens?authSource=admin"
            assert result == expected

    @patch("testcontainers.mongodb.MongoDbContainer")
    def test_url_parsing_with_trailing_slash(self, mock_container_class):
        """Test parsing URL with trailing slash."""
        mock_container = Mock()
        mock_container.get_connection_url.return_value = (
            "mongodb://test:test@localhost:27017/"
        )
        mock_container_class.return_value = mock_container

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", None),
            patch("builtins.open", mock_open()),
        ):
            result = get_testcontainer_mongodb_url()
            expected = "mongodb://test:test@localhost:27017/claudelens?authSource=admin"
            assert result == expected

    @patch("testcontainers.mongodb.MongoDbContainer")
    def test_url_parsing_malformed_url(self, mock_container_class):
        """Test handling malformed MongoDB URL."""
        mock_container = Mock()
        mock_container.get_connection_url.return_value = "invalid-url"
        mock_container_class.return_value = mock_container

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", None),
            patch("builtins.open", mock_open()),
        ):
            result = get_testcontainer_mongodb_url()
            # Should still try to process it
            expected = "invalid-url/claudelens?authSource=admin"
            assert result == expected


class TestStopTestcontainerMongoDB:
    """Test stopping testcontainer MongoDB."""

    def test_stop_with_active_container(self):
        """Test stopping active container."""
        mock_container = Mock()

        with (
            patch("app.core.testcontainers_db._mongo_container", mock_container),
            patch("os.path.exists", return_value=True),
            patch("os.remove") as mock_remove,
        ):
            stop_testcontainer_mongodb()

            mock_container.stop.assert_called_once()
            mock_remove.assert_called_once()

    def test_stop_with_no_container(self):
        """Test stopping when no container is active."""
        with patch("app.core.testcontainers_db._mongo_container", None):
            # Should not raise exception
            stop_testcontainer_mongodb()

    def test_stop_with_container_stop_failure(self):
        """Test handling container stop failure."""
        mock_container = Mock()
        mock_container.stop.side_effect = Exception("Stop failed")

        with (
            patch("app.core.testcontainers_db._mongo_container", mock_container),
            patch("os.path.exists", return_value=False),
        ):
            # Should not raise exception
            stop_testcontainer_mongodb()

    def test_stop_with_file_cleanup_failure(self):
        """Test handling temp file cleanup failure."""
        mock_container = Mock()

        with (
            patch("app.core.testcontainers_db._mongo_container", mock_container),
            patch("os.path.exists", return_value=True),
            patch("os.remove", side_effect=OSError("Remove failed")),
        ):
            # Should not raise exception
            stop_testcontainer_mongodb()
            mock_container.stop.assert_called_once()

    def test_stop_with_logging_system_down(self):
        """Test stopping when logging system is already shut down."""
        mock_container = Mock()

        with (
            patch("app.core.testcontainers_db._mongo_container", mock_container),
            patch("os.path.exists", return_value=False),
            patch(
                "app.core.testcontainers_db.logger.info",
                side_effect=ValueError("Logging down"),
            ),
        ):
            # Should still stop container
            stop_testcontainer_mongodb()
            mock_container.stop.assert_called_once()


class TestIsTestcontainerActive:
    """Test checking if testcontainer is active."""

    def test_is_active_with_container(self):
        """Test checking when container is active."""
        mock_container = Mock()

        with patch("app.core.testcontainers_db._mongo_container", mock_container):
            assert is_testcontainer_active() is True

    def test_is_active_without_container(self):
        """Test checking when no container is active."""
        with patch("app.core.testcontainers_db._mongo_container", None):
            assert is_testcontainer_active() is False


class TestEnvironmentVariableHandling:
    """Test environment variable handling."""

    def test_use_test_db_case_insensitive(self):
        """Test USE_TEST_DB is case insensitive."""
        test_cases = ["TRUE", "True", "true"]

        for value in test_cases:
            with patch.dict(
                os.environ,
                {"USE_TEST_DB": value, "TESTCONTAINER_MONGODB_URL": "test-url"},
            ):
                result = get_testcontainer_mongodb_url()
                assert result == "test-url"

    def test_use_test_db_false_values(self):
        """Test USE_TEST_DB false values."""
        test_cases = ["false", "FALSE", "no", "0", ""]

        for value in test_cases:
            with patch.dict(os.environ, {"USE_TEST_DB": value}, clear=False):
                result = get_testcontainer_mongodb_url()
                assert result is None

    def test_environment_variable_priority(self):
        """Test that existing URL takes priority over container creation."""
        existing_url = "mongodb://existing:url@host:port/db"

        with (
            patch.dict(
                os.environ,
                {"USE_TEST_DB": "true", "TESTCONTAINER_MONGODB_URL": existing_url},
                clear=False,
            ),
            patch("testcontainers.mongodb.MongoDbContainer") as mock_container_class,
        ):
            result = get_testcontainer_mongodb_url()

            assert result == existing_url
            # Should not try to create new container
            mock_container_class.assert_not_called()


class TestTempFileHandling:
    """Test temporary file operations."""

    @patch("testcontainers.mongodb.MongoDbContainer")
    def test_temp_file_creation_success(self, mock_container_class):
        """Test successful temp file creation."""
        mock_container = Mock()
        mock_container.get_connection_url.return_value = (
            "mongodb://test:test@localhost:27017"
        )
        mock_container_class.return_value = mock_container

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", None),
            patch("builtins.open", mock_open()) as mock_file,
            patch("tempfile.gettempdir", return_value="/tmp"),
        ):
            result = get_testcontainer_mongodb_url()

            assert result is not None
            # Check file was written
            mock_file.assert_called_once()
            expected_path = "/tmp/claudelens_testcontainer_url.txt"
            assert mock_file.call_args[0][0] == expected_path

    @patch("testcontainers.mongodb.MongoDbContainer")
    def test_temp_file_creation_failure(self, mock_container_class):
        """Test handling temp file creation failure."""
        mock_container = Mock()
        mock_container.get_connection_url.return_value = (
            "mongodb://test:test@localhost:27017"
        )
        mock_container_class.return_value = mock_container

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", None),
            patch("builtins.open", side_effect=IOError("File write failed")),
        ):
            # Should still return URL even if file write fails
            result = get_testcontainer_mongodb_url()
            assert result is not None

    def test_temp_file_cleanup_success(self):
        """Test successful temp file cleanup."""
        mock_container = Mock()

        with (
            patch("app.core.testcontainers_db._mongo_container", mock_container),
            patch("os.path.exists", return_value=True),
            patch("os.remove") as mock_remove,
            patch("tempfile.gettempdir", return_value="/tmp"),
        ):
            stop_testcontainer_mongodb()

            expected_path = "/tmp/claudelens_testcontainer_url.txt"
            mock_remove.assert_called_once_with(expected_path)

    def test_temp_file_cleanup_file_not_exists(self):
        """Test temp file cleanup when file doesn't exist."""
        mock_container = Mock()

        with (
            patch("app.core.testcontainers_db._mongo_container", mock_container),
            patch("os.path.exists", return_value=False),
            patch("os.remove") as mock_remove,
        ):
            stop_testcontainer_mongodb()

            # Should not try to remove non-existent file
            mock_remove.assert_not_called()


class TestRegexURLParsing:
    """Test regex-based URL parsing logic."""

    @patch("testcontainers.mongodb.MongoDbContainer")
    def test_regex_url_matching_standard_format(self, mock_container_class):
        """Test regex matching for standard MongoDB URL format."""
        mock_container = Mock()
        mock_container.get_connection_url.return_value = (
            "mongodb://user:pass@host:27017"
        )
        mock_container_class.return_value = mock_container

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", None),
            patch("builtins.open", mock_open()),
        ):
            result = get_testcontainer_mongodb_url()
            expected = "mongodb://user:pass@host:27017/claudelens?authSource=admin"
            assert result == expected

    @patch("testcontainers.mongodb.MongoDbContainer")
    def test_regex_url_matching_with_database(self, mock_container_class):
        """Test regex matching when URL already has database."""
        mock_container = Mock()
        mock_container.get_connection_url.return_value = (
            "mongodb://user:pass@host:27017/existing_db"
        )
        mock_container_class.return_value = mock_container

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", None),
            patch("builtins.open", mock_open()),
        ):
            result = get_testcontainer_mongodb_url()
            expected = "mongodb://user:pass@host:27017/claudelens?authSource=admin"
            assert result == expected

    @patch("testcontainers.mongodb.MongoDbContainer")
    def test_regex_url_matching_with_params(self, mock_container_class):
        """Test regex matching with existing query parameters."""
        mock_container = Mock()
        mock_container.get_connection_url.return_value = (
            "mongodb://user:pass@host:27017/db?param=value"
        )
        mock_container_class.return_value = mock_container

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", None),
            patch("builtins.open", mock_open()),
        ):
            result = get_testcontainer_mongodb_url()
            expected = "mongodb://user:pass@host:27017/claudelens?authSource=admin"
            assert result == expected


class TestContainerLifecycle:
    """Test complete container lifecycle."""

    @patch("testcontainers.mongodb.MongoDbContainer")
    def test_complete_lifecycle(self, mock_container_class):
        """Test complete container start-stop lifecycle."""
        mock_container = Mock()
        mock_container.get_connection_url.return_value = (
            "mongodb://test:test@localhost:27017"
        )
        mock_container_class.return_value = mock_container

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", None),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=True),
            patch("os.remove") as mock_remove,
        ):
            # Start container
            url = get_testcontainer_mongodb_url()
            assert url is not None

            # Check container is active
            with patch("app.core.testcontainers_db._mongo_container", mock_container):
                assert is_testcontainer_active() is True

            # Stop container
            with patch("app.core.testcontainers_db._mongo_container", mock_container):
                stop_testcontainer_mongodb()

            mock_container.stop.assert_called_once()
            mock_remove.assert_called_once()

    def test_is_testcontainer_active_global_state(self):
        """Test that is_testcontainer_active reflects global state."""
        # Test with None
        with patch("app.core.testcontainers_db._mongo_container", None):
            assert is_testcontainer_active() is False

        # Test with mock container
        mock_container = Mock()
        with patch("app.core.testcontainers_db._mongo_container", mock_container):
            assert is_testcontainer_active() is True


class TestErrorScenarios:
    """Test various error scenarios."""

    @patch("testcontainers.mongodb.MongoDbContainer")
    def test_import_error_handling(self, mock_container_class):
        """Test handling when testcontainers import fails."""
        # Simulate import error
        mock_container_class.side_effect = ImportError("testcontainers not installed")

        with (
            patch.dict(os.environ, {"USE_TEST_DB": "true"}, clear=False),
            patch("app.core.testcontainers_db._mongo_container", None),
        ):
            result = get_testcontainer_mongodb_url()
            assert result is None

    def test_stop_with_logging_errors(self):
        """Test stop handling when logging throws errors."""
        mock_container = Mock()

        with (
            patch("app.core.testcontainers_db._mongo_container", mock_container),
            patch(
                "app.core.testcontainers_db.logger.info",
                side_effect=ValueError("Logging error"),
            ),
            patch("os.path.exists", return_value=False),
        ):
            # Should not raise exception
            stop_testcontainer_mongodb()
            mock_container.stop.assert_called_once()

    def test_stop_with_multiple_errors(self):
        """Test stop handling with multiple cascading errors."""
        mock_container = Mock()
        mock_container.stop.side_effect = Exception("Stop failed")

        with (
            patch("app.core.testcontainers_db._mongo_container", mock_container),
            patch(
                "app.core.testcontainers_db.logger.info",
                side_effect=OSError("Log failed"),
            ),
            patch(
                "app.core.testcontainers_db.logger.error",
                side_effect=ValueError("Error log failed"),
            ),
        ):
            # Should handle all errors gracefully
            stop_testcontainer_mongodb()
