"""Tests for deterministic AutoResearch readiness planning."""

from __future__ import annotations

import json
import subprocess
import sys
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
    script: 00_setup_environment.py
    contract:
      input_artifacts: ["projects/{project}/"]
      output_artifacts: ["projects/{project}/output/"]
      definition_of_done: "Environment is ready."
      failure_code: "ENVIRONMENT_SETUP_FAILED"
      retry_policy: 0
  - name: Project Analysis
    script: 02_run_analysis.py
    depends_on: [Environment Setup]
    contract:
      input_artifacts: ["projects/{project}/src/"]
      output_artifacts: ["projects/{project}/output/data/result.csv"]
      definition_of_done: "Analysis writes the declared result."
      failure_code: "PROJECT_ANALYSIS_FAILED"
      retry_policy: 0
      gate: "experiment_method_design"
  - name: Output Validation
    script: 04_validate_output.py
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
            }
        ],
        "issues": [],
    }
    (project / "output" / "reports" / "artifact_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    return repo_root


def test_load_config_defaults_when_absent(tmp_path: Path) -> None:
    from infrastructure.autoresearch import load_autoresearch_config

    project = tmp_path / "project"
    project.mkdir()

    config = load_autoresearch_config(project)

    assert config.enabled is True
    assert config.strict is False
    assert "evidence_registry" in config.quality_checks


def test_load_config_supports_method_contract_fields(tmp_path: Path) -> None:
    from infrastructure.autoresearch import load_autoresearch_config

    project = tmp_path / "project"
    project.mkdir()
    (project / "autoresearch.yaml").write_text(
        """
enabled: true
strict: true
topic: "Bounded auto-research"
autonomy_level: human_approved
budget:
  max_iterations: 3
  max_wall_clock_minutes: 15
  max_llm_calls: 0
  max_cost_usd: 0.0
edit_allowlist:
  - projects/demo/src/
  - projects/demo/scripts/
metric_direction: minimize
acceptance_policy: "accept only evidence-linked proposals"
review_gates:
  - name: proposal_review
    required: true
source_manifests:
  - output/reports/evidence_registry.json
benchmark_tasks:
  - id: smoke
    description: "Smoke benchmark"
    grading_output: output/reports/benchmark_smoke.json
disclosure_required: true
disclosure_text: "AI-assisted AutoResearch"
security_profile:
  enabled: true
  mode: local_deterministic
  threat_model_frameworks: [STRIDE, MITRE_ATT&CK_T1195]
  integrity_algorithm: sha256
  network_policy: default_offline
  external_signing: false
""",
        encoding="utf-8",
    )

    config = load_autoresearch_config(project)

    assert config.autonomy_level == "human_approved"
    assert config.budget_policy.max_iterations == 3
    assert config.budget_policy.max_wall_clock_minutes == 15
    assert config.edit_allowlist == ("projects/demo/src/", "projects/demo/scripts/")
    assert config.metric_direction == "minimize"
    assert config.acceptance_policy == "accept only evidence-linked proposals"
    assert config.review_gates[0].name == "proposal_review"
    assert config.review_gates[0].required is True
    assert config.source_manifests == ("output/reports/evidence_registry.json",)
    assert config.benchmark_tasks[0].identifier == "smoke"
    assert config.benchmark_tasks[0].grading_output == "output/reports/benchmark_smoke.json"
    assert config.disclosure_required is True
    assert config.disclosure_text == "AI-assisted AutoResearch"
    assert config.security_profile.enabled is True
    assert config.security_profile.mode == "local_deterministic"
    assert config.security_profile.threat_model_frameworks == ("STRIDE", "MITRE_ATT&CK_T1195")
    assert config.security_profile.external_signing is False


def test_load_config_rejects_unsupported_security_profile(tmp_path: Path) -> None:
    from infrastructure.autoresearch import load_autoresearch_config

    project = tmp_path / "project"
    project.mkdir()
    (project / "autoresearch.yaml").write_text(
        """
security_profile:
  enabled: true
  mode: external_signing
""",
        encoding="utf-8",
    )

    try:
        load_autoresearch_config(project)
    except ValueError as exc:
        assert "security_profile.mode" in str(exc)
    else:
        raise AssertionError("unsupported security profile mode was accepted")


def test_autoresearch_method_models_serialize_stable_payloads() -> None:
    from infrastructure.autoresearch import (
        BenchmarkTask,
        BudgetPolicy,
        EvidenceLink,
        ExperimentCandidate,
        ResearchIdea,
        ResearchProgram,
        ReviewGate,
        RunLedger,
        SecurityProfile,
    )

    evidence = EvidenceLink(
        claim_id="idea-1",
        evidence_path="output/reports/evidence_registry.json",
        evidence_type="artifact",
    )
    idea = ResearchIdea(
        identifier="idea-1",
        title="Bounded proposal",
        rationale="Keeps the loop inspectable.",
        status="accepted",
        evidence_links=(evidence,),
    )
    candidate = ExperimentCandidate(
        identifier="exp-1",
        idea_id="idea-1",
        status="deferred",
        metric_name="readiness",
        metric_direction="maximize",
        touched_paths=("projects/demo/src/loop.py",),
        expected_artifacts=("output/data/run_ledger.json",),
    )
    program = ResearchProgram(
        path="program.md",
        summary="Human-authored research program.",
        autonomy_level="proposal_only",
        budget_policy=BudgetPolicy(max_iterations=2, max_wall_clock_minutes=10),
        edit_allowlist=("projects/demo/src/",),
    )
    ledger = RunLedger(
        budget_policy=program.budget_policy,
        iterations_used=2,
        wall_clock_minutes_used=10,
        budget_exhausted=True,
        exhaustion_reason="iteration budget reached",
    )

    assert program.to_dict()["budget_policy"]["max_iterations"] == 2
    assert idea.to_dict()["evidence_links"][0]["evidence_path"].endswith("evidence_registry.json")
    assert candidate.to_dict()["touched_paths"] == ["projects/demo/src/loop.py"]
    assert ledger.to_dict()["budget_exhausted"] is True
    assert ReviewGate(name="proposal_review").to_dict()["decision"] == ""
    assert SecurityProfile(enabled=True).to_dict()["mode"] == "local_deterministic"
    assert (
        BenchmarkTask(identifier="smoke", description="Smoke", grading_output="out.json").to_dict()["grading_output"]
        == "out.json"
    )


def test_build_plan_composes_pipeline_and_project_overlays(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    (repo_root / "projects" / "demo" / "autoresearch.yaml").write_text(
        """
enabled: true
strict: true
topic: "Deterministic readiness"
quality_checks: [domain_profile, experiment_plan, pipeline_contracts, artifact_manifest]
stage_gates: [Project Analysis, Output Validation]
required_artifacts: [output/data/result.csv]
""",
        encoding="utf-8",
    )

    plan = build_autoresearch_plan(repo_root, "demo")

    assert plan.config.topic == "Deterministic readiness"
    assert plan.domain == "code_research"
    assert [stage.name for stage in plan.stages] == [
        "Environment Setup",
        "Project Analysis",
        "Output Validation",
    ]
    assert plan.stage_gates == ("Project Analysis", "Output Validation")
    assert "output/data/result.csv" in plan.required_artifacts


def test_validation_reports_invalid_stage_and_missing_artifact(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan, validate_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [domain_profile, experiment_plan, pipeline_contracts, artifact_manifest]
stage_gates: [Unknown Stage]
required_artifacts: [output/data/missing.csv]
""",
        encoding="utf-8",
    )

    plan = build_autoresearch_plan(repo_root, "demo")
    report = validate_autoresearch_plan(plan, project)

    assert report.valid is False
    assert {issue.code for issue in report.issues} >= {
        "AUTORESEARCH.STAGE_UNKNOWN",
        "AUTORESEARCH.ARTIFACT_MISSING",
    }
    assert report.summary["errors"] >= 2


def test_validation_checks_enabled_security_profile(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan, validate_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "output" / "figures").mkdir(parents=True, exist_ok=True)
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [security_profile]
security_profile:
  enabled: true
  mode: local_deterministic
  threat_model_frameworks: [STRIDE, MITRE_ATT&CK_T1195]
  integrity_algorithm: sha256
  network_policy: default_offline
  external_signing: false
""",
        encoding="utf-8",
    )
    (project / "output" / "data" / "autoresearch_security_profile.json").write_text(
        json.dumps(
            {
                "enabled": True,
                "mode": "local_deterministic",
                "integrity_algorithm": "sha256",
                "network_policy": "default_offline",
                "external_signing": False,
            }
        ),
        encoding="utf-8",
    )
    for name in (
        "autoresearch_threat_model.json",
        "autoresearch_supply_chain_inventory.json",
        "autoresearch_inventory_export.json",
    ):
        (project / "output" / "data" / name).write_text("{}\n", encoding="utf-8")
    attestation = project / "output" / "data" / "autoresearch_integrity_attestation.json"
    attestation.write_text(json.dumps({"status": "passed"}), encoding="utf-8")
    (project / "output" / "reports" / "autoresearch_security_review.md").write_text("# Review\n", encoding="utf-8")
    for name in ("autoresearch_security_control_matrix.png", "autoresearch_integrity_chain.png"):
        (project / "output" / "figures" / name).write_bytes(b"png")

    plan = build_autoresearch_plan(repo_root, "demo")
    report = validate_autoresearch_plan(plan, project, phase="extrinsic")
    assert report.valid is True

    attestation.write_text(json.dumps({"status": "failed"}), encoding="utf-8")
    failed = validate_autoresearch_plan(plan, project, phase="extrinsic")
    assert failed.valid is False
    assert any(issue.code == "AUTORESEARCH.SECURITY_ATTESTATION_FAILED" for issue in failed.issues)


def test_external_method_contract_validation_passes_with_declared_artifacts(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan, validate_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "manuscript" / "02_methodology.md").write_text(
        "This manuscript declares {{DISCLOSURE_TEXT}} with human review.\n",
        encoding="utf-8",
    )
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [method_contracts, review_gates, benchmark_tasks, ai_disclosure]
autonomy_level: proposal_only
edit_allowlist: [projects/demo/src/]
review_gates:
  - name: proposal_review
    required: true
benchmark_tasks:
  - id: smoke
    description: Smoke benchmark
    grading_output: output/reports/benchmark_smoke.json
disclosure_required: true
disclosure_text: "AI-assisted AutoResearch"
""",
        encoding="utf-8",
    )
    (project / "output" / "reports" / "benchmark_smoke.json").write_text('{"score": 1.0}\n', encoding="utf-8")
    (project / "output" / "data" / "idea_ledger.json").write_text(
        json.dumps(
            {
                "ideas": [
                    {
                        "id": "idea-1",
                        "title": "Bounded proposal",
                        "status": "accepted",
                        "evidence_links": [
                            {
                                "claim_id": "idea-1",
                                "evidence_path": "output/reports/evidence_registry.json",
                            }
                        ],
                    }
                ],
                "candidates": [
                    {
                        "id": "exp-1",
                        "idea_id": "idea-1",
                        "status": "deferred",
                        "touched_paths": ["projects/demo/src/loop.py"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (project / "output" / "data" / "run_ledger.json").write_text(
        json.dumps({"budget_exhausted": True, "exhaustion_reason": "iteration budget reached"}),
        encoding="utf-8",
    )
    (project / "output" / "data" / "review_decisions.json").write_text(
        json.dumps({"decisions": [{"gate": "proposal_review", "decision": "approved"}]}),
        encoding="utf-8",
    )
    (project / "output" / "data" / "benchmark_scores.json").write_text(
        json.dumps({"tasks": [{"id": "smoke", "grading_output_path": "output/reports/benchmark_smoke.json"}]}),
        encoding="utf-8",
    )

    plan = build_autoresearch_plan(repo_root, "demo")
    report = validate_autoresearch_plan(plan, project)

    assert report.valid is True
    assert report.issues == ()


def test_external_method_contract_validation_reports_invariant_issues(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan, validate_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [method_contracts, review_gates, benchmark_tasks, ai_disclosure]
edit_allowlist: [projects/demo/src/]
review_gates:
  - name: proposal_review
    required: true
benchmark_tasks:
  - id: smoke
    description: Smoke benchmark
    grading_output: output/reports/benchmark_smoke.json
disclosure_required: true
disclosure_text: "AI-assisted AutoResearch"
""",
        encoding="utf-8",
    )
    (project / "output" / "data" / "idea_ledger.json").write_text(
        json.dumps(
            {
                "ideas": [{"id": "idea-1", "title": "Unsupported", "status": "accepted"}],
                "candidates": [{"id": "exp-1", "touched_paths": ["projects/demo/unsafe.py"]}],
            }
        ),
        encoding="utf-8",
    )
    (project / "output" / "data" / "run_ledger.json").write_text(
        json.dumps({"budget_exhausted": True}),
        encoding="utf-8",
    )
    (project / "output" / "data" / "review_decisions.json").write_text(
        json.dumps({"decisions": [{"gate": "proposal_review", "decision": "pending"}]}),
        encoding="utf-8",
    )
    (project / "output" / "data" / "benchmark_scores.json").write_text(
        json.dumps({"tasks": [{"id": "smoke"}]}),
        encoding="utf-8",
    )
    (project / "manuscript" / "02_methodology.md").write_text("No disclosure here.\n", encoding="utf-8")

    plan = build_autoresearch_plan(repo_root, "demo")
    report = validate_autoresearch_plan(plan, project)

    assert report.valid is False
    assert {issue.code for issue in report.issues} >= {
        "AUTORESEARCH.ACCEPTED_IDEA_WITHOUT_EVIDENCE",
        "AUTORESEARCH.EDIT_ALLOWLIST",
        "AUTORESEARCH.BUDGET_EXHAUSTION_UNRECORDED",
        "AUTORESEARCH.REVIEW_GATE_PENDING",
        "AUTORESEARCH.BENCHMARK_GRADING_MISSING",
        "AUTORESEARCH.AI_DISCLOSURE_MISSING",
    }


def test_review_validation_blocks_generated_self_approval(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan, validate_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [review_gates]
review_gates:
  - name: proposal_review
    required: true
""",
        encoding="utf-8",
    )
    (project / "output" / "data" / "review_decisions.json").write_text(
        json.dumps(
            {
                "publication_approved": True,
                "decisions": [{"gate": "proposal_review", "decision": "approved"}],
            }
        ),
        encoding="utf-8",
    )

    plan = build_autoresearch_plan(repo_root, "demo")
    report = validate_autoresearch_plan(plan, project, phase="extrinsic")

    assert report.valid is False
    assert "AUTORESEARCH.REVIEW_SELF_APPROVAL" in {issue.code for issue in report.issues}

    (project / "human_review.yaml").write_text(
        """
schema: template-autoresearch-human-review-v1
publication_approved: true
reviewer: Human Reviewer
reviewed_at: 2026-05-26
decisions:
  proposal_review: approved
notes: approved after inspection
""",
        encoding="utf-8",
    )

    approved = validate_autoresearch_plan(plan, project, phase="extrinsic")
    assert approved.valid is True


def test_write_report_outputs_json_and_markdown(tmp_path: Path) -> None:
    from infrastructure.autoresearch import (
        AutoResearchIssue,
        AutoResearchReport,
        write_autoresearch_report,
    )

    project = tmp_path / "project"
    project.mkdir()
    report = AutoResearchReport(
        project_name="demo",
        valid=False,
        issues=(
            AutoResearchIssue(
                severity="error",
                code="AUTORESEARCH.TEST",
                message="Example issue",
                source_path="autoresearch.yaml",
                suggested_action="Fix the config.",
            ),
        ),
    )

    json_path, md_path = write_autoresearch_report(project, report)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["summary"]["errors"] == 1
    assert "AUTORESEARCH.TEST" in md_path.read_text(encoding="utf-8")


def test_review_packet_summary_and_benchmark_scores_write_branch_outputs(tmp_path: Path) -> None:
    from infrastructure.autoresearch import (
        AutoResearchConfig,
        AutoResearchIssue,
        AutoResearchPlan,
        AutoResearchReport,
        BenchmarkTask,
    )
    from infrastructure.autoresearch.reports import (
        write_autoresearch_review_packet,
        write_autoresearch_summary,
        write_benchmark_scores,
    )

    project = tmp_path / "project"
    project.mkdir()
    (project / "output" / "reports").mkdir(parents=True)
    (project / "output" / "reports" / "graded.json").write_text('{"score": 1}\n', encoding="utf-8")
    report = AutoResearchReport(
        project_name="demo",
        valid=False,
        issues=(
            AutoResearchIssue(
                severity="warning",
                code="AUTORESEARCH.REVIEW",
                message="Human review required",
                source_path="human_review.yaml",
                suggested_action="Record a reviewer decision.",
            ),
        ),
    )
    plan = AutoResearchPlan(
        repo_root=tmp_path,
        project_root=project,
        project_name="demo",
        config=AutoResearchConfig(
            benchmark_tasks=(
                BenchmarkTask(identifier="graded", description="Present", grading_output="output/reports/graded.json"),
                BenchmarkTask(
                    identifier="missing",
                    description="Absent",
                    grading_output="output/reports/missing.json",
                ),
            )
        ),
    )

    packet_json, packet_md = write_autoresearch_review_packet(project, report)
    summary_md = write_autoresearch_summary(project, report)
    scores_path = write_benchmark_scores(project, plan)

    packet = json.loads(packet_json.read_text(encoding="utf-8"))
    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    assert packet["ready_for_review"] is False
    assert "`AUTORESEARCH.REVIEW`" in packet_md.read_text(encoding="utf-8")
    assert "Warnings: 1" in summary_md.read_text(encoding="utf-8")
    assert [task["status"] for task in scores["tasks"]] == ["graded", "missing"]


def test_validation_intrinsic_passes_without_loop_outputs(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan, validate_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "output" / "reports" / "artifact_manifest.json").unlink()
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [domain_profile, experiment_plan, pipeline_contracts, artifact_manifest, evidence_registry]
stage_gates: [Project Analysis]
required_artifacts: [output/data/result.csv]
""",
        encoding="utf-8",
    )

    plan = build_autoresearch_plan(repo_root, "demo")
    report = validate_autoresearch_plan(plan, project, phase="intrinsic")

    assert report.valid is True
    assert not any(issue.code.startswith("AUTORESEARCH.ARTIFACT") for issue in report.issues)
    assert not any(issue.code.startswith("AUTORESEARCH.EVIDENCE") for issue in report.issues)


def test_validation_extrinsic_fails_before_manifest_and_passes_after(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan, validate_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "output" / "reports" / "artifact_manifest.json").unlink()
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [artifact_manifest]
required_artifacts: [output/data/result.csv]
""",
        encoding="utf-8",
    )
    plan = build_autoresearch_plan(repo_root, "demo")

    missing = validate_autoresearch_plan(plan, project, phase="extrinsic")
    assert missing.valid is False
    assert "AUTORESEARCH.ARTIFACT_MANIFEST_MISSING" in {issue.code for issue in missing.issues}

    result = project / "output" / "data" / "result.csv"
    manifest = {
        "entries": [
            {
                "path": "output/data/result.csv",
                "size_bytes": result.stat().st_size,
                "sha256": compute_sha256(result),
                "stage_num": 2,
                "stage_name": "Project Analysis",
                "contract_match": True,
            }
        ],
        "issues": [],
    }
    (project / "output" / "reports" / "artifact_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    present = validate_autoresearch_plan(plan, project, phase="extrinsic")
    assert present.valid is True


def test_validation_phase_all_matches_combined_checks(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan, validate_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [domain_profile, artifact_manifest]
required_artifacts: [output/data/missing.csv]
""",
        encoding="utf-8",
    )
    plan = build_autoresearch_plan(repo_root, "demo")
    report = validate_autoresearch_plan(plan, project, phase="all")

    assert report.valid is False
    assert "AUTORESEARCH.ARTIFACT_MISSING" in {issue.code for issue in report.issues}


