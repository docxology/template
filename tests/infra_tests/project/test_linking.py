#!/usr/bin/env python3
"""Tests for :mod:`infrastructure.project.linking` (no mocks — real symlinks).

Every test uses ``tmp_path`` with real directories and real symlinks. The
safety-critical guarantee under test is that pruning only ever removes lifecycle
links the syncer itself manages and never a real directory, an unmanaged
symlink, or a protected exemplar.

The private companion repo carries five lifecycle folders
(``active``/``working``/``published``/``archive``/``other``); each mirrors into a
same-named *typed subfolder* under ``projects/`` (``projects/active/<name>``,
``projects/working/<name>``, …). Only ``active`` is rendered by default.
"""

from __future__ import annotations

import subprocess
import sys
import os
from collections.abc import Sequence
from pathlib import Path

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.project.linking import (
    ACTIVE_SUBDIR,
    ARCHIVE_SUBDIR,
    CONFIG_FILENAME,
    ENV_VAR,
    LIFECYCLE_SUBDIRS,
    PROTECTED_NAMES,
    WORKING_SUBDIR,
    is_managed_symlink,
    private_projects_root,
    sync_active_links,
    sync_private_project_links,
)
from infrastructure.project.validation import validate_project_structure


# --- fixtures ---------------------------------------------------------------


def _make_repo(tmp_path: Path) -> Path:
    """A template repo root with a real projects/ dir."""
    repo = tmp_path / "template"
    (repo / "projects").mkdir(parents=True)
    return repo


def _make_private(tmp_path: Path, *, active: Sequence[str] = (), name: str = "projects") -> Path:
    """A private companion repo with the full five-folder lifecycle signature."""
    private = tmp_path / name
    for sub in LIFECYCLE_SUBDIRS:
        (private / sub).mkdir(parents=True)
    for proj in active:
        _make_project(private / ACTIVE_SUBDIR / proj)
    return private


