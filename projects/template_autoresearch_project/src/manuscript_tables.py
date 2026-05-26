"""Manuscript table builders for the AutoResearch exemplar."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Sequence


def build_table_specs(
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
    candidate_selection: dict[str, Any],
    diagnostic_boundary: dict[str, Any],
    security_profile: dict[str, Any],
    security_threat_model: dict[str, Any],
    security_inventory: dict[str, Any],
    security_attestation: dict[str, Any],
) -> dict[str, tuple[str, str, str]]:
    """Build manuscript table variables and provenance pointers."""
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
        "CANDIDATE_SELECTION_AUDIT_TABLE": (
            _candidate_selection_audit_table(candidate_selection),
            "output/data/ml_candidate_selection_audit.json",
            "/rows",
        ),
        "DIAGNOSTIC_BOUNDARY_TABLE": (
            _diagnostic_boundary_table(diagnostic_boundary),
            "output/data/ml_diagnostic_boundary.json",
            "/rows",
        ),
        "SECURITY_ARTIFACT_TABLE": (
            _security_artifact_table(security_profile, security_inventory, security_attestation),
            "output/data/autoresearch_supply_chain_inventory.json",
            "/",
        ),
        "SECURITY_THREAT_MODEL_TABLE": (
            _security_threat_model_table(security_threat_model),
            "output/data/autoresearch_threat_model.json",
            "/threats",
        ),
        "SECURITY_INTEGRITY_TABLE": (
            _security_integrity_table(security_attestation),
            "output/data/autoresearch_integrity_attestation.json",
            "/",
        ),
    }
    return table_specs


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


def _candidate_selection_audit_table(candidate_selection: dict[str, Any]) -> str:
    rows = [
        (
            _string_value(row.get("rank", "N/A")),
            _candidate_display_label(row.get("candidate_id", "N/A")),
            _string_value(row.get("status", "N/A")),
            _percent_value(row.get("test_accuracy")),
            f"{_percent_value(row.get('wilson_ci_low'))} to {_percent_value(row.get('wilson_ci_high'))}",
            _decimal_value(row.get("brier_score")),
            _decimal_value(row.get("negative_log_likelihood")),
            _string_value(row.get("parameter_count", "N/A")),
        )
        for row in _mapping_list(candidate_selection.get("rows"))
    ]
    return _markdown_table(
        ("Rank", "Candidate", "Status", "Accuracy", "Wilson 95%", "Brier", "NLL", "Parameters"),
        rows,
        "Candidate-selection audit from `output/data/ml_candidate_selection_audit.json`; the objective metric ranks candidates, while probability diagnostics and parameter counts audit the chosen tie-break context. {#tbl:candidate-selection-audit}",
    )


def _diagnostic_boundary_table(diagnostic_boundary: dict[str, Any]) -> str:
    rows = [
        (
            _string_value(row.get("surface", "N/A")).replace("_", " "),
            _artifact_markdown_link(_string_value(row.get("source_artifact", "N/A"))),
            _short_scope(_string_value(row.get("method", "N/A")), limit=80),
            _short_scope(_string_value(row.get("supports", "N/A")), limit=80),
            _short_scope(_string_value(row.get("does_not_support", "N/A")), limit=80),
        )
        for row in _mapping_list(diagnostic_boundary.get("rows"))
    ]
    return _pdf_small_table(
        ("Surface", "Source", "Method", "Supports", "Does not support"),
        rows,
        "Diagnostic claim-boundary table from `output/data/ml_diagnostic_boundary.json`. {#tbl:diagnostic-boundary}",
    )


def _security_artifact_table(
    security_profile: dict[str, Any],
    security_inventory: dict[str, Any],
    security_attestation: dict[str, Any],
) -> str:
    rows = [
        (
            "profile",
            _artifact_markdown_link("output/data/autoresearch_security_profile.json"),
            _string_value(security_profile.get("mode", "N/A")),
        ),
        (
            "threat model",
            _artifact_markdown_link("output/data/autoresearch_threat_model.json"),
            _string_value(security_profile.get("network_policy", "N/A")),
        ),
        (
            "inventory",
            _artifact_markdown_link("output/data/autoresearch_supply_chain_inventory.json"),
            f"{len(_mapping_list(security_inventory.get('inputs')))} inputs",
        ),
        (
            "attestation",
            _artifact_markdown_link("output/data/autoresearch_integrity_attestation.json"),
            _string_value(security_attestation.get("status", "N/A")),
        ),
        (
            "review",
            _artifact_markdown_link("output/reports/autoresearch_security_review.md"),
            "human review input",
        ),
    ]
    return _markdown_table(
        ("Security artifact", "Path", "Summary"),
        rows,
        "Local security artifacts generated for the bounded AutoResearch run. {#tbl:security-artifacts}",
    )


def _security_threat_model_table(threat_model: dict[str, Any]) -> str:
    rows = [
        (
            _string_value(row.get("id", "N/A")).removeprefix("threat-").replace("-", " "),
            _string_value(row.get("stride_category", "N/A")),
            _string_value(row.get("attack_technique", "N/A")),
            _short_scope(_string_value(row.get("scenario", "N/A")), limit=72),
            _short_scope(_string_value(row.get("residual_risk", "N/A")), limit=72),
        )
        for row in _mapping_list(threat_model.get("threats"))
    ]
    return _pdf_small_table(
        ("Threat", "STRIDE", "ATT&CK", "Scenario", "Residual risk"),
        rows,
        "Threat-model rows from `output/data/autoresearch_threat_model.json`; ATT&CK labels scope supply-chain compromise analogies. {#tbl:security-threat-model}",
    )


def _security_integrity_table(attestation: dict[str, Any]) -> str:
    rows = [
        ("status", _string_value(attestation.get("status", "N/A"))),
        ("algorithm", _string_value(attestation.get("algorithm", "N/A"))),
        ("checked files", _string_value(attestation.get("checked_count", "N/A"))),
        ("missing files", _string_value(attestation.get("missing_count", "N/A"))),
        ("checksum mismatches", _string_value(attestation.get("mismatch_count", "N/A"))),
        ("external signature", _string_value(attestation.get("external_signature", "N/A"))),
    ]
    return _markdown_table(
        ("Integrity field", "Value"),
        rows,
        "Integrity-attestation summary from `output/data/autoresearch_integrity_attestation.json`. {#tbl:security-integrity}",
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


def variable_provenance_table(provenance: dict[str, dict[str, str]]) -> str:
    """Build the manuscript variable provenance table."""
    return _variable_provenance_table(provenance)


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


def _decimal_value(value: object) -> str:
    if not isinstance(value, int | float):
        return "N/A"
    return f"{float(value):.3f}"


def _p_value(value: object) -> str:
    if not isinstance(value, int | float):
        return "N/A"
    return f"{float(value):.3f}"


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
    label = _artifact_link_label(path)
    if path.startswith("output/"):
        target = "../" + path.removeprefix("output/")
    elif path.startswith("data/"):
        target = "../../" + path
    else:
        target = path
    return f"[{label}]({target})"


def _artifact_link_label(path: str) -> str:
    if path in {"", "N/A"}:
        return "N/A"
    stem = Path(path).stem
    for prefix in ("autoresearch_", "ml_", "mnist_"):
        stem = stem.removeprefix(prefix)
    labels = {
        "integrity_attestation": "integrity attestation",
        "security_profile": "security profile",
        "supply_chain_inventory": "supply inventory",
        "threat_model": "threat model",
        "candidate_intervals": "candidate intervals",
        "classification_diagnostics": "class diagnostics",
        "statistical_summary": "statistical summary",
        "probability_diagnostics": "probability diagnostics",
    }
    return labels.get(stem, stem.replace("_", " "))


def _short_scope(value: str, *, limit: int = 92) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")
