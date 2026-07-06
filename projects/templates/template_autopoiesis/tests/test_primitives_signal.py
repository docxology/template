"""Tests for signal primitives: dft and convolve_known."""
from __future__ import annotations

import numpy as np

from src.primitives.signal import dft, convolve_known, _identity_kernel_convolve, PRIMITIVES


_SIGNAL = (np.sin(2 * np.pi * 5 * np.linspace(0, 1, 64))).tolist()
_KERNEL = [0.25, 0.5, 0.25]


# ---------------------------------------------------------------------------
# dft
# ---------------------------------------------------------------------------


def test_dft_returns_dict():
    result = dft({"signal": _SIGNAL})
    assert "spectrum" in result and "magnitudes" in result and "phases" in result


def test_dft_spectrum_length():
    result = dft({"signal": _SIGNAL})
    assert len(result["spectrum"]) == 64


def test_dft_parseval():
    """Parseval's theorem: sum(|X[k]|^2) = N * sum(|x[n]|^2)."""
    x = np.array(_SIGNAL)
    result = dft({"signal": _SIGNAL})
    N = len(x)
    lhs = float(np.sum(np.abs(result["spectrum"]) ** 2))
    rhs = N * float(np.sum(x ** 2))
    assert abs(lhs - rhs) / (rhs + 1e-12) < 1e-6


def test_dft_magnitudes_nonneg():
    result = dft({"signal": _SIGNAL})
    assert np.all(np.array(result["magnitudes"]) >= 0)


def test_dft_single_frequency():
    """Pure 5 Hz tone in 64-sample signal: dominant frequency bin is 5."""
    result = dft({"signal": _SIGNAL})
    mags = np.array(result["magnitudes"])
    dominant = int(np.argmax(mags))
    assert dominant == 5 or dominant == 64 - 5  # positive or negative freq


def test_dft_different_signal_different_spectrum():
    r1 = dft({"signal": _SIGNAL})
    # Use a completely different signal (cosine at different frequency)
    signal2 = np.cos(2 * np.pi * 13 * np.linspace(0, 1, 64)).tolist()
    r2 = dft({"signal": signal2})
    mags1 = np.array(r1["magnitudes"])
    mags2 = np.array(r2["magnitudes"])
    assert not np.allclose(mags1, mags2)


# ---------------------------------------------------------------------------
# convolve_known
# ---------------------------------------------------------------------------


def test_convolve_known_returns_dict():
    result = convolve_known({"signal": _SIGNAL, "kernel": _KERNEL, "mode": "same"})
    assert "output" in result


def test_convolve_known_output_length_full():
    sig = [1.0] * 10
    ker = [1.0] * 3
    result = convolve_known({"signal": sig, "kernel": ker, "mode": "full"})
    assert len(result["output"]) == 10 + 3 - 1


def test_convolve_known_output_length_same():
    result = convolve_known({"signal": _SIGNAL, "kernel": _KERNEL, "mode": "same"})
    assert len(result["output"]) == len(_SIGNAL)


def test_convolve_known_smoothing_reduces_variance():
    """Smoothing kernel should reduce variance."""
    x = np.array(_SIGNAL)
    result = convolve_known({"signal": _SIGNAL, "kernel": _KERNEL, "mode": "same"})
    y = np.array(result["output"])
    assert float(np.var(y)) <= float(np.var(x)) + 1e-6


# ---------------------------------------------------------------------------
# Negative control: identity kernel
# ---------------------------------------------------------------------------


def test_identity_kernel_preserves_signal():
    result = _identity_kernel_convolve({"signal": _SIGNAL, "kernel": _KERNEL, "mode": "same"})
    x = np.array(_SIGNAL)
    out = np.array(result["output"])
    assert np.allclose(out, x, atol=1e-12)


def test_identity_differs_from_smoothing():
    smoothed = convolve_known({"signal": _SIGNAL, "kernel": _KERNEL, "mode": "same"})
    identity = _identity_kernel_convolve({"signal": _SIGNAL, "kernel": _KERNEL, "mode": "same"})
    assert not np.allclose(smoothed["output"], identity["output"])


# ---------------------------------------------------------------------------
# PRIMITIVES registry
# ---------------------------------------------------------------------------


def test_primitives_length():
    assert len(PRIMITIVES) == 2


def test_primitives_names():
    names = {p.name for p in PRIMITIVES}
    assert names == {"dft", "convolve_known"}


def test_primitives_domain():
    for p in PRIMITIVES:
        assert p.domain == "signal"


def test_dft_example_input():
    spec = next(p for p in PRIMITIVES if p.name == "dft")
    result = spec.fn(spec.example_input)
    assert len(result["magnitudes"]) == 64


def test_convolve_negative_control_exists():
    spec = next(p for p in PRIMITIVES if p.name == "convolve_known")
    assert spec.negative_control is not None
