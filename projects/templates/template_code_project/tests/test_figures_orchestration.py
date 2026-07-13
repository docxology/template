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
        results = _sample_results(cfg)
        _, f_star = quadratic_optimum(cfg.A_array(), cfg.b_array())
        plot_path = generate_convergence_plot(results, config=cfg)
        assert plot_path.exists()

        companion = figure_root / "output" / "data" / "convergence_plot.json"
        assert companion.exists()
        payload = json.loads(companion.read_text(encoding="utf-8"))
        stable = payload["0.1"]
        final_objective = stable["objectives"][-1]
        assert isinstance(final_objective, (int, float))
        assert final_objective == pytest.approx(f_star, rel=1e-6, abs=1e-6)

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
        report.write_text(json.dumps({"schema_version": "template_code_project/performance_benchmark/v2"}))
        path = generate_benchmark_visualization(report)
        assert path is not None and path.exists()
        first_bytes = path.read_bytes()
        second_path = generate_benchmark_visualization(report)
        assert second_path.read_bytes() == first_bytes

    def test_stability_visualization_none_path(self):
        assert generate_stability_visualization(None) is None

    def test_benchmark_visualization_none_path(self):
        assert generate_benchmark_visualization(None) is None


class TestBackendProfile:
    """Test BackendProfile pure analysis methods (covers uncovered complexity lines)."""

    def test_effective_max_stable_alpha_uses_explicit_value(self):
        """Line 53: explicit max_stable_alpha overrides the 2/L formula."""
        from src.figures.scientific_complexity import BackendProfile

        p = BackendProfile(
            name="Custom",
            hessian_scale=4.0,
            description="explicit override",
            max_stable_alpha=0.3,  # not 2/4=0.5
        )
        assert p.effective_max_stable_alpha() == 0.3

    def test_effective_max_stable_alpha_derived(self):
        """When max_stable_alpha is None, returns 2/hessian_scale."""
        from src.figures.scientific_complexity import BackendProfile

        p = BackendProfile(name="Derived", hessian_scale=2.0, description="derived")
        assert p.effective_max_stable_alpha() == pytest.approx(1.0)

    def test_effective_label_alpha_uses_explicit_value(self):
        """Line 58-59: explicit label_alpha is returned directly."""
        from src.figures.scientific_complexity import BackendProfile

        p = BackendProfile(
            name="WithLabel",
            hessian_scale=1.0,
            description="label override",
            label_alpha=0.42,
        )
        assert p.effective_label_alpha() == 0.42

    def test_effective_label_alpha_derived(self):
        """Line 60: label_alpha defaults to 0.5 * max_stable_alpha."""
        from src.figures.scientific_complexity import BackendProfile

        p = BackendProfile(name="NoLabel", hessian_scale=1.0, description="no label")
        # effective_max_stable_alpha = 2/1 = 2.0 → label = 0.5 * 2.0 = 1.0
        assert p.effective_label_alpha() == pytest.approx(1.0)

    def test_profile_stable_region_returns_zero_to_bound(self):
        """Line 196: profile_stable_region always starts at 0.0."""
        from src.figures.scientific_complexity import BackendProfile, profile_stable_region

        p = BackendProfile(name="TestP", hessian_scale=5.0, description="test")
        lo, hi = profile_stable_region(p)
        assert lo == 0.0
        assert hi == pytest.approx(2.0 / 5.0)

    def test_compare_profiles_at_alpha_returns_one_row_per_profile(self):
        """Lines 232-247: compare_profiles_at_alpha covers the loop + dict build."""
        from src.figures.scientific_complexity import (
            BackendProfile,
            compare_profiles_at_alpha,
        )

        profiles = (
            BackendProfile(name="A", hessian_scale=1.0, description="A"),
            BackendProfile(name="B", hessian_scale=2.0, description="B"),
        )
        rows = compare_profiles_at_alpha(0.4, profiles=profiles)
        assert len(rows) == 2
        for row in rows:
            assert "name" in row
            assert "contraction" in row
            assert "theoretical_complexity" in row
            assert "optimal_alpha" in row
            assert "is_stable" in row

    def test_compare_profiles_at_alpha_uses_default_backend_profiles(self):
        """compare_profiles_at_alpha works with the default BACKEND_PROFILES tuple."""
        from src.figures.scientific_complexity import BACKEND_PROFILES, compare_profiles_at_alpha

        rows = compare_profiles_at_alpha(0.1)
        assert len(rows) == len(BACKEND_PROFILES)
        # α=0.1 with H=1: rho=|1-0.1|=0.9 → stable
        assert rows[0]["is_stable"] is True
