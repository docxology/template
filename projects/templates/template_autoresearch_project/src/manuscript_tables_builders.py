"""Manuscript table builder functions for the AutoResearch exemplar."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .json_coerce import mapping, mapping_list
from .manuscript_tables_format import artifact_markdown_link, markdown_table, pdf_small_table
from .manuscript_tokens_format import (
    artifact_role,
    candidate_display_label,
    decimal_value,
    metric_label,
    model_type_label,
    p_value,
    percent_value,
    short_scope,
    string_value,
)


def candidate_ledger_table(candidate_ledger: dict[str, Any]) -> str:
    baseline = mapping(candidate_ledger.get("baseline"))
    candidates = mapping_list(candidate_ledger.get("candidates"))
    rows = [
        (
            candidate_display_label(baseline.get("identifier", "baseline")),
            model_type_label(baseline.get("model_type", "N/A")),
            "baseline",
            percent_value(baseline.get("test_accuracy")),
            string_value(baseline.get("parameter_count", "N/A")),
        )
    ]
    for candidate in candidates:
        rows.append(
            (
                candidate_display_label(candidate.get("identifier", "N/A")),
                model_type_label(candidate.get("model_type", "N/A")),
                string_value(candidate.get("status", "N/A")),
                percent_value(candidate.get("test_accuracy")),
                string_value(candidate.get("parameter_count", "N/A")),
            )
        )
    return markdown_table(
        ("Candidate", "Model", "Status", "Test accuracy", "Parameters"),
        rows,
        "Candidate lifecycle ledger from `output/data/ml_candidate_ledger.json`. {#tbl:ml-candidate-ledger}",
    )


def figure_method_table(registry: dict[str, Any]) -> str:
    rows = []
    for label, record in sorted(registry.items()):
        if not isinstance(record, dict):
            continue
        metadata = mapping(record.get("metadata"))
        rows.append(
            (
                f"@{string_value(label)}",
                artifact_markdown_link(string_value(metadata.get("source", "N/A"))),
                short_scope(string_value(metadata.get("method", "N/A")), limit=84),
                short_scope(string_value(metadata.get("claim_boundary", "N/A"))),
            )
        )
    return pdf_small_table(
        ("Figure", "Source", "Method", "Scope"),
        rows,
        "Registry-backed figure methods from [`figure_registry.json`](../figures/figure_registry.json); full validation hooks, alt text, and claim boundaries remain in the registry. {#tbl:figure-methods}",
    )


def candidate_interval_table(candidate_intervals: dict[str, Any]) -> str:
    rows = [
        (
            candidate_display_label(row.get("candidate_id", "N/A")),
            string_value(row.get("status", "N/A")),
            f"{string_value(row.get('successes', 'N/A'))}/{string_value(row.get('test_size', 'N/A'))}",
            percent_value(row.get("accuracy")),
            f"{percent_value(row.get('ci_low'))} to {percent_value(row.get('ci_high'))}",
        )
        for row in mapping_list(candidate_intervals.get("rows"))
    ]
    return markdown_table(
        ("Candidate", "Status", "Correct/test", "Accuracy", "Wilson 95% interval"),
        rows,
        "Candidate accuracy intervals from `output/data/ml_candidate_intervals.json`; intervals describe the fixed local test split. {#tbl:candidate-intervals}",
    )


def class_balance_table(class_balance: dict[str, Any]) -> str:
    rows = [
        (
            string_value(row.get("split", "N/A")),
            string_value(row.get("class_label", "N/A")),
            string_value(row.get("count", "N/A")),
            percent_value(row.get("fraction")),
        )
        for row in mapping_list(class_balance.get("rows"))
    ]
    return markdown_table(
        ("Split", "Class", "Count", "Fraction"),
        rows,
        "Local fixture class-balance table from `output/data/ml_class_balance.json`; counts describe the offline fixture used by this run. {#tbl:class-balance}",
    )


def artifact_manifest_table(artifact_manifest: dict[str, Any]) -> str:
    entries = mapping_list(artifact_manifest.get("entries"))
    rows = [
        (
            string_value(entry.get("path", "N/A")),
            artifact_role(string_value(entry.get("path", ""))),
            string_value(entry.get("size_bytes", "N/A")),
        )
        for entry in entries
    ]
    return markdown_table(
        ("Artifact", "Role", "Bytes"),
        rows,
        "Generated artifact manifest from `output/reports/artifact_manifest.json`. {#tbl:autoresearch-loop}",
    )


def review_gate_table(review_decisions: dict[str, Any]) -> str:
    rows = [
        (
            string_value(row.get("gate", "N/A")),
            string_value(row.get("required", "N/A")),
            string_value(row.get("decision", "N/A")),
            string_value(row.get("rationale", "N/A")),
        )
        for row in mapping_list(review_decisions.get("decisions"))
    ]
    return markdown_table(
        ("Gate", "Required", "Decision", "Rationale"),
        rows,
        "Review-gate decisions from `output/data/review_decisions.json`. {#tbl:review-gates}",
    )


def benchmark_score_table(benchmark_scores: dict[str, Any]) -> str:
    rows = [
        (
            string_value(row.get("id", "N/A")),
            string_value(row.get("status", "N/A")),
            string_value(row.get("score", "N/A")),
            string_value(row.get("grading_output_path", "N/A")),
        )
        for row in mapping_list(benchmark_scores.get("tasks"))
    ]
    return markdown_table(
        ("Benchmark task", "Status", "Score", "Grading output"),
        rows,
        "Benchmark grading table from `output/data/benchmark_scores.json`. {#tbl:benchmark-scores}",
    )


def classification_diagnostics_table(classification: dict[str, Any]) -> str:
    rows = [
        (
            string_value(row.get("class_label", "N/A")),
            percent_value(row.get("precision")),
            percent_value(row.get("recall")),
            percent_value(row.get("f1")),
            string_value(row.get("support", "N/A")),
        )
        for row in mapping_list(classification.get("per_class"))
    ]
    return markdown_table(
        ("Class", "Precision", "Recall", "F1", "Support"),
        rows,
        "Accepted-candidate class diagnostics from `output/data/ml_classification_diagnostics.json`. {#tbl:classification-diagnostics}",
    )


def calibration_bin_table(calibration: dict[str, Any]) -> str:
    rows = [
        (
            f"{string_value(row.get('lower', 'N/A'))}-{string_value(row.get('upper', 'N/A'))}",
            string_value(row.get("count", "N/A")),
            percent_value(row.get("accuracy")),
            percent_value(row.get("mean_confidence")),
            percent_value(row.get("absolute_gap")),
        )
        for row in mapping_list(calibration.get("bins"))
    ]
    return markdown_table(
        ("Confidence bin", "Count", "Accuracy", "Mean confidence", "Gap"),
        rows,
        "Calibration bins from `output/data/ml_calibration_report.json`. {#tbl:calibration-bins}",
    )


def calibration_bin_interval_table(calibration_intervals: dict[str, Any]) -> str:
    rows = [
        (
            f"{string_value(row.get('lower', 'N/A'))}-{string_value(row.get('upper', 'N/A'))}",
            string_value(row.get("count", "N/A")),
            string_value(row.get("successes", "N/A")),
            percent_value(row.get("accuracy")),
            f"{percent_value(row.get('ci_low'))} to {percent_value(row.get('ci_high'))}",
            string_value(row.get("empty_bin", "N/A")),
        )
        for row in mapping_list(calibration_intervals.get("bins"))
    ]
    return markdown_table(
        ("Confidence bin", "Count", "Correct", "Accuracy", "Wilson 95%", "Empty"),
        rows,
        "Calibration-bin Wilson intervals from `output/data/ml_calibration_bin_intervals.json`; empty bins are reported explicitly. {#tbl:calibration-bin-intervals}",
    )


def confusion_pair_table(classification: dict[str, Any]) -> str:
    rows = [
        (
            f"{string_value(row.get('true_label', 'N/A'))} -> {string_value(row.get('predicted_label', 'N/A'))}",
            string_value(row.get("count", "N/A")),
            percent_value(row.get("true_class_error_rate")),
        )
        for row in mapping_list(classification.get("top_confusion_pairs"))
    ]
    return markdown_table(
        ("Pair", "Count", "True-class error rate"),
        rows,
        "Top non-diagonal confusion pairs from `output/data/ml_classification_diagnostics.json`. {#tbl:confusion-pairs}",
    )


def robustness_score_table(robustness: dict[str, Any]) -> str:
    rows = [
        (
            candidate_display_label(row.get("candidate_id", "N/A")),
            string_value(row.get("transform", "N/A")),
            percent_value(row.get("accuracy")),
            string_value(row.get("sample_count", "N/A")),
        )
        for row in mapping_list(robustness.get("rows"))
    ]
    return markdown_table(
        ("Candidate", "Transform", "Accuracy", "Samples"),
        rows,
        "Deterministic no-retrain robustness smoke test from `output/data/ml_robustness_report.json`. {#tbl:robustness-scores}",
    )


def probability_diagnostics_table(probability: dict[str, Any]) -> str:
    rows = [
        ("Mean confidence", percent_value(probability.get("mean_confidence"))),
        ("Mean correct confidence", percent_value(probability.get("mean_correct_confidence"))),
        ("Mean error confidence", percent_value(probability.get("mean_error_confidence"))),
        ("Mean margin", percent_value(probability.get("mean_margin"))),
        ("Mean correct margin", percent_value(probability.get("mean_correct_margin"))),
        ("Mean error margin", percent_value(probability.get("mean_error_margin"))),
        ("Low-margin count", string_value(probability.get("low_margin_count", "N/A"))),
    ]
    return markdown_table(
        ("Statistic", "Value"),
        rows,
        "Accepted-candidate probability diagnostics from `output/data/ml_probability_diagnostics.json`. {#tbl:probability-diagnostics}",
    )


def bootstrap_interval_table(bootstrap: dict[str, Any]) -> str:
    rows = [
        (
            metric_label(row.get("metric", "N/A")),
            percent_value(row.get("observed")),
            percent_value(row.get("ci_low")),
            percent_value(row.get("ci_high")),
            percent_value(row.get("resample_mean")),
        )
        for row in mapping_list(bootstrap.get("intervals"))
    ]
    return markdown_table(
        ("Metric", "Observed", "CI low", "CI high", "Resample mean"),
        rows,
        "Deterministic percentile-bootstrap intervals from `output/data/ml_bootstrap_intervals.json`. {#tbl:bootstrap-intervals}",
    )


def paired_comparison_table(paired: dict[str, Any]) -> str:
    rows = [
        ("Both correct", string_value(paired.get("both_correct", "N/A"))),
        ("Accepted only correct", string_value(paired.get("accepted_only_correct", "N/A"))),
        ("Baseline only correct", string_value(paired.get("baseline_only_correct", "N/A"))),
        ("Both wrong", string_value(paired.get("both_wrong", "N/A"))),
        ("Discordant examples", string_value(paired.get("discordant_count", "N/A"))),
        ("Exact McNemar p", p_value(paired.get("exact_mcnemar_p"))),
        ("Net accuracy gain", percent_value(paired.get("net_accuracy_gain"))),
    ]
    return markdown_table(
        ("Matched comparison statistic", "Value"),
        rows,
        "Accepted-candidate versus baseline paired comparison from `output/data/ml_paired_comparison.json`. {#tbl:paired-comparison}",
    )


def statistical_summary_table(statistical: dict[str, Any]) -> str:
    rows = [
        ("Accuracy", percent_value(statistical.get("accuracy"))),
        ("Balanced accuracy", percent_value(statistical.get("balanced_accuracy"))),
        ("Macro F1", percent_value(statistical.get("macro_f1"))),
        ("Top-2 accuracy", percent_value(statistical.get("top2_accuracy"))),
        ("Cohen kappa", decimal_value(statistical.get("cohen_kappa"))),
        ("Brier score", decimal_value(statistical.get("brier_score"))),
        ("Negative log likelihood", decimal_value(statistical.get("negative_log_likelihood"))),
        ("Expected calibration error", percent_value(statistical.get("expected_calibration_error"))),
    ]
    return markdown_table(
        ("Statistic", "Value"),
        rows,
        "Accepted-candidate statistical summary from `output/data/ml_statistical_summary.json`. {#tbl:statistical-summary}",
    )


def selective_accuracy_table(statistical: dict[str, Any]) -> str:
    rows = [
        (
            percent_value(row.get("threshold")),
            percent_value(row.get("coverage")),
            percent_value(row.get("selective_accuracy")),
            string_value(row.get("retained_count", "N/A")),
            string_value(row.get("error_count", "N/A")),
        )
        for row in mapping_list(statistical.get("coverage_curve"))
    ]
    return markdown_table(
        ("Confidence threshold", "Coverage", "Selective accuracy", "Retained", "Errors"),
        rows,
        "Selective-accuracy threshold table from `output/data/ml_statistical_summary.json`. {#tbl:selective-accuracy}",
    )


def probability_quality_table(statistical: dict[str, Any]) -> str:
    rows = [
        (
            candidate_display_label(row.get("candidate_id", "N/A")),
            percent_value(row.get("accuracy")),
            percent_value(row.get("top2_accuracy")),
            decimal_value(row.get("brier_score")),
            decimal_value(row.get("negative_log_likelihood")),
            percent_value(row.get("mean_confidence")),
        )
        for row in mapping_list(statistical.get("candidate_probability_quality"))
    ]
    return markdown_table(
        ("Candidate", "Accuracy", "Top-2 accuracy", "Brier", "NLL", "Mean confidence"),
        rows,
        "Candidate probability-quality table from `output/data/ml_statistical_summary.json`. {#tbl:probability-quality}",
    )


def training_diagnostics_table(training: dict[str, Any]) -> str:
    rows = [
        (
            candidate_display_label(row.get("candidate_id", "N/A")),
            string_value(row.get("status", "N/A")),
            string_value(row.get("best_epoch", "N/A")),
            percent_value(row.get("best_test_accuracy")),
            percent_value(row.get("final_test_accuracy")),
            percent_value(row.get("train_test_accuracy_gap")),
            decimal_value(row.get("loss_reduction")),
            decimal_value(row.get("final_learning_rate")),
        )
        for row in mapping_list(training.get("rows"))
    ]
    return markdown_table(
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


def candidate_rank_stability_table(rank_stability: dict[str, Any]) -> str:
    rows = [
        (
            candidate_display_label(row.get("candidate_id", "N/A")),
            string_value(row.get("observed_rank", "N/A")),
            percent_value(row.get("rank_1_frequency")),
            decimal_value(row.get("mean_rank")),
            percent_value(row.get("test_accuracy")),
        )
        for row in mapping_list(rank_stability.get("rank_frequencies"))
    ]
    return markdown_table(
        ("Candidate", "Observed rank", "Top-rank frequency", "Mean rank", "Accuracy"),
        rows,
        "Candidate rank-stability table from `output/data/ml_candidate_rank_stability.json`; frequencies are deterministic local bootstrap summaries. {#tbl:candidate-rank-stability}",
    )


def candidate_selection_audit_table(candidate_selection: dict[str, Any]) -> str:
    rows = [
        (
            string_value(row.get("rank", "N/A")),
            candidate_display_label(row.get("candidate_id", "N/A")),
            string_value(row.get("status", "N/A")),
            percent_value(row.get("test_accuracy")),
            f"{percent_value(row.get('wilson_ci_low'))} to {percent_value(row.get('wilson_ci_high'))}",
            decimal_value(row.get("brier_score")),
            decimal_value(row.get("negative_log_likelihood")),
            string_value(row.get("parameter_count", "N/A")),
        )
        for row in mapping_list(candidate_selection.get("rows"))
    ]
    return markdown_table(
        ("Rank", "Candidate", "Status", "Accuracy", "Wilson 95%", "Brier", "NLL", "Parameters"),
        rows,
        "Candidate-selection audit from `output/data/ml_candidate_selection_audit.json`; the objective metric ranks candidates, while probability diagnostics and parameter counts audit the chosen tie-break context. {#tbl:candidate-selection-audit}",
    )


def diagnostic_boundary_table(diagnostic_boundary: dict[str, Any]) -> str:
    rows = [
        (
            string_value(row.get("surface", "N/A")).replace("_", " "),
            artifact_markdown_link(string_value(row.get("source_artifact", "N/A"))),
            short_scope(string_value(row.get("method", "N/A")), limit=80),
            short_scope(string_value(row.get("supports", "N/A")), limit=80),
            short_scope(string_value(row.get("does_not_support", "N/A")), limit=80),
        )
        for row in mapping_list(diagnostic_boundary.get("rows"))
    ]
    return pdf_small_table(
        ("Surface", "Source", "Method", "Supports", "Does not support"),
        rows,
        "Diagnostic claim-boundary table from `output/data/ml_diagnostic_boundary.json`. {#tbl:diagnostic-boundary}",
    )


def phase_ledger_table(phase_ledger: dict[str, Any]) -> str:
    rows = [
        (
            string_value(row.get("phase", "N/A")).replace("_", " "),
            string_value(row.get("order", "N/A")),
            string_value(row.get("artifact_group", "N/A")),
            string_value(row.get("observed_artifact_count", "N/A")),
            short_scope(string_value(row.get("description", "N/A")), limit=80),
        )
        for row in mapping_list(phase_ledger.get("phases"))
    ]
    return markdown_table(
        ("Phase", "Order", "Group", "Observed artifacts", "Description"),
        rows,
        "Deterministic phase ledger from `output/data/autoresearch_phase_ledger.json`; settlement order is not an autonomy claim. {#tbl:phase-ledger}",
    )


def figure_quality_table(figure_quality: dict[str, Any]) -> str:
    rows = [
        (
            string_value(row.get("label", "N/A")),
            string_value(row.get("width_px", "N/A")) + "x" + string_value(row.get("height_px", "N/A")),
            decimal_value(row.get("pixel_variance")),
            string_value(row.get("source_exists", "N/A")),
            string_value(row.get("nonblank", "N/A")),
        )
        for row in mapping_list(figure_quality.get("figures"))
    ]
    caption = (
        "Figure-quality checks from `output/data/figure_quality_report.json`; "
        f"{string_value(figure_quality.get('figure_count', 'N/A'))} registered figure(s) were checked. "
        "{#tbl:figure-quality}"
    )
    return markdown_table(("Figure", "Pixels", "Variance", "Source exists", "Nonblank"), rows, caption)


def security_artifact_table(
    security_profile: dict[str, Any],
    security_inventory: dict[str, Any],
    security_attestation: dict[str, Any],
) -> str:
    rows = [
        (
            "profile",
            artifact_markdown_link("output/data/autoresearch_security_profile.json"),
            string_value(security_profile.get("mode", "N/A")),
        ),
        (
            "threat model",
            artifact_markdown_link("output/data/autoresearch_threat_model.json"),
            string_value(security_profile.get("network_policy", "N/A")),
        ),
        (
            "inventory",
            artifact_markdown_link("output/data/autoresearch_supply_chain_inventory.json"),
            f"{len(mapping_list(security_inventory.get('inputs')))} inputs",
        ),
        (
            "inventory export",
            artifact_markdown_link("output/data/autoresearch_inventory_export.json"),
            "local non-SBOM export",
        ),
        (
            "attestation",
            artifact_markdown_link("output/data/autoresearch_integrity_attestation.json"),
            string_value(security_attestation.get("status", "N/A")),
        ),
        (
            "review",
            artifact_markdown_link("output/reports/autoresearch_security_review.md"),
            "human review input",
        ),
    ]
    return markdown_table(
        ("Security artifact", "Path", "Summary"),
        rows,
        "Local security artifacts generated for the bounded AutoResearch run. {#tbl:security-artifacts}",
    )


def security_threat_model_table(threat_model: dict[str, Any]) -> str:
    rows = [
        (
            string_value(row.get("id", "N/A")).removeprefix("threat-").replace("-", " "),
            string_value(row.get("stride_category", "N/A")),
            string_value(row.get("attack_technique", "N/A")),
            short_scope(string_value(row.get("scenario", "N/A")), limit=72),
            short_scope(string_value(row.get("residual_risk", "N/A")), limit=72),
        )
        for row in mapping_list(threat_model.get("threats"))
    ]
    return pdf_small_table(
        ("Threat", "STRIDE", "ATT&CK", "Scenario", "Residual risk"),
        rows,
        "Threat-model rows from `output/data/autoresearch_threat_model.json`; ATT&CK labels scope supply-chain compromise analogies. {#tbl:security-threat-model}",
    )


def security_integrity_table(attestation: dict[str, Any]) -> str:
    rows = [
        ("status", string_value(attestation.get("status", "N/A"))),
        ("algorithm", string_value(attestation.get("algorithm", "N/A"))),
        ("checked files", string_value(attestation.get("checked_count", "N/A"))),
        ("missing files", string_value(attestation.get("missing_count", "N/A"))),
        ("checksum mismatches", string_value(attestation.get("mismatch_count", "N/A"))),
        ("external signature", string_value(attestation.get("external_signature", "N/A"))),
    ]
    return markdown_table(
        ("Integrity field", "Value"),
        rows,
        "Integrity-attestation summary from `output/data/autoresearch_integrity_attestation.json`. {#tbl:security-integrity}",
    )


def variable_provenance_table(provenance: dict[str, dict[str, str]]) -> str:
    counts = Counter(row["source"] for row in provenance.values())
    rows = [(source, str(count)) for source, count in sorted(counts.items())]
    return markdown_table(
        ("Source artifact", "Injected variables or fragments"),
        rows,
        "Variable provenance summary from `output/data/manuscript_variable_provenance.json`. {#tbl:variable-provenance}",
    )
