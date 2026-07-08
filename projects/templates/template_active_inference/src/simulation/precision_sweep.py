"""Closed-form precision (gamma) sweep over the T-maze policy posterior.

Active Inference selects policies from the softmax of the negative Expected Free
Energy, scaled by the precision (inverse temperature) ``gamma``:

    q(pi) = softmax(-gamma * G(pi))

As ``gamma`` increases the posterior sharpens toward the EFE-minimising
policies: the Shannon entropy ``H[q]`` decreases monotonically and the
probability mass placed on the EFE-optimal policy *set* increases monotonically
toward one. This module reuses :func:`simulation.efe_decomposition.decompose_all_policies`
for the closed-form ``G(pi)`` and computes the posterior, its entropy, the
argmax-selected policy, and the optimal-set mass on a deterministic ``gamma``
grid -- no sampling, byte-deterministic.

Honest note on the canonical T-maze: the goal state is absorbing, so the second
action is behaviourally irrelevant once the goal is reached. Two policies tie at
the EFE minimum (``00`` and ``01``). The posterior therefore concentrates on the
*optimal set*, not a single policy: ``H[q]`` saturates at ``ln(|optimal set|)``
(here ``ln 2``) rather than zero, and ``qmax`` saturates at ``1/|optimal set|``.
"Selection becomes deterministic" is consequently defined as the optimal-set
mass crossing a high threshold (default 0.99), which is the faithful statement
for a model with tied optima -- mirroring the EFE module's discipline of
asserting only what the closed form supports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from simulation.efe_decomposition import decompose_all_policies

ArrayF = NDArray[np.float64]

# Default precision grid: 0..16 inclusive in 33 points (step 0.5). Chosen so the
# 0.99 optimal-set-mass crossing for the canonical T-maze lands on a grid point.
DEFAULT_GAMMA_MAX: float = 16.0
DEFAULT_GAMMA_GRID_POINTS: int = 33
# Optimal-set tie tolerance (shared scale with EFE_IDENTITY_ATOL).
OPTIMAL_TIE_ATOL: float = 1e-9
# Mass threshold defining "deterministic" selection onto the optimal set.
SELECTION_MASS_THRESHOLD: float = 0.99


def _softmax(logits: ArrayF) -> ArrayF:
    shifted = logits - np.max(logits)
    weights = np.exp(shifted)
    return cast(ArrayF, weights / weights.sum())


def _entropy(distribution: ArrayF) -> float:
    """Shannon entropy in nats, ignoring zero-probability outcomes."""
    p = np.asarray(distribution, dtype=np.float64).reshape(-1)
    nonzero = p[p > 0.0]
    return float(-np.sum(nonzero * np.log(nonzero)))


@dataclass(frozen=True)
class PrecisionPoint:
    """Policy-posterior summary at one precision value."""

    gamma: float
    entropy: float
    selected_policy: tuple[int, ...]
    selected_prob: float
    optimal_set_mass: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "gamma": self.gamma,
            "entropy": self.entropy,
            "selected_policy": list(self.selected_policy),
            "selected_prob": self.selected_prob,
            "optimal_set_mass": self.optimal_set_mass,
        }


def gamma_grid(
    gamma_max: float = DEFAULT_GAMMA_MAX,
    grid_points: int = DEFAULT_GAMMA_GRID_POINTS,
) -> list[float]:
    """Deterministic precision grid ``[0, gamma_max]`` with ``grid_points`` samples."""
    return [float(x) for x in np.linspace(0.0, float(gamma_max), int(grid_points))]


def posterior_at_gamma(efe_totals: ArrayF, gamma: float) -> ArrayF:
    """Policy posterior ``q(pi) = softmax(-gamma * G)`` for a fixed precision."""
    totals = np.asarray(efe_totals, dtype=np.float64).reshape(-1)
    return _softmax(-float(gamma) * totals)


def sweep_precision(
    model: dict[str, Any],
    *,
    gamma_max: float = DEFAULT_GAMMA_MAX,
    grid_points: int = DEFAULT_GAMMA_GRID_POINTS,
    selection_mass_threshold: float = SELECTION_MASS_THRESHOLD,
) -> dict[str, Any]:
    """Sweep precision over the policy posterior of ``model``.

    Returns a JSON-ready dict: one row per ``gamma`` (entropy, argmax-selected
    policy, its probability, and the EFE-optimal-set mass) plus aggregate fields
    used by the manuscript / claim ledger -- the grid size, the entropy at
    ``gamma`` = 1, the saturating ``ln(|optimal set|)`` floor, the optimal-set
    size, and the smallest grid ``gamma`` at which the optimal-set mass crosses
    ``selection_mass_threshold`` (``None`` if it never does on the grid).
    """
    decomposition = decompose_all_policies(model)
    rows = decomposition["rows"]
    policies = [tuple(int(a) for a in row["policy"]) for row in rows]
    totals = np.array([float(row["total"]) for row in rows], dtype=np.float64)

    optimal_mask = np.isclose(totals, totals.min(), atol=OPTIMAL_TIE_ATOL)
    optimal_set_size = int(optimal_mask.sum())
    entropy_floor = float(np.log(optimal_set_size)) if optimal_set_size > 0 else 0.0

    grid = gamma_grid(gamma_max, grid_points)
    points: list[PrecisionPoint] = []
    for gamma in grid:
        posterior = posterior_at_gamma(totals, gamma)
        selected_index = int(np.argmax(posterior))
        points.append(
            PrecisionPoint(
                gamma=float(gamma),
                entropy=_entropy(posterior),
                selected_policy=policies[selected_index],
                selected_prob=float(posterior[selected_index]),
                optimal_set_mass=float(posterior[optimal_mask].sum()),
            )
        )

    entropy_at_one = next(
        (p.entropy for p in points if abs(p.gamma - 1.0) <= 1e-12),
        _entropy(posterior_at_gamma(totals, 1.0)),
    )
    gamma_deterministic = next(
        (p.gamma for p in points if p.optimal_set_mass >= selection_mass_threshold),
        None,
    )
    entropies = [p.entropy for p in points]
    masses = [p.optimal_set_mass for p in points]

    return {
        "schema": "template_active_inference.precision_sweep.v1",
        "policy_count": len(policies),
        "optimal_policy_set": [list(p) for p, keep in zip(policies, optimal_mask, strict=True) if keep],
        "optimal_set_size": optimal_set_size,
        "entropy_floor": entropy_floor,
        "gamma_grid_points": len(grid),
        "gamma_max": float(gamma_max),
        "selection_mass_threshold": float(selection_mass_threshold),
        "entropy_at_gamma_one": float(entropy_at_one),
        "gamma_deterministic_selection": (None if gamma_deterministic is None else float(gamma_deterministic)),
        "entropy_monotone_nonincreasing": bool(
            all(b <= a + 1e-12 for a, b in zip(entropies, entropies[1:], strict=False))
        ),
        "optimal_mass_monotone_nondecreasing": bool(
            all(b >= a - 1e-12 for a, b in zip(masses, masses[1:], strict=False))
        ),
        "rows": [p.to_dict() for p in points],
    }
