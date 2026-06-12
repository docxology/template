"""Build artifact and output completeness checks."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


class BuildArtifactValidation(TypedDict):
    """Typed result from validate_build_artifacts."""

    expected_files: list[str]
    missing_files: list[str]
    unexpected_files: list[str]
    validation_passed: bool


class PermissionCheck(TypedDict):
    """Typed result from check_file_permissions."""

    readable: bool
    writable: bool
    executable: bool
    issues: list[str]


class OutputCompleteness(TypedDict):
    """Typed result from verify_output_completeness."""

    pdf_complete: bool
    figures_complete: bool
    data_complete: bool
    latex_complete: bool
    html_complete: bool
    missing_outputs: list[str]
    incomplete_outputs: list[str]


def validate_build_artifacts(
    output_dir: Path, expected_files: dict[str, list[str]] | None = None
) -> BuildArtifactValidation:
    """Validate that all expected build artifacts are present and correct."""
    validation: BuildArtifactValidation = {
        "expected_files": [],
        "missing_files": [],
        "unexpected_files": [],
        "validation_passed": True,
    }

    expected_structure: dict[str, list[str]] = expected_files if expected_files is not None else {}

    for category, files in expected_structure.items():
        category_dir = output_dir / category
        if not category_dir.exists():
            for expected_file in files:
                validation["missing_files"].append(expected_file)
                validation["validation_passed"] = False
        else:
            for expected_file in files:
                expected_path = category_dir / expected_file
                if not expected_path.exists():
                    validation["missing_files"].append(expected_file)
                    validation["validation_passed"] = False
                else:
                    validation["expected_files"].append(expected_file)

    for item in output_dir.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(output_dir)
            is_expected = any(
                str(rel_path).startswith(cat) and any(f in str(rel_path) for f in files)
                for cat, files in expected_structure.items()
            )
            if not is_expected:
                validation["unexpected_files"].append(str(rel_path))

    return validation


def check_file_permissions(output_dir: Path) -> PermissionCheck:
    """Check directory permissions by probing with a temporary write-read-delete cycle."""
    permissions: PermissionCheck = {
        "readable": True,
        "writable": True,
        "executable": os.access(output_dir, os.X_OK) if output_dir.exists() else False,
        "issues": [],
    }

    if not output_dir.exists():
        permissions["readable"] = False
        permissions["issues"].append(f"Output directory does not exist: {output_dir}")
        return permissions

    try:
        test_file = output_dir / ".permission_test"
        test_file.write_text("test")
        test_file_content = test_file.read_text()
        test_file.unlink()

        if test_file_content != "test":
            permissions["readable"] = False
            permissions["writable"] = False
            permissions["issues"].append("File read/write test failed")

    except OSError as e:
        permissions["writable"] = False
        permissions["issues"].append(f"Permission test failed: {e}")

    return permissions


def verify_output_completeness(output_dir: Path) -> OutputCompleteness:
    """Verify that all expected outputs are present and complete."""
    completeness: OutputCompleteness = {
        "pdf_complete": True,
        "figures_complete": True,
        "data_complete": True,
        "latex_complete": True,
        "html_complete": True,
        "missing_outputs": [],
        "incomplete_outputs": [],
    }

    pdf_dir = output_dir / "pdf"
    if not pdf_dir.exists():
        completeness["pdf_complete"] = False
        completeness["missing_outputs"].append("PDF directory")
    else:
        for pdf_path in pdf_dir.glob("*.pdf"):
            if pdf_path.stat().st_size == 0:
                completeness["pdf_complete"] = False
                completeness["incomplete_outputs"].append(f"Empty PDF: {pdf_path.name}")

    figures_dir = output_dir / "figures"
    if not figures_dir.exists():
        completeness["figures_complete"] = False
        completeness["missing_outputs"].append("Figures directory")
    else:
        figures = list(figures_dir.glob("*.png")) + list(figures_dir.glob("*.pdf"))
        for fig_path in figures:
            if fig_path.stat().st_size < 1000:
                completeness["incomplete_outputs"].append(f"Small figure: {fig_path.name}")

    data_dir = output_dir / "data"
    if not data_dir.exists():
        completeness["data_complete"] = False
        completeness["missing_outputs"].append("Data directory")
    else:
        for data_path in data_dir.iterdir():
            if data_path.is_file() and data_path.stat().st_size == 0:
                completeness["data_complete"] = False
                completeness["incomplete_outputs"].append(f"Empty data: {data_path.name}")

    tex_dir = output_dir / "tex"
    if not tex_dir.exists():
        completeness["latex_complete"] = False
        completeness["missing_outputs"].append("LaTeX directory")
    else:
        for tex_path in tex_dir.glob("*.tex"):
            if tex_path.stat().st_size == 0:
                completeness["latex_complete"] = False
                completeness["incomplete_outputs"].append(f"Empty LaTeX: {tex_path.name}")

    html_files = list(output_dir.glob("*.html"))
    if not html_files:
        completeness["html_complete"] = False
        completeness["missing_outputs"].append("HTML output")
    else:
        for html_file in html_files:
            if html_file.stat().st_size == 0:
                completeness["html_complete"] = False
                completeness["incomplete_outputs"].append(f"Empty HTML: {html_file.name}")

    return completeness
