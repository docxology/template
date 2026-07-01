"""Regression pins for the deterministic coordination-mechanism testbed.

Manuscript: projects/templates/template_autoscientists/manuscript/03_results.md.

This exemplar's entire contribution is an *honest* one: under a matched
sequential experiment budget, splitting work into coordinated teams does NOT
beat the single-thread baseline on solution quality (clean-metric advantage is
exactly 0.0000), and the measurable benefits are search hygiene (dead-end
registry: 36 wasted re-probes -> 0) and noise robustness (noise-band
confirmation: ~13x less accepted noise). These pins bind those exact claims to
the source: each value is re-derived by calling ``src.search.run_search`` /
``src.objective.SyntheticObjective.clean`` with the same objective, proposer,
config, and budget the analysis scripts (``run_search_comparison.py`` /
``run_ablation.py``) use -- never by hand-copying a number from the manuscript.

No mocks: real deterministic objects only, in line with the repo no-mock policy.
"""

from __future__ import annotations

from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_autoscientists"

_PKG_ALIAS = "_autoscientists_src"


def _load_src_package() -> ModuleType:
    """Load this exemplar's ``src`` package under a project-unique alias.

    Every public exemplar ships a top-level ``src`` package, so a bare
    ``sys.path.insert`` + ``from src...`` collides on ``sys.modules['src']``
    once a second project's regression test joins the same pytest session.
    Registering under a namespaced key keeps the real tested functions in
    scope (no mocks) and stays collision-free regardless of collection order.
    """

    if _PKG_ALIAS in sys.modules:
        return sys.modules[_PKG_ALIAS]
    src_init = PROJECT_ROOT / "src" / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        _PKG_ALIAS,
        src_init,
        submodule_search_locations=[str(PROJECT_ROOT / "src")],
    )
    assert spec is not None and spec.loader is not None, f"cannot load {src_init}"
    package = importlib.util.module_from_spec(spec)
    sys.modules[_PKG_ALIAS] = package
    spec.loader.exec_module(package)
    return package


def _import_submodule(dotted: str) -> ModuleType:
    _load_src_package()
    return importlib.import_module(f"{_PKG_ALIAS}.{dotted}")


DeterministicProposer = _import_submodule("agents").DeterministicProposer
SyntheticObjective = _import_submodule("objective").SyntheticObjective
_search_mod = _import_submodule("search")
SearchConfig = _search_mod.SearchConfig
SearchResult = _search_mod.SearchResult
run_search = _search_mod.run_search


# Mirror of the analysis-script constants
# (scripts/run_search_comparison.py, scripts/run_ablation.py).
BUDGET = 60
_OBJECTIVE_KW = {"dimensions": 4, "noise_scale": 0.02}


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int) -> None:
    tolerance = entry.get("abs_tolerance", 0)
    assert observed == pytest.approx(entry["value"], abs=tolerance)


def _objective() -> SyntheticObjective:
    return SyntheticObjective(**_OBJECTIVE_KW)


@pytest.fixture(scope="module")
def comparison_runs() -> tuple[SyntheticObjective, SearchResult, SearchResult]:
    """Re-derive the matched-budget comparison exactly as run_search_comparison.py does."""

    objective = _objective()
    proposer = DeterministicProposer()
    coordinated = run_search(objective, proposer, SearchConfig(budget=BUDGET))
    baseline = run_search(objective, proposer, SearchConfig.single_thread_baseline(budget=BUDGET))
    return objective, coordinated, baseline


@pytest.fixture(scope="module")
def ablation_runs() -> tuple[SyntheticObjective, dict[str, SearchResult]]:
    """Re-derive the ablation rows exactly as run_ablation.py does."""

    objective = _objective()
    proposer = DeterministicProposer()
    base = SearchConfig(budget=BUDGET)
    ablations = (
        ("full coordination", {}),
        ("no confirmation", {"use_confirmation": False}),
    )
    rows: dict[str, SearchResult] = {}
    for label, overrides in ablations:
        config = replace(base, **overrides) if overrides else base
        rows[label] = run_search(objective, proposer, config)
    return objective, rows


def test_matched_budget_efficiency_claims_rederive_from_source(
    load_pinned_values: Any,
    comparison_runs: tuple[SyntheticObjective, SearchResult, SearchResult],
) -> None:
    """Bind the honest no-speedup headline + efficiency counts to a fresh source run.

    03_results.md / Matched-budget comparison table + prose (lines 15-20, 48).
    """

    pinned = load_pinned_values("template_autoscientists")
    objective, coordinated, baseline = comparison_runs

    # Coordinated reaches the clean optimum at experiment 16 (marginally slower
    # than the baseline's 12 -- the manuscript reports this plainly).
    _assert_pin_matches(
        _pin(pinned, "comparison_coordinated_experiments_to_optimum"),
        coordinated.experiments_to_target,
    )

    # The baseline (no dead-end registry) wastes 36 re-probes over the full budget.
    _assert_pin_matches(
        _pin(pinned, "comparison_baseline_redundant_reprobes"),
        baseline.redundant_experiments,
    )

    # The honest headline: coordination's clean-quality advantage is exactly 0.0.
    advantage = objective.clean(coordinated.champion.params) - objective.clean(baseline.champion.params)
    _assert_pin_matches(_pin(pinned, "comparison_clean_metric_advantage"), advantage)


def test_ablation_reported_metric_claims_rederive_from_source(
    load_pinned_values: Any,
    ablation_runs: tuple[SyntheticObjective, dict[str, SearchResult]],
) -> None:
    """Bind the load-bearing robustness claim to a fresh source run.

    03_results.md / Per-mechanism ablation table + prose (lines 30-36, 49). Full
    coordination reports ~0.00121; removing confirmation inflates the reported
    metric to ~0.01565 (a ~13x increase in accepted noise) while the clean metric
    stays 0.0. Both reported metrics are pinned at full float precision.
    """

    pinned = load_pinned_values("template_autoscientists")
    _, rows = ablation_runs

    _assert_pin_matches(
        _pin(pinned, "ablation_full_coordination_reported_metric"),
        rows["full coordination"].champion.metric,
    )
    _assert_pin_matches(
        _pin(pinned, "ablation_no_confirmation_reported_metric"),
        rows["no confirmation"].champion.metric,
    )


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    Non-vacuity control (feedback-verify-not-trust-machine-proof): proves the
    assertion above can actually fail, so a green run means the re-derivation
    genuinely matched the pin -- not that the comparison is a no-op.
    """

    pinned = load_pinned_values("template_autoscientists")
    entry = dict(_pin(pinned, "comparison_baseline_redundant_reprobes"))
    observed = entry["value"]
    entry["value"] = observed + 1  # perturb the pinned ground truth

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
