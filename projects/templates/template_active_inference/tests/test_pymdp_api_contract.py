"""Actual pinned Agent vector API, Bayesian oracle and policy evidence."""

from __future__ import annotations

from importlib.metadata import version
from pathlib import Path

import numpy as np
import pytest

from simulation.logging_utils import RunLogger
from simulation.pymdp_config import apply_pymdp_overrides, load_pymdp_config
from simulation.pymdp_runtime import construct_agent_with_diagnostics
from simulation.si_belief import marginal_state_belief
from simulation.si_runner import run_si_tmaze
from simulation.tmaze_model import build_tmaze_generative_model


@pytest.mark.parametrize("prior", [[1.0, 0.0], [0.8, 0.2], [0.5, 0.5]])
def test_actual_filter_matches_independent_bayes_with_column_model_prior(
    project_root: Path, prior: list[float]
) -> None:
    assert version("inferactively-pymdp") == "1.0.1"
    config = load_pymdp_config(project_root)
    model = build_tmaze_generative_model(config)
    model["D"] = [np.asarray(prior, dtype=np.float64).reshape(2, 1)]
    agent, diagnostics = construct_agent_with_diagnostics(
        project_root, config=config, model=model, policy_len=config.horizon, context="independent_bayes_contract"
    )
    observed = marginal_state_belief(agent.infer_states([np.array([0], dtype=np.int32)], agent.D))
    likelihood = np.asarray(model["A"][0])[0]
    expected = likelihood * np.asarray(prior)
    expected = expected / expected.sum()
    assert np.max(np.abs(observed - expected)) < 1e-6, (observed, expected)
    assert diagnostics["unexpected_warning_count"] == 0


@pytest.mark.parametrize("horizon", [2, 3])
def test_actual_policy_inference_produces_normalized_posterior_and_finite_efe(
    project_root: Path, tmp_path: Path, horizon: int
) -> None:
    config = apply_pymdp_overrides(
        load_pymdp_config(project_root),
        mode="policy_inference",
        horizon=horizon,
        seed=7,
        steps=2,
        logging_enabled=False,
    )
    result = run_si_tmaze(project_root, config=config, logger=RunLogger(tmp_path / "unused.jsonl", enabled=False))
    assert result.runtime_diagnostics["policy_fallback_count"] == 0
    assert len(result.trace_steps) == 2
    for step in result.trace_steps:
        assert step["policy_method"] == "infer_policies"
        assert step["q_pi_normalized"] is True
        assert step["expected_free_energy_available"] is True
        assert np.isfinite(step["expected_free_energy_values"]).all()
