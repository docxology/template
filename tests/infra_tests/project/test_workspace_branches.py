"""Branch-gap tests for infrastructure/project/workspace.py.

Covers the real subprocess OSError path and the success/failure branches
of the workspace status reader with real pyproject.toml fixtures.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.project import workspace


def test_run_uv_command_returns_one_on_oserror(tmp_path: Path) -> None:
    """A missing/failed executable surfaces as return code 1, not a crash."""

    assert workspace.run_uv_command(["definitely-not-a-real-executable-xyz"], cwd=tmp_path) == 1


def test_show_workspace_status_missing_pyproject(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert workspace.show_workspace_status() == 1


def test_show_workspace_status_without_workspace_section(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "solo"\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert workspace.show_workspace_status() == 1


def test_show_workspace_status_valid_lists_members(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.uv.workspace]\nmembers = ["projects/a", "projects/b"]\n',
        encoding="utf-8",
    )
    (tmp_path / "uv.lock").write_text("lock = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert workspace.show_workspace_status() == 0


def test_show_workspace_status_warns_when_lock_missing(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.uv.workspace]\nmembers = []\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert workspace.show_workspace_status() == 0


def test_sync_and_update_report_real_uv_failure(tmp_path: Path, monkeypatch) -> None:
    """Real uv binary against an empty dir fails; helpers must report nonzero."""

    monkeypatch.chdir(tmp_path)
    assert workspace.sync_workspace() != 0
    assert workspace.update_workspace() != 0
