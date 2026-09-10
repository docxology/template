"""No-op resolution and dry-run behavior tests (formerly part of test_linking.py)."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.project.linking import ENV_VAR, sync_private_project_links

from ._linking_helpers import _make_private, _make_repo


def test_noop_when_no_private_root(tmp_path: Path, monkeypatch) -> None:
    repo = _make_repo(tmp_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    result = sync_private_project_links(repo)  # auto-resolve, nothing present
    assert result.private_root is None
    assert not result.changed
    assert list(repo.joinpath("projects").iterdir()) == []


def test_dry_run_makes_no_changes(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    result = sync_private_project_links(repo, private, dry_run=True)
    assert result.created == ["projects/active/alpha"]
    assert not (repo / "projects" / "active" / "alpha").exists()  # nothing written


def test_link_projects_cli_dry_run_reports_without_linking(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The public CLI exposes the same dry-run/no-write contract."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    monkeypatch.setenv(ENV_VAR, str(private))

    from infrastructure.orchestration.cli import main as orchestration_main

    rc = orchestration_main(["--repo-root", str(repo), "link-projects", "--dry-run"])
    captured = capsys.readouterr()

    assert rc == 0
    assert "+ projects/active/alpha" in captured.out
    assert not (repo / "projects" / "active" / "alpha").exists()
