"""Tests for infrastructure.rendering.pipeline (pure-logic functions).

Covers _resolve_manuscript_dir, _log_manuscript_composition,
_run_override_script, and _validate_latex_packages without invoking LaTeX
and without using any mocking framework.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.rendering.latex_validation import ValidationReport
from infrastructure.rendering.pipeline import (
    _log_manuscript_composition,
    _resolve_manuscript_dir,
    _run_override_script,
    _validate_latex_packages,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_report(
    *,
    all_required: bool = True,
    missing_req: list[str] | None = None,
    missing_opt: list[str] | None = None,
) -> ValidationReport:
    """Build a real ValidationReport dataclass for testing _validate_latex_packages."""
    return ValidationReport(
        required_packages=[],
        optional_packages=[],
        missing_required=missing_req or [],
        missing_optional=missing_opt or [],
        all_required_available=all_required,
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
# _run_override_script  (real subprocess — no mocking)
# ---------------------------------------------------------------------------


def test_run_override_script_success(tmp_path: Path) -> None:
    """Returns 0 when a real override script exits successfully."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("import sys\nsys.exit(0)\n")

    result = _run_override_script(tmp_path, override)

    assert result == 0


def test_run_override_script_failure(tmp_path: Path) -> None:
    """Returns non-zero when a real override script exits with error."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("import sys\nsys.exit(1)\n")

    result = _run_override_script(tmp_path, override)

    assert result == 1


def test_run_override_script_non_zero_exit_code(tmp_path: Path) -> None:
    """Returns the specific non-zero exit code from the override script."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("import sys\nsys.exit(42)\n")

    result = _run_override_script(tmp_path, override)

    assert result == 42


def test_run_override_script_subprocess_error(tmp_path: Path) -> None:
    """Returns 1 when the script cannot be executed (non-Python binary content)."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    # Write a script that immediately raises a SyntaxError so the interpreter
    # exits non-zero — this exercises the failure path without needing OSError.
    override.write_bytes(b"\x00\x01\x02\x03\xff\xfe")  # Invalid UTF-8 / binary

    result = _run_override_script(tmp_path, override)

    # A binary file run through Python will fail (exit non-zero or raise)
    assert result != 0


# ---------------------------------------------------------------------------
# _validate_latex_packages  (real ValidationReport instances — no mocking)
# ---------------------------------------------------------------------------


def test_validate_latex_packages_all_available() -> None:
    """Returns 0 when all required packages are available."""
    result = _validate_latex_packages(report=_make_report(all_required=True))

    assert result == 0


def test_validate_latex_packages_missing_required() -> None:
    """Returns 1 when required packages are missing."""
    result = _validate_latex_packages(
        report=_make_report(all_required=False, missing_req=["multirow", "cleveref"])
    )

    assert result == 1


def test_validate_latex_packages_optional_missing_still_passes() -> None:
    """Returns 0 even when optional packages are absent."""
    result = _validate_latex_packages(
        report=_make_report(all_required=True, missing_opt=["minted"])
    )

    assert result == 0


def test_validate_latex_packages_empty_report() -> None:
    """Returns 0 for an all-clean report with no packages at all."""
    result = _validate_latex_packages(report=_make_report())

    assert result == 0


def test_validate_latex_packages_multiple_missing_required() -> None:
    """Returns 1 with multiple missing required packages."""
    result = _validate_latex_packages(
        report=_make_report(
            all_required=False,
            missing_req=["multirow", "cleveref", "doi", "newunicodechar"],
        )
    )

    assert result == 1


def test_validate_latex_packages_os_error_is_non_fatal() -> None:
    """Returns 0 (proceed anyway) when report=None and validator raises OSError.

    This test calls _validate_latex_packages() with no report so it runs the
    live validate_preamble_packages path.  On systems without kpsewhich the
    OSError handler returns 0 (non-fatal).  On systems with LaTeX installed
    the function also returns 0 (all packages available) or 1 (missing).
    Either way the function must not raise.
    """
    result = _validate_latex_packages()

    assert result in (0, 1)
