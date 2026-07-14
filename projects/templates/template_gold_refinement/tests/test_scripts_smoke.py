"""Subprocess smoke tests for gold-refinement scripts."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_ENV = {**os.environ, "SOURCE_DATE_EPOCH": "1782345600"}
_HAS_SHARED_INFRASTRUCTURE = importlib.util.find_spec("infrastructure") is not None


class TestRefinementAnalysisScript:
    def test_script_exits_zero(self):
        import subprocess

        proc = subprocess.run(
            [sys.executable, str(_PROJECT_ROOT / "scripts" / "refinement_analysis.py")],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(_PROJECT_ROOT),
            env=_SCRIPT_ENV,
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout
        # Check output files exist
        assert (_PROJECT_ROOT / "output" / "data" / "refinery_results.json").exists()
        assert (_PROJECT_ROOT / "output" / "reports" / "token_plan.json").exists()
        assert (_PROJECT_ROOT / "output" / "reports" / "claim_support_registry.json").exists()
        assert (_PROJECT_ROOT / "output" / "reports" / "figure_quality_report.json").exists()
        assert (_PROJECT_ROOT / "output" / "data" / "seed_sensitivity.json").exists()
        # Check figures were generated
        figures_dir = _PROJECT_ROOT / "output" / "figures"
        assert (figures_dir / "purity_progression.png").exists()
        assert (figures_dir / "purity_progression.svg").exists()
        assert (figures_dir / "karat_grading.png").exists()
        assert (figures_dir / "karat_grading.svg").exists()
        assert (figures_dir / "token_density.png").exists()
        assert (figures_dir / "token_density.svg").exists()
        assert (figures_dir / "seed_sensitivity.png").exists()
        assert (figures_dir / "seed_sensitivity.svg").exists()
        assert (figures_dir / "figure_registry.json").exists()

    def test_refinery_results_content(self):
        import subprocess

        proc = subprocess.run(
            [sys.executable, str(_PROJECT_ROOT / "scripts" / "refinement_analysis.py")],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(_PROJECT_ROOT),
            env=_SCRIPT_ENV,
        )
        assert proc.returncode == 0
        data = json.loads((_PROJECT_ROOT / "output" / "data" / "refinery_results.json").read_text())
        assert data["stage_count"] == 5
        assert data["is_nine_nines_certified"] is True
        assert data["final_karat"] == "24K (nine-nines certified)"
        seed_data = json.loads((_PROJECT_ROOT / "output" / "data" / "seed_sensitivity.json").read_text())
        assert seed_data["sample_size"] == 1024
        assert seed_data["meets_precision_target"] is True
        assert seed_data["minimum_sample_size_for_precision_target"] == 738
        assert seed_data["bootstrap_replicates"] == 2000
        assert seed_data["seed_sampling_scheme"] == "contiguous_integer_seeds"


@pytest.mark.skipif(
    not _HAS_SHARED_INFRASTRUCTURE,
    reason="Manuscript hydration is provided by the shared template infrastructure.",
)
class TestManuscriptVariablesScript:
    def test_script_exits_zero_with_analysis(self):
        # Ensure analysis outputs exist first
        import subprocess

        proc = subprocess.run(
            [sys.executable, str(_PROJECT_ROOT / "scripts" / "refinement_analysis.py")],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(_PROJECT_ROOT),
            env=_SCRIPT_ENV,
        )
        assert proc.returncode == 0

        proc2 = subprocess.run(
            [
                sys.executable,
                str(_PROJECT_ROOT / "scripts" / "z_generate_manuscript_variables.py"),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(_PROJECT_ROOT),
            env=_SCRIPT_ENV,
        )
        assert proc2.returncode == 0, proc2.stderr or proc2.stdout
        vars_path = _PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
        assert vars_path.exists()
        variables = json.loads(vars_path.read_text())
        assert "REFINERY_NUM_STAGES" in variables
        assert "FIGURE_PURITY_PROGRESSION" in variables
        assert "fig:purity_progression" in variables["FIGURE_PURITY_PROGRESSION"]
        assert "CONTRIBUTION_CLAIMS_TABLE" in variables
        assert "PIPELINE_PHASES_TABLE" in variables
        assert "FORMALISM_EQUATION_BLOCKS" in variables
        assert "FIGURE_INTEGRITY_GATE_MATRIX" in variables
        assert "FIGURE_FORMALISM_TRACEABILITY" in variables
        assert "FIGURE_IMPLEMENTATION_CIRCUIT" in variables
        assert "FIGURE_CLAIM_EVIDENCE_ASSAY" in variables
        assert "FIGURE_INTEGRITY_RISK_MATRIX" in variables
        assert "FIGURE_EVIDENCE_TIER_LADDER" in variables
        assert "FIGURE_SEED_SENSITIVITY" in variables
        assert variables["SEED_STUDY_N"] == "1024"
        assert variables["SEED_STUDY_MEETS_PRECISION"] == "Yes"
        assert variables["SEED_STUDY_MINIMUM_N"] == "738"
        assert variables["SEED_STUDY_BOOTSTRAP_REPLICATES"] == "2000"
        assert "INTEGRITY_DIMENSION_TABLE" in variables
        assert "EVIDENCE_TIER_TABLE" in variables
        assert "FIGURE_QUALITY_TABLE" in variables
        assert variables["FIGURE_QUALITY_REPORT_PATH"] == "output/reports/figure_quality_report.json"

    def test_script_draft_mode(self):
        import subprocess

        proc = subprocess.run(
            [
                sys.executable,
                str(_PROJECT_ROOT / "scripts" / "z_generate_manuscript_variables.py"),
                "--allow-draft",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(_PROJECT_ROOT),
            env=_SCRIPT_ENV,
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout


@pytest.mark.skipif(
    not _HAS_SHARED_INFRASTRUCTURE,
    reason="Manuscript hydration is provided by the shared template infrastructure.",
)
class TestCoverVisualizationScript:
    def test_script_exits_zero_after_manuscript_variables(self):
        import subprocess

        for script in (
            "refinement_analysis.py",
            "z_generate_manuscript_variables.py",
            "zz_generate_cover_visualization.py",
        ):
            proc = subprocess.run(
                [sys.executable, str(_PROJECT_ROOT / "scripts" / script)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(_PROJECT_ROOT),
                env=_SCRIPT_ENV,
            )
            assert proc.returncode == 0, proc.stderr or proc.stdout
        cover_path = _PROJECT_ROOT / "output" / "figures" / "cover_visualization.png"
        assert cover_path.exists() and cover_path.stat().st_size > 1000
