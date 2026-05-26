"""Render-time manuscript variables for the AutoResearch exemplar."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

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
        "FIGURE_BLOCK_CANDIDATE_LIFECYCLE",
        "FIGURE_BLOCK_DATASET_CLASS_BALANCE",
        "FIGURE_BLOCK_DATASET_CONTACT_SHEET",
        "FIGURE_BLOCK_CLOSURE_FLOW",
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
    TRANSFORMER_CANDIDATE_TITLE
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
        "robustness_report": _load_optional_json_mapping(output / "data" / "ml_robustness_report.json"),
        "probability_diagnostics": _load_optional_json_mapping(output / "data" / "ml_probability_diagnostics.json"),
        "bootstrap_intervals": _load_optional_json_mapping(output / "data" / "ml_bootstrap_intervals.json"),
        "paired_comparison": _load_optional_json_mapping(output / "data" / "ml_paired_comparison.json"),
        "statistical_summary": _load_optional_json_mapping(output / "data" / "ml_statistical_summary.json"),
        "training_diagnostics": _load_optional_json_mapping(output / "data" / "ml_training_diagnostics.json"),
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
    robustness = _mapping(artifacts.get("robustness_report"))
    probability = _mapping(artifacts.get("probability_diagnostics"))
    bootstrap = _mapping(artifacts.get("bootstrap_intervals"))
    paired = _mapping(artifacts.get("paired_comparison"))
    statistical = _mapping(artifacts.get("statistical_summary"))
    training = _mapping(artifacts.get("training_diagnostics"))
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
        "BENCHMARK_TASK_IDS",
        _benchmark_task_ids(config),
        "output/data/autoresearch_loop.json",
        "/config/benchmark_tasks",
    )
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
        robustness,
        probability,
        bootstrap,
        paired,
        statistical,
        training,
    )
    put(
        "MANUSCRIPT_VARIABLE_COUNT", len(variables) + 1, "output/data/manuscript_variable_provenance.json", "/variables"
    )
    variables["VARIABLE_PROVENANCE_TABLE"] = _variable_provenance_table(provenance)
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
        "ML_ROBUSTNESS_REPORT_PATH": "output/data/ml_robustness_report.json",
        "ML_PROBABILITY_DIAGNOSTICS_PATH": "output/data/ml_probability_diagnostics.json",
        "ML_BOOTSTRAP_INTERVALS_PATH": "output/data/ml_bootstrap_intervals.json",
        "ML_PAIRED_COMPARISON_PATH": "output/data/ml_paired_comparison.json",
        "ML_STATISTICAL_SUMMARY_PATH": "output/data/ml_statistical_summary.json",
        "ML_TRAINING_DIAGNOSTICS_PATH": "output/data/ml_training_diagnostics.json",
        "ML_RESULTS_PATH": "output/data/ml_task_results.json",
        "READINESS_REPORT_PATH": "output/reports/autoresearch_readiness.json",
        "RESEARCH_PROGRAM_PATH": "output/data/research_program.json",
        "REVIEW_DECISIONS_PATH": "output/data/review_decisions.json",
        "RUN_LEDGER_PATH": "output/data/run_ledger.json",
        "VARIABLE_PROVENANCE_PATH": "output/data/manuscript_variable_provenance.json",
    }
    for token, path in path_tokens.items():
        put(token, path, "output/data/autoresearch_loop.json", "/output_paths")


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
        "FIGURE_BLOCK_CANDIDATE_LIFECYCLE": "fig:autoresearch_candidate_lifecycle",
        "FIGURE_BLOCK_DATASET_CLASS_BALANCE": "fig:mnist_class_balance",
        "FIGURE_BLOCK_DATASET_CONTACT_SHEET": "fig:mnist_subset_contact_sheet",
        "FIGURE_BLOCK_CLOSURE_FLOW": "fig:autoresearch_closure_flow",
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
        "FIGURE_REF_CANDIDATE_LIFECYCLE": "fig:autoresearch_candidate_lifecycle",
        "FIGURE_REF_DATASET_CLASS_BALANCE": "fig:mnist_class_balance",
        "FIGURE_REF_DATASET_CONTACT_SHEET": "fig:mnist_subset_contact_sheet",
        "FIGURE_REF_CLOSURE_FLOW": "fig:autoresearch_closure_flow",
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
    robustness: dict[str, Any],
    probability: dict[str, Any],
    bootstrap: dict[str, Any],
    paired: dict[str, Any],
    statistical: dict[str, Any],
    training: dict[str, Any],
) -> None:
    table_specs = {
        "FIGURE_METHOD_TABLE": (
            _figure_method_table(registry),
            "output/figures/figure_registry.json",
            "/",
        ),
        "ML_CANDIDATE_LEDGER_TABLE": (
            _candidate_ledger_table(candidate_ledger),
            "output/data/ml_candidate_ledger.json",
            "/candidates",
        ),
        "AUTORESEARCH_ARTIFACT_TABLE": (
            _artifact_manifest_table(artifact_manifest),
            "output/reports/artifact_manifest.json",
            "/entries",
        ),
        "REVIEW_GATE_TABLE": (
            _review_gate_table(review_decisions),
            "output/data/review_decisions.json",
            "/decisions",
        ),
        "BENCHMARK_SCORE_TABLE": (
            _benchmark_score_table(benchmark_scores),
            "output/data/benchmark_scores.json",
            "/tasks",
        ),
        "CLASSIFICATION_DIAGNOSTICS_TABLE": (
            _classification_diagnostics_table(classification),
            "output/data/ml_classification_diagnostics.json",
            "/per_class",
        ),
        "CANDIDATE_INTERVAL_TABLE": (
            _candidate_interval_table(candidate_intervals),
            "output/data/ml_candidate_intervals.json",
            "/rows",
        ),
        "CLASS_BALANCE_TABLE": (
            _class_balance_table(class_balance),
            "output/data/ml_class_balance.json",
            "/rows",
        ),
        "CALIBRATION_BIN_TABLE": (
            _calibration_bin_table(calibration),
            "output/data/ml_calibration_report.json",
            "/bins",
        ),
        "CONFUSION_PAIR_TABLE": (
            _confusion_pair_table(classification),
            "output/data/ml_classification_diagnostics.json",
            "/top_confusion_pairs",
        ),
        "ROBUSTNESS_SCORE_TABLE": (
            _robustness_score_table(robustness),
            "output/data/ml_robustness_report.json",
            "/rows",
        ),
        "PROBABILITY_DIAGNOSTICS_TABLE": (
            _probability_diagnostics_table(probability),
            "output/data/ml_probability_diagnostics.json",
            "/",
        ),
        "BOOTSTRAP_INTERVAL_TABLE": (
            _bootstrap_interval_table(bootstrap),
            "output/data/ml_bootstrap_intervals.json",
            "/intervals",
        ),
        "PAIRED_COMPARISON_TABLE": (
            _paired_comparison_table(paired),
            "output/data/ml_paired_comparison.json",
            "/",
        ),
        "STATISTICAL_SUMMARY_TABLE": (
            _statistical_summary_table(statistical),
            "output/data/ml_statistical_summary.json",
            "/",
        ),
        "SELECTIVE_ACCURACY_TABLE": (
            _selective_accuracy_table(statistical),
            "output/data/ml_statistical_summary.json",
            "/coverage_curve",
        ),
        "PROBABILITY_QUALITY_TABLE": (
            _probability_quality_table(statistical),
            "output/data/ml_statistical_summary.json",
            "/candidate_probability_quality",
        ),
        "TRAINING_DIAGNOSTICS_TABLE": (
            _training_diagnostics_table(training),
            "output/data/ml_training_diagnostics.json",
            "/rows",
        ),
    }
    for token, (value, source, pointer) in table_specs.items():
        variables[token] = value
        provenance[token] = {"source": source, "pointer": pointer}


def _candidate_ledger_table(candidate_ledger: dict[str, Any]) -> str:
    baseline = _mapping(candidate_ledger.get("baseline"))
    candidates = _mapping_list(candidate_ledger.get("candidates"))
    rows = [
        (
            _candidate_display_label(baseline.get("identifier", "baseline")),
            _model_type_label(baseline.get("model_type", "N/A")),
            "baseline",
            _percent_value(baseline.get("test_accuracy")),
            _string_value(baseline.get("parameter_count", "N/A")),
        )
    ]
    for candidate in candidates:
        rows.append(
            (
                _candidate_display_label(candidate.get("identifier", "N/A")),
                _model_type_label(candidate.get("model_type", "N/A")),
                _string_value(candidate.get("status", "N/A")),
                _percent_value(candidate.get("test_accuracy")),
                _string_value(candidate.get("parameter_count", "N/A")),
            )
        )
    return _markdown_table(
        ("Candidate", "Model", "Status", "Test accuracy", "Parameters"),
        rows,
        "Candidate lifecycle ledger from `output/data/ml_candidate_ledger.json`. {#tbl:ml-candidate-ledger}",
    )


def _figure_method_table(registry: dict[str, Any]) -> str:
    rows = []
    for label, record in sorted(registry.items()):
        if not isinstance(record, dict):
            continue
        metadata = _mapping(record.get("metadata"))
        rows.append(
            (
                f"@{_string_value(label)}",
                _artifact_markdown_link(_string_value(metadata.get("source", "N/A"))),
                _short_scope(_string_value(metadata.get("method", "N/A")), limit=84),
                _short_scope(_string_value(metadata.get("claim_boundary", "N/A"))),
            )
        )
    return _pdf_small_table(
        ("Figure", "Source", "Method", "Scope"),
        rows,
        "Registry-backed figure methods from [`figure_registry.json`](../figures/figure_registry.json); full validation hooks, alt text, and claim boundaries remain in the registry. {#tbl:figure-methods}",
    )


def _candidate_interval_table(candidate_intervals: dict[str, Any]) -> str:
    rows = [
        (
            _candidate_display_label(row.get("candidate_id", "N/A")),
            _string_value(row.get("status", "N/A")),
            f"{_string_value(row.get('successes', 'N/A'))}/{_string_value(row.get('test_size', 'N/A'))}",
            _percent_value(row.get("accuracy")),
            f"{_percent_value(row.get('ci_low'))} to {_percent_value(row.get('ci_high'))}",
        )
        for row in _mapping_list(candidate_intervals.get("rows"))
    ]
    return _markdown_table(
        ("Candidate", "Status", "Correct/test", "Accuracy", "Wilson 95% interval"),
        rows,
        "Candidate accuracy intervals from `output/data/ml_candidate_intervals.json`; intervals describe the fixed local test split. {#tbl:candidate-intervals}",
    )


def _class_balance_table(class_balance: dict[str, Any]) -> str:
    rows = [
        (
            _string_value(row.get("split", "N/A")),
            _string_value(row.get("class_label", "N/A")),
            _string_value(row.get("count", "N/A")),
            _percent_value(row.get("fraction")),
        )
        for row in _mapping_list(class_balance.get("rows"))
    ]
    return _markdown_table(
        ("Split", "Class", "Count", "Fraction"),
        rows,
        "Local fixture class-balance table from `output/data/ml_class_balance.json`; counts describe the offline fixture used by this run. {#tbl:class-balance}",
    )


def _artifact_manifest_table(artifact_manifest: dict[str, Any]) -> str:
    entries = _mapping_list(artifact_manifest.get("entries"))
    rows = [
        (
            _string_value(entry.get("path", "N/A")),
            _artifact_role(_string_value(entry.get("path", ""))),
            _string_value(entry.get("size_bytes", "N/A")),
        )
        for entry in entries
    ]
    return _markdown_table(
        ("Artifact", "Role", "Bytes"),
        rows,
        "Generated artifact manifest from `output/reports/artifact_manifest.json`. {#tbl:autoresearch-loop}",
    )


def _review_gate_table(review_decisions: dict[str, Any]) -> str:
    rows = [
        (
            _string_value(row.get("gate", "N/A")),
            _string_value(row.get("required", "N/A")),
            _string_value(row.get("decision", "N/A")),
            _string_value(row.get("rationale", "N/A")),
        )
        for row in _mapping_list(review_decisions.get("decisions"))
    ]
    return _markdown_table(
        ("Gate", "Required", "Decision", "Rationale"),
        rows,
        "Review-gate decisions from `output/data/review_decisions.json`. {#tbl:review-gates}",
    )


def _benchmark_score_table(benchmark_scores: dict[str, Any]) -> str:
    rows = [
        (
            _string_value(row.get("id", "N/A")),
            _string_value(row.get("status", "N/A")),
            _string_value(row.get("score", "N/A")),
            _string_value(row.get("grading_output_path", "N/A")),
        )
        for row in _mapping_list(benchmark_scores.get("tasks"))
    ]
    return _markdown_table(
        ("Benchmark task", "Status", "Score", "Grading output"),
        rows,
        "Benchmark grading table from `output/data/benchmark_scores.json`. {#tbl:benchmark-scores}",
    )


def _classification_diagnostics_table(classification: dict[str, Any]) -> str:
    rows = [
        (
            _string_value(row.get("class_label", "N/A")),
            _percent_value(row.get("precision")),
            _percent_value(row.get("recall")),
            _percent_value(row.get("f1")),
            _string_value(row.get("support", "N/A")),
        )
        for row in _mapping_list(classification.get("per_class"))
    ]
    return _markdown_table(
        ("Class", "Precision", "Recall", "F1", "Support"),
        rows,
        "Accepted-candidate class diagnostics from `output/data/ml_classification_diagnostics.json`. {#tbl:classification-diagnostics}",
    )


def _calibration_bin_table(calibration: dict[str, Any]) -> str:
    rows = [
        (
            f"{_string_value(row.get('lower', 'N/A'))}-{_string_value(row.get('upper', 'N/A'))}",
            _string_value(row.get("count", "N/A")),
            _percent_value(row.get("accuracy")),
            _percent_value(row.get("mean_confidence")),
            _percent_value(row.get("absolute_gap")),
        )
        for row in _mapping_list(calibration.get("bins"))
    ]
    return _markdown_table(
        ("Confidence bin", "Count", "Accuracy", "Mean confidence", "Gap"),
        rows,
        "Calibration bins from `output/data/ml_calibration_report.json`. {#tbl:calibration-bins}",
    )


def _confusion_pair_table(classification: dict[str, Any]) -> str:
    rows = [
        (
            f"{_string_value(row.get('true_label', 'N/A'))} -> {_string_value(row.get('predicted_label', 'N/A'))}",
            _string_value(row.get("count", "N/A")),
            _percent_value(row.get("true_class_error_rate")),
        )
        for row in _mapping_list(classification.get("top_confusion_pairs"))
    ]
    return _markdown_table(
        ("Pair", "Count", "True-class error rate"),
        rows,
        "Top non-diagonal confusion pairs from `output/data/ml_classification_diagnostics.json`. {#tbl:confusion-pairs}",
    )


def _robustness_score_table(robustness: dict[str, Any]) -> str:
    rows = [
        (
            _candidate_display_label(row.get("candidate_id", "N/A")),
            _string_value(row.get("transform", "N/A")),
            _percent_value(row.get("accuracy")),
            _string_value(row.get("sample_count", "N/A")),
        )
        for row in _mapping_list(robustness.get("rows"))
    ]
    return _markdown_table(
        ("Candidate", "Transform", "Accuracy", "Samples"),
        rows,
        "Deterministic no-retrain robustness smoke test from `output/data/ml_robustness_report.json`. {#tbl:robustness-scores}",
    )


def _probability_diagnostics_table(probability: dict[str, Any]) -> str:
    rows = [
        ("Mean confidence", _percent_value(probability.get("mean_confidence"))),
        ("Mean correct confidence", _percent_value(probability.get("mean_correct_confidence"))),
        ("Mean error confidence", _percent_value(probability.get("mean_error_confidence"))),
        ("Mean margin", _percent_value(probability.get("mean_margin"))),
        ("Mean correct margin", _percent_value(probability.get("mean_correct_margin"))),
        ("Mean error margin", _percent_value(probability.get("mean_error_margin"))),
        ("Low-margin count", _string_value(probability.get("low_margin_count", "N/A"))),
    ]
    return _markdown_table(
        ("Statistic", "Value"),
        rows,
        "Accepted-candidate probability diagnostics from `output/data/ml_probability_diagnostics.json`. {#tbl:probability-diagnostics}",
    )


def _bootstrap_interval_table(bootstrap: dict[str, Any]) -> str:
    rows = [
        (
            _metric_label(row.get("metric", "N/A")),
            _percent_value(row.get("observed")),
            _percent_value(row.get("ci_low")),
            _percent_value(row.get("ci_high")),
            _percent_value(row.get("resample_mean")),
        )
        for row in _mapping_list(bootstrap.get("intervals"))
    ]
    return _markdown_table(
        ("Metric", "Observed", "CI low", "CI high", "Resample mean"),
        rows,
        "Deterministic percentile-bootstrap intervals from `output/data/ml_bootstrap_intervals.json`. {#tbl:bootstrap-intervals}",
    )


def _paired_comparison_table(paired: dict[str, Any]) -> str:
    rows = [
        ("Both correct", _string_value(paired.get("both_correct", "N/A"))),
        ("Accepted only correct", _string_value(paired.get("accepted_only_correct", "N/A"))),
        ("Baseline only correct", _string_value(paired.get("baseline_only_correct", "N/A"))),
        ("Both wrong", _string_value(paired.get("both_wrong", "N/A"))),
        ("Discordant examples", _string_value(paired.get("discordant_count", "N/A"))),
        ("Exact McNemar p", _p_value(paired.get("exact_mcnemar_p"))),
        ("Net accuracy gain", _percent_value(paired.get("net_accuracy_gain"))),
    ]
    return _markdown_table(
        ("Matched comparison statistic", "Value"),
        rows,
        "Accepted-candidate versus baseline paired comparison from `output/data/ml_paired_comparison.json`. {#tbl:paired-comparison}",
    )


def _statistical_summary_table(statistical: dict[str, Any]) -> str:
    rows = [
        ("Accuracy", _percent_value(statistical.get("accuracy"))),
        ("Balanced accuracy", _percent_value(statistical.get("balanced_accuracy"))),
        ("Macro F1", _percent_value(statistical.get("macro_f1"))),
        ("Top-2 accuracy", _percent_value(statistical.get("top2_accuracy"))),
        ("Cohen kappa", _decimal_value(statistical.get("cohen_kappa"))),
        ("Brier score", _decimal_value(statistical.get("brier_score"))),
        ("Negative log likelihood", _decimal_value(statistical.get("negative_log_likelihood"))),
        ("Expected calibration error", _percent_value(statistical.get("expected_calibration_error"))),
    ]
    return _markdown_table(
        ("Statistic", "Value"),
        rows,
        "Accepted-candidate statistical summary from `output/data/ml_statistical_summary.json`. {#tbl:statistical-summary}",
    )


def _selective_accuracy_table(statistical: dict[str, Any]) -> str:
    rows = [
        (
            _percent_value(row.get("threshold")),
            _percent_value(row.get("coverage")),
            _percent_value(row.get("selective_accuracy")),
            _string_value(row.get("retained_count", "N/A")),
            _string_value(row.get("error_count", "N/A")),
        )
        for row in _mapping_list(statistical.get("coverage_curve"))
    ]
    return _markdown_table(
        ("Confidence threshold", "Coverage", "Selective accuracy", "Retained", "Errors"),
        rows,
        "Selective-accuracy threshold table from `output/data/ml_statistical_summary.json`. {#tbl:selective-accuracy}",
    )


def _probability_quality_table(statistical: dict[str, Any]) -> str:
    rows = [
        (
            _candidate_display_label(row.get("candidate_id", "N/A")),
            _percent_value(row.get("accuracy")),
            _percent_value(row.get("top2_accuracy")),
            _decimal_value(row.get("brier_score")),
            _decimal_value(row.get("negative_log_likelihood")),
            _percent_value(row.get("mean_confidence")),
        )
        for row in _mapping_list(statistical.get("candidate_probability_quality"))
    ]
    return _markdown_table(
        ("Candidate", "Accuracy", "Top-2 accuracy", "Brier", "NLL", "Mean confidence"),
        rows,
        "Candidate probability-quality table from `output/data/ml_statistical_summary.json`. {#tbl:probability-quality}",
    )


def _training_diagnostics_table(training: dict[str, Any]) -> str:
    rows = [
        (
            _candidate_display_label(row.get("candidate_id", "N/A")),
            _string_value(row.get("status", "N/A")),
            _string_value(row.get("best_epoch", "N/A")),
            _percent_value(row.get("best_test_accuracy")),
            _percent_value(row.get("final_test_accuracy")),
            _percent_value(row.get("train_test_accuracy_gap")),
            _decimal_value(row.get("loss_reduction")),
            _decimal_value(row.get("final_learning_rate")),
        )
        for row in _mapping_list(training.get("rows"))
    ]
    return _markdown_table(
        (
            "Candidate",
            "Status",
            "Best epoch",
            "Best test accuracy",
            "Final test accuracy",
            "Train-test gap",
            "Loss reduction",
            "Final learning rate",
        ),
        rows,
        "Configured-training diagnostics from `output/data/ml_training_diagnostics.json`. {#tbl:training-diagnostics}",
    )


def _variable_provenance_table(provenance: dict[str, dict[str, str]]) -> str:
    counts = Counter(row["source"] for row in provenance.values())
    rows = [(source, str(count)) for source, count in sorted(counts.items())]
    return _markdown_table(
        ("Source artifact", "Injected variables or fragments"),
        rows,
        "Variable provenance summary from `output/data/manuscript_variable_provenance.json`. {#tbl:variable-provenance}",
    )


def _markdown_table(headers: Sequence[str], rows: Sequence[Sequence[str]], caption: str) -> str:
    safe_rows = rows or tuple(("N/A",) * len(headers) for _ in range(1))
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in safe_rows:
        lines.append("| " + " | ".join(_escape_table_cell(cell) for cell in row) + " |")
    lines.extend(("", f": {caption}"))
    return "\n".join(lines)


def _pdf_small_table(headers: Sequence[str], rows: Sequence[Sequence[str]], caption: str) -> str:
    return "\n".join(("\\begingroup\\footnotesize", _markdown_table(headers, rows, caption), "\\endgroup"))


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
