"""Output validation utilities.

This module provides functions for validating copied outputs and
output directory structure.
"""

from collections.abc import Collection
from pathlib import Path
from typing import Any, TypedDict

from infrastructure.core.files.pdf_locator import find_combined_pdf as _find_combined_pdf
from infrastructure.core.logging.utils import get_logger, log_success
from infrastructure.core.pipeline.artifacts import (
    STABLE_OUTPUT_INVENTORY_MODE,
    OutputInventoryMode,
    StableOutputInventory,
    collect_stable_output_inventory,
)

from infrastructure.project.discovery import discover_projects
from infrastructure.validation.output.layout import OPTIONAL_OUTPUT_SUBDIRS, OUTPUT_SUBDIR_NAMES
from infrastructure.validation.output.render_formats import validate_enabled_render_outputs


class _DirectoryDetail(TypedDict, total=False):
    exists: bool
    file_count: int
    size_mb: str
    largest_file: str | None
    largest_file_path: str | None


class _IssuesBySeverity(TypedDict):
    critical: list[str]
    warning: list[str]
    info: list[str]


class OutputStructureResult(TypedDict):
    """Validation details for one generated output tree."""

    valid: bool
    issues: list[str]
    missing_files: list[str]
    suspicious_sizes: list[str]
    warnings: list[str]
    directory_structure: dict[str, dict[str, Any]]
    inventory_mode: str


class ValidationResultDict(TypedDict):
    """Data container for ValidationResultDict."""

    structure: OutputStructureResult
    directories: dict[str, _DirectoryDetail]
    file_counts: dict[str, int]
    total_size_mb: float
    issues_by_severity: _IssuesBySeverity
    recommendations: list[Any]
    inventory_mode: str


logger = get_logger(__name__)

_RENDER_FORMAT_BY_SUBDIR = {
    "pdf": "pdf",
    "web": "html",
    "slides": "slides",
    "docx": "docx",
    "epub": "epub",
}


def _stable_category_required(
    category: str,
    enabled_formats: Collection[str] | None,
    *,
    require_pdf: bool,
) -> bool:
    """Return whether an empty stable category is actionable for this run."""

    if category == "pdf":
        return require_pdf
    format_name = _RENDER_FORMAT_BY_SUBDIR.get(category)
    if format_name is not None and enabled_formats is not None:
        return format_name in enabled_formats
    return category not in OPTIONAL_OUTPUT_SUBDIRS


def _stable_files_by_subdir(
    output_dir: Path,
    inventory: StableOutputInventory | None = None,
    *,
    inventory_mode: OutputInventoryMode = STABLE_OUTPUT_INVENTORY_MODE,
) -> tuple[StableOutputInventory, dict[str, tuple[Path, ...]]]:
    """Return one fail-closed stable inventory grouped by output category."""
    output_dir = output_dir.absolute()
    current = (
        inventory
        if inventory is not None
        else collect_stable_output_inventory(output_dir, inventory_mode=inventory_mode)
    )
    if current.issues:
        raise ValueError("unstable output inventory: " + "; ".join(current.issues))
    grouped: dict[str, list[Path]] = {name: [] for name in OUTPUT_SUBDIR_NAMES}
    for path in current.files:
        try:
            relative = path.relative_to(output_dir)
        except ValueError as exc:
            raise ValueError(f"stable output path escapes output directory: {path}") from exc
        category = relative.parts[0] if len(relative.parts) > 1 else "root"
        grouped.setdefault(category, []).append(path)
    if sum(len(paths) for paths in grouped.values()) != len(current.files):
        raise ValueError("stable output inventory grouping is incomplete")
    return current, {name: tuple(paths) for name, paths in grouped.items()}


