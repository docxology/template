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
)
from src.experiment_config import ExperimentConfig, load_experiment_config
from src.optimizer import OptimizationResult

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
        monkeypatch.setattr("src.analysis.project_root", tmp_path)
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
        monkeypatch.setattr("src.analysis.project_root", tmp_path)
        path = run_stability_analysis()
        assert path.exists()
        data = json.loads(path.read_text())
        assert "stability_score" in data

    def test_benchmark_writes_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("src.analysis.project_root", tmp_path)
        path = run_performance_benchmarking()
        assert path.exists()
        data = json.loads(path.read_text())
        assert "execution_time" in data


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
    def test_stability_analysis_without_infra(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("src.analysis.INFRASTRUCTURE_AVAILABLE", False)
        monkeypatch.setattr("src.analysis.project_root", tmp_path)
        path = run_stability_analysis()
        assert path.exists()

    def test_benchmark_without_infra(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("src.analysis.INFRASTRUCTURE_AVAILABLE", False)
        monkeypatch.setattr("src.analysis.project_root", tmp_path)
        path = run_performance_benchmarking()
        assert path.exists()

    def test_stability_score_standalone(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("src.analysis.INFRASTRUCTURE_AVAILABLE", False)
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
        monkeypatch.setattr("src.analysis.project_root", tmp_path)
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
        monkeypatch.setattr("src.analysis.project_root", tmp_path)
        from src.analysis import save_publishing_materials

        save_publishing_materials({"title": "only title"}, None)
        assert (tmp_path / "output" / "citations" / "optimization_metadata.json").exists()


class TestValidationAndRegistration:
    def test_validate_and_save_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        if not __import__("src.analysis", fromlist=["INFRASTRUCTURE_AVAILABLE"]).INFRASTRUCTURE_AVAILABLE:
            pytest.skip("Infrastructure not available")
        monkeypatch.setattr("src.analysis.project_root", tmp_path)
        (tmp_path / "output" / "figures").mkdir(parents=True)
        (tmp_path / "output" / "figures" / "convergence_plot.png").write_bytes(b"png")

        from src.analysis import save_validation_report, validate_generated_outputs

        report = validate_generated_outputs()
        if report:
            path = save_validation_report(report)
            assert path is not None and path.exists()

    def test_register_figure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("src.analysis.project_root", tmp_path)
        (tmp_path / "output" / "figures").mkdir(parents=True)
        from src.analysis import register_figure

        register_figure()
        registry = tmp_path / "output" / "figures" / "figure_registry.json"
        assert registry.exists()


class TestMainPipelineSmoke:
    def test_main_writes_core_artifacts(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        import shutil

        shutil.copytree(PROJECT_ROOT / "manuscript", tmp_path / "manuscript")
        monkeypatch.setattr("src.analysis.project_root", tmp_path)
        monkeypatch.setattr("src.figures.project_root", tmp_path)

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

    def test_performance_benchmarking_execution(self):
        result_path = run_performance_benchmarking()

        if result_path:
            assert result_path.exists()
            assert result_path.is_file()

            data = json.loads(result_path.read_text())
            assert "execution_time" in data
            assert "function_name" in data
            assert "result_summary" in data
            assert "iterations" in data
            assert isinstance(data["execution_time"], (int, float))
            assert data["execution_time"] > 0
        else:
            pytest.fail("Performance benchmarking returned None")

    def test_performance_visualization(self):
        report_path = run_performance_benchmarking()

        if report_path:
            viz_path = generate_benchmark_visualization(report_path)

            if viz_path:
                assert viz_path.exists()
                assert viz_path.is_file()
                assert viz_path.suffix == ".png"
            else:
                pytest.fail("Performance visualization returned None")
        else:
            pytest.fail("Performance benchmarking returned None")
