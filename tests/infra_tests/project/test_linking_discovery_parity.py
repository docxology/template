"""Discovery, validation, and import parity through symlinks (formerly part of test_linking.py).

The core promise: linked lifecycle projects are discoverable, validate, and
import through the symlink; legacy and non-active lifecycles stay compatible.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.project.discovery import discover_projects
from infrastructure.project.linking import (
    ARCHIVE_SUBDIR,
    ENV_VAR,
    ONGOING_SUBDIR,
    PROTECTED_NAMES,
    WORKING_SUBDIR,
    sync_active_links,
    sync_private_project_links,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.project.validation import validate_project_structure

from ._linking_helpers import _make_project, _make_private, _make_repo


def test_discovery_finds_linked_project(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["linked_proj"], name="priv")
    sync_private_project_links(repo, private)
    names = {p.name for p in discover_projects(repo)}
    assert "linked_proj" in names


def test_orchestration_list_projects_auto_syncs_private_active(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Every run.sh/orchestration invocation sees private active projects."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["linked_proj"], name="priv")
    monkeypatch.setenv(ENV_VAR, str(private))

    from infrastructure.orchestration.cli import main as orchestration_main

    rc = orchestration_main(["--repo-root", str(repo), "list-projects"])
    captured = capsys.readouterr()

    assert rc == 0
    assert "active/linked_proj" in captured.out.splitlines()
    assert (repo / "projects" / "active" / "linked_proj").is_symlink()


def test_validation_passes_for_symlinked_project(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["linked_proj"], name="priv")
    sync_private_project_links(repo, private)
    ok, msg = validate_project_structure(repo / "projects" / "active" / "linked_proj")
    assert ok, msg


def test_import_resolves_through_symlink(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["linked_proj"], name="priv")
    sync_private_project_links(repo, private)
    # Prove `projects.active.linked_proj.src.calc` imports through the symlink, in
    # a clean subprocess so the test suite's sys.modules/sys.path stay pristine.
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import projects.active.linked_proj.src.calc as m; print(m.answer())",
        ],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "42"


@pytest.mark.parametrize("name", sorted(PROTECTED_NAMES))
def test_protected_names_are_public_exemplars(name: str) -> None:
    public_short_names = {Path(qualified).name for qualified in PUBLIC_PROJECT_NAMES}
    assert name in public_short_names


@pytest.mark.slow
def test_legacy_sync_active_links_wrapper_syncs_all_lifecycles(tmp_path: Path) -> None:
    """The old public function name remains lifecycle-aware for compatibility."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    _make_project(private / WORKING_SUBDIR / "notes")
    _make_project(private / ARCHIVE_SUBDIR / "old")

    result = sync_active_links(repo, private)

    assert result.created == [
        "projects/active/alpha",
        "projects/working/notes",
        "projects/archive/old",
    ]
    assert (repo / "projects" / "active" / "alpha").is_symlink()
    assert (repo / "projects" / "working" / "notes").is_symlink()
    assert (repo / "projects" / "archive" / "old").is_symlink()


@pytest.mark.slow
def test_nonactive_lifecycle_links_are_not_default_discovered(tmp_path: Path) -> None:
    """Working/archive projects are visible locally but not rendered by default."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["linked_proj"], name="priv")
    _make_project(private / WORKING_SUBDIR / "notes")
    _make_project(private / ARCHIVE_SUBDIR / "old")

    sync_private_project_links(repo, private)

    assert (repo / "projects" / "working" / "notes").resolve() == (private / WORKING_SUBDIR / "notes").resolve()
    assert (repo / "projects" / "archive" / "old").resolve() == (private / ARCHIVE_SUBDIR / "old").resolve()
    assert {p.name for p in discover_projects(repo)} == {"linked_proj"}


def test_ongoing_lifecycle_is_linked_but_not_default_discovered(tmp_path: Path) -> None:
    """``ongoing/`` projects (no publication target) are visible but never rendered."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["linked_proj"], name="priv")
    _make_project(private / ONGOING_SUBDIR / "platform")

    result = sync_private_project_links(repo, private)

    assert "projects/ongoing/platform" in result.created
    link = repo / "projects" / "ongoing" / "platform"
    assert link.is_symlink()
    assert link.resolve() == (private / ONGOING_SUBDIR / "platform").resolve()
    # Non-rendered: discovery excludes it, only the active project renders.
    assert {p.name for p in discover_projects(repo)} == {"linked_proj"}


def test_ongoing_qualified_name_resolves(tmp_path: Path) -> None:
    """``resolve_project_root`` resolves the ``ongoing/<name>`` qualified prefix."""
    from infrastructure.core.project_paths import resolve_project_root

    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    _make_project(private / ONGOING_SUBDIR / "platform")
    sync_private_project_links(repo, private)

    resolved = resolve_project_root(repo, "ongoing/platform")
    assert resolved.resolve() == (private / ONGOING_SUBDIR / "platform").resolve()


def test_ongoing_prune_removes_stale_managed_link(tmp_path: Path) -> None:
    """A project leaving ``ongoing/`` has its managed mirror link pruned."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    _make_project(private / ONGOING_SUBDIR / "platform")
    sync_private_project_links(repo, private)
    # platform graduates to a publication target → moves to working/.
    (private / ONGOING_SUBDIR / "platform").rename(private / WORKING_SUBDIR / "platform")
    result = sync_private_project_links(repo, private)
    assert result.removed == ["projects/ongoing/platform"]
    assert not (repo / "projects" / "ongoing" / "platform").is_symlink()
    assert (repo / "projects" / "working" / "platform").is_symlink()
