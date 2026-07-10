"""Tests for the deterministic demonstration study (no mocks, real computation)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from registered_report import (
    build_deviation_ledger,
    deviation_timeline,
    freeze_registration,
)
from registered_report.demo_study import (
    analysis_plan_stages,
    generate_demo_dataset,
    hypothesis_outcome_map,
    mean,
    permutation_null_distribution,
    run_permutation_test,
    run_registered_analysis,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_registration() -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        json.loads((PROJECT_ROOT / "data" / "example_registration.json").read_text(encoding="utf-8")),
    )


class TestDemoDataset:
    """Cover deterministic dataset synthesis and its guards."""

    def test_dataset_is_deterministic_for_a_fixed_seed(self) -> None:
        first = generate_demo_dataset(seed=20260709, n_per_group=24, effect=0.8)
        second = generate_demo_dataset(seed=20260709, n_per_group=24, effect=0.8)

        assert first == second
        assert first.n_control == 24
        assert first.n_treatment == 24

    def test_different_seeds_produce_different_data(self) -> None:
        assert generate_demo_dataset(seed=1) != generate_demo_dataset(seed=2)

    def test_invalid_sizes_and_sigma_are_rejected(self) -> None:
        with pytest.raises(ValueError):
            generate_demo_dataset(seed=1, n_per_group=0)
        with pytest.raises(ValueError):
            generate_demo_dataset(seed=1, sigma=0.0)

    def test_mean_rejects_empty_sequence(self) -> None:
        assert mean((2.0, 4.0)) == 3.0
        with pytest.raises(ValueError):
            mean(())


class TestPermutationTest:
    """Cover the registered permutation test and its null distribution."""

    def test_positive_effect_is_significant_and_reproducible(self) -> None:
        dataset = generate_demo_dataset(seed=20260709, n_per_group=24, effect=0.8)

        result = run_permutation_test(dataset, seed=20260709, n_permutations=2000)
        again = run_permutation_test(dataset, seed=20260709, n_permutations=2000)

        assert result == again
        assert result.observed_difference > 0.0
        assert result.p_value < 0.05
        # Add-one correction keeps the p-value strictly positive.
        assert result.p_value == round((result.n_at_least_as_extreme + 1) / 2001, 6)
        assert result.p_value > 0.0

    def test_null_effect_is_not_significant(self) -> None:
        dataset = generate_demo_dataset(seed=7, n_per_group=30, effect=0.0)

        result = run_permutation_test(dataset, seed=7, n_permutations=500)

        assert result.p_value > 0.05

    def test_null_distribution_length_and_guard(self) -> None:
        dataset = generate_demo_dataset(seed=3, n_per_group=10, effect=0.5)

        distribution = permutation_null_distribution(dataset, seed=3, n_permutations=128)

        assert len(distribution) == 128
        with pytest.raises(ValueError):
            permutation_null_distribution(dataset, seed=3, n_permutations=0)


class TestRegisteredAnalysis:
    """Cover the plan-driven analysis binding used by the manuscript."""

    def test_analysis_reads_plan_seed_and_alpha(self) -> None:
        frozen = freeze_registration(load_registration())

        summary = run_registered_analysis(frozen)

        assert summary["seed"] == 20260709
        assert summary["alpha"] == 0.05
        assert summary["primary_model"] == "permutation_test"
        assert summary["primary_outcome"] == "primary_score"
        assert summary["n_control"] == 24
        assert summary["significant"] is True
        assert summary["p_value"] < summary["alpha"]
        assert summary["outcomes"] == ["primary_score"]

    def test_analysis_matches_the_committed_artifact(self) -> None:
        artifact_path = PROJECT_ROOT / "output" / "data" / "demo_analysis.json"
        if not artifact_path.is_file():
            pytest.skip("demo_analysis.json is a disposable output; run scripts/generate_figures.py first")
        frozen = freeze_registration(load_registration())

        summary = run_registered_analysis(frozen)
        stored = json.loads(artifact_path.read_text(encoding="utf-8"))

        assert summary == stored

    def test_analysis_defaults_outcome_when_registration_has_none(self) -> None:
        summary = run_registered_analysis({"analysis_plan": {"seed": 5, "alpha": 0.05}})

        assert summary["primary_outcome"] == "primary_score"
        assert summary["primary_model"] == "permutation_test"


class TestDiagramData:
    """Cover the pure figure-data helpers used by the rendering script."""

    def test_hypothesis_outcome_map_links_registered_fields(self) -> None:
        frozen = freeze_registration(load_registration())

        edges = hypothesis_outcome_map(frozen)

        assert len(edges) == 1
        assert edges[0].hypothesis_id == "H1"
        assert edges[0].outcome == "primary_score"
        assert edges[0].analysis == "two-sided permutation test"

    def test_hypothesis_map_reuses_last_outcome_and_skips_non_mappings(self) -> None:
        registration = {
            "hypotheses": [
                {"id": "H1", "claim": "first"},
                "not-a-mapping",
                {"id": "H2", "claim": "second"},
            ],
            "outcomes": [{"name": "only_outcome", "measure": "m", "analysis": "a"}],
        }

        edges = hypothesis_outcome_map(registration)

        assert [edge.hypothesis_id for edge in edges] == ["H1", "H2"]
        assert edges[1].outcome == "only_outcome"

    def test_hypothesis_map_handles_missing_outcomes(self) -> None:
        edges = hypothesis_outcome_map({"hypotheses": [{"id": "H1", "claim": "c"}]})

        assert edges[0].outcome == ""

    def test_analysis_plan_stages_mark_the_lock_boundary(self) -> None:
        stages = analysis_plan_stages()

        locked = [stage for stage in stages if stage.locks_before_results]
        post = [stage for stage in stages if not stage.locks_before_results]

        assert [stage.index for stage in stages] == [0, 1, 2, 3, 4, 5]
        assert len(locked) == 4
        assert post[0].key == "compare"

    def test_deviation_timeline_preserves_ledger_order_and_severity(self) -> None:
        frozen = freeze_registration(load_registration())
        executed = {"outcomes": ["primary_score", "secondary_score"], "primary_model": "linear_model"}
        deviations = [
            {"kind": "outcome", "target": "secondary_score", "rationale": "exploratory robustness endpoint"},
            {"kind": "model", "target": "linear_model", "rationale": "robustness sensitivity"},
        ]

        ledger = build_deviation_ledger(frozen, executed, deviations)
        events = deviation_timeline(ledger)

        assert [event.severity for event in events] == ["ok", "warning", "warning"]
        assert events[0].registered is True
        assert events[1].documented is True
