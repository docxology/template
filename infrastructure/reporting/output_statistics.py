"""Output file statistics collection and summary reporting.

This module provides functions for collecting comprehensive output file
statistics and generating summary reports of output copying results.
"""

import json
from collections.abc import Collection, Mapping
from pathlib import Path
from typing import Any

from infrastructure.core.logging.constants import BANNER_WIDTH
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.artifacts import (
    STABLE_OUTPUT_INVENTORY_MODE,
    OutputInventoryMode,
    StableOutputInventory,
    collect_stable_output_inventory,
)
from infrastructure.validation.output.layout import OPTIONAL_OUTPUT_SUBDIRS, OUTPUT_SUBDIR_NAMES

logger = get_logger(__name__)

PROJECT_OUTPUT_INVENTORY_SCOPE = "project-output"
STAGE5_DELIVERY_INVENTORY_SCOPE = "stage5-delivery-mirror"
_INVENTORY_SCOPES = frozenset({PROJECT_OUTPUT_INVENTORY_SCOPE, STAGE5_DELIVERY_INVENTORY_SCOPE})


def log_output_summary(
    output_dir: Path,
    stats: dict[str, Any],
    structure_validation: Mapping[str, Any] | None = None,
) -> None:
    """Generate summary of output copying results.

    Args:
        output_dir: Path to output directory
        stats: Dictionary with copy statistics
        structure_validation: Optional validation results dict
    """
    logger.info("\n" + "=" * BANNER_WIDTH)
    logger.info("Output Copying Summary")
    logger.info("=" * BANNER_WIDTH)

    logger.info(f"\nOutput directory: {output_dir}")
    logger.info("\nFiles copied by directory:")
    logger.info(f"  • PDF files: {stats['pdf_files']}")
    logger.info(f"  • Web files: {stats['web_files']}")
    logger.info(f"  • Slides files: {stats['slides_files']}")
    logger.info(f"  • DOCX files: {stats.get('docx_files', 0)}")
    logger.info(f"  • EPUB files: {stats.get('epub_files', 0)}")
    logger.info(f"  • Figures: {stats['figures_files']}")
    logger.info(f"  • Data files: {stats['data_files']}")
    logger.info(f"  • Reports: {stats['reports_files']}")
    logger.info(f"  • Simulations: {stats['simulations_files']}")
    logger.info(f"  • LLM reviews: {stats['llm_files']}")
    logger.info(f"  • Log files: {stats['logs_files']}")
    logger.info(f"  • Combined PDF (root): {stats['combined_pdf']}")
    logger.info(f"\n  Total files copied: {stats['total_files']}")

    # Include structure validation if provided
    if structure_validation:
        logger.info("\nDirectory structure:")
        for item, info in structure_validation.get("directory_structure", {}).items():
            if info.get("exists"):
                if "size_mb" in info and "files" in info:
                    logger.info(f"  ✓ {item}: {info['files']} files, {info['size_mb']} MB")
                elif "size_mb" in info:
                    logger.info(f"  ✓ {item}: {info['size_mb']} MB")
                elif "files" in info:
                    logger.info(f"  ✓ {item}: {info['files']} files")
            elif info.get("required") is False:
                logger.info(f"  ○ {item}: Not required for this run")
            else:
                logger.info(f"  ✗ {item}: Not found")

    if stats["errors"]:
        logger.info(f"\nWarnings/Errors ({len(stats['errors'])}):")
        for error in stats["errors"]:
            logger.warning(f"  • {error}")

    logger.info("")


