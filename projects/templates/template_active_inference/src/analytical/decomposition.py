"""Theorem 5.1 entanglement decomposition (numerical realization)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.special import logsumexp

from .coupling import expected_value
from .free_energy import free_energy, marginal_free_energy, total_correlation
from .joint_dist import mean_field_to_joint

ArrayF = NDArray[np.float64]


@dataclass(frozen=True)
class DecompositionTerms:
    sum_marginal_free_energies: float
    coupling_cost_term: float
    coupling_prior_term: float
    total_correlation_gain: float

    @property
    def total(self) -> float:
        return (
            self.sum_marginal_free_energies
            + self.coupling_cost_term
            + self.coupling_prior_term
            + self.total_correlation_gain
        )


def sum_marginal_free_energies(
    q: ArrayF,
    mf_prior: Sequence[ArrayF],
    per_stream_g: Sequence[ArrayF],
    gamma: float,
) -> float:
    qa = np.asarray(q, dtype=np.float64)
    return float(sum(marginal_free_energy(qa, mf_prior, per_stream_g, gamma, k) for k in range(qa.ndim)))


def coupling_cost_term(q: ArrayF, coupling_kc: ArrayF, gamma: float, lam: float) -> float:
    return gamma * lam * expected_value(q, coupling_kc)


def coupling_prior_term(
    q: ArrayF,
    coupling_j: ArrayF,
    mf_prior: Sequence[ArrayF],
    lam: float,
) -> float:
    ja = np.asarray(coupling_j, dtype=np.float64)
    base = mean_field_to_joint(mf_prior)
    log_z = float(logsumexp(lam * ja, b=base))
    return log_z - lam * expected_value(q, ja)


def entanglement_decomposition_rhs(
    q: ArrayF,
    mf_prior: Sequence[ArrayF],
    per_stream_g: Sequence[ArrayF],
    coupling_j: ArrayF,
    coupling_kc: ArrayF,
    gamma: float,
    lam: float,
) -> DecompositionTerms:
    return DecompositionTerms(
        sum_marginal_free_energies=sum_marginal_free_energies(q, mf_prior, per_stream_g, gamma),
        coupling_cost_term=coupling_cost_term(q, coupling_kc, gamma, lam),
        coupling_prior_term=coupling_prior_term(q, coupling_j, mf_prior, lam),
        total_correlation_gain=float(total_correlation(q)),
    )


def _marginals_g_broadcast(per_stream_g: Sequence[ArrayF], joint_shape: tuple[int, ...]) -> ArrayF:
    acc = np.zeros(joint_shape, dtype=np.float64)
    nd = len(joint_shape)
    for k, gk in enumerate(per_stream_g):
        ga = np.asarray(gk, dtype=np.float64)
        expand = tuple(joint_shape[k] if axis == k else 1 for axis in range(nd))
        acc += ga.reshape(expand)
    return acc


def free_energy_against_entangled_prior(
    q: ArrayF,
    mf_prior: Sequence[ArrayF],
    per_stream_g: Sequence[ArrayF],
    coupling_j: ArrayF,
    coupling_kc: ArrayF,
    gamma: float,
    lam: float,
) -> float:
    base = mean_field_to_joint(mf_prior)
    ja = np.asarray(coupling_j, dtype=np.float64)
    kc = np.asarray(coupling_kc, dtype=np.float64)
    prior_unnorm = base * np.exp(lam * ja)
    prior = prior_unnorm / float(np.sum(prior_unnorm))
    g_lambda = _marginals_g_broadcast(per_stream_g, ja.shape) + lam * kc
    return free_energy(q, prior, g_lambda, gamma)


def decomposition_identity_holds(
    q: ArrayF,
    mf_prior: Sequence[ArrayF],
    per_stream_g: Sequence[ArrayF],
    coupling_j: ArrayF,
    coupling_kc: ArrayF,
    gamma: float,
    lam: float,
    atol: float = 1e-10,
) -> bool:
    lhs = free_energy_against_entangled_prior(q, mf_prior, per_stream_g, coupling_j, coupling_kc, gamma, lam)
    rhs = entanglement_decomposition_rhs(q, mf_prior, per_stream_g, coupling_j, coupling_kc, gamma, lam).total
    return bool(np.isclose(lhs, rhs, atol=atol))
