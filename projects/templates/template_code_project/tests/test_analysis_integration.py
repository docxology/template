"""Integration tests for analysis orchestration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.analysis import (
    extract_optimization_metadata,
    run_convergence_experiment,
    run_performance_benchmarking,
    run_stability_analysis,
    save_optimization_results,
    infrastructure_context,
)
from src.experiment_config import ExperimentConfig, load_experiment_config
from src.optimizer import OptimizationResult
from src.project_paths import project_root_context


@pytest.fixture(autouse=True)
def _isolated_project_root(tmp_path: Path):
    with project_root_context(tmp_path):
        yield


try:
    from src.figures import (
        generate_benchmark_visualization,
        generate_stability_visualization,
    )

    FIGURES_AVAILABLE = True
except ImportError:
    FIGURES_AVAILABLE = False


class TestRunConvergenceExperiment:
    def test_returns_all_configured_step_sizes(self):
        cfg = load_experiment_config(PROJECT_ROOT)
        results = run_convergence_experiment(config=cfg)
        assert len(results) == len(cfg.step_sizes)
        assert set(results.keys()) == {float(s) for s in cfg.step_sizes}

    def test_on_step_callback(self):
        cfg = ExperimentConfig(step_sizes=(0.1, 0.5))
        seen: list[float] = []

        def on_step(alpha: float, _result: OptimizationResult) -> None:
            seen.append(alpha)

        run_convergence_experiment(on_step=on_step, config=cfg)
        assert seen == [0.1, 0.5]


class TestSaveOptimizationResults:
    def test_csv_serializes_full_solution_vector(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        results = {
            0.1: OptimizationResult(
                solution=np.array([1.0, 2.0]),
                objective_value=-1.5,
                iterations=3,
                converged=True,
                gradient_norm=1e-9,
            )
        }
        path = save_optimization_results(results)
        text = path.read_text()
        assert "1.000000;2.000000" in text


class TestScientificAnalysis:
    def test_stability_analysis_writes_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        path = run_stability_analysis()
        assert path.exists()
        data = json.loads(path.read_text())
        assert "stability_score" in data

    def test_benchmark_writes_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        path = run_performance_benchmarking()
        assert path.exists()
        first_bytes = path.read_bytes()
        second_path = run_performance_benchmarking()
        assert second_path.read_bytes() == first_bytes
        data = json.loads(path.read_text())
        assert data["schema_version"] == "template_code_project/performance_benchmark/v2"
        assert data["checks"]["all_inputs_evaluated"] is True
        assert data["checks"]["all_objective_values_finite"] is True
        assert "execution_time" not in data
        assert "timestamp" not in data


class TestExtractOptimizationMetadata:
    def test_extracts_best_step_size(self):
        results = {
            0.1: OptimizationResult(
                solution=np.array([0.5]),
                objective_value=-0.25,
                iterations=10,
                converged=True,
                gradient_norm=1e-6,
                objective_history=[0.0, -0.25],
            ),
            0.5: OptimizationResult(
                solution=np.array([1.0]),
                objective_value=-0.5,
                iterations=2,
                converged=True,
                gradient_norm=1e-9,
                objective_history=[0.0, -0.5],
            ),
        }
        meta = extract_optimization_metadata(results)
        assert meta is not None
        assert meta["best_step_size"] == 0.5

    def test_extract_metadata_failure_on_empty(self):
        assert extract_optimization_metadata({}) is None


class TestAnalysisStandalonePaths:
    def test_stability_analysis_without_infra(self, tmp_path: Path):
        with infrastructure_context(False):
            path = run_stability_analysis()
        assert path.exists()

    def test_benchmark_without_infra(self, tmp_path: Path):
        with infrastructure_context(False):
            path = run_performance_benchmarking()
        assert path.exists()

    def test_stability_score_standalone(self):
        cfg = ExperimentConfig(stability_starting_points=(0.0, 10.0))
        from src.analysis import _stability_score_from_runs

        score, max_error, recs = _stability_score_from_runs(
            [np.array([0.0]), np.array([10.0])],
            cfg.A_array(),
            cfg.b_array(),
        )
        assert 0.0 <= score <= 1.0
        assert max_error >= 0.0
        assert isinstance(recs, list)

    def test_benchmark_timings_standalone(self):
        from src.analysis import _benchmark_timings

        cfg = ExperimentConfig()
        avg = _benchmark_timings([np.array([0.0])], cfg.A_array(), cfg.b_array(), iterations=2)
        assert avg > 0.0


class TestPublishingHelpers:
    def test_citations_and_save_materials(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        from src.analysis import generate_citations_from_metadata, save_publishing_materials

        meta = {
            "title": "Test",
            "description": "desc",
            "algorithm": "GD",
            "best_step_size": 0.1,
            "final_objective": -0.5,
            "iterations_to_convergence": 10,
        }
        citations = generate_citations_from_metadata(meta)
        save_publishing_materials(meta, citations)
        assert (tmp_path / "output" / "citations" / "optimization_metadata.json").exists()

    def test_save_publishing_materials_handles_missing_keys(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        from src.analysis import save_publishing_materials

        save_publishing_materials({"title": "only title"}, None)
        assert (tmp_path / "output" / "citations" / "optimization_metadata.json").exists()


class TestValidationAndRegistration:
    def test_validate_and_save_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        if not __import__("src.analysis", fromlist=["INFRASTRUCTURE_AVAILABLE"]).INFRASTRUCTURE_AVAILABLE:
            pytest.skip("Infrastructure not available")
        (tmp_path / "output" / "figures").mkdir(parents=True)
        (tmp_path / "output" / "figures" / "convergence_plot.png").write_bytes(b"png")

        from src.analysis import save_validation_report, validate_generated_outputs

        report = validate_generated_outputs()
        if report:
            path = save_validation_report(report)
            assert path is not None and path.exists()

    def test_register_figure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        (tmp_path / "output" / "figures").mkdir(parents=True)
        from src.analysis import register_figure

        register_figure()
        registry = tmp_path / "output" / "figures" / "figure_registry.json"
        assert registry.exists()


class TestMainPipelineSmoke:
    def test_main_writes_core_artifacts(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        import shutil

        shutil.copytree(PROJECT_ROOT / "manuscript", tmp_path / "manuscript")

        from src.analysis import main

        main()

        assert (tmp_path / "output" / "figures" / "convergence_plot.png").exists()
        assert (tmp_path / "output" / "data" / "optimization_results.csv").exists()


@pytest.mark.skipif(not FIGURES_AVAILABLE, reason="Figure modules not available")
class TestStabilityAnalysis:
    """Test numerical stability analysis functions."""

    def test_stability_analysis_execution(self):
        result_path = run_stability_analysis()

        if result_path:
            assert result_path.exists()
            assert result_path.is_file()

            data = json.loads(result_path.read_text())
            assert "stability_score" in data
            assert "function_name" in data
            assert "recommendations" in data
            assert isinstance(data["stability_score"], (int, float))
            assert 0.0 <= data["stability_score"] <= 1.0
        else:
            pytest.fail("Stability analysis returned None")

    def test_stability_visualization(self):
        report_path = run_stability_analysis()

        if report_path:
            viz_path = generate_stability_visualization(report_path)

            if viz_path:
                assert viz_path.exists()
                assert viz_path.is_file()
                assert viz_path.suffix == ".png"
            else:
                pytest.fail("Stability visualization returned None")
        else:
            pytest.fail("Stability analysis returned None")


@pytest.mark.skipif(not FIGURES_AVAILABLE, reason="Figure modules not available")
class TestPerformanceBenchmarking:
    """Test performance benchmarking functions."""

    def test_performance_benchmarking_execution(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        result_path = run_performance_benchmarking()

        if result_path:
            assert result_path.exists()
            assert result_path.is_file()

            data = json.loads(result_path.read_text())
            assert "function_name" in data
            assert "result_summary" in data
            assert "diagnostic_iterations_per_input" in data
            assert data["observations"]
            assert "execution_time" not in data
            assert "timestamp" not in data
        else:
            pytest.fail("Performance benchmarking returned None")

    def test_performance_visualization(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        report_path = run_performance_benchmarking()

        if report_path:
            viz_path = generate_benchmark_visualization(report_path)

            if viz_path:
                assert viz_path.exists()
                assert viz_path.is_file()
                assert viz_path.suffix == ".png"
                first_bytes = viz_path.read_bytes()
                second_path = generate_benchmark_visualization(report_path)
                assert second_path.read_bytes() == first_bytes
            else:
                pytest.fail("Performance visualization returned None")
        else:
            pytest.fail("Performance benchmarking returned None")


# ---------------------------------------------------------------------------
# compare_algorithms — cross-variant ranking
# ---------------------------------------------------------------------------


class TestCompareAlgorithms:
    """Tests for src.analysis.compare_algorithms (lines 251-357)."""

    def test_compare_returns_algorithm_comparison(self):
        """compare_algorithms returns a populated AlgorithmComparison."""
        from src.analysis import AlgorithmComparison, compare_algorithms
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1, 0.5), max_iterations=200)
        result = compare_algorithms(config=cfg, stability_check=False, time_runs=False)
        assert isinstance(result, AlgorithmComparison)
        assert len(result.variants) == 2

    def test_compare_best_variant_converged(self):
        """The best variant among converged candidates has the lowest final objective."""
        from src.analysis import compare_algorithms
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1, 0.5, 1.0), max_iterations=500)
        result = compare_algorithms(config=cfg, stability_check=False, time_runs=False)
        # All three should converge for H=I (α < 2)
        if result.best_variant.converged:
            converged = [v for v in result.variants if v.converged]
            assert result.best_variant.final_objective == min(v.final_objective for v in converged)

    def test_compare_pre_computed_results(self):
        """compare_algorithms accepts pre-computed results dict."""
        from src.analysis import compare_algorithms
        from src.experiment_config import ExperimentConfig
        from src.optimizer import OptimizationResult

        pre = {
            0.1: OptimizationResult(
                solution=np.array([1.0]),
                objective_value=-0.5,
                iterations=50,
                converged=True,
                gradient_norm=1e-9,
                objective_history=[0.0, -0.3, -0.5],
            ),
            2.5: OptimizationResult(
                solution=np.array([100.0]),
                objective_value=500.0,
                iterations=200,
                converged=False,
                gradient_norm=100.0,
                objective_history=[0.0, 100.0, 500.0],
            ),
        }
        cfg = ExperimentConfig(step_sizes=(0.1, 2.5), max_iterations=200)
        result = compare_algorithms(results=pre, config=cfg, stability_check=False, time_runs=False)
        assert result.convergence_summary == pytest.approx(50.0)  # 1/2 converged

    def test_compare_convergence_summary_all_converged(self):
        """convergence_summary is 100 when all variants converge."""
        from src.analysis import compare_algorithms
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1, 0.5), max_iterations=1000)
        result = compare_algorithms(config=cfg, stability_check=False, time_runs=False)
        # Both step sizes are stable for H=I
        assert result.convergence_summary == pytest.approx(100.0)

    def test_compare_ranking_table_structure(self):
        """ranking_table has the required keys per row."""
        from src.analysis import compare_algorithms
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1,), max_iterations=200)
        result = compare_algorithms(config=cfg, stability_check=False, time_runs=False)
        for row in result.ranking_table:
            assert "rank" in row
            assert "name" in row
            assert "step_size" in row
            assert "converged" in row
            assert "final_objective" in row
            assert "iterations" in row

    def test_compare_with_timing_enabled(self):
        """time_runs=True records a non-negative timing for each variant."""
        from src.analysis import compare_algorithms
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1,), max_iterations=50)
        result = compare_algorithms(config=cfg, stability_check=False, time_runs=True)
        for v in result.variants:
            assert v.timing_s >= 0.0

    def test_compare_with_stability_check(self):
        """stability_check=True sets stability_score on each variant."""
        from src.analysis import compare_algorithms
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1,), max_iterations=100)
        result = compare_algorithms(config=cfg, stability_check=True, time_runs=False)
        for v in result.variants:
            assert v.stability_score is not None
            assert 0.0 <= v.stability_score <= 1.0

    def test_compare_history_convergence_rate(self):
        """Variants with ≥2 history points have convergence_rate > 0."""
        from src.analysis import compare_algorithms
        from src.experiment_config import ExperimentConfig
        from src.optimizer import OptimizationResult

        pre = {
            0.1: OptimizationResult(
                solution=np.array([1.0]),
                objective_value=-0.5,
                iterations=5,
                converged=True,
                gradient_norm=1e-9,
                objective_history=[0.0, -0.2, -0.4, -0.5],
            )
        }
        cfg = ExperimentConfig(step_sizes=(0.1,), max_iterations=100)
        result = compare_algorithms(results=pre, config=cfg, stability_check=False, time_runs=False)
        assert result.variants[0].convergence_rate > 0.0

    def test_compare_convergence_rate_zero_when_single_history(self):
        """Variant with <2 history points gets convergence_rate=0.0 (line 275)."""
        from src.analysis import compare_algorithms
        from src.experiment_config import ExperimentConfig
        from src.optimizer import OptimizationResult

        pre = {
            0.1: OptimizationResult(
                solution=np.array([1.0]),
                objective_value=-0.5,
                iterations=1,
                converged=True,
                gradient_norm=1e-9,
                objective_history=[-0.5],  # only 1 point → conv_rate = 0.0
            )
        }
        cfg = ExperimentConfig(step_sizes=(0.1,), max_iterations=100)
        result = compare_algorithms(results=pre, config=cfg, stability_check=False, time_runs=False)
        assert result.variants[0].convergence_rate == 0.0

    def test_compare_fastest_slowest_convergence(self):
        """fastest_convergence and slowest_convergence names are populated."""
        from src.analysis import compare_algorithms
        from src.experiment_config import ExperimentConfig

        # Two step sizes with notably different iteration counts
        cfg = ExperimentConfig(step_sizes=(0.01, 0.9), max_iterations=5000)
        result = compare_algorithms(config=cfg, stability_check=False, time_runs=False)
        # With 2 converged variants, fastest ≠ slowest (or at least one is set)
        assert result.fastest_convergence != "none" or result.slowest_convergence != "none"


# ---------------------------------------------------------------------------
# multi_factor_analysis — composite scoring
# ---------------------------------------------------------------------------


class TestMultiFactorAnalysis:
    """Tests for src.analysis.multi_factor_analysis (lines 438-590)."""

    def test_multi_factor_returns_report(self):
        """multi_factor_analysis returns a MultiFactorReport."""
        from src.analysis import MultiFactorReport, multi_factor_analysis
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1, 0.5), max_iterations=200)
        report = multi_factor_analysis(config=cfg)
        assert isinstance(report, MultiFactorReport)

    def test_composite_score_in_range(self):
        """Composite score is ∈ [0, 1]."""
        from src.analysis import multi_factor_analysis
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1, 0.5), max_iterations=200)
        report = multi_factor_analysis(config=cfg)
        assert 0.0 <= report.composite_score <= 1.0

    def test_factor_weights_sum_to_one(self):
        """Normalised factor weights sum to 1.0."""
        from src.analysis import multi_factor_analysis
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1,), max_iterations=200)
        report = multi_factor_analysis(config=cfg)
        assert sum(report.factor_weights.values()) == pytest.approx(1.0)

    def test_recommendations_non_empty(self):
        """recommendations list always has at least one entry."""
        from src.analysis import multi_factor_analysis
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1, 0.5), max_iterations=200)
        report = multi_factor_analysis(config=cfg)
        assert len(report.recommendations) >= 1

    def test_custom_factor_weights(self):
        """Custom factor weights override defaults and are normalised."""
        from src.analysis import multi_factor_analysis
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1,), max_iterations=200)
        report = multi_factor_analysis(config=cfg, factor_weights={"convergence": 0.8, "stability": 0.2})
        assert sum(report.factor_weights.values()) == pytest.approx(1.0)

    def test_custom_factor_weights_with_unknown_key(self):
        """Unknown keys in factor_weights are silently ignored (line 467 False branch)."""
        from src.analysis import multi_factor_analysis
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1,), max_iterations=200)
        # "nonexistent_key" is not in the defaults → silently skipped
        report = multi_factor_analysis(config=cfg, factor_weights={"convergence": 0.5, "nonexistent_key": 99.0})
        # Normalisation should still work with valid keys only
        assert sum(report.factor_weights.values()) == pytest.approx(1.0)
        # The unknown key should not appear in the final weights
        assert "nonexistent_key" not in report.factor_weights

    def test_factor_weights_zero_total_skips_normalisation(self):
        """factor_weights summing to 0 skips normalisation (line 471 False branch)."""
        from src.analysis import multi_factor_analysis
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1,), max_iterations=200)
        # All-zero weights → total_w = 0 → normalisation step is skipped
        report = multi_factor_analysis(
            config=cfg,
            factor_weights={"convergence": 0.0, "stability": 0.0, "performance": 0.0, "efficiency": 0.0},
        )
        # The composite score will be 0.0 since all weights are zero
        assert report.composite_score == pytest.approx(0.0)

    def test_with_pre_computed_comparison(self):
        """multi_factor_analysis accepts a pre-computed AlgorithmComparison."""
        from src.analysis import compare_algorithms, multi_factor_analysis
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1, 0.5), max_iterations=200)
        cmp = compare_algorithms(config=cfg, stability_check=True, time_runs=False)
        report = multi_factor_analysis(comparison=cmp, config=cfg)
        assert report.best_overall_variant != ""

    def test_degenerate_empty_variants(self):
        """Degenerate case (no variants) returns a zeroed MultiFactorReport."""
        from src.analysis import (
            AlgorithmComparison,
            AlgorithmVariant,
            MultiFactorReport,
            multi_factor_analysis,
        )
        from src.experiment_config import ExperimentConfig

        # Build an empty comparison — need at least one variant for the dataclass
        # but we trigger the degenerate path by making variants=[] via a patched comparison
        empty_cmp = AlgorithmComparison(
            variants=[],
            best_variant=AlgorithmVariant(
                name="dummy",
                step_size=0.1,
                converged=False,
                iterations=0,
                final_objective=0.0,
                gradient_norm=0.0,
            ),
            convergence_summary=0.0,
            objective_spread=0.0,
            mean_iterations=0.0,
            fastest_convergence="none",
            slowest_convergence="none",
            ranking_table=[],
        )
        cfg = ExperimentConfig(step_sizes=(0.1,), max_iterations=200)
        report = multi_factor_analysis(comparison=empty_cmp, config=cfg)
        assert isinstance(report, MultiFactorReport)
        assert report.composite_score == pytest.approx(0.0)
        assert "No algorithm variants available" in report.recommendations[0]

    def test_factor_breakdown_keys(self):
        """factor_breakdown contains all expected keys."""
        from src.analysis import multi_factor_analysis
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1,), max_iterations=200)
        report = multi_factor_analysis(config=cfg)
        assert "convergence" in report.factor_breakdown
        assert "stability" in report.factor_breakdown
        assert "performance" in report.factor_breakdown
        assert "efficiency" in report.factor_breakdown

    def test_stability_fallback_recomputes_when_scores_none(self):
        """When no variant has stability_score, multi_factor_analysis recomputes it."""
        from src.analysis import (
            compare_algorithms,
            multi_factor_analysis,
        )
        from src.experiment_config import ExperimentConfig

        cfg = ExperimentConfig(step_sizes=(0.1,), max_iterations=200)
        # compare_algorithms with stability_check=False → stability_score=None
        cmp = compare_algorithms(config=cfg, stability_check=False, time_runs=False)
        # Nullify all stability scores to force the fallback branch
        for v in cmp.variants:
            v.stability_score = None
        report = multi_factor_analysis(comparison=cmp, config=cfg)
        # Fallback should still produce a valid score
        assert 0.0 <= report.stability_factor <= 1.0

    def test_recommendation_low_convergence(self):
        """convergence_factor < 0.5 triggers the convergence recommendation."""
        from src.analysis import compare_algorithms, multi_factor_analysis
        from src.experiment_config import ExperimentConfig
        from src.optimizer import OptimizationResult

        # One converged, three diverged → convergence_factor = 0.25 < 0.5
        pre = {
            0.1: OptimizationResult(
                solution=np.array([1.0]),
                objective_value=-0.5,
                iterations=50,
                converged=True,
                gradient_norm=1e-9,
                objective_history=[0.0, -0.5],
            ),
            2.5: OptimizationResult(
                solution=np.array([1e6]),
                objective_value=1e12,
                iterations=100,
                converged=False,
                gradient_norm=1e6,
                objective_history=[],
            ),
            3.0: OptimizationResult(
                solution=np.array([1e6]),
                objective_value=1e12,
                iterations=100,
                converged=False,
                gradient_norm=1e6,
                objective_history=[],
            ),
            4.0: OptimizationResult(
                solution=np.array([1e6]),
                objective_value=1e12,
                iterations=100,
                converged=False,
                gradient_norm=1e6,
                objective_history=[],
            ),
        }
        cfg = ExperimentConfig(step_sizes=(0.1, 2.5, 3.0, 4.0), max_iterations=100)
        cmp = compare_algorithms(results=pre, config=cfg, stability_check=False, time_runs=False)
        report = multi_factor_analysis(comparison=cmp, config=cfg)
        assert any("failed to converge" in r.lower() for r in report.recommendations)

    def test_recommendation_low_stability(self):
        """stability_factor < 0.8 triggers the stability recommendation.

        Force by building variants with explicitly low stability scores.
        """
        from src.analysis import (
            AlgorithmComparison,
            AlgorithmVariant,
            multi_factor_analysis,
        )
        from src.experiment_config import ExperimentConfig

        # Create a variant with a low stability score
        variant = AlgorithmVariant(
            name="GD α=0.1",
            step_size=0.1,
            converged=True,
            iterations=50,
            final_objective=-0.5,
            gradient_norm=1e-9,
            objective_history=[0.0, -0.5],
            stability_score=0.2,  # below 0.8 threshold
        )
        cmp = AlgorithmComparison(
            variants=[variant],
            best_variant=variant,
            convergence_summary=100.0,
            objective_spread=0.0,
            mean_iterations=50.0,
            fastest_convergence=variant.name,
            slowest_convergence="none",
            ranking_table=[],
        )
        cfg = ExperimentConfig(step_sizes=(0.1,), max_iterations=200)
        report = multi_factor_analysis(comparison=cmp, config=cfg)
        assert any("stability" in r.lower() for r in report.recommendations)

    def test_variant_score_unconverged_returns_negative(self):
        """_variant_score returns -1.0 for unconverged variants (line 547)."""
        from src.analysis import (
            AlgorithmComparison,
            AlgorithmVariant,
            multi_factor_analysis,
        )
        from src.experiment_config import ExperimentConfig

        converged_v = AlgorithmVariant(
            name="GD α=0.1",
            step_size=0.1,
            converged=True,
            iterations=10,
            final_objective=-0.5,
            gradient_norm=1e-9,
            objective_history=[0.0, -0.5],
            stability_score=0.9,
        )
        diverged_v = AlgorithmVariant(
            name="GD α=3.0",
            step_size=3.0,
            converged=False,  # → _variant_score returns -1.0
            iterations=200,
            final_objective=1e6,
            gradient_norm=1e6,
            objective_history=[],
            stability_score=0.1,
        )
        cmp = AlgorithmComparison(
            variants=[converged_v, diverged_v],
            best_variant=converged_v,
            convergence_summary=50.0,
            objective_spread=0.0,
            mean_iterations=105.0,
            fastest_convergence=converged_v.name,
            slowest_convergence="none",
            ranking_table=[],
        )
        cfg = ExperimentConfig(step_sizes=(0.1, 3.0), max_iterations=200)
        report = multi_factor_analysis(comparison=cmp, config=cfg)
        # The best_overall_variant should be the converged one, not the diverged one
        assert report.best_overall_variant == converged_v.name


# ---------------------------------------------------------------------------
# AlphaSweepConfig.resolved_alphas — ValueError edge case
# ---------------------------------------------------------------------------


class TestAlphaSweepConfigResolvedAlphas:
    """sweeps.py line 64: ValueError when neither alphas nor min/max/num provided."""

    def test_resolved_alphas_raises_when_all_none(self):
        """AlphaSweepConfig.resolved_alphas raises ValueError when alphas=None
        and alpha_min/alpha_max/alpha_num are all unset."""
        import numpy as np
        from src.sweeps import AlphaSweepConfig

        cfg = AlphaSweepConfig(
            A=np.eye(1),
            b=np.ones(1),
            initial_point=np.zeros(1),
            max_iterations=100,
            tolerance=1e-6,
            alphas=None,
            alpha_min=None,
            alpha_max=None,
            alpha_num=None,
        )
        with pytest.raises(ValueError, match="Provide either alphas or alpha_min"):
            cfg.resolved_alphas()

    def test_resolved_alphas_linspace_path(self):
        """alpha_min/max/num fully specified → linspace grid."""
        import numpy as np
        from src.sweeps import AlphaSweepConfig

        cfg = AlphaSweepConfig(
            A=np.eye(1),
            b=np.ones(1),
            initial_point=np.zeros(1),
            max_iterations=100,
            tolerance=1e-6,
            alphas=None,
            alpha_min=0.01,
            alpha_max=0.5,
            alpha_num=5,
        )
        grid = cfg.resolved_alphas()
        assert len(grid) == 5
        assert grid[0] == pytest.approx(0.01)
        assert grid[-1] == pytest.approx(0.5)
