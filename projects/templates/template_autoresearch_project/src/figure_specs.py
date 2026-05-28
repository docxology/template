"""Authoritative figure specifications for AutoResearch registry parity."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import figures_ml, figures_process
from .figures_security import write_security_control_matrix_figure, write_security_integrity_chain_figure
from .json_coerce import mapping
from .ml_task import MLTaskResult
from .models import AutoResearchLoopResult


@dataclass(frozen=True)
class FigureRenderContext:
    """Shared inputs for registry-driven figure rendering."""

    project_root: Path
    figures_dir: Path
    loop_result: AutoResearchLoopResult | None
    ml_result: MLTaskResult
    diagnostics: dict[str, Any]


@dataclass(frozen=True)
class FigureDispatchEntry:
    """Registry key binding with loop-only scope and output filename."""

    filename: str
    loop_only: bool
    render: Callable[[FigureRenderContext], Path]
    security_channel: bool = False


FIGURE_METHODS: dict[str, str] = {
    "fig:autoresearch_stage_matrix": "Horizontal count summary from final loop metrics.",
    "fig:ml_candidate_scores": "Lollipop accuracy comparison with Wilson interval error bars and direct labels.",
    "fig:ml_confusion_matrix": "Row-normalized heatmap with cell counts and row percentages.",
    "fig:autoresearch_closure_flow": "File-backed process-flow diagram from final loop state.",
    "fig:ml_per_class_accuracy": "Per-class accuracy bars computed from the confusion matrix diagonal.",
    "fig:ml_learning_curves": "Epoch-level held-out accuracy lines with accepted best-epoch marker.",
    "fig:ml_complexity_accuracy": "Log-parameter scatter plot against held-out accuracy.",
    "fig:mnist_error_examples": "Deterministic grid of the first accepted-candidate misclassifications.",
    "fig:ml_calibration_reliability": "Reliability curve with confidence-bin support histogram.",
    "fig:ml_classification_metrics_heatmap": "Per-class precision, recall, and F1 heatmap.",
    "fig:ml_confusion_pairs": "Ranked off-diagonal confusion-pair bars with true-class error rates.",
    "fig:ml_generalization_gap": "Grouped train/test accuracy and loss bars by evaluated candidate.",
    "fig:ml_robustness_matrix": "Candidate-by-transform accuracy heatmap for deterministic perturbations.",
    "fig:ml_probability_margin_distribution": "Confidence and margin histograms split by correctness.",
    "fig:ml_bootstrap_intervals": "Horizontal percentile-bootstrap interval plot.",
    "fig:ml_paired_correctness": "Matched accepted-versus-baseline correctness heatmap.",
    "fig:ml_selective_accuracy": "Confidence-threshold coverage and selective-accuracy line chart.",
    "fig:ml_probability_quality": "Brier score and negative-log-likelihood bar comparison.",
    "fig:ml_training_dynamics": "Final and best-epoch accuracy bars plus train-test gap bars.",
    "fig:ml_candidate_rank_stability": "Bootstrap top-rank frequency and mean-rank comparison.",
    "fig:autoresearch_candidate_lifecycle": "Candidate lifecycle status-count bar chart.",
    "fig:mnist_subset_contact_sheet": "Class-balanced contact sheet from fixed local MNIST arrays.",
    "fig:mnist_class_balance": "Grouped train/test class-count bars from the local MNIST fixture.",
    "fig:autoresearch_security_control_matrix": "Structured control matrix from local threat-model controls.",
    "fig:autoresearch_integrity_chain": "Local checksum attestation chain with checked, missing, and mismatch counts.",
}

ALL_FIGURE_LABELS: tuple[str, ...] = tuple(FIGURE_METHODS.keys())


def _require_loop_result(ctx: FigureRenderContext) -> AutoResearchLoopResult:
    if ctx.loop_result is None:
        raise ValueError("loop_result is required for loop-only figures")
    return ctx.loop_result


def _load_output_json(ctx: FigureRenderContext, relative: str) -> dict[str, Any]:
    path = ctx.project_root / relative
    if not path.is_file():
        return {}
    return mapping(json.loads(path.read_text(encoding="utf-8")))


def _render_security_control(ctx: FigureRenderContext) -> Path:
    return write_security_control_matrix_figure(
        ctx.figures_dir,
        _load_output_json(ctx, "output/data/autoresearch_threat_model.json"),
    )


def _render_integrity_chain(ctx: FigureRenderContext) -> Path:
    return write_security_integrity_chain_figure(
        ctx.figures_dir,
        _load_output_json(ctx, "output/data/autoresearch_integrity_attestation.json"),
    )


def build_figure_dispatch() -> dict[str, FigureDispatchEntry]:
    """Build the registry-driven figure dispatch table from specs."""
    return {
        "fig:autoresearch_stage_matrix": FigureDispatchEntry(
            "autoresearch_stage_matrix.png",
            True,
            lambda ctx: figures_process.write_stage_matrix_figure(ctx.figures_dir, _require_loop_result(ctx)),
        ),
        "fig:autoresearch_closure_flow": FigureDispatchEntry(
            "autoresearch_closure_flow.png",
            True,
            lambda ctx: figures_process.write_closure_flow_figure(ctx.figures_dir, _require_loop_result(ctx)),
        ),
        "fig:ml_candidate_scores": FigureDispatchEntry(
            "ml_candidate_scores.png",
            False,
            lambda ctx: figures_ml.write_ml_candidate_scores_figure(
                ctx.figures_dir, ctx.ml_result, ctx.diagnostics["candidate_intervals"]
            ),
        ),
        "fig:ml_confusion_matrix": FigureDispatchEntry(
            "ml_confusion_matrix.png",
            False,
            lambda ctx: figures_ml.write_ml_confusion_matrix_figure(ctx.figures_dir, ctx.ml_result),
        ),
        "fig:ml_per_class_accuracy": FigureDispatchEntry(
            "ml_per_class_accuracy.png",
            False,
            lambda ctx: figures_ml.write_ml_per_class_accuracy_figure(ctx.figures_dir, ctx.ml_result),
        ),
        "fig:ml_learning_curves": FigureDispatchEntry(
            "ml_learning_curves.png",
            False,
            lambda ctx: figures_ml.write_ml_learning_curve_figure(ctx.figures_dir, ctx.ml_result),
        ),
        "fig:ml_complexity_accuracy": FigureDispatchEntry(
            "ml_complexity_accuracy.png",
            False,
            lambda ctx: figures_ml.write_ml_complexity_accuracy_figure(ctx.figures_dir, ctx.ml_result),
        ),
        "fig:mnist_error_examples": FigureDispatchEntry(
            "mnist_error_examples.png",
            False,
            lambda ctx: figures_ml.write_mnist_error_examples_figure(ctx.project_root, ctx.figures_dir, ctx.ml_result),
        ),
        "fig:ml_calibration_reliability": FigureDispatchEntry(
            "ml_calibration_reliability.png",
            False,
            lambda ctx: figures_ml.write_ml_calibration_reliability_figure(
                ctx.figures_dir,
                ctx.diagnostics["calibration_report"],
                ctx.diagnostics["calibration_bin_intervals"],
            ),
        ),
        "fig:ml_classification_metrics_heatmap": FigureDispatchEntry(
            "ml_classification_metrics_heatmap.png",
            False,
            lambda ctx: figures_ml.write_ml_classification_metrics_heatmap(
                ctx.figures_dir, ctx.diagnostics["classification_diagnostics"]
            ),
        ),
        "fig:ml_confusion_pairs": FigureDispatchEntry(
            "ml_confusion_pairs.png",
            False,
            lambda ctx: figures_ml.write_ml_confusion_pairs_figure(
                ctx.figures_dir, ctx.diagnostics["classification_diagnostics"]
            ),
        ),
        "fig:ml_generalization_gap": FigureDispatchEntry(
            "ml_generalization_gap.png",
            False,
            lambda ctx: figures_ml.write_ml_generalization_gap_figure(
                ctx.figures_dir, ctx.diagnostics["classification_diagnostics"]
            ),
        ),
        "fig:ml_robustness_matrix": FigureDispatchEntry(
            "ml_robustness_matrix.png",
            False,
            lambda ctx: figures_ml.write_ml_robustness_matrix_figure(
                ctx.figures_dir, ctx.diagnostics["robustness_report"]
            ),
        ),
        "fig:ml_probability_margin_distribution": FigureDispatchEntry(
            "ml_probability_margin_distribution.png",
            False,
            lambda ctx: figures_ml.write_ml_probability_margin_figure(
                ctx.figures_dir, ctx.diagnostics["probability_diagnostics"]
            ),
        ),
        "fig:ml_bootstrap_intervals": FigureDispatchEntry(
            "ml_bootstrap_intervals.png",
            False,
            lambda ctx: figures_ml.write_ml_bootstrap_intervals_figure(
                ctx.figures_dir, ctx.diagnostics["bootstrap_intervals"]
            ),
        ),
        "fig:ml_paired_correctness": FigureDispatchEntry(
            "ml_paired_correctness.png",
            False,
            lambda ctx: figures_ml.write_ml_paired_correctness_figure(
                ctx.figures_dir, ctx.diagnostics["paired_comparison"]
            ),
        ),
        "fig:ml_selective_accuracy": FigureDispatchEntry(
            "ml_selective_accuracy.png",
            False,
            lambda ctx: figures_ml.write_ml_selective_accuracy_figure(
                ctx.figures_dir, ctx.diagnostics["statistical_summary"]
            ),
        ),
        "fig:ml_probability_quality": FigureDispatchEntry(
            "ml_probability_quality.png",
            False,
            lambda ctx: figures_ml.write_ml_probability_quality_figure(
                ctx.figures_dir, ctx.diagnostics["statistical_summary"]
            ),
        ),
        "fig:ml_training_dynamics": FigureDispatchEntry(
            "ml_training_dynamics.png",
            False,
            lambda ctx: figures_ml.write_ml_training_dynamics_figure(
                ctx.figures_dir, ctx.diagnostics["training_diagnostics"]
            ),
        ),
        "fig:ml_candidate_rank_stability": FigureDispatchEntry(
            "ml_candidate_rank_stability.png",
            False,
            lambda ctx: figures_ml.write_ml_candidate_rank_stability_figure(
                ctx.figures_dir, ctx.diagnostics["candidate_rank_stability"]
            ),
        ),
        "fig:autoresearch_candidate_lifecycle": FigureDispatchEntry(
            "autoresearch_candidate_lifecycle.png",
            False,
            lambda ctx: figures_process.write_candidate_lifecycle_figure(ctx.figures_dir, ctx.ml_result),
        ),
        "fig:mnist_class_balance": FigureDispatchEntry(
            "mnist_class_balance.png",
            False,
            lambda ctx: figures_ml.write_mnist_class_balance_figure(ctx.figures_dir, ctx.diagnostics["class_balance"]),
        ),
        "fig:mnist_subset_contact_sheet": FigureDispatchEntry(
            "mnist_subset_contact_sheet.png",
            False,
            lambda ctx: figures_ml.write_mnist_subset_contact_sheet_figure(
                ctx.project_root, ctx.figures_dir, ctx.ml_result
            ),
        ),
        "fig:autoresearch_security_control_matrix": FigureDispatchEntry(
            "autoresearch_security_control_matrix.png",
            False,
            _render_security_control,
            security_channel=True,
        ),
        "fig:autoresearch_integrity_chain": FigureDispatchEntry(
            "autoresearch_integrity_chain.png",
            False,
            _render_integrity_chain,
            security_channel=True,
        ),
    }


FIGURE_DISPATCH = build_figure_dispatch()


def render_figure_batch(
    ctx: FigureRenderContext,
    *,
    include_loop_only: bool,
    include_security: bool = False,
) -> list[Path]:
    """Render figures selected by registry scope."""
    paths: list[Path] = []
    for entry in FIGURE_DISPATCH.values():
        if entry.security_channel and not include_security:
            continue
        if entry.loop_only is not include_loop_only:
            continue
        paths.append(entry.render(ctx))
    return paths


def render_all_figures(ctx: FigureRenderContext, *, include_security: bool = False) -> list[Path]:
    """Render every registered figure (loop-bound and ML-bound)."""
    loop_paths = render_figure_batch(ctx, include_loop_only=True)
    ml_paths = render_figure_batch(ctx, include_loop_only=False, include_security=include_security)
    return loop_paths + ml_paths


def render_security_figures(ctx: FigureRenderContext) -> list[Path]:
    """Render security figures after threat-model and attestation JSON exist."""
    return [
        FIGURE_DISPATCH["fig:autoresearch_security_control_matrix"].render(ctx),
        FIGURE_DISPATCH["fig:autoresearch_integrity_chain"].render(ctx),
    ]


def build_figure_registry_records(captions: dict[str, str]) -> dict[str, dict[str, object]]:
    """Build registry records from dispatch filenames and static per-label metadata."""
    from .figure_registry_metadata import FIGURE_RECORD_SPECS

    records: dict[str, dict[str, object]] = {}
    for index, label in enumerate(ALL_FIGURE_LABELS):
        spec = FIGURE_RECORD_SPECS[label]
        dispatch = FIGURE_DISPATCH[label]
        records[label] = {
            "figure_id": f"figure_{index:03d}",
            "filename": dispatch.filename,
            "caption": captions[spec.caption_field],
            "label": label,
            "section": spec.section,
            "width": spec.width,
            "placement": spec.placement,
            "generated_by": spec.generated_by,
            "metadata": dict(spec.metadata),
        }
    return records


__all__ = [
    "ALL_FIGURE_LABELS",
    "FIGURE_DISPATCH",
    "FIGURE_METHODS",
    "FigureDispatchEntry",
    "FigureRenderContext",
    "build_figure_dispatch",
    "build_figure_registry_records",
    "render_all_figures",
    "render_figure_batch",
    "render_security_figures",
]
