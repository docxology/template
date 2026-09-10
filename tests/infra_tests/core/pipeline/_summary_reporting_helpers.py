"""Shared helpers for the split summary-reporting test modules (formerly test_summary_reporting.py)."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.pipeline.types import PipelineStageResult


def _result(
    name: str,
    *,
    stage_num: int = 1,
    success: bool = True,
    duration: float = 1.0,
    exit_code: int = 0,
    error_message: str = "",
) -> PipelineStageResult:
    return PipelineStageResult(
        stage_num=stage_num,
        stage_name=name,
        success=success,
        duration=duration,
        exit_code=exit_code,
        error_message=error_message,
    )


def _make_output_dir(tmp_path: Path, files: dict[str, str] | None = None) -> Path:
    """Create an ``output/`` directory tree with optional files.

    ``files`` maps ``category/filename`` → content. Categories are standard
    output subdirectories (``pdf``, ``data``, ``reports``, etc.).
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)
    if files:
        for rel, content in files.items():
            path = output_dir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    return output_dir
