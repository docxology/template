"""Figure generation for the AutoResearch loop."""

from __future__ import annotations

from pathlib import Path

from .ml_task import MLTaskResult
from .models import AutoResearchLoopResult


def write_stage_matrix_figure(figures_dir: Path, result: AutoResearchLoopResult) -> Path:
    """Write the stage matrix bar chart."""
    from matplotlib import pyplot as plt

    path = figures_dir / "autoresearch_stage_matrix.png"
    labels = ("stages", "claims", "artifacts")
    values = (
        len(result.stage_results),
        result.supported_claim_count,
        len(result.config.required_artifacts),
    )
    colors = ("#2563eb", "#0f766e", "#7c2d12")
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    ax.barh(labels, values, color=colors)
    ax.set_title("AutoResearch readiness matrix")
    ax.set_xlabel("count")
    ax.set_xlim(0, max(values) + 1)
    for index, value in enumerate(values):
        ax.text(value + 0.1, index, str(value), va="center", fontsize=10)
    ax.grid(axis="x", color="#d4d4d8", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_ml_candidate_scores_figure(figures_dir: Path, result: MLTaskResult) -> Path:
    """Write a bar chart comparing the baseline and evaluated candidates."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_candidate_scores.png"
    evaluated = [candidate for candidate in result.candidates if candidate.accuracy is not None]
    labels = ["baseline", *(candidate.identifier.replace("exp-", "") for candidate in evaluated)]
    values = [result.baseline.accuracy, *(float(candidate.accuracy or 0.0) for candidate in evaluated)]
    colors = ["#52525b", *("#0f766e" if candidate.status == "accepted" else "#2563eb" for candidate in evaluated)]
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    ax.bar(labels, values, color=colors)
    ax.set_title("Bounded ML-loop candidate accuracy")
    ax.set_ylabel("held-out accuracy")
    ax.set_ylim(0.0, 1.05)
    ax.grid(axis="y", color="#d4d4d8", linewidth=0.8)
    ax.set_axisbelow(True)
    for index, value in enumerate(values):
        ax.text(index, value + 0.02, f"{value:.3f}", ha="center", va="bottom", fontsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.autofmt_xdate(rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def figure_registry_payload() -> dict[str, dict[str, object]]:
    """Return figure registry metadata for generated AutoResearch figures."""
    return {
        "fig:autoresearch_stage_matrix": {
            "figure_id": "figure_000",
            "filename": "autoresearch_stage_matrix.png",
            "caption": "Deterministic AutoResearch stage, claim, and required-artifact counts.",
            "label": "fig:autoresearch_stage_matrix",
            "section": "Results",
            "width": "0.8\\textwidth",
            "placement": "h",
            "generated_by": "src.loop.run_autoresearch_loop",
            "metadata": {
                "source": "output/data/autoresearch_loop.json",
            },
        },
        "fig:ml_candidate_scores": {
            "figure_id": "figure_001",
            "filename": "ml_candidate_scores.png",
            "caption": "Held-out accuracy for the majority-class baseline and bounded ML-loop candidates.",
            "label": "fig:ml_candidate_scores",
            "section": "Results",
            "width": "0.8\\textwidth",
            "placement": "h",
            "generated_by": "src.ml_task.run_bounded_ml_task",
            "metadata": {
                "source": "output/data/ml_task_results.json",
            },
        },
    }
