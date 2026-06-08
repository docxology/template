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
    """The four additive terms of the Theorem 5.1 entanglement decomposition (nats).

    Their sum (:attr:`total`) equals the free energy against the entangled prior
    (:func:`free_energy_against_entangled_prior`); :func:`decomposition_identity_holds`
    checks that equality.

    Attributes:
        sum_marginal_free_energies: Σ_k of the per-stream (mean-field) free energies.
        coupling_cost_term: Precision-weighted expected coupling cost ``γλ·E_q[K_c]``.
        coupling_prior_term: Log-partition correction for the coupled prior minus
            ``λ·E_q[J]`` (the prior-side contribution of the coupling).
        total_correlation_gain: Total correlation ``TC(q)`` induced by the coupling.
    """

    sum_marginal_free_energies: float
    coupling_cost_term: float
    coupling_prior_term: float
    total_correlation_gain: float

    @property
    def total(self) -> float:
        """Sum of the four decomposition terms (the RHS of the identity), in nats."""
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
    """Sum over streams of the per-stream free energies, ``Σ_k F_k`` (nats).

    The first decomposition term: aggregates :func:`marginal_free_energy` across
    every axis of the joint belief ``q``.
    """
    qa = np.asarray(q, dtype=np.float64)
    return float(sum(marginal_free_energy(qa, mf_prior, per_stream_g, gamma, k) for k in range(qa.ndim)))


def coupling_cost_term(q: ArrayF, coupling_kc: ArrayF, gamma: float, lam: float) -> float:
    """Precision-weighted expected coupling cost ``γλ·E_q[K_c]`` (nats).

    The second decomposition term: the energy-side contribution of the coupling.
    """
    return gamma * lam * expected_value(q, coupling_kc)


def coupling_prior_term(
    q: ArrayF,
    coupling_j: ArrayF,
    mf_prior: Sequence[ArrayF],
    lam: float,
) -> float:
    """Prior-side coupling term ``log Z(λ) - λ·E_q[J]`` (nats).

    The third decomposition term: the log-partition of the ``λ``-coupled prior
    (relative to the mean-field base) minus the expected coupling potential under
    ``q``.
    """
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
    """Assemble the four-term RHS of the Theorem 5.1 decomposition.

    Returns:
        A :class:`DecompositionTerms` whose ``total`` should equal
        :func:`free_energy_against_entangled_prior` for the same inputs.
    """
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
    """Free energy of ``q`` against the fully entangled (``λ``-coupled) prior (nats).

    Builds the coupled prior ``∝ base · exp(λ J)`` and the combined cost
    ``Σ_k g_k + λ K_c``, then evaluates :func:`~analytical.free_energy.free_energy`.
    This is the LHS of the Theorem 5.1 identity.
    """
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
    """True iff the Theorem 5.1 identity holds within ``atol`` (nats).

    Checks that the free energy against the entangled prior equals the four-term
    decomposition RHS, i.e. ``free_energy_against_entangled_prior == DecompositionTerms.total``.

    Args:
        atol: Absolute tolerance for the numerical equality.

    Returns:
        Whether LHS and RHS agree to ``atol``.
    """
    lhs = free_energy_against_entangled_prior(q, mf_prior, per_stream_g, coupling_j, coupling_kc, gamma, lam)
    rhs = entanglement_decomposition_rhs(q, mf_prior, per_stream_g, coupling_j, coupling_kc, gamma, lam).total
    return bool(np.isclose(lhs, rhs, atol=atol))
