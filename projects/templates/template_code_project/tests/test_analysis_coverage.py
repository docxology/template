"""Targeted coverage for analysis.py orchestration branches."""

from __future__ import annotations

import json
import builtins
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import src.analysis as analysis_mod  # noqa: E402
from src.analysis import (  # noqa: E402
    _get_logger,
    _setup_fallback_logging,
    _stability_score_from_runs,
    extract_optimization_metadata,
    generate_citations_from_metadata,
    save_publishing_materials,
    save_validation_report,
    validate_generated_outputs,
)
from src.experiment_config import ExperimentConfig  # noqa: E402
from src.optimizer import OptimizationResult  # noqa: E402


class TestFallbackLogging:
    def test_setup_fallback_logging_idempotent(self):
        logger = _setup_fallback_logging()
        again = _setup_fallback_logging()
        assert logger.name == again.name
        assert logger.handlers

    def test_get_logger_without_infra(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(analysis_mod, "INFRASTRUCTURE_AVAILABLE", False)
        logger = _get_logger()
        assert logger.name == "template_code_project.optimization_analysis"

    def test_log_success_fallback_is_noop(self, monkeypatch: pytest.MonkeyPatch):
        """log_success no-op fallback (lines 71-74) is callable and returns None."""
        monkeypatch.setattr(analysis_mod, "INFRASTRUCTURE_AVAILABLE", False)
        # The fallback is only redefined at module import time; test via the no-op
        # directly by calling it when infrastructure is unavailable.
        # We can call the global log_success — if infrastructure is available,
        # it is the real one; if not, it is the no-op. Either way it should not raise.
        result = analysis_mod.log_success("test message", None)
        assert result is None


class TestValidateOutputs:
    def test_skips_when_infra_unavailable(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(analysis_mod, "INFRASTRUCTURE_AVAILABLE", False)
        assert validate_generated_outputs() is None

    def test_returns_summary_when_infra_available(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        if not analysis_mod.INFRASTRUCTURE_AVAILABLE:
            pytest.skip("Infrastructure not available")
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        figures = tmp_path / "output" / "figures"
        figures.mkdir(parents=True)
        (figures / "convergence_plot.png").write_bytes(b"png-bytes")
        (figures / "step_size_sensitivity.png").write_bytes(b"png-bytes")
        report = validate_generated_outputs()
        assert report is not None
        assert "integrity_check" in report

    def test_handles_validation_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        if not analysis_mod.INFRASTRUCTURE_AVAILABLE:
            pytest.skip("Infrastructure not available")
        from infrastructure.core.exceptions import ValidationError

        def _raise_validation(_path: Path) -> None:
            raise ValidationError("integrity check failed")

        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        monkeypatch.setattr(analysis_mod, "verify_output_integrity", _raise_validation)
        assert validate_generated_outputs() is None

    def test_handles_unexpected_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        if not analysis_mod.INFRASTRUCTURE_AVAILABLE:
            pytest.skip("Infrastructure not available")

        def _raise_oserror(_path: Path) -> None:
            raise OSError("disk full")

        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        monkeypatch.setattr(analysis_mod, "verify_output_integrity", _raise_oserror)
        assert validate_generated_outputs() is None

    def test_logs_integrity_issues_when_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        if not analysis_mod.INFRASTRUCTURE_AVAILABLE:
            pytest.skip("Infrastructure not available")
        from infrastructure.validation.integrity.checks import IntegrityReport

        def _report_with_issues(_path: Path) -> IntegrityReport:
            return IntegrityReport(
                file_integrity={"fig.png": False},
                issues=["corrupt png", "missing hash"],
                warnings=[],
                recommendations=[],
            )

        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        monkeypatch.setattr(analysis_mod, "verify_output_integrity", _report_with_issues)
        report = validate_generated_outputs()
        assert report is not None
        assert report["integrity_check"]["issues_found"] == 2


class TestSaveValidationReport:
    def test_returns_none_for_empty_report(self):
        assert save_validation_report(None) is None

    def test_saves_json(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        path = save_validation_report({"integrity_check": {"total_files": 1}})
        assert path is not None and path.exists()
        data = json.loads(path.read_text())
        assert data["integrity_check"]["total_files"] == 1

    def test_returns_none_on_write_oserror(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        real_open = builtins.open

        def _fail_json_write(*args: object, **kwargs: object):
            path = args[0] if args else kwargs.get("file")
            if path and str(path).endswith("output_validation.json"):
                raise OSError("write failed")
            return real_open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", _fail_json_write)
        assert save_validation_report({"integrity_check": {"total_files": 1}}) is None

    def test_returns_none_when_reports_path_is_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        reports = tmp_path / "output" / "reports"
        reports.parent.mkdir(parents=True)
        reports.write_text("not-a-directory")
        assert save_validation_report({"integrity_check": {"total_files": 1}}) is None


class TestStabilityScoreBranches:
    def test_recommends_adaptive_step_when_error_large(self):
        A = np.array([[1.0]])
        b = np.array([1.0])
        _score, max_error, recs = _stability_score_from_runs(
            [np.array([100.0])],
            A,
            b,
            step_size=2.5,
        )
        if max_error >= 1e-6:
            assert recs == ["Consider adaptive step size"]


class TestScientificInfraPaths:
    def test_stability_uses_infrastructure_report(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        if not analysis_mod.INFRASTRUCTURE_AVAILABLE:
            pytest.skip("Infrastructure not available")
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        from src.analysis import run_stability_analysis

        path = run_stability_analysis(ExperimentConfig(stability_starting_points=(0.0, 1.0)))
        data = json.loads(path.read_text())
        assert "expected_behavior" in data
        assert "actual_behavior" in data

    def test_benchmark_uses_infrastructure_report(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        if not analysis_mod.INFRASTRUCTURE_AVAILABLE:
            pytest.skip("Infrastructure not available")
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        from src.analysis import run_performance_benchmarking

        path = run_performance_benchmarking()
        data = json.loads(path.read_text())
        assert data["schema_version"] == "template_code_project/performance_benchmark/v2"
        assert data["timing_policy"]
        assert "memory_usage" not in data
        assert "timestamp" not in data


class TestExtractMetadataExtended:
    def test_includes_convergence_rate_with_history(self):
        results = {
            0.1: OptimizationResult(
                solution=np.array([1.0]),
                objective_value=-0.5,
                iterations=5,
                converged=True,
                gradient_norm=1e-9,
                objective_history=[0.0, -0.2, -0.45, -0.5],
            )
        }
        meta = extract_optimization_metadata(results)
        assert meta is not None
        assert meta["iterations_to_convergence"] == 4
        assert meta["convergence_rate"] > 0

    def test_returns_none_on_bad_results(self):
        class BadResult:
            objective_value = "not-a-float"

        assert extract_optimization_metadata({0.1: BadResult()}) is None  # type: ignore[arg-type]


class TestCitationsExtended:
    def test_generates_all_formats_when_infra(self):
        if not analysis_mod.INFRASTRUCTURE_AVAILABLE:
            pytest.skip("Infrastructure not available")
        meta = {
            "title": "Optimization Study",
            "description": "Gradient descent sweep",
            "algorithm": "Gradient Descent",
            "best_step_size": 0.1,
            "final_objective": -0.5,
            "iterations_to_convergence": 3,
        }
        citations = generate_citations_from_metadata(meta)
        assert citations is not None
        assert citations["bibtex"]
        assert citations["apa"]
        assert citations["mla"]

    def test_returns_none_on_missing_title(self):
        assert generate_citations_from_metadata({}) is None


class TestPublishingExtended:
    def test_writes_citation_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        meta = {
            "title": "Optimization Study",
            "description": "Gradient descent sweep",
            "algorithm": "Gradient Descent",
            "best_step_size": 0.1,
            "final_objective": -0.5,
            "iterations_to_convergence": 3,
        }
        citations = {"bibtex": "@article{key, title={T}}", "apa": "Author (2026). T."}
        save_publishing_materials(meta, citations)
        cite_dir = tmp_path / "output" / "citations"
        assert (cite_dir / "citation_bibtex.txt").exists()
        assert (cite_dir / "citation_apa.txt").exists()
        summary = (cite_dir / "publication_summary.md").read_text()
        assert "Optimization Study" in summary
        assert "bibtex" in summary.lower() or "BIBTEX" in summary

    def test_handles_missing_metadata_keys(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        save_publishing_materials({"description": "no title key"})
        cite_dir = tmp_path / "output" / "citations"
        assert (cite_dir / "optimization_metadata.json").exists()
        summary = (cite_dir / "publication_summary.md").read_text()
        assert summary.startswith("# Optimization Analysis Publication Summary")


class TestMainBranches:
    def _copy_manuscript(self, tmp_path: Path) -> None:
        shutil.copytree(PROJECT_ROOT / "manuscript", tmp_path / "manuscript")

    def test_main_without_infra(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        self._copy_manuscript(tmp_path)
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        monkeypatch.setattr("src.figures.project_root", tmp_path)
        monkeypatch.setattr(analysis_mod, "INFRASTRUCTURE_AVAILABLE", False)
        analysis_mod.main()
        assert (tmp_path / "output" / "data" / "optimization_results.csv").exists()
        assert (tmp_path / "output" / "figures" / "convergence_plot.png").exists()

    def test_main_unhealthy_health_check(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        if not analysis_mod.INFRASTRUCTURE_AVAILABLE:
            pytest.skip("Infrastructure not available")
        self._copy_manuscript(tmp_path)
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        monkeypatch.setattr("src.figures.project_root", tmp_path)

        class UnhealthyChecker:
            def get_health_status(self) -> dict:
                return {
                    "overall_status": "degraded",
                    "checks": {"disk": {"status": "unhealthy", "error": "full"}},
                }

        monkeypatch.setattr(analysis_mod, "SystemHealthChecker", UnhealthyChecker)
        analysis_mod.main()
        assert (tmp_path / "output" / "reports" / "stability_analysis.json").exists()

    def test_main_handles_publishing_demo_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        if not analysis_mod.INFRASTRUCTURE_AVAILABLE:
            pytest.skip("Infrastructure not available")
        self._copy_manuscript(tmp_path)
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        monkeypatch.setattr("src.figures.project_root", tmp_path)

        base_logger = analysis_mod._get_logger()

        class _DemoFailLogger:
            def info(self, msg: str, *args: object, **kwargs: object) -> None:
                if "Publishing interfaces available" in msg:
                    raise ValueError("demo failed")
                base_logger.info(msg, *args, **kwargs)

            def warning(self, msg: str, *args: object, **kwargs: object) -> None:
                base_logger.warning(msg, *args, **kwargs)

            def __getattr__(self, name: str) -> object:
                return getattr(base_logger, name)

        monkeypatch.setattr(analysis_mod, "_get_logger", lambda: _DemoFailLogger())
        analysis_mod.main()
        assert (tmp_path / "output" / "data" / "optimization_results.csv").exists()


class TestMainErrors:
    def _copy_manuscript(self, tmp_path: Path) -> None:
        shutil.copytree(PROJECT_ROOT / "manuscript", tmp_path / "manuscript")

    def test_main_reraises_script_execution_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        if not analysis_mod.INFRASTRUCTURE_AVAILABLE:
            pytest.skip("Infrastructure not available")
        from infrastructure.core.exceptions import ScriptExecutionError

        self._copy_manuscript(tmp_path)
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        monkeypatch.setattr("src.figures.project_root", tmp_path)

        err = ScriptExecutionError("pipeline failed", recovery_commands=["uv sync"])

        def _boom(**_kwargs: object) -> dict:
            raise err

        monkeypatch.setattr(analysis_mod, "run_convergence_experiment", _boom)
        with pytest.raises(ScriptExecutionError):
            analysis_mod.main()

    def test_main_reraises_template_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        if not analysis_mod.INFRASTRUCTURE_AVAILABLE:
            pytest.skip("Infrastructure not available")
        from infrastructure.core.exceptions import TemplateError

        self._copy_manuscript(tmp_path)
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        monkeypatch.setattr("src.figures.project_root", tmp_path)

        err = TemplateError("template failed", suggestions=["check config"])

        def _boom(**_kwargs: object) -> dict:
            raise err

        monkeypatch.setattr(analysis_mod, "run_convergence_experiment", _boom)
        with pytest.raises(TemplateError):
            analysis_mod.main()

    def test_main_reraises_unexpected_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        if not analysis_mod.INFRASTRUCTURE_AVAILABLE:
            pytest.skip("Infrastructure not available")
        self._copy_manuscript(tmp_path)
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        monkeypatch.setattr("src.figures.project_root", tmp_path)

        def _boom(**_kwargs: object) -> dict:
            raise RuntimeError("unexpected")

        monkeypatch.setattr(analysis_mod, "run_convergence_experiment", _boom)
        with pytest.raises(RuntimeError):
            analysis_mod.main()

    def test_main_reraises_import_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        self._copy_manuscript(tmp_path)
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        monkeypatch.setattr("src.figures.project_root", tmp_path)

        def _boom(**_kwargs: object) -> dict:
            raise ImportError("missing module")

        monkeypatch.setattr(analysis_mod, "run_convergence_experiment", _boom)
        with pytest.raises(ImportError, match="missing module"):
            analysis_mod.main()

    def test_main_reraises_file_not_found_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        self._copy_manuscript(tmp_path)
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        monkeypatch.setattr("src.figures.project_root", tmp_path)

        def _boom(**_kwargs: object) -> dict:
            raise FileNotFoundError("config missing")

        monkeypatch.setattr(analysis_mod, "run_convergence_experiment", _boom)
        with pytest.raises(FileNotFoundError, match="config missing"):
            analysis_mod.main()


class TestRegisterFigure:
    def test_register_figure_writes_registry(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        figures = tmp_path / "output" / "figures"
        figures.mkdir(parents=True)
        from src.analysis import register_figure

        register_figure()
        registry = figures / "figure_registry.json"
        assert registry.exists()
        data = json.loads(registry.read_text())
        assert isinstance(data, dict)

    def test_register_figure_handles_import_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        real_import = builtins.__import__

        def _block_figure_manager(name: str, *args: object, **kwargs: object) -> object:
            if name == "infrastructure.documentation.figure_manager":
                raise ImportError("figure manager unavailable")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", _block_figure_manager)
        from src.analysis import register_figure

        register_figure()

    def test_register_figure_handles_oserror(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(analysis_mod, "project_root", tmp_path)
        (tmp_path / "output" / "figures").mkdir(parents=True)

        class _BrokenFigureManager:
            def __init__(self, **kwargs: object) -> None:
                pass

            def register_figure(self, **kwargs: object) -> None:
                raise OSError("registry write failed")

        import types

        fake_mod = types.ModuleType("infrastructure.documentation.figure_manager")
        fake_mod.FigureManager = _BrokenFigureManager  # type: ignore[attr-defined]
        monkeypatch.setitem(
            sys.modules,
            "infrastructure.documentation.figure_manager",
            fake_mod,
        )
        from src.analysis import register_figure

        register_figure()


class TestImportFallback:
    def test_infrastructure_import_fallback(self) -> None:
        """Import path when infrastructure modules are unavailable at load time."""
        import subprocess
        import sys

        project_root = PROJECT_ROOT
        code = """
import builtins
import importlib.util
import sys
from pathlib import Path

project_root = Path(sys.argv[1])
real_import = builtins.__import__

def _block_infra(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "infrastructure" or name.startswith("infrastructure."):
        raise ImportError("infrastructure unavailable")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = _block_infra
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

spec = importlib.util.spec_from_file_location(
    "analysis_infra_isolated",
    project_root / "src" / "analysis" / "_infra.py",
)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)
assert mod.INFRASTRUCTURE_AVAILABLE is False
"""
        result = subprocess.run(
            [sys.executable, "-c", code, str(project_root)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert result.returncode == 0, result.stderr or result.stdout
