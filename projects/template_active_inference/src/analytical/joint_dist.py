"""Joint and mean-field distributions over finite policy spaces."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

ArrayF = NDArray[np.float64]


def is_pmf(q: ArrayF, atol: float = 1e-9) -> bool:
    qa = np.asarray(q, dtype=np.float64)
    return bool(np.all(qa >= -atol)) and bool(abs(float(qa.sum()) - 1.0) <= atol)


def normalize(q: ArrayF) -> ArrayF:
    qa = np.asarray(q, dtype=np.float64)
    total = float(qa.sum())
    if total <= 0.0:
        raise ValueError(f"cannot normalize non-positive mass: total={total}")
    return np.asarray(qa / total, dtype=np.float64)


def mean_field_to_joint(marginals: Sequence[ArrayF]) -> ArrayF:
    if not marginals:
        raise ValueError("mean_field_to_joint requires at least one stream")
    out = np.asarray(marginals[0], dtype=np.float64)
    for m in marginals[1:]:
        out = np.multiply.outer(out, np.asarray(m, dtype=np.float64))
    return out


def joint_marginal(q: ArrayF, k: int) -> ArrayF:
    qa = np.asarray(q, dtype=np.float64)
    if not 0 <= k < qa.ndim:
        raise IndexError(f"stream index {k} out of range for ndim={qa.ndim}")
    axes = tuple(i for i in range(qa.ndim) if i != k)
    return np.asarray(qa.sum(axis=axes) if axes else qa.copy(), dtype=np.float64)


def joint_marginals(q: ArrayF) -> list[ArrayF]:
    qa = np.asarray(q, dtype=np.float64)
    return [joint_marginal(qa, k) for k in range(qa.ndim)]


def is_mean_field(q: ArrayF, atol: float = 1e-9) -> bool:
    qa = np.asarray(q, dtype=np.float64)
    proj = mean_field_to_joint(joint_marginals(qa))
    return bool(np.max(np.abs(qa - proj)) <= atol)


def m_projection(q: ArrayF) -> ArrayF:
    return mean_field_to_joint(joint_marginals(q))
