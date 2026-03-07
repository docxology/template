"""Integrity verification tools for ensuring research output validity.

This module provides utilities for:
- Output file integrity checking
- Cross-reference validation
- Data consistency verification
- Build artifact validation
- Academic standard compliance

All functions follow the thin orchestrator pattern and maintain
100% test coverage requirements.
"""

from __future__ import annotations

import json
import os
import pickle  # noqa: S403 — used for pickle file validation
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, TypedDict

from infrastructure.core.file_operations import calculate_file_hash
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class IntegrityReport:
    """Container for integrity verification results."""

    file_integrity: dict[str, bool] = field(default_factory=dict)
    cross_reference_integrity: dict[str, bool] = field(default_factory=dict)
    data_consistency: dict[str, bool] = field(default_factory=dict)
    academic_standards: dict[str, bool] = field(default_factory=dict)
    overall_integrity: bool = True
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


def verify_file_integrity(
    file_paths: list[Path], expected_hashes: Optional[dict[str, str]] = None
) -> dict[str, bool]:
    """Verify file integrity using hash comparison."""
    integrity = {}

    for file_path in file_paths:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            integrity[str(file_path)] = False
            continue

        try:
            # Calculate actual hash
            actual_hash = calculate_file_hash(file_path)

            if expected_hashes and str(file_path) in expected_hashes:
                expected = expected_hashes[str(file_path)]
                integrity[str(file_path)] = actual_hash == expected
                if actual_hash != expected:
                    logger.warning(f"Hash mismatch for {file_path}")
            else:
                # Just verify file is readable and not corrupted
                integrity[str(file_path)] = actual_hash is not None

        except OSError as e:
            logger.error(f"Error verifying {file_path}: {e}")
            integrity[str(file_path)] = False

    passed = sum(1 for v in integrity.values() if v)
    logger.info(f"Integrity check complete: {passed}/{len(integrity)} files passed")
    return integrity


def verify_cross_references(markdown_files: list[Path]) -> dict[str, bool]:
    """Verify cross-reference integrity in markdown files."""
    integrity: dict[str, bool] = {
        "equations": True,
        "figures": True,
        "tables": True,
        "sections": True,
        "citations": True,
        "scan_errors": False,
    }

    # Collect all labels and references
    labels = set()
    references = set()
    scan_error_count = 0

    for md_file in markdown_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find all labels (both LaTeX and markdown style)
            latex_labels = re.findall(r"\\label\{([^}]+)\}", content)
            markdown_labels = re.findall(r"\{#([^}]+)\}", content)
            labels.update(latex_labels)
            labels.update(markdown_labels)

            # Find all references (both LaTeX and markdown style)
            ref_matches = re.findall(r"\\ref\{([^}]+)\}", content)
            eqref_matches = re.findall(r"\\eqref\{([^}]+)\}", content)
            references.update(ref_matches)
            references.update(eqref_matches)

        except OSError as e:
            logger.error(f"Error reading {md_file}: {e}")
            scan_error_count += 1

    if scan_error_count > 0:
        integrity["scan_errors"] = True

    # Check if all references have corresponding labels, broken down by type prefix
    missing_labels = references - labels

    if missing_labels:
        logger.warning(f"Missing labels for references: {missing_labels}")
        _prefix_to_key = {
            "eq:": "equations",
            "fig:": "figures",
            "tab:": "tables",
            "sec:": "sections",
            "cite:": "citations",
            "ref:": "citations",
        }
        for ref in missing_labels:
            matched = False
            for prefix, key in _prefix_to_key.items():
                if ref.startswith(prefix):
                    integrity[key] = False
                    matched = True
                    break
            if not matched:
                # Unknown prefix — mark all types as potentially broken
                for key in integrity:
                    integrity[key] = False
    else:
        logger.debug(f"Found {len(labels)} labels and {len(references)} references")

    return integrity