def validate_copied_outputs(
    output_dir: Path,
    *,
    project_name: str | None = None,
    enabled_formats: Collection[str] | None = None,
    manuscript_dir: Path | None = None,
    inventory: StableOutputInventory | None = None,
) -> bool:
    """Validate all project outputs were copied successfully.

    Checks:
    - When ``enabled_formats`` is supplied, validates exactly those canonical
      copied artifacts and rejects canonical artifacts for disabled formats.
    - Otherwise preserves the legacy combined-PDF lookup contract.
    - All expected subdirectories exist (pdf, web, slides, figures, data, reports, simulations, llm, logs)
    - Each directory contains files
    - All files are readable

    Args:
        output_dir: Path to top-level output directory.
        project_name: Qualified project name or basename. Defaults to the
            copied output directory name.
        enabled_formats: Effective render formats. ``None`` preserves the
            legacy PDF-only behavior for callers that do not have config.
        manuscript_dir: Current source manuscript, used to derive exact slide
            deck names when slides are enabled.
        inventory: Optional canonical inventory for the copied tree. Stage 5
            supplies one whose Git-ignore decisions are mapped to the source
            project output rather than the intentionally ignored root mirror.

    Returns:
        True if validation successful, False if critical files missing
    """
    logger.info("Validating copied outputs...")

    validation_passed = True

    inferred_project_name = project_name or (output_dir.name if "output" in output_dir.parts else None)
    if enabled_formats is not None:
        if inferred_project_name is None:
            logger.error("Cannot validate configured render outputs without a project name")
            validation_passed = False
        else:
            validation_passed = validate_enabled_render_outputs(
                output_dir,
                inferred_project_name,
                enabled_formats,
                manuscript_dir=manuscript_dir,
                inventory=inventory,
            )
    else:
        # Preserve the historical PDF contract for callers without an
        # effective render configuration.
        combined_pdf_found = False
        if inferred_project_name:
            pdf_result = _find_combined_pdf(output_dir, inferred_project_name)
            if pdf_result:
                _pdf_path, size_mb = pdf_result
                log_success(f"Combined PDF valid ({size_mb:.2f} MB)", logger)
                combined_pdf_found = True

        if not combined_pdf_found:
            logger.error("Combined manuscript PDF missing or empty")
            if inferred_project_name:
                logger.error(
                    f"  Expected: output/{inferred_project_name}/{Path(inferred_project_name).name}_combined.pdf"
                )
                logger.error(
                    f"  Or in: output/{inferred_project_name}/pdf/{Path(inferred_project_name).name}_combined.pdf"
                )
                logger.error(
                    f"  Or in source: projects/{inferred_project_name}/output/pdf/"
                    f"{Path(inferred_project_name).name}_combined.pdf"
                )
                logger.error(
                    f"  Or in WIP source: projects/working/{inferred_project_name}/output/pdf/"
                    f"{Path(inferred_project_name).name}_combined.pdf"
                )
            else:
                logger.error("  Expected: output/{project_name}_combined.pdf")
            logger.error("  → PDF rendering stage may have failed")
            logger.error("  → Check project output/ directory for the combined PDF")
            validation_passed = False

    # Check all expected subdirectories
    expected_dirs = {
        "pdf": "PDF manuscripts and metadata",
        "web": "HTML web outputs",
        "slides": "Beamer slide presentations",
        "docx": "Microsoft Word manuscript deliverables",
        "epub": "EPUB manuscript deliverables",
        "figures": "Generated figures and images",
        "data": "Data files and datasets",
        "reports": "Analysis and simulation reports",
        "simulations": "Simulation outputs and checkpoints",
        "llm": "LLM-generated manuscript reviews",
        "logs": "Pipeline execution logs",
    }

    # Directories that are optional or populated later in the pipeline
    optional_dirs = set(OPTIONAL_OUTPUT_SUBDIRS)

    _inventory, files_by_subdir = _stable_files_by_subdir(output_dir, inventory)

    for dir_name, description in expected_dirs.items():
        files = files_by_subdir[dir_name]
        if files:
            file_count = len(files)
            total_size_mb = sum(f.stat().st_size for f in files) / (1024 * 1024)
            log_success(
                f"{dir_name}/ valid ({file_count} files, {total_size_mb:.2f} MB)",
                logger,
            )
        else:
            if enabled_formats is not None:
                if _stable_category_required(
                    dir_name,
                    enabled_formats,
                    require_pdf="pdf" in enabled_formats,
                ):
                    logger.warning(f"{dir_name}/ has no stable artifacts ({description})")
                else:
                    logger.debug(f"{dir_name}/ is not enabled and has no stable artifacts")
            elif dir_name in optional_dirs:
                logger.debug(f"{dir_name}/ has no stable artifacts (optional, generated in later stage)")
            else:
                logger.warning(f"{dir_name}/ has no stable artifacts ({description})")

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
    project_names = set(p.qualified_name for p in projects)
    project_output_roots = {Path(name).parts[0] for name in project_names if Path(name).parts}

    issues = []
    project_folders = []
    invalid_folders = []

    for item in output_dir.iterdir():
        if not item.is_dir():
            continue  # Skip files

        item_name = item.name

        # Keep project-specific folders
        if item_name in project_names or item_name in project_output_roots:
            project_folders.append(item_name)
            continue

        # Keep special directories generated by multi-project reporting.
        if item_name in [
            ".gitkeep",
            ".gitignore",
            "multi_project_summary",
            "executive_summary",
        ]:
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
            issues.append(f"Unknown directory '{item_name}' in output/ (should only contain project folders)")

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


