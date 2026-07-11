"""Direct leg-deterministic failure controls for ``roadmap_tracks.toy_sweep``.

``validate_toy_sweep_artifacts`` re-derives every stored aggregate from its rows
(PR#23 hardening) so a row-only forgery fails closed. On the tracked snapshot the
toy-sweep artifacts validate cleanly, so those failure arms only ran when a gate
rebuilt state. This file settles an isolated project-tree copy once with the real
``write_toy_sweep_artifacts`` (deterministic closed-form builders, no pymdp),
asserts the writer-then-validate baseline is clean, then injects one defect at a
time into a written artifact and asserts the exact issue string, restoring each
mutation byte-for-byte.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import pytest

from roadmap_tracks.toy_sweep import validate_toy_sweep_artifacts, write_toy_sweep_artifacts

from direct_recompute_support import copy_project_tree


@pytest.fixture(scope="module")
def settled_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = copy_project_tree(tmp_path_factory.mktemp("toy_sweep_tree"))
    write_toy_sweep_artifacts(root)
    return root


@pytest.mark.timeout(300)
def test_writer_then_validate_is_clean(settled_root: Path) -> None:
    assert validate_toy_sweep_artifacts(settled_root) == []


def _assert_injected_issue(root: Path, rel: str, mutate: Callable[[dict], None], expected: str) -> None:
    path = root / rel
    original = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        mutate(payload)
        path.write_text(json.dumps(payload), encoding="utf-8")
        assert expected in validate_toy_sweep_artifacts(root)
    finally:
        path.write_text(original, encoding="utf-8")


@pytest.mark.timeout(300)
def test_sensitivity_schema_mismatch(settled_root: Path) -> None:
    _assert_injected_issue(
        settled_root,
        "output/data/sensitivity_sweep.json",
        lambda p: p.__setitem__("schema", "wrong.schema"),
        "sensitivity_sweep.json schema mismatch",
    )


@pytest.mark.timeout(300)
def test_sensitivity_incomplete_grid(settled_root: Path) -> None:
    _assert_injected_issue(
        settled_root,
        "output/data/sensitivity_sweep.json",
        lambda p: p.__setitem__("complete_grid", False),
        "sensitivity_sweep.json grid is incomplete",
    )


@pytest.mark.timeout(300)
def test_uncertainty_unnormalized_rows(settled_root: Path) -> None:
    _assert_injected_issue(
        settled_root,
        "output/data/uncertainty_summary.json",
        lambda p: p.__setitem__("all_normalized", False),
        "uncertainty_summary.json contains unnormalized rows",
    )


@pytest.mark.timeout(300)
def test_benchmark_model_set_incomplete(settled_root: Path) -> None:
    _assert_injected_issue(
        settled_root,
        "output/data/toy_benchmark_matrix.json",
        lambda p: p.__setitem__("models", ["bernoulli_ising"]),
        "toy_benchmark_matrix.json model set is incomplete",
    )


@pytest.mark.timeout(300)
def test_policy_grid_incomplete(settled_root: Path) -> None:
    _assert_injected_issue(
        settled_root,
        "output/data/si_policy_grid.json",
        lambda p: p.__setitem__("complete_grid", False),
        "si_policy_grid.json grid is incomplete",
    )


@pytest.mark.timeout(300)
def test_efe_terms_unexplained(settled_root: Path) -> None:
    _assert_injected_issue(
        settled_root,
        "output/data/si_efe_terms.json",
        lambda p: p.__setitem__("all_rows_explained", False),
        "si_efe_terms.json has unexplained EFE rows",
    )


@pytest.mark.timeout(300)
def test_state_space_catalog_schema_mismatch(settled_root: Path) -> None:
    _assert_injected_issue(
        settled_root,
        "output/data/state_space_catalog.json",
        lambda p: p.__setitem__("schema", "wrong.schema"),
        "state_space_catalog.json schema mismatch",
    )


@pytest.mark.timeout(300)
def test_causal_ablation_incomplete(settled_root: Path) -> None:
    _assert_injected_issue(
        settled_root,
        "output/data/causal_ablation_matrix.json",
        lambda p: p.__setitem__("all_deterministic", False),
        "causal_ablation_matrix.json has incomplete or non-deterministic cells",
    )


@pytest.mark.timeout(300)
def test_assumption_index_schema_mismatch(settled_root: Path) -> None:
    _assert_injected_issue(
        settled_root,
        "output/data/analytical_assumption_index.json",
        lambda p: p.__setitem__("schema", "wrong.schema"),
        "analytical_assumption_index.json schema mismatch",
    )