def verify_data_consistency(data_files: list[Path]) -> dict[str, bool]:
    """Verify data file consistency and integrity."""
    consistency = {
        "file_readable": True,
        "data_integrity": True,
        "metadata_consistent": True,
    }

    try:
        import numpy as np  # optional; only used for .npz/.npy validation
    except ImportError:
        np = None  # type: ignore[assignment]

    for data_file in data_files:
        if not data_file.exists():
            logger.warning(f"Data file not found: {data_file}")
            consistency["file_readable"] = False
            continue

        try:
            # Try to read as different data formats
            file_extension = data_file.suffix.lower()
            logger.debug(f"Checking {data_file} ({file_extension})")

            if file_extension == ".json":
                with open(data_file, "r") as f:
                    json.load(f)
            elif file_extension == ".csv":
                # Basic CSV validation
                with open(data_file, "r") as f:
                    lines = f.readlines()
                    if lines:
                        first_line = lines[0].strip()
                        if "," not in first_line and "\t" not in first_line:
                            consistency["data_integrity"] = False
            elif file_extension in [".npz", ".npy"]:
                # NumPy array validation
                if np is None:
                    continue
                data = np.load(data_file)
                if not hasattr(data, "shape"):
                    consistency["data_integrity"] = False
            elif file_extension == ".pkl":
                # Pickle validation
                with open(data_file, "rb") as f:
                    pickle.load(f)  # nosec B301 — validating project's own output files

        except (OSError, ValueError, pickle.UnpicklingError) as e:
            logger.warning(f"Data integrity check failed for {data_file}: {e}")
            consistency["data_integrity"] = False

    return consistency


def verify_academic_standards(markdown_files: list[Path]) -> dict[str, bool]:
    """Verify compliance with academic writing standards."""
    combined_content = ""
    for md_file in markdown_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                combined_content += f.read() + "\n"
        except OSError as e:
            logger.warning(f"Could not read markdown file {md_file}: {e}")

    content_lower = combined_content.lower()

    citation_patterns = [
        r"\\cite\{[^}]+\}",
        r"\\[a-z]*cite[a-z]*\{[^}]+\}",
        r"\[\d+\]",
        r"\(\d+\)",
    ]
    has_citations = any(re.search(pattern, combined_content) for pattern in citation_patterns)

    return {
        "has_abstract": bool(re.search(r"\\section\{.*abstract|#\s*abstract", content_lower)),
        "has_introduction": bool(
            re.search(r"\\section\{.*introduction|#\s*introduction", content_lower)
        ),
        "has_methodology": bool(
            re.search(
                r"\\section\{.*methodology|#\s*methodology|#\s*methods", content_lower
            )
        ),
        "has_results": bool(re.search(r"\\section\{.*results?|#\s*results?", content_lower)),
        "has_discussion": bool(
            re.search(r"\\section\{.*discussion|#\s*discussion", content_lower)
        ),
        "has_conclusion": bool(
            re.search(r"\\section\{.*conclusion|#\s*conclusion", content_lower)
        ),
        "has_references": bool(
            re.search(
                r"\\section\{.*references?|#\s*references?|\\bibliography", content_lower
            )
        ),
        "proper_citations": has_citations,
        "equation_labels": bool(re.findall(r"\\label\{eq:[^}]+\}", combined_content)),
        "figure_captions": bool(re.findall(r"\\caption\{[^}]+\}", combined_content)),
    }


def verify_output_integrity(
    output_dir: Path, manuscript_dir: Optional[Path] = None
) -> IntegrityReport:
    """Perform comprehensive integrity verification of all outputs."""
    report = IntegrityReport()

    if not output_dir.exists():
        report.issues.append(f"Output directory does not exist: {output_dir}")
        report.overall_integrity = False
        return report

    pdf_files = list(output_dir.rglob("*.pdf"))
    data_files = (
        list(output_dir.rglob("*.csv"))
        + list(output_dir.rglob("*.npz"))
        + list(output_dir.rglob("*.json"))
    )
    markdown_files = list(output_dir.rglob("*.md"))

    report.file_integrity = verify_file_integrity(pdf_files + data_files)
    if not all(report.file_integrity.values()):
        report.issues.append("Some output files failed integrity verification")
        report.overall_integrity = False

    report.cross_reference_integrity = verify_cross_references(markdown_files)
    if not all(report.cross_reference_integrity.values()):
        report.issues.append("Cross-reference integrity issues found")
        report.overall_integrity = False

    report.data_consistency = verify_data_consistency(data_files)
    if not all(report.data_consistency.values()):
        report.issues.append("Data consistency issues found")
        report.overall_integrity = False

    # Verify academic standards
    # Use manuscript directory if provided, otherwise use output markdown files
    academic_standards_files = markdown_files
    if manuscript_dir and manuscript_dir.exists():
        academic_standards_files = list(manuscript_dir.rglob("*.md"))
        # Exclude documentation files (AGENTS.md, README.md) from academic standards check
        academic_standards_files = [
            f for f in academic_standards_files if f.name not in ("AGENTS.md", "README.md")
        ]

    report.academic_standards = verify_academic_standards(academic_standards_files)

    # Check for any academic standards failures - only include standards that are actually False
    missing_standards = [k for k, v in report.academic_standards.items() if not v]
    if missing_standards:
        report.warnings.append(f"Missing academic standards: {', '.join(missing_standards)}")

    # Generate recommendations
    if not report.overall_integrity:
        report.recommendations.append("Fix integrity issues before proceeding")
        report.recommendations.append("Check file permissions and paths")
        report.recommendations.append("Verify all cross-references are properly defined")

    if report.warnings:
        report.recommendations.append("Consider addressing academic standard warnings")

    return report