def collect_output_statistics(
    repo_root: Path,
    project_name: str = "project",
    project_dir: Path | None = None,
    *,
    require_pdf: bool = True,
    output_dir: Path | None = None,
    inventory: StableOutputInventory | None = None,
    enabled_formats: Collection[str] | None = None,
    inventory_scope: str = PROJECT_OUTPUT_INVENTORY_SCOPE,
    inventory_mode: OutputInventoryMode = STABLE_OUTPUT_INVENTORY_MODE,
) -> dict[str, Any]:
    """Collect comprehensive output file statistics.

    Args:
        repo_root: Repository root path.
        project_name: Name of the project (default: "project").
        project_dir: Absolute path to the project directory. When provided,
            overrides ``repo_root / 'projects' / project_name``.
        require_pdf: Whether a canonical combined PDF is required by the
            effective render-format configuration.
        output_dir: Exact output tree to describe. When omitted, derives the
            canonical project output from ``project_dir`` or ``repo_root``.
        inventory: Optional stable inventory already collected for
            ``output_dir``; useful for Stage 5's filtered delivery mirror.
        enabled_formats: Effective publication formats. When supplied,
            missing-format diagnostics describe only enabled deliverables;
            disabled PDF/HTML/slides/DOCX/EPUB directories are not warnings.
        inventory_scope: Machine-readable identity for the tree being counted.
            Stage 5 uses ``stage5-delivery-mirror`` because its source-located
            report intentionally describes the filtered top-level copy.
        inventory_mode: Explicit stable inventory policy used when ``inventory``
            is not already supplied. Defaults to fail-closed Git-shippable mode.

    Returns:
        Dictionary with comprehensive output statistics including:
        - File counts by category
        - File sizes by category
        - Largest files
        - Missing expected files
        - Total size and file count
    """
    output_dir = (
        output_dir
        if output_dir is not None
        else (project_dir if project_dir is not None else repo_root / "projects" / project_name) / "output"
    ).absolute()

    if inventory_scope not in _INVENTORY_SCOPES:
        raise ValueError(f"unsupported output inventory scope: {inventory_scope!r}")
    current = (
        inventory
        if inventory is not None
        else collect_stable_output_inventory(output_dir, inventory_mode=inventory_mode)
    )
    if current.issues:
        raise ValueError("unstable output inventory: " + "; ".join(current.issues))

    inventory_root = (
        _release_safe_output_dir(output_dir)
        if inventory_scope == STAGE5_DELIVERY_INVENTORY_SCOPE
        else (Path("projects") / project_name / "output").as_posix()
    )
    stats: dict[str, Any] = {
        "directories": {},
        "total_files": 0,
        "total_size_mb": 0.0,
        "largest_files": [],
        "missing_expected_files": [],
        "sizes_by_category": {},
        "inventory_mode": current.mode,
        "inventory_scope": inventory_scope,
        "inventory_root": inventory_root,
    }

    # Expected output directories
    expected_dirs = list(OUTPUT_SUBDIR_NAMES)
    enabled = set(enabled_formats) if enabled_formats is not None else None

    files_by_directory: dict[str, list[Path]] = {name: [] for name in expected_dirs}
    for path in current.files:
        relative = path.relative_to(output_dir)
        category = relative.parts[0] if len(relative.parts) > 1 else "root"
        files_by_directory.setdefault(category, []).append(path)

    if sum(len(paths) for paths in files_by_directory.values()) != len(current.files):
        raise ValueError("stable output inventory grouping is incomplete")

    project_basename = Path(project_name).name
    combined_pdf_candidates = (
        output_dir / f"{project_basename}_combined.pdf",
        output_dir / "pdf" / f"{project_basename}_combined.pdf",
    )

    category_names = (*expected_dirs, *sorted(set(files_by_directory) - set(expected_dirs)))
    for dir_name in category_names:
        files = files_by_directory[dir_name]

        if files:
            # Calculate total size
            sizes = [(f.stat().st_size, f) for f in files]
            total_size = sum(size for size, _ in sizes)
            size_mb = total_size / (1024 * 1024)

            # Find largest files in this directory
            largest_in_dir = sorted(sizes, key=lambda item: (-item[0], item[1].relative_to(output_dir).as_posix()))[:3]
            largest_files_info = [
                {
                    "name": f.name,
                    "size_mb": f"{size / (1024 * 1024):.2f}",
                    "size_bytes": size,
                    "path": f.relative_to(output_dir).as_posix(),
                }
                for size, f in largest_in_dir
            ]

            # Count files by extension
            extensions: dict[str, int] = {}
            for f in files:
                ext = f.suffix.lower() or "no_extension"
                extensions[ext] = extensions.get(ext, 0) + 1

            stats["directories"][dir_name] = {
                "exists": True,
                "file_count": len(files),
                "size_mb": f"{size_mb:.2f}",
                "total_size_bytes": total_size,
                "largest_files": largest_files_info,
                "extensions": extensions,
            }

            stats["total_files"] += len(files)
            stats["total_size_mb"] += size_mb
            stats["sizes_by_category"][dir_name] = size_mb

            # The directory payload is intentionally limited to three, but the
            # global top ten must consider every stable file. Otherwise a
            # category containing more than three of the repository's largest
            # artifacts is silently under-represented.
            for size, f in sizes:
                stats["largest_files"].append(
                    {
                        "name": f.name,
                        "size_mb": f"{size / (1024 * 1024):.2f}",
                        "size_bytes": size,
                        "category": dir_name,
                        "path": f.relative_to(output_dir).as_posix(),
                    }
                )
        else:
            stats["directories"][dir_name] = {
                "exists": False,
                "file_count": 0,
                "size_mb": "0.00",
                "total_size_bytes": 0,
            }
            is_render_directory = dir_name in {"pdf", "web", "slides", "docx", "epub"}
            if (
                dir_name not in OPTIONAL_OUTPUT_SUBDIRS
                and dir_name != "pdf"
                and not (enabled is not None and is_render_directory)
            ):
                stats["missing_expected_files"].append(f"{dir_name}/ directory")

    # Sort largest files by size
    stats["largest_files"] = sorted(
        stats["largest_files"],
        key=lambda item: (-item["size_bytes"], item["path"]),
    )[:10]

    # Check for expected combined PDF
    required_formats = enabled if enabled is not None else ({"pdf"} if require_pdf else set())
    format_candidates: dict[str, tuple[Path, ...]] = {
        "pdf": combined_pdf_candidates,
        "html": (output_dir / "web" / "index.html",),
        "slides": tuple(sorted((output_dir / "slides").glob("*_slides.pdf"))),
        "docx": (output_dir / "docx" / f"{project_basename}_combined.docx",),
        "epub": (output_dir / "epub" / f"{project_basename}_combined.epub",),
    }
    format_labels = {
        "pdf": f"{project_basename}_combined.pdf",
        "html": "web/index.html",
        "slides": "slides/*_slides.pdf",
        "docx": f"{project_basename}_combined.docx",
        "epub": f"{project_basename}_combined.epub",
    }
    stable_files = set(current.files)
    for format_name in sorted(required_formats):
        candidates = format_candidates.get(format_name, ())
        if not candidates or not any(path in stable_files for path in candidates):
            stats["missing_expected_files"].append(format_labels.get(format_name, format_name))

    # Add file type counts
    all_extensions: dict[str, int] = {}
    for dir_info in stats["directories"].values():
        if dir_info["exists"]:
            for ext, count in dir_info.get("extensions", {}).items():
                all_extensions[ext] = all_extensions.get(ext, 0) + count
    stats["file_counts_by_type"] = all_extensions

    return stats


