"""AutoResearch config loading, domain models, and report-writer unit tests (formerly part of test_autoresearch.py)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_autoresearch_manifest_reader_preserves_explicit_inventory_mode(tmp_path: Path) -> None:
    from infrastructure.autoresearch.validation_checks import _read_artifact_manifest

    manifest_path = tmp_path / "artifact_manifest.json"
    manifest_path.write_text(
        '{"entries": [], "issues": [], "inventory_mode": "stable-local-output-v1"}\n',
        encoding="utf-8",
    )

    assert _read_artifact_manifest(manifest_path).inventory_mode == "stable-local-output-v1"


def test_autoresearch_evidence_registry_uses_local_mode_for_blanket_ignored_sidecar(
    tmp_path: Path,
) -> None:
    from infrastructure.autoresearch.models import AutoResearchConfig, AutoResearchPlan
    from infrastructure.autoresearch.validation_checks import _validate_evidence_registry

    repo_root = tmp_path / "template"
    project = tmp_path / "private" / "demo"
    variables = project / "output" / "data" / "manuscript_variables.json"
    variables.parent.mkdir(parents=True)
    variables.write_text('{"LOCAL_VALUE": 7}\n', encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True, capture_output=True)
    (project / ".gitignore").write_text("output/\n", encoding="utf-8")
    plan = AutoResearchPlan(
        repo_root=repo_root,
        project_root=project,
        project_name="demo",
        config=AutoResearchConfig(strict=True),
    )
    issues = []

    _validate_evidence_registry(project, plan, issues)

    assert issues == []


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


def test_write_report_is_byte_stable_across_checkout_roots(tmp_path: Path) -> None:
    from infrastructure.autoresearch import (
        AutoResearchConfig,
        AutoResearchIssue,
        AutoResearchPlan,
        AutoResearchReport,
        write_autoresearch_report,
    )

    def write_from_checkout(repo_root: Path) -> tuple[bytes, bytes]:
        project = repo_root / "projects" / "templates" / "demo"
        plan = AutoResearchPlan(
            repo_root=repo_root,
            project_root=project,
            project_name="templates/demo",
            config=AutoResearchConfig(source_path=str(project / "autoresearch.yaml")),
        )
        report = AutoResearchReport(
            project_name="templates/demo",
            valid=False,
            issues=(
                AutoResearchIssue(
                    severity="warning",
                    code="AUTORESEARCH.DEMO",
                    message="Demonstrate portable issue paths.",
                    source_path=str(project / "output" / "data" / "evidence.json"),
                ),
            ),
            plan=plan,
        )
        json_path, markdown_path = write_autoresearch_report(project, report)
        return json_path.read_bytes(), markdown_path.read_bytes()

    first_json, first_markdown = write_from_checkout(tmp_path / "checkout-a")
    second_json, second_markdown = write_from_checkout(tmp_path / "checkout-b")

    assert first_json == second_json
    assert first_markdown == second_markdown
    payload = json.loads(first_json)
    assert payload["plan"]["repo_root"] == "."
    assert payload["plan"]["project_root"] == "projects/templates/demo"
    assert payload["plan"]["config"]["source_path"] == "projects/templates/demo/autoresearch.yaml"
    assert payload["issues"][0]["source_path"] == "projects/templates/demo/output/data/evidence.json"


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
