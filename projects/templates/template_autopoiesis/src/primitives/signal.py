"""Signal primitives: DFT and convolution."""
from __future__ import annotations

import numpy as np

from .base import PrimitiveSpec


def dft(inputs: dict) -> dict:
    """Compute the Discrete Fourier Transform of a signal.

    inputs: signal (1-D array)
    Returns: spectrum (complex ndarray), magnitudes, phases
    """
    x = np.array(inputs["signal"], dtype=float)
    N = len(x)
    n = np.arange(N)
    k = n.reshape((N, 1))
    M = np.exp(-2j * np.pi * k * n / N)
    spectrum = M @ x
    return {
        "spectrum": spectrum,
        "magnitudes": np.abs(spectrum),
        "phases": np.angle(spectrum),
    }


def convolve_known(inputs: dict) -> dict:
    """Convolve signal with a known kernel using numpy.

    inputs: signal (1-D), kernel (1-D)
    Returns: output (1-D)
    """
    signal = np.array(inputs["signal"], dtype=float)
    kernel = np.array(inputs["kernel"], dtype=float)
    output = np.convolve(signal, kernel, mode=inputs.get("mode", "full"))
    return {"output": output}


def _identity_kernel_convolve(inputs: dict) -> dict:
    """Convolve with the identity kernel [1]: output == input."""
    inp = dict(inputs)
    inp["kernel"] = [1.0]
    inp["mode"] = "same"
    return convolve_known(inp)


_SIGNAL = np.sin(2 * np.pi * 5 * np.linspace(0, 1, 64)).tolist()
_KERNEL = [0.25, 0.5, 0.25]  # smoothing kernel

_EXAMPLE_DFT = {"signal": _SIGNAL}
_EXAMPLE_CONV = {"signal": _SIGNAL, "kernel": _KERNEL, "mode": "same"}

PRIMITIVES: tuple[PrimitiveSpec, ...] = (
    PrimitiveSpec(
        name="dft",
        domain="signal",
        fn=dft,
        callable_name="dft",
        example_input=_EXAMPLE_DFT,
        expected=None,  # validated by Parseval and symmetry
        tolerance=1e-8,
    ),
    PrimitiveSpec(
        name="convolve_known",
        domain="signal",
        fn=convolve_known,
        callable_name="convolve_known",
        example_input=_EXAMPLE_CONV,
        expected=None,
        tolerance=1e-10,
        negative_control=_identity_kernel_convolve,
    ),
)
