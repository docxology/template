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
    pa = np.asarray(p, dtype=np.float64)
    mask = pa > 0.0
    return float(-(pa[mask] * np.log(pa[mask])).sum())


def kl_divergence(q: ArrayF, p: ArrayF) -> float:
    qa = np.asarray(q, dtype=np.float64).ravel()
    pa = np.asarray(p, dtype=np.float64).ravel()
    if qa.shape != pa.shape:
        raise ValueError(f"kl_divergence shape mismatch: q={qa.shape}, p={pa.shape}")
    mask_q = qa > 0.0
    if np.any(pa[mask_q] <= 0.0):
        return float("inf")
    return float(np.sum(qa[mask_q] * (np.log(qa[mask_q]) - np.log(pa[mask_q]))))


def total_correlation(q: ArrayF) -> float:
    qa = np.asarray(q, dtype=np.float64)
    margs = joint_marginals(qa)
    return float(sum(shannon_entropy(m) for m in margs) - shannon_entropy(qa))


def total_correlation_via_kl(q: ArrayF) -> float:
    return kl_divergence(q, m_projection(q))


def free_energy(q: ArrayF, prior: ArrayF, g: ArrayF, gamma: float) -> float:
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
    qa = np.asarray(q, dtype=np.float64)
    qk = joint_marginal(qa, k)
    ek = np.asarray(mf_prior[k], dtype=np.float64)
    gk = np.asarray(per_stream_g[k], dtype=np.float64)
    exp_gk = float(np.sum(qk * gk))
    exp_log_ek = float(np.sum(qk * _safe_log(ek)))
    return gamma * exp_gk - exp_log_ek - shannon_entropy(qk)