def generate_integrity_report(report: IntegrityReport) -> str:
    """Generate a human-readable integrity report."""
    lines = []
    lines.append("=" * 60)
    lines.append("INTEGRITY VERIFICATION REPORT")
    lines.append("=" * 60)

    # Overall status
    status = "PASSED" if report.overall_integrity else "FAILED"
    lines.append(f"Overall Integrity: {status}")
    lines.append("")

    # File integrity
    lines.append("File Integrity:")
    for file_path, integrity in report.file_integrity.items():
        status = "OK" if integrity else "FAIL"
        lines.append(f"  [{status}] {file_path}")
    lines.append("")

    # Cross-reference integrity
    lines.append("Cross-Reference Integrity:")
    for ref_type, integrity in report.cross_reference_integrity.items():
        status = "OK" if integrity else "FAIL"
        lines.append(f"  [{status}] {ref_type}")
    lines.append("")

    # Data consistency
    lines.append("Data Consistency:")
    for check_type, integrity in report.data_consistency.items():
        status = "OK" if integrity else "FAIL"
        lines.append(f"  [{status}] {check_type}")
    lines.append("")

    # Academic standards
    lines.append("Academic Standards:")
    for standard, compliance in report.academic_standards.items():
        status = "OK" if compliance else "WARN"
        lines.append(f"  [{status}] {standard}")
    lines.append("")

    # Issues
    if report.issues:
        lines.append("Issues Found:")
        for issue in report.issues:
            lines.append(f"  - {issue}")
        lines.append("")

    # Warnings
    if report.warnings:
        lines.append("Warnings:")
        for warning in report.warnings:
            lines.append(f"  - {warning}")
        lines.append("")

    # Recommendations
    if report.recommendations:
        lines.append("Recommendations:")
        for rec in report.recommendations:
            lines.append(f"  - {rec}")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


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
    output_dir: Path, expected_files: Optional[dict[str, list[str]]] = None
) -> BuildArtifactValidation:
    """Validate that all expected build artifacts are present and correct."""
    validation: BuildArtifactValidation = {
        "expected_files": [],
        "missing_files": [],
        "unexpected_files": [],
        "validation_passed": True,
    }

    # Expected output structure (callers must supply expected_files for project-specific content)
    expected_structure: dict[str, list[str]] = expected_files if expected_files is not None else {}

    # Check for missing expected files and directories
    for category, files in expected_structure.items():
        category_dir = output_dir / category
        if not category_dir.exists():
            # Missing entire directory
            for expected_file in files:
                validation["missing_files"].append(expected_file)
                validation["validation_passed"] = False
        else:
            # Directory exists, check for missing files
            for expected_file in files:
                expected_path = category_dir / expected_file
                if not expected_path.exists():
                    validation["missing_files"].append(expected_file)
                    validation["validation_passed"] = False
                else:
                    validation["expected_files"].append(expected_file)

    # Check for unexpected files (basic check)
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
    """Check file permissions and accessibility."""
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
        # Test read access
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

    # Check PDF completeness
    pdf_dir = output_dir / "pdf"
    if not pdf_dir.exists():
        completeness["pdf_complete"] = False
        completeness["missing_outputs"].append("PDF directory")
    else:
        for pdf_path in pdf_dir.glob("*.pdf"):
            if pdf_path.stat().st_size == 0:
                completeness["pdf_complete"] = False
                completeness["incomplete_outputs"].append(f"Empty PDF: {pdf_path.name}")

    # Check figures completeness
    figures_dir = output_dir / "figures"
    if not figures_dir.exists():
        completeness["figures_complete"] = False
        completeness["missing_outputs"].append("Figures directory")
    else:
        figures = list(figures_dir.glob("*.png")) + list(figures_dir.glob("*.pdf"))
        for fig_path in figures:
            if fig_path.stat().st_size < 1000:
                completeness["incomplete_outputs"].append(f"Small figure: {fig_path.name}")

    # Check data completeness
    data_dir = output_dir / "data"
    if not data_dir.exists():
        completeness["data_complete"] = False
        completeness["missing_outputs"].append("Data directory")
    else:
        data_files_found = list(data_dir.iterdir())
        for data_path in data_files_found:
            if data_path.is_file() and data_path.stat().st_size == 0:
                completeness["data_complete"] = False
                completeness["incomplete_outputs"].append(f"Empty data: {data_path.name}")

    # Check LaTeX completeness
    tex_dir = output_dir / "tex"
    if not tex_dir.exists():
        completeness["latex_complete"] = False
        completeness["missing_outputs"].append("LaTeX directory")
    else:
        for tex_path in tex_dir.glob("*.tex"):
            if tex_path.stat().st_size == 0:
                completeness["latex_complete"] = False
                completeness["incomplete_outputs"].append(f"Empty LaTeX: {tex_path.name}")

    # Check HTML completeness (any HTML file in output root)
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


