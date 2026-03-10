"""Tests for infrastructure/core/errors.py.

Tests the InfraError dataclass and typed error constants.
No mocks — tests actual error formatting behavior.
"""

from __future__ import annotations

import pytest

from infrastructure.core.errors import (
    InfraError,
    PIPELINE_STAGE_FAILED,
    PIPELINE_STAGES_INCOMPLETE,
    PIPELINE_EXECUTION_FAILED,
    STAGE_FAILED,
    STAGE_EXCEPTION,
    SCRIPT_EXECUTION_FAILED,
    CLI_UNKNOWN_COMMAND,
    CLI_COMMAND_FAILED,
    CLI_UNKNOWN_EXECUTION_TYPE,
    NO_PROJECTS_FOUND,
    INVALID_PROJECTS,
    NO_PROJECTS_TO_EXECUTE,
    PROJECT_FAILED,
    PROJECT_EXCEPTION,
    PROJECTS_INCOMPLETE,
    MULTI_PROJECT_FAILED,
    INVENTORY_FAILED,
    SUMMARY_FAILED,
    DISCOVER_FAILED,
    CONFIG_IMPORT_FAILED,
    CONFIG_YAML_MISSING,
    PDF_NOT_FOUND,
)


class TestInfraError:
    """Test InfraError dataclass structure and format method."""

    def test_basic_creation(self):
        """Test creating a basic InfraError."""
        err = InfraError(code="TEST_ERR", message="Something failed")
        assert err.code == "TEST_ERR"
        assert err.message == "Something failed"
        assert err.suggestion == ""

    def test_creation_with_suggestion(self):
        """Test creating InfraError with suggestion."""
        err = InfraError(code="TEST_ERR", message="Failed", suggestion="Try again")
        assert err.suggestion == "Try again"

    def test_frozen_immutable(self):
        """Test that InfraError is immutable (frozen dataclass)."""
        err = InfraError(code="TEST", message="msg")
        with pytest.raises((AttributeError, TypeError)):
            err.code = "OTHER"  # type: ignore[misc]

    def test_format_no_placeholders(self):
        """Test format() with no placeholders."""
        err = InfraError(code="SIMPLE", message="No placeholders")
        result = err.format()
        assert "❌" in result
        assert "[SIMPLE]" in result
        assert "No placeholders" in result

    def test_format_with_suggestion(self):
        """Test format() includes suggestion with dash separator."""
        err = InfraError(code="ERR", message="Failed", suggestion="Fix it")
        result = err.format()
        assert " — " in result
        assert "Fix it" in result

    def test_format_with_placeholders(self):
        """Test format() substitutes context variables."""
        err = InfraError(
            code="STAGE_FAIL",
            message="Stage {stage_num} failed: {stage_name}",
            suggestion="Check {stage_name} logs",
        )
        result = err.format(stage_num=3, stage_name="PDF Rendering")
        assert "Stage 3 failed: PDF Rendering" in result
        assert "Check PDF Rendering logs" in result

    def test_format_missing_placeholder_raises(self):
        """Test format() raises KeyError for missing context."""
        err = InfraError(code="ERR", message="Stage {stage_num} failed")
        with pytest.raises(KeyError):
            err.format()  # Missing stage_num

    def test_format_output_structure(self):
        """Test format() output follows expected pattern."""
        err = InfraError(code="MY_CODE", message="Test message", suggestion="My suggestion")
        result = err.format()
        assert result.startswith("❌")
        assert "[MY_CODE]" in result
        assert "Test message" in result
        assert "My suggestion" in result


class TestPipelineErrors:
    """Test pipeline error constants."""

    def test_pipeline_stage_failed(self):
        """Test PIPELINE_STAGE_FAILED format."""
        result = PIPELINE_STAGE_FAILED.format(stage_num=2, stage_name="Run Analysis")
        assert "2" in result
        assert "Run Analysis" in result
        assert "PIPELINE_STAGE_FAILED" in result

    def test_pipeline_stages_incomplete(self):
        """Test PIPELINE_STAGES_INCOMPLETE format."""
        result = PIPELINE_STAGES_INCOMPLETE.format()
        assert "PIPELINE_STAGES_INCOMPLETE" in result
        assert "failed" in result.lower()

    def test_pipeline_execution_failed(self):
        """Test PIPELINE_EXECUTION_FAILED format."""
        result = PIPELINE_EXECUTION_FAILED.format(error="Timeout")
        assert "Timeout" in result

    def test_stage_failed(self):
        """Test STAGE_FAILED format."""
        result = STAGE_FAILED.format(stage_num=5)
        assert "5" in result

    def test_stage_exception(self):
        """Test STAGE_EXCEPTION format."""
        result = STAGE_EXCEPTION.format(stage_num=3, error="ValueError")
        assert "3" in result
        assert "ValueError" in result

    def test_script_execution_failed(self):
        """Test SCRIPT_EXECUTION_FAILED format."""
        result = SCRIPT_EXECUTION_FAILED.format(script_name="analysis.py", error="exit 1")
        assert "analysis.py" in result
        assert "exit 1" in result


