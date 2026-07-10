"""Deterministic procedural manuscript cover art.

No external AI image-generation API, no network call, no binary blob
copied in from an untracked source -- a stylized ant-robot silhouette
with a cross-sectioned abdomen exposing an interlocking type-lattice
(illegal shapes have nowhere left to fit), standing over a faint
database/network-grid floor. It remains an optional presentation surface (a
missing matplotlib returns ``None`` and logs why), while the analysis figures
in :mod:`template_formal.colony.visualization` are required by the publication
pipeline and fail closed when expected output cannot be rendered. Both keep
figure construction in ``src/`` so scripts only orchestrate.

Every random choice (leg-knee jitter, lattice-cell fill color) is drawn
from a seeded ``random.Random`` instance, never the process-global
``random`` module, so the same seed always draws the same composition.
See ``tests/colony/test_cover_art.py`` for what is and is not asserted
about reproducibility: within one process/environment the same seed
produces a byte-identical PNG (proving the seed is actually consumed,
not merely accepted); byte-identity is *not* claimed across matplotlib
versions or platforms, where font/anti-aliasing differences are expected
-- the same honesty discipline as the rest of this template's
figure-generation tests.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.axes import Axes

COVER_ART_FILENAME = "cover_colony.png"

_BACKGROUND = "#0B1220"
_COPPER = "#D9A441"
_COPPER_DARK = "#B8732E"
_TEAL = "#5FB3B3"
_CHARCOAL = "#16202C"
_LATTICE_FILLS = ("#D9A441", "#5FB3B3", "#EDEDED", "#B8732E")

_HEAD_CENTER = (3.0, 6.6)
_HEAD_RADIUS = 0.45
_THORAX_CENTER = (3.0, 5.55)
_THORAX_SIZE = (1.5, 1.1)
_ABDOMEN_CENTER = (3.0, 3.85)
_ABDOMEN_SIZE = (2.6, 2.0)


def generate_cover_art(output_path: Path, *, seed: int = 0) -> Path | None:
    """Render the ant-robot/type-lattice cover illustration to ``output_path``.

    Returns the written path, or ``None`` if matplotlib is unavailable or
    rendering fails for any reason -- this is presentation, not a
    pipeline invariant, so it degrades the same way
    :func:`template_formal.colony.visualization.write_demo_convergence_figure`
    does rather than raising.
    """
    try:
        import matplotlib.pyplot as plt

        rng = random.Random(seed)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(6.0, 8.0), dpi=200)
        fig.patch.set_facecolor(_BACKGROUND)
        ax.set_facecolor(_BACKGROUND)
        ax.set_xlim(0.0, 6.0)
        ax.set_ylim(0.0, 8.0)
        ax.set_aspect("equal")
        ax.axis("off")

        _draw_floor_lattice(ax)
        _draw_legs(ax, rng)
        _draw_antennae(ax)
        _draw_body(ax)
        _draw_abdomen_type_lattice(ax, rng)

        fig.tight_layout(pad=0)
        fig.savefig(output_path, dpi=200, facecolor=_BACKGROUND)
        plt.close(fig)
        return output_path
    except Exception as exc:  # noqa: BLE001 - safety net: rendering is optional presentation, never fails the pipeline
        print(f"cover art generation skipped: {exc}", file=sys.stderr)
        return None


def require_cover_art(output_path: Path, *, seed: int = 0) -> Path:
    written = generate_cover_art(output_path, seed=seed)
    if written is None:
        raise RuntimeError(f"required cover art was not generated: {output_path}")
    return written


def _draw_floor_lattice(ax: "Axes") -> None:
    """Faint teal grid in the lower third -- a database/network floor."""
    for y in (0.2, 0.45, 0.75, 1.1, 1.5, 2.0, 2.55):
        alpha = 0.28 * (1.0 - (y / 2.6))
        ax.plot([0.2, 5.8], [y, y], color=_TEAL, linewidth=0.6, alpha=max(alpha, 0.03))
    for x_index in range(13):
        x = 0.2 + x_index * 0.467
        ax.plot([x, x], [0.15, 2.6], color=_TEAL, linewidth=0.5, alpha=0.12)


def _draw_antennae(ax: "Axes") -> None:
    head_x, head_y = _HEAD_CENTER
    for side in (-1, 1):
        x0, y0 = head_x + side * 0.15, head_y + _HEAD_RADIUS * 0.7
        x1, y1 = head_x + side * 0.55, head_y + 0.75
        x2, y2 = head_x + side * 0.95, head_y + 0.55
        ax.plot([x0, x1, x2], [y0, y1, y2], color=_COPPER, linewidth=1.3, solid_capstyle="round")


def _draw_legs(ax: "Axes", rng: random.Random) -> None:
    hip_ys = [_THORAX_CENTER[1] + 0.35, _THORAX_CENTER[1] - 0.05, _ABDOMEN_CENTER[1] + 0.85]
    for side in (-1, 1):
        for index, hip_y in enumerate(hip_ys):
            hip_x = 3.0 + side * 0.65
            jitter = rng.uniform(-0.12, 0.12)
            knee_x = 3.0 + side * (1.5 + index * 0.18)
            knee_y = hip_y - 0.55 + jitter
            foot_x = 3.0 + side * (2.25 + index * 0.28)
            foot_y = max(hip_y - 1.65 - index * 0.15, 0.35)
            ax.plot([hip_x, knee_x], [hip_y, knee_y], color=_COPPER_DARK, linewidth=2.0, solid_capstyle="round")
            ax.plot([knee_x, foot_x], [knee_y, foot_y], color=_COPPER, linewidth=1.6, solid_capstyle="round")


def _draw_body(ax: "Axes") -> None:
    from matplotlib.patches import Ellipse

    head = Ellipse(
        _HEAD_CENTER,
        _HEAD_RADIUS * 2,
        _HEAD_RADIUS * 1.8,
        facecolor=_CHARCOAL,
        edgecolor=_COPPER,
        linewidth=1.6,
        zorder=5,
    )
    thorax = Ellipse(_THORAX_CENTER, *_THORAX_SIZE, facecolor=_CHARCOAL, edgecolor=_COPPER, linewidth=1.6, zorder=5)
    abdomen = Ellipse(_ABDOMEN_CENTER, *_ABDOMEN_SIZE, facecolor=_CHARCOAL, edgecolor=_COPPER, linewidth=1.8, zorder=4)
    ax.add_patch(abdomen)
    ax.add_patch(thorax)
    ax.add_patch(head)
    # waist connectors
    ax.plot(
        [3.0, 3.0],
        [_HEAD_CENTER[1] - _HEAD_RADIUS * 0.9, _THORAX_CENTER[1] + _THORAX_SIZE[1] / 2],
        color=_COPPER,
        linewidth=1.2,
    )
    ax.plot(
        [3.0, 3.0],
        [_THORAX_CENTER[1] - _THORAX_SIZE[1] / 2, _ABDOMEN_CENTER[1] + _ABDOMEN_SIZE[1] / 2],
        color=_COPPER,
        linewidth=1.2,
    )


def _draw_abdomen_type_lattice(ax: "Axes", rng: random.Random) -> None:
    """A hex tessellation of interlocking cells clipped inside the abdomen
    ellipse -- the "illegal states have no shape left to fit into" cutaway.
    Cells are kept only when their center lies within an inset ellipse
    (simple point-membership test, not a matplotlib clip path) so the
    result is trivial to reason about and to test.
    """
    from matplotlib.patches import RegularPolygon

    cx, cy = _ABDOMEN_CENTER
    a, b = _ABDOMEN_SIZE[0] / 2 * 0.88, _ABDOMEN_SIZE[1] / 2 * 0.88
    hex_radius = 0.22
    row_height = hex_radius * 1.5
    col_width = hex_radius * math.sqrt(3)

    num_rows = int((2 * b) / row_height) + 2
    num_cols = int((2 * a) / col_width) + 2
    for row in range(-num_rows, num_rows + 1):
        y = cy + row * row_height * 0.5
        offset = col_width / 2 if row % 2 else 0.0
        for col in range(-num_cols, num_cols + 1):
            x = cx + offset + col * col_width
            if ((x - cx) / a) ** 2 + ((y - cy) / b) ** 2 > 1.0:
                continue
            fill = _LATTICE_FILLS[rng.randrange(len(_LATTICE_FILLS))]
            cell = RegularPolygon(
                (x, y),
                numVertices=6,
                radius=hex_radius * 0.92,
                orientation=math.pi / 6,
                facecolor=fill,
                edgecolor="#F5F5F5",
                linewidth=0.4,
                alpha=0.55,
                zorder=6,
            )
            ax.add_patch(cell)


__all__ = ["COVER_ART_FILENAME", "generate_cover_art", "require_cover_art"]
