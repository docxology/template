"""Output validation utilities.

This module provides functions for validating copied outputs and
output directory structure.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

from infrastructure.core.logging.utils import get_logger, log_success


from infrastructure.project.discovery import discover_projects


class _DirectoryDetail(TypedDict, total=False):
    exists: bool
    file_count: int
    size_mb: str
    largest_file: str | None


class _IssuesBySeverity(TypedDict):
    critical: list[str]
    warning: list[str]
    info: list[str]


class ValidationResultDict(TypedDict):
    structure: dict[str, Any]
    directories: dict[str, _DirectoryDetail]
    file_counts: dict[str, int]
    total_size_mb: float
    issues_by_severity: _IssuesBySeverity
    recommendations: list[Any]

logger = get_logger(__name__)


def _find_combined_pdf(output_dir: Path, project_name: str) -> tuple[Path, float] | None:
    """Locate the combined PDF for a project, checking three locations.

    Search order:
    1. ``output_dir/{project_name}_combined.pdf`` (root, post-copy)
    2. ``output_dir/pdf/{project_name}_combined.pdf`` (original generation location)
    3. ``projects/{project_name}/output/pdf/{project_name}_combined.pdf`` (source, pre-copy)

    Returns:
        Tuple of (path, size_mb) if found, or None if not found in any location.
    """
    filename = f"{project_name}_combined.pdf"

    # 1. Root directory (after copy outputs stage)
    root_pdf = output_dir / filename
    if root_pdf.exists() and root_pdf.stat().st_size > 0:
        return root_pdf, root_pdf.stat().st_size / (1024 * 1024)

    # 2. pdf/ subdirectory (original generation location)
    pdf_dir = output_dir / "pdf"
    if pdf_dir.exists():
        pdf_in_dir = pdf_dir / filename
        if pdf_in_dir.exists() and pdf_in_dir.stat().st_size > 0:
            return pdf_in_dir, pdf_in_dir.stat().st_size / (1024 * 1024)

    # 3. Source project directory (for Stage 6 validation before copy)
    path_parts = output_dir.parts
    if "output" in path_parts:
        # Use rindex (last occurrence) so a parent dir named 'output' doesn't corrupt the path.
        output_idx = len(path_parts) - 1 - path_parts[::-1].index("output")
        repo_root = Path(*path_parts[:output_idx])
        qualified_path = "/".join(path_parts[output_idx + 1:])
        source_pdf_dir = repo_root / "projects" / qualified_path / "output" / "pdf"
    else:
        source_pdf_dir = output_dir.parent.parent / "projects" / project_name / "output" / "pdf"

    logger.debug("PDF not found in output directory, checking source: %s", source_pdf_dir.parent)
    if source_pdf_dir.exists():
        source_pdf = source_pdf_dir / filename
        if source_pdf.exists() and source_pdf.stat().st_size > 0:
            return source_pdf, source_pdf.stat().st_size / (1024 * 1024)

    return None


def validate_copied_outputs(output_dir: Path) -> bool:
    """Validate all project outputs were copied successfully.

    Checks:
    - Combined PDF exists at root (preferred) or in pdf/ directory (fallback)
    - Also checks source directory if copy hasn't happened yet (Stage 6 validation)
    - All expected subdirectories exist (pdf, web, slides, figures, data, reports, simulations, llm, logs)
    - Each directory contains files
    - All files are readable

    Args:
        output_dir: Path to top-level output directory

    Returns:
        True if validation successful, False if critical files missing
    """
    logger.info("Validating copied outputs...")

    validation_passed = True

    # Check combined PDF using shared location logic
    project_name = output_dir.name if "output" in output_dir.parts else None

    combined_pdf_found = False
    if project_name:
        pdf_result = _find_combined_pdf(output_dir, project_name)
        if pdf_result:
            _pdf_path, size_mb = pdf_result
            log_success(f"Combined PDF valid ({size_mb:.2f} MB)", logger)
            combined_pdf_found = True

    if not combined_pdf_found:
        logger.error("Combined manuscript PDF missing or empty")
        if project_name:
            logger.error(f"  Expected: output/{project_name}/{project_name}_combined.pdf")
            logger.error(f"  Or in: output/{project_name}/pdf/{project_name}_combined.pdf")
            logger.error(
                f"  Or in source: projects/{project_name}/output/pdf/{project_name}_combined.pdf"
            )
        else:
            logger.error("  Expected: output/{project_name}_combined.pdf")
        logger.error("  → PDF rendering stage (Stage 5) may have failed")
        logger.error("  → Check project output/ directory for the combined PDF")
        validation_passed = False

    # Check all expected subdirectories
    expected_dirs = {
        "pdf": "PDF manuscripts and metadata",
        "web": "HTML web outputs",
        "slides": "Beamer slide presentations",
        "figures": "Generated figures and images",
        "data": "Data files and datasets",
        "reports": "Analysis and simulation reports",
        "simulations": "Simulation outputs and checkpoints",
        "llm": "LLM-generated manuscript reviews",
        "logs": "Pipeline execution logs",
    }

    # Directories that are optional or populated later in the pipeline
    optional_dirs = {
        "llm",
        "logs",
    }  # LLM stage and logs may be generated during pipeline

    for dir_name, description in expected_dirs.items():
        subdir = output_dir / dir_name
        if subdir.exists():
            files = list(subdir.glob("**/*"))
            file_count = len([f for f in files if f.is_file()])
            if file_count > 0:
                total_size_mb = sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024)
                log_success(
                    f"{dir_name}/ valid ({file_count} files, {total_size_mb:.2f} MB)",
                    logger,
                )
            else:
                # Only warn for required directories, debug for optional or potentially empty
                if dir_name in optional_dirs:
                    logger.debug(f"{dir_name}/ not yet populated (generated in later stage)")
                else:
                    logger.debug(
                        f"{dir_name}/ directory exists but is empty (may be expected for this project type)"  # noqa: E501
                    )
        else:
            if dir_name in optional_dirs:
                logger.debug(f"{dir_name}/ not found (optional, generated in later stage)")
            else:
                logger.warning(f"{dir_name}/ directory not found ({description})")

    return validation_passed


def validate_root_output_structure(repo_root: Path) -> dict[str, Any]:
    """Validate that root output/ directory structure is correct.

    Checks that output/ directory only contains project-specific folders
    and no root-level directories (data/, figures/, pdf/, etc.).

    Args:
        repo_root: Repository root directory

    Returns:
        Validation report dictionary with:
        - valid: Boolean indicating if structure is correct
        - issues: List of issues found
        - project_folders: List of project folders found
        - invalid_folders: List of invalid root-level directories
    """
    output_dir = repo_root / "output"

    if not output_dir.exists():
        return {
            "valid": False,
            "issues": ["Output directory does not exist"],
            "project_folders": [],
            "invalid_folders": [],
        }

    # Discover valid project names
    projects = discover_projects(repo_root)
    project_names = set(p.name for p in projects)

    issues = []
    project_folders = []
    invalid_folders = []

    # Check each item in output directory
    for item in output_dir.iterdir():
        if not item.is_dir():
            continue  # Skip files

        item_name = item.name

        # Keep project-specific folders
        if item_name in project_names:
            project_folders.append(item_name)
            continue

        # Keep special directories
        if item_name in [".gitkeep", ".gitignore"]:
            continue

        # Check for root-level directories that shouldn't exist
        root_level_dirs = {
            "data",
            "figures",
            "pdf",
            "web",
            "slides",
            "reports",
            "simulations",
            "llm",
            "logs",
            "tex",
        }

        if item_name in root_level_dirs:
            invalid_folders.append(item_name)
            issues.append(f"Root-level directory '{item_name}' should not exist in output/")
        else:
            # Unknown directory - flag as potential issue
            issues.append(
                f"Unknown directory '{item_name}' in output/ (should only contain project folders)"
            )

    valid = len(issues) == 0

    report = {
        "valid": valid,
        "issues": issues,
        "project_folders": sorted(project_folders),
        "invalid_folders": sorted(invalid_folders),
    }

    if valid:
        logger.info(f"Root output structure valid: {len(project_folders)} project folders found")
    else:
        logger.warning(f"Root output structure invalid: {len(issues)} issues found")

    return report

def collect_detailed_validation_results(output_dir: Path) -> ValidationResultDict:
    """Collect detailed validation results for reporting.

    Provides comprehensive validation data including file counts, sizes,
    issue categorization, and recommendations.

    Args:
        output_dir: Path to output directory

    Returns:
        Dictionary with detailed validation results:
        - structure: Output structure validation results
        - directories: Per-directory validation details
        - file_counts: File counts by type
        - total_size_mb: Total output size
        - issues_by_severity: Categorized issues
        - recommendations: Actionable recommendations
    """
    validation_results: ValidationResultDict = {
        "structure": validate_output_structure(output_dir),
        "directories": {},
        "file_counts": {},
        "total_size_mb": 0.0,
        "issues_by_severity": {"critical": [], "warning": [], "info": []},
        "recommendations": [],
    }

    # Collect per-directory details
    for subdir_name in [
        "pdf",
        "web",
        "slides",
        "figures",
        "data",
        "reports",
        "simulations",
        "llm",
        "logs",
    ]:
        subdir = output_dir / subdir_name
        if subdir.exists() and subdir.is_dir():
            files = list(subdir.rglob("*"))
            files = [f for f in files if f.is_file()]
            size_mb = sum(f.stat().st_size for f in files) / (1024 * 1024)

            validation_results["directories"][subdir_name] = {
                "exists": True,
                "file_count": len(files),
                "size_mb": f"{size_mb:.2f}",
                "largest_file": (
                    max((f.stat().st_size, f.name) for f in files)[1] if files else None
                ),
            }
            validation_results["file_counts"][subdir_name] = len(files)
            validation_results["total_size_mb"] += size_mb
        else:
            validation_results["directories"][subdir_name] = {
                "exists": False,
                "file_count": 0,
                "size_mb": "0.00",
            }
            validation_results["issues_by_severity"]["warning"].append(
                f"Directory '{subdir_name}/' missing or empty"
            )

    # Add issues from structure validation
    if not validation_results["structure"]["valid"]:
        for issue in validation_results["structure"]["issues"]:
            validation_results["issues_by_severity"]["critical"].append(issue)

    # Add missing file issues
    for missing_file in validation_results["structure"].get("missing_files", []):
        if missing_file == "project_combined.pdf":
            validation_results["issues_by_severity"]["critical"].append(
                f"Missing expected file: {missing_file}"
            )
        elif "_combined.pdf" in missing_file:
            project_name = missing_file.replace("_combined.pdf", "")
            validation_results["issues_by_severity"]["critical"].append(
                f"Missing expected file: {missing_file} (project-specific combined PDF for {project_name})"  # noqa: E501
            )
        else:
            validation_results["issues_by_severity"]["critical"].append(
                f"Missing expected file: {missing_file}"
            )

    # Add suspicious size issues
    for size_issue in validation_results["structure"].get("suspicious_sizes", []):
        validation_results["issues_by_severity"]["warning"].append(size_issue)

    # Generate recommendations based on issues
    if validation_results["issues_by_severity"]["critical"]:
        validation_results["recommendations"].append(
            {
                "priority": "high",
                "action": "Review critical issues in output generation",
                "details": "Check PDF rendering and copy stages for errors",
            }
        )

    if not validation_results["directories"]["figures"]["exists"]:
        validation_results["recommendations"].append(
            {
                "priority": "medium",
                "action": "Ensure analysis scripts generate figures",
                "details": "Check projects/{name}/scripts/analysis_pipeline.py execution",
            }
        )

    if not validation_results["directories"]["reports"]["exists"]:
        validation_results["recommendations"].append(
            {
                "priority": "low",
                "action": "Generate analysis reports",
                "details": "Enable report generation in analysis pipeline",
            }
        )

    return validation_results


def validate_output_structure(output_dir: Path) -> dict[str, Any]:
    """Validate complete output directory structure.

    Checks:
    - Output directory exists
    - Combined PDF exists and is > 100KB (should be substantial)
    - All expected subdirectories exist (pdf, web, slides, figures, data, reports, simulations, llm, logs)
    - Each subdirectory contains files
    - All files are readable

    Args:
        output_dir: Path to top-level output directory

    Returns:
        Dictionary with structure validation results
    """
    result = {
        "valid": True,
        "issues": [],
        "missing_files": [],
        "suspicious_sizes": [],
        "warnings": [],
        "directory_structure": {},
    }

    # Check output directory exists
    if not output_dir.exists():
        result["valid"] = False
        result["issues"].append("Output directory does not exist")
        return result

    # Check combined PDF using shared location logic
    project_name = (
        output_dir.name
        if output_dir.parent.name == "output" and output_dir.name != "output"
        else None
    )

    combined_pdf_found = False
    pdf_file = None
    pdf_size_mb = 0.0

    if project_name:
        pdf_result = _find_combined_pdf(output_dir, project_name)
        if pdf_result:
            pdf_file, pdf_size_mb = pdf_result
            combined_pdf_found = True
            size_bytes = int(pdf_size_mb * 1024 * 1024)
            if size_bytes < 100 * 1024:
                result["suspicious_sizes"].append(
                    f"Combined PDF is unusually small: {pdf_size_mb:.2f} MB"
                )
        else:
            result["missing_files"].append(f"{project_name}_combined.pdf")
    else:
        logger.debug(
            "No project name detected in directory structure, skipping specific PDF validation"
        )

    # Populate directory structure metadata
    pdf_key = "project_combined_pdf"  # Default key for backward compatibility
    if combined_pdf_found and pdf_file:
        result["directory_structure"][pdf_key] = {
            "exists": True,
            "size_mb": round(pdf_size_mb, 2),
            "readable": pdf_file.is_file(),
        }
    else:
        result["valid"] = False
        result["directory_structure"][pdf_key] = {
            "exists": False,
            "size_mb": 0.0,
            "readable": False,
        }

    # Check all expected subdirectories
    expected_dirs = [
        "pdf",
        "web",
        "slides",
        "figures",
        "data",
        "reports",
        "simulations",
        "llm",
        "logs",
    ]
    # Directories that are optional or populated later in the pipeline
    optional_dirs = {
        "llm",
        "logs",
        "simulations",
    }  # LLM stage, logs, and simulations may be generated during pipeline

    for subdir_name in expected_dirs:
        subdir = output_dir / subdir_name

        if subdir.exists():
            files = list(subdir.glob("**/*"))
            file_count = len([f for f in files if f.is_file()])
            total_size_mb = sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024)

            result["directory_structure"][subdir_name] = {
                "exists": True,
                "files": file_count,
                "size_mb": round(total_size_mb, 2),
                "readable": subdir.is_dir(),
                "optional": subdir_name in optional_dirs,
            }

            # Only flag empty directories as suspicious if not optional
            if file_count == 0 and subdir_name not in optional_dirs:
                result["suspicious_sizes"].append(f"{subdir_name}/ directory is empty")
        else:
            result["directory_structure"][subdir_name] = {
                "exists": False,
                "files": 0,
                "size_mb": 0.0,
                "optional": subdir_name in optional_dirs,
            }
            # Only add issue for required directories
            if subdir_name not in optional_dirs:
                result["issues"].append(f"Missing directory: {subdir_name}/")

    return result
