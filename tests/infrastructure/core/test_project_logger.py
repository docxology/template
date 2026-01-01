"""Tests for ProjectLogger and standardized logging interface."""

import pytest
from infrastructure.core.logging_utils import ProjectLogger, get_project_logger, setup_project_logging


class TestProjectLogger:
    """Test the ProjectLogger class."""

    def test_project_logger_initialization(self):
        """Test ProjectLogger initialization."""
        log = ProjectLogger("test_logger")

        assert log._logger.name == "test_logger"
        assert hasattr(log, 'info')
        assert hasattr(log, 'debug')
        assert hasattr(log, 'success')

    def test_project_logger_methods(self):
        """Test ProjectLogger method calls don't raise exceptions."""
        log = ProjectLogger("test_logger")

        # These should not raise exceptions
        log.debug("Debug message")
        log.info("Info message")
        log.warning("Warning message")
        log.error("Error message")
        log.success("Success message")
        log.header("Header message")
        log.progress(50, 100, "Progress task")
        log.stage(1, 3, "Stage name")
        log.substep("Substep message")

    def test_project_logger_context_managers(self):
        """Test ProjectLogger context managers."""
        log = ProjectLogger("test_logger")

        # These should not raise exceptions
        with log.operation("Test operation"):
            pass

        with log.timing("Test timing"):
            pass

    def test_get_project_logger(self):
        """Test get_project_logger convenience function."""
        log = get_project_logger("test_module")

        assert isinstance(log, ProjectLogger)
        assert log.name == "test_module"

    def test_setup_project_logging(self, tmp_path):
        """Test setup_project_logging with file output."""
        log_file = tmp_path / "test.log"
        log = setup_project_logging("test_module", log_file=str(log_file))

        assert isinstance(log, ProjectLogger)
        assert log.name == "test_module"

        # Test that file logging works
        log.info("Test message")

        # File should exist and contain the message
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_project_logger_resource_usage(self):
        """Test resource usage logging."""
        log = ProjectLogger("test_logger")

        # This should not raise an exception (even if psutil not available)
        log.resource_usage("Test stage")