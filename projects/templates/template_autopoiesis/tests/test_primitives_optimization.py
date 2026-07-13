"""Tests for optimization primitives: gradient_descent and analytic_minimizer."""

from __future__ import annotations

import numpy as np

from src.primitives.optimization import (
    gradient_descent,
    analytic_minimizer,
    _negative_control_wrong_sign,
    PRIMITIVES,
)

_EXAMPLE = {
    "A": [[2.0, 0.0], [0.0, 2.0]],
    "c": [1.0, -1.0],
    "x0": [0.0, 0.0],
    "lr": 0.1,
    "steps": 200,
}


# ---------------------------------------------------------------------------
# gradient_descent
# ---------------------------------------------------------------------------


def test_gradient_descent_returns_dict():
    result = gradient_descent(_EXAMPLE)
    assert "x_final" in result and "trajectory" in result


def test_gradient_descent_converges_to_minimum():
    result = gradient_descent(_EXAMPLE)
    x_final = np.array(result["x_final"])
    c = np.array([1.0, -1.0])
    assert np.linalg.norm(x_final - c) < 1e-3


def test_gradient_descent_trajectory_shape():
    result = gradient_descent(_EXAMPLE)
    traj = np.array(result["trajectory"])
    assert traj.shape == (201, 2)  # steps+1 × dim


def test_gradient_descent_trajectory_starts_at_x0():
    result = gradient_descent(_EXAMPLE)
    traj = np.array(result["trajectory"])
    assert np.allclose(traj[0], [0.0, 0.0])


def test_gradient_descent_monotone_decrease():
    """Loss should decrease monotonically for this simple convex problem."""
    A = np.array([[2.0, 0.0], [0.0, 2.0]])
    c = np.array([1.0, -1.0])
    result = gradient_descent(_EXAMPLE)
    traj = np.array(result["trajectory"])
    losses = [float(0.5 * (x - c) @ A @ (x - c)) for x in traj]
    for i in range(len(losses) - 1):
        assert losses[i] >= losses[i + 1] - 1e-10


# ---------------------------------------------------------------------------
# analytic_minimizer
# ---------------------------------------------------------------------------


def test_analytic_minimizer_returns_c():
    result = analytic_minimizer(_EXAMPLE)
    assert np.allclose(result["x_star"], [1.0, -1.0])


def test_analytic_minimizer_exact():
    inp = {"c": [3.0, -2.0, 1.0]}
    result = analytic_minimizer(inp)
    assert np.allclose(result["x_star"], [3.0, -2.0, 1.0])


# ---------------------------------------------------------------------------
# Negative control: wrong-sign gradient
# ---------------------------------------------------------------------------


def test_wrong_sign_diverges():
    result = _negative_control_wrong_sign(_EXAMPLE)
    x_final = np.array(result["x_final"])
    # Wrong-sign gradient ascent should diverge far from minimum
    c = np.array([1.0, -1.0])
    assert np.linalg.norm(x_final - c) > 1.0


def test_wrong_sign_differs_from_correct():
    correct = gradient_descent(_EXAMPLE)
    wrong = _negative_control_wrong_sign(_EXAMPLE)
    assert not np.allclose(correct["x_final"], wrong["x_final"])


# ---------------------------------------------------------------------------
# PRIMITIVES registry
# ---------------------------------------------------------------------------


def test_primitives_length():
    assert len(PRIMITIVES) == 2


def test_primitives_names():
    names = {p.name for p in PRIMITIVES}
    assert names == {"gradient_descent", "analytic_minimizer"}


def test_gradient_descent_primitive_example():
    spec = next(p for p in PRIMITIVES if p.name == "gradient_descent")
    result = spec.fn(spec.example_input)
    x_final = np.array(result["x_final"])
    x_star = spec.expected["x_star"]
    assert np.linalg.norm(x_final - x_star) < spec.tolerance + 0.01


def test_gradient_descent_negative_control_exists():
    spec = next(p for p in PRIMITIVES if p.name == "gradient_descent")
    assert spec.negative_control is not None
