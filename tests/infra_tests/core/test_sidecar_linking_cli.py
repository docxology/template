"""Characterization tests for the shared sidecar link-sync CLI surface.

Four top-level resource trees (``projects/``, ``fonds/``, ``rules/``, ``tools/``)
expose the same ``linking`` command. These tests pin the behaviour every one of
them must keep while the duplicated argument parser, sync dispatch and delta
printer live in one place.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from infrastructure.core import sidecar_linking
from infrastructure.core.sidecar_linking import LinkSyncResult
from infrastructure.fonds import linking as fonds_linking
from infrastructure.project import linking as project_linking
from infrastructure.rules import linking as rules_linking
from infrastructure.tools import linking as tools_linking

POOL_MODULES = (
    pytest.param(project_linking, "projects", "projects", id="projects"),
    pytest.param(fonds_linking, "fonds", "fonds", id="fonds"),
    pytest.param(rules_linking, "rules", "rules", id="rules"),
    pytest.param(tools_linking, "tools", "tools", id="tools"),
)


def _make_repo(tmp_path: Path, tree: str) -> Path:
    repo = tmp_path / "template"
    (repo / tree).mkdir(parents=True)
    return repo


def _make_private_root(tmp_path: Path, *, working: tuple[str, ...] = ("demo",)) -> Path:
    private = tmp_path / "sidecar"
    (private / "working").mkdir(parents=True)
    (private / "archive").mkdir(parents=True)
    for name in working:
        (private / "working" / name).mkdir()
    return private


@pytest.mark.parametrize(("module", "tree", "prefix"), POOL_MODULES)
def test_link_cli_parser_exposes_the_shared_flag_contract(module, tree: str, prefix: str) -> None:
    parser = module._build_parser()  # noqa: SLF001 - pinned public CLI shape
    assert parser.prog == f"python -m {module.__name__}"
    assert parser.description

    defaults = parser.parse_args([])
    assert defaults.repo_root is None
    assert defaults.private_root is None
    assert defaults.dry_run is False
    assert defaults.no_prune is False

    explicit = parser.parse_args(["--repo-root", "/repo", "--private-root", "/private", "--dry-run", "--no-prune"])
    assert explicit.repo_root == Path("/repo")
    assert explicit.private_root == Path("/private")
    assert explicit.dry_run is True
    assert explicit.no_prune is True


@pytest.mark.parametrize(("module", "tree", "prefix"), POOL_MODULES)
def test_link_cli_dry_run_reports_deltas_without_touching_the_tree(
    module, tree: str, prefix: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _make_repo(tmp_path, tree)
    private = _make_private_root(tmp_path)

    exit_code = module.main(["--repo-root", str(repo), "--private-root", str(private), "--dry-run"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert f"link-sync @ {private.resolve()}" in out
    assert "1 created, 0 updated, 0 removed, 0 skipped" in out
    assert f"  + {prefix}/working/demo" in out
    assert not (repo / tree / "working").exists()


@pytest.mark.parametrize(("module", "tree", "prefix"), POOL_MODULES)
def test_link_cli_creates_the_managed_symlink(module, tree: str, prefix: str, tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, tree)
    private = _make_private_root(tmp_path)

    assert module.main(["--repo-root", str(repo), "--private-root", str(private)]) == 0

    link = repo / tree / "working" / "demo"
    assert link.is_symlink()
    assert link.resolve() == (private / "working" / "demo").resolve()


@pytest.mark.parametrize(("module", "tree", "prefix"), POOL_MODULES)
def test_link_cli_without_a_private_root_is_an_announced_noop(
    module, tree: str, prefix: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _make_repo(tmp_path, tree)

    assert module.main(["--repo-root", str(repo)]) == 0
    assert capsys.readouterr().out.strip() == "link-sync: no private projects root found (no-op)"


@pytest.mark.parametrize(("module", "tree", "prefix"), POOL_MODULES)
def test_link_cli_no_prune_keeps_stale_managed_links(
    module, tree: str, prefix: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _make_repo(tmp_path, tree)
    private = _make_private_root(tmp_path)
    assert module.main(["--repo-root", str(repo), "--private-root", str(private)]) == 0
    capsys.readouterr()

    (private / "working" / "demo").rmdir()
    assert module.main(["--repo-root", str(repo), "--private-root", str(private), "--no-prune"]) == 0

    out = capsys.readouterr().out
    assert "0 created, 0 updated, 0 removed" in out
    assert (repo / tree / "working" / "demo").is_symlink()


@pytest.mark.parametrize(("module", "tree", "prefix"), POOL_MODULES)
def test_link_cli_prunes_stale_managed_links(
    module, tree: str, prefix: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _make_repo(tmp_path, tree)
    private = _make_private_root(tmp_path)
    assert module.main(["--repo-root", str(repo), "--private-root", str(private)]) == 0
    capsys.readouterr()

    (private / "working" / "demo").rmdir()
    assert module.main(["--repo-root", str(repo), "--private-root", str(private)]) == 0

    out = capsys.readouterr().out
    assert "0 created, 0 updated, 1 removed" in out
    assert f"  - {prefix}/working/demo" in out
    assert not (repo / tree / "working" / "demo").exists()


def test_print_link_sync_result_defaults_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    result = LinkSyncResult(
        created=["working/demo"],
        updated=["archive/old"],
        removed=["working/retired"],
        skipped=["working/unchanged"],
        private_root=Path("/tmp/private"),
    )

    sidecar_linking.print_link_sync_result(result)

    out = capsys.readouterr().out
    assert "link-sync @ /tmp/private" in out
    assert "  + working/demo" in out
    assert "  ~ archive/old" in out
    assert "  - working/retired" in out
    assert "  . working/unchanged" in out


def test_print_link_sync_result_writes_to_a_requested_stream() -> None:
    result = LinkSyncResult(created=["working/demo"], private_root=Path("/tmp/private"))
    buffer = io.StringIO()

    sidecar_linking.print_link_sync_result(result, stream=buffer)

    assert buffer.getvalue().splitlines() == [
        "link-sync @ /tmp/private: 1 created, 0 updated, 0 removed, 0 skipped",
        "  + working/demo",
    ]


def test_pool_packages_keep_distinct_sidecar_roots() -> None:
    configs = (
        project_linking.PROJECT_LINK_CONFIG,
        fonds_linking.FONDS_LINK_CONFIG,
        rules_linking.RULES_LINK_CONFIG,
        tools_linking.TOOLS_LINK_CONFIG,
    )
    assert len({config.config_filename for config in configs}) == 4
    assert len({config.env_var for config in configs}) == 4
    assert len({config.skip_env_var for config in configs}) == 4
    assert {config.lifecycle_link_dirs["working"] for config in configs} == {
        "projects/working",
        "fonds/working",
        "rules/working",
        "tools/working",
    }


def test_passive_pools_share_one_lifecycle_contract() -> None:
    pool_configs = (
        fonds_linking.FONDS_LINK_CONFIG,
        rules_linking.RULES_LINK_CONFIG,
        tools_linking.TOOLS_LINK_CONFIG,
    )
    assert {config.lifecycle_subdirs for config in pool_configs} == {("working", "archive")}
    assert {config.required_private_root_subdirs for config in pool_configs} == {("working", "archive")}
    assert {config.ignored_lifecycle_entry_names for config in pool_configs} == {frozenset({"output"})}


def test_each_pool_linking_module_keeps_its_documented_public_names() -> None:
    public_names = (
        (project_linking, "sync_private_project_links", "private_projects_root"),
        (fonds_linking, "sync_private_fond_links", "private_fonds_root"),
        (rules_linking, "sync_private_rule_links", "private_rules_root"),
        (tools_linking, "sync_private_tool_links", "private_tools_root"),
    )
    for module, sync_name, root_name in public_names:
        assert callable(getattr(module, sync_name))
        assert callable(getattr(module, root_name))
        assert callable(module.is_managed_symlink)
        assert callable(module.main)
        assert callable(module._build_parser)
