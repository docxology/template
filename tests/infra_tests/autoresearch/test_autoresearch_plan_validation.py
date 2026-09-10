"""AutoResearch plan composition and phased validation tests (formerly part of test_autoresearch.py)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from infrastructure.core.pipeline.artifacts import compute_sha256

from tests.infra_tests.autoresearch._autoresearch_plan_helpers import _write_repo_scaffold


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
    present = validate_autoresearch_plan(plan, project, phase="extrinsic")
    assert present.valid is True


def test_autoresearch_rejects_mode_mismatch_and_git_ignored_manifest_entry(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan, validate_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "autoresearch.yaml").write_text(
        "strict: true\nquality_checks: [artifact_manifest]\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True, capture_output=True)
    (repo_root / ".gitignore").write_text(
        "projects/demo/output/data/result.csv\n",
        encoding="utf-8",
    )
    manifest_path = project / "output" / "reports" / "artifact_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["inventory_mode"] = "stable-shippable-output-v1"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    report = validate_autoresearch_plan(
        build_autoresearch_plan(repo_root, "demo"),
        project,
        phase="extrinsic",
    )
    messages = "\n".join(issue.message for issue in report.issues)

    assert report.valid is False
    assert "artifact inventory mode mismatch" in messages
    assert "artifact outside stable-local-output-v1 inventory" in messages


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
