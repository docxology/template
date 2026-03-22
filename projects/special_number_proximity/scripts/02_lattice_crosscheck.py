#!/usr/bin/env python3
"""Export brute-force vs scaled-lattice agreement for selected reals (thin orchestrator)."""

from __future__ import annotations

import json
import logging
import math
import os
import sys
from pathlib import Path

project_root = Path(
    os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent)
).resolve()
sys.path.insert(0, str(project_root / "src"))

from diophantine_bounds import (
    dirichlet_pigeonhole_upper_bound,
    max_integer_residual_over_q,
    min_rational_distance_via_scaled_lattice,
)
from rational_distance import min_rational_distance

try:
    from infrastructure.core.logging_utils import get_logger

    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


def main() -> None:
    xs = [
        ("pi", math.pi),
        ("e", math.e),
        ("sqrt2", math.sqrt(2.0)),
        ("neg_pi", -math.pi),
        ("phi", (1.0 + math.sqrt(5.0)) / 2.0),
    ]
    q_list = [1, 8, 40, 120]
    rows: list[dict[str, object]] = []
    for label, x in xs:
        for q_max in q_list:
            brute = min_rational_distance(x, q_max)
            lattice = min_rational_distance_via_scaled_lattice(x, q_max)
            mx = max_integer_residual_over_q(x, q_max)
            bound = dirichlet_pigeonhole_upper_bound(q_max)
            rows.append(
                {
                    "label": label,
                    "q_max": q_max,
                    "brute_delta_Q": brute,
                    "lattice_delta_Q": lattice,
                    "abs_diff": abs(brute - lattice),
                    "min_integer_residual": mx,
                    "dirichlet_bound_residual": bound,
                    "residual_obeyed": bool(mx <= bound + 1e-12),
                }
            )
    out_dir = project_root / "output" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "lattice_crosscheck.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    logger.info("Wrote %s", path)
    print(str(path))


if __name__ == "__main__":
    main()
