#!/usr/bin/env python3
"""Tests for infrastructure.project.workspace."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.workspace import show_workspace_status


def test_show_workspace_status_valid(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.uv.workspace]\nmembers = ["projects/a"]\n',
        encoding="utf-8",
    )
    (tmp_path / "uv.lock").write_text("# lock\n", encoding="utf-8")
    assert show_workspace_status() == 0


def test_show_workspace_status_missing_pyproject(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert show_workspace_status() == 1
