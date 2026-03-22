#!/usr/bin/env python3
"""Write JSON/CSV density summaries from `src/` models (thin orchestrator)."""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

_project = Path(
    os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent)
).resolve()
sys.path.insert(0, str(_project / "src"))

try:
    from infrastructure.core.logging_utils import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

import fluid_reference
import ideal_gas
import insect_composition
import scenarios


def main() -> None:
    out_dir = _project / "output" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    dry = ideal_gas.dry_air_density_stp_ideal_kg_m3()
    liquids = fluid_reference.reference_liquids_table()
    presets_payload = []
    for preset in insect_composition.list_presets():
        rho = scenarios.mixture_density_for_preset(preset)
        lo_g, hi_g = scenarios.internal_gas_export_sweep_bounds(preset)
        env = scenarios.sweep_internal_gas_mass_fraction_interval(preset, lo_g, hi_g)
        presets_payload.append(
            {
                "preset": preset.name,
                "description": preset.description,
                "mixture_density_kg_m3": rho,
                "internal_gas_sweep_kg_m3": {"low": env.low, "high": env.high},
            }
        )

    payload = {
        "dry_air_ideal_stp_kg_m3": dry,
        "dry_air_literature_band_kg_m3": {
            "min": ideal_gas.DRY_AIR_DENSITY_STP_LITERATURE_MIN_KG_M3,
            "max": ideal_gas.DRY_AIR_DENSITY_STP_LITERATURE_MAX_KG_M3,
        },
        "reference_liquids": liquids,
        "insect_presets": presets_payload,
    }

    json_path = out_dir / "density_summary.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Wrote %s", json_path)

    csv_path = out_dir / "preset_densities.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["preset", "density_kg_m3", "sweep_low_kg_m3", "sweep_high_kg_m3"])
        for row in presets_payload:
            w.writerow(
                [
                    row["preset"],
                    f"{row['mixture_density_kg_m3']:.4f}",
                    f"{row['internal_gas_sweep_kg_m3']['low']:.4f}",
                    f"{row['internal_gas_sweep_kg_m3']['high']:.4f}",
                ]
            )
    logger.info("Wrote %s", csv_path)

    print(str(json_path))
    print(str(csv_path))


if __name__ == "__main__":
    main()
