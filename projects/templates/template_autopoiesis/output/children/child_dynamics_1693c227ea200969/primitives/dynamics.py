"""Dynamics primitives: damped harmonic oscillator."""

from __future__ import annotations

import numpy as np

from .base import PrimitiveSpec


def damped_oscillator(inputs: dict) -> dict:
    """Simulate a damped harmonic oscillator.

    x''(t) + 2*zeta*omega*x'(t) + omega^2*x(t) = 0

    inputs: omega, zeta, x0, v0, dt, steps
    Returns: t array, x array, analytical envelope
    """
    omega = float(inputs.get("omega", 1.0))
    zeta = float(inputs.get("zeta", 0.1))
    x0 = float(inputs.get("x0", 1.0))
    v0 = float(inputs.get("v0", 0.0))
    dt = float(inputs.get("dt", 0.05))
    steps = int(inputs.get("steps", 200))

    t = np.linspace(0, steps * dt, steps + 1)
    x = np.zeros(steps + 1)
    v = np.zeros(steps + 1)
    x[0] = x0
    v[0] = v0

    for i in range(steps):
        acc = -(2 * zeta * omega * v[i] + omega**2 * x[i])
        v[i + 1] = v[i] + acc * dt
        x[i + 1] = x[i] + v[i + 1] * dt

    # Analytical envelope (under-damped)
    envelope = x0 * np.exp(-zeta * omega * t)
    return {"t": t, "x": x, "envelope": envelope}


def _zero_damping_control(inputs: dict) -> dict:
    """Zero-damping control: oscillator should not decay."""
    inp = dict(inputs)
    inp["zeta"] = 0.0
    result = damped_oscillator(inp)
    # The envelope should be flat (no decay)
    return result


_EXAMPLE = {"omega": 2.0, "zeta": 0.15, "x0": 1.0, "v0": 0.0, "dt": 0.05, "steps": 200}

PRIMITIVES: tuple[PrimitiveSpec, ...] = (
    PrimitiveSpec(
        name="damped_oscillator",
        domain="dynamics",
        fn=damped_oscillator,
        callable_name="damped_oscillator",
        example_input=_EXAMPLE,
        expected=None,  # validated by envelope bound
        tolerance=0.05,
        negative_control=_zero_damping_control,
    ),
)