def test_cli_validate_writes_report_and_fails_on_strict_issues(tmp_path: Path) -> None:
    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [unknown_check]
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "infrastructure.autoresearch.cli",
            "validate",
            "--repo-root",
            str(repo_root),
            "--project",
            "demo",
            "--fail-on-issues",
        ],
        cwd=Path(__file__).resolve().parents[3],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert (project / "output" / "reports" / "autoresearch_readiness.json").exists()


def test_cli_plan_review_summarize_and_benchmark_write_declared_artifacts(tmp_path: Path) -> None:
    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [benchmark_tasks]
benchmark_tasks:
  - id: smoke
    description: Smoke benchmark
    grading_output: output/reports/benchmark_smoke.json
""",
        encoding="utf-8",
    )
    (project / "output" / "reports" / "benchmark_smoke.json").write_text('{"score": 1.0}\n', encoding="utf-8")

    root = Path(__file__).resolve().parents[3]
    for command in ("plan", "review-packet", "summarize", "benchmark"):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.autoresearch.cli",
                command,
                "--repo-root",
                str(repo_root),
                "--project",
                "demo",
            ],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

    assert (project / "output" / "data" / "autoresearch_plan.json").exists()
    assert (project / "output" / "reports" / "autoresearch_review_packet.md").exists()
    assert (project / "output" / "reports" / "autoresearch_summary.md").exists()
    scores = json.loads((project / "output" / "data" / "benchmark_scores.json").read_text(encoding="utf-8"))
    assert scores["tasks"][0]["id"] == "smoke"


def test_validate_autoresearch_overlay_returns_empty_without_marker(tmp_path: Path) -> None:
    from infrastructure.autoresearch import validate_autoresearch_overlay

    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)

    issues = validate_autoresearch_overlay(project, tmp_path)

    assert issues == []
    assert not (project / "output" / "reports" / "autoresearch_readiness.json").exists()


def test_validate_autoresearch_overlay_surfaces_errors_and_writes_report(tmp_path: Path) -> None:
    from infrastructure.autoresearch import validate_autoresearch_overlay

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "autoresearch.yaml").write_text(
        "strict: true\nquality_checks: [unknown_check]\n",
        encoding="utf-8",
    )

    issues = validate_autoresearch_overlay(project, repo_root)

    assert any("AUTORESEARCH.QUALITY_CHECK_UNKNOWN" in issue for issue in issues)
    assert (project / "output" / "reports" / "autoresearch_readiness.json").exists()


def test_validate_autoresearch_overlay_reports_failures_gracefully(tmp_path: Path) -> None:
    from infrastructure.autoresearch import validate_autoresearch_overlay

    # Marker present but no pipeline.yaml scaffold -> build raises, surfaced as a string.
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    (project / "autoresearch.yaml").write_text("strict: true\n", encoding="utf-8")

    issues = validate_autoresearch_overlay(project, tmp_path)

    assert any("AutoResearch readiness validation failed" in issue for issue in issues)
