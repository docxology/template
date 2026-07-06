"""Schema constants and tolerances for toy sweep artifacts."""

from __future__ import annotations

TOY_SWEEP_SCHEMA = "template_active_inference.toy_sweep_tracks.v1"
ASSUMPTION_INDEX_SCHEMA = "template_active_inference.analytical_assumption_index.v1"
EXPECTED_ASSUMPTION_EQUATIONS = {
    "eq:entangled_joint",
    "joint_entropy",
    "marginal_entropy",
    "mi_closed_form",
    "eq:ising_spin_correlation",
    "posterior_correlation",
    "same_state_probability",
}
OBSERVABLE_RESIDUAL_TOLERANCE = 1e-9