def generate_detailed_output_report(output_dir: Path, stats: dict[str, Any]) -> str:
    """Generate detailed output statistics report.

    Args:
        output_dir: Path to output directory
        stats: Output statistics dictionary

    Returns:
        Formatted report string
    """
    inventory_mode = stats.get("inventory_mode", STABLE_OUTPUT_INVENTORY_MODE)
    inventory_scope = stats.get("inventory_scope", PROJECT_OUTPUT_INVENTORY_SCOPE)
    inventory_root = stats.get("inventory_root", _release_safe_output_dir(output_dir))
    lines = [
        "",
        "OUTPUT STATISTICS REPORT",
        "=" * BANNER_WIDTH,
        "",
        f"Output Directory: {_release_safe_output_dir(output_dir)}",
        f"Inventory Mode: {inventory_mode}",
        f"Inventory Scope: {inventory_scope}",
        f"Inventory Root: {inventory_root}",
        "",
        f"Total Files: {stats['total_files']}",
        f"Total Size: {stats['total_size_mb']:.2f} MB",
        "",
        "Files by Category:",
    ]

    for dir_name, dir_info in stats["directories"].items():
        if dir_info["exists"] and dir_info["file_count"] > 0:
            lines.append(f"  • {dir_name}: {dir_info['file_count']} files ({dir_info['size_mb']} MB)")

    if stats["largest_files"]:
        lines.append("")
        lines.append("Largest Files:")
        for file_info in stats["largest_files"][:5]:
            lines.append(f"  • {file_info['name']}: {file_info['size_mb']} MB ({file_info['category']})")

    if stats["missing_expected_files"]:
        lines.append("")
        lines.append("Missing Expected Files:")
        for missing in stats["missing_expected_files"]:
            lines.append(f"  ⚠  {missing}")

    if stats["file_counts_by_type"]:
        lines.append("")
        lines.append("File Types:")
        for ext, count in sorted(stats["file_counts_by_type"].items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"  • {ext}: {count} file(s)")

    lines.append("")

    return "\n".join(lines)


def _release_safe_output_dir(output_dir: Path) -> str:
    """Return a path label suitable for copied release-facing reports."""
    parts = output_dir.parts
    if "output" in parts:
        index = len(parts) - 1 - parts[::-1].index("output")
        return Path(*parts[index:]).as_posix()
    if "projects" in parts:
        index = len(parts) - 1 - parts[::-1].index("projects")
        return Path(*parts[index:]).as_posix()
    return output_dir.name


def write_output_statistics_reports(
    project_output_dir: Path,
    stats: dict[str, Any],
    *,
    report_output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Write text and JSON output statistics reports under ``output/reports``."""
    report = generate_detailed_output_report(report_output_dir or project_output_dir, stats)
    reports_dir = project_output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    text_path = reports_dir / "output_statistics.txt"
    json_path = reports_dir / "output_statistics.json"
    text_path.write_text(report, encoding="utf-8")
    json_path.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    return text_path, json_path
