"""Coupling potentials and lambda-entangled posteriors."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from .joint_dist import mean_field_to_joint, normalize

ArrayF = NDArray[np.float64]


def entangled_prior_unnormalised(
    mf_prior: Sequence[ArrayF],
    coupling_j: ArrayF,
    lam: float,
) -> ArrayF:
    base = mean_field_to_joint(mf_prior)
    ja = np.asarray(coupling_j, dtype=np.float64)
    if base.shape != ja.shape:
        raise ValueError(f"coupling shape {ja.shape} != mean-field shape {base.shape}")
    return base * np.exp(lam * ja)


def entangled_posterior(
    mf_prior: Sequence[ArrayF],
    per_stream_g: Sequence[ArrayF],
    coupling_j: ArrayF,
    coupling_kc: ArrayF,
    gamma: float,
    lam: float,
) -> ArrayF:
    prior_unn = entangled_prior_unnormalised(mf_prior, coupling_j, lam)
    g_total = mean_field_to_joint([np.exp(-gamma * np.asarray(g, dtype=np.float64)) for g in per_stream_g])
    kc = np.asarray(coupling_kc, dtype=np.float64)
    if kc.shape != prior_unn.shape:
        raise ValueError(f"coupling K_c shape {kc.shape} != joint shape {prior_unn.shape}")
    return normalize(prior_unn * g_total * np.exp(-gamma * lam * kc))


def expected_value(q: ArrayF, f: ArrayF) -> float:
    qa = np.asarray(q, dtype=np.float64)
    fa = np.asarray(f, dtype=np.float64)
    if qa.shape != fa.shape:
        raise ValueError(f"expected_value shape mismatch: q={qa.shape}, f={fa.shape}")
    return float(np.sum(qa * fa))
