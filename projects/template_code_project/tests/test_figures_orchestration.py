"""Tests for figure orchestration using real OptimizationResult data."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from src.experiment_config import ExperimentConfig, load_experiment_config
from src.figures import (
    generate_benchmark_visualization,
    generate_complexity_visualization,
    generate_convergence_plot,
    generate_convergence_rate_plot,
    generate_stability_visualization,
    generate_step_size_sensitivity_plot,
)
from src.optimizer import OptimizationResult, quadratic_optimum

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _sample_results(cfg: ExperimentConfig) -> dict[float, OptimizationResult]:
    _, f_star = quadratic_optimum(cfg.A_array(), cfg.b_array())
    history = [0.0, -0.2, f_star]
    return {
        0.1: OptimizationResult(
            solution=cfg.x0(),
            objective_value=f_star,
            iterations=2,
            converged=True,
            gradient_norm=1e-9,
            objective_history=history,
        ),
        1.5: OptimizationResult(
            solution=np.array([5.0]),
            objective_value=10.0,
            iterations=50,
            converged=False,
            gradient_norm=1.0,
            objective_history=[0.0, 1.0, 5.0, 10.0],
        ),
    }


@pytest.fixture
def figure_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr("src.figures.project_root", tmp_path)
    (tmp_path / "output" / "figures").mkdir(parents=True)
    return tmp_path


class TestFiguresOrchestration:
    def test_convergence_plot_uses_objective_history(self, figure_root: Path):
        cfg = load_experiment_config(PROJECT_ROOT)
        plot_path = generate_convergence_plot(_sample_results(cfg), config=cfg)
        assert plot_path.exists()

    def test_rate_plot_errors_match_optimum(self, figure_root: Path):
        cfg = ExperimentConfig(
            quadratic_A=((2.0,),),
            quadratic_b=(4.0,),
            step_sizes=(0.1,),
        )
        _, f_star = quadratic_optimum(cfg.A_array(), cfg.b_array())
        results = {
            0.1: OptimizationResult(
                solution=np.array([2.0]),
                objective_value=f_star,
                iterations=1,
                converged=True,
                gradient_norm=1e-10,
                objective_history=[0.0, f_star],
            )
        }
        plot_path = generate_convergence_rate_plot(results, config=cfg)
        assert plot_path.exists()

    def test_step_size_sensitivity_plot(self, figure_root: Path):
        cfg = load_experiment_config(PROJECT_ROOT)
        path = generate_step_size_sensitivity_plot(_sample_results(cfg), config=cfg)
        assert path.exists()

    def test_complexity_visualization(self, figure_root: Path):
        cfg = load_experiment_config(PROJECT_ROOT)
        path = generate_complexity_visualization(_sample_results(cfg), config=cfg)
        assert path.exists()

    def test_stability_visualization(self, figure_root: Path):
        report = figure_root / "output" / "reports" / "stability_analysis.json"
        report.parent.mkdir(parents=True)
        report.write_text(json.dumps({"stability_score": 0.95}))
        path = generate_stability_visualization(report)
        assert path is not None and path.exists()

    def test_benchmark_visualization(self, figure_root: Path):
        report = figure_root / "output" / "reports" / "performance_benchmark.json"
        report.parent.mkdir(parents=True)
        report.write_text(json.dumps({"execution_time": 0.001}))
        path = generate_benchmark_visualization(report)
        assert path is not None and path.exists()

    def test_stability_visualization_none_path(self):
        assert generate_stability_visualization(None) is None

    def test_benchmark_visualization_none_path(self):
        assert generate_benchmark_visualization(None) is None