def collect_detailed_validation_results(
    output_dir: Path,
    *,
    require_pdf: bool = True,
    inventory: StableOutputInventory | None = None,
    enabled_formats: Collection[str] | None = None,
    inventory_mode: OutputInventoryMode = STABLE_OUTPUT_INVENTORY_MODE,
) -> ValidationResultDict:
    """Collect detailed validation results for reporting.

    Provides comprehensive validation data including file counts, sizes,
    issue categorization, and recommendations.

    Args:
        output_dir: Path to output directory
        require_pdf: Whether the effective render configuration requires a PDF
            deliverable.
        inventory: Optional canonical inventory to reuse across one validation
            run. When omitted it is collected from ``output_dir``.
        enabled_formats: Effective publication formats for required-category
            diagnostics. ``None`` preserves legacy structure semantics.

    Returns:
        Dictionary with detailed validation results:
        - structure: Output structure validation results
        - directories: Per-directory validation details
        - file_counts: File counts by type
        - total_size_mb: Total output size
        - issues_by_severity: Categorized issues
        - recommendations: Actionable recommendations
    """
    output_dir = output_dir.absolute()
    current, files_by_subdir = _stable_files_by_subdir(
        output_dir,
        inventory,
        inventory_mode=inventory_mode,
    )
    validation_results: ValidationResultDict = {
        "structure": validate_output_structure(
            output_dir,
            require_pdf=require_pdf,
            inventory=current,
            enabled_formats=enabled_formats,
        ),
        "directories": {},
        "file_counts": {},
        "total_size_mb": 0.0,
        "issues_by_severity": {"critical": [], "warning": [], "info": []},
        "recommendations": [],
        "inventory_mode": current.mode,
    }

    category_names = (*OUTPUT_SUBDIR_NAMES, *sorted(set(files_by_subdir) - set(OUTPUT_SUBDIR_NAMES)))
    for subdir_name in category_names:
        files = files_by_subdir[subdir_name]
        if files:
            size_mb = sum(f.stat().st_size for f in files) / (1024 * 1024)
            largest = min(
                files,
                key=lambda path: (-path.stat().st_size, path.relative_to(output_dir).as_posix()),
            )

            validation_results["directories"][subdir_name] = {
                "exists": True,
                "file_count": len(files),
                "size_mb": f"{size_mb:.2f}",
                "largest_file": largest.name,
                "largest_file_path": largest.relative_to(output_dir).as_posix(),
            }
            validation_results["file_counts"][subdir_name] = len(files)
            validation_results["total_size_mb"] += size_mb
        else:
            validation_results["directories"][subdir_name] = {
                "exists": False,
                "file_count": 0,
                "size_mb": "0.00",
            }
            if _stable_category_required(
                subdir_name,
                enabled_formats,
                require_pdf=require_pdf,
            ):
                validation_results["issues_by_severity"]["warning"].append(
                    f"{subdir_name}/ has no stable publication artifacts"
                )

    if not validation_results["structure"]["valid"]:
        for issue in validation_results["structure"]["issues"]:
            validation_results["issues_by_severity"]["critical"].append(issue)

    for missing_file in validation_results["structure"].get("missing_files", []):
        if "_combined.pdf" in missing_file:
            project_name = missing_file.replace("_combined.pdf", "")
            validation_results["issues_by_severity"]["critical"].append(
                f"Missing expected file: {missing_file} (project-specific combined PDF for {project_name})"
            )
        else:
            validation_results["issues_by_severity"]["critical"].append(f"Missing expected file: {missing_file}")

    for size_issue in validation_results["structure"].get("suspicious_sizes", []):
        # An empty subdirectory with no producer is informational, not a
        # warning: many projects legitimately omit ``data/`` (pure-proof
        # workspaces such as fep_lean) or ``simulations/``. Truly anomalous
        # sizes (unusually small combined PDF, etc.) remain warnings.
        if "directory is empty" in size_issue:
            validation_results["issues_by_severity"]["info"].append(size_issue)
        else:
            validation_results["issues_by_severity"]["warning"].append(size_issue)

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


