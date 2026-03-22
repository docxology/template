"""Smoke tests for analysis script logic (import from ``scripts/``)."""

from __future__ import annotations

import sys
from pathlib import Path


def test_run_proximity_study_beta_and_reference_summary() -> None:
    project_root = Path(__file__).resolve().parents[1]
    scripts_dir = str(project_root / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import proximity_monte_carlo as pmc

    s = pmc.run_proximity_study(
        project_root,
        seed=3,
        q_max=8,
        n_uniform=12,
        n_quadratic=4,
        n_beta=6,
        beta_a=1.0,
        beta_b=1.0,
    )
    assert s["reference_combined_n"] == 22
    assert s["reference_summary"]["n"] == 22.0
    assert s["reference_summary"]["median"] >= 0.0
    assert s["n_beta"] == 6
    assert "min_q_squared_error" in s["constants"][0]
    assert "p05" in s["reference_summary"]
