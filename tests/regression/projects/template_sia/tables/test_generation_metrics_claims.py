"""Regression pins for the deterministic SIA self-improvement harness.

Manuscript: projects/templates/template_sia/manuscript/03_results.md.

This exemplar is a *self-improvement* harness: a Meta -> Target -> Feedback
loop that, under fixture replay (``sia.live: false`` in manuscript/config.yaml,
the CI default), advances a target agent across three generations and records
an accuracy metric each time. The load-bearing manuscript claims are the
self-refinement measurement itself -- accuracy remains 1.0000 across three
genuinely executed threshold variants, for a final-minus-first delta of 0.0000
and a final injected token ``accuracy=1.0000 (n=6)``. These pins bind those values
to the source: each value is re-derived by running the real
``infrastructure.sia.run_sia_loop`` in fixture-replay mode (which copies the
recorded per-generation fixtures into a fresh output tree and reads each
``results.json`` verbatim via the real ``EvaluationResult`` contract) -- never
by hand-copying a rendered manuscript token, and never in a live /
non-deterministic mode.

Fixture replay executes no generated agent code and calls no external LLM, in
line with the exemplar's determinism contract and the repo no-mock policy: the
run uses real deterministic objects and the real loop state machine only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_sia"


# SUBMODULAR-SIA-1: the exemplar package is a regular nested package
# (``src/template_sia/``) whose modules import via absolute
# ``template_sia.*`` paths, so the exemplar imports directly -- no
# project-unique alias or scoped meta-path finder is needed. The alias
# machinery existed only to resolve the pre-split flat layout's relative
# ``from ..generation_records import ...`` imports, which no longer exist.
from template_sia.loop.loop import build_run_config  # noqa: E402

# The infrastructure loop + config live one import below; use them directly to
# run into an isolated output tree without touching the committed run.
from infrastructure.sia import RunConfig, run_sia_loop  # noqa: E402


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int) -> None:
    tolerance = entry.get("abs_tolerance", 0)
    assert observed == pytest.approx(entry["value"], abs=tolerance)


@pytest.fixture(scope="module")
def replay_evaluations(tmp_path_factory: pytest.TempPathFactory) -> list[Any]:
    """Re-derive the three-generation fixture-replay metrics from the real loop.

    Runs ``infrastructure.sia.run_sia_loop`` with the exemplar's own config
    (``build_run_config``) but redirected to an isolated output directory, so
    the re-derivation is a genuine fresh run and never reads the committed
    ``output/runs/run_1/run_summary.json``. ``live`` is forced ``False`` to pin
    the deterministic fixture-replay path the manuscript describes.
    """

    base = build_run_config(PROJECT_ROOT, live=False)
    assert base.live is False, "regression pins must use deterministic fixture replay"
    isolated_out = tmp_path_factory.mktemp("sia_replay")
    config = RunConfig(
        task_dir=base.task_dir,
        output_dir=isolated_out,
        run_id=base.run_id,
        max_generations=base.max_generations,
        live=False,
        fixtures_dir=base.fixtures_dir,
        target_timeout_sec=base.target_timeout_sec,
        llm_model=base.llm_model,
    )
    artifacts = run_sia_loop(config)
    evaluations = [artifact.evaluation for artifact in artifacts]
    assert all(ev is not None for ev in evaluations), "every replayed generation must evaluate"
    return evaluations


def test_generation_metric_progression_claims_rederive_from_source(
    load_pinned_values: Any,
    replay_evaluations: list[Any],
) -> None:
    """Bind the fixture-replay metrics table headline numbers to a fresh source run.

    03_results.md / SIA generation metrics (fixture replay) table + final-token
    prose. The self-refinement signal (accuracy 0.5000 -> ... -> 0.8333 across
    three generations, n=6) is what this exemplar exists to demonstrate.
    """

    pinned = load_pinned_values("template_sia")
    evaluations = replay_evaluations

    # Loop length: the three-generation Meta -> Target -> Feedback cycle.
    _assert_pin_matches(_pin(pinned, "generation_count"), len(evaluations))

    # Seed baseline and final accuracy. Equality is load-bearing: it prevents
    # the manuscript from inventing improvement across a saturated toy task.
    _assert_pin_matches(_pin(pinned, "first_generation_accuracy"), evaluations[0].metric_value)
    _assert_pin_matches(_pin(pinned, "final_generation_accuracy"), evaluations[-1].metric_value)

    # Final sample count backing the reported accuracy=0.8333 (n=6) token.
    _assert_pin_matches(_pin(pinned, "final_generation_n_samples"), evaluations[-1].n_samples)


def test_self_improvement_delta_claim_rederives_from_source(
    load_pinned_values: Any,
    replay_evaluations: list[Any],
) -> None:
    """Bind the measured delta (final - first) to a fresh source run.

    03_results.md / 'Metric delta (final - first generation): 0.0000'. Computed
    from the real loop's first and last evaluation.metric_value, not read from
    the rendered SIA_METRIC_DELTA token.
    """

    pinned = load_pinned_values("template_sia")
    evaluations = replay_evaluations

    delta = evaluations[-1].metric_value - evaluations[0].metric_value
    _assert_pin_matches(_pin(pinned, "metric_delta_final_minus_first"), delta)


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    Non-vacuity control (feedback-verify-not-trust-machine-proof): proves the
    assertions above can actually fail, so a green run means the re-derivation
    genuinely matched the pin -- not that the comparison is a no-op.
    """

    pinned = load_pinned_values("template_sia")
    entry = dict(_pin(pinned, "final_generation_accuracy"))
    observed = entry["value"]
    entry["value"] = observed + 0.5  # perturb the pinned ground truth well beyond tolerance

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