def validate_output_structure(
    output_dir: Path,
    *,
    require_pdf: bool = True,
    inventory: StableOutputInventory | None = None,
    enabled_formats: Collection[str] | None = None,
    inventory_mode: OutputInventoryMode = STABLE_OUTPUT_INVENTORY_MODE,
) -> OutputStructureResult:
    """Validate complete output directory structure.

    Checks:
    - Output directory exists
    - When ``require_pdf`` is true, a combined PDF exists and is > 100KB
    - All expected subdirectories exist (pdf, web, slides, figures, data, reports, simulations, llm, logs)
    - Each subdirectory contains files
    - All files are readable

    Args:
        output_dir: Path to top-level output directory
        require_pdf: Whether the effective format configuration requires PDF.
        inventory: Optional canonical inventory to reuse across one validation
            run. When omitted it is collected from ``output_dir``.
        enabled_formats: Effective publication formats for required-category
            diagnostics. ``None`` preserves legacy structure semantics.

    Returns:
        Dictionary with structure validation results
    """
    output_dir = output_dir.absolute()
    result: OutputStructureResult = {
        "valid": True,
        "issues": [],
        "missing_files": [],
        "suspicious_sizes": [],
        "warnings": [],
        "directory_structure": {},
        "inventory_mode": STABLE_OUTPUT_INVENTORY_MODE,
    }

    if not output_dir.exists():
        result["valid"] = False
        result["issues"].append("Output directory does not exist")
        return result

    current, files_by_subdir = _stable_files_by_subdir(
        output_dir,
        inventory,
        inventory_mode=inventory_mode,
    )
    result["inventory_mode"] = current.mode

    # Check combined PDF using shared location logic
    path_parts = output_dir.parts
    if output_dir.name == "output" and "projects" in path_parts:
        # Handle source project directory, including typed-subfolder and nested
        # layouts: projects/{name}/output, projects/{type}/{name}/output (e.g.
        # projects/templates/{name}/output), or projects/{program}/{name}/output.
        projects_idx = len(path_parts) - 1 - path_parts[::-1].index("projects")
        project_parts = path_parts[projects_idx + 1 : -1]
        project_name = "/".join(project_parts) if project_parts else output_dir.parent.name
    elif output_dir.name == "output":
        # A project checkout passes its canonical ``<project>/output``
        # directory here.  The previous branches handled copied output trees
        # but left this common source layout with no project name, causing a
        # valid PDF in output/pdf/ to be reported as missing.
        project_name = output_dir.parent.name
    elif output_dir.parent.name == "output" and output_dir.name != "output":
        # Handle copied root directory (e.g. output/{name})
        project_name = output_dir.name
    elif "output" in path_parts and output_dir.name != "output":
        # Handle copied nested root directory, e.g.
        # output/{program}/{name}.
        output_idx = len(path_parts) - 1 - path_parts[::-1].index("output")
        project_parts = path_parts[output_idx + 1 :]
        project_name = "/".join(project_parts) if project_parts else output_dir.name
    else:
        project_name = None

    combined_pdf_found = False
    pdf_file = None
    pdf_size_mb = 0.0

    if require_pdf and project_name:
        pdf_result = _find_combined_pdf(output_dir, project_name)
        pdf_is_stable = bool(pdf_result and pdf_result[0].absolute() in current.files)
        if pdf_result and not pdf_is_stable and inventory is None:
            candidate = pdf_result[0].absolute()
            try:
                candidate.relative_to(output_dir.absolute())
            except ValueError:
                # Legacy pre-copy validation may resolve the canonical PDF from
                # ``projects/<qualified>/output/pdf``. Admit that fallback only
                # when it belongs to its own stable inventory; a Git-ignored
                # source PDF must not satisfy the copied-output contract.
                source_output = candidate.parent.parent
                source_inventory = collect_stable_output_inventory(
                    source_output,
                    inventory_mode=inventory_mode,
                )
                result["issues"].extend(source_inventory.issues)
                pdf_is_stable = not source_inventory.issues and candidate in source_inventory.files
        if pdf_result and pdf_is_stable:
            pdf_file, pdf_size_mb = pdf_result
            combined_pdf_found = True
            size_bytes = int(pdf_size_mb * 1024 * 1024)
            if size_bytes < 100 * 1024:
                result["suspicious_sizes"].append(f"Combined PDF is unusually small: {pdf_size_mb:.2f} MB")
        else:
            result["missing_files"].append(f"{project_name}_combined.pdf")
    elif require_pdf:
        logger.debug("No project name detected in directory structure, skipping specific PDF validation")

    # Populate directory structure metadata
    pdf_key = "combined_pdf"
    if combined_pdf_found and pdf_file:
        result["directory_structure"][pdf_key] = {
            "exists": True,
            "size_mb": round(pdf_size_mb, 2),
            "readable": pdf_file.is_file(),
        }
    else:
        result["directory_structure"][pdf_key] = {
            "exists": False,
            "size_mb": 0.0,
            "readable": False,
            "required": require_pdf,
        }
        if require_pdf:
            result["valid"] = False
            result["issues"].append("Missing required combined PDF")

    category_names = (*OUTPUT_SUBDIR_NAMES, *sorted(set(files_by_subdir) - set(OUTPUT_SUBDIR_NAMES)))
    for subdir_name in category_names:
        files = files_by_subdir[subdir_name]

        if files:
            file_count = len(files)
            total_size_mb = sum(f.stat().st_size for f in files) / (1024 * 1024)

            result["directory_structure"][subdir_name] = {
                "exists": True,
                "files": file_count,
                "size_mb": round(total_size_mb, 2),
                "readable": all(f.is_file() for f in files),
                "optional": subdir_name in OPTIONAL_OUTPUT_SUBDIRS,
                "required": _stable_category_required(
                    subdir_name,
                    enabled_formats,
                    require_pdf=require_pdf,
                ),
            }
        else:
            required = _stable_category_required(
                subdir_name,
                enabled_formats,
                require_pdf=require_pdf,
            )
            result["directory_structure"][subdir_name] = {
                "exists": False,
                "files": 0,
                "size_mb": 0.0,
                "optional": subdir_name in OPTIONAL_OUTPUT_SUBDIRS,
                "required": required,
            }
            # Physical absence, an empty directory, and a directory containing
            # only ignored runtime files are deliberately the same stable
            # publication state.
            if required:
                result["suspicious_sizes"].append(f"{subdir_name}/ directory is empty of stable publication artifacts")

    return result
