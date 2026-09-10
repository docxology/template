"""Figure rendering for template_autopoiesis.

Provides domain-agnostic figure rendering on top of primitive kernel outputs,
plus a figure registry builder used by the manuscript pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np


def _first_plottable_array(result: Any) -> Optional[np.ndarray]:
    """Extract the first plottable array from a primitive result."""
    if isinstance(result, np.ndarray) and result.ndim >= 1:
        return result.ravel()
    if isinstance(result, (list, tuple)) and result:
        arr = np.array(result, dtype=float)
        return arr.ravel()
    return None


def _scalar_summary_lines(result: Any) -> list[str]:
    """Return human-readable summary lines for a scalar-ish result."""
    if isinstance(result, (int, float, complex)):
        return [f"value = {result:.6g}"]
    if isinstance(result, np.ndarray):
        mean = "n/a" if result.size == 0 else f"{float(result.mean()):.6g}"
        return [f"shape = {result.shape}", f"mean = {mean}"]
    if isinstance(result, dict):
        return [f"{k} = {v!r}" for k, v in list(result.items())[:4]]
    return [repr(result)[:80]]


def render_primitive_figure(
    name: str,
    result: Any,
    out_path: str | Path,
    title: Optional[str] = None,
) -> Path:
    """Render a figure from a primitive result and save to *out_path*."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 4))
    arr = _first_plottable_array(result)
    if arr is not None and len(arr) > 1:
        ax.plot(arr, color="#0d9488", linewidth=2)
        ax.set_xlabel("index")
        ax.set_ylabel("value")
    else:
        summary = _scalar_summary_lines(result)
        ax.text(0.5, 0.5, "\n".join(summary), ha="center", va="center", transform=ax.transAxes, fontsize=12)
        ax.axis("off")

    ax.set_title(title or name)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def build_figure_registry(
    domain: str,
    results: list[tuple[str, Any]],
    out_dir: str | Path,
) -> dict[str, Path]:
    """Render figures for all *results* and return a name→path registry."""
    out_dir = Path(out_dir)
    registry: dict[str, Path] = {}
    for name, result in results:
        fig_path = out_dir / f"{domain}_{name}.png"
        registry[name] = render_primitive_figure(name, result, fig_path)
    return registry
