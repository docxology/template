"""Pipeline summary helper functions — stage formatting, path utilities.

Extracted from summary.py to keep each module under 300 LOC.
These helpers are used by summary_formatters.py and summary.py and should not
be imported directly by callers — use summary.py as the entry point.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.files.inventory import FileInventoryEntry
from infrastructure.core.logging.helpers import format_duration
from infrastructure.core.pipeline.executor import PipelineStageResult


def format_stage_result(
    result: PipelineStageResult, total_duration: float, skip_infra: bool
) -> str:
    """Format a single stage result for display.

    Args:
        result: Stage result
        total_duration: Total pipeline duration
        skip_infra: Whether infrastructure tests were skipped

    Returns:
        Formatted stage result string
    """
    if not result.success and result.exit_code == 0:
        # Skipped stage
        return f"\u2298 Stage {result.stage_num}: {result.stage_name} (skipped)"

    duration_formatted = f"{result.duration:.1f}s"
    percentage = (result.duration * 100) / total_duration if total_duration > 0 else 0

    if result.success:
        # Highlight as bottleneck if this stage took more than 10 seconds
        if result.duration > 10:
            return f"\u2713 Stage {result.stage_num}: {result.stage_name} ({duration_formatted}, {percentage:.1f}%) \u26a0 bottleneck"  # noqa: E501
        else:
            return f"\u2713 Stage {result.stage_num}: {result.stage_name} ({duration_formatted}, {percentage:.1f}%)"  # noqa: E501
    else:
        return f"\u2717 Stage {result.stage_num}: {result.stage_name} ({duration_formatted}) FAILED"


def stage_result_to_dict(result: PipelineStageResult | None) -> dict | None:
    """Convert stage result to dictionary.

    Args:
        result: Stage result

    Returns:
        Dictionary representation
    """
    if result is None:
        return None

    return {
        "stage_num": result.stage_num,
        "stage_name": result.stage_name,
        "success": result.success,
        "duration": result.duration,
        "duration_formatted": format_duration(result.duration),
        "exit_code": result.exit_code,
        "error_message": result.error_message,
    }


def get_final_log_path(log_file: Path) -> Path:
    """Get the final log file path after copying.

    Args:
        log_file: Current log file path

    Returns:
        Final log file path
    """
    # Handle paths like "projects/{name}/output/..." -> "output/..."
    parts = log_file.parts
    if "projects" in parts and "output" in parts:
        output_idx = parts.index("output")
        projects_idx = parts.index("projects")
        if projects_idx < output_idx:
            return Path("output").joinpath(*parts[output_idx + 1 :])
    return log_file


def find_base_output_dir(inventory: list[FileInventoryEntry]) -> Path | None:
    """Find the base output directory from inventory.

    Args:
        inventory: File inventory

    Returns:
        Base output directory path
    """
    if not inventory:
        return None

    # Find the most common parent directory
    paths = [entry.path for entry in inventory]
    if not paths:
        return None

    # Start with the first path and find common parent
    common_parent = paths[0].parent
    for path in paths[1:]:
        while not path.is_relative_to(common_parent):
            common_parent = common_parent.parent
            if common_parent == common_parent.parent:  # root
                break

    return common_parent


def extract_project_name_from_path(path: Path) -> str | None:
    """Extract project name from output path.

    Args:
        path: Path containing project name

    Returns:
        Project name
    """
    parts = path.parts
    if "projects" in parts and "output" in parts:
        projects_idx = parts.index("projects")
        output_idx = parts.index("output")
        if projects_idx < output_idx and output_idx > projects_idx + 1:
            return parts[projects_idx + 1]
    return None