class TestCliErrors:
    """Test CLI error constants."""

    def test_cli_unknown_command(self):
        """Test CLI_UNKNOWN_COMMAND format."""
        result = CLI_UNKNOWN_COMMAND.format(command="bogus")
        assert "bogus" in result
        assert "--help" in result

    def test_cli_command_failed(self):
        """Test CLI_COMMAND_FAILED format."""
        result = CLI_COMMAND_FAILED.format(error="permission denied")
        assert "permission denied" in result

    def test_cli_unknown_execution_type(self):
        """Test CLI_UNKNOWN_EXECUTION_TYPE format."""
        result = CLI_UNKNOWN_EXECUTION_TYPE.format(execution_type="weird")
        assert "weird" in result
        assert "full" in result


class TestProjectErrors:
    """Test project error constants."""

    def test_no_projects_found(self):
        """Test NO_PROJECTS_FOUND format."""
        result = NO_PROJECTS_FOUND.format()
        assert "NO_PROJECTS" in result

    def test_invalid_projects(self):
        """Test INVALID_PROJECTS format."""
        result = INVALID_PROJECTS.format(projects=["proj_a", "proj_b"])
        assert "proj_a" in result

    def test_project_failed(self):
        """Test PROJECT_FAILED format."""
        result = PROJECT_FAILED.format(project_name="my_project")
        assert "my_project" in result

    def test_project_exception(self):
        """Test PROJECT_EXCEPTION format."""
        result = PROJECT_EXCEPTION.format(project_name="proj", error="RuntimeError")
        assert "proj" in result
        assert "RuntimeError" in result

    def test_multi_project_failed(self):
        """Test MULTI_PROJECT_FAILED format."""
        result = MULTI_PROJECT_FAILED.format(error="disk full")
        assert "disk full" in result


class TestConfigErrors:
    """Test config error constants."""

    def test_config_import_failed(self):
        """Test CONFIG_IMPORT_FAILED format."""
        result = CONFIG_IMPORT_FAILED.format(error="ModuleNotFoundError")
        assert "ModuleNotFoundError" in result
        assert "config_loader" in result

    def test_config_yaml_missing(self):
        """Test CONFIG_YAML_MISSING format."""
        result = CONFIG_YAML_MISSING.format()
        assert "PyYAML" in result
        assert "pyyaml" in result

    def test_pdf_not_found(self):
        """Test PDF_NOT_FOUND format."""
        result = PDF_NOT_FOUND.format(path="/output/manuscript.pdf")
        assert "manuscript.pdf" in result


class TestErrorCodeUniqueness:
    """Test that all error codes are unique."""

    def test_all_codes_unique(self):
        """All error constants have unique codes."""
        errors = [
            PIPELINE_STAGE_FAILED,
            PIPELINE_STAGES_INCOMPLETE,
            PIPELINE_EXECUTION_FAILED,
            STAGE_FAILED,
            STAGE_EXCEPTION,
            SCRIPT_EXECUTION_FAILED,
            CLI_UNKNOWN_COMMAND,
            CLI_COMMAND_FAILED,
            CLI_UNKNOWN_EXECUTION_TYPE,
            NO_PROJECTS_FOUND,
            INVALID_PROJECTS,
            NO_PROJECTS_TO_EXECUTE,
            PROJECT_FAILED,
            PROJECT_EXCEPTION,
            PROJECTS_INCOMPLETE,
            MULTI_PROJECT_FAILED,
            INVENTORY_FAILED,
            SUMMARY_FAILED,
            DISCOVER_FAILED,
            CONFIG_IMPORT_FAILED,
            CONFIG_YAML_MISSING,
            PDF_NOT_FOUND,
        ]
        codes = [e.code for e in errors]
        assert len(codes) == len(set(codes)), "Duplicate error codes found"
