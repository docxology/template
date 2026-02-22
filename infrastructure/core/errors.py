"""Typed error constants for consistent error messaging.

This module defines a frozen InfraError dataclass and typed error constants
for all common error conditions in the infrastructure layer. Error messages
follow a standardized format: ❌ [CODE] message — suggestion.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InfraError:
    """Typed error constant with code, message, and actionable suggestion.

    Attributes:
        code: Short uppercase error code (e.g., "PIPELINE_STAGE_FAILED")
        message: Human-readable description, may contain {placeholders}
        suggestion: Actionable fix guidance, may contain {placeholders}

    Example:
        >>> err = PIPELINE_STAGE_FAILED
        >>> logger.error(err.format(stage_num=3, stage_name="PDF Rendering"))
        ❌ [PIPELINE_STAGE_FAILED] Pipeline failed at stage 3: PDF Rendering — Check stage logs for details
    """

    code: str
    message: str
    suggestion: str = ""

    def format(self, **context: Any) -> str:
        """Format error with context variables.

        Args:
            **context: Keyword arguments to substitute into message and suggestion

        Returns:
            Formatted error string: ❌ [CODE] message — suggestion
        """
        msg = f"❌ [{self.code}] {self.message.format(**context)}"
        if self.suggestion:
            msg += f" — {self.suggestion.format(**context)}"
        return msg


# =============================================================================
# PIPELINE ERRORS
# =============================================================================

PIPELINE_STAGE_FAILED = InfraError(
    code="PIPELINE_STAGE_FAILED",
    message="Pipeline failed at stage {stage_num}: {stage_name}",
    suggestion="Check stage logs for details",
)

PIPELINE_STAGES_INCOMPLETE = InfraError(
    code="PIPELINE_STAGES_INCOMPLETE",
    message="Some pipeline stages failed",
    suggestion="Review failed stages above and retry",
)

PIPELINE_EXECUTION_FAILED = InfraError(
    code="PIPELINE_EXEC_FAILED",
    message="Pipeline execution failed: {error}",
    suggestion="Check logs and retry",
)

STAGE_FAILED = InfraError(
    code="STAGE_FAILED",
    message="✗ Stage {stage_num} failed",
    suggestion="",
)

STAGE_EXCEPTION = InfraError(
    code="STAGE_EXCEPTION",
    message="✗ Stage {stage_num} failed with exception: {error}",
    suggestion="",
)

SCRIPT_EXECUTION_FAILED = InfraError(
    code="SCRIPT_EXEC_FAILED",
    message="Failed to run script {script_name}: {error}",
    suggestion="Verify script exists and has correct permissions",
)


# =============================================================================
# CLI ERRORS
# =============================================================================

CLI_UNKNOWN_COMMAND = InfraError(
    code="CLI_UNKNOWN_CMD",
    message="Unknown command: {command}",
    suggestion="Run with --help to see available commands",
)

CLI_COMMAND_FAILED = InfraError(
    code="CLI_CMD_FAILED",
    message="CLI command failed: {error}",
    suggestion="Check logs for details",
)

CLI_UNKNOWN_EXECUTION_TYPE = InfraError(
    code="CLI_UNKNOWN_EXEC_TYPE",
    message="Unknown execution type: {execution_type}",
    suggestion="Use one of: full, core, full-no-infra, core-no-infra",
)


# =============================================================================
# PROJECT ERRORS
# =============================================================================

NO_PROJECTS_FOUND = InfraError(
    code="NO_PROJECTS",
    message="No valid projects found",
    suggestion="Ensure projects/ directory contains valid project folders with config.yaml",
)

INVALID_PROJECTS = InfraError(
    code="INVALID_PROJECTS",
    message="Invalid projects: {projects}",
    suggestion="Check spelling and available project names",
)

NO_PROJECTS_TO_EXECUTE = InfraError(
    code="NO_PROJECTS_TO_EXEC",
    message="No projects to execute after filtering",
    suggestion="Check --projects argument values",
)

PROJECT_FAILED = InfraError(
    code="PROJECT_FAILED",
    message="Project '{project_name}' failed",
    suggestion="Check project logs for details",
)

PROJECT_EXCEPTION = InfraError(
    code="PROJECT_EXCEPTION",
    message="Project '{project_name}' failed with exception: {error}",
    suggestion="Check project logs and configuration",
)

PROJECTS_INCOMPLETE = InfraError(
    code="PROJECTS_INCOMPLETE",
    message="Some projects failed",
    suggestion="Review failed projects and retry",
)

MULTI_PROJECT_FAILED = InfraError(
    code="MULTI_PROJECT_FAILED",
    message="Multi-project execution failed: {error}",
    suggestion="Check logs for details",
)


# =============================================================================
# INVENTORY / SUMMARY ERRORS
# =============================================================================

INVENTORY_FAILED = InfraError(
    code="INVENTORY_FAILED",
    message="Failed to generate inventory: {error}",
    suggestion="Check output directory permissions",
)

SUMMARY_FAILED = InfraError(
    code="SUMMARY_FAILED",
    message="Failed to generate summary: {error}",
    suggestion="Check output directory and log file paths",
)

DISCOVER_FAILED = InfraError(
    code="DISCOVER_FAILED",
    message="Failed to discover projects: {error}",
    suggestion="Check repository root path",
)


# =============================================================================
# CONFIG ERRORS
# =============================================================================

CONFIG_IMPORT_FAILED = InfraError(
    code="CONFIG_IMPORT_FAILED",
    message="Failed to import from infrastructure/core/config_loader.py: {error}",
    suggestion="Falling back to environment variables only",
)

CONFIG_YAML_MISSING = InfraError(
    code="CONFIG_YAML_MISSING",
    message="PyYAML not installed",
    suggestion="Install with: pip install pyyaml",
)


# =============================================================================
# VALIDATION ERRORS
# =============================================================================

PDF_NOT_FOUND = InfraError(
    code="PDF_NOT_FOUND",
    message="PDF file not found: {path}",
    suggestion="Ensure PDF rendering stage completed successfully",
)
