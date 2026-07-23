"""Additional tests for infrastructure/project/workspace.py.

Targets subprocess coverage for sync_workspace, add_dependency,
update_workspace, show_workspace_tree, and the run_uv_command
error/timeout branches. Uses real subprocess calls and real files.
"""

from __future__ import annotations

from pathlib import Path


from infrastructure.project.workspace import (
    add_dependency,
    run_uv_command,
    show_workspace_status,
    show_workspace_tree,
    sync_workspace,
    update_workspace,
)


def test_run_uv_command_success(tmp_path: Path) -> None:
    """A real command that exits 0 returns 0."""
    assert run_uv_command(["true"], cwd=tmp_path) == 0


def test_run_uv_command_failure(tmp_path: Path) -> None:
    """A real command that exits non-zero returns that exit code."""
    assert run_uv_command(["false"], cwd=tmp_path) == 1


def test_run_uv_command_missing_binary_returns_1(tmp_path: Path) -> None:
    """OSError (binary not found) is caught and returns 1."""
    missing = tmp_path / "definitely-not-a-command"
    assert run_uv_command([str(missing)], cwd=tmp_path) == 1


def test_sync_workspace_reports_uv_missing(tmp_path: Path, monkeypatch) -> None:
    """When uv is not on PATH, sync_workspace returns 1."""
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    assert sync_workspace() == 1


def test_add_dependency_missing_project_dir(tmp_path: Path, monkeypatch) -> None:
    """add_dependency returns 1 when the project directory does not exist."""
    monkeypatch.chdir(tmp_path)
    result = add_dependency("nonexistent-package", "nonexistent_project")
    assert result == 1


def test_add_dependency_reports_uv_missing(tmp_path: Path, monkeypatch) -> None:
    """When uv is not on PATH, add_dependency returns 1 even for a valid project dir."""
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    (tmp_path / "projects" / "test_proj").mkdir(parents=True)
    result = add_dependency("some-package", "test_proj")
    assert result == 1


def test_update_workspace_reports_uv_missing(tmp_path: Path, monkeypatch) -> None:
    """When uv is not on PATH, update_workspace returns 1."""
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    assert update_workspace() == 1


def test_show_workspace_tree_reports_uv_missing(tmp_path: Path, monkeypatch) -> None:
    """When uv is not on PATH, show_workspace_tree returns non-zero."""
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = show_workspace_tree()
    assert result != 0


def test_show_workspace_status_valid_with_lock(tmp_path: Path, monkeypatch) -> None:
    """Valid workspace config with lock file returns 0."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.uv.workspace]\nmembers = ["projects/a", "projects/b"]\n',
        encoding="utf-8",
    )
    (tmp_path / "uv.lock").write_text("# lock file\n", encoding="utf-8")
    assert show_workspace_status() == 0


def test_show_workspace_status_valid_without_lock(tmp_path: Path, monkeypatch) -> None:
    """Valid workspace config without lock file still returns 0 (just warns)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.uv.workspace]\nmembers = ["projects/a"]\n',
        encoding="utf-8",
    )
    assert show_workspace_status() == 0


def test_show_workspace_status_missing_pyproject(tmp_path: Path, monkeypatch) -> None:
    """Missing pyproject.toml returns 1."""
    monkeypatch.chdir(tmp_path)
    assert show_workspace_status() == 1


def test_show_workspace_status_no_workspace_config(tmp_path: Path, monkeypatch) -> None:
    """pyproject.toml without [tool.uv.workspace] returns 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'demo'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )
    assert show_workspace_status() == 1


def test_show_workspace_status_malformed_pyproject(tmp_path: Path, monkeypatch) -> None:
    """Malformed TOML returns 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[tool.uv.workspace\n", encoding="utf-8")
    assert show_workspace_status() == 1


def test_show_workspace_status_empty_members(tmp_path: Path, monkeypatch) -> None:
    """Workspace with empty members list returns 0."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        "[tool.uv.workspace]\nmembers = []\n",
        encoding="utf-8",
    )
    assert show_workspace_status() == 0
