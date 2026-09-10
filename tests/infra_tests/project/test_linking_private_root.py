"""private_projects_root resolution tests: env override, config file, sibling fallback (formerly part of test_linking.py)."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.linking import (
    CONFIG_FILENAME,
    ENV_VAR,
    REQUIRED_PRIVATE_ROOT_SUBDIRS,
    private_projects_root,
)

from ._linking_helpers import _make_private, _make_repo


def test_private_root_env_takes_precedence(tmp_path: Path, monkeypatch) -> None:
    repo = _make_repo(tmp_path)
    env_root = _make_private(tmp_path, name="env_private")
    monkeypatch.setenv(ENV_VAR, str(env_root))
    assert private_projects_root(repo) == env_root.resolve()


def test_private_root_config_file(tmp_path: Path, monkeypatch) -> None:
    repo = _make_repo(tmp_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    cfg_root = _make_private(tmp_path, name="cfg_private")
    (repo / CONFIG_FILENAME).write_text(str(cfg_root) + "\n", encoding="utf-8")
    assert private_projects_root(repo) == cfg_root.resolve()


def test_private_root_sibling_default(tmp_path: Path, monkeypatch) -> None:
    repo = _make_repo(tmp_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    sibling = _make_private(tmp_path, name="projects")  # tmp_path/projects == repo.parent/projects
    assert private_projects_root(repo) == sibling.resolve()


def test_private_root_none_without_lifecycle_dirs(tmp_path: Path, monkeypatch) -> None:
    repo = _make_repo(tmp_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    # A sibling 'projects' dir without lifecycle subdirs is NOT the private repo.
    (tmp_path / "projects").mkdir()
    assert private_projects_root(repo) is None


def test_sibling_fallback_requires_simplified_signature(tmp_path: Path, monkeypatch) -> None:
    """A coincidental sibling projects/active/ is rejected without working+archive."""
    repo = _make_repo(tmp_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    (tmp_path / "projects" / "active").mkdir(parents=True)  # active/ only
    assert private_projects_root(repo) is None


def test_sibling_fallback_accepts_working_archive_signature(tmp_path: Path, monkeypatch) -> None:
    """The simplified sidecar root is recognized with working/ + archive/."""
    repo = _make_repo(tmp_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    sibling = tmp_path / "projects"
    for sub in REQUIRED_PRIVATE_ROOT_SUBDIRS:
        (sibling / sub).mkdir(parents=True)
    assert private_projects_root(repo) == sibling.resolve()


def test_env_root_accepts_active_only(tmp_path: Path, monkeypatch) -> None:
    """Explicit env override is permissive — active/ alone is enough."""
    repo = _make_repo(tmp_path)
    explicit = tmp_path / "explicit"
    (explicit / "active").mkdir(parents=True)  # no other lifecycle folders
    monkeypatch.setenv(ENV_VAR, str(explicit))
    assert private_projects_root(repo) == explicit.resolve()
