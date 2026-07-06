"""Optimization primitives: gradient descent on convex quadratics."""
from __future__ import annotations

import numpy as np

from .base import PrimitiveSpec


def gradient_descent(inputs: dict) -> dict:
    """Run gradient descent on f(x) = 0.5*(x-c)^T A (x-c).

    inputs keys: A (ndarray), c (ndarray), x0 (ndarray), lr (float), steps (int)
    """
    A = np.array(inputs["A"], dtype=float)
    c = np.array(inputs["c"], dtype=float)
    x = np.array(inputs["x0"], dtype=float)
    lr = float(inputs.get("lr", 0.1))
    steps = int(inputs.get("steps", 100))

    trajectory = [x.copy()]
    for _ in range(steps):
        grad = A @ (x - c)
        x = x - lr * grad
        trajectory.append(x.copy())

    return {"x_final": x, "trajectory": np.array(trajectory)}


def analytic_minimizer(inputs: dict) -> dict:
    """Analytic minimum: x* = c."""
    c = np.array(inputs["c"], dtype=float)
    return {"x_star": c}


def _negative_control_wrong_sign(inputs: dict) -> dict:
    """Wrong-sign gradient (ascent instead of descent)."""
    A = np.array(inputs["A"], dtype=float)
    c = np.array(inputs["c"], dtype=float)
    x = np.array(inputs["x0"], dtype=float)
    lr = float(inputs.get("lr", 0.1))
    steps = int(inputs.get("steps", 100))

    trajectory = [x.copy()]
    for _ in range(steps):
        grad = A @ (x - c)
        x = x + lr * grad  # wrong sign → diverges
        trajectory.append(x.copy())

    return {"x_final": x, "trajectory": np.array(trajectory)}


_EXAMPLE = {
    "A": [[2.0, 0.0], [0.0, 2.0]],
    "c": [1.0, -1.0],
    "x0": [0.0, 0.0],
    "lr": 0.1,
    "steps": 200,
}

PRIMITIVES: tuple[PrimitiveSpec, ...] = (
    PrimitiveSpec(
        name="gradient_descent",
        domain="optimization",
        fn=gradient_descent,
        callable_name="gradient_descent",
        example_input=_EXAMPLE,
        expected={"x_star": np.array([1.0, -1.0])},
        tolerance=1e-4,
        negative_control=_negative_control_wrong_sign,
    ),
    PrimitiveSpec(
        name="analytic_minimizer",
        domain="optimization",
        fn=analytic_minimizer,
        callable_name="analytic_minimizer",
        example_input=_EXAMPLE,
        expected={"x_star": np.array([1.0, -1.0])},
        tolerance=1e-12,
    ),
)
