"""Registry-backed invariants for the analytical track."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from .bernoulli_toy import (
    BERNOULLI_VERIFICATION_TOLERANCE,
    empirical_mutual_information,
    ising_joint_posterior,
    ising_mutual_information,
)
from .decomposition import decomposition_identity_holds
from .hyperparameters import lambda_grid, load_hyperparameters

InvariantFn = Callable[[], bool]


def inv_ising_mi_at_zero() -> bool:
    return abs(ising_mutual_information(0.0)) <= BERNOULLI_VERIFICATION_TOLERANCE


def inv_ising_mi_saturates() -> bool:
    high = ising_mutual_information(100.0)
    return bool(np.isclose(high, np.log(2.0), atol=1e-3))


def inv_empirical_matches_closed_form() -> bool:
    hp = load_hyperparameters()
    for lam in lambda_grid(hp):
        closed = ising_mutual_information(lam)
        empirical = empirical_mutual_information(lam)
        if abs(closed - empirical) > hp.bernoulli_verification_tolerance:
            return False
    return True


def inv_decomposition_identity() -> bool:
    lam = 1.5
    q = ising_joint_posterior(lam)
    from .bernoulli_toy import ising_coupling, symmetric_mean_field_prior

    mf = symmetric_mean_field_prior()
    g0 = [np.zeros(2, dtype=np.float64), np.zeros(2, dtype=np.float64)]
    return decomposition_identity_holds(
        q,
        mf,
        g0,
        ising_coupling(),
        np.zeros((2, 2), dtype=np.float64),
        gamma=1.0,
        lam=lam,
    )


def inv_joint_is_pmf() -> bool:
    from .joint_dist import is_pmf

    q = ising_joint_posterior(2.0)
    return is_pmf(q)


def inv_mean_field_at_lambda_zero() -> bool:
    from .joint_dist import is_mean_field

    q = ising_joint_posterior(0.0)
    return is_mean_field(q)


CORE_INVARIANTS: dict[str, InvariantFn] = {
    "ising_mi_at_zero": inv_ising_mi_at_zero,
    "ising_mi_saturates": inv_ising_mi_saturates,
    "empirical_matches_closed_form": inv_empirical_matches_closed_form,
    "decomposition_identity": inv_decomposition_identity,
    "joint_is_pmf": inv_joint_is_pmf,
    "mean_field_at_lambda_zero": inv_mean_field_at_lambda_zero,
}


def run_invariants() -> dict[str, bool]:
    return {name: fn() for name, fn in CORE_INVARIANTS.items()}


def all_invariants_pass(results: dict[str, bool] | None = None) -> bool:
    inv = results if results is not None else run_invariants()
    return all(inv.values())
