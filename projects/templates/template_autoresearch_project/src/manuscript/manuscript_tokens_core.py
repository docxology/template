"""Core orchestration for manuscript token hydration."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from src.artifact_loader import LoopArtifacts
from .manuscript_token_registry import STRICT_VALUE_TOKENS
from .manuscript_tables import build_table_specs, variable_provenance_table
from src.json_coerce import mapping, mapping_list
from .manuscript_tokens_figures import put_figure_blocks, save_figure_blocks
from .manuscript_tokens_format import (
    string_value,
)
from .manuscript_tokens_ml import compute_ml_variables, put_ml_detail_variables

_TOKEN_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")


def compute_variables(project_root: Path) -> dict[str, str]:
    """Compute strict manuscript variables from the validated loop payload."""
    variables, _provenance = compute_variables_and_provenance(
        project_root,
        require_valid=True,
        validate_sources=True,
    )
    return variables


def compute_variables_and_provenance(
    project_root: Path,
    *,
    require_valid: bool = True,
    validate_sources: bool = False,
) -> tuple[dict[str, str], dict[str, object]]:
    """Compute manuscript variables plus source provenance."""
    artifacts = _load_project_artifacts(project_root, require_valid=require_valid)
    variables, provenance = _build_variables(project_root, artifacts)
    if validate_sources:
        validate_manuscript_source_values(project_root, variables)
    return variables, _provenance_payload(provenance)


def compute_variables_from_payload(payload: dict[str, Any]) -> dict[str, str]:
    """Compute manuscript variables from an in-memory loop payload."""
    metrics = payload.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}
    config = payload.get("config", {})
    if not isinstance(config, dict):
        config = {}
    stage_results = payload.get("stage_results", [])
    claims = payload.get("claims", [])
    stage_count = int(metrics.get("stage_count", len(stage_results)) or 0)
    supported_claim_count = int(metrics.get("supported_claim_count", len(claims)) or 0)
    required_artifact_count = int(metrics.get("required_artifact_count", 0) or 0)
    readiness_valid = bool(metrics.get("readiness_valid", False))
    readiness_status = "passed" if readiness_valid else "requires review"
    return {
        "AUTORESEARCH_TOPIC": str(config.get("topic", "Deterministic AutoResearch")),
        "LOOP_STAGE_COUNT": str(stage_count),
        "SUPPORTED_CLAIM_COUNT": str(supported_claim_count),
        "REQUIRED_ARTIFACT_COUNT": str(required_artifact_count),
        "READINESS_STATUS": readiness_status,
        "READINESS_VALID": str(readiness_valid).lower(),
        **compute_ml_variables(payload.get("ml_task", {})),
    }


def validate_manuscript_source_values(project_root: Path, variables: dict[str, str]) -> None:
    """Reject raw run-derived values in numbered manuscript sources."""
    strict_pairs = _strict_value_pairs(variables)
    issues: list[str] = []
    for path in sorted((project_root / "manuscript").glob("[0-9][0-9]_*.md")):
        source = _TOKEN_RE.sub("", path.read_text(encoding="utf-8"))
        for token, value in strict_pairs:
            if _raw_value_present(source, value):
                issues.append(f"{path.name}: raw run-derived value for {token!s} appears as {value!r}")
    if issues:
        raise ValueError("Numbered manuscript sources contain uninjected run-derived values:\n" + "\n".join(issues))


def write_manuscript_hydration_artifacts(
    project_root: Path,
    *,
    require_valid: bool = False,
    validate_sources: bool = False,
) -> list[Path]:
    """Write variables, provenance, and figure-block sidecars."""
    variables, provenance = compute_variables_and_provenance(
        project_root,
        require_valid=require_valid,
        validate_sources=validate_sources,
    )
    data_dir = project_root / "output" / "data"
    return [
        save_variables(variables, data_dir / "manuscript_variables.json"),
        save_variable_provenance(provenance, data_dir / "manuscript_variable_provenance.json"),
        save_figure_blocks(variables, data_dir / "manuscript_figure_blocks.json"),
    ]


def save_variables(variables: dict[str, str], path: Path) -> Path:
    """Write manuscript variables as stable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(variables, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def save_variable_provenance(provenance: dict[str, object], path: Path) -> Path:
    """Write the variable-source provenance sidecar."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _load_project_artifacts(project_root: Path, *, require_valid: bool) -> LoopArtifacts:
    from src.artifact_loader import load_loop_artifacts

    return load_loop_artifacts(project_root, require_valid=require_valid)


def _build_variables(project_root: Path, artifacts: LoopArtifacts) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    loop = mapping(artifacts.loop)
    ml = mapping(artifacts.ml) or mapping(loop.get("ml_task"))
    registry = mapping(artifacts.figure_registry)
    classification = mapping(artifacts.classification_diagnostics)
    class_balance = mapping(artifacts.class_balance)
    calibration = mapping(artifacts.calibration_report)
    robustness = mapping(artifacts.robustness_report)
    probability = mapping(artifacts.probability_diagnostics)
    bootstrap = mapping(artifacts.bootstrap_intervals)
    paired = mapping(artifacts.paired_comparison)
    statistical = mapping(artifacts.statistical_summary)
    training = mapping(artifacts.training_diagnostics)
    rank_stability = mapping(artifacts.candidate_rank_stability)
    phase_ledger = mapping(artifacts.phase_ledger)
    figure_quality = mapping(artifacts.figure_quality)
    security_profile = mapping(artifacts.security_profile)
    security_threat_model = mapping(artifacts.security_threat_model)
    security_inventory = mapping(artifacts.security_inventory)
    security_attestation = mapping(artifacts.security_attestation)
    schema_manifest = mapping(artifacts.schema_manifest)
    research_object_manifest = mapping(artifacts.research_object_manifest)
    config = mapping(loop.get("config"))
    ml_task_summary = mapping(loop.get("ml_task"))
    task_config = mapping(ml.get("task_config"))
    dataset = mapping(ml.get("dataset"))
    baseline = mapping(ml.get("baseline"))
    accepted = mapping(ml.get("accepted_candidate"))
    candidates = mapping_list(ml.get("candidates"))
    variables: dict[str, str] = {}
    provenance: dict[str, dict[str, str]] = {}

    def put(key: str, value: object, source: str, pointer: str) -> None:
        variables[key] = string_value(value)
        provenance[key] = {"source": source, "pointer": pointer}

    for key, value in compute_variables_from_payload(loop).items():
        put(key, value, *_default_provenance_for_key(key))
    put(
        "PROJECT_NAME",
        loop.get("project_name", "template_autoresearch_project"),
        "output/data/autoresearch_loop.json",
        "/project_name",
    )
    put(
        "AUTONOMY_LEVEL",
        config.get("autonomy_level", "proposal_only"),
        "output/data/autoresearch_loop.json",
        "/config/autonomy_level",
    )
    put(
        "REVIEW_POLICY",
        config.get("review_policy", "human_review_required"),
        "output/data/autoresearch_loop.json",
        "/config/review_policy",
    )
    put(
        "ACCEPTANCE_POLICY",
        config.get("acceptance_policy", ""),
        "output/data/autoresearch_loop.json",
        "/config/acceptance_policy",
    )
    put(
        "DISCLOSURE_TEXT",
        config.get("disclosure_text", "N/A"),
        "output/data/autoresearch_loop.json",
        "/config/disclosure_text",
    )
    put_ml_detail_variables(
        put,
        ml=ml,
        config=config,
        ml_task_summary=ml_task_summary,
        task_config=task_config,
        dataset=dataset,
        baseline=baseline,
        accepted=accepted,
        candidates=candidates,
        classification=classification,
        calibration=calibration,
        class_balance=class_balance,
        robustness=robustness,
        probability=probability,
        bootstrap=bootstrap,
        paired=paired,
        statistical=statistical,
        training=training,
        rank_stability=rank_stability,
        phase_ledger=phase_ledger,
        figure_quality=figure_quality,
    )
    _put_security_variables(
        put,
        security_profile,
        security_threat_model,
        security_inventory,
        security_attestation,
    )
    _put_research_object_variables(put, schema_manifest, research_object_manifest)
    _put_artifact_path_variables(put)
    put_figure_blocks(project_root, variables, provenance, registry)
    _put_tables(variables, provenance, artifacts)
    put(
        "MANUSCRIPT_VARIABLE_COUNT", len(variables) + 1, "output/data/manuscript_variable_provenance.json", "/variables"
    )
    variables["VARIABLE_PROVENANCE_TABLE"] = variable_provenance_table(provenance)
    provenance["VARIABLE_PROVENANCE_TABLE"] = {
        "source": "output/data/manuscript_variable_provenance.json",
        "pointer": "/variables",
    }
    return variables, provenance


def _put_artifact_path_variables(put: Any) -> None:
    path_tokens = {
        "ARTIFACT_MANIFEST_PATH": "output/reports/artifact_manifest.json",
        "AUTORESEARCH_CLAIMS_PATH": "output/data/autoresearch_claims.json",
        "AUTORESEARCH_LOOP_PATH": "output/data/autoresearch_loop.json",
        "AUTORESEARCH_SECURITY_PROFILE_PATH": "output/data/autoresearch_security_profile.json",
        "AUTORESEARCH_THREAT_MODEL_PATH": "output/data/autoresearch_threat_model.json",
        "AUTORESEARCH_SUPPLY_CHAIN_INVENTORY_PATH": "output/data/autoresearch_supply_chain_inventory.json",
        "AUTORESEARCH_INTEGRITY_ATTESTATION_PATH": "output/data/autoresearch_integrity_attestation.json",
        "AUTORESEARCH_PHASE_LEDGER_PATH": "output/data/autoresearch_phase_ledger.json",
        "AUTORESEARCH_SCHEMA_MANIFEST_PATH": "output/data/autoresearch_schema_manifest.json",
        "FIGURE_QUALITY_REPORT_PATH": "output/data/figure_quality_report.json",
        "RESEARCH_OBJECT_MANIFEST_PATH": "output/data/research_object_manifest.json",
        "AUTORESEARCH_SECURITY_REVIEW_PATH": "output/reports/autoresearch_security_review.md",
        "BENCHMARK_SCORES_PATH": "output/data/benchmark_scores.json",
        "EVIDENCE_REGISTRY_PATH": "output/reports/evidence_registry.json",
        "FIGURE_BLOCKS_PATH": "output/data/manuscript_figure_blocks.json",
        "FIGURE_REGISTRY_PATH": "output/figures/figure_registry.json",
        "MANUSCRIPT_VARIABLES_PATH": "output/data/manuscript_variables.json",
        "ML_BENCHMARK_SCORE_PATH": "output/reports/ml_benchmark_score.json",
        "ML_CANDIDATE_LEDGER_PATH": "output/data/ml_candidate_ledger.json",
        "ML_CONFUSION_MATRIX_PATH": "output/data/ml_confusion_matrix.csv",
        "ML_TRAINING_HISTORY_PATH": "output/data/ml_training_history.csv",
        "ML_ERROR_EXAMPLES_PATH": "output/data/ml_error_examples.json",
        "ML_PREDICTION_RECORDS_PATH": "output/data/ml_prediction_records.json",
        "ML_CLASSIFICATION_DIAGNOSTICS_PATH": "output/data/ml_classification_diagnostics.json",
        "ML_CANDIDATE_INTERVALS_PATH": "output/data/ml_candidate_intervals.json",
        "ML_CLASS_BALANCE_PATH": "output/data/ml_class_balance.json",
        "ML_CALIBRATION_REPORT_PATH": "output/data/ml_calibration_report.json",
        "ML_CALIBRATION_BIN_INTERVALS_PATH": "output/data/ml_calibration_bin_intervals.json",
        "ML_ROBUSTNESS_REPORT_PATH": "output/data/ml_robustness_report.json",
        "ML_PROBABILITY_DIAGNOSTICS_PATH": "output/data/ml_probability_diagnostics.json",
        "ML_BOOTSTRAP_INTERVALS_PATH": "output/data/ml_bootstrap_intervals.json",
        "ML_PAIRED_COMPARISON_PATH": "output/data/ml_paired_comparison.json",
        "ML_STATISTICAL_SUMMARY_PATH": "output/data/ml_statistical_summary.json",
        "ML_TRAINING_DIAGNOSTICS_PATH": "output/data/ml_training_diagnostics.json",
        "ML_CANDIDATE_RANK_STABILITY_PATH": "output/data/ml_candidate_rank_stability.json",
        "ML_CANDIDATE_SELECTION_AUDIT_PATH": "output/data/ml_candidate_selection_audit.json",
        "ML_DIAGNOSTIC_BOUNDARY_PATH": "output/data/ml_diagnostic_boundary.json",
        "ML_RESULTS_PATH": "output/data/ml_task_results.json",
        "READINESS_REPORT_PATH": "output/reports/autoresearch_readiness.json",
        "RESEARCH_PROGRAM_PATH": "output/data/research_program.json",
        "REVIEW_DECISIONS_PATH": "output/data/review_decisions.json",
        "RUN_LEDGER_PATH": "output/data/run_ledger.json",
        "VARIABLE_PROVENANCE_PATH": "output/data/manuscript_variable_provenance.json",
    }
    for token, path in path_tokens.items():
        put(token, path, "output/data/autoresearch_loop.json", "/output_paths")


def _put_security_variables(
    put: Any,
    security_profile: dict[str, Any],
    threat_model: dict[str, Any],
    inventory: dict[str, Any],
    attestation: dict[str, Any],
) -> None:
    summary = mapping(threat_model.get("summary"))
    put(
        "SECURITY_PROFILE_MODE",
        security_profile.get("mode", "N/A"),
        "output/data/autoresearch_security_profile.json",
        "/mode",
    )
    put(
        "SECURITY_NETWORK_POLICY",
        security_profile.get("network_policy", "N/A"),
        "output/data/autoresearch_security_profile.json",
        "/network_policy",
    )
    put(
        "SECURITY_INTEGRITY_ALGORITHM",
        security_profile.get("integrity_algorithm", "N/A"),
        "output/data/autoresearch_security_profile.json",
        "/integrity_algorithm",
    )
    put(
        "SECURITY_EXTERNAL_SIGNING",
        str(bool(security_profile.get("external_signing", False))).lower(),
        "output/data/autoresearch_security_profile.json",
        "/external_signing",
    )
    put(
        "SECURITY_FRAMEWORKS",
        ", ".join(str(value) for value in security_profile.get("threat_model_frameworks", []) if value),
        "output/data/autoresearch_security_profile.json",
        "/threat_model_frameworks",
    )
    put(
        "SECURITY_CLAIM_SCOPE",
        security_profile.get("claim_scope", "N/A"),
        "output/data/autoresearch_security_profile.json",
        "/claim_scope",
    )
    put(
        "SECURITY_ASSET_COUNT",
        summary.get("asset_count", "N/A"),
        "output/data/autoresearch_threat_model.json",
        "/summary/asset_count",
    )
    put(
        "SECURITY_THREAT_COUNT",
        summary.get("threat_count", "N/A"),
        "output/data/autoresearch_threat_model.json",
        "/summary/threat_count",
    )
    put(
        "SECURITY_CONTROL_COUNT",
        summary.get("control_count", "N/A"),
        "output/data/autoresearch_threat_model.json",
        "/summary/control_count",
    )
    put(
        "SECURITY_INVENTORY_INPUT_COUNT",
        len(mapping_list(inventory.get("inputs"))),
        "output/data/autoresearch_supply_chain_inventory.json",
        "/inputs",
    )
    put(
        "SECURITY_INVENTORY_ARTIFACT_COUNT",
        len(mapping_list(inventory.get("generated_artifacts"))),
        "output/data/autoresearch_supply_chain_inventory.json",
        "/generated_artifacts",
    )
    put(
        "SECURITY_ATTESTATION_STATUS",
        attestation.get("status", "N/A"),
        "output/data/autoresearch_integrity_attestation.json",
        "/status",
    )
    put(
        "SECURITY_ATTESTATION_CHECKED_COUNT",
        attestation.get("checked_count", "N/A"),
        "output/data/autoresearch_integrity_attestation.json",
        "/checked_count",
    )
    put(
        "SECURITY_ATTESTATION_MISSING_COUNT",
        attestation.get("missing_count", "N/A"),
        "output/data/autoresearch_integrity_attestation.json",
        "/missing_count",
    )
    put(
        "SECURITY_ATTESTATION_MISMATCH_COUNT",
        attestation.get("mismatch_count", "N/A"),
        "output/data/autoresearch_integrity_attestation.json",
        "/mismatch_count",
    )


def _put_research_object_variables(
    put: Any,
    schema_manifest: dict[str, Any],
    research_object_manifest: dict[str, Any],
) -> None:
    approval_state = mapping(research_object_manifest.get("approval_state"))
    put(
        "SCHEMA_MANIFEST_SCHEMA_COUNT",
        len(mapping_list(schema_manifest.get("schema_artifacts"))),
        "output/data/autoresearch_schema_manifest.json",
        "/schema_artifacts",
    )
    put(
        "RESEARCH_OBJECT_ARTIFACT_COUNT",
        research_object_manifest.get("artifact_count", "N/A"),
        "output/data/research_object_manifest.json",
        "/artifact_count",
    )
    put(
        "RESEARCH_OBJECT_APPROVAL_STATE",
        str(bool(approval_state.get("publication_approved", False))).lower(),
        "output/data/research_object_manifest.json",
        "/approval_state/publication_approved",
    )


def _put_tables(
    variables: dict[str, str],
    provenance: dict[str, dict[str, str]],
    artifacts: LoopArtifacts,
) -> None:
    table_specs = build_table_specs(artifacts)
    for token, (value, source, pointer) in table_specs.items():
        variables[token] = value
        provenance[token] = {"source": source, "pointer": pointer}


def _provenance_payload(provenance: dict[str, dict[str, str]]) -> dict[str, object]:
    return {
        "schema": "template-autoresearch-manuscript-provenance-v1",
        "variables": provenance,
    }


def _default_provenance_for_key(key: str) -> tuple[str, str]:
    pointers = {
        "AUTORESEARCH_TOPIC": "/config/topic",
        "LOOP_STAGE_COUNT": "/metrics/stage_count",
        "SUPPORTED_CLAIM_COUNT": "/metrics/supported_claim_count",
        "REQUIRED_ARTIFACT_COUNT": "/metrics/required_artifact_count",
        "READINESS_STATUS": "/metrics/readiness_valid",
        "READINESS_VALID": "/metrics/readiness_valid",
    }
    ml_pointers = {
        "ML_TASK_SEED": "/seed",
        "CANDIDATE_COUNT": "/candidate_count",
        "EVALUATED_CANDIDATE_COUNT": "/evaluated_candidate_count",
        "ACCEPTED_CANDIDATE_ID": "/accepted_candidate_id",
        "BASELINE_ACCURACY": "/baseline_accuracy",
        "BEST_ACCURACY": "/best_accuracy",
        "ACCURACY_DELTA": "/accuracy_delta",
        "BUDGET_EXHAUSTED": "/budget_exhausted",
        "BENCHMARK_SCORE": "/benchmark_score",
        "LLM_CALLS_USED": "/llm_calls_used",
        "COST_USD_USED": "/cost_usd_used",
        "DATASET_NAME": "/dataset_name",
        "TRAIN_SIZE": "/train_size",
        "TEST_SIZE": "/test_size",
        "ACCEPTED_MODEL_TYPE": "/accepted_model_type",
        "ACCEPTED_PARAMETER_COUNT": "/parameter_count",
        "TRANSFORMER_EVALUATED": "/transformer_evaluated",
    }
    if key in pointers:
        return "output/data/autoresearch_loop.json", pointers[key]
    return "output/data/ml_task_results.json", ml_pointers.get(key, "/")


def _validate_required_artifacts(project_root: Path, loop_payload: dict[str, Any]) -> None:
    config = mapping(loop_payload.get("config"))
    required = config.get("required_artifacts", [])
    if not isinstance(required, list):
        raise ValueError("loop payload required_artifacts must be a list")
    missing = [path for path in required if isinstance(path, str) and not (project_root / path).exists()]
    if missing:
        raise ValueError("missing required AutoResearch artifacts: " + ", ".join(sorted(missing)))


def _strict_value_pairs(variables: dict[str, str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for token, value in variables.items():
        if not value or value in {"N/A", "true", "false", "passed", "requires review"}:
            continue
        strict_token = token in STRICT_VALUE_TOKENS or token.endswith("_PATH") or token.endswith("_ACCURACY")
        if len(value) <= 3 and value.replace(".", "", 1).isdigit() and not strict_token:
            continue
        if strict_token:
            pairs.append((token, value))
    for token, value in variables.items():
        if token.startswith("FIGURE_BLOCK_"):
            match = re.match(r"!\[(?P<caption>[^\]]+)\]", value)
            if match:
                pairs.append((token, match.group("caption")))
    return pairs


def _raw_value_present(source: str, value: str) -> bool:
    if len(value) <= 3 and value.isalnum():
        pattern = rf"(?<![A-Za-z0-9_-]){re.escape(value)}(?![A-Za-z0-9_-])"
        return re.search(pattern, source) is not None
    return value in source
