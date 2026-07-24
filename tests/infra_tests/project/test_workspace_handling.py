"""Real-behavior tests for workspace discovery and sidecar linking code paths.

Exercises ``infrastructure.project.discovery.discover_projects``,
``infrastructure.project.linking`` (sync + ``is_managed_symlink``), and
``infrastructure.project.workspace`` helpers against real ``tmp_path`` directory
trees. No mocks: real files, real symlinks, real subprocess calls.

This module complements ``test_workspace.py``, ``test_workspace_additional.py``,
``test_discovery.py``, and ``test_linking.py`` by focusing on *interactions*
between workspace discovery and sidecar linking — the integration boundary
where a linked lifecycle entry must be discoverable as a project, and where
``resolve_project_root`` resolves a linked entry back to its source.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from infrastructure.core.project_paths import resolve_project_root
from infrastructure.project.discovery import (
    discover_projects,
    get_default_project,
    project_name_from_root,
)
from infrastructure.project.linking import (
    ARCHIVE_SUBDIR,
    CONFIG_FILENAME,
    ENV_VAR,
    LIFECYCLE_SUBDIRS,
    WORKING_SUBDIR,
    is_managed_symlink,
    private_projects_root,
    sync_active_links,
    sync_private_project_links,
)
from infrastructure.project.validation import validate_project_structure
from infrastructure.project.workspace import (
    add_dependency,
    run_uv_command,
    show_workspace_status,
    show_workspace_tree,
    sync_workspace,
    update_workspace,
)


# --- helpers ----------------------------------------------------------------


def _make_repo(tmp_path: Path) -> Path:
    """A template repo root with a real projects/ dir."""
    repo = tmp_path / "template"
    (repo / "projects").mkdir(parents=True)
    return repo


def _make_private(
    tmp_path: Path,
    *,
    active: Sequence[str] = (),
    working: Sequence[str] = (),
    archive: Sequence[str] = (),
    name: str = "projects",
) -> Path:
    """A private companion repo with every supported lifecycle folder."""
    private = tmp_path / name
    for sub in LIFECYCLE_SUBDIRS:
        (private / sub).mkdir(parents=True)
    for proj in active:
        _make_project(private / "active" / proj)
    for proj in working:
        _make_project(private / WORKING_SUBDIR / proj)
    for proj in archive:
        _make_project(private / ARCHIVE_SUBDIR / proj)
    return private


def _make_project(path: Path) -> Path:
    """A minimal valid project (src/ with a .py + tests/)."""
    (path / "src").mkdir(parents=True)
    (path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (path / "src" / "calc.py").write_text("def answer() -> int:\n    return 42\n", encoding="utf-8")
    (path / "tests").mkdir()
    (path / "tests" / "__init__.py").write_text("", encoding="utf-8")
    return path


# --- discover_projects + linking integration --------------------------------


def test_discover_projects_finds_synced_active_entry(tmp_path: Path) -> None:
    """A synced active lifecycle entry is discoverable as a real project."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["linked_proj"], name="priv")
    sync_private_project_links(repo, private)

    projects = discover_projects(repo)
    names = {p.name for p in projects}
    assert "linked_proj" in names, f"expected linked_proj in {names}"


def test_discover_projects_skips_working_lifecycle(tmp_path: Path) -> None:
    """Working lifecycle entries are mirrored but NOT discovered."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, working=["wip_proj"], name="priv")
    sync_private_project_links(repo, private)

    assert (repo / "projects" / "working" / "wip_proj").is_symlink()
    projects = discover_projects(repo)
    names = {p.name for p in projects}
    assert "wip_proj" not in names, f"working entry should not be discovered: {names}"


def test_discover_projects_skips_archive_lifecycle(tmp_path: Path) -> None:
    """Archive lifecycle entries are mirrored but NOT discovered."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, archive=["old_proj"], name="priv")
    sync_private_project_links(repo, private)

    assert (repo / "projects" / "archive" / "old_proj").is_symlink()
    projects = discover_projects(repo)
    names = {p.name for p in projects}
    assert "old_proj" not in names


def test_resolve_project_root_round_trips_linked_active(tmp_path: Path) -> None:
    """resolve_project_root resolves a synced active entry back to its source."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_private_project_links(repo, private)

    resolved = resolve_project_root(repo, "alpha")
    assert resolved.resolve() == (private / "active" / "alpha").resolve()


def test_resolve_project_root_qualified_working_path(tmp_path: Path) -> None:
    """A qualified ``working/<name>`` path resolves to the synced link."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, working=["draft"], name="priv")
    sync_private_project_links(repo, private)

    resolved = resolve_project_root(repo, "working/draft")
    assert resolved.resolve() == (private / WORKING_SUBDIR / "draft").resolve()


