#!/usr/bin/env python3
"""Matplotlib overview figures for manuscript (thin orchestrator, headless)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_project = Path(
    os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent)
).resolve()
sys.path.insert(0, str(_project / "src"))

os.environ.setdefault("MPLBACKEND", "Agg")

try:
    from infrastructure.core.logging_utils import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

import matplotlib.pyplot as plt
import numpy as np

import fluid_reference
import ideal_gas
import insect_composition
import scenarios


def main() -> None:
    fig_dir = _project / "output" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    names: list[str] = []
    densities: list[float] = []
    for preset in insect_composition.list_presets():
        names.append(preset.name.replace("_", " "))
        densities.append(scenarios.mixture_density_for_preset(preset))

    liq = fluid_reference.reference_liquids_table()
    names.extend(["water (15 C)", "water (25 C)", "seawater (15 C)", "ethanol (20 C)"])
    densities.extend(
        [
            liq["water"]["density_kg_m3"],
            liq["water_25c"]["density_kg_m3"],
            liq["seawater"]["density_kg_m3"],
            liq["ethanol"]["density_kg_m3"],
        ]
    )
    names.append("dry air (ideal STP)")
    densities.append(ideal_gas.dry_air_density_stp_ideal_kg_m3())

    fig, ax = plt.subplots(figsize=(9, 6.2))
    y_pos = np.arange(len(names))
    n_presets = len(insect_composition.list_presets())
    # Presets, then liquids (fresh x2, seawater, ethanol), then ideal air
    colors = (
        ["#2b6cb0"] * n_presets
        + ["#3182ce", "#3182ce", "#2c7a7b", "#805ad5"]
        + ["#718096"]
    )
    if len(colors) != len(densities):
        colors = ["#2c5282"] * len(densities)
    ax.barh(y_pos, densities, color=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel(r"Density (kg m$^{-3}$)")
    ax.set_title("Illustrative preset densities vs reference fluids and dry air (ideal STP)")
    xmax = max(densities) * 1.06
    ax.set_xlim(0, xmax)
    for i, d in enumerate(densities):
        ax.text(
            d + xmax * 0.01,
            i,
            f"{d:.1f}",
            va="center",
            fontsize=8,
            color="#2d3748",
        )
    ax.axvline(
        fluid_reference.WATER_DENSITY_25C_KG_M3,
        color="#c05621",
        linestyle="--",
        linewidth=1,
        label="Water 25 C ref.",
    )
    ax.legend(loc="lower right")
    fig.tight_layout()
    out = fig_dir / "density_overview.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote %s", out)
    print(str(out))


if __name__ == "__main__":
    main()
