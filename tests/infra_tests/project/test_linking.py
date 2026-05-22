#!/usr/bin/env python3
"""Tests for :mod:`infrastructure.project.linking` (no mocks — real symlinks).

Every test uses ``tmp_path`` with real directories and real symlinks. The
safety-critical guarantee under test is that pruning only ever removes symlinks
the syncer itself manages (resolving into the private root) and never a real
directory, an unmanaged symlink, or a protected exemplar.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.project.discovery import discover_projects
from infrastructure.project.linking import (
    ACTIVE_SUBDIR,
    CONFIG_FILENAME,
    ENV_VAR,
    PROTECTED_NAMES,
    is_managed_symlink,
    private_projects_root,
    sync_active_links,
)
from infrastructure.project.validation import validate_project_structure


# --- fixtures ---------------------------------------------------------------


def _make_repo(tmp_path: Path) -> Path:
    """A template repo root with a real projects/ dir."""
    repo = tmp_path / "template"
    (repo / "projects").mkdir(parents=True)
    return repo


def _make_private(tmp_path: Path, *, active: list[str] = (), name: str = "projects") -> Path:
    """A private companion repo with active/passive/archive folders."""
    private = tmp_path / name
    for sub in (ACTIVE_SUBDIR, "passive", "archive"):
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
    """A coincidental sibling projects/active/ (no passive/archive) is rejected."""
    repo = _make_repo(tmp_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    (tmp_path / "projects" / "active").mkdir(parents=True)  # active/ only
    assert private_projects_root(repo) is None


def test_env_root_accepts_active_only(tmp_path: Path, monkeypatch) -> None:
    """Explicit env override is permissive — active/ alone is enough."""
    repo = _make_repo(tmp_path)
    explicit = tmp_path / "explicit"
    (explicit / "active").mkdir(parents=True)  # no passive/archive
    monkeypatch.setenv(ENV_VAR, str(explicit))
    assert private_projects_root(repo) == explicit.resolve()


# --- sync_active_links: creation / idempotency ------------------------------


def test_sync_creates_symlink(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    result = sync_active_links(repo, private)
    link = repo / "projects" / "alpha"
    assert link.is_symlink()
    assert result.created == ["alpha"]


def test_created_symlink_resolves_to_source(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_active_links(repo, private)
    link = repo / "projects" / "alpha"
    assert link.resolve() == (private / ACTIVE_SUBDIR / "alpha").resolve()


def test_sync_is_idempotent(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha", "beta"], name="priv")
    sync_active_links(repo, private)
    second = sync_active_links(repo, private)
    assert second.created == []
    assert second.updated == []
    assert second.removed == []


# --- sync_active_links: prune safety ----------------------------------------


def test_prune_removes_stale_managed_link(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_active_links(repo, private)
    # alpha leaves active/ (e.g. moved to passive/)
    (private / ACTIVE_SUBDIR / "alpha").rename(private / "passive" / "alpha")
    result = sync_active_links(repo, private)
    assert result.removed == ["alpha"]
    assert not (repo / "projects" / "alpha").exists()
    assert not (repo / "projects" / "alpha").is_symlink()


def test_prune_leaves_unmanaged_symlink(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    # A symlink to somewhere OUTSIDE the private root must never be pruned.
    outside = tmp_path / "outside_target"
    outside.mkdir()
    foreign = repo / "projects" / "foreign"
    foreign.symlink_to(outside)
    result = sync_active_links(repo, private)
    assert "foreign" not in result.removed
    assert foreign.is_symlink()


def test_prune_never_touches_real_directory(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    # A real directory under projects/ (e.g. an exemplar / native project).
    real = repo / "projects" / "native_proj"
    _make_project(real)
    sync_active_links(repo, private)
    assert real.is_dir() and not real.is_symlink()
    assert (real / "src" / "calc.py").exists()


def test_no_prune_keeps_stale_link(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_active_links(repo, private)
    (private / ACTIVE_SUBDIR / "alpha").rename(private / "archive" / "alpha")
    result = sync_active_links(repo, private, prune=False)
    assert result.removed == []
    # The now-broken symlink survives (prune disabled).
    assert (repo / "projects" / "alpha").is_symlink()


def test_repoint_managed_stale_symlink(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    # A MANAGED link (points into active/) but at a stale/missing target.
    link = repo / "projects" / "alpha"
    link.symlink_to(private / ACTIVE_SUBDIR / "ghost")
    result = sync_active_links(repo, private)
    assert result.updated == ["alpha"]
    assert link.resolve() == (private / ACTIVE_SUBDIR / "alpha").resolve()


def test_unmanaged_symlink_collision_not_clobbered(tmp_path: Path) -> None:
    """Forge finding #3: a foreign same-named symlink must not be repointed."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    external = tmp_path / "external_alpha"
    _make_project(external)
    link = repo / "projects" / "alpha"
    link.symlink_to(external)  # points OUTSIDE the private root
    result = sync_active_links(repo, private)
    assert any("alpha" in s and "unmanaged" in s for s in result.skipped)
    assert link.resolve() == external.resolve()  # left untouched


