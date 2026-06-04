"""ML task manuscript token hydration for the AutoResearch exemplar."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.json_coerce import mapping
from .manuscript_tokens_format import (
    accuracy_interval,
    benchmark_task_ids,
    bootstrap_interval,
    dataset_short_name,
    decimal_value,
    first_model_candidate,
    image_shape,
    last_coverage_value,
    model_family_labels,
    model_type_label,
    p_value,
    percent_value,
    per_class_count,
    status_counts,
    status_summary,
    string_value,
    top_confusion_pair_label,
    currency_value,
)


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
        "ML_TASK_SEED": string_value(payload.get("seed", dataset.get("seed", "N/A"))),
        "CANDIDATE_COUNT": string_value(payload.get("candidate_count", "N/A")),
        "EVALUATED_CANDIDATE_COUNT": string_value(payload.get("evaluated_candidate_count", "N/A")),
        "ACCEPTED_CANDIDATE_ID": string_value(payload.get("accepted_candidate_id", "N/A")),
        "BASELINE_ACCURACY": percent_value(payload.get("baseline_accuracy")),
        "BEST_ACCURACY": percent_value(payload.get("best_accuracy")),
        "ACCURACY_DELTA": percent_value(payload.get("accuracy_delta")),
        "BUDGET_EXHAUSTED": str(bool(payload.get("budget_exhausted", False))).lower(),
        "BENCHMARK_SCORE": string_value(payload.get("benchmark_score", "N/A")),
        "LLM_CALLS_USED": string_value(payload.get("llm_calls_used", 0)),
        "COST_USD_USED": currency_value(payload.get("cost_usd_used", 0.0)),
        "DATASET_NAME": string_value(payload.get("dataset_name", dataset.get("dataset_name", "N/A"))),
        "TRAIN_SIZE": string_value(payload.get("train_size", dataset.get("train_size", "N/A"))),
        "TEST_SIZE": string_value(payload.get("test_size", dataset.get("test_size", "N/A"))),
        "ACCEPTED_MODEL_TYPE": string_value(payload.get("accepted_model_type", accepted.get("model_type", "N/A"))),
        "ACCEPTED_PARAMETER_COUNT": string_value(
            payload.get("parameter_count", accepted.get("parameter_count", "N/A"))
        ),
        "TRANSFORMER_EVALUATED": str(transformer_evaluated).lower(),
    }


def put_ml_detail_variables(
    put: Callable[[str, object, str, str], None],
    *,
    ml: dict[str, Any],
    config: dict[str, Any],
    ml_task_summary: dict[str, Any],
    task_config: dict[str, Any],
    dataset: dict[str, Any],
    baseline: dict[str, Any],
    accepted: dict[str, Any],
    candidates: list[dict[str, Any]],
    classification: dict[str, Any],
    calibration: dict[str, Any],
    class_balance: dict[str, Any],
    robustness: dict[str, Any],
    probability: dict[str, Any],
    bootstrap: dict[str, Any],
    paired: dict[str, Any],
    statistical: dict[str, Any],
    training: dict[str, Any],
    rank_stability: dict[str, Any],
    phase_ledger: dict[str, Any],
    figure_quality: dict[str, Any],
) -> None:
    """Register ML detail tokens and provenance via ``put``."""
    put("TASK_IDENTIFIER", task_config.get("id", "N/A"), "output/data/ml_task_results.json", "/task_config/id")
    put("ML_TASK_NAME", ml.get("task_name", "N/A"), "output/data/ml_task_results.json", "/task_name")
    put(
        "DATASET_SHORT_NAME",
        dataset_short_name(string_value(dataset.get("dataset_name", "N/A"))),
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
        image_shape(dataset.get("image_shape")),
        "output/data/ml_task_results.json",
        "/dataset/image_shape",
    )
    put(
        "METRIC_NAME",
        mapping(ml.get("objective")).get("metric", task_config.get("metric_name", "N/A")),
        "output/data/ml_task_results.json",
        "/objective/metric",
    )
    put(
        "METRIC_DIRECTION",
        mapping(ml.get("objective")).get("direction", task_config.get("metric_direction", "N/A")),
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
        status_counts(candidates).get("deferred", 0),
        "output/data/ml_task_results.json",
        "/candidates",
    )
    put("CANDIDATE_STATUS_SUMMARY", status_summary(candidates), "output/data/ml_task_results.json", "/candidates")
    put(
        "MODEL_FAMILY_LABELS",
        model_family_labels(baseline, candidates),
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
        model_type_label(baseline.get("model_type", "N/A")),
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
        model_type_label(accepted.get("model_type", "N/A")),
        "output/data/ml_task_results.json",
        "/accepted_candidate/model_type",
    )
    transformer = first_model_candidate(candidates, "tiny_patch_transformer")
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
        percent_value(classification.get("macro_f1")),
        "output/data/ml_classification_diagnostics.json",
        "/macro_f1",
    )
    put(
        "ACCEPTED_ACCURACY_INTERVAL",
        accuracy_interval(classification),
        "output/data/ml_classification_diagnostics.json",
        "/accuracy_ci_low",
    )
    put(
        "ACCEPTED_CALIBRATION_ECE",
        percent_value(calibration.get("expected_calibration_error")),
        "output/data/ml_calibration_report.json",
        "/expected_calibration_error",
    )
    put(
        "TOP_CONFUSION_PAIR",
        top_confusion_pair_label(classification),
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
        per_class_count(class_balance, "train"),
        "output/data/ml_class_balance.json",
        "/rows",
    )
    put(
        "TEST_PER_CLASS_COUNT",
        per_class_count(class_balance, "test"),
        "output/data/ml_class_balance.json",
        "/rows",
    )
    put(
        "ROBUSTNESS_MIN_ACCURACY",
        percent_value(robustness.get("accepted_min_accuracy")),
        "output/data/ml_robustness_report.json",
        "/accepted_min_accuracy",
    )
    put(
        "MEAN_CORRECT_CONFIDENCE",
        percent_value(probability.get("mean_correct_confidence")),
        "output/data/ml_probability_diagnostics.json",
        "/mean_correct_confidence",
    )
    put(
        "MEAN_ERROR_CONFIDENCE",
        percent_value(probability.get("mean_error_confidence")),
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
        bootstrap_interval(bootstrap, "accuracy"),
        "output/data/ml_bootstrap_intervals.json",
        "/intervals",
    )
    put(
        "BOOTSTRAP_MACRO_F1_INTERVAL",
        bootstrap_interval(bootstrap, "macro_f1"),
        "output/data/ml_bootstrap_intervals.json",
        "/intervals",
    )
    put(
        "PAIRED_NET_GAIN",
        percent_value(paired.get("net_accuracy_gain")),
        "output/data/ml_paired_comparison.json",
        "/net_accuracy_gain",
    )
    put(
        "MCNEMAR_P_VALUE",
        p_value(paired.get("exact_mcnemar_p")),
        "output/data/ml_paired_comparison.json",
        "/exact_mcnemar_p",
    )
    put(
        "ACCEPTED_BRIER_SCORE",
        decimal_value(statistical.get("brier_score")),
        "output/data/ml_statistical_summary.json",
        "/brier_score",
    )
    put(
        "ACCEPTED_NEGATIVE_LOG_LIKELIHOOD",
        decimal_value(statistical.get("negative_log_likelihood")),
        "output/data/ml_statistical_summary.json",
        "/negative_log_likelihood",
    )
    put(
        "ACCEPTED_TOP2_ACCURACY",
        percent_value(statistical.get("top2_accuracy")),
        "output/data/ml_statistical_summary.json",
        "/top2_accuracy",
    )
    put(
        "ACCEPTED_COHEN_KAPPA",
        decimal_value(statistical.get("cohen_kappa")),
        "output/data/ml_statistical_summary.json",
        "/cohen_kappa",
    )
    put(
        "SELECTIVE_HIGH_CONFIDENCE_COVERAGE",
        percent_value(last_coverage_value(statistical, "coverage")),
        "output/data/ml_statistical_summary.json",
        "/coverage_curve",
    )
    put(
        "SELECTIVE_HIGH_CONFIDENCE_ACCURACY",
        percent_value(last_coverage_value(statistical, "selective_accuracy")),
        "output/data/ml_statistical_summary.json",
        "/coverage_curve",
    )
    training_policy = mapping(training.get("training_policy"))
    accepted_training = mapping(training.get("accepted"))
    put(
        "LEARNING_RATE_DECAY",
        string_value(training_policy.get("learning_rate_decay", "N/A")),
        "output/data/ml_training_diagnostics.json",
        "/training_policy/learning_rate_decay",
    )
    put(
        "GRADIENT_CLIP_NORM",
        string_value(training_policy.get("gradient_clip_norm", "N/A")),
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
        decimal_value(accepted_training.get("final_learning_rate")),
        "output/data/ml_training_diagnostics.json",
        "/accepted/final_learning_rate",
    )
    put(
        "ACCEPTED_LOSS_REDUCTION",
        decimal_value(accepted_training.get("loss_reduction")),
        "output/data/ml_training_diagnostics.json",
        "/accepted/loss_reduction",
    )
    put(
        "ACCEPTED_TRAIN_TEST_GAP",
        percent_value(accepted_training.get("train_test_accuracy_gap")),
        "output/data/ml_training_diagnostics.json",
        "/accepted/train_test_accuracy_gap",
    )
    put(
        "ACCEPTED_TOP_RANK_FREQUENCY",
        percent_value(rank_stability.get("accepted_top_rank_frequency")),
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
        benchmark_task_ids(config),
        "output/data/autoresearch_loop.json",
        "/config/benchmark_tasks",
    )