def test_project_name_from_root_for_linked_entry(tmp_path: Path) -> None:
    """project_name_from_root returns the discovery name for a linked entry.

    The linked entry resolves to its source under the private root, which is
    *outside* ``<repo>/projects``, so the function falls back to the bare
    directory basename (``alpha``). A real (non-symlink) project under
    ``projects/active/<name>`` returns the qualified ``active/<name>``.
    """
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_private_project_links(repo, private)

    # Symlink resolves to the private root, so the relative_to branch fails
    # and the bare basename fallback kicks in.
    link = repo / "projects" / "active" / "alpha"
    name = project_name_from_root(link, repo)
    assert name == "alpha"

    # A real directory under projects/active/ yields the qualified form.
    real = repo / "projects" / "active" / "native"
    _make_project(real)
    qualified = project_name_from_root(real, repo)
    assert qualified == "active/native"


def test_project_name_from_root_falls_back_to_basename(tmp_path: Path) -> None:
    """When the project is outside projects/, the bare name is returned."""
    repo = _make_repo(tmp_path)
    external = tmp_path / "external"
    _make_project(external)
    name = project_name_from_root(external, repo)
    assert name == "external"


# --- discovery edge cases ---------------------------------------------------


def test_discover_projects_empty_repo_returns_empty_list(tmp_path: Path) -> None:
    """An empty projects/ dir yields an empty discovery list."""
    repo = _make_repo(tmp_path)
    assert discover_projects(repo) == []


def test_discover_projects_missing_projects_dir(tmp_path: Path) -> None:
    """A repo without projects/ returns an empty list (no crash)."""
    repo = tmp_path / "no_projects"
    repo.mkdir()
    assert discover_projects(repo) == []


def test_discover_projects_skips_hidden_and_dotdirs(tmp_path: Path) -> None:
    """Hidden directories under projects/ are not discovered."""
    repo = _make_repo(tmp_path)
    (repo / "projects" / ".hidden").mkdir()
    _make_project(repo / "projects" / "visible")
    projects = discover_projects(repo)
    names = {p.name for p in projects}
    assert "visible" in names
    assert ".hidden" not in names


def test_validate_project_structure_rejects_empty_src(tmp_path: Path) -> None:
    """A project with src/ but no Python files is invalid."""
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "src").mkdir()
    (proj / "tests").mkdir()
    is_valid, msg = validate_project_structure(proj)
    assert is_valid is False
    assert "no Python files" in msg


def test_validate_project_structure_accepts_valid(tmp_path: Path) -> None:
    """A project with src/*.py and tests/ is valid."""
    proj = tmp_path / "proj"
    _make_project(proj)
    is_valid, msg = validate_project_structure(proj)
    assert is_valid is True
    assert msg == "Valid project structure"


def test_get_default_project_none_when_missing(tmp_path: Path) -> None:
    """get_default_project returns None when projects/project absent."""
    repo = _make_repo(tmp_path)
    assert get_default_project(repo) is None


def test_get_default_project_returns_valid(tmp_path: Path) -> None:
    """get_default_project returns a ProjectInfo when projects/project exists."""
    repo = _make_repo(tmp_path)
    _make_project(repo / "projects" / "project")
    info = get_default_project(repo)
    assert info is not None
    assert info.name == "project"
    assert info.is_valid


# --- is_managed_symlink classification --------------------------------------


def test_is_managed_symlink_false_for_regular_file(tmp_path: Path) -> None:
    """A regular file is never a managed symlink."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    file = repo / "projects" / "notes.txt"
    file.write_text("hi", encoding="utf-8")
    assert not is_managed_symlink(file, private.resolve())


def test_is_managed_symlink_false_for_foreign_symlink(tmp_path: Path) -> None:
    """A symlink pointing outside the private root is not managed."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    outside = tmp_path / "outside"
    outside.mkdir()
    link = repo / "projects" / "active" / "foreign"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside)
    assert not is_managed_symlink(link, private.resolve())


