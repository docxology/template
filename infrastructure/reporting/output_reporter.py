"""Output reporting utilities.

This module provides functions for generating output summaries and
collecting output statistics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

def generate_output_summary(
    output_dir: Path,
    stats: dict[str, Any],
    structure_validation: dict[str, Any | None] = None,
) -> None:
    """Generate summary of output copying results.

    Args:
        output_dir: Path to output directory
        stats: Dictionary with copy statistics
        structure_validation: Optional validation results dict
    """
    logger.info("\n" + "=" * 60)
    logger.info("Output Copying Summary")
    logger.info("=" * 60)

    logger.info(f"\nOutput directory: {output_dir}")
    logger.info("\nFiles copied by directory:")
    logger.info(f"  • PDF files: {stats['pdf_files']}")
    logger.info(f"  • Web files: {stats['web_files']}")
    logger.info(f"  • Slides files: {stats['slides_files']}")
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
            else:
                logger.info(f"  ✗ {item}: Not found")

    if stats["errors"]:
        logger.info(f"\nWarnings/Errors ({len(stats['errors'])}):")
        for error in stats["errors"]:
            logger.warning(f"  • {error}")

    logger.info("")

def collect_output_statistics(repo_root: Path, project_name: str = "project") -> dict[str, Any]:
    """Collect comprehensive output file statistics.

    Args:
        repo_root: Repository root path
        project_name: Name of the project (default: "project")

    Returns:
        Dictionary with comprehensive output statistics including:
        - File counts by category
        - File sizes by category
        - Largest files
        - Missing expected files
        - Total size and file count
    """
    output_dir = repo_root / "projects" / project_name / "output"

    stats = {
        "directories": {},
        "total_files": 0,
        "total_size_mb": 0.0,
        "largest_files": [],
        "missing_expected_files": [],
        "file_counts_by_type": {},
        "sizes_by_category": {},
    }

    # Expected output directories
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

    for dir_name in expected_dirs:
        subdir = output_dir / dir_name

        if subdir.exists() and subdir.is_dir():
            files = list(subdir.rglob("*"))
            files = [f for f in files if f.is_file()]

            # Calculate total size
            sizes = [(f.stat().st_size, f) for f in files]
            total_size = sum(size for size, _ in sizes)
            size_mb = total_size / (1024 * 1024)

            # Find largest files in this directory
            largest_in_dir = sorted(sizes, key=lambda x: x[0], reverse=True)[:3]
            largest_files_info = [
                {
                    "name": f.name,
                    "size_mb": f"{size / (1024 * 1024):.2f}",
                    "path": str(f.relative_to(output_dir)),
                }
                for size, f in largest_in_dir
            ]

            # Count files by extension
            extensions = {}  # type: ignore
            for f in files:
                ext = f.suffix.lower() or "no_extension"
                extensions[ext] = extensions.get(ext, 0) + 1

            stats["directories"][dir_name] = {  # type: ignore
                "exists": True,
                "file_count": len(files),
                "size_mb": f"{size_mb:.2f}",
                "total_size_bytes": total_size,
                "largest_files": largest_files_info,
                "extensions": extensions,
            }

            stats["total_files"] += len(files)  # type: ignore
            stats["total_size_mb"] += size_mb  # type: ignore
            stats["sizes_by_category"][dir_name] = size_mb  # type: ignore

            # Track all largest files across directories
            for size, f in largest_in_dir:
                stats["largest_files"].append(  # type: ignore
                    {
                        "name": f.name,
                        "size_mb": f"{size / (1024 * 1024):.2f}",
                        "category": dir_name,
                        "path": str(f.relative_to(output_dir)),
                    }
                )
        else:
            stats["directories"][dir_name] = {  # type: ignore
                "exists": False,
                "file_count": 0,
                "size_mb": "0.00",
                "total_size_bytes": 0,
            }
            stats["missing_expected_files"].append(f"{dir_name}/ directory")  # type: ignore

    # Sort largest files by size
    stats["largest_files"] = sorted(  # type: ignore
        stats["largest_files"], key=lambda x: float(x["size_mb"]), reverse=True
    )[:10]  # Keep top 10

    # Check for expected combined PDF
    # Use project basename for file matching (handles nested projects like "cognitive_integrity/cogsec_multiagent_1_theory")  # noqa: E501
    project_basename = Path(project_name).name
    combined_pdf_found = False
    for pdf_name in [f"{project_basename}_combined.pdf", "project_combined.pdf"]:
        pdf_path = output_dir / "pdf" / pdf_name
        if pdf_path.exists():
            combined_pdf_found = True
            break

    if not combined_pdf_found:
        stats["missing_expected_files"].append(  # type: ignore
            f"{project_basename}_combined.pdf or project_combined.pdf"
        )

    # Add file type counts
    all_extensions = {}  # type: ignore
    for dir_info in stats["directories"].values():  # type: ignore
        if dir_info["exists"]:
            for ext, count in dir_info.get("extensions", {}).items():
                all_extensions[ext] = all_extensions.get(ext, 0) + count
    stats["file_counts_by_type"] = all_extensions

    # Add simplified keys for backward compatibility with tests
    stats["pdf_files"] = stats["directories"].get("pdf", {}).get("file_count", 0)  # type: ignore
    stats["figures"] = stats["directories"].get("figures", {}).get("file_count", 0)  # type: ignore
    stats["data_files"] = stats["directories"].get("data", {}).get("file_count", 0)  # type: ignore

    return stats

def generate_detailed_output_report(output_dir: Path, stats: dict[str, Any]) -> str:
    """Generate detailed output statistics report.

    Args:
        output_dir: Path to output directory
        stats: Output statistics dictionary

    Returns:
        Formatted report string
    """
    lines = [
        "",
        "OUTPUT STATISTICS REPORT",
        "=" * 60,
        "",
        f"Output Directory: {output_dir}",
        "",
        f"Total Files: {stats['total_files']}",
        f"Total Size: {stats['total_size_mb']:.2f} MB",
        "",
        "Files by Category:",
    ]

    for dir_name, dir_info in stats["directories"].items():
        if dir_info["exists"] and dir_info["file_count"] > 0:
            lines.append(
                f"  • {dir_name}: {dir_info['file_count']} files ({dir_info['size_mb']} MB)"
            )

    if stats["largest_files"]:
        lines.append("")
        lines.append("Largest Files:")
        for file_info in stats["largest_files"][:5]:
            lines.append(
                f"  • {file_info['name']}: {file_info['size_mb']} MB ({file_info['category']})"
            )

    if stats["missing_expected_files"]:
        lines.append("")
        lines.append("Missing Expected Files:")
        for missing in stats["missing_expected_files"]:
            lines.append(f"  ⚠  {missing}")

    if stats["file_counts_by_type"]:
        lines.append("")
        lines.append("File Types:")
        for ext, count in sorted(
            stats["file_counts_by_type"].items(), key=lambda x: x[1], reverse=True
        )[:10]:
            lines.append(f"  • {ext}: {count} file(s)")

    lines.append("")

    return "\n".join(lines)

# =============================================================================
# LOG ANALYSIS
# =============================================================================

def _collect_log_statistics(log_file: Path) -> dict[str, Any]:
    """Collect statistics from a log file."""
    if not log_file.exists():
        return {"error": "Log file not found", "counts": {}, "total_lines": 0}

    stats: dict[str, Any] = {
        "counts": {"debug": 0, "info": 0, "warning": 0, "error": 0, "critical": 0},
        "total_lines": 0,
        "errors": [],
        "warnings": [],
    }

    try:
        with open(log_file, "r") as f:
            for line in f:
                stats["total_lines"] += 1
                line_lower = line.lower()

                if "debug" in line_lower:
                    stats["counts"]["debug"] += 1
                elif "info" in line_lower:
                    stats["counts"]["info"] += 1
                elif "warning" in line_lower or "warn" in line_lower:
                    stats["counts"]["warning"] += 1
                    if len(stats["warnings"]) < 10:
                        stats["warnings"].append(line.strip())
                elif "error" in line_lower:
                    stats["counts"]["error"] += 1
                    if len(stats["errors"]) < 10:
                        stats["errors"].append(line.strip())
                elif "critical" in line_lower:
                    stats["counts"]["critical"] += 1
                    if len(stats["errors"]) < 10:
                        stats["errors"].append(line.strip())

    except Exception as e:
        stats["error"] = f"Failed to parse log file: {e}"

    return stats

def generate_log_summary(log_file: Path, output_file: Path | None = None) -> str:
    """Generate summary report from log file.

    Args:
        log_file: Path to log file to analyze
        output_file: Optional path to save summary (default: None)

    Returns:
        Formatted summary string
    """
    stats = _collect_log_statistics(log_file)

    if "error" in stats and stats.get("total_lines", 0) == 0:
        return f"Error: {stats['error']}"

    lines = [
        "",
        f"LOG ANALYSIS: {log_file.name}",
        "=" * 60,
        "",
        f"Total Lines: {stats['total_lines']}",
        "",
        "Message Breakdown:",
    ]

    for level, count in stats["counts"].items():
        if count > 0:
            lines.append(f"  {level.upper()}: {count}")

    if stats.get("errors"):
        lines.append("")
        lines.append(f"Recent Errors ({len(stats['errors'])}):")
        for err in stats["errors"][:5]:
            lines.append(f"  • {err[:100]}")

    if stats.get("warnings"):
        lines.append("")
        lines.append(f"Recent Warnings ({len(stats['warnings'])}):")
        for warn in stats["warnings"][:5]:
            lines.append(f"  • {warn[:100]}")

    lines.append("")

    summary_text = "\n".join(lines)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(summary_text)

    return summary_text