def _make_project(path: Path) -> Path:
    """A minimal valid project (src/ with a .py + tests/)."""
    (path / "src").mkdir(parents=True)
    (path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (path / "src" / "calc.py").write_text("def answer() -> int:\n    return 42\n", encoding="utf-8")
    (path / "tests").mkdir()
    (path / "tests" / "__init__.py").write_text("", encoding="utf-8")
    return path


def _mirror(repo: Path, lifecycle: str = ACTIVE_SUBDIR) -> Path:
    """Ensure (and return) the local mirror dir ``projects/<lifecycle>``."""
    mirror = repo / "projects" / lifecycle
    mirror.mkdir(parents=True, exist_ok=True)
    return mirror


# --- private_projects_root --------------------------------------------------


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


def test_private_root_none_when_no_active(tmp_path: Path, monkeypatch) -> None:
    repo = _make_repo(tmp_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    # A sibling 'projects' dir without an active/ subdir is NOT the private repo.
    (tmp_path / "projects").mkdir()
    assert private_projects_root(repo) is None


def test_sibling_fallback_requires_full_lifecycle(tmp_path: Path, monkeypatch) -> None:
    """A coincidental sibling projects/active/ (no full lifecycle) is rejected."""
    repo = _make_repo(tmp_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    (tmp_path / "projects" / "active").mkdir(parents=True)  # active/ only
    assert private_projects_root(repo) is None


def test_env_root_accepts_active_only(tmp_path: Path, monkeypatch) -> None:
    """Explicit env override is permissive — active/ alone is enough."""
    repo = _make_repo(tmp_path)
    explicit = tmp_path / "explicit"
    (explicit / "active").mkdir(parents=True)  # no other lifecycle folders
    monkeypatch.setenv(ENV_VAR, str(explicit))
    assert private_projects_root(repo) == explicit.resolve()


# --- sync_private_project_links: creation / idempotency ---------------------


def test_sync_creates_symlink(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    result = sync_private_project_links(repo, private)
    link = repo / "projects" / "active" / "alpha"
    assert link.is_symlink()
    assert result.created == ["projects/active/alpha"]


def test_created_symlink_resolves_to_source(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_private_project_links(repo, private)
    link = repo / "projects" / "active" / "alpha"
    assert link.resolve() == (private / ACTIVE_SUBDIR / "alpha").resolve()


def test_active_lifecycle_entry_can_be_symlink_to_self_versioned_repo(tmp_path: Path) -> None:
    """A private lifecycle entry may point at a sibling canonical git checkout."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    canonical = _make_project(tmp_path / "AGEINT")
    (private / ACTIVE_SUBDIR / "AGEINT").symlink_to(canonical, target_is_directory=True)

    result = sync_private_project_links(repo, private)
    link = repo / "projects" / "active" / "AGEINT"

    assert result.created == ["projects/active/AGEINT"]
    assert link.is_symlink()
    assert link.resolve() == canonical.resolve()
    assert {p.name for p in discover_projects(repo)} == {"AGEINT"}


def test_sync_is_idempotent(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha", "beta"], name="priv")
    sync_private_project_links(repo, private)
    second = sync_private_project_links(repo, private)
    assert second.created == []
    assert second.updated == []
    assert second.removed == []


# --- sync_private_project_links: prune safety -------------------------------


def test_prune_removes_stale_managed_link(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_private_project_links(repo, private)
    # alpha leaves active/ (e.g. moved to working/)
    (private / ACTIVE_SUBDIR / "alpha").rename(private / WORKING_SUBDIR / "alpha")
    result = sync_private_project_links(repo, private)
    assert result.removed == ["projects/active/alpha"]
    assert not (repo / "projects" / "active" / "alpha").exists()
    assert not (repo / "projects" / "active" / "alpha").is_symlink()
    assert (repo / "projects" / "working" / "alpha").is_symlink()


def test_prune_leaves_unmanaged_symlink(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    # A symlink to somewhere OUTSIDE the private root must never be pruned.
    outside = tmp_path / "outside_target"
    outside.mkdir()
    foreign = _mirror(repo) / "foreign"
    foreign.symlink_to(outside)
    result = sync_private_project_links(repo, private)
    assert "projects/active/foreign" not in result.removed
    assert foreign.is_symlink()


def test_prune_never_touches_real_directory(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    # A real directory under the active mirror (e.g. a native project).
    real = repo / "projects" / "active" / "native_proj"
    _make_project(real)
    sync_private_project_links(repo, private)
    assert real.is_dir() and not real.is_symlink()
    assert (real / "src" / "calc.py").exists()


def test_no_prune_keeps_stale_link(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_private_project_links(repo, private)
    (private / ACTIVE_SUBDIR / "alpha").rename(private / ARCHIVE_SUBDIR / "alpha")
    result = sync_private_project_links(repo, private, prune=False)
    assert result.removed == []
    # The now-broken symlink survives (prune disabled).
    assert (repo / "projects" / "active" / "alpha").is_symlink()
    assert (repo / "projects" / "archive" / "alpha").is_symlink()


def test_repoint_managed_stale_symlink(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    # A MANAGED link (points into active/) but at a stale/missing target.
    link = _mirror(repo) / "alpha"
    link.symlink_to(private / ACTIVE_SUBDIR / "ghost")
    result = sync_private_project_links(repo, private)
    assert result.updated == ["projects/active/alpha"]
    assert link.resolve() == (private / ACTIVE_SUBDIR / "alpha").resolve()


def test_source_symlink_uses_lifecycle_entry_and_prunes(tmp_path: Path) -> None:
    """Self-versioned source repos still get lifecycle-managed links."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    external = tmp_path / "external_notes"
    _make_project(external)
    lifecycle_entry = private / WORKING_SUBDIR / "notes"
    lifecycle_entry.symlink_to(external)

    result = sync_private_project_links(repo, private)
    link = repo / "projects" / "working" / "notes"

    assert result.created == ["projects/working/notes"]
    assert Path(os.readlink(link)) == lifecycle_entry
    assert link.resolve() == external.resolve()

    lifecycle_entry.unlink()
    second = sync_private_project_links(repo, private)
    assert second.removed == ["projects/working/notes"]
    assert not link.is_symlink()


def test_old_direct_self_versioned_link_is_repointed_to_lifecycle_entry(tmp_path: Path) -> None:
    """Links made by the old resolved-target behavior are normalized."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    external = tmp_path / "external_alpha"
    _make_project(external)
    lifecycle_entry = private / ACTIVE_SUBDIR / "alpha"
    lifecycle_entry.symlink_to(external)
    old_link = _mirror(repo) / "alpha"
    old_link.symlink_to(external)

    result = sync_private_project_links(repo, private)

    assert result.updated == ["projects/active/alpha"]
    assert Path(os.readlink(old_link)) == lifecycle_entry
    assert old_link.resolve() == external.resolve()


def test_unmanaged_symlink_collision_not_clobbered(tmp_path: Path) -> None:
    """Forge finding #3: a foreign same-named symlink must not be repointed."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    external = tmp_path / "external_alpha"
    _make_project(external)
    link = _mirror(repo) / "alpha"
    link.symlink_to(external)  # points OUTSIDE the private root
    result = sync_private_project_links(repo, private)
    assert any("alpha" in s and "unmanaged" in s for s in result.skipped)
    assert link.resolve() == external.resolve()  # left untouched


def test_link_into_other_lifecycle_not_pruned(tmp_path: Path) -> None:
    """Forge finding #2: a user link into the wrong mirror is unmanaged, never pruned."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    _make_project(private / WORKING_SUBDIR / "notes")
    # A user link sitting in the active mirror but pointing at a working source
    # is a lifecycle mismatch — unmanaged, so it is never pruned.
    userlink = _mirror(repo) / "notes"
    userlink.symlink_to(private / WORKING_SUBDIR / "notes")
    result = sync_private_project_links(repo, private)
    assert "projects/active/notes" not in result.removed
    assert userlink.is_symlink()
    assert (repo / "projects" / "working" / "notes").is_symlink()


def test_broken_link_outside_active_not_pruned(tmp_path: Path) -> None:
    """A broken symlink whose target was OUTSIDE active/ must never be pruned."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    gone = tmp_path / "gone_external"  # never existed under active/
    broken = _mirror(repo) / "orphan"
    broken.symlink_to(gone)  # broken link pointing outside the private root
    result = sync_private_project_links(repo, private)
    assert "projects/active/orphan" not in result.removed
    assert broken.is_symlink()  # left intact


def test_symlink_loop_does_not_crash(tmp_path: Path) -> None:
    """Forge finding #1: a symlink loop under projects/ must not crash the sync."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    mirror = _mirror(repo)
    loop_a = mirror / "loop_a"
    loop_b = mirror / "loop_b"
    loop_a.symlink_to(loop_b)
    loop_b.symlink_to(loop_a)
    # Must not raise RuntimeError("Symlink loop") — and still link alpha.
    result = sync_private_project_links(repo, private)
    assert "projects/active/alpha" in result.created
    assert "projects/active/loop_a" not in result.removed
    assert "projects/active/loop_b" not in result.removed


# --- sync_private_project_links: protections --------------------------------


def test_protected_exemplar_never_overwritten(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    # A real exemplar directory with the same name as an (illegal) active source.
    exemplar = next(iter(PROTECTED_NAMES))
    _make_project(repo / "projects" / "active" / exemplar)
    private = _make_private(tmp_path, active=[exemplar], name="priv")
    result = sync_private_project_links(repo, private)
    assert (repo / "projects" / "active" / exemplar).is_dir()
    assert not (repo / "projects" / "active" / exemplar).is_symlink()
    assert any(exemplar in s for s in result.skipped)


def test_real_path_collision_skipped(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    # A real directory already occupies projects/active/alpha.
    _make_project(repo / "projects" / "active" / "alpha")
    result = sync_private_project_links(repo, private)
    assert (repo / "projects" / "active" / "alpha").is_dir()
    assert not (repo / "projects" / "active" / "alpha").is_symlink()
    assert any("alpha" in s and "real path" in s for s in result.skipped)


def test_md_file_in_active_not_linked(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    (private / ACTIVE_SUBDIR / "README.md").write_text("doc\n", encoding="utf-8")
    sync_private_project_links(repo, private)
    assert not (repo / "projects" / "active" / "README.md").exists()


def test_hidden_dir_in_active_skipped(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    (private / ACTIVE_SUBDIR / ".hidden").mkdir()
    sync_private_project_links(repo, private)
    assert not (repo / "projects" / "active" / ".hidden").exists()


# --- no-op + dry-run --------------------------------------------------------


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


# --- is_managed_symlink -----------------------------------------------------


def test_is_managed_symlink_true_for_in_private(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_private_project_links(repo, private)
    assert is_managed_symlink(repo / "projects" / "active" / "alpha", private.resolve())


def test_is_managed_symlink_false_for_real_dir(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=[], name="priv")
    real = repo / "projects" / "active" / "native"
    _make_project(real)
    assert not is_managed_symlink(real, private.resolve())


# --- discovery / validation / import parity (the core promise) --------------


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
