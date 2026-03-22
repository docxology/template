#!/usr/bin/env python3
"""Sensitivity envelope figure: preset mixture density vs internal_gas sweep (thin orchestrator)."""

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
import insect_composition
import scenarios


def main() -> None:
    fig_dir = _project / "output" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    presets = insect_composition.list_presets()
    y_pos = np.arange(len(presets))
    labels = [p.name.replace("_", " ") for p in presets]

    fig, ax = plt.subplots(figsize=(9, 3.8))
    for i, preset in enumerate(presets):
        rho = scenarios.mixture_density_for_preset(preset)
        lo_g, hi_g = scenarios.internal_gas_export_sweep_bounds(preset)
        env = scenarios.sweep_internal_gas_mass_fraction_interval(preset, lo_g, hi_g)
        ax.plot(
            [env.low, env.high],
            [i, i],
            color="#2c5282",
            linewidth=7,
            solid_capstyle="round",
            alpha=0.85,
            label="internal_gas sweep" if i == 0 else None,
        )
        ax.plot(rho, i, "o", color="#c05621", markersize=9, zorder=3, label="nominal preset" if i == 0 else None)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.axvline(
        fluid_reference.WATER_DENSITY_25C_KG_M3,
        color="#2d3748",
        linestyle="--",
        linewidth=1.2,
        label="fresh water 25 C",
    )
    ax.axvline(
        fluid_reference.SEAWATER_DENSITY_15C_KG_M3,
        color="#4a5568",
        linestyle=":",
        linewidth=1.2,
        label="seawater 15 C (illustrative)",
    )
    ax.set_xlabel(r"Effective mixture density (kg m$^{-3}$)")
    ax.set_title(
        "Interval envelope over internal_gas mass fraction (other compartments scaled; see scenarios)"
    )
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="x", linestyle="-", alpha=0.25)
    fig.tight_layout()
    out = fig_dir / "preset_density_envelopes.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote %s", out)
    print(str(out))


if __name__ == "__main__":
    main()
