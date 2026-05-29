"""LaTeX log parsing helpers for PDF rendering."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def check_latex_log_for_graphics_errors(log_file: Path) -> dict[str, list[str]]:
    """Parse LaTeX log file for graphics-related errors and warnings."""
    result: dict[str, list[str]] = {
        "graphics_errors": [],
        "graphics_warnings": [],
        "missing_files": [],
    }

    if not log_file.exists():
        return result

    try:
        log_content = log_file.read_text(errors="ignore")

        file_not_found = re.findall(r"File `([^`]+)` not found", log_content)
        result["missing_files"].extend(file_not_found)

        graphics_warnings = re.findall(
            r"((?:Package graphics|Graphics Error).*?)(?=\n(?:!|\s*$))",
            log_content,
            re.IGNORECASE,
        )
        result["graphics_warnings"].extend(graphics_warnings)

        if r"\includegraphics" in log_content and "Undefined" in log_content:
            result["graphics_errors"].append("includegraphics command undefined - graphicx package may not be loaded")

        return result

    except (OSError, UnicodeDecodeError) as exc:
        logger.warning("Error parsing LaTeX log: %s", exc)
        return result


def parse_missing_latex_package_from_log(log_file: Path) -> str | None:
    """Parse LaTeX log for missing package errors."""
    if not log_file.exists():
        return None

    try:
        log_content = log_file.read_text(encoding="utf-8", errors="ignore")

        match = re.search(r"File `([^']+\.sty)' not found", log_content)
        if match:
            return match.group(1).replace(".sty", "")

        match = re.search(r"! LaTeX Error: File `?([^'`\s]+\.sty)'? not found", log_content)
        if match:
            return match.group(1).replace(".sty", "")

    except OSError as exc:
        logger.debug("Error parsing log file for package errors: %s", exc)

    return None


__all__ = ["check_latex_log_for_graphics_errors", "parse_missing_latex_package_from_log"]
