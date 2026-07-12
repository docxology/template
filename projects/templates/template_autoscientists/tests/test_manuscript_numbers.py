"""Pin every headline magnitude in manuscript/03_results.md to actual computation.

This is the load-bearing test for an HONEST-TESTBED exemplar: the manuscript's
entire contribution is that its quoted numbers are exactly what ``src/`` produces.
Without this test, a proposer/objective change could silently desync every quoted
value while the rest of the suite stayed green (it only asserts directional/range
invariants). The orchestration here mirrors ``scripts/run_search_comparison.py``
and ``scripts/run_ablation.py`` exactly (same objective, proposer, configs, budget)
and asserts the published figures to the precision the manuscript displays.

No mocks: real deterministic objects only.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from src.agents import DeterministicProposer
from src.ablation import AblationRow, build_ablation_payload, run_ablations
from src.comparison import build_objective, run_comparison
from src.objective import SyntheticObjective
from src.search import SearchConfig, run_search

_CONFIG_YAML = Path(__file__).resolve().parent.parent / "manuscript" / "config.yaml"

# Mirror of the script constants (scripts/run_*.py).
BUDGET = 60
_OBJECTIVE_KW = {"dimensions": 4, "noise_scale": 0.02}

# Manuscript display precision: comparison table rounds reported to 4 dp,
# ablation table to 5 dp (manuscript/03_results.md:15-16, 30-34).
_REPORTED_FULL = 0.0012065640438283457  # full/coordinated reported_metric
_NO_CONF_FULL = 0.015645836069054717  # "no confirmation" reported_metric


def _objective() -> SyntheticObjective:
    return SyntheticObjective(**_OBJECTIVE_KW)


def test_matched_budget_comparison_numbers_match_manuscript() -> None:
    """03_results.md §Matched-budget comparison table + prose (lines 15-20, 48)."""
    objective = _objective()
    proposer = DeterministicProposer()
    coordinated = run_search(objective, proposer, SearchConfig(budget=BUDGET))
    baseline = run_search(objective, proposer, SearchConfig.single_thread_baseline(budget=BUDGET))

    # Coordinated row: 0.0012 | 0.0000 | 16 | 36 | 0
    assert round(coordinated.champion.metric, 4) == 0.0012
    assert objective.clean(coordinated.champion.params) == 0.0
    assert coordinated.experiments_to_target == 16
    assert len(coordinated.trajectory) == 36
    assert coordinated.redundant_experiments == 0

    # Baseline row: 0.0012 | 0.0000 | 12 | 60 | 36
    assert round(baseline.champion.metric, 4) == 0.0012
    assert objective.clean(baseline.champion.params) == 0.0
    assert baseline.experiments_to_target == 12
    assert len(baseline.trajectory) == 60
    assert baseline.redundant_experiments == 36

    # Headline: clean-metric advantage is exactly 0.0000 (line 18, 48).
    advantage = objective.clean(coordinated.champion.params) - objective.clean(baseline.champion.params)
    assert advantage == 0.0

    # Coordinated halts early using 36 of 60; baseline spends the full budget
    # and wastes 36 re-probes (line 20).
    assert len(coordinated.trajectory) == 36 < BUDGET
    assert len(baseline.trajectory) == BUDGET
    assert baseline.redundant_experiments == 36


def _run_ablation_rows() -> dict[str, AblationRow]:
    """Run the same source-layer study used by the output orchestrator."""
    return {row["configuration"]: row for row in run_ablations(budget=BUDGET)}


def test_ablation_table_numbers_match_manuscript() -> None:
    """03_results.md §Per-mechanism ablation table (lines 30-34)."""
    rows = _run_ablation_rows()

    # Every configuration reaches the same clean optimum (column "Clean metric").
    for label, row in rows.items():
        assert row["clean_metric"] == 0.0, f"{label} clean metric drifted"

    # Reported metric column, rounded to manuscript's 5 dp.
    assert round(rows["full coordination"]["reported_metric"], 5) == 0.00121
    assert round(rows["no confirmation"]["reported_metric"], 5) == 0.01565
    assert round(rows["no dead-end registry"]["reported_metric"], 5) == 0.00121
    assert round(rows["no effect-size ranking"]["reported_metric"], 5) == 0.00121
    assert round(rows["no reorganization"]["reported_metric"], 5) == 0.00121

    # Experiments used / redundant re-probes columns.
    assert rows["full coordination"]["experiments_used"] == 36
    assert rows["full coordination"]["redundant_experiments"] == 0
    assert rows["no dead-end registry"]["experiments_used"] == 60
    assert rows["no dead-end registry"]["redundant_experiments"] == 36
    for label in ("no confirmation", "no effect-size ranking", "no reorganization"):
        assert rows[label]["experiments_used"] == 36, label
        assert rows[label]["redundant_experiments"] == 0, label


def test_confirmation_noise_inflation_is_about_thirteenfold() -> None:
    """03_results.md prose: "roughly 13x" (lines 36, 49)."""
    rows = _run_ablation_rows()
    full = rows["full coordination"]["reported_metric"]
    no_conf = rows["no confirmation"]["reported_metric"]
    ratio = no_conf / full
    assert 12.0 < ratio < 14.0, f"noise-inflation ratio {ratio} no longer ~13x"

    payload = build_ablation_payload(run_ablations(budget=BUDGET), budget=BUDGET)
    assert payload["noise_inflation_ratio_without_confirmation"] == ratio


def test_comparison_helpers_are_the_persisted_experiment_path() -> None:
    """The reusable source layer reproduces the matched-budget comparison."""
    objective = build_objective()
    coordinated, baseline = run_comparison(objective, budget=BUDGET)
    assert len(coordinated.trajectory) == 36
    assert len(baseline.trajectory) == BUDGET


def test_reported_metric_full_precision_is_pinned() -> None:
    """Tight tolerance on the underlying floats — catches sub-display drift."""
    rows = _run_ablation_rows()
    assert abs(rows["full coordination"]["reported_metric"] - _REPORTED_FULL) < 1e-12
    assert abs(rows["no confirmation"]["reported_metric"] - _NO_CONF_FULL) < 1e-12


def test_config_yaml_experiment_block_mirrors_code_defaults() -> None:
    """config.yaml `experiment:` is documented as mirroring the dataclass defaults;
    bind it so the hand-maintained shadow copy cannot silently drift from `src/`."""
    experiment = yaml.safe_load(_CONFIG_YAML.read_text())["experiment"]
    cfg = SearchConfig()
    obj = SyntheticObjective()

    # Keys backed by SearchConfig defaults.
    assert experiment["budget"] == cfg.budget == 60
    assert experiment["num_teams"] == cfg.num_teams == 3
    assert experiment["confirm_seeds"] == list(cfg.confirm_seeds) == [101, 202, 303]
    assert experiment["base_seed"] == cfg.base_seed == 7
    assert experiment["stagnation_window"] == cfg.stagnation_window == 10
    assert experiment["dead_end_threshold"] == cfg.dead_end_threshold == 3
    assert experiment["sigma"] == cfg.sigma == 2.0

    # Keys backed by SyntheticObjective defaults.
    assert experiment["dimensions"] == obj.dimensions == 4
    assert experiment["noise_scale"] == obj.noise_scale == 0.02
    assert experiment["ripple"] == obj.ripple == 0.15
