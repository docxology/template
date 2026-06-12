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

import json
import pickle  # noqa: S403 — used for pickle file validation
import re
from dataclasses import dataclass, field
from pathlib import Path

from infrastructure.core._optional_deps import np
from infrastructure.core.files.operations import calculate_file_hash
from infrastructure.core.logging.constants import BANNER_WIDTH
from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.integrity.completeness import (  # noqa: F401
    BuildArtifactValidation,
    OutputCompleteness,
    PermissionCheck,
    check_file_permissions,
    validate_build_artifacts,
    verify_output_completeness,
)
from infrastructure.validation.integrity.manifest import (  # noqa: F401
    create_integrity_manifest,
    load_integrity_manifest,
    save_integrity_manifest,
    verify_integrity_against_manifest,
)

logger = get_logger(__name__)

_REPORT_SEPARATOR = "=" * BANNER_WIDTH


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


def verify_file_integrity(file_paths: list[Path], expected_hashes: dict[str, str] | None = None) -> dict[str, bool]:
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
    from infrastructure.validation.content.symbols import resolve_cross_reference_integrity

    return resolve_cross_reference_integrity(markdown_files)


def verify_data_consistency(data_files: list[Path]) -> dict[str, bool]:
    """Verify data file consistency and integrity."""
    consistency = {
        "file_readable": True,
        "data_integrity": True,
        "metadata_consistent": True,
    }

    for data_file in data_files:
        if not data_file.exists():
            logger.warning(f"Data file not found: {data_file}")
            consistency["file_readable"] &= False
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
                    # Validate this project's own output files.
                    pickle.load(f)  # nosec B301

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
            continue

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
        "has_introduction": bool(re.search(r"\\section\{.*introduction|#\s*introduction", content_lower)),
        "has_methodology": bool(re.search(r"\\section\{.*methodology|#\s*methodology|#\s*methods", content_lower)),
        "has_results": bool(re.search(r"\\section\{.*results?|#\s*results?", content_lower)),
        "has_discussion": bool(re.search(r"\\section\{.*discussion|#\s*discussion", content_lower)),
        "has_conclusion": bool(re.search(r"\\section\{.*conclusion|#\s*conclusion", content_lower)),
        "has_references": bool(re.search(r"\\section\{.*references?|#\s*references?|\\bibliography", content_lower)),
        "proper_citations": has_citations,
        "equation_labels": bool(re.findall(r"\\label\{eq:[^}]+\}", combined_content)),
        "figure_captions": bool(re.findall(r"\\caption\{[^}]+\}", combined_content)),
    }


def verify_output_integrity(output_dir: Path, manuscript_dir: Path | None = None) -> IntegrityReport:
    """Perform comprehensive integrity verification of all outputs."""
    report = IntegrityReport()

    if not output_dir.exists():
        report.issues.append(f"Output directory does not exist: {output_dir}")
        report.overall_integrity = False
        return report

    pdf_files = list(output_dir.rglob("*.pdf"))
    data_files = list(output_dir.rglob("*.csv")) + list(output_dir.rglob("*.npz")) + list(output_dir.rglob("*.json"))
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
        academic_standards_files = [f for f in academic_standards_files if f.name not in ("AGENTS.md", "README.md")]

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
    lines.append(_REPORT_SEPARATOR)
    lines.append("INTEGRITY VERIFICATION REPORT")
    lines.append(_REPORT_SEPARATOR)

    # Overall status
    overall_status = "PASSED" if report.overall_integrity else "FAILED"
    lines.append(f"Overall Integrity: {overall_status}")
    lines.append("")

    lines.append("File Integrity:")
    for file_path, integrity in report.file_integrity.items():
        check_status = "OK" if integrity else "FAIL"
        lines.append(f"  [{check_status}] {file_path}")
    lines.append("")

    lines.append("Cross-Reference Integrity:")
    for ref_type, integrity in report.cross_reference_integrity.items():
        check_status = "OK" if integrity else "FAIL"
        lines.append(f"  [{check_status}] {ref_type}")
    lines.append("")

    lines.append("Data Consistency:")
    for check_type, integrity in report.data_consistency.items():
        check_status = "OK" if integrity else "FAIL"
        lines.append(f"  [{check_status}] {check_type}")
    lines.append("")

    lines.append("Academic Standards:")
    for standard, compliance in report.academic_standards.items():
        check_status = "OK" if compliance else "WARN"
        lines.append(f"  [{check_status}] {standard}")
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

    lines.append(_REPORT_SEPARATOR)

    return "\n".join(lines)


__all__ = [
    "BuildArtifactValidation",
    "IntegrityReport",
    "OutputCompleteness",
    "PermissionCheck",
    "check_file_permissions",
    "create_integrity_manifest",
    "generate_integrity_report",
    "load_integrity_manifest",
    "save_integrity_manifest",
    "validate_build_artifacts",
    "verify_academic_standards",
    "verify_cross_references",
    "verify_data_consistency",
    "verify_file_integrity",
    "verify_integrity_against_manifest",
    "verify_output_completeness",
    "verify_output_integrity",
]