def create_integrity_manifest(output_dir: Path) -> dict[str, Any]:
    """Create an integrity manifest for all output files."""
    manifest: dict[str, Any] = {
        "timestamp": output_dir.stat().st_ctime if output_dir.exists() else None,
        "file_count": 0,
        "total_size": 0,
        "file_hashes": {},
        "directory_structure": {},
    }

    if not output_dir.exists():
        return manifest

    file_count = 0
    total_size = 0

    # Calculate file hashes and collect metadata
    for item in output_dir.rglob("*"):
        if item.is_file():
            rel_path = str(item.relative_to(output_dir))
            file_hash = calculate_file_hash(item)
            file_size = item.stat().st_size

            manifest["file_hashes"][rel_path] = {
                "hash": file_hash,
                "size": file_size,
                "modified": item.stat().st_mtime,
            }

            file_count += 1
            total_size += file_size

    manifest["file_count"] = file_count
    manifest["total_size"] = total_size

    # Create directory structure
    for dir_path in output_dir.rglob("*"):
        if dir_path.is_dir():
            rel_path = str(dir_path.relative_to(output_dir))
            manifest["directory_structure"][rel_path] = {
                "file_count": len(list(dir_path.glob("*"))),
                "total_size": sum(f.stat().st_size for f in dir_path.glob("*") if f.is_file()),
            }

    return manifest


def save_integrity_manifest(manifest: dict[str, Any], output_path: Path) -> None:
    """Save integrity manifest to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)


def load_integrity_manifest(manifest_path: Path) -> Optional[dict[str, Any]]:
    """Load integrity manifest from JSON file, or None on failure."""
    if not manifest_path.exists():
        return None

    try:
        with open(manifest_path, "r") as f:
            result: Optional[dict[str, Any]] = json.load(f)
            return result
    except (OSError, json.JSONDecodeError) as e:
        logger.debug(f"Could not load manifest from {manifest_path}: {e}")
        return None


def verify_integrity_against_manifest(
    current_manifest: dict[str, Any], saved_manifest: dict[str, Any]
) -> dict[str, Any]:
    """Verify current integrity against a saved manifest."""
    verification = {
        "file_count_changed": current_manifest["file_count"] != saved_manifest["file_count"],
        "total_size_changed": current_manifest["total_size"] != saved_manifest["total_size"],
        "files_changed": 0,
        "files_added": 0,
        "files_removed": 0,
        "details": {},
    }

    current_files = set(current_manifest["file_hashes"].keys())
    saved_files = set(saved_manifest["file_hashes"].keys())

    # Check for changed files
    for file_path in current_files & saved_files:
        current_hash = current_manifest["file_hashes"][file_path]["hash"]
        saved_hash = saved_manifest["file_hashes"][file_path]["hash"]

        if current_hash != saved_hash:
            verification["files_changed"] += 1
            verification["details"][file_path] = "modified"

    # Check for added files
    for file_path in current_files - saved_files:
        verification["files_added"] += 1
        verification["details"][file_path] = "added"

    # Check for removed files
    for file_path in saved_files - current_files:
        verification["files_removed"] += 1
        verification["details"][file_path] = "removed"

    return verification
