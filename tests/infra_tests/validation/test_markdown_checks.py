"""Tests for infrastructure/validation/output/markdown_checks.py.

Covers the Stage-4 markdown wrapper's advisory-vs-breakage semantics:
- missing/empty manuscript dirs and clean validation pass return True
- advisory validation notes return True (non-critical)
- genuine validator breakage (ImportError / OSError / RuntimeError) returns
  False so the failure is surfaced in the Stage-4 summary instead of being
  silently reported as PASSED (VAL-5).

Follows No Mocks Policy — real files + tmp_path; monkeypatch only to inject a
real recording callable / raising stub in place of the underlying validator.
"""

from __future__ import annotations

import builtins

import pytest

import infrastructure.validation.output.markdown_checks as checks
from infrastructure.validation.output.markdown_checks import (
    validate_manuscript_output_markdown,
)


def _make_project(tmp_path):
    project_root = tmp_path / "project"
    manuscript = project_root / "manuscript"
    manuscript.mkdir(parents=True)
    (project_root / "output").mkdir(parents=True)
    return project_root


def test_missing_manuscript_dir_returns_true(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    assert validate_manuscript_output_markdown(project_root, tmp_path, "demo") is True


def test_empty_manuscript_dir_returns_true(tmp_path):
    project_root = _make_project(tmp_path)
    assert validate_manuscript_output_markdown(project_root, tmp_path, "demo") is True


def test_clean_markdown_returns_true(tmp_path, monkeypatch):
    project_root = _make_project(tmp_path)
    (project_root / "manuscript" / "01_intro.md").write_text("# Intro\n\nHi.")

    def fake_validate_md(directory, repo_root, strict=False):
        return [], 0

    monkeypatch.setattr(
        "infrastructure.validation.content.markdown_validator.validate_markdown",
        fake_validate_md,
    )
    assert validate_manuscript_output_markdown(project_root, tmp_path, "demo") is True


def test_advisory_notes_return_true(tmp_path, monkeypatch):
    """Validation notes are advisory: the check still passes (True)."""
    from infrastructure.core.logging.diagnostic import (
        DiagnosticEvent,
        DiagnosticSeverity,
    )

    project_root = _make_project(tmp_path)
    (project_root / "manuscript" / "01_intro.md").write_text("# Intro\n\nHi.")

    note = DiagnosticEvent(
        severity=DiagnosticSeverity.WARNING,
        category="markdown",
        message="advisory note",
        file_path="01_intro.md",
    )

    def fake_validate_md(directory, repo_root, strict=False):
        return [note], 1

    monkeypatch.setattr(
        "infrastructure.validation.content.markdown_validator.validate_markdown",
        fake_validate_md,
    )
    assert validate_manuscript_output_markdown(project_root, tmp_path, "demo") is True


def test_import_error_returns_false(tmp_path, monkeypatch):
    """A broken validator import is genuine breakage -> False (VAL-5)."""
    project_root = _make_project(tmp_path)
    (project_root / "manuscript" / "01_intro.md").write_text("# Intro\n\nHi.")

    real_import = builtins.__import__

    def raising_import(name, *args, **kwargs):
        if name == "infrastructure.validation.content.markdown_validator":
            raise ImportError("validator unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", raising_import)
    assert validate_manuscript_output_markdown(project_root, tmp_path, "demo") is False


def test_runtime_error_returns_false(tmp_path, monkeypatch):
    """A validator that raises mid-run is broken -> False (VAL-5)."""
    project_root = _make_project(tmp_path)
    (project_root / "manuscript" / "01_intro.md").write_text("# Intro\n\nHi.")

    def boom(directory, repo_root, strict=False):
        raise RuntimeError("validator exploded")

    monkeypatch.setattr(
        "infrastructure.validation.content.markdown_validator.validate_markdown",
        boom,
    )
    assert validate_manuscript_output_markdown(project_root, tmp_path, "demo") is False


def test_os_error_returns_false(tmp_path, monkeypatch):
    project_root = _make_project(tmp_path)
    (project_root / "manuscript" / "01_intro.md").write_text("# Intro\n\nHi.")

    def boom(directory, repo_root, strict=False):
        raise OSError("disk gone")

    monkeypatch.setattr(
        "infrastructure.validation.content.markdown_validator.validate_markdown",
        boom,
    )
    assert validate_manuscript_output_markdown(project_root, tmp_path, "demo") is False


@pytest.mark.parametrize("exc", [ValueError, AttributeError])
def test_value_and_attribute_errors_return_false(tmp_path, monkeypatch, exc):
    project_root = _make_project(tmp_path)
    (project_root / "manuscript" / "01_intro.md").write_text("# Intro\n\nHi.")

    def boom(directory, repo_root, strict=False):
        raise exc("bad")

    monkeypatch.setattr(
        "infrastructure.validation.content.markdown_validator.validate_markdown",
        boom,
    )
    assert validate_manuscript_output_markdown(project_root, tmp_path, "demo") is False


def test_module_logger_is_used():
    """Sanity: module exposes a logger (no bare prints)."""
    assert checks.logger is not None
