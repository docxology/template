"""Batch distances and comparison of a constant against a reference sample."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np

from rational_distance import min_q_squared_error, min_rational_distance


def _batch_min_rational_distances_vectorized(x: np.ndarray, q_max: int) -> np.ndarray:
    """Vectorized ``min |x - p/q|`` matching the three-``p`` scan per ``q``."""
    x = np.asarray(x, dtype=np.float64).ravel()
    n = x.size
    if n == 0:
        return np.empty(0, dtype=np.float64)
    best = np.full(n, np.inf, dtype=np.float64)
    for q in range(1, q_max + 1):
        k = np.rint(x * q).astype(np.int64)
        for dt in (-1, 0, 1):
            p = k + dt
            d = np.abs(x - p.astype(np.float64) / q)
            best = np.minimum(best, d)
    return best


def _batch_min_q_squared_vectorized(x: np.ndarray, q_max: int) -> np.ndarray:
    """Vectorized ``min q^2|x - p/q|`` with the same candidates as :func:`rational_at_min_q_squared_error`."""
    x = np.asarray(x, dtype=np.float64).ravel()
    n = x.size
    if n == 0:
        return np.empty(0, dtype=np.float64)
    best = np.full(n, np.inf, dtype=np.float64)
    for q in range(1, q_max + 1):
        qq = float(q * q)
        k = np.rint(x * q).astype(np.int64)
        for dt in (-1, 0, 1):
            p = k + dt
            d = np.abs(x - p.astype(np.float64) / q)
            m = qq * d
            best = np.minimum(best, m)
    return best


def batch_min_rational_distances(
    values: np.ndarray | Sequence[float],
    q_max: int,
    *,
    implementation: str = "auto",
) -> np.ndarray:
    """Minimum rational distance per sample; ``implementation`` is ``auto``, ``vectorized``, or ``scalar``."""
    arr = np.asarray(values, dtype=np.float64).ravel()
    if implementation == "scalar":
        return np.array([min_rational_distance(float(v), q_max) for v in arr], dtype=np.float64)
    if implementation == "vectorized":
        return _batch_min_rational_distances_vectorized(arr, q_max)
    # auto: vectorized (equivalent to scalar; used for performance at larger batches)
    if arr.size == 0:
        return np.array([], dtype=np.float64)
    return _batch_min_rational_distances_vectorized(arr, q_max)


def batch_min_q_squared_errors(
    values: np.ndarray | Sequence[float],
    q_max: int,
    *,
    implementation: str = "auto",
) -> np.ndarray:
    """Minimum ``q^2|x-p/q|`` per sample."""
    arr = np.asarray(values, dtype=np.float64).ravel()
    if implementation == "scalar":
        return np.array([min_q_squared_error(float(v), q_max) for v in arr], dtype=np.float64)
    if implementation == "vectorized":
        return _batch_min_q_squared_vectorized(arr, q_max)
    if arr.size == 0:
        return np.array([], dtype=np.float64)
    return _batch_min_q_squared_vectorized(arr, q_max)


def empirical_percentile_rank(value: float, reference: np.ndarray) -> float:
    """Proportion of ``reference`` samples strictly below ``value``.

    Returns a value in ``[0, 1]``. Ties count toward the upper tail (strict ``<``).
    """
    ref = np.asarray(reference, dtype=np.float64).ravel()
    if ref.size == 0:
        return 0.5
    below = np.sum(ref < value)
    return float(below / ref.size)


def reference_percentiles(
    distances: np.ndarray | Sequence[float],
    levels: tuple[float, ...] = (5.0, 25.0, 50.0, 75.0, 95.0),
) -> dict[str, float]:
    """Named percentiles (0--100 scale in keys ``p05``, ``p25``, …) for a sample."""
    ref = np.asarray(distances, dtype=np.float64).ravel()
    if ref.size == 0:
        return {f"p{int(lv):02d}": float("nan") for lv in levels}
    out: dict[str, float] = {}
    for lv in levels:
        key = f"p{int(lv):02d}"
        out[key] = float(np.percentile(ref, lv))
    return out


def summarize_vs_reference(
    name: str,
    x: float,
    q_max: int,
    reference_distances: np.ndarray,
    reference_q_squared: np.ndarray | None = None,
    *,
    use_fractional_part: bool = False,
) -> dict[str, Any]:
    """Compare one number's metrics at ``q_max`` to precomputed reference arrays."""
    x_eval = (x - math.floor(x)) if use_fractional_part else x
    d = min_rational_distance(x_eval, q_max)
    ref = np.asarray(reference_distances, dtype=np.float64).ravel()
    rank = empirical_percentile_rank(d, ref)
    row: dict[str, Any] = {
        "name": name,
        "x": x,
        "q_max": q_max,
        "use_fractional_part": use_fractional_part,
        "min_distance": d,
        "reference_median": float(np.median(ref)) if ref.size else float("nan"),
        "reference_mean": float(np.mean(ref)) if ref.size else float("nan"),
        "empirical_percentile_rank": rank,
        "reference_n": int(ref.size),
    }
    if reference_q_squared is not None:
        rq = np.asarray(reference_q_squared, dtype=np.float64).ravel()
        mq = min_q_squared_error(x_eval, q_max)
        row["min_q_squared_error"] = mq
        row["empirical_percentile_rank_q_squared"] = empirical_percentile_rank(mq, rq)
    return row


def compare_constant_table(
    constants: Mapping[str, float],
    q_max: int,
    reference_distances: np.ndarray,
    reference_q_squared: np.ndarray | None = None,
    *,
    use_fractional_part: bool = False,
) -> list[dict[str, Any]]:
    """Run :func:`summarize_vs_reference` for each ``(name, value)`` pair."""
    rows: list[dict[str, Any]] = []
    for name, val in constants.items():
        rows.append(
            summarize_vs_reference(
                name,
                float(val),
                q_max,
                reference_distances,
                reference_q_squared,
                use_fractional_part=use_fractional_part,
            )
        )
    return rows


def empirical_percentile_rank_midrank(value: float, reference: np.ndarray) -> float:
    """Midrank-style empirical CDF at ``value`` (ties split symmetrically).

    Returns ``(#{ref < v} + 0.5 * #{ref == v}) / n`` in ``[0, 1]``.
    """
    ref = np.asarray(reference, dtype=np.float64).ravel()
    if ref.size == 0:
        return 0.5
    below = np.sum(ref < value)
    equal = np.sum(ref == value)
    return float((below + 0.5 * equal) / ref.size)


def reference_distribution_summary(reference: np.ndarray) -> dict[str, float]:
    """Order statistics for a reference sample of ``\\delta_Q`` values."""
    ref = np.asarray(reference, dtype=np.float64).ravel()
    base = reference_percentiles(ref, levels=(5.0, 25.0, 50.0, 75.0, 95.0))
    if ref.size == 0:
        return {
            "n": 0.0,
            "min": float("nan"),
            "q25": float("nan"),
            "median": float("nan"),
            "q75": float("nan"),
            "max": float("nan"),
            "mean": float("nan"),
            "p05": float("nan"),
            "p95": float("nan"),
        }
    return {
        "n": float(ref.size),
        "min": float(np.min(ref)),
        "q25": base["p25"],
        "median": base["p50"],
        "q75": base["p75"],
        "max": float(np.max(ref)),
        "mean": float(np.mean(ref)),
        "p05": base["p05"],
        "p95": base["p95"],
    }
