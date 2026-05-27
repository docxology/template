"""Figure registry metadata for generated AutoResearch figures."""

from __future__ import annotations

from .figure_registry_contract import finalize_figure_registry
from .ml_task import MLTaskResult
from .models import AutoResearchLoopResult


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def figure_registry_payload(
    result: AutoResearchLoopResult | None = None,
    ml_result: MLTaskResult | None = None,
) -> dict[str, dict[str, object]]:
    """Return figure registry metadata for generated AutoResearch figures."""
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
    records: dict[str, dict[str, object]] = {
        "fig:autoresearch_stage_matrix": {
            "figure_id": "figure_000",
            "filename": "autoresearch_stage_matrix.png",
            "caption": stage_caption,
            "label": "fig:autoresearch_stage_matrix",
            "section": "Results",
            "width": "0.8\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_stage_matrix_figure",
            "metadata": {
                "source": "output/data/autoresearch_loop.json",
                "alt_text": "Horizontal bar chart showing configured stages, supported claims, and required artifacts.",
                "claim_boundary": "Readiness artifacts summarize local validation only; publication approval is human.",
            },
        },
        "fig:ml_candidate_scores": {
            "figure_id": "figure_001",
            "filename": "ml_candidate_scores.png",
            "caption": score_caption,
            "label": "fig:ml_candidate_scores",
            "section": "Results",
            "width": "0.8\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_candidate_scores_figure",
            "metadata": {
                "source": "output/data/ml_candidate_intervals.json",
                "source_results": "output/data/ml_task_results.json",
                "alt_text": "Lollipop chart comparing baseline and evaluated candidate accuracies with Wilson interval error bars.",
                "claim_boundary": "Scores apply only to the fixed local subset and configured candidates.",
            },
        },
        "fig:ml_confusion_matrix": {
            "figure_id": "figure_002",
            "filename": "ml_confusion_matrix.png",
            "caption": confusion_caption,
            "label": "fig:ml_confusion_matrix",
            "section": "Results",
            "width": "0.72\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_confusion_matrix_figure",
            "metadata": {
                "source": "output/data/ml_confusion_matrix.csv",
                "alt_text": "Ten-by-ten confusion matrix for the accepted candidate on the local test split.",
                "claim_boundary": "Confusion counts diagnose this run only and do not imply full-dataset generalization.",
            },
        },
        "fig:autoresearch_closure_flow": {
            "figure_id": "figure_003",
            "filename": "autoresearch_closure_flow.png",
            "caption": closure_caption,
            "label": "fig:autoresearch_closure_flow",
            "section": "Results",
            "width": "0.95\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_closure_flow_figure",
            "metadata": {
                "source": "output/data/autoresearch_loop.json",
                "alt_text": "Flow diagram linking program, proposals, evaluation, ledgers, claims, manuscript, readiness, and review.",
                "claim_boundary": "The workflow is file-backed and inspectable but not self-approving.",
            },
        },
        "fig:ml_per_class_accuracy": {
            "figure_id": "figure_004",
            "filename": "ml_per_class_accuracy.png",
            "caption": per_class_caption,
            "label": "fig:ml_per_class_accuracy",
            "section": "Results",
            "width": "0.78\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_per_class_accuracy_figure",
            "metadata": {
                "source": "output/data/ml_confusion_matrix.csv",
                "alt_text": "Bar chart of accepted-candidate accuracy for each true digit class.",
                "claim_boundary": "Per-class values diagnose this local split only and do not certify robustness.",
            },
        },
        "fig:ml_learning_curves": {
            "figure_id": "figure_007",
            "filename": "ml_learning_curves.png",
            "caption": learning_curve_caption,
            "label": "fig:ml_learning_curves",
            "section": "Results",
            "width": "0.82\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_learning_curve_figure",
            "metadata": {
                "source": "output/data/ml_training_history.csv",
                "alt_text": "Line chart of held-out accuracy by epoch for each evaluated candidate.",
                "claim_boundary": "Learning curves diagnose configured training only, not convergence in general.",
            },
        },
        "fig:ml_complexity_accuracy": {
            "figure_id": "figure_008",
            "filename": "ml_complexity_accuracy.png",
            "caption": complexity_caption,
            "label": "fig:ml_complexity_accuracy",
            "section": "Results",
            "width": "0.78\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_complexity_accuracy_figure",
            "metadata": {
                "source": "output/data/ml_task_results.json",
                "alt_text": "Scatter plot comparing parameter count and held-out accuracy.",
                "claim_boundary": "The plot compares this bounded candidate set and does not infer a scaling law.",
            },
        },
        "fig:mnist_error_examples": {
            "figure_id": "figure_009",
            "filename": "mnist_error_examples.png",
            "caption": error_caption,
            "label": "fig:mnist_error_examples",
            "section": "Results",
            "width": "0.82\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_mnist_error_examples_figure",
            "metadata": {
                "source": "output/data/ml_error_examples.json",
                "source_images": "data/mnist_small.npz",
                "alt_text": "Grid of accepted-candidate misclassified test examples with true and predicted labels.",
                "claim_boundary": "Examples are qualitative diagnostics for this run, not an error taxonomy.",
            },
        },
        "fig:ml_calibration_reliability": {
            "figure_id": "figure_012",
            "filename": "ml_calibration_reliability.png",
            "caption": calibration_caption,
            "label": "fig:ml_calibration_reliability",
            "section": "Results",
            "width": "0.82\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_calibration_reliability_figure",
            "metadata": {
                "source": "output/data/ml_calibration_report.json",
                "alt_text": "Reliability curve with accepted-candidate confidence-bin counts.",
                "claim_boundary": "Calibration values describe the fixed local split only.",
            },
        },
        "fig:ml_classification_metrics_heatmap": {
            "figure_id": "figure_013",
            "filename": "ml_classification_metrics_heatmap.png",
            "caption": class_metrics_caption,
            "label": "fig:ml_classification_metrics_heatmap",
            "section": "Results",
            "width": "0.76\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_classification_metrics_heatmap",
            "metadata": {
                "source": "output/data/ml_classification_diagnostics.json",
                "alt_text": "Heatmap of per-class precision, recall, and F1 for the accepted candidate.",
                "claim_boundary": "Class metrics diagnose this run only and are not full-dataset estimates.",
            },
        },
        "fig:ml_confusion_pairs": {
            "figure_id": "figure_014",
            "filename": "ml_confusion_pairs.png",
            "caption": confusion_pairs_caption,
            "label": "fig:ml_confusion_pairs",
            "section": "Results",
            "width": "0.82\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_confusion_pairs_figure",
            "metadata": {
                "source": "output/data/ml_classification_diagnostics.json",
                "alt_text": "Horizontal bar chart of the most frequent non-diagonal confusion pairs.",
                "claim_boundary": "Pair counts identify local error cases and are not a general taxonomy.",
            },
        },
        "fig:ml_generalization_gap": {
            "figure_id": "figure_015",
            "filename": "ml_generalization_gap.png",
            "caption": generalization_caption,
            "label": "fig:ml_generalization_gap",
            "section": "Results",
            "width": "0.82\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_generalization_gap_figure",
            "metadata": {
                "source": "output/data/ml_classification_diagnostics.json",
                "alt_text": "Grouped bars comparing train and test accuracy and loss by candidate.",
                "claim_boundary": "Gaps are local bounded-loop diagnostics, not convergence guarantees.",
            },
        },
        "fig:ml_robustness_matrix": {
            "figure_id": "figure_016",
            "filename": "ml_robustness_matrix.png",
            "caption": robustness_caption,
            "label": "fig:ml_robustness_matrix",
            "section": "Results",
            "width": "0.84\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_robustness_matrix_figure",
            "metadata": {
                "source": "output/data/ml_robustness_report.json",
                "alt_text": "Heatmap of candidate accuracy under identity, shift, and low-contrast transforms.",
                "claim_boundary": "Deterministic perturbations are a smoke test and do not certify robustness.",
            },
        },
        "fig:ml_probability_margin_distribution": {
            "figure_id": "figure_017",
            "filename": "ml_probability_margin_distribution.png",
            "caption": probability_caption,
            "label": "fig:ml_probability_margin_distribution",
            "section": "Results",
            "width": "0.82\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_probability_margin_figure",
            "metadata": {
                "source": "output/data/ml_probability_diagnostics.json",
                "source_predictions": "output/data/ml_prediction_records.json",
                "alt_text": "Two histograms of accepted-candidate confidence and prediction margin by correctness.",
                "claim_boundary": "Distributions are descriptive diagnostics for the fixed local test split.",
            },
        },
        "fig:ml_bootstrap_intervals": {
            "figure_id": "figure_018",
            "filename": "ml_bootstrap_intervals.png",
            "caption": bootstrap_caption,
            "label": "fig:ml_bootstrap_intervals",
            "section": "Results",
            "width": "0.78\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_bootstrap_intervals_figure",
            "metadata": {
                "source": "output/data/ml_bootstrap_intervals.json",
                "alt_text": "Horizontal interval chart for accepted-candidate accuracy and macro F1.",
                "claim_boundary": "Bootstrap intervals summarize local test-set resampling only.",
            },
        },
        "fig:ml_paired_correctness": {
            "figure_id": "figure_019",
            "filename": "ml_paired_correctness.png",
            "caption": paired_caption,
            "label": "fig:ml_paired_correctness",
            "section": "Results",
            "width": "0.66\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_paired_correctness_figure",
            "metadata": {
                "source": "output/data/ml_paired_comparison.json",
                "alt_text": "Two-by-two heatmap of baseline and accepted-candidate correctness on matched examples.",
                "claim_boundary": "Matched comparison is limited to the fixed local test split.",
            },
        },
        "fig:ml_selective_accuracy": {
            "figure_id": "figure_020",
            "filename": "ml_selective_accuracy.png",
            "caption": selective_caption,
            "label": "fig:ml_selective_accuracy",
            "section": "Results",
            "width": "0.76\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_selective_accuracy_figure",
            "metadata": {
                "source": "output/data/ml_statistical_summary.json",
                "alt_text": "Line chart comparing coverage, selective accuracy, and overall accuracy by confidence threshold.",
                "claim_boundary": "Selective accuracy describes thresholded predictions on the fixed local split only.",
            },
        },
        "fig:ml_probability_quality": {
            "figure_id": "figure_021",
            "filename": "ml_probability_quality.png",
            "caption": probability_quality_caption,
            "label": "fig:ml_probability_quality",
            "section": "Results",
            "width": "0.82\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_probability_quality_figure",
            "metadata": {
                "source": "output/data/ml_statistical_summary.json",
                "alt_text": "Paired horizontal bar charts of Brier score and negative log likelihood with the accepted candidate highlighted.",
                "claim_boundary": "Probability-quality metrics compare the configured evaluated candidates only.",
            },
        },
        "fig:ml_training_dynamics": {
            "figure_id": "figure_022",
            "filename": "ml_training_dynamics.png",
            "caption": training_dynamics_caption,
            "label": "fig:ml_training_dynamics",
            "section": "Results",
            "width": "0.84\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_training_dynamics_figure",
            "metadata": {
                "source": "output/data/ml_training_diagnostics.json",
                "source_history": "output/data/ml_training_history.csv",
                "alt_text": "Two-panel chart showing final versus best held-out accuracy and train-test accuracy gaps by candidate.",
                "claim_boundary": "Training dynamics diagnose this configured deterministic run only.",
            },
        },
        "fig:ml_candidate_rank_stability": {
            "figure_id": "figure_026",
            "filename": "ml_candidate_rank_stability.png",
            "caption": rank_stability_caption,
            "label": "fig:ml_candidate_rank_stability",
            "section": "Results",
            "width": "0.82\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_ml_candidate_rank_stability_figure",
            "metadata": {
                "source": "output/data/ml_candidate_rank_stability.json",
                "source_results": "output/data/ml_task_results.json",
                "alt_text": "Two-panel chart of candidate top-rank frequency and mean rank under deterministic bootstrap resampling.",
                "claim_boundary": "Rank stability describes local resampling behavior, not model-selection certainty.",
            },
        },
        "fig:autoresearch_candidate_lifecycle": {
            "figure_id": "figure_010",
            "filename": "autoresearch_candidate_lifecycle.png",
            "caption": lifecycle_caption,
            "label": "fig:autoresearch_candidate_lifecycle",
            "section": "Results",
            "width": "0.78\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_candidate_lifecycle_figure",
            "metadata": {
                "source": "output/data/ml_candidate_ledger.json",
                "alt_text": "Bar chart of proposed, evaluated, accepted, rejected, and deferred candidate counts.",
                "claim_boundary": "Lifecycle counts describe bounded orchestration, not autonomous approval.",
            },
        },
        "fig:mnist_class_balance": {
            "figure_id": "figure_023",
            "filename": "mnist_class_balance.png",
            "caption": class_balance_caption,
            "label": "fig:mnist_class_balance",
            "section": "Methodology",
            "width": "0.78\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_mnist_class_balance_figure",
            "metadata": {
                "source": "output/data/ml_class_balance.json",
                "source_fixture": "data/mnist_small.npz",
                "source_provenance": "data/mnist_small_provenance.json",
                "alt_text": "Grouped bar chart showing train and test example counts for each digit class.",
                "claim_boundary": "Class counts describe the local fixed fixture and are not population statistics.",
            },
        },
        "fig:mnist_subset_contact_sheet": {
            "figure_id": "figure_011",
            "filename": "mnist_subset_contact_sheet.png",
            "caption": contact_sheet_caption,
            "label": "fig:mnist_subset_contact_sheet",
            "section": "Methodology",
            "width": "0.78\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_mnist_subset_contact_sheet_figure",
            "metadata": {
                "source": "data/mnist_small.npz",
                "source_provenance": "data/mnist_small_provenance.json",
                "alt_text": "Two-row grid with one local handwritten digit example for each class zero through nine.",
                "claim_boundary": "The sheet illustrates the local fixed subset and is not a statistical sample claim.",
            },
        },
        "fig:autoresearch_security_control_matrix": {
            "figure_id": "figure_024",
            "filename": "autoresearch_security_control_matrix.png",
            "caption": security_control_caption,
            "label": "fig:autoresearch_security_control_matrix",
            "section": "Methodology",
            "width": "0.84\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_security_control_matrix_figure",
            "metadata": {
                "source": "output/data/autoresearch_threat_model.json",
                "alt_text": "Matrix of local security controls mapped to framework-inspired evidence surfaces and status.",
                "claim_boundary": "Controls are local research-artifact safeguards, not production security certification.",
            },
        },
        "fig:autoresearch_integrity_chain": {
            "figure_id": "figure_025",
            "filename": "autoresearch_integrity_chain.png",
            "caption": integrity_chain_caption,
            "label": "fig:autoresearch_integrity_chain",
            "section": "Results",
            "width": "0.84\\textwidth",
            "placement": "h",
            "generated_by": "src.figures.write_security_integrity_chain_figure",
            "metadata": {
                "source": "output/data/autoresearch_integrity_attestation.json",
                "source_inventory": "output/data/autoresearch_supply_chain_inventory.json",
                "alt_text": "Process-chain diagram and bar chart summarizing checked, missing, and mismatched local artifact records.",
                "claim_boundary": "Integrity checks are local SHA-256 observations and are not externally signed provenance.",
            },
        },
    }
    return finalize_figure_registry(records)