def test_link_into_passive_not_pruned(tmp_path: Path) -> None:
    """Forge finding #2: a user link into passive/ is unmanaged, never pruned."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    _make_project(private / "passive" / "notes")
    userlink = repo / "projects" / "notes"
    userlink.symlink_to(private / "passive" / "notes")  # in private root, NOT active/
    result = sync_active_links(repo, private)
    assert "notes" not in result.removed
    assert userlink.is_symlink()


def test_broken_link_outside_active_not_pruned(tmp_path: Path) -> None:
    """A broken symlink whose target was OUTSIDE active/ must never be pruned."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    gone = tmp_path / "gone_external"  # never existed under active/
    broken = repo / "projects" / "orphan"
    broken.symlink_to(gone)  # broken link pointing outside the private root
    result = sync_active_links(repo, private)
    assert "orphan" not in result.removed
    assert broken.is_symlink()  # left intact


def test_symlink_loop_does_not_crash(tmp_path: Path) -> None:
    """Forge finding #1: a symlink loop under projects/ must not crash the sync."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    loop_a = repo / "projects" / "loop_a"
    loop_b = repo / "projects" / "loop_b"
    loop_a.symlink_to(loop_b)
    loop_b.symlink_to(loop_a)
    # Must not raise RuntimeError("Symlink loop") — and still link alpha.
    result = sync_active_links(repo, private)
    assert "alpha" in result.created
    assert "loop_a" not in result.removed and "loop_b" not in result.removed


# --- sync_active_links: protections -----------------------------------------


def test_protected_exemplar_never_overwritten(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    # A real exemplar directory with the same name as an (illegal) active source.
    exemplar = next(iter(PROTECTED_NAMES))
    _make_project(repo / "projects" / exemplar)
    private = _make_private(tmp_path, active=[exemplar], name="priv")
    result = sync_active_links(repo, private)
    assert (repo / "projects" / exemplar).is_dir()
    assert not (repo / "projects" / exemplar).is_symlink()
    assert any(exemplar in s for s in result.skipped)


def test_real_path_collision_skipped(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    # A real directory already occupies projects/alpha.
    _make_project(repo / "projects" / "alpha")
    result = sync_active_links(repo, private)
    assert (repo / "projects" / "alpha").is_dir()
    assert not (repo / "projects" / "alpha").is_symlink()
    assert any("alpha" in s and "real path" in s for s in result.skipped)


def test_md_file_in_active_not_linked(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    (private / ACTIVE_SUBDIR / "README.md").write_text("doc\n", encoding="utf-8")
    sync_active_links(repo, private)
    assert not (repo / "projects" / "README.md").exists()


def test_hidden_dir_in_active_skipped(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    (private / ACTIVE_SUBDIR / ".hidden").mkdir()
    sync_active_links(repo, private)
    assert not (repo / "projects" / ".hidden").exists()


# --- no-op + dry-run --------------------------------------------------------


def test_noop_when_no_private_root(tmp_path: Path, monkeypatch) -> None:
    repo = _make_repo(tmp_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    result = sync_active_links(repo)  # auto-resolve, nothing present
    assert result.private_root is None
    assert not result.changed
    assert list(repo.joinpath("projects").iterdir()) == []


def test_dry_run_makes_no_changes(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    result = sync_active_links(repo, private, dry_run=True)
    assert result.created == ["alpha"]
    assert not (repo / "projects" / "alpha").exists()  # nothing written


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
    assert "+ alpha" in captured.out
    assert not (repo / "projects" / "alpha").exists()


# --- is_managed_symlink -----------------------------------------------------


def test_is_managed_symlink_true_for_in_private(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_active_links(repo, private)
    assert is_managed_symlink(repo / "projects" / "alpha", private.resolve())


def test_is_managed_symlink_false_for_real_dir(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=[], name="priv")
    real = repo / "projects" / "native"
    _make_project(real)
    assert not is_managed_symlink(real, private.resolve())


# --- discovery / validation / import parity (the core promise) --------------


def test_discovery_finds_linked_project(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["linked_proj"], name="priv")
    sync_active_links(repo, private)
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
    assert "linked_proj" in captured.out.splitlines()
    assert (repo / "projects" / "linked_proj").is_symlink()


def test_validation_passes_for_symlinked_project(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["linked_proj"], name="priv")
    sync_active_links(repo, private)
    ok, msg = validate_project_structure(repo / "projects" / "linked_proj")
    assert ok, msg


def test_import_resolves_through_symlink(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["linked_proj"], name="priv")
    sync_active_links(repo, private)
    # Prove `projects.linked_proj.src.calc` imports through the symlink, in a
    # clean subprocess so the test suite's sys.modules/sys.path stay pristine.
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import projects.linked_proj.src.calc as m; print(m.answer())",
        ],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "42"


@pytest.mark.parametrize("name", sorted(PROTECTED_NAMES))
def test_protected_names_are_the_two_exemplars(name: str) -> None:
    assert name in {"template_code_project", "template_prose_project"}
