import json
import subprocess
import sys

import numpy as np
import pytest

from simulation.logging_utils import RunLogger
from simulation.pymdp_config import apply_pymdp_overrides, load_pymdp_config
from simulation.si_loop import sample_next_state, sample_observation
from simulation.si_runner import pymdp_available, run_and_persist, run_si_tmaze, write_si_artifacts
from simulation.tmaze_model import build_tmaze_generative_model


def test_tmaze_model_shapes() -> None:
    model = build_tmaze_generative_model()
    assert len(model["A"]) == 1
    assert int(model["A"][0].shape[0]) == 2
    assert int(model["policy_len"]) >= 2


def test_tmaze_model_uses_config_likelihood(project_root) -> None:
    cfg = apply_pymdp_overrides(load_pymdp_config(project_root), horizon=2)
    model = build_tmaze_generative_model(cfg)
    assert float(model["A"][0][0, 0]) == pytest.approx(cfg.tmaze.likelihood_diag)


def test_sampling_rejects_zero_mass_transition_and_observation() -> None:
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError, match="transition probabilities"):
        sample_next_state(rng, np.zeros((2, 2, 2)), state=0, action=0)
    with pytest.raises(ValueError, match="observation probabilities"):
        sample_observation(rng, np.zeros((2, 2)), state=0)


def test_sampling_rejects_non_finite_probability() -> None:
    rng = np.random.default_rng(0)
    transition = np.zeros((2, 2, 2))
    transition[:, 0, 0] = [np.nan, 1.0]
    with pytest.raises(ValueError, match="transition probabilities"):
        sample_next_state(rng, transition, state=0, action=0)


@pytest.mark.requires_pymdp
def test_si_tmaze_rollout(project_root, tmp_path) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    cfg = apply_pymdp_overrides(load_pymdp_config(project_root), steps=2, seed=123)
    logger = RunLogger(tmp_path / "log.jsonl")
    logger.fresh()
    result = run_si_tmaze(project_root, config=cfg, steps=2, logger=logger)
    assert result.steps == 2
    assert len(result.actions) == 2
    assert result.policy_len >= 2
    assert result.num_policies >= 2
    assert result.config_hash
    assert result.goal_reached
    assert logger.records()[0]["event"] == "si_tmaze_run_header"


@pytest.mark.requires_pymdp
def test_write_si_artifacts_schema(project_root, tmp_path) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    cfg = load_pymdp_config(project_root)
    logger = RunLogger(tmp_path / "log.jsonl", enabled=False)
    result = run_si_tmaze(project_root, config=cfg, steps=2, logger=logger)
    paths = write_si_artifacts(project_root, result, config=cfg)
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    trace = json.loads(paths["trace"].read_text(encoding="utf-8"))
    report = json.loads(paths["run_report"].read_text(encoding="utf-8"))
    assert summary["config"]["mode"] == cfg.mode
    assert len(trace["steps"]) == summary["steps"]
    assert report["log_record_count"] >= 0


@pytest.mark.requires_pymdp
def test_policy_inference_mode(project_root) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    cfg = apply_pymdp_overrides(load_pymdp_config(project_root), mode="policy_inference", seed=99, steps=2)
    result = run_si_tmaze(project_root, config=cfg)
    assert result.mode == "policy_inference"
    assert len(result.actions) == 2
    assert result.runtime_diagnostics["inference_step_count"] == 2
    assert result.runtime_diagnostics["policy_fallback_count"] >= 0


def test_simulate_cli_help(project_root) -> None:
    script = project_root / "scripts" / "simulate_si_tmaze.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "--seed" in proc.stdout


@pytest.mark.requires_pymdp
def test_run_and_persist(project_root) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    payload = run_and_persist(project_root)
    assert payload["paths"]["summary"].exists()
