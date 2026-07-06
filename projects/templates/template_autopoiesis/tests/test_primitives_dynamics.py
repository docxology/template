"""Tests for dynamics primitives: damped_oscillator."""
from __future__ import annotations

import numpy as np

from src.primitives.dynamics import damped_oscillator, _zero_damping_control, PRIMITIVES


# ---------------------------------------------------------------------------
# damped_oscillator
# ---------------------------------------------------------------------------


def test_damped_oscillator_returns_dict():
    inp = {"omega": 2.0, "zeta": 0.15, "x0": 1.0, "v0": 0.0, "dt": 0.05, "steps": 50}
    result = damped_oscillator(inp)
    assert isinstance(result, dict)
    assert "t" in result and "x" in result and "envelope" in result


def test_damped_oscillator_t_shape():
    inp = {"omega": 1.0, "zeta": 0.1, "x0": 1.0, "v0": 0.0, "dt": 0.1, "steps": 100}
    result = damped_oscillator(inp)
    assert len(result["t"]) == 101
    assert len(result["x"]) == 101


def test_damped_oscillator_initial_condition():
    inp = {"omega": 1.0, "zeta": 0.1, "x0": 2.5, "v0": 0.0, "dt": 0.01, "steps": 10}
    result = damped_oscillator(inp)
    assert abs(result["x"][0] - 2.5) < 1e-12


def test_damped_oscillator_amplitude_bounded_by_envelope():
    """Numerical solution amplitude should stay below analytical envelope."""
    inp = {"omega": 2.0, "zeta": 0.15, "x0": 1.0, "v0": 0.0, "dt": 0.05, "steps": 200}
    result = damped_oscillator(inp)
    x = np.array(result["x"])
    envelope = np.array(result["envelope"])
    # Allow 5% tolerance for the Euler integration error
    assert np.all(np.abs(x) <= envelope + 0.05)


def test_damped_oscillator_decays_to_near_zero():
    inp = {"omega": 2.0, "zeta": 0.5, "x0": 1.0, "v0": 0.0, "dt": 0.05, "steps": 200}
    result = damped_oscillator(inp)
    # High damping: should be close to 0 at end
    assert abs(result["x"][-1]) < 0.1


def test_damped_oscillator_envelope_monotone_decreasing():
    inp = {"omega": 2.0, "zeta": 0.3, "x0": 1.0, "v0": 0.0, "dt": 0.05, "steps": 50}
    result = damped_oscillator(inp)
    env = np.array(result["envelope"])
    assert np.all(np.diff(env) <= 0)


# ---------------------------------------------------------------------------
# Negative control: zero damping
# ---------------------------------------------------------------------------


def test_zero_damping_envelope_flat():
    """Zero-damping envelope should be flat (no decay)."""
    inp = {"omega": 2.0, "zeta": 0.15, "x0": 1.0, "v0": 0.0, "dt": 0.05, "steps": 100}
    result = _zero_damping_control(inp)
    env = np.array(result["envelope"])
    # All envelope values should equal x0 = 1.0
    assert np.allclose(env, 1.0, atol=1e-10)


def test_zero_damping_differs_from_damped():
    inp = {"omega": 2.0, "zeta": 0.3, "x0": 1.0, "v0": 0.0, "dt": 0.05, "steps": 100}
    damped = damped_oscillator(inp)
    undamped = _zero_damping_control(inp)
    # Damped envelope should be < undamped envelope at end
    assert damped["envelope"][-1] < undamped["envelope"][-1]


# ---------------------------------------------------------------------------
# PRIMITIVES registry
# ---------------------------------------------------------------------------


def test_primitives_length():
    assert len(PRIMITIVES) == 1


def test_primitives_name():
    assert PRIMITIVES[0].name == "damped_oscillator"


def test_primitives_domain():
    assert PRIMITIVES[0].domain == "dynamics"


def test_primitives_example_input():
    spec = PRIMITIVES[0]
    result = spec.fn(spec.example_input)
    assert "x" in result


def test_primitives_negative_control_exists():
    assert PRIMITIVES[0].negative_control is not None
