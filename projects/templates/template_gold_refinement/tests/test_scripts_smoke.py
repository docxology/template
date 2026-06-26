"""Subprocess smoke tests for gold-refinement scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestRefinementAnalysisScript:
    def test_script_exits_zero(self):
        import subprocess
        proc = subprocess.run(
            [sys.executable, str(_PROJECT_ROOT / "scripts" / "refinement_analysis.py")],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(_PROJECT_ROOT),
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout
        # Check output files exist
        assert (_PROJECT_ROOT / "output" / "data" / "refinery_results.json").exists()
        assert (_PROJECT_ROOT / "output" / "reports" / "token_plan.json").exists()
        # Check figures were generated
        figures_dir = _PROJECT_ROOT / "output" / "figures"
        assert (figures_dir / "purity_progression.png").exists()
        assert (figures_dir / "karat_grading.png").exists()
        assert (figures_dir / "token_density.png").exists()
        assert (figures_dir / "figure_registry.json").exists()

    def test_refinery_results_content(self):
        import subprocess
        proc = subprocess.run(
            [sys.executable, str(_PROJECT_ROOT / "scripts" / "refinement_analysis.py")],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(_PROJECT_ROOT),
        )
        assert proc.returncode == 0
        data = json.loads(
            (_PROJECT_ROOT / "output" / "data" / "refinery_results.json").read_text()
        )
        assert data["stage_count"] == 5
        assert data["is_nine_nines_certified"] is True
        assert data["final_karat"] == "24K (nine-nines certified)"


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
        )
        assert proc2.returncode == 0, proc2.stderr or proc2.stdout
        vars_path = _PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
        assert vars_path.exists()
        variables = json.loads(vars_path.read_text())
        assert "REFINERY_NUM_STAGES" in variables
        assert "FIGURE_PURITY_PROGRESSION" in variables
        assert "CONTRIBUTION_CLAIMS_TABLE" in variables
        assert "PIPELINE_PHASES_TABLE" in variables

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
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout
