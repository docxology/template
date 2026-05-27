"""Tests for pymdp.yaml configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from simulation.pymdp_config import (
    apply_pymdp_overrides,
    config_hash,
    load_pymdp_config,
    pymdp_config_path,
)


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
