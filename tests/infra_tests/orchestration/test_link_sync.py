"""Tests for infrastructure.orchestration.link_sync helpers."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from infrastructure.core.sidecar_linking import LinkSyncResult
from infrastructure.fonds.linking import ENV_VAR as FONDS_ENV_VAR
from infrastructure.fonds.linking import SKIP_ENV_VAR as FONDS_SKIP_ENV_VAR
from infrastructure.orchestration.link_sync import (
    maybe_sync_all_links,
    print_link_sync_result,
    print_link_sync_results,
    registered_link_sync_hooks,
)
from infrastructure.project.linking import ENV_VAR as PROJECTS_ENV_VAR
from infrastructure.project.linking import SKIP_ENV_VAR as PROJECTS_SKIP_ENV_VAR
from infrastructure.rules.linking import ENV_VAR as RULES_ENV_VAR
from infrastructure.rules.linking import SKIP_ENV_VAR as RULES_SKIP_ENV_VAR
from infrastructure.tools.linking import ENV_VAR as TOOLS_ENV_VAR
from infrastructure.tools.linking import SKIP_ENV_VAR as TOOLS_SKIP_ENV_VAR

RESOURCE_TREES = ("projects", "fonds", "rules", "tools")
ROOT_ENV_VARS = (PROJECTS_ENV_VAR, FONDS_ENV_VAR, RULES_ENV_VAR, TOOLS_ENV_VAR)
SKIP_ENV_VARS = (
    PROJECTS_SKIP_ENV_VAR,
    FONDS_SKIP_ENV_VAR,
    RULES_SKIP_ENV_VAR,
    TOOLS_SKIP_ENV_VAR,
)


def _isolate_sidecar_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in (*ROOT_ENV_VARS, *SKIP_ENV_VARS):
        monkeypatch.delenv(variable, raising=False)


def _sidecar_and_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    _isolate_sidecar_env(monkeypatch)
    repo = tmp_path / "template"
    for tree in RESOURCE_TREES:
        (repo / tree).mkdir(parents=True)
    roots: dict[str, Path] = {}
    for tree, env_var in zip(RESOURCE_TREES, ROOT_ENV_VARS, strict=True):
        private = tmp_path / f"sidecar-{tree}"
        (private / "working" / "demo").mkdir(parents=True)
        (private / "archive").mkdir(parents=True)
        monkeypatch.setenv(env_var, str(private))
        roots[tree] = private.resolve()
    return {"repo": repo, **roots}


def test_print_link_sync_result_writes_summary_and_deltas() -> None:
    result = LinkSyncResult(
        created=["working/demo"],
        updated=["archive/old"],
        removed=["working/retired"],
        skipped=["working/unchanged"],
        private_root=Path("/tmp/private"),
    )
    buf = io.StringIO()
    print_link_sync_result(result, stream=buf)
    text = buf.getvalue()
    assert "link-sync @ /tmp/private" in text
    assert "+ working/demo" in text


def test_print_link_sync_results_only_reports_changed_domains() -> None:
    changed = LinkSyncResult(created=["a"], private_root=Path("/tmp/private"))
    unchanged = LinkSyncResult(skipped=["b"], private_root=Path("/tmp/private"))
    buf = io.StringIO()
    print_link_sync_results([changed, unchanged], stream=buf)
    assert buf.getvalue().count("[link-sync]") == 1


def test_registered_link_sync_hooks_cover_all_resource_trees() -> None:
    assert len(registered_link_sync_hooks()) == 4


def test_maybe_sync_all_links_binds_each_tree_to_its_own_sidecar_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = _sidecar_and_repo(tmp_path, monkeypatch)

    results = maybe_sync_all_links(layout["repo"])

    assert len(results) == len(RESOURCE_TREES)
    assert [result.private_root for result in results] == [layout[tree] for tree in RESOURCE_TREES]
    assert all(result.changed for result in results)
    for tree in RESOURCE_TREES:
        link = layout["repo"] / tree / "working" / "demo"
        assert link.is_symlink(), tree
        assert link.resolve() == (layout[tree] / "working" / "demo").resolve()


def test_each_skip_variable_disables_only_its_own_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    layout = _sidecar_and_repo(tmp_path, monkeypatch)
    monkeypatch.setenv(SKIP_ENV_VARS[1], "1")

    results = maybe_sync_all_links(layout["repo"])

    assert results[1].private_root is None
    assert not results[1].changed
    assert all(result.changed for index, result in enumerate(results) if index != 1)
    assert not (layout["repo"] / "fonds" / "working").exists()
