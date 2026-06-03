"""Dynamic caption strings for AutoResearch figure registry entries."""

from __future__ import annotations

from src.ml.task import MLTaskResult
from src.models import AutoResearchLoopResult


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_figure_registry_captions(
    result: AutoResearchLoopResult | None = None,
    ml_result: MLTaskResult | None = None,
) -> dict[str, str]:
    """Return caption strings keyed by registry field name."""
    stage_caption = (
        "Validated AutoResearch stage, supported-claim, and required-artifact counts "
        "from output/data/autoresearch_loop.json; this is a readiness summary, not "
        "evidence that human review approved publication."
    )
    score_caption = (
        "Held-out accuracy with Wilson intervals for the baseline and evaluated "
        "candidates from output/data/ml_candidate_intervals.json; accepted status "
        "is highlighted and deferred candidates remain in the ledger."
    )
    confusion_caption = (
        "Accepted-candidate confusion matrix on the fixed MNIST test split from "
        "output/data/ml_confusion_matrix.csv; this descriptive diagnostic is scoped "
        "to the local fixture."
    )
    closure_caption = (
        "File-backed AutoResearch closure from program through review, generated from "
        "output/data/autoresearch_loop.json and method ledgers; the closure is an "
        "inspectable workflow, not autonomous self-approval."
    )
    per_class_caption = (
        "Per-class accepted-candidate accuracy computed from "
        "output/data/ml_confusion_matrix.csv; the diagnostic is scoped to the fixed "
        "local test split."
    )
    lifecycle_caption = (
        "Candidate lifecycle counts from output/data/ml_candidate_ledger.json, showing "
        "which proposals were evaluated, accepted, rejected, or deferred under budget."
    )
    contact_sheet_caption = (
        "Deterministic contact sheet from data/mnist_small.npz and "
        "data/mnist_small_provenance.json; it illustrates the local subset used by "
        "the run rather than downloading data at runtime."
    )
    class_balance_caption = (
        "Train and test class counts from output/data/ml_class_balance.json; the "
        "diagnostic verifies the local fixture is stratified by digit class."
    )
    learning_curve_caption = (
        "Epoch-level held-out accuracy curves from output/data/ml_training_history.csv; "
        "the curves diagnose configured candidate training under the fixed budget."
    )
    complexity_caption = (
        "Parameter-count versus held-out accuracy diagnostic from output/data/ml_task_results.json; "
        "the chart compares model size and metric outcome for the bounded candidate set."
    )
    error_caption = (
        "Accepted-candidate test-set error examples from output/data/ml_error_examples.json "
        "and data/mnist_small.npz; examples are diagnostic cases, not a statistical error taxonomy."
    )
    calibration_caption = (
        "Accepted-candidate reliability curve and confidence-bin counts from "
        "output/data/ml_calibration_report.json; calibration is descriptive for the fixed local split."
    )
    class_metrics_caption = (
        "Accepted-candidate per-class precision, recall, and F1 from "
        "output/data/ml_classification_diagnostics.json; values diagnose local split behavior."
    )
    confusion_pairs_caption = (
        "Ranked off-diagonal confusion pairs from output/data/ml_classification_diagnostics.json; "
        "counts identify local error patterns rather than a general taxonomy."
    )
    generalization_caption = (
        "Train/test accuracy and loss by evaluated candidate from "
        "output/data/ml_classification_diagnostics.json; gaps are bounded-loop diagnostics."
    )
    robustness_caption = (
        "Candidate accuracy under deterministic no-retrain test transforms from "
        "output/data/ml_robustness_report.json; this is a smoke test, not a certified robustness result."
    )
    probability_caption = (
        "Accepted-candidate confidence and prediction-margin histograms from "
        "output/data/ml_probability_diagnostics.json; distributions separate correct and error cases."
    )
    bootstrap_caption = (
        "Deterministic percentile-bootstrap intervals for accepted-candidate accuracy and macro F1 from "
        "output/data/ml_bootstrap_intervals.json; intervals describe the fixed local test split."
    )
    paired_caption = (
        "Matched accepted-candidate versus baseline correctness counts from "
        "output/data/ml_paired_comparison.json, including exact McNemar discordance summary."
    )
    selective_caption = (
        "Accepted-candidate selective accuracy by configured confidence threshold from "
        "output/data/ml_statistical_summary.json; threshold labels show the retained-confidence policy."
    )
    probability_quality_caption = (
        "Candidate probability-quality diagnostics from output/data/ml_statistical_summary.json, comparing "
        "Brier score and negative log likelihood for evaluated candidates."
    )
    rank_stability_caption = (
        "Candidate rank-stability diagnostics from output/data/ml_candidate_rank_stability.json, comparing "
        "top-rank frequencies and mean ranks under deterministic local bootstrap resampling."
    )
    training_dynamics_caption = (
        "Configured-training dynamics from output/data/ml_training_diagnostics.json, comparing final and "
        "best-epoch held-out accuracy plus train-test accuracy gaps for evaluated candidates."
    )
    security_control_caption = (
        "Local security-control matrix from output/data/autoresearch_threat_model.json; controls map "
        "NIST, SLSA, and ATT&CK-inspired safeguards to deterministic evidence surfaces without claiming "
        "production security certification. Generation method: structured control matrix with separate "
        "control, evidence, framework, and status columns."
    )
    integrity_chain_caption = (
        "Local integrity chain from output/data/autoresearch_integrity_attestation.json; checksums summarize "
        "the observed run artifacts and remain unsigned local evidence."
    )
    if result is not None:
        stage_caption = (
            f"Validated AutoResearch run with {len(result.stage_results)} stages, "
            f"{result.supported_claim_count} supported claims, and "
            f"{len(result.config.required_artifacts)} required artifacts from "
            "output/data/autoresearch_loop.json; the count summarizes readiness "
            "artifacts, not human approval."
        )
        closure_caption = (
            "File-backed AutoResearch closure from program through review, with "
            f"{result.supported_claim_count} supported claims and readiness "
            f"{'passed' if result.readiness_valid else 'pending'}; review remains "
            "a deferred human decision and the provenance path remains inspectable."
        )
    if ml_result is not None:
        score_caption = (
            "Held-out accuracy with Wilson intervals for the baseline and evaluated "
            "candidates from output/data/ml_candidate_intervals.json; accepted candidate "
            f"{ml_result.accepted_candidate_id} improves accuracy from "
            f"{_format_percent(ml_result.baseline.test_accuracy)} to "
            f"{_format_percent(ml_result.best_accuracy)} on the fixed subset, with "
            "deferred proposals kept in the candidate ledger."
        )
        confusion_caption = (
            f"Accepted-candidate confusion matrix for {ml_result.accepted_candidate_id} "
            f"on the fixed {ml_result.dataset.dataset_name} test split, sourced from "
            "output/data/ml_confusion_matrix.csv; it diagnoses the selected run, not "
            "general full-dataset performance."
        )
        per_class_caption = (
            f"Per-class accuracy for {ml_result.accepted_candidate_id}, computed from "
            "output/data/ml_confusion_matrix.csv; variation across digits is a "
            "run diagnostic for the fixed local test split."
        )
        lifecycle_caption = (
            f"Candidate lifecycle ledger from output/data/ml_candidate_ledger.json: "
            f"{ml_result.evaluated_candidate_count} evaluated out of "
            f"{ml_result.candidate_count} proposed candidates, with deferred proposals "
            "kept visible instead of executed automatically."
        )
        contact_sheet_caption = (
            f"Deterministic class-balanced contact sheet for {ml_result.dataset.dataset_name} "
            "from data/mnist_small.npz and data/mnist_small_provenance.json; the figure "
            "documents the local subset used by the offline run."
        )
        class_balance_caption = (
            "Train and test class counts from output/data/ml_class_balance.json; "
            f"the local fixture contains {ml_result.dataset.train_size} train and "
            f"{ml_result.dataset.test_size} test examples across {ml_result.dataset.class_count} classes."
        )
        learning_curve_caption = (
            "Epoch-level held-out accuracy curves for evaluated candidates from "
            "output/data/ml_training_history.csv; the accepted curve is visually emphasized "
            f"for {ml_result.accepted_candidate_id}."
        )
        complexity_caption = (
            "Parameter-count versus held-out accuracy for the baseline and evaluated candidates "
            "from output/data/ml_task_results.json; the accepted candidate is highlighted "
            "without claiming a general scaling law."
        )
        error_caption = (
            f"First accepted-candidate error examples for {ml_result.accepted_candidate_id}, "
            "sourced from output/data/ml_error_examples.json and data/mnist_small.npz; "
            "these images support qualitative diagnosis only."
        )
        calibration_caption = (
            f"Reliability curve for {ml_result.accepted_candidate_id} from "
            "output/data/ml_calibration_report.json; expected calibration error and bin counts "
            "summarize the accepted candidate on the fixed local test split."
        )
        class_metrics_caption = (
            f"Per-class precision, recall, and F1 for {ml_result.accepted_candidate_id}, "
            "sourced from output/data/ml_classification_diagnostics.json; metrics are scoped "
            "to the local test split."
        )
        confusion_pairs_caption = (
            f"Top non-diagonal confusion pairs for {ml_result.accepted_candidate_id}, "
            "sourced from output/data/ml_classification_diagnostics.json; the bars highlight "
            "which local digit pairs account for accepted-candidate errors."
        )
        generalization_caption = (
            "Train/test accuracy and loss for evaluated candidates from "
            "output/data/ml_classification_diagnostics.json; the plot exposes local "
            "generalization gaps without claiming full-dataset behavior."
        )
        robustness_caption = (
            "Accuracy for evaluated candidates under identity, one-pixel shifts, and low contrast "
            "from output/data/ml_robustness_report.json; the deterministic transforms provide a "
            "bounded smoke test only."
        )
        probability_caption = (
            f"Confidence and prediction-margin histograms for {ml_result.accepted_candidate_id} "
            "from output/data/ml_probability_diagnostics.json; the figure separates correct and "
            "incorrect local test predictions."
        )
        bootstrap_caption = (
            f"Deterministic percentile-bootstrap intervals for {ml_result.accepted_candidate_id} "
            "from output/data/ml_bootstrap_intervals.json; the intervals summarize local sampling "
            "variation for accuracy and macro F1."
        )
        paired_caption = (
            f"Matched correctness comparison between {ml_result.accepted_candidate_id} and the "
            f"{ml_result.baseline.identifier} baseline from output/data/ml_paired_comparison.json; "
            "discordant cells support the paired test summary."
        )
        selective_caption = (
            f"Confidence-threshold trade-off for {ml_result.accepted_candidate_id} from "
            "output/data/ml_statistical_summary.json; the plot compares retained coverage, selective "
            "accuracy, and the unthresholded accepted-candidate accuracy on the fixed local split."
        )
        probability_quality_caption = (
            "Brier score and negative log likelihood for evaluated candidates from "
            "output/data/ml_statistical_summary.json; lower values indicate better probability quality "
            "within the configured local run, and the accepted candidate is highlighted."
        )
        rank_stability_caption = (
            f"Rank-stability summary for {ml_result.accepted_candidate_id} from "
            "output/data/ml_candidate_rank_stability.json; deterministic local bootstrap resampling "
            "shows how often each evaluated candidate ranks first under the fixed test split."
        )
        training_dynamics_caption = (
            "Configured-training dynamics for evaluated candidates from "
            f"output/data/ml_training_diagnostics.json; {ml_result.accepted_candidate_id} is highlighted while "
            "best-epoch markers and train-test gaps remain bounded to the local run."
        )
    return {
        "stage_caption": stage_caption,
        "score_caption": score_caption,
        "confusion_caption": confusion_caption,
        "closure_caption": closure_caption,
        "per_class_caption": per_class_caption,
        "lifecycle_caption": lifecycle_caption,
        "contact_sheet_caption": contact_sheet_caption,
        "class_balance_caption": class_balance_caption,
        "learning_curve_caption": learning_curve_caption,
        "complexity_caption": complexity_caption,
        "error_caption": error_caption,
        "calibration_caption": calibration_caption,
        "class_metrics_caption": class_metrics_caption,
        "confusion_pairs_caption": confusion_pairs_caption,
        "generalization_caption": generalization_caption,
        "robustness_caption": robustness_caption,
        "probability_caption": probability_caption,
        "bootstrap_caption": bootstrap_caption,
        "paired_caption": paired_caption,
        "selective_caption": selective_caption,
        "probability_quality_caption": probability_quality_caption,
        "rank_stability_caption": rank_stability_caption,
        "training_dynamics_caption": training_dynamics_caption,
        "security_control_caption": security_control_caption,
        "integrity_chain_caption": integrity_chain_caption,
    }
