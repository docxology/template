"""Validation for deterministic AutoResearch readiness plans."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import yaml

from infrastructure.autoresearch.models import (
    KNOWN_QUALITY_CHECKS,
    AutoResearchIssue,
    AutoResearchPlan,
    AutoResearchReport,
)
from infrastructure.core.pipeline.artifacts import (
    ArtifactManifest,
    ArtifactManifestEntry,
    validate_artifact_manifest,
)
from infrastructure.project.domain_profile import load_domain_profile
from infrastructure.project.drift.models import Report
from infrastructure.project.drift.orchestrator import check_project_scripts, check_repo_scripts
from infrastructure.project.experiment_plan import load_experiment_plan, validate_experiment_plan
from infrastructure.validation.evidence_registry import build_project_evidence_registry

ValidationPhase = Literal["all", "intrinsic", "extrinsic"]

INTRINSIC_QUALITY_CHECKS = frozenset(
    {
        "domain_profile",
        "experiment_plan",
        "pipeline_contracts",
        "thin_orchestrators",
        "ai_disclosure",
    }
)
EXTRINSIC_QUALITY_CHECKS = frozenset(
    {
        "evidence_registry",
        "artifact_manifest",
        "method_contracts",
        "review_gates",
        "benchmark_tasks",
        "security_profile",
    }
)
_REVIEW_DECISIONS = frozenset({"approved", "revised", "blocked", "deferred", "rejected"})
_HUMAN_REVIEW_SCHEMA = "template-autoresearch-human-review-v1"


def validate_autoresearch_plan(
    plan: AutoResearchPlan,
    project_root: Path,
    *,
    phase: ValidationPhase = "all",
) -> AutoResearchReport:
    """Validate an AutoResearch plan against deterministic repository surfaces."""
    if not plan.config.enabled:
        return AutoResearchReport(project_name=plan.project_name, valid=True, plan=plan)

    issues: list[AutoResearchIssue] = []
    stage_names = {stage.name for stage in plan.stages}
    for stage_name in plan.stage_gates:
        if stage_name not in stage_names:
            issues.append(
                _issue(
                    "error",
                    "AUTORESEARCH.STAGE_UNKNOWN",
                    f"stage_gates entry does not match a pipeline stage: {stage_name}",
                    plan.config.source_path or "autoresearch.yaml",
                    "Use an exact stage name from pipeline.yaml.",
                )
            )

    for check in plan.quality_checks:
        if check not in KNOWN_QUALITY_CHECKS:
            issues.append(
                _issue(
                    "error",
                    "AUTORESEARCH.QUALITY_CHECK_UNKNOWN",
                    f"unknown quality check: {check}",
                    plan.config.source_path or "autoresearch.yaml",
                    f"Use one of: {', '.join(sorted(KNOWN_QUALITY_CHECKS))}.",
                )
            )

    active_checks = _checks_for_phase(plan.quality_checks, phase)
    if "domain_profile" in active_checks:
        _validate_domain_profile(project_root, issues)
    if "experiment_plan" in active_checks:
        _validate_experiment_plan(project_root, plan, issues)
    if "pipeline_contracts" in active_checks:
        _validate_pipeline_contracts(plan, issues)
    if "evidence_registry" in active_checks:
        _validate_evidence_registry(project_root, plan, issues)
    if "artifact_manifest" in active_checks:
        _validate_artifact_manifest(project_root, plan, issues)
    if "thin_orchestrators" in active_checks:
        _validate_thin_orchestrators(plan, issues)
    if "method_contracts" in active_checks:
        _validate_method_contracts(project_root, plan, issues)
    if "review_gates" in active_checks:
        _validate_review_gates(project_root, plan, issues)
    if "benchmark_tasks" in active_checks:
        _validate_benchmark_tasks(project_root, plan, issues)
    if "ai_disclosure" in active_checks:
        _validate_ai_disclosure(project_root, plan, issues)
    if "security_profile" in active_checks:
        _validate_security_profile(project_root, plan, issues)

    valid = not any(issue.severity == "error" for issue in issues)
    return AutoResearchReport(project_name=plan.project_name, valid=valid, issues=tuple(issues), plan=plan)


def _checks_for_phase(
    quality_checks: tuple[str, ...],
    phase: ValidationPhase,
) -> frozenset[str]:
    configured = frozenset(quality_checks)
    if phase == "all":
        return configured
    if phase == "intrinsic":
        return configured & INTRINSIC_QUALITY_CHECKS
    return configured & EXTRINSIC_QUALITY_CHECKS


def _validate_domain_profile(project_root: Path, issues: list[AutoResearchIssue]) -> None:
    try:
        load_domain_profile(project_root)
    except ValueError as exc:
        issues.append(
            _issue(
                "error",
                "AUTORESEARCH.DOMAIN_PROFILE",
                str(exc),
                str(project_root / "domain_profile.yaml"),
                "Fix the domain profile schema.",
            )
        )


def _validate_experiment_plan(
    project_root: Path,
    plan: AutoResearchPlan,
    issues: list[AutoResearchIssue],
) -> None:
    try:
        experiment_plan = load_experiment_plan(project_root)
        result = validate_experiment_plan(experiment_plan)
    except ValueError as exc:
        issues.append(
            _issue(
                "error",
                "AUTORESEARCH.EXPERIMENT_PLAN",
                str(exc),
                str(project_root / "experiment_plan.yaml"),
                "Fix the experiment plan schema.",
            )
        )
        return
    severity = _strict_severity(plan)
    for message in result.issues:
        issues.append(
            _issue(
                severity,
                "AUTORESEARCH.EXPERIMENT_PLAN",
                message,
                str(project_root / "experiment_plan.yaml"),
                "Declare a complete deterministic experiment design.",
            )
        )


def _validate_pipeline_contracts(plan: AutoResearchPlan, issues: list[AutoResearchIssue]) -> None:
    severity = _strict_severity(plan)
    for stage in plan.stages:
        if not stage.definition_of_done.strip():
            issues.append(
                _issue(
                    severity,
                    "AUTORESEARCH.CONTRACT_MISSING_DONE",
                    f"pipeline stage lacks definition_of_done: {stage.name}",
                    "pipeline.yaml",
                    "Add a concrete definition_of_done to the stage contract.",
                )
            )
        if not stage.output_artifacts:
            issues.append(
                _issue(
                    severity,
                    "AUTORESEARCH.CONTRACT_MISSING_OUTPUTS",
                    f"pipeline stage lacks output_artifacts: {stage.name}",
                    "pipeline.yaml",
                    "Declare the stage output artifacts.",
                )
            )


def _validate_evidence_registry(
    project_root: Path,
    plan: AutoResearchPlan,
    issues: list[AutoResearchIssue],
) -> None:
    registry = build_project_evidence_registry(project_root)
    if registry.facts():
        return
    issues.append(
        _issue(
            _strict_severity(plan),
            "AUTORESEARCH.EVIDENCE_REGISTRY_EMPTY",
            "evidence registry has no registered project facts",
            str(project_root / "output" / "reports" / "evidence_registry.json"),
            "Generate or register artifact-backed manuscript facts before publication.",
        )
    )


def _validate_artifact_manifest(
    project_root: Path,
    plan: AutoResearchPlan,
    issues: list[AutoResearchIssue],
) -> None:
    severity = _strict_severity(plan)
    manifest_path = project_root / "output" / "reports" / "artifact_manifest.json"
    if not manifest_path.exists():
        issues.append(
            _issue(
                severity,
                "AUTORESEARCH.ARTIFACT_MANIFEST_MISSING",
                "artifact manifest is missing",
                str(manifest_path),
                "Run the pipeline or refresh output artifact manifests.",
            )
        )
    else:
        try:
            manifest = _read_artifact_manifest(manifest_path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            issues.append(
                _issue(
                    "error",
                    "AUTORESEARCH.ARTIFACT_MANIFEST_INVALID",
                    f"artifact manifest cannot be parsed: {exc}",
                    str(manifest_path),
                    "Regenerate the artifact manifest.",
                )
            )
        else:
            report = validate_artifact_manifest(manifest, project_dir=project_root)
            for message in report.issues:
                issues.append(
                    _issue(
                        severity,
                        "AUTORESEARCH.ARTIFACT_MANIFEST_ISSUE",
                        message,
                        str(manifest_path),
                        "Regenerate declared outputs or update the stage contract.",
                    )
                )

    for artifact in plan.required_artifacts:
        artifact_path = _artifact_path(project_root, artifact)
        if not artifact_path.exists():
            issues.append(
                _issue(
                    severity,
                    "AUTORESEARCH.ARTIFACT_MISSING",
                    f"required artifact is missing: {artifact}",
                    artifact,
                    "Run the producing pipeline stage or correct required_artifacts.",
                )
            )


def _validate_thin_orchestrators(
    plan: AutoResearchPlan,
    issues: list[AutoResearchIssue],
) -> None:
    drift_report = Report()
    check_project_scripts(plan.project_root, plan.repo_root, drift_report, plan.project_name)
    check_repo_scripts(plan.repo_root, drift_report)
    for finding in (*drift_report.errors(), *drift_report.warnings()):
        severity = "error" if finding.severity == "ERROR" and plan.config.strict else "warning"
        issues.append(
            _issue(
                severity,
                "AUTORESEARCH.THIN_ORCHESTRATOR",
                finding.message,
                finding.project,
                "Move reusable logic into infrastructure/ or project src/ modules.",
            )
        )


def _validate_method_contracts(
    project_root: Path,
    plan: AutoResearchPlan,
    issues: list[AutoResearchIssue],
) -> None:
    severity = _strict_severity(plan)
    idea_ledger_path = project_root / "output" / "data" / "idea_ledger.json"
    idea_ledger = _read_json_mapping(idea_ledger_path, issues, severity, "AUTORESEARCH.IDEA_LEDGER_INVALID")
    if idea_ledger is None:
        issues.append(
            _issue(
                severity,
                "AUTORESEARCH.IDEA_LEDGER_MISSING",
                "idea ledger is missing or invalid",
                str(idea_ledger_path),
                "Generate output/data/idea_ledger.json from the AutoResearch loop.",
            )
        )
    else:
        _validate_idea_ledger(idea_ledger, plan, str(idea_ledger_path), issues)

    run_ledger_path = project_root / "output" / "data" / "run_ledger.json"
    run_ledger = _read_json_mapping(run_ledger_path, issues, severity, "AUTORESEARCH.RUN_LEDGER_INVALID")
    if run_ledger is None:
        issues.append(
            _issue(
                severity,
                "AUTORESEARCH.RUN_LEDGER_MISSING",
                "run ledger is missing or invalid",
                str(run_ledger_path),
                "Generate output/data/run_ledger.json with replay and budget status.",
            )
        )
        return
    if bool(run_ledger.get("budget_exhausted")) and not str(run_ledger.get("exhaustion_reason", "")).strip():
        issues.append(
            _issue(
                severity,
                "AUTORESEARCH.BUDGET_EXHAUSTION_UNRECORDED",
                "budget_exhausted is true but no exhaustion_reason is recorded",
                str(run_ledger_path),
                "Record why the bounded run stopped.",
            )
        )


def _validate_idea_ledger(
    payload: dict[str, Any],
    plan: AutoResearchPlan,
    source_path: str,
    issues: list[AutoResearchIssue],
) -> None:
    severity = _strict_severity(plan)
    ideas = payload.get("ideas", [])
    candidates = payload.get("candidates", [])
    if not isinstance(ideas, list):
        ideas = []
    if not isinstance(candidates, list):
        candidates = []

    for idea in ideas:
        if not isinstance(idea, dict):
            continue
        if str(idea.get("status", "")).strip() == "accepted" and not _has_evidence_links(idea):
            issues.append(
                _issue(
                    severity,
                    "AUTORESEARCH.ACCEPTED_IDEA_WITHOUT_EVIDENCE",
                    f"accepted idea lacks evidence links: {idea.get('id', '<unknown>')}",
                    source_path,
                    "Attach at least one evidence link to every accepted idea.",
                )
            )

    allowlist = plan.config.edit_allowlist
    if not allowlist and candidates:
        issues.append(
            _issue(
                severity,
                "AUTORESEARCH.EDIT_ALLOWLIST_MISSING",
                "experiment candidates exist but edit_allowlist is empty",
                plan.config.source_path or "autoresearch.yaml",
                "Declare edit_allowlist entries for candidate touched_paths.",
            )
        )
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        raw_paths = candidate.get("touched_paths", [])
        touched_paths = raw_paths if isinstance(raw_paths, list) else []
        for touched_path in touched_paths:
            path_text = str(touched_path)
            if allowlist and not any(path_text.startswith(prefix) for prefix in allowlist):
                issues.append(
                    _issue(
                        severity,
                        "AUTORESEARCH.EDIT_ALLOWLIST",
                        f"candidate touches path outside edit_allowlist: {path_text}",
                        source_path,
                        "Restrict proposals to declared editable paths or expand the allowlist deliberately.",
                    )
                )


def _has_evidence_links(idea: dict[str, Any]) -> bool:
    links = idea.get("evidence_links", [])
    if not isinstance(links, list):
        return False
    return any(isinstance(link, dict) and str(link.get("evidence_path", "")).strip() for link in links)


def _validate_review_gates(
    project_root: Path,
    plan: AutoResearchPlan,
    issues: list[AutoResearchIssue],
) -> None:
    required_gates = [gate for gate in plan.config.review_gates if gate.required]
    if not required_gates:
        return
    severity = _strict_severity(plan)
    path = project_root / "output" / "data" / "review_decisions.json"
    payload = _read_json_mapping(path, issues, severity, "AUTORESEARCH.REVIEW_DECISIONS_INVALID")
    if payload is None:
        issues.append(
            _issue(
                severity,
                "AUTORESEARCH.REVIEW_DECISIONS_MISSING",
                "required review gates exist but review_decisions.json is missing",
                str(path),
                "Record human decisions for every required review gate.",
            )
        )
        return
    if payload.get("publication_approved") is True:
        _validate_publication_approval_source(project_root, path, issues)
    decisions = _review_decision_map(payload)
    for gate in required_gates:
        decision = decisions.get(gate.name, "").strip()
        if decision not in _REVIEW_DECISIONS:
            issues.append(
                _issue(
                    severity,
                    "AUTORESEARCH.REVIEW_GATE_PENDING",
                    f"required review gate has no final decision: {gate.name}",
                    str(path),
                    "Use one of: approved, revised, blocked, deferred, rejected.",
                )
            )


def _validate_publication_approval_source(
    project_root: Path,
    generated_path: Path,
    issues: list[AutoResearchIssue],
) -> None:
    source_path = project_root / "human_review.yaml"
    try:
        payload = yaml.safe_load(source_path.read_text(encoding="utf-8")) if source_path.exists() else None
    except (OSError, yaml.YAMLError) as exc:
        issues.append(
            _issue(
                "error",
                "AUTORESEARCH.REVIEW_SELF_APPROVAL",
                f"generated approval cannot be verified from human_review.yaml: {exc}",
                str(generated_path),
                "Use a valid human_review.yaml as the approval source.",
            )
        )
        return
    if not isinstance(payload, dict) or payload.get("schema") != _HUMAN_REVIEW_SCHEMA:
        issues.append(
            _issue(
                "error",
                "AUTORESEARCH.REVIEW_SELF_APPROVAL",
                "generated outputs claim publication approval without a valid human_review.yaml source",
                str(generated_path),
                "Add a human-authored human_review.yaml or keep publication_approved false.",
            )
        )
        return
    if payload.get("publication_approved") is not True:
        issues.append(
            _issue(
                "error",
                "AUTORESEARCH.REVIEW_SELF_APPROVAL",
                "generated outputs claim publication approval but human_review.yaml is unapproved",
                str(generated_path),
                "Only copy publication approval from a human-authored approval file.",
            )
        )


def _review_decision_map(payload: dict[str, Any]) -> dict[str, str]:
    decisions: dict[str, str] = {}
    raw = payload.get("decisions", [])
    if not isinstance(raw, list):
        return decisions
    for row in raw:
        if not isinstance(row, dict):
            continue
        gate = str(row.get("gate") or row.get("name") or "").strip()
        decision = str(row.get("decision", "") or "").strip()
        if gate:
            decisions[gate] = decision
    return decisions


def _validate_benchmark_tasks(
    project_root: Path,
    plan: AutoResearchPlan,
    issues: list[AutoResearchIssue],
) -> None:
    if not plan.config.benchmark_tasks:
        return
    severity = _strict_severity(plan)
    path = project_root / "output" / "data" / "benchmark_scores.json"
    payload = _read_json_mapping(path, issues, severity, "AUTORESEARCH.BENCHMARK_SCORES_INVALID")
    if payload is None:
        issues.append(
            _issue(
                severity,
                "AUTORESEARCH.BENCHMARK_SCORES_MISSING",
                "benchmark tasks are configured but benchmark_scores.json is missing",
                str(path),
                "Run the AutoResearch benchmark writer.",
            )
        )
        return
    tasks = _benchmark_task_map(payload)
    for task in plan.config.benchmark_tasks:
        row = tasks.get(task.identifier)
        grading_output = ""
        if row is not None:
            grading_output = str(row.get("grading_output_path") or row.get("grading_output") or "")
        if not grading_output:
            grading_output = task.grading_output
        if row is None or not _artifact_path(project_root, grading_output).exists():
            issues.append(
                _issue(
                    severity,
                    "AUTORESEARCH.BENCHMARK_GRADING_MISSING",
                    f"benchmark task lacks grading output: {task.identifier}",
                    str(path),
                    "Write a grading output for every configured benchmark task.",
                )
            )


def _benchmark_task_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = payload.get("tasks", [])
    if not isinstance(raw, list):
        return {}
    tasks: dict[str, dict[str, Any]] = {}
    for row in raw:
        if not isinstance(row, dict):
            continue
        identifier = str(row.get("id") or row.get("identifier") or "").strip()
        if identifier:
            tasks[identifier] = row
    return tasks


def _validate_ai_disclosure(
    project_root: Path,
    plan: AutoResearchPlan,
    issues: list[AutoResearchIssue],
) -> None:
    if not plan.config.disclosure_required:
        return
    disclosure = plan.config.disclosure_text.strip()
    if not disclosure:
        return
    manuscript_dirs = (project_root / "manuscript", project_root / "output" / "manuscript")
    for directory in manuscript_dirs:
        if not directory.exists():
            continue
        for path in directory.glob("*.md"):
            if _contains_disclosure_or_token(path.read_text(encoding="utf-8"), disclosure):
                return
    variables_path = project_root / "output" / "data" / "manuscript_variables.json"
    if variables_path.exists():
        variables = _read_json_mapping(
            variables_path,
            issues,
            _strict_severity(plan),
            "AUTORESEARCH.AI_DISCLOSURE_VARIABLES_MALFORMED",
        )
        if variables is not None and variables.get("DISCLOSURE_TEXT") == disclosure:
            return
    issues.append(
        _issue(
            _strict_severity(plan),
            "AUTORESEARCH.AI_DISCLOSURE_MISSING",
            f"configured disclosure text was not found: {disclosure}",
            str(project_root / "manuscript"),
            "Add the configured disclosure to the manuscript source or generated manuscript.",
        )
    )


def _contains_disclosure_or_token(text: str, disclosure: str) -> bool:
    return disclosure in text or "{{DISCLOSURE_TEXT}}" in text


def _validate_security_profile(
    project_root: Path,
    plan: AutoResearchPlan,
    issues: list[AutoResearchIssue],
) -> None:
    profile = plan.config.security_profile
    if not profile.enabled:
        return
    severity = _strict_severity(plan)
    paths = {
        "profile": project_root / "output" / "data" / "autoresearch_security_profile.json",
        "threat_model": project_root / "output" / "data" / "autoresearch_threat_model.json",
        "inventory": project_root / "output" / "data" / "autoresearch_supply_chain_inventory.json",
        "inventory_export": project_root / "output" / "data" / "autoresearch_inventory_export.json",
        "attestation": project_root / "output" / "data" / "autoresearch_integrity_attestation.json",
        "review": project_root / "output" / "reports" / "autoresearch_security_review.md",
        "control_matrix": project_root / "output" / "figures" / "autoresearch_security_control_matrix.png",
        "integrity_chain": project_root / "output" / "figures" / "autoresearch_integrity_chain.png",
    }
    for label, path in paths.items():
        if not path.exists():
            issues.append(
                _issue(
                    severity,
                    "AUTORESEARCH.SECURITY_ARTIFACT_MISSING",
                    f"security artifact is missing: {label}",
                    str(path),
                    "Run the AutoResearch loop to regenerate local security artifacts.",
                )
            )
    if any(not path.exists() for path in paths.values()):
        return

    payload = _read_json_mapping(
        paths["profile"],
        issues,
        severity,
        "AUTORESEARCH.SECURITY_PROFILE_INVALID",
    )
    if payload is None:
        return
    expected = profile.to_dict()
    for key in ("mode", "integrity_algorithm", "network_policy", "external_signing"):
        if payload.get(key) != expected[key]:
            issues.append(
                _issue(
                    severity,
                    "AUTORESEARCH.SECURITY_PROFILE_MISMATCH",
                    f"security profile {key} does not match autoresearch.yaml",
                    str(paths["profile"]),
                    "Regenerate security artifacts from the configured profile.",
                )
            )
    if payload.get("enabled") is not True:
        issues.append(
            _issue(
                severity,
                "AUTORESEARCH.SECURITY_PROFILE_DISABLED",
                "security_profile.enabled is true in config but generated profile is disabled",
                str(paths["profile"]),
                "Regenerate security artifacts from the configured profile.",
            )
        )

    attestation = _read_json_mapping(
        paths["attestation"],
        issues,
        severity,
        "AUTORESEARCH.SECURITY_ATTESTATION_INVALID",
    )
    if attestation is not None and attestation.get("status") != "passed":
        issues.append(
            _issue(
                severity,
                "AUTORESEARCH.SECURITY_ATTESTATION_FAILED",
                f"integrity attestation status is {attestation.get('status')!s}",
                str(paths["attestation"]),
                "Refresh artifacts or resolve checksum mismatches before publication review.",
            )
        )


def _artifact_path(project_root: Path, artifact: str) -> Path:
    path = Path(artifact)
    if path.is_absolute():
        return path
    return project_root / path


def _read_json_mapping(
    path: Path,
    issues: list[AutoResearchIssue],
    severity: str,
    code: str,
) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(
            _issue(
                severity,
                code,
                f"JSON artifact cannot be parsed: {exc}",
                str(path),
                "Regenerate the malformed AutoResearch artifact.",
            )
        )
        return None
    if not isinstance(payload, dict):
        issues.append(
            _issue(
                severity,
                code,
                "JSON artifact root must be a mapping",
                str(path),
                "Regenerate the malformed AutoResearch artifact.",
            )
        )
        return None
    return payload


def _read_artifact_manifest(path: Path) -> ArtifactManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("manifest root must be a mapping")
    entries = tuple(_entry_from_payload(row) for row in payload.get("entries", []) if isinstance(row, dict))
    issues = tuple(str(issue) for issue in payload.get("issues", []))
    return ArtifactManifest(entries=entries, issues=issues)


def _entry_from_payload(row: dict[str, Any]) -> ArtifactManifestEntry:
    return ArtifactManifestEntry(
        path=str(row.get("path", "")),
        size_bytes=int(row.get("size_bytes", 0) or 0),
        sha256=str(row.get("sha256", "")),
        stage_num=int(row.get("stage_num", 0) or 0),
        stage_name=str(row.get("stage_name", "")),
        contract_match=bool(row.get("contract_match", False)),
        timestamp=str(row.get("timestamp", "")),
    )


def _strict_severity(plan: AutoResearchPlan) -> str:
    return "error" if plan.config.strict else "warning"


def _issue(
    severity: str,
    code: str,
    message: str,
    source_path: str,
    suggested_action: str,
) -> AutoResearchIssue:
    return AutoResearchIssue(
        severity=severity,
        code=code,
        message=message,
        source_path=source_path,
        suggested_action=suggested_action,
    )
