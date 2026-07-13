"""Tests for pymdp.yaml configuration loading."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from simulation.pymdp_config import (
    PymdpConfig,
    apply_pymdp_overrides,
    config_hash,
    config_snapshot,
    default_pymdp_config,
    load_pymdp_config,
)
from simulation.si_belief import (
    belief_entropy,
    marginal_state_belief,
    qs_marginal_state1,
    state_inference_action,
    state_inference_next_obs,
)
from simulation.tmaze_model import (
    build_tmaze_generative_model,
    spec_from_config,
)


# ---- pymdp_config tests ----


def test_load_default_pymdp_config(project_root: Path) -> None:
    cfg = load_pymdp_config(project_root)
    assert cfg.horizon == 2
    assert cfg.steps == 2
    assert cfg.mode == "state_inference"
    assert cfg.tmaze.likelihood_diag == pytest.approx(0.9)


def test_apply_overrides(project_root: Path) -> None:
    cfg = load_pymdp_config(project_root)
    updated = apply_pymdp_overrides(cfg, steps=5, horizon=3, seed=42, mode="policy_inference")
    assert updated.steps == 5
    assert updated.horizon == 3
    assert updated.random_seed == 42
    assert updated.mode == "policy_inference"


def test_config_hash_stable(project_root: Path) -> None:
    cfg = load_pymdp_config(project_root)
    assert config_hash(cfg) == config_hash(load_pymdp_config(project_root))


def test_custom_yaml(tmp_path: Path) -> None:
    custom = tmp_path / "custom_pymdp.yaml"
    custom.write_text(
        "horizon: 4\nsteps: 3\nrandom_seed: 7\nmode: policy_inference\n",
        encoding="utf-8",
    )
    cfg = load_pymdp_config(tmp_path, config_path=custom)
    assert cfg.horizon == 4
    assert cfg.steps == 3
    assert cfg.random_seed == 7
    assert cfg.mode == "policy_inference"


def test_pymdp_config_rejects_invalid_mode(tmp_path: Path) -> None:
    bad = tmp_path / "pymdp.yaml"
    bad.write_text("mode: invalid_mode\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported pymdp mode"):
        load_pymdp_config(tmp_path, config_path=bad)


def test_load_pymdp_config_missing_file_returns_default(tmp_path: Path) -> None:
    """When the config file is absent, load_pymdp_config returns the default."""
    cfg = load_pymdp_config(tmp_path)  # no pymdp.yaml in tmp_path
    default = default_pymdp_config()
    assert cfg.horizon == default.horizon
    assert cfg.mode == default.mode
    assert cfg.random_seed == default.random_seed


def test_default_pymdp_config_is_plain_dataclass() -> None:
    """default_pymdp_config returns a PymdpConfig with factory defaults."""
    cfg = default_pymdp_config()
    assert isinstance(cfg, PymdpConfig)
    assert cfg.horizon == 2
    assert cfg.mode == "state_inference"


def test_apply_overrides_logging_enabled() -> None:
    """apply_pymdp_overrides must update the logging.enabled flag."""
    cfg = default_pymdp_config()
    assert cfg.logging.enabled is True
    updated = apply_pymdp_overrides(cfg, logging_enabled=False)
    assert updated.logging.enabled is False
    # All other fields remain unchanged.
    assert updated.horizon == cfg.horizon
    assert updated.mode == cfg.mode


def test_apply_overrides_no_args_is_identity() -> None:
    """Calling apply_pymdp_overrides with no keyword arguments returns an equivalent config."""
    cfg = default_pymdp_config()
    unchanged = apply_pymdp_overrides(cfg)
    assert unchanged == cfg


def test_config_snapshot_round_trips_mode() -> None:
    """config_snapshot must serialise and preserve all top-level fields."""
    cfg = default_pymdp_config()
    snapshot = config_snapshot(cfg)
    assert snapshot["mode"] == cfg.mode
    assert snapshot["horizon"] == cfg.horizon
    assert snapshot["random_seed"] == cfg.random_seed
    assert snapshot["policy_len"] == cfg.policy_len
    assert isinstance(snapshot["comparison"]["horizons"], list)


def test_policy_len_equals_horizon() -> None:
    """PymdpConfig.policy_len is an alias for horizon."""
    cfg = default_pymdp_config()
    assert cfg.policy_len == cfg.horizon


# ---- tmaze_model tests ----


def test_build_tmaze_model_from_pymdp_config() -> None:
    """build_tmaze_generative_model must accept a PymdpConfig and extract TMazeSpec."""
    cfg = default_pymdp_config()
    model = build_tmaze_generative_model(cfg)
    assert isinstance(model, dict)
    assert "A" in model and "B" in model and "C" in model and "D" in model
    # Policy len comes from config.horizon.
    assert model["policy_len"] == cfg.horizon


def test_spec_from_config_maps_fields() -> None:
    """spec_from_config must map every PymdpConfig field to the matching TMazeSpec field."""
    cfg = default_pymdp_config()
    spec = spec_from_config(cfg)
    assert spec.num_states == cfg.tmaze.num_states
    assert spec.likelihood_diag == pytest.approx(cfg.tmaze.likelihood_diag)
    assert spec.seed == cfg.random_seed
    assert spec.policy_len == cfg.policy_len


# ---- si_belief tests ----


def test_marginal_state_belief_1d_input() -> None:
    """A plain 1-D belief vector must pass through unchanged (normalised)."""
    q = [np.array([0.3, 0.7], dtype=np.float64)]
    out = marginal_state_belief(q)
    assert abs(float(out.sum()) - 1.0) < 1e-12
    assert abs(float(out[1]) - 0.7) < 1e-9


def test_marginal_state_belief_2d_input_takes_last_row() -> None:
    """A 2-D belief (rows = time steps) must return the last row."""
    # Two time steps; the second row is the more-concentrated belief.
    q = [np.array([[0.5, 0.5], [0.1, 0.9]], dtype=np.float64)]
    out = marginal_state_belief(q)
    assert abs(float(out.sum()) - 1.0) < 1e-12
    # After normalisation the dominant component should be state 1.
    assert float(out[1]) > float(out[0])


def test_marginal_state_belief_clips_to_positive() -> None:
    """Very small or near-zero probabilities must be clipped to 1e-12, not NaN."""
    q = [np.array([0.0, 0.0], dtype=np.float64)]
    out = marginal_state_belief(q)
    assert np.all(np.isfinite(out))


def test_belief_entropy_uniform_is_log2() -> None:
    q = [np.array([0.5, 0.5], dtype=np.float64)]
    assert abs(belief_entropy(q) - np.log(2.0)) < 1e-9


def test_qs_marginal_state1_single_element() -> None:
    """When the belief has only 1 state, qs_marginal_state1 returns the last (=only) element."""
    q = [np.array([1.0], dtype=np.float64)]
    # size < 2, so the function returns q_flat[-1]
    result = qs_marginal_state1(q)
    assert abs(result - 1.0) < 1e-12


def test_state_inference_action_and_next_obs() -> None:
    """state_inference_action and state_inference_next_obs implement the rule correctly."""
    # obs < goal_obs (0 < 1): move toward goal
    assert state_inference_action(0, 1) == 0
    # obs >= goal_obs (1 >= 1): stay at goal
    assert state_inference_action(1, 1) == 1

    # action=0 from obs=0: next obs advances to 1
    assert state_inference_next_obs(0, 0) == 1
    # action=1 from obs=0: stay
    assert state_inference_next_obs(0, 1) == 0
    # already at obs=1: stays regardless of action
    assert state_inference_next_obs(1, 0) == 1
