"""Render-time manuscript variables for the AutoResearch exemplar."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .manuscript_tables import build_table_specs, variable_provenance_table

_TOKEN_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")
_FIGURE_BLOCK_KEYS = frozenset(
    {
        "FIGURE_BLOCK_STAGE_MATRIX",
        "FIGURE_BLOCK_CANDIDATE_SCORES",
        "FIGURE_BLOCK_CONFUSION_MATRIX",
        "FIGURE_BLOCK_PER_CLASS_ACCURACY",
        "FIGURE_BLOCK_LEARNING_CURVES",
        "FIGURE_BLOCK_COMPLEXITY_ACCURACY",
        "FIGURE_BLOCK_ERROR_EXAMPLES",
        "FIGURE_BLOCK_CALIBRATION_RELIABILITY",
        "FIGURE_BLOCK_CLASSIFICATION_METRICS",
        "FIGURE_BLOCK_CONFUSION_PAIRS",
        "FIGURE_BLOCK_GENERALIZATION_GAP",
        "FIGURE_BLOCK_ROBUSTNESS_MATRIX",
        "FIGURE_BLOCK_PROBABILITY_MARGIN",
        "FIGURE_BLOCK_BOOTSTRAP_INTERVALS",
        "FIGURE_BLOCK_PAIRED_CORRECTNESS",
        "FIGURE_BLOCK_SELECTIVE_ACCURACY",
        "FIGURE_BLOCK_PROBABILITY_QUALITY",
        "FIGURE_BLOCK_TRAINING_DYNAMICS",
        "FIGURE_BLOCK_CANDIDATE_RANK_STABILITY",
        "FIGURE_BLOCK_CANDIDATE_LIFECYCLE",
        "FIGURE_BLOCK_DATASET_CLASS_BALANCE",
        "FIGURE_BLOCK_DATASET_CONTACT_SHEET",
        "FIGURE_BLOCK_CLOSURE_FLOW",
        "FIGURE_BLOCK_SECURITY_CONTROL_MATRIX",
        "FIGURE_BLOCK_INTEGRITY_CHAIN",
    }
)
_STRICT_VALUE_TOKENS = frozenset(
    """
    ACCEPTED_CANDIDATE_ID ACCEPTED_CANDIDATE_STATUS ACCEPTED_CANDIDATE_TITLE ACCEPTED_MODEL_TYPE
    ACCEPTED_MODEL_TYPE_LABEL ACCEPTED_PARAMETER_COUNT ACCURACY_DELTA ACCEPTED_ACCURACY_INTERVAL
    ACCEPTED_CALIBRATION_ECE ACCEPTED_MACRO_F1 BOOTSTRAP_ACCURACY_INTERVAL BOOTSTRAP_MACRO_F1_INTERVAL
    AUTONOMY_LEVEL BASELINE_ACCURACY BASELINE_ID BASELINE_MODEL_TYPE BASELINE_MODEL_TYPE_LABEL BENCHMARK_SCORE
    BEST_ACCURACY BUDGET_EXHAUSTED CANDIDATE_BUDGET CANDIDATE_COUNT DATASET_NAME DATASET_CLASS_COUNT
    DATASET_IMAGE_SHAPE DATASET_SHORT_NAME DATASET_SOURCE DISCLOSURE_TEXT EVALUATED_CANDIDATE_COUNT
    DEFERRED_CANDIDATE_COUNT IMAGE_SHAPE METRIC_DIRECTION METRIC_NAME ML_TASK_NAME MODEL_FAMILY_LABELS
    REVIEW_POLICY TEST_SIZE TRAIN_SIZE TRAIN_PER_CLASS_COUNT TEST_PER_CLASS_COUNT ROBUSTNESS_MIN_ACCURACY
    MCNEMAR_P_VALUE MEAN_CORRECT_CONFIDENCE MEAN_ERROR_CONFIDENCE LOW_MARGIN_COUNT PAIRED_NET_GAIN
    ACCEPTED_BRIER_SCORE ACCEPTED_BEST_EPOCH ACCEPTED_FINAL_LEARNING_RATE ACCEPTED_LOSS_REDUCTION
    ACCEPTED_NEGATIVE_LOG_LIKELIHOOD ACCEPTED_TRAIN_TEST_GAP ACCEPTED_TOP2_ACCURACY ACCEPTED_COHEN_KAPPA
    GRADIENT_CLIP_NORM LEARNING_RATE_DECAY SELECTIVE_HIGH_CONFIDENCE_COVERAGE
    SELECTIVE_HIGH_CONFIDENCE_ACCURACY TASK_IDENTIFIER TOP_CONFUSION_PAIR TRANSFORMER_CANDIDATE_ID
    TRANSFORMER_CANDIDATE_TITLE SECURITY_PROFILE_MODE SECURITY_NETWORK_POLICY SECURITY_INTEGRITY_ALGORITHM
    SECURITY_EXTERNAL_SIGNING SECURITY_FRAMEWORKS SECURITY_THREAT_COUNT SECURITY_CONTROL_COUNT SECURITY_ASSET_COUNT
    SECURITY_INVENTORY_INPUT_COUNT SECURITY_INVENTORY_ARTIFACT_COUNT SECURITY_ATTESTATION_STATUS
    SECURITY_ATTESTATION_CHECKED_COUNT SECURITY_ATTESTATION_MISSING_COUNT SECURITY_ATTESTATION_MISMATCH_COUNT
    SECURITY_CLAIM_SCOPE RESEARCH_OBJECT_ARTIFACT_COUNT RESEARCH_OBJECT_APPROVAL_STATE
    SCHEMA_MANIFEST_SCHEMA_COUNT ACCEPTED_TOP_RANK_FREQUENCY RANK_STABILITY_RUNNER_UP_ID
    PHASE_LEDGER_SETTLEMENT_PASS_COUNT FIGURE_QUALITY_FIGURE_COUNT FIGURE_QUALITY_VALID
    """.split()
)


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


def compute_ml_variables(payload: object) -> dict[str, str]:
    """Compute manuscript variables from an ML task payload or summary."""
    if not isinstance(payload, dict):
        payload = {}
    dataset = payload.get("dataset", {})
    if not isinstance(dataset, dict):
        dataset = {}
    accepted = payload.get("accepted_candidate", {})
    if not isinstance(accepted, dict):
        accepted = {}
    transformer_evaluated = bool(payload.get("transformer_evaluated", False))
    if not transformer_evaluated:
        candidates = payload.get("candidates", [])
        if isinstance(candidates, list):
            transformer_evaluated = any(
                isinstance(candidate, dict)
                and candidate.get("model_type") == "tiny_patch_transformer"
                and candidate.get("test_accuracy") is not None
                for candidate in candidates
            )
    return {
        "ML_TASK_SEED": _string_value(payload.get("seed", dataset.get("seed", "N/A"))),
        "CANDIDATE_COUNT": _string_value(payload.get("candidate_count", "N/A")),
        "EVALUATED_CANDIDATE_COUNT": _string_value(payload.get("evaluated_candidate_count", "N/A")),
        "ACCEPTED_CANDIDATE_ID": _string_value(payload.get("accepted_candidate_id", "N/A")),
        "BASELINE_ACCURACY": _percent_value(payload.get("baseline_accuracy")),
        "BEST_ACCURACY": _percent_value(payload.get("best_accuracy")),
        "ACCURACY_DELTA": _percent_value(payload.get("accuracy_delta")),
        "BUDGET_EXHAUSTED": str(bool(payload.get("budget_exhausted", False))).lower(),
        "BENCHMARK_SCORE": _string_value(payload.get("benchmark_score", "N/A")),
        "LLM_CALLS_USED": _string_value(payload.get("llm_calls_used", 0)),
        "COST_USD_USED": _currency_value(payload.get("cost_usd_used", 0.0)),
        "DATASET_NAME": _string_value(payload.get("dataset_name", dataset.get("dataset_name", "N/A"))),
        "TRAIN_SIZE": _string_value(payload.get("train_size", dataset.get("train_size", "N/A"))),
        "TEST_SIZE": _string_value(payload.get("test_size", dataset.get("test_size", "N/A"))),
        "ACCEPTED_MODEL_TYPE": _string_value(payload.get("accepted_model_type", accepted.get("model_type", "N/A"))),
        "ACCEPTED_PARAMETER_COUNT": _string_value(
            payload.get("parameter_count", accepted.get("parameter_count", "N/A"))
        ),
        "TRANSFORMER_EVALUATED": str(transformer_evaluated).lower(),
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


def save_figure_blocks(variables: dict[str, str], path: Path) -> Path:
    """Write generated figure blocks as a small JSON sidecar."""
    payload = {key: variables[key] for key in sorted(_FIGURE_BLOCK_KEYS) if key in variables}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _load_project_artifacts(project_root: Path, *, require_valid: bool) -> dict[str, Any]:
    output = project_root / "output"
    loop_path = output / "data" / "autoresearch_loop.json"
    loop_payload = _load_json_mapping(loop_path)
    if require_valid:
        metrics = _mapping(loop_payload.get("metrics"))
        if metrics.get("readiness_valid") is not True:
            raise ValueError("autoresearch_loop.json does not contain a valid final readiness state")
        readiness = _load_json_mapping(output / "reports" / "autoresearch_readiness.json")
        if readiness.get("valid") is not True:
            raise ValueError("autoresearch_readiness.json is missing or not valid")
        _validate_required_artifacts(project_root, loop_payload)
    return {
        "loop": loop_payload,
        "ml": _load_optional_json_mapping(output / "data" / "ml_task_results.json"),
        "candidate_ledger": _load_optional_json_mapping(output / "data" / "ml_candidate_ledger.json"),
        "review_decisions": _load_optional_json_mapping(output / "data" / "review_decisions.json"),
        "benchmark_scores": _load_optional_json_mapping(output / "data" / "benchmark_scores.json"),
        "artifact_manifest": _load_optional_json_mapping(output / "reports" / "artifact_manifest.json"),
        "figure_registry": _load_optional_json_mapping(output / "figures" / "figure_registry.json"),
        "classification_diagnostics": _load_optional_json_mapping(
            output / "data" / "ml_classification_diagnostics.json"
        ),
        "candidate_intervals": _load_optional_json_mapping(output / "data" / "ml_candidate_intervals.json"),
        "class_balance": _load_optional_json_mapping(output / "data" / "ml_class_balance.json"),
        "calibration_report": _load_optional_json_mapping(output / "data" / "ml_calibration_report.json"),
        "calibration_bin_intervals": _load_optional_json_mapping(output / "data" / "ml_calibration_bin_intervals.json"),
        "robustness_report": _load_optional_json_mapping(output / "data" / "ml_robustness_report.json"),
        "probability_diagnostics": _load_optional_json_mapping(output / "data" / "ml_probability_diagnostics.json"),
        "bootstrap_intervals": _load_optional_json_mapping(output / "data" / "ml_bootstrap_intervals.json"),
        "paired_comparison": _load_optional_json_mapping(output / "data" / "ml_paired_comparison.json"),
        "statistical_summary": _load_optional_json_mapping(output / "data" / "ml_statistical_summary.json"),
        "training_diagnostics": _load_optional_json_mapping(output / "data" / "ml_training_diagnostics.json"),
        "candidate_rank_stability": _load_optional_json_mapping(output / "data" / "ml_candidate_rank_stability.json"),
        "candidate_selection_audit": _load_optional_json_mapping(output / "data" / "ml_candidate_selection_audit.json"),
        "diagnostic_boundary": _load_optional_json_mapping(output / "data" / "ml_diagnostic_boundary.json"),
        "phase_ledger": _load_optional_json_mapping(output / "data" / "autoresearch_phase_ledger.json"),
        "figure_quality": _load_optional_json_mapping(output / "data" / "figure_quality_report.json"),
        "security_profile": _load_optional_json_mapping(output / "data" / "autoresearch_security_profile.json"),
        "security_threat_model": _load_optional_json_mapping(output / "data" / "autoresearch_threat_model.json"),
        "security_inventory": _load_optional_json_mapping(output / "data" / "autoresearch_supply_chain_inventory.json"),
        "security_attestation": _load_optional_json_mapping(
            output / "data" / "autoresearch_integrity_attestation.json"
        ),
        "schema_manifest": _load_optional_json_mapping(output / "data" / "autoresearch_schema_manifest.json"),
        "research_object_manifest": _load_optional_json_mapping(output / "data" / "research_object_manifest.json"),
    }


def _build_variables(project_root: Path, artifacts: dict[str, Any]) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    loop = _mapping(artifacts.get("loop"))
    ml = _mapping(artifacts.get("ml")) or _mapping(loop.get("ml_task"))
    candidate_ledger = _mapping(artifacts.get("candidate_ledger"))
    review_decisions = _mapping(artifacts.get("review_decisions"))
    benchmark_scores = _mapping(artifacts.get("benchmark_scores"))
    artifact_manifest = _mapping(artifacts.get("artifact_manifest"))
    registry = _mapping(artifacts.get("figure_registry"))
    classification = _mapping(artifacts.get("classification_diagnostics"))
    candidate_intervals = _mapping(artifacts.get("candidate_intervals"))
    class_balance = _mapping(artifacts.get("class_balance"))
    calibration = _mapping(artifacts.get("calibration_report"))
    calibration_intervals = _mapping(artifacts.get("calibration_bin_intervals"))
    robustness = _mapping(artifacts.get("robustness_report"))
    probability = _mapping(artifacts.get("probability_diagnostics"))
    bootstrap = _mapping(artifacts.get("bootstrap_intervals"))
    paired = _mapping(artifacts.get("paired_comparison"))
    statistical = _mapping(artifacts.get("statistical_summary"))
    training = _mapping(artifacts.get("training_diagnostics"))
    rank_stability = _mapping(artifacts.get("candidate_rank_stability"))
    candidate_selection = _mapping(artifacts.get("candidate_selection_audit"))
    diagnostic_boundary = _mapping(artifacts.get("diagnostic_boundary"))
    phase_ledger = _mapping(artifacts.get("phase_ledger"))
    figure_quality = _mapping(artifacts.get("figure_quality"))
    security_profile = _mapping(artifacts.get("security_profile"))
    security_threat_model = _mapping(artifacts.get("security_threat_model"))
    security_inventory = _mapping(artifacts.get("security_inventory"))
    security_attestation = _mapping(artifacts.get("security_attestation"))
    schema_manifest = _mapping(artifacts.get("schema_manifest"))
    research_object_manifest = _mapping(artifacts.get("research_object_manifest"))
    config = _mapping(loop.get("config"))
    ml_task_summary = _mapping(loop.get("ml_task"))
    task_config = _mapping(ml.get("task_config"))
    dataset = _mapping(ml.get("dataset"))
    baseline = _mapping(ml.get("baseline"))
    accepted = _mapping(ml.get("accepted_candidate"))
    candidates = _mapping_list(ml.get("candidates"))
    variables: dict[str, str] = {}
    provenance: dict[str, dict[str, str]] = {}

    def put(key: str, value: object, source: str, pointer: str) -> None:
        variables[key] = _string_value(value)
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
    put("TASK_IDENTIFIER", task_config.get("id", "N/A"), "output/data/ml_task_results.json", "/task_config/id")
    put("ML_TASK_NAME", ml.get("task_name", "N/A"), "output/data/ml_task_results.json", "/task_name")
    put(
        "DATASET_SHORT_NAME",
        _dataset_short_name(_string_value(dataset.get("dataset_name", "N/A"))),
        "output/data/ml_task_results.json",
        "/dataset/dataset_name",
    )
    put("DATASET_SOURCE", dataset.get("source", "N/A"), "output/data/ml_task_results.json", "/dataset/source")
    put(
        "DATASET_PATH",
        task_config.get("dataset_path", "N/A"),
        "output/data/ml_task_results.json",
        "/task_config/dataset_path",
    )
    put(
        "DATASET_PROVENANCE_PATH",
        task_config.get("provenance_path", "N/A"),
        "output/data/ml_task_results.json",
        "/task_config/provenance_path",
    )
    put(
        "DATASET_CLASS_COUNT",
        dataset.get("class_count", "N/A"),
        "output/data/ml_task_results.json",
        "/dataset/class_count",
    )
    put(
        "IMAGE_SHAPE",
        _image_shape(dataset.get("image_shape")),
        "output/data/ml_task_results.json",
        "/dataset/image_shape",
    )
    put(
        "METRIC_NAME",
        _mapping(ml.get("objective")).get("metric", task_config.get("metric_name", "N/A")),
        "output/data/ml_task_results.json",
        "/objective/metric",
    )
    put(
        "METRIC_DIRECTION",
        _mapping(ml.get("objective")).get("direction", task_config.get("metric_direction", "N/A")),
        "output/data/ml_task_results.json",
        "/objective/direction",
    )
    put(
        "CANDIDATE_BUDGET",
        task_config.get("max_candidates", ml_task_summary.get("evaluated_candidate_count", "N/A")),
        "output/data/ml_task_results.json",
        "/task_config/max_candidates",
    )
    put(
        "DEFERRED_CANDIDATE_COUNT",
        _status_counts(candidates).get("deferred", 0),
        "output/data/ml_task_results.json",
        "/candidates",
    )
    put("CANDIDATE_STATUS_SUMMARY", _status_summary(candidates), "output/data/ml_task_results.json", "/candidates")
    put(
        "MODEL_FAMILY_LABELS",
        _model_family_labels(baseline, candidates),
        "output/data/ml_task_results.json",
        "/candidates",
    )
    put("BASELINE_ID", baseline.get("identifier", "N/A"), "output/data/ml_task_results.json", "/baseline/identifier")
    put(
        "BASELINE_MODEL_TYPE",
        baseline.get("model_type", "N/A"),
        "output/data/ml_task_results.json",
        "/baseline/model_type",
    )
    put(
        "BASELINE_MODEL_TYPE_LABEL",
        _model_type_label(baseline.get("model_type", "N/A")),
        "output/data/ml_task_results.json",
        "/baseline/model_type",
    )
    put(
        "ACCEPTED_CANDIDATE_TITLE",
        accepted.get("title", "N/A"),
        "output/data/ml_task_results.json",
        "/accepted_candidate/title",
    )
    put(
        "ACCEPTED_CANDIDATE_STATUS",
        accepted.get("status", "N/A"),
        "output/data/ml_task_results.json",
        "/accepted_candidate/status",
    )
    put(
        "ACCEPTED_MODEL_TYPE_LABEL",
        _model_type_label(accepted.get("model_type", "N/A")),
        "output/data/ml_task_results.json",
        "/accepted_candidate/model_type",
    )
    transformer = _first_model_candidate(candidates, "tiny_patch_transformer")
    put(
        "TRANSFORMER_CANDIDATE_ID",
        transformer.get("identifier", "N/A"),
        "output/data/ml_task_results.json",
        "/candidates",
    )
    put(
        "TRANSFORMER_CANDIDATE_TITLE",
        transformer.get("title", "N/A"),
        "output/data/ml_task_results.json",
        "/candidates",
    )
    put(
        "ACCEPTED_MACRO_F1",
        _percent_value(classification.get("macro_f1")),
        "output/data/ml_classification_diagnostics.json",
        "/macro_f1",
    )
    put(
        "ACCEPTED_ACCURACY_INTERVAL",
        _accuracy_interval(classification),
        "output/data/ml_classification_diagnostics.json",
        "/accuracy_ci_low",
    )
    put(
        "ACCEPTED_CALIBRATION_ECE",
        _percent_value(calibration.get("expected_calibration_error")),
        "output/data/ml_calibration_report.json",
        "/expected_calibration_error",
    )
    put(
        "TOP_CONFUSION_PAIR",
        _top_confusion_pair_label(classification),
        "output/data/ml_classification_diagnostics.json",
        "/top_confusion_pairs/0",
    )
    put(
        "HIGH_CONFIDENCE_ERROR_COUNT",
        calibration.get("high_confidence_error_count", "N/A"),
        "output/data/ml_calibration_report.json",
        "/high_confidence_error_count",
    )
    put(
        "TRAIN_PER_CLASS_COUNT",
        _per_class_count(class_balance, "train"),
        "output/data/ml_class_balance.json",
        "/rows",
    )
    put(
        "TEST_PER_CLASS_COUNT",
        _per_class_count(class_balance, "test"),
        "output/data/ml_class_balance.json",
        "/rows",
    )
    put(
        "ROBUSTNESS_MIN_ACCURACY",
        _percent_value(robustness.get("accepted_min_accuracy")),
        "output/data/ml_robustness_report.json",
        "/accepted_min_accuracy",
    )
    put(
        "MEAN_CORRECT_CONFIDENCE",
        _percent_value(probability.get("mean_correct_confidence")),
        "output/data/ml_probability_diagnostics.json",
        "/mean_correct_confidence",
    )
    put(
        "MEAN_ERROR_CONFIDENCE",
        _percent_value(probability.get("mean_error_confidence")),
        "output/data/ml_probability_diagnostics.json",
        "/mean_error_confidence",
    )
    put(
        "LOW_MARGIN_COUNT",
        probability.get("low_margin_count", "N/A"),
        "output/data/ml_probability_diagnostics.json",
        "/low_margin_count",
    )
    put(
        "BOOTSTRAP_ACCURACY_INTERVAL",
        _bootstrap_interval(bootstrap, "accuracy"),
        "output/data/ml_bootstrap_intervals.json",
        "/intervals",
    )
    put(
        "BOOTSTRAP_MACRO_F1_INTERVAL",
        _bootstrap_interval(bootstrap, "macro_f1"),
        "output/data/ml_bootstrap_intervals.json",
        "/intervals",
    )
    put(
        "PAIRED_NET_GAIN",
        _percent_value(paired.get("net_accuracy_gain")),
        "output/data/ml_paired_comparison.json",
        "/net_accuracy_gain",
    )
    put(
        "MCNEMAR_P_VALUE",
        _p_value(paired.get("exact_mcnemar_p")),
        "output/data/ml_paired_comparison.json",
        "/exact_mcnemar_p",
    )
    put(
        "ACCEPTED_BRIER_SCORE",
        _decimal_value(statistical.get("brier_score")),
        "output/data/ml_statistical_summary.json",
        "/brier_score",
    )
    put(
        "ACCEPTED_NEGATIVE_LOG_LIKELIHOOD",
        _decimal_value(statistical.get("negative_log_likelihood")),
        "output/data/ml_statistical_summary.json",
        "/negative_log_likelihood",
    )
    put(
        "ACCEPTED_TOP2_ACCURACY",
        _percent_value(statistical.get("top2_accuracy")),
        "output/data/ml_statistical_summary.json",
        "/top2_accuracy",
    )
    put(
        "ACCEPTED_COHEN_KAPPA",
        _decimal_value(statistical.get("cohen_kappa")),
        "output/data/ml_statistical_summary.json",
        "/cohen_kappa",
    )
    put(
        "SELECTIVE_HIGH_CONFIDENCE_COVERAGE",
        _percent_value(_last_coverage_value(statistical, "coverage")),
        "output/data/ml_statistical_summary.json",
        "/coverage_curve",
    )
    put(
        "SELECTIVE_HIGH_CONFIDENCE_ACCURACY",
        _percent_value(_last_coverage_value(statistical, "selective_accuracy")),
        "output/data/ml_statistical_summary.json",
        "/coverage_curve",
    )
    training_policy = _mapping(training.get("training_policy"))
    accepted_training = _mapping(training.get("accepted"))
    put(
        "LEARNING_RATE_DECAY",
        _string_value(training_policy.get("learning_rate_decay", "N/A")),
        "output/data/ml_training_diagnostics.json",
        "/training_policy/learning_rate_decay",
    )
    put(
        "GRADIENT_CLIP_NORM",
        _string_value(training_policy.get("gradient_clip_norm", "N/A")),
        "output/data/ml_training_diagnostics.json",
        "/training_policy/gradient_clip_norm",
    )
    put(
        "ACCEPTED_BEST_EPOCH",
        accepted_training.get("best_epoch", "N/A"),
        "output/data/ml_training_diagnostics.json",
        "/accepted/best_epoch",
    )
    put(
        "ACCEPTED_FINAL_LEARNING_RATE",
        _decimal_value(accepted_training.get("final_learning_rate")),
        "output/data/ml_training_diagnostics.json",
        "/accepted/final_learning_rate",
    )
    put(
        "ACCEPTED_LOSS_REDUCTION",
        _decimal_value(accepted_training.get("loss_reduction")),
        "output/data/ml_training_diagnostics.json",
        "/accepted/loss_reduction",
    )
    put(
        "ACCEPTED_TRAIN_TEST_GAP",
        _percent_value(accepted_training.get("train_test_accuracy_gap")),
        "output/data/ml_training_diagnostics.json",
        "/accepted/train_test_accuracy_gap",
    )
    put(
        "ACCEPTED_TOP_RANK_FREQUENCY",
        _percent_value(rank_stability.get("accepted_top_rank_frequency")),
        "output/data/ml_candidate_rank_stability.json",
        "/accepted_top_rank_frequency",
    )
    put(
        "RANK_STABILITY_RUNNER_UP_ID",
        rank_stability.get("runner_up_id", "N/A"),
        "output/data/ml_candidate_rank_stability.json",
        "/runner_up_id",
    )
    put(
        "PHASE_LEDGER_SETTLEMENT_PASS_COUNT",
        phase_ledger.get("settlement_pass_count", "N/A"),
        "output/data/autoresearch_phase_ledger.json",
        "/settlement_pass_count",
    )
    put(
        "FIGURE_QUALITY_FIGURE_COUNT",
        figure_quality.get("figure_count", "N/A"),
        "output/data/figure_quality_report.json",
        "/figure_count",
    )
    put(
        "FIGURE_QUALITY_VALID",
        str(bool(figure_quality.get("valid", False))).lower(),
        "output/data/figure_quality_report.json",
        "/valid",
    )
    put(
        "BENCHMARK_TASK_IDS",
        _benchmark_task_ids(config),
        "output/data/autoresearch_loop.json",
        "/config/benchmark_tasks",
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
    _put_figure_blocks(project_root, variables, provenance, registry)
    _put_tables(
        variables,
        provenance,
        registry,
        candidate_ledger,
        review_decisions,
        benchmark_scores,
        artifact_manifest,
        classification,
        candidate_intervals,
        class_balance,
        calibration,
        calibration_intervals,
        robustness,
        probability,
        bootstrap,
        paired,
        statistical,
        training,
        rank_stability,
        candidate_selection,
        diagnostic_boundary,
        phase_ledger,
        figure_quality,
        security_profile,
        security_threat_model,
        security_inventory,
        security_attestation,
    )
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
    summary = _mapping(threat_model.get("summary"))
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
        len(_mapping_list(inventory.get("inputs"))),
        "output/data/autoresearch_supply_chain_inventory.json",
        "/inputs",
    )
    put(
        "SECURITY_INVENTORY_ARTIFACT_COUNT",
        len(_mapping_list(inventory.get("generated_artifacts"))),
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
    approval_state = _mapping(research_object_manifest.get("approval_state"))
    put(
        "SCHEMA_MANIFEST_SCHEMA_COUNT",
        len(_mapping_list(schema_manifest.get("schema_artifacts"))),
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


def _put_figure_blocks(
    project_root: Path,
    variables: dict[str, str],
    provenance: dict[str, dict[str, str]],
    registry: dict[str, Any],
) -> None:
    labels = {
        "FIGURE_BLOCK_STAGE_MATRIX": "fig:autoresearch_stage_matrix",
        "FIGURE_BLOCK_CANDIDATE_SCORES": "fig:ml_candidate_scores",
        "FIGURE_BLOCK_CONFUSION_MATRIX": "fig:ml_confusion_matrix",
        "FIGURE_BLOCK_PER_CLASS_ACCURACY": "fig:ml_per_class_accuracy",
        "FIGURE_BLOCK_LEARNING_CURVES": "fig:ml_learning_curves",
        "FIGURE_BLOCK_COMPLEXITY_ACCURACY": "fig:ml_complexity_accuracy",
        "FIGURE_BLOCK_ERROR_EXAMPLES": "fig:mnist_error_examples",
        "FIGURE_BLOCK_CALIBRATION_RELIABILITY": "fig:ml_calibration_reliability",
        "FIGURE_BLOCK_CLASSIFICATION_METRICS": "fig:ml_classification_metrics_heatmap",
        "FIGURE_BLOCK_CONFUSION_PAIRS": "fig:ml_confusion_pairs",
        "FIGURE_BLOCK_GENERALIZATION_GAP": "fig:ml_generalization_gap",
        "FIGURE_BLOCK_ROBUSTNESS_MATRIX": "fig:ml_robustness_matrix",
        "FIGURE_BLOCK_PROBABILITY_MARGIN": "fig:ml_probability_margin_distribution",
        "FIGURE_BLOCK_BOOTSTRAP_INTERVALS": "fig:ml_bootstrap_intervals",
        "FIGURE_BLOCK_PAIRED_CORRECTNESS": "fig:ml_paired_correctness",
        "FIGURE_BLOCK_SELECTIVE_ACCURACY": "fig:ml_selective_accuracy",
        "FIGURE_BLOCK_PROBABILITY_QUALITY": "fig:ml_probability_quality",
        "FIGURE_BLOCK_TRAINING_DYNAMICS": "fig:ml_training_dynamics",
        "FIGURE_BLOCK_CANDIDATE_RANK_STABILITY": "fig:ml_candidate_rank_stability",
        "FIGURE_BLOCK_CANDIDATE_LIFECYCLE": "fig:autoresearch_candidate_lifecycle",
        "FIGURE_BLOCK_DATASET_CLASS_BALANCE": "fig:mnist_class_balance",
        "FIGURE_BLOCK_DATASET_CONTACT_SHEET": "fig:mnist_subset_contact_sheet",
        "FIGURE_BLOCK_CLOSURE_FLOW": "fig:autoresearch_closure_flow",
        "FIGURE_BLOCK_SECURITY_CONTROL_MATRIX": "fig:autoresearch_security_control_matrix",
        "FIGURE_BLOCK_INTEGRITY_CHAIN": "fig:autoresearch_integrity_chain",
    }
    for token, label in labels.items():
        block = _figure_block(project_root, registry, label)
        variables[token] = block
        provenance[token] = {"source": "output/figures/figure_registry.json", "pointer": f"/{label}"}
    reference_tokens = {
        "FIGURE_REF_STAGE_MATRIX": "fig:autoresearch_stage_matrix",
        "FIGURE_REF_CANDIDATE_SCORES": "fig:ml_candidate_scores",
        "FIGURE_REF_CONFUSION_MATRIX": "fig:ml_confusion_matrix",
        "FIGURE_REF_PER_CLASS_ACCURACY": "fig:ml_per_class_accuracy",
        "FIGURE_REF_LEARNING_CURVES": "fig:ml_learning_curves",
        "FIGURE_REF_COMPLEXITY_ACCURACY": "fig:ml_complexity_accuracy",
        "FIGURE_REF_ERROR_EXAMPLES": "fig:mnist_error_examples",
        "FIGURE_REF_CALIBRATION_RELIABILITY": "fig:ml_calibration_reliability",
        "FIGURE_REF_CLASSIFICATION_METRICS": "fig:ml_classification_metrics_heatmap",
        "FIGURE_REF_CONFUSION_PAIRS": "fig:ml_confusion_pairs",
        "FIGURE_REF_GENERALIZATION_GAP": "fig:ml_generalization_gap",
        "FIGURE_REF_ROBUSTNESS_MATRIX": "fig:ml_robustness_matrix",
        "FIGURE_REF_PROBABILITY_MARGIN": "fig:ml_probability_margin_distribution",
        "FIGURE_REF_BOOTSTRAP_INTERVALS": "fig:ml_bootstrap_intervals",
        "FIGURE_REF_PAIRED_CORRECTNESS": "fig:ml_paired_correctness",
        "FIGURE_REF_SELECTIVE_ACCURACY": "fig:ml_selective_accuracy",
        "FIGURE_REF_PROBABILITY_QUALITY": "fig:ml_probability_quality",
        "FIGURE_REF_TRAINING_DYNAMICS": "fig:ml_training_dynamics",
        "FIGURE_REF_CANDIDATE_RANK_STABILITY": "fig:ml_candidate_rank_stability",
        "FIGURE_REF_CANDIDATE_LIFECYCLE": "fig:autoresearch_candidate_lifecycle",
        "FIGURE_REF_DATASET_CLASS_BALANCE": "fig:mnist_class_balance",
        "FIGURE_REF_DATASET_CONTACT_SHEET": "fig:mnist_subset_contact_sheet",
        "FIGURE_REF_CLOSURE_FLOW": "fig:autoresearch_closure_flow",
        "FIGURE_REF_SECURITY_CONTROL_MATRIX": "fig:autoresearch_security_control_matrix",
        "FIGURE_REF_INTEGRITY_CHAIN": "fig:autoresearch_integrity_chain",
    }
    for token, label in reference_tokens.items():
        variables[token] = f"@{label}"
        provenance[token] = {"source": "output/figures/figure_registry.json", "pointer": f"/{label}/label"}


def _put_tables(
    variables: dict[str, str],
    provenance: dict[str, dict[str, str]],
    registry: dict[str, Any],
    candidate_ledger: dict[str, Any],
    review_decisions: dict[str, Any],
    benchmark_scores: dict[str, Any],
    artifact_manifest: dict[str, Any],
    classification: dict[str, Any],
    candidate_intervals: dict[str, Any],
    class_balance: dict[str, Any],
    calibration: dict[str, Any],
    calibration_intervals: dict[str, Any],
    robustness: dict[str, Any],
    probability: dict[str, Any],
    bootstrap: dict[str, Any],
    paired: dict[str, Any],
    statistical: dict[str, Any],
    training: dict[str, Any],
    rank_stability: dict[str, Any],
    candidate_selection: dict[str, Any],
    diagnostic_boundary: dict[str, Any],
    phase_ledger: dict[str, Any],
    figure_quality: dict[str, Any],
    security_profile: dict[str, Any],
    security_threat_model: dict[str, Any],
    security_inventory: dict[str, Any],
    security_attestation: dict[str, Any],
) -> None:
    table_specs = build_table_specs(
        registry,
        candidate_ledger,
        review_decisions,
        benchmark_scores,
        artifact_manifest,
        classification,
        candidate_intervals,
        class_balance,
        calibration,
        calibration_intervals,
        robustness,
        probability,
        bootstrap,
        paired,
        statistical,
        training,
        rank_stability,
        candidate_selection,
        diagnostic_boundary,
        phase_ledger,
        figure_quality,
        security_profile,
        security_threat_model,
        security_inventory,
        security_attestation,
    )
    for token, (value, source, pointer) in table_specs.items():
        variables[token] = value
        provenance[token] = {"source": source, "pointer": pointer}


def _figure_block(project_root: Path, registry: dict[str, Any], label: str) -> str:
    record = _mapping(registry.get(label))
    filename = _string_value(record.get("filename", ""))
    caption = _string_value(record.get("caption", ""))
    width = _string_value(record.get("width", "0.8\\textwidth"))
    if not filename or not caption:
        raise ValueError(f"figure registry record is incomplete for {label}")
    figure_path = project_root / "output" / "figures" / filename
    if not figure_path.exists():
        raise ValueError(f"registered figure is missing for {label}: {figure_path}")
    return f'![{caption}](../figures/{filename}){{#{label} width="{width}"}}'


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
    config = _mapping(loop_payload.get("config"))
    required = config.get("required_artifacts", [])
    if not isinstance(required, list):
        raise ValueError("loop payload required_artifacts must be a list")
    missing = [path for path in required if isinstance(path, str) and not (project_root / path).exists()]
    if missing:
        raise ValueError("missing required AutoResearch artifacts: " + ", ".join(sorted(missing)))


def _load_json_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"required JSON artifact is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must contain a mapping: {path}")
    return payload


def _load_optional_json_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load_json_mapping(path)


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _string_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _percent_value(value: object) -> str:
    if not isinstance(value, int | float):
        return "N/A"
    return f"{float(value) * 100:.1f}%"


def _currency_value(value: object) -> str:
    if not isinstance(value, int | float):
        return "N/A"
    return f"{float(value):.2f}"


def _decimal_value(value: object) -> str:
    if not isinstance(value, int | float):
        return "N/A"
    return f"{float(value):.3f}"


def _accuracy_interval(classification: dict[str, Any]) -> str:
    low = classification.get("accuracy_ci_low")
    high = classification.get("accuracy_ci_high")
    if not isinstance(low, int | float) or not isinstance(high, int | float):
        return "N/A"
    return f"{_percent_value(low)} to {_percent_value(high)}"


def _top_confusion_pair_label(classification: dict[str, Any]) -> str:
    pairs = _mapping_list(classification.get("top_confusion_pairs"))
    if not pairs:
        return "none"
    first = pairs[0]
    return (
        f"{_string_value(first.get('true_label', 'N/A'))} -> "
        f"{_string_value(first.get('predicted_label', 'N/A'))} "
        f"({_string_value(first.get('count', 'N/A'))})"
    )


def _bootstrap_interval(bootstrap: dict[str, Any], metric: str) -> str:
    for row in _mapping_list(bootstrap.get("intervals")):
        if row.get("metric") == metric:
            return f"{_percent_value(row.get('ci_low'))} to {_percent_value(row.get('ci_high'))}"
    return "N/A"


def _p_value(value: object) -> str:
    if not isinstance(value, int | float):
        return "N/A"
    return f"{float(value):.3f}"


def _last_coverage_value(statistical: dict[str, Any], key: str) -> float | None:
    rows = _mapping_list(statistical.get("coverage_curve"))
    if not rows:
        return None
    value = rows[-1].get(key)
    return float(value) if isinstance(value, int | float) else None


def _dataset_short_name(dataset_name: str) -> str:
    return dataset_name.split(maxsplit=1)[0] if dataset_name and dataset_name != "N/A" else dataset_name


def _image_shape(value: object) -> str:
    if isinstance(value, list | tuple) and len(value) == 2:
        return f"{value[0]} by {value[1]}"
    return "N/A"


def _model_type_label(value: object) -> str:
    labels = {
        "mlp": "MLP",
        "nearest_centroid": "nearest-centroid",
        "softmax_regression": "softmax regression",
        "tiny_patch_transformer": "tiny patch-attention",
    }
    return labels.get(_string_value(value), _string_value(value).replace("_", " "))


def _candidate_display_label(value: object) -> str:
    text = _string_value(value)
    if text == "nearest_centroid_baseline":
        return "baseline"
    return text.removeprefix("exp-").replace("-", " ")


def _metric_label(value: object) -> str:
    labels = {
        "accuracy": "accuracy",
        "macro_f1": "macro F1",
    }
    return labels.get(_string_value(value), _string_value(value).replace("_", " "))


def _status_counts(candidates: list[dict[str, Any]]) -> Counter[str]:
    return Counter(_string_value(candidate.get("status", "unknown")) for candidate in candidates)


def _status_summary(candidates: list[dict[str, Any]]) -> str:
    counts = _status_counts(candidates)
    return ", ".join(f"{status}: {count}" for status, count in sorted(counts.items()))


def _model_family_labels(baseline: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    model_types = {_model_type_label(baseline.get("model_type", "N/A"))}
    model_types.update(_model_type_label(candidate.get("model_type", "N/A")) for candidate in candidates)
    return ", ".join(sorted(model_types))


def _first_model_candidate(candidates: list[dict[str, Any]], model_type: str) -> dict[str, Any]:
    for candidate in candidates:
        if candidate.get("model_type") == model_type:
            return candidate
    return {}


def _benchmark_task_ids(config: dict[str, Any]) -> str:
    return ", ".join(_string_value(row.get("id", "N/A")) for row in _mapping_list(config.get("benchmark_tasks")))


def _artifact_role(path: str) -> str:
    if path.endswith(".png"):
        return "Generated figure"
    if "manuscript" in path:
        return "Manuscript hydration"
    if "benchmark" in path:
        return "Benchmark grading"
    if "review" in path:
        return "Review packet"
    if "security" in path or "threat_model" in path or "attestation" in path or "inventory" in path:
        return "Security evidence"
    if "ledger" in path:
        return "Run or candidate ledger"
    if "readiness" in path:
        return "Readiness validation"
    if "evidence" in path:
        return "Evidence registry"
    return "Loop artifact"


def _artifact_markdown_link(path: str) -> str:
    label = Path(path).name if path not in {"", "N/A"} else "N/A"
    if path.startswith("output/"):
        target = "../" + path.removeprefix("output/")
    elif path.startswith("data/"):
        target = "../../" + path
    else:
        target = path
    return f"[{label}]({target})"


def _short_scope(value: str, *, limit: int = 92) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _per_class_count(class_balance: dict[str, Any], split: str) -> str:
    counts = [int(row.get("count", 0)) for row in _mapping_list(class_balance.get("rows")) if row.get("split") == split]
    if not counts:
        return "N/A"
    unique = sorted(set(counts))
    return str(unique[0]) if len(unique) == 1 else ", ".join(str(value) for value in unique)


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _strict_value_pairs(variables: dict[str, str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for token, value in variables.items():
        if not value or value in {"N/A", "true", "false", "passed", "requires review"}:
            continue
        strict_token = token in _STRICT_VALUE_TOKENS or token.endswith("_PATH") or token.endswith("_ACCURACY")
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
