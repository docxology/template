"""Tests for shared experiment configuration loading."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from src.experiment_config import ExperimentConfig, load_experiment_config
from src.invariants import OptimizerSweepConfig

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestExperimentConfig:
    def test_load_from_project_yaml(self):
        cfg = load_experiment_config(PROJECT_ROOT)
        assert len(cfg.step_sizes) == 6
        assert cfg.step_sizes == (0.01, 0.1, 0.5, 1.0, 1.5, 2.5)
        assert cfg.max_iterations == 1000

    def test_defaults_when_missing_file(self, tmp_path: Path):
        cfg = load_experiment_config(tmp_path)
        assert cfg.step_sizes == (0.01, 0.1, 0.5, 1.0, 1.5, 2.5)

    def test_array_helpers(self):
        cfg = ExperimentConfig()
        np.testing.assert_allclose(cfg.A_array(), [[1.0]])
        np.testing.assert_allclose(cfg.b_array(), [1.0])
        np.testing.assert_allclose(cfg.x0(), [0.0])

    def test_to_sweep_config(self):
        cfg = ExperimentConfig(step_sizes=(0.1, 0.5), initial_point=0.5)
        sweep = cfg.to_sweep_config()
        assert isinstance(sweep, OptimizerSweepConfig)
        assert sweep.step_sizes == (0.1, 0.5)
        np.testing.assert_allclose(sweep.x0(), [0.5])

    def test_coerce_list_initial_point(self, tmp_path: Path):
        config_path = tmp_path / "manuscript" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("experiment:\n  initial_point: [0.25]\n  step_sizes: [0.1]\n")
        cfg = load_experiment_config(tmp_path)
        assert cfg.initial_point == pytest.approx(0.25)

    def test_empty_optional_lists_use_defaults(self, tmp_path: Path):
        config_path = tmp_path / "manuscript" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("experiment:\n  step_sizes: []\n")
        cfg = load_experiment_config(tmp_path)
        assert len(cfg.step_sizes) == 6

    def test_scalar_matrix_and_int_lists(self, tmp_path: Path):
        config_path = tmp_path / "manuscript" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("experiment:\n  step_sizes: 0.5\n  quadratic_b: 2.0\n  benchmark_dimensions: 3\n")
        cfg = load_experiment_config(tmp_path)
        assert cfg.step_sizes == (0.5,)
        assert cfg.quadratic_b == (2.0,)
        assert cfg.benchmark_dimensions == (3,)

    def test_invalid_matrix_falls_back_to_default(self, tmp_path: Path):
        config_path = tmp_path / "manuscript" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("experiment:\n  quadratic_A: 1.0\n")
        cfg = load_experiment_config(tmp_path)
        assert cfg.quadratic_A == ((1.0,),)

    def test_empty_initial_point_list_defaults_to_zero(self, tmp_path: Path):
        config_path = tmp_path / "manuscript" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("experiment:\n  initial_point: []\n")
        cfg = load_experiment_config(tmp_path)
        assert cfg.initial_point == 0.0

    def test_load_without_project_root_uses_module_parent(self):
        cfg = load_experiment_config(None)
        assert len(cfg.step_sizes) >= 1
