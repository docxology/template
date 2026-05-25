"""Figure generation for the AutoResearch loop."""

from __future__ import annotations

from pathlib import Path

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


def figure_registry_payload() -> dict[str, dict[str, object]]:
    """Return figure registry metadata for the stage matrix."""
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
        }
    }
