"""Statistics primitives: ordinary least squares regression."""

from __future__ import annotations

import numpy as np

from .base import PrimitiveSpec


def ols_fit(inputs: dict) -> dict:
    """Ordinary least squares regression: y = X @ beta + noise.

    inputs: X (n x p array), y (n array)
    Returns: beta_hat, residuals, r_squared
    """
    X = np.array(inputs["X"], dtype=float)
    y = np.array(inputs["y"], dtype=float)

    # beta_hat = (X^T X)^{-1} X^T y
    XtX = X.T @ X
    Xty = X.T @ y
    beta_hat = np.linalg.solve(XtX, Xty)

    y_hat = X @ beta_hat
    residuals = y - y_hat
    ss_res = float(residuals @ residuals)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {"beta_hat": beta_hat, "residuals": residuals, "r_squared": r_squared}


def _shuffled_control(inputs: dict) -> dict:
    """Shuffle y labels: should produce poor R²."""
    rng = np.random.default_rng(0)
    inp = dict(inputs)
    inp["y"] = rng.permutation(np.array(inputs["y"], dtype=float))
    return ols_fit(inp)


# Inject known coefficients
_n = 50
_rng = np.random.default_rng(42)
_X = np.column_stack([np.ones(_n), _rng.standard_normal(_n)])
_true_beta = np.array([2.0, -3.0])
_y = _X @ _true_beta + _rng.standard_normal(_n) * 0.1

_EXAMPLE = {"X": _X.tolist(), "y": _y.tolist()}

PRIMITIVES: tuple[PrimitiveSpec, ...] = (
    PrimitiveSpec(
        name="ols_fit",
        domain="statistics",
        fn=ols_fit,
        callable_name="ols_fit",
        example_input=_EXAMPLE,
        expected={"beta_hat": _true_beta},
        tolerance=0.1,
        negative_control=_shuffled_control,
    ),
)
