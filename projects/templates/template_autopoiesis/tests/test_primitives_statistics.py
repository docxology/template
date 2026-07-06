"""Tests for statistics primitives: ols_fit."""
from __future__ import annotations

import numpy as np

from src.primitives.statistics import ols_fit, _shuffled_control, PRIMITIVES

# Inject known coefficients
_n = 50
_rng = np.random.default_rng(42)
_X = np.column_stack([np.ones(_n), _rng.standard_normal(_n)])
_true_beta = np.array([2.0, -3.0])
_y = _X @ _true_beta + _rng.standard_normal(_n) * 0.1

_EXAMPLE = {"X": _X.tolist(), "y": _y.tolist()}


# ---------------------------------------------------------------------------
# ols_fit
# ---------------------------------------------------------------------------


def test_ols_fit_returns_dict():
    result = ols_fit(_EXAMPLE)
    assert "beta_hat" in result and "residuals" in result and "r_squared" in result


def test_ols_fit_recovers_beta():
    result = ols_fit(_EXAMPLE)
    beta = np.array(result["beta_hat"])
    assert np.linalg.norm(beta - _true_beta) < 0.1


def test_ols_fit_high_r_squared():
    result = ols_fit(_EXAMPLE)
    assert result["r_squared"] > 0.95


def test_ols_fit_residuals_small():
    result = ols_fit(_EXAMPLE)
    residuals = np.array(result["residuals"])
    assert float(np.mean(np.abs(residuals))) < 0.5


def test_ols_fit_residuals_mean_near_zero():
    result = ols_fit(_EXAMPLE)
    residuals = np.array(result["residuals"])
    # With an intercept column, residuals should be near zero mean
    assert abs(float(np.mean(residuals))) < 0.05


def test_ols_fit_deterministic():
    r1 = ols_fit(_EXAMPLE)
    r2 = ols_fit(_EXAMPLE)
    assert np.allclose(r1["beta_hat"], r2["beta_hat"])


# ---------------------------------------------------------------------------
# Negative control: shuffled labels
# ---------------------------------------------------------------------------


def test_shuffled_control_poor_r_squared():
    result = _shuffled_control(_EXAMPLE)
    assert result["r_squared"] < 0.5


def test_shuffled_differs_from_correct():
    correct = ols_fit(_EXAMPLE)
    shuffled = _shuffled_control(_EXAMPLE)
    assert not np.allclose(correct["beta_hat"], shuffled["beta_hat"])


# ---------------------------------------------------------------------------
# PRIMITIVES registry
# ---------------------------------------------------------------------------


def test_primitives_length():
    assert len(PRIMITIVES) == 1


def test_primitives_name():
    assert PRIMITIVES[0].name == "ols_fit"


def test_primitives_domain():
    assert PRIMITIVES[0].domain == "statistics"


def test_primitives_example_input_matches():
    spec = PRIMITIVES[0]
    result = spec.fn(spec.example_input)
    beta = np.array(result["beta_hat"])
    expected = np.array(spec.expected["beta_hat"])
    assert np.linalg.norm(beta - expected) < spec.tolerance + 0.01


def test_primitives_negative_control_exists():
    assert PRIMITIVES[0].negative_control is not None
