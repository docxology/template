"""Tests for infrastructure.rendering.pipeline (pure-logic functions).

Covers _resolve_manuscript_dir, _log_manuscript_composition, and
execute_render_pipeline error-path branching without invoking LaTeX.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from infrastructure.rendering.pipeline import (
    _log_manuscript_composition,
    _resolve_manuscript_dir,
    _run_override_script,
    _validate_latex_packages,
)


# ---------------------------------------------------------------------------
# _resolve_manuscript_dir
# ---------------------------------------------------------------------------


def test_resolve_manuscript_dir_uses_injected_when_present(tmp_path: Path) -> None:
    """Prefers output/manuscript/ when it exists and contains .md files."""
    injected = tmp_path / "output" / "manuscript"
    injected.mkdir(parents=True)
    (injected / "01_intro.md").write_text("# Intro")

    result = _resolve_manuscript_dir(tmp_path)

    assert result == injected


def test_resolve_manuscript_dir_falls_back_to_source(tmp_path: Path) -> None:
    """Falls back to manuscript/ when injected dir is absent."""
    result = _resolve_manuscript_dir(tmp_path)

    assert result == tmp_path / "manuscript"


def test_resolve_manuscript_dir_falls_back_when_injected_empty(tmp_path: Path) -> None:
    """Falls back to source when injected dir exists but has no .md files."""
    injected = tmp_path / "output" / "manuscript"
    injected.mkdir(parents=True)
    # directory exists but no .md files

    result = _resolve_manuscript_dir(tmp_path)

    assert result == tmp_path / "manuscript"


def test_resolve_manuscript_dir_ignores_non_md_files_in_injected(tmp_path: Path) -> None:
    """Falls back to source when injected dir has only non-.md files."""
    injected = tmp_path / "output" / "manuscript"
    injected.mkdir(parents=True)
    (injected / "notes.txt").write_text("just a note")

    result = _resolve_manuscript_dir(tmp_path)

    assert result == tmp_path / "manuscript"


# ---------------------------------------------------------------------------
# _log_manuscript_composition
# ---------------------------------------------------------------------------


def test_log_manuscript_composition_mixed_files(tmp_path: Path) -> None:
    """Logs without error for a mix of .md and .tex files."""
    md1 = tmp_path / "01_intro.md"
    md1.write_text("# Intro section")
    md2 = tmp_path / "02_methods.md"
    md2.write_text("# Methods section")
    tex = tmp_path / "preamble.tex"
    tex.write_text(r"\documentclass{article}")

    # Should not raise
    _log_manuscript_composition([md1, md2, tex])


def test_log_manuscript_composition_only_md(tmp_path: Path) -> None:
    """Handles markdown-only file list without error."""
    md = tmp_path / "01_abstract.md"
    md.write_text("Abstract content")

    _log_manuscript_composition([md])


def test_log_manuscript_composition_empty(tmp_path: Path) -> None:
    """Handles empty source file list without error."""
    _log_manuscript_composition([])


# ---------------------------------------------------------------------------
# _run_override_script
# ---------------------------------------------------------------------------


def test_run_override_script_success(tmp_path: Path) -> None:
    """Returns 0 when subprocess exits successfully."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("# override")

    with patch("infrastructure.rendering.pipeline.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch(
            "infrastructure.core.runtime.environment.get_python_command",
            return_value=["python3"],
        ):
            result = _run_override_script(tmp_path, override)

    assert result == 0


def test_run_override_script_failure(tmp_path: Path) -> None:
    """Returns non-zero when subprocess exits with error."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("# override")

    with patch("infrastructure.rendering.pipeline.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        with patch(
            "infrastructure.core.runtime.environment.get_python_command",
            return_value=["python3"],
        ):
            result = _run_override_script(tmp_path, override)

    assert result == 1


def test_run_override_script_subprocess_error(tmp_path: Path) -> None:
    """Returns 1 when subprocess raises OSError."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("# override")

    with patch(
        "infrastructure.rendering.pipeline.subprocess.run",
        side_effect=OSError("no such file"),
    ):
        with patch(
            "infrastructure.core.runtime.environment.get_python_command",
            return_value=["python3"],
        ):
            result = _run_override_script(tmp_path, override)

    assert result == 1


# ---------------------------------------------------------------------------
# _validate_latex_packages
# ---------------------------------------------------------------------------


def test_validate_latex_packages_all_available() -> None:
    """Returns 0 when all required packages are available."""
    mock_report = MagicMock()
    mock_report.all_required_available = True
    mock_report.missing_optional = []

    with patch(
        "infrastructure.rendering.pipeline.validate_preamble_packages",
        return_value=mock_report,
    ):
        result = _validate_latex_packages()

    assert result == 0


def test_validate_latex_packages_missing_required() -> None:
    """Returns 1 when required packages are missing."""
    mock_report = MagicMock()
    mock_report.all_required_available = False
    mock_report.missing_required = ["multirow", "cleveref"]

    with patch(
        "infrastructure.rendering.pipeline.validate_preamble_packages",
        return_value=mock_report,
    ):
        result = _validate_latex_packages()

    assert result == 1


def test_validate_latex_packages_os_error_is_non_fatal() -> None:
    """Returns 0 (proceed anyway) when the validator raises OSError."""
    with patch(
        "infrastructure.rendering.pipeline.validate_preamble_packages",
        side_effect=OSError("tlmgr not found"),
    ):
        result = _validate_latex_packages()

    assert result == 0


def test_validate_latex_packages_optional_missing_still_passes() -> None:
    """Returns 0 even when optional packages are absent."""
    mock_report = MagicMock()
    mock_report.all_required_available = True
    mock_report.missing_optional = ["minted"]

    with patch(
        "infrastructure.rendering.pipeline.validate_preamble_packages",
        return_value=mock_report,
    ):
        result = _validate_latex_packages()

    assert result == 0
