"""Shared repo-scaffold helper for the split AutoResearch test modules (formerly test_autoresearch.py)."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.core.pipeline.artifacts import compute_sha256


def _write_repo_scaffold(tmp_path: Path) -> Path:
    repo_root = tmp_path
    pipeline_dir = repo_root / "infrastructure" / "core" / "pipeline"
    pipeline_dir.mkdir(parents=True)
    (pipeline_dir / "pipeline.yaml").write_text(
        """
stages:
  - name: Environment Setup
    script: scripts/pipeline/stage_00_setup.py
    contract:
      input_artifacts: ["projects/{project}/"]
      output_artifacts: ["projects/{project}/output/"]
      definition_of_done: "Environment is ready."
      failure_code: "ENVIRONMENT_SETUP_FAILED"
      retry_policy: 0
  - name: Project Analysis
    script: scripts/pipeline/stage_02_analysis.py
    depends_on: [Environment Setup]
    contract:
      input_artifacts: ["projects/{project}/src/"]
      output_artifacts: ["projects/{project}/output/data/result.csv"]
      definition_of_done: "Analysis writes the declared result."
      failure_code: "PROJECT_ANALYSIS_FAILED"
      retry_policy: 0
      gate: "experiment_method_design"
  - name: Output Validation
    script: scripts/pipeline/stage_04_validate.py
    depends_on: [Project Analysis]
    contract:
      input_artifacts: ["projects/{project}/output/"]
      output_artifacts: ["projects/{project}/output/reports/"]
      definition_of_done: "Validation report is written."
      failure_code: "OUTPUT_VALIDATION_FAILED"
      retry_policy: 0
      gate: "publication_readiness"
control:
  hitl_mode: full-auto
""",
        encoding="utf-8",
    )
    project = repo_root / "projects" / "demo"
    for child in ("src", "tests", "scripts", "manuscript", "output/data", "output/reports"):
        (project / child).mkdir(parents=True)
    (project / "domain_profile.yaml").write_text(
        """
domain: code_research
display_name: Demo Research
validation_gates: [experiment_method_design, publication_readiness]
artifact_expectations: [output/data/result.csv]
""",
        encoding="utf-8",
    )
    (project / "experiment_plan.yaml").write_text(
        """
conditions:
  - name: baseline
    role: reference
  - name: proposal
    role: proposed
  - name: ablation
    role: variant
metrics:
  primary:
    name: score
    direction: maximize
protocol: "Run all conditions with identical seeds."
expected_figures: [fig:score]
expected_tables: [tbl:results]
baselines: [baseline]
ablations: [ablation]
""",
        encoding="utf-8",
    )
    result = project / "output" / "data" / "result.csv"
    result.write_text("score\n1.0\n", encoding="utf-8")
    manifest = {
        "entries": [
            {
                "path": "output/data/result.csv",
                "size_bytes": result.stat().st_size,
                "sha256": compute_sha256(result),
                "stage_num": 2,
                "stage_name": "Project Analysis",
                "contract_match": True,
                "timestamp": "",
            }
        ],
        "issues": [],
        "inventory_mode": "stable-local-output-v1",
    }
    (project / "output" / "reports" / "artifact_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    return repo_root
