#!/usr/bin/env python3
"""Tests for infrastructure.rendering.preflight (manuscript mermaid preflight)."""

from __future__ import annotations

from pathlib import Path

from infrastructure.rendering.preflight import (
    project_manuscript_has_mermaid,
    puppeteer_cache_has_chrome,
    run_manuscript_preflight,
)


def test_project_manuscript_has_mermaid_detects_fence(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "01.md").write_text("```mermaid\ngraph TD\n  A-->B\n```\n", encoding="utf-8")
    assert project_manuscript_has_mermaid(manuscript) is True


def test_project_manuscript_has_mermaid_absent(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "01.md").write_text("# No diagrams\n", encoding="utf-8")
    assert project_manuscript_has_mermaid(manuscript) is False


def test_project_manuscript_has_mermaid_ignores_doc_only_files(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "AGENTS.md").write_text("```mermaid\ngraph TD\n  A-->B\n```\n", encoding="utf-8")
    (manuscript / "01_section.md").write_text("# Plain\n", encoding="utf-8")
    assert project_manuscript_has_mermaid(manuscript) is False


def test_run_manuscript_preflight_no_mermaid_ok(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "01.md").write_text("# Plain\n", encoding="utf-8")
    ok, message = run_manuscript_preflight(manuscript)
    assert ok is True
    assert message == ""


def test_puppeteer_cache_has_chrome_returns_bool() -> None:
    assert isinstance(puppeteer_cache_has_chrome(), bool)
