"""Compact publication-pairing diagram for transmission bookends."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

_STEPS = ("Render", "Zenodo", "GitHub", "Re-render")


def write_transmission_diagram(output_path: Path, *, current: Mapping[str, str | None]) -> Path:
    """Write a compact PNG flow diagram for the release pairing pipeline."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doi = str(current.get("doi") or "pending")
    pdf_hash = str(current.get("pdf_sha256") or "pending")
    hash_label = pdf_hash[:12] + "…" if len(pdf_hash) > 12 else pdf_hash

    fig, ax = plt.subplots(figsize=(3.5, 2.0), dpi=150)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")

    x_positions = [1.0, 3.5, 6.0, 8.5]
    for index, (label, x_pos) in enumerate(zip(_STEPS, x_positions, strict=True)):
        box = FancyBboxPatch(
            (x_pos - 0.9, 1.6),
            1.8,
            1.0,
            boxstyle="round,pad=0.05",
            linewidth=1.0,
            edgecolor="#1e3a8a",
            facecolor="#e0e7ff",
        )
        ax.add_patch(box)
        ax.text(x_pos, 2.1, label, ha="center", va="center", fontsize=8, fontweight="bold")
        if index < len(_STEPS) - 1:
            ax.annotate(
                "",
                xy=(x_positions[index + 1] - 0.95, 2.1),
                xytext=(x_pos + 0.95, 2.1),
                arrowprops={"arrowstyle": "->", "color": "#334155", "lw": 1.0},
            )

    ax.text(5.0, 0.55, f"DOI: {doi}", ha="center", va="center", fontsize=7)
    ax.text(5.0, 0.15, f"PDF SHA-256: {hash_label}", ha="center", va="center", fontsize=7)

    fig.tight_layout(pad=0.2)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote transmission pairing diagram: %s", output_path)
    return output_path
