"""Free energies, entropies, and total correlation (nats)."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from .joint_dist import joint_marginal, joint_marginals, m_projection

ArrayF = NDArray[np.float64]

_LOG_FLOOR = 1e-300


def _safe_log(p: ArrayF) -> ArrayF:
    pa = np.asarray(p, dtype=np.float64)
    return np.log(np.where(pa > 0.0, pa, _LOG_FLOOR))


def shannon_entropy(p: ArrayF) -> float:
    """Shannon entropy ``H(p) = -Σ p log p`` in nats.

    Zero-probability entries are dropped (``0 log 0 := 0``), so ``p`` need not be
    strictly positive.

    Args:
        p: Probability array (any shape); should sum to 1 over its support.

    Returns:
        Entropy in nats.
    """
    pa = np.asarray(p, dtype=np.float64)
    mask = pa > 0.0
    return float(-(pa[mask] * np.log(pa[mask])).sum())


def kl_divergence(q: ArrayF, p: ArrayF) -> float:
    """Kullback-Leibler divergence ``D(q‖p) = Σ q log(q/p)`` in nats.

    Both arrays are flattened and must share a shape. Returns ``inf`` when ``q``
    places mass where ``p`` is zero (the divergence is unbounded there);
    ``q``-zero entries are skipped.

    Args:
        q: Reference distribution (the expectation is taken under ``q``).
        p: Comparison distribution.

    Returns:
        Divergence in nats (``>= 0``, or ``inf`` if ``p`` lacks ``q``'s support).

    Raises:
        ValueError: If ``q`` and ``p`` have different shapes.
    """
    qa = np.asarray(q, dtype=np.float64).ravel()
    pa = np.asarray(p, dtype=np.float64).ravel()
    if qa.shape != pa.shape:
        raise ValueError(f"kl_divergence shape mismatch: q={qa.shape}, p={pa.shape}")
    mask_q = qa > 0.0
    if np.any(pa[mask_q] <= 0.0):
        return float("inf")
    return float(np.sum(qa[mask_q] * (np.log(qa[mask_q]) - np.log(pa[mask_q]))))


def total_correlation(q: ArrayF) -> float:
    """Total correlation ``TC(q) = Σ_k H(q_k) - H(q)`` in nats (direct form).

    Measures the total shared information among the factors of a joint
    distribution: the sum of per-axis marginal entropies minus the joint
    entropy. Zero for a product (independent) distribution.

    Args:
        q: Joint distribution with one axis per variable.

    Returns:
        Total correlation in nats (``>= 0``).
    """
    qa = np.asarray(q, dtype=np.float64)
    margs = joint_marginals(qa)
    return float(sum(shannon_entropy(m) for m in margs) - shannon_entropy(qa))


def total_correlation_via_kl(q: ArrayF) -> float:
    """Total correlation as ``D(q‖∏_k q_k)`` in nats (KL form).

    Equivalent to :func:`total_correlation` but computed as the KL divergence
    from ``q`` to its product-of-marginals (``m``) projection; the two agree to
    numerical precision and this form makes the "distance from independence"
    reading explicit.

    Args:
        q: Joint distribution with one axis per variable.

    Returns:
        Total correlation in nats (``>= 0``).
    """
    return kl_divergence(q, m_projection(q))


def free_energy(q: ArrayF, prior: ArrayF, g: ArrayF, gamma: float) -> float:
    """Variational free energy ``F = γ·E_q[G] - E_q[log prior] - H(q)`` in nats.

    The standard energy minus entropy form: expected (precision-weighted) cost
    under the belief ``q``, minus the cross-entropy with the ``prior``, minus the
    entropy of ``q``.

    Args:
        q: Belief (posterior) distribution.
        prior: Prior distribution over the same support.
        g: Cost / energy term per state (same shape as ``q``).
        gamma: Precision weighting ``γ`` on the energy term.

    Returns:
        Free energy in nats.

    Raises:
        ValueError: If ``q``, ``prior``, and ``g`` do not share a shape.
    """
    qa = np.asarray(q, dtype=np.float64)
    pa = np.asarray(prior, dtype=np.float64)
    ga = np.asarray(g, dtype=np.float64)
    if qa.shape != pa.shape or qa.shape != ga.shape:
        raise ValueError("q, prior, G must share a common shape")
    exp_g = float(np.sum(qa * ga))
    exp_log_p = float(np.sum(qa * _safe_log(pa)))
    return gamma * exp_g - exp_log_p - shannon_entropy(qa)


def marginal_free_energy(
    q: ArrayF,
    mf_prior: Sequence[ArrayF],
    per_stream_g: Sequence[ArrayF],
    gamma: float,
    k: int,
) -> float:
    """Per-stream (mean-field) free energy for factor ``k`` in nats.

    The single-stream analogue of :func:`free_energy`, evaluated on the ``k``-th
    marginal of ``q`` against that stream's mean-field prior and cost.

    Args:
        q: Joint belief distribution.
        mf_prior: Mean-field priors, one per stream.
        per_stream_g: Cost / energy terms, one per stream.
        gamma: Precision weighting ``γ`` on the energy term.
        k: Index of the stream to evaluate.

    Returns:
        Stream-``k`` free energy in nats.
    """
    qa = np.asarray(q, dtype=np.float64)
    qk = joint_marginal(qa, k)
    ek = np.asarray(mf_prior[k], dtype=np.float64)
    gk = np.asarray(per_stream_g[k], dtype=np.float64)
    exp_gk = float(np.sum(qk * gk))
    exp_log_ek = float(np.sum(qk * _safe_log(ek)))
    return gamma * exp_gk - exp_log_ek - shannon_entropy(qk)
