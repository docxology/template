"""Tests for the opt-in methods-plan gate (scripts/gates/methods_plan_check.py).

No mocks: each case builds a real synthetic repo under ``tmp_path`` (real
``pipeline.yaml``, manuscript, and output-report files on disk) and exercises the
gate's pass and fail exit paths through its ``main`` entry point.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.gates.methods_plan_check import main as gate_main  # noqa: E402
from tests._support.projects import make_project, write_doc  # noqa: E402

_VALID_PIPELINE = """
stages:
  - name: Project Analysis
    script: 02_run_analysis.py
    tags: [core]
    contract:
      input_artifacts: ["projects/{project}/src/", "projects/{project}/scripts/"]
      output_artifacts: ["projects/{project}/output/data/result.csv"]
      definition_of_done: "Analysis writes a result."
      failure_code: "PROJECT_ANALYSIS_FAILED"
      retry_policy: 0
      gate: "experiment_method_design"
"""


def _write_pipeline(repo_root: Path) -> None:
    pipeline_dir = repo_root / "infrastructure" / "core" / "pipeline"
    write_doc(pipeline_dir / "pipeline.yaml", _VALID_PIPELINE)


def test_gate_passes_for_fully_specified_project(tmp_path: Path) -> None:
    """A project with a methods section + present evidence files exits 0."""
    _write_pipeline(tmp_path)
    project = make_project(tmp_path, "template_test", with_manuscript=True, with_scripts=True)
    write_doc(project / "manuscript" / "02_methodology.md", "# Methodology\n\nWe did X.\n")
    reports = project / "output" / "reports"
    write_doc(reports / "artifact_manifest.json", "{}\n")
    write_doc(reports / "evidence_registry.json", "{}\n")

    exit_code = gate_main(["--repo-root", str(tmp_path), "--project", "template_test"])

    assert exit_code == 0


def test_gate_fails_when_methods_contract_unmet(tmp_path: Path) -> None:
    """A project missing its methods section + evidence files exits non-zero."""
    _write_pipeline(tmp_path)
    # No manuscript methods section, no output/reports/*.json — blocking errors.
    make_project(tmp_path, "template_test", with_scripts=True)

    exit_code = gate_main(["--repo-root", str(tmp_path), "--project", "template_test"])

    assert exit_code == 1


def test_gate_reports_failing_project_name(tmp_path: Path, capsys) -> None:
    """The gate names the failing project in its failure summary."""
    _write_pipeline(tmp_path)
    make_project(tmp_path, "template_test", with_scripts=True)

    exit_code = gate_main(["--repo-root", str(tmp_path), "--project", "template_test"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "template_test" in captured.out
    assert "methods-plan gate" in captured.out
