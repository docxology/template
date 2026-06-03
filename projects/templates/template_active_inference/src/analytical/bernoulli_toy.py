"""Closed-form K=2 Bernoulli / Ising toy model."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .coupling import entangled_posterior
from .free_energy import total_correlation

ArrayF = NDArray[np.float64]

BERNOULLI_VERIFICATION_TOLERANCE = 1e-9


def ising_coupling(shape: tuple[int, int] = (2, 2)) -> ArrayF:
    if shape != (2, 2):
        raise ValueError("ising_coupling is only defined for shape (2, 2)")
    return np.array([[0.5, -0.5], [-0.5, 0.5]], dtype=np.float64)


def symmetric_mean_field_prior() -> tuple[ArrayF, ArrayF]:
    half = np.array([0.5, 0.5], dtype=np.float64)
    return (half, half)


def ising_mutual_information(lam: float) -> float:
    lam = float(lam)
    if lam >= 0:
        pa = 1.0 / (1.0 + np.exp(-lam))
    else:
        e = np.exp(lam)
        pa = e / (1.0 + e)
    if pa <= 0.0 or pa >= 1.0:
        h_b = 0.0
    else:
        h_b = -pa * np.log(pa) - (1.0 - pa) * np.log(1.0 - pa)
    return float(np.log(2.0) - h_b)


def ising_joint_posterior(lam: float) -> ArrayF:
    mf = list(symmetric_mean_field_prior())
    g0 = np.zeros(2, dtype=np.float64)
    kc = np.zeros((2, 2), dtype=np.float64)
    return entangled_posterior(mf, [g0, g0], ising_coupling(), kc, gamma=0.0, lam=lam)


def empirical_mutual_information(lam: float) -> float:
    """Mutual information recomputed independently from the joint via total correlation.

    Despite the historical name, this is a *deterministic exact recomputation* — not a
    Monte Carlo / sampled estimate. It evaluates total correlation on the exact entangled
    joint, providing a second code path that must agree with the closed-form
    ``ising_mutual_information`` to machine precision (see ``invariants.py`` and
    ``test_bernoulli_toy``). It exists as a cross-implementation oracle, so manuscript
    figures/prose describe it as an "exact recomputation", never as an empirical estimate.
    """
    return float(total_correlation(ising_joint_posterior(lam)))


def lambda_sweep_values(num_points: int = 21, *, lambda_max: float | None = None) -> list[float]:
    """Backward-compatible sweep grid; delegates to ``lambda_grid`` SSOT."""
    from .hyperparameters import Hyperparameters, lambda_grid

    if num_points < 2:
        raise ValueError("num_points must be at least 2")
    hp = Hyperparameters(
        lambda_grid_points=num_points,
        lambda_max=lambda_max if lambda_max is not None else Hyperparameters().lambda_max,
    )
    return lambda_grid(hp)