def test_is_managed_symlink_true_for_synced_link(tmp_path: Path) -> None:
    """A synced active link is classified as managed."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_private_project_links(repo, private)
    link = repo / "projects" / "active" / "alpha"
    assert is_managed_symlink(link, private.resolve())


# --- sync_active_links alias ------------------------------------------------


def test_sync_active_links_is_alias_for_sync_private(tmp_path: Path) -> None:
    """sync_active_links delegates to sync_private_project_links."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["beta"], name="priv")
    result = sync_active_links(repo, private)
    assert result.created == ["projects/active/beta"]
    assert (repo / "projects" / "active" / "beta").is_symlink()


def test_sync_no_op_when_private_root_none(tmp_path: Path, monkeypatch) -> None:
    """sync is a no-op when no private root is resolvable."""
    repo = _make_repo(tmp_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    result = sync_private_project_links(repo)
    assert result.private_root is None
    assert not result.changed


# --- private_projects_root resolution ---------------------------------------


def test_private_projects_root_env_override(tmp_path: Path, monkeypatch) -> None:
    """TEMPLATE_PRIVATE_PROJECTS_ROOT env var takes precedence."""
    repo = _make_repo(tmp_path)
    env_root = _make_private(tmp_path, name="env_private")
    monkeypatch.setenv(ENV_VAR, str(env_root))
    assert private_projects_root(repo) == env_root.resolve()


def test_private_projects_root_config_file(tmp_path: Path, monkeypatch) -> None:
    """The .private_projects_root config file is honored."""
    repo = _make_repo(tmp_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    cfg_root = _make_private(tmp_path, name="cfg_private")
    (repo / CONFIG_FILENAME).write_text(str(cfg_root) + "\n", encoding="utf-8")
    assert private_projects_root(repo) == cfg_root.resolve()


def test_private_projects_root_none_without_signature(tmp_path: Path, monkeypatch) -> None:
    """No private root when no lifecycle signature is present."""
    repo = _make_repo(tmp_path)
    monkeypatch.delenv(ENV_VAR, raising=False)
    (tmp_path / "projects").mkdir()  # sibling without lifecycle subdirs
    assert private_projects_root(repo) is None


# --- workspace helpers (integration with linking state) --------------------


def test_show_workspace_status_valid_with_synced_links(tmp_path: Path, monkeypatch) -> None:
    """show_workspace_status reads a valid pyproject even after sync ran."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_private_project_links(repo, private)
    (repo / "pyproject.toml").write_text(
        '[tool.uv.workspace]\nmembers = ["projects/active/alpha"]\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(repo)
    assert show_workspace_status() == 0


def test_show_workspace_tree_fails_without_uv(tmp_path: Path, monkeypatch) -> None:
    """show_workspace_tree returns non-zero when uv is absent from PATH."""
    repo = _make_repo(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.chdir(repo)
    result = show_workspace_tree()
    assert result != 0


def test_sync_workspace_fails_without_uv(tmp_path: Path, monkeypatch) -> None:
    """sync_workspace returns 1 when uv is not on PATH."""
    repo = _make_repo(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.chdir(repo)
    assert sync_workspace() == 1


def test_update_workspace_fails_without_uv(tmp_path: Path, monkeypatch) -> None:
    """update_workspace returns 1 when uv is not on PATH."""
    repo = _make_repo(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.chdir(repo)
    assert update_workspace() == 1


def test_add_dependency_missing_project_dir(tmp_path: Path, monkeypatch) -> None:
    """add_dependency returns 1 for a nonexistent project directory."""
    monkeypatch.chdir(tmp_path)
    assert add_dependency("some-pkg", "nonexistent_project") == 1


def test_add_dependency_uv_missing_for_real_project(tmp_path: Path, monkeypatch) -> None:
    """add_dependency returns 1 when uv absent even if project dir exists."""
    repo = _make_repo(tmp_path)
    (repo / "projects" / "test_proj").mkdir(parents=True)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.chdir(repo)
    assert add_dependency("some-pkg", "test_proj") == 1


def test_run_uv_command_real_success(tmp_path: Path) -> None:
    """A real command that exits 0 returns 0."""
    assert run_uv_command(["true"], cwd=tmp_path) == 0


def test_run_uv_command_real_failure(tmp_path: Path) -> None:
    """A real command that exits non-zero returns that exit code."""
    assert run_uv_command(["false"], cwd=tmp_path) == 1


def test_run_uv_command_missing_binary(tmp_path: Path) -> None:
    """OSError (binary not found) is caught and returns 1."""
    missing = tmp_path / "definitely-not-a-command"
    assert run_uv_command([str(missing)], cwd=tmp_path) == 1
