"""Further direct negative controls for ``manuscript.sheaf.semantic_issues``.

``test_semantic_issues_direct`` already covers the stale-manuscript-variable and
pymdp-mode-mismatch arms. This file covers the remaining reachable-by-copy-
mutation disagreement branches: policy-comparison run count / mode set, policy
posterior normalization, runtime diagnostics ok / unexpected warnings, and the
graph-world step/goal restrictions. Each test injects one defect into a single
artifact in an isolated project-tree copy, asserts the exact issue string the
aggregator emits (binding to the injected value where the string carries one),
and restores the artifact byte-for-byte in ``finally`` so the module-scoped copy
stays reusable and the git-tracked tree is never touched.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from manuscript.sheaf.semantic_issues import semantic_gluing_issues

from direct_recompute_support import copy_project_tree


@pytest.fixture(scope="module")
def copied_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return copy_project_tree(tmp_path_factory.mktemp("semantic_issues_more_tree"))


def _mutate(path: Path, mutate) -> str:
    original = path.read_text(encoding="utf-8")
    payload = json.loads(original)
    mutate(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return original


@pytest.mark.timeout(300)
def test_flags_policy_comparison_run_count_too_small(copied_root: Path) -> None:
    path = copied_root / "output" / "data" / "si_policy_comparison.json"

    def _mut(payload: dict) -> None:
        payload.setdefault("summary", {})["run_count"] = 1

    original = _mutate(path, _mut)
    try:
        issues = semantic_gluing_issues(copied_root)
        assert any("policy comparison run count too small: 1" in issue for issue in issues), issues
    finally:
        path.write_text(original, encoding="utf-8")


@pytest.mark.timeout(300)
def test_flags_policy_comparison_mode_set_invalid(copied_root: Path) -> None:
    path = copied_root / "output" / "data" / "si_policy_comparison.json"

    def _mut(payload: dict) -> None:
        for row in payload.get("runs") or []:
            row["mode"] = "__forced_mode__"

    original = _mutate(path, _mut)
    try:
        issues = semantic_gluing_issues(copied_root)
        assert any("policy comparison mode set invalid" in issue and "__forced_mode__" in issue for issue in issues), (
            issues
        )
    finally:
        path.write_text(original, encoding="utf-8")


@pytest.mark.timeout(300)
def test_flags_unnormalized_policy_posterior(copied_root: Path) -> None:
    path = copied_root / "output" / "data" / "pymdp_policy_posterior_grid.json"

    def _mut(payload: dict) -> None:
        payload["all_available_posteriors_normalized"] = False

    original = _mutate(path, _mut)
    try:
        issues = semantic_gluing_issues(copied_root)
        assert "pymdp policy posterior grid has unnormalized posterior rows" in issues, issues
    finally:
        path.write_text(original, encoding="utf-8")


@pytest.mark.timeout(300)
def test_flags_runtime_diagnostics_not_ok(copied_root: Path) -> None:
    path = copied_root / "output" / "reports" / "pymdp_runtime_diagnostics.json"

    def _mut(payload: dict) -> None:
        payload["ok"] = False

    original = _mutate(path, _mut)
    try:
        issues = semantic_gluing_issues(copied_root)
        assert "pymdp runtime diagnostics are not ok" in issues, issues
    finally:
        path.write_text(original, encoding="utf-8")


@pytest.mark.timeout(300)
def test_flags_runtime_unexpected_warnings(copied_root: Path) -> None:
    path = copied_root / "output" / "reports" / "pymdp_runtime_diagnostics.json"

    def _mut(payload: dict) -> None:
        payload["unexpected_warning_count"] = 3  # ok stays True; only the warnings arm fires

    original = _mutate(path, _mut)
    try:
        issues = semantic_gluing_issues(copied_root)
        assert "pymdp runtime diagnostics captured unexpected warnings" in issues, issues
    finally:
        path.write_text(original, encoding="utf-8")


@pytest.mark.timeout(300)
def test_flags_graph_world_step_mismatch(copied_root: Path) -> None:
    path = copied_root / "output" / "data" / "si_graph_world_summary.json"

    def _mut(payload: dict) -> None:
        payload["steps"] = 999  # disagrees with the trace length

    original = _mutate(path, _mut)
    try:
        issues = semantic_gluing_issues(copied_root)
        assert any(
            "graph-world summary/trace mismatch" in issue and "summary steps=999" in issue for issue in issues
        ), issues
    finally:
        path.write_text(original, encoding="utf-8")


@pytest.mark.timeout(300)
def test_flags_graph_world_goal_not_reached(copied_root: Path) -> None:
    path = copied_root / "output" / "data" / "si_graph_world_summary.json"

    def _mut(payload: dict) -> None:
        payload["goal_reached"] = False

    original = _mutate(path, _mut)
    try:
        issues = semantic_gluing_issues(copied_root)
        assert "graph-world summary does not record goal_reached=true" in issues, issues
    finally:
        path.write_text(original, encoding="utf-8")
