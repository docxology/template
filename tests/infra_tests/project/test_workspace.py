#!/usr/bin/env python3
"""Tests for infrastructure.project.workspace."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.workspace import run_uv_command, show_workspace_status


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


def test_show_workspace_status_without_workspace_table(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    assert show_workspace_status() == 1


def test_show_workspace_status_malformed_pyproject(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[tool.uv.workspace\n", encoding="utf-8")

    assert show_workspace_status() == 1


def test_run_uv_command_reports_missing_binary(tmp_path: Path) -> None:
    missing = tmp_path / "definitely-not-a-command"

    assert run_uv_command([str(missing)], cwd=tmp_path) == 1
