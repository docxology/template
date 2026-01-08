"""Validation utilities - thin wrapper around infrastructure validation."""

from pathlib import Path
from typing import Any, Dict, List, Optional

# Lazy imports to avoid import issues during test collection
def _get_infra_validate_markdown():
    # Ensure infrastructure is available
    _ensure_infrastructure_path()
    from infrastructure.validation.markdown_validator import validate_markdown
    return validate_markdown

def _get_infra_verify_output_integrity():
    # Ensure infrastructure is available
    _ensure_infrastructure_path()
    from infrastructure.validation.integrity import verify_output_integrity
    return verify_output_integrity

def _get_infra_validate_pdf_rendering():
    # Ensure infrastructure is available
    _ensure_infrastructure_path()
    from infrastructure.validation.pdf_validator import validate_pdf_rendering
    return validate_pdf_rendering

def _get_infra_validate_figure_registry():
    # Ensure infrastructure is available
    _ensure_infrastructure_path()
    from infrastructure.validation.figure_validator import validate_figure_registry
    return validate_figure_registry

def _ensure_infrastructure_path():
    """Ensure the infrastructure module is available in sys.path."""
    import sys
    import os

    # Check if infrastructure is already available
    try:
        import infrastructure
        return
    except ImportError:
        pass

    # Find repo root (parent of projects/)
    current_path = Path(__file__).resolve()
    # Go up: src/utils/validation.py -> src/utils/ -> src/ -> project/ -> projects/ -> repo_root/
    repo_root = current_path.parent.parent.parent.parent.parent

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def validate_markdown(markdown_path: str, strict: bool = False) -> Dict[str, Any]:
    """Validate markdown files using infrastructure validation.

    Args:
        markdown_path: Path to markdown files
        strict: Whether to use strict validation

    Returns:
        Validation results
    """
    try:
        # Infrastructure function requires both markdown_dir and repo_root
        repo_root = Path(".").resolve()  # Current directory as repo root
        infra_validate_markdown = _get_infra_validate_markdown()
        problems, exit_code = infra_validate_markdown(Path(markdown_path), repo_root, strict=strict)
        return {
            "status": "validated" if exit_code == 0 else "issues_found",
            "issues": problems,
            "summary": {
                "total_issues": len(problems),
                "exit_code": exit_code
            },
            "path": markdown_path
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "path": markdown_path
        }


def validate_figure_registry(registry_path: Path, manuscript_dir: Path) -> Dict[str, Any]:
    """Validate figure registry using infrastructure validation.

    Args:
        registry_path: Path to figure registry JSON file
        manuscript_dir: Path to manuscript directory containing markdown files

    Returns:
        Validation results dictionary with status, issues, and summary
    """
    try:
        infra_validate_figure_registry = _get_infra_validate_figure_registry()
        success, issues = infra_validate_figure_registry(registry_path, manuscript_dir)
        return {
            "status": "validated" if success else "issues_found",
            "success": success,
            "issues": issues,
            "summary": {
                "total_issues": len(issues),
                "validated": success
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "success": False,
            "issues": []
        }


def verify_output_integrity(output_path: Path) -> Dict[str, Any]:
    """Verify output integrity using infrastructure validation.

    Args:
        output_path: Path to output directory

    Returns:
        Integrity report
    """
    try:
        infra_verify_output_integrity = _get_infra_verify_output_integrity()
        results = infra_verify_output_integrity(output_path)
        return {
            "status": "validated" if results["status"] == "passed" else "issues_found",
            "issues": results.get("issues", []),
            "summary": results.get("summary", ""),
            "path": str(output_path)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "path": str(output_path)
        }


def validate_pdf_rendering(pdf_path: str) -> Dict[str, Any]:
    """Validate PDF rendering using infrastructure validation.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Validation results
    """
    try:
        infra_validate_pdf_rendering = _get_infra_validate_pdf_rendering()
        results = infra_validate_pdf_rendering(pdf_path)
        return {
            "status": "validated" if not results.get("issues") else "issues_found",
            "issues": results.get("issues", []),
            "warnings": results.get("warnings", []),
            "path": pdf_path
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "path": pdf_path
        }


class IntegrityReport:
    """Compatibility wrapper for infrastructure integrity reports."""

    def __init__(self, results: Optional[Dict[str, Any]] = None):
        if results:
            self.summary = results.get("summary", "")
            self.issues = results.get("issues", [])
            self.status = results.get("status", "unknown")
        else:
            self.summary = "No validation performed"
            self.issues = []
            self.status = "not_validated"

    def __str__(self):
        return f"IntegrityReport(status='{self.status}', issues={len(self.issues)})"