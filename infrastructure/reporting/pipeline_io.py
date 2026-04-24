"""Pipeline I/O utilities for saving reports, errors, and validation results.

Provides atomic file writing helpers and report serialization functions.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger

from .pipeline_markdown import _generate_pipeline_markdown
from .pipeline_html import generate_html_report
from .pipeline_report_model import PipelineReport

logger = get_logger(__name__)


def _atomic_write_json(path: Path, data: dict[str, Any], **dump_kwargs: Any) -> None:
    """Write *data* as JSON to *path* atomically via a .tmp intermediate file."""
    _tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(_tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, **dump_kwargs)
        _tmp.replace(path)
    except (OSError, ValueError):
        _tmp.unlink(missing_ok=True)
        raise


def _atomic_write_text(path: Path, content: str) -> None:
    """Write *content* as text to *path* atomically via a .tmp intermediate file."""
    _tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        _tmp.write_text(content)
        _tmp.replace(path)
    except OSError:
        _tmp.unlink(missing_ok=True)
        raise


def save_pipeline_report(
    report: PipelineReport, output_dir: Path, formats: list[str] | None = None
) -> dict[str, Path]:
    """Save pipeline report in multiple formats; returns dict mapping format to path.

    Raises:
        OSError: On the first write failure. The exception has an ``already_saved``
            attribute (``dict[str, Path]``) containing formats that were successfully
            written before the failure, so callers can inspect partial output.
    """
    if formats is None:
        formats = ["json", "html", "markdown"]

    from dataclasses import asdict

    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files = {}

    report_dict = {
        "timestamp": report.timestamp,
        "total_duration": report.total_duration,
        "stages": [asdict(stage) for stage in report.stages],
        "test_results": report.test_results,
        "validation_results": report.validation_results,
        "performance_metrics": report.performance_metrics,
        "error_summary": report.error_summary,
        "output_statistics": report.output_statistics,
    }

    formats_to_write = []
    if "json" in formats:
        formats_to_write.append(
            ("json", output_dir / "pipeline_report.json", json.dumps(report_dict, indent=2))
        )
    if "markdown" in formats:
        formats_to_write.append(
            ("markdown", output_dir / "pipeline_report.md", _generate_pipeline_markdown(report))
        )
    if "html" in formats:
        formats_to_write.append(
            ("html", output_dir / "pipeline_report.html", generate_html_report(report))
        )

    for fmt, path, content in formats_to_write:
        try:
            _atomic_write_text(path, content)
            saved_files[fmt] = path
            logger.info(f"Pipeline report ({fmt.upper()}) saved: {path}")
        except OSError as e:
            logger.error(f"Failed to write {fmt.upper()} report {path}: {e}")
            # Attach already-written files so callers can inspect partial output
            e.already_saved = saved_files  # type: ignore[attr-defined]
            raise

    return saved_files


def save_test_results(test_results: dict[str, Any], output_dir: Path) -> Path:
    """Write test_results dict to test_results.json and return the path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "test_results.json"
    _atomic_write_json(report_path, test_results, default=str)
    return report_path


def save_validation_report(
    validation_results: dict[str, Any], output_dir: Path
) -> dict[str, Path]:
    """Generate validation report as JSON and Markdown; returns paths by format key."""
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files = {}

    # Stamp generation time so downstream consumers (CI dashboards, manuscript
    # variables, jq filters) can sort/age reports without parsing the markdown
    # twin. Mirrors the ``**Generated:**`` line in generate_validation_markdown.
    # Overwrite explicit None (e.g. callers pre-allocating a placeholder) as
    # well as missing keys; a null timestamp is never useful downstream.
    if not validation_results.get("timestamp"):
        validation_results["timestamp"] = datetime.now().isoformat()

    json_path = output_dir / "validation_report.json"
    try:
        _atomic_write_json(json_path, validation_results)
        saved_files["json"] = json_path
    except OSError as e:
        logger.error(f"Failed to write validation JSON {json_path}: {e}")
        raise

    md_path = output_dir / "validation_report.md"
    try:
        _atomic_write_text(md_path, generate_validation_markdown(validation_results))
        saved_files["markdown"] = md_path
    except OSError as e:
        logger.error(f"Failed to write validation Markdown {md_path}: {e}")
        raise

    return saved_files


def generate_validation_markdown(results: dict[str, Any]) -> str:
    """Return Markdown-formatted validation report for the given results dict."""
    lines = [
        "# Validation Report",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
    ]

    # Add validation details
    if "checks" in results:
        lines.append("## Validation Checks")
        lines.append("")
        for check_name, check_result in results["checks"].items():
            status = "\u2705 PASS" if check_result else "\u274c FAIL"
            lines.append(f"- {status}: {check_name}")
        lines.append("")

    return "\n".join(lines)


def save_performance_report(performance_metrics: dict[str, Any], output_dir: Path) -> Path:
    """Write performance_metrics dict to performance_report.json and return the path."""
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "performance_report.json"
    try:
        _atomic_write_json(json_path, performance_metrics)
    except OSError as e:
        logger.error(f"Failed to write performance report {json_path}: {e}")
        raise

    return json_path


def save_error_summary(errors: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    """Aggregate errors, write JSON and Markdown reports, and return the summary dict."""
    output_dir.mkdir(parents=True, exist_ok=True)

    by_type: dict[str, list[dict[str, Any]]] = {}
    for error in errors:
        error_type = error.get("type", "unknown")
        if error_type not in by_type:
            by_type[error_type] = []
        by_type[error_type].append(error)

    summary = {
        "total_errors": len(errors),
        "errors_by_type": {k: len(v) for k, v in by_type.items()},
        "errors": errors,
    }

    json_path = output_dir / "error_summary.json"
    try:
        _atomic_write_json(json_path, summary)
    except OSError as e:
        logger.error(f"Failed to write error summary JSON {json_path}: {e}")
        raise

    md_path = output_dir / "error_summary.md"
    try:
        _atomic_write_text(md_path, generate_error_markdown(summary))
    except OSError as e:
        logger.error(f"Failed to write error summary Markdown {md_path}: {e}")
        raise

    return summary


def generate_error_markdown(summary: dict[str, Any]) -> str:
    """Generate Markdown error summary."""
    lines = [
        "# Error Summary",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
        f"**Total Errors:** {summary.get('total_errors', 0)}",
        "",
    ]

    if summary.get("errors_by_type"):
        lines.append("## Errors by Type")
        lines.append("")
        for error_type, count in summary["errors_by_type"].items():
            lines.append(f"- **{error_type}:** {count}")
        lines.append("")

    if summary.get("errors"):
        lines.append("## Error Details")
        lines.append("")
        for i, error in enumerate(summary["errors"][:10], 1):  # Limit to first 10
            lines.append(f"### Error {i}")
            lines.append(f"- **Type:** {error.get('type', 'unknown')}")
            lines.append(f"- **Message:** {error.get('message', 'N/A')}")
            if error.get("file"):
                lines.append(f"- **File:** {error.get('file')}")
            if error.get("suggestions"):
                lines.append("- **Suggestions:**")
                for suggestion in error.get("suggestions", []):
                    lines.append(f"  - {suggestion}")
            lines.append("")

        if len(summary["errors"]) > 10:
            lines.append(f"*... and {len(summary['errors']) - 10} more errors*")

    return "\n".join(lines)
