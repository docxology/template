"""Log file analysis and summary generation.

This module provides functions for collecting statistics from log files
and generating human-readable log summary reports.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def _collect_log_statistics(log_file: Path) -> dict[str, Any]:
    """Collect statistics from a log file.

    Raises:
        FileNotFoundError: If log_file does not exist.
        OSError: If the file cannot be read.
        UnicodeDecodeError: If the file contains invalid text.
    """
    if not log_file.exists():
        raise FileNotFoundError(f"Log file not found: {log_file}")

    stats: dict[str, Any] = {
        "counts": {"debug": 0, "info": 0, "warning": 0, "error": 0, "critical": 0},
        "total_lines": 0,
        "errors": [],
        "warnings": [],
    }

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

    return stats


def generate_log_summary(log_file: Path, output_file: Path | None = None) -> str:
    """Generate summary report from log file.

    Args:
        log_file: Path to log file to analyze
        output_file: Optional path to save summary (default: None)

    Returns:
        Formatted summary string.

    Raises:
        OSError: If the log file cannot be read.
    """
    stats = _collect_log_statistics(log_file)

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
