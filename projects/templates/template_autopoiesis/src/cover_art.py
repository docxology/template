"""Cover art: ouroboros autopoiesis diagram.

Renders a pure-matplotlib ouroboros ring with domain labels, seed dots,
gradient glow, and publication metadata.  The image is deterministic given
the same grammar seed and domain list.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

DOMAIN_COLORS = {
    "optimization": "#0d9488",
    "dynamics": "#1d4ed8",
    "statistics": "#7c3aed",
    "signal": "#db2777",
    "graph": "#d97706",
}

FALLBACK_COLORS = [
    "#0d9488", "#1d4ed8", "#7c3aed", "#db2777", "#d97706",
    "#059669", "#2563eb", "#9333ea",
]


@dataclass(frozen=True)
class BranchSegment:
    """A single arc segment on the ouroboros ring."""

    domain: str
    theta_start: float
    theta_end: float
    color: str
    radius: float


def ring_root_angles(n_domains: int) -> list[float]:
    """Return evenly-spaced angles for *n_domains* domain roots."""
    return [2 * math.pi * i / n_domains for i in range(n_domains)]


def domain_root_indices(domains: tuple[str, ...]) -> dict[str, int]:
    return {d: i for i, d in enumerate(domains)}


def branch_segments(
    domains: tuple[str, ...],
    radius: float = 1.0,
    gap_fraction: float = 0.05,
) -> list[BranchSegment]:
    """Build arc segments for the ouroboros ring."""
    n = len(domains)
    arc_size = 2 * math.pi / n
    gap = arc_size * gap_fraction
    segments = []
    for i, domain in enumerate(domains):
        theta_start = arc_size * i + gap / 2
        theta_end = arc_size * (i + 1) - gap / 2
        color = DOMAIN_COLORS.get(domain, FALLBACK_COLORS[i % len(FALLBACK_COLORS)])
        segments.append(
            BranchSegment(
                domain=domain,
                theta_start=theta_start,
                theta_end=theta_end,
                color=color,
                radius=radius,
            )
        )
    return segments


def build_ring_geometry(
    domains: tuple[str, ...],
    radius: float = 1.0,
) -> list[BranchSegment]:
    return branch_segments(domains, radius=radius)


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def render_cover(
    domains: tuple[str, ...],
    seed: int,
    out_path: str | Path,
    title: str = "Autopoietic Project Generation",
    subtitle: str = "A combinatoric grammar for deterministic project generation",
    author: str = "template_autopoiesis",
    figsize: tuple[float, float] = (8, 8),
    dpi: int = 150,
) -> Path:
    """Render the cover art to *out_path* and return the resolved Path."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize, subplot_kw={"aspect": "equal"})
    ax.set_xlim(-1.8, 1.8)
    ax.set_ylim(-2.2, 2.2)
    ax.axis("off")
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#0f172a")

    ring_r = 1.0
    ring_width = 0.25
    segments = build_ring_geometry(domains, radius=ring_r)

    # Draw gradient glow behind ring
    for layer in range(6, 0, -1):
        glow_r = ring_r + ring_width * 0.5 + layer * 0.04
        glow_alpha = 0.04
        glow_circle = mpatches.Circle(
            (0, 0), glow_r, fill=False, linewidth=ring_width * 20 / layer,
            edgecolor="#60a5fa", alpha=glow_alpha,
        )
        ax.add_patch(glow_circle)

    # Draw arc segments
    for seg in segments:
        theta = np.linspace(seg.theta_start, seg.theta_end, 80)
        xs_outer = (ring_r + ring_width / 2) * np.cos(theta)
        ys_outer = (ring_r + ring_width / 2) * np.sin(theta)
        xs_inner = (ring_r - ring_width / 2) * np.cos(theta)
        ys_inner = (ring_r - ring_width / 2) * np.sin(theta)

        xs = np.concatenate([xs_outer, xs_inner[::-1], [xs_outer[0]]])
        ys = np.concatenate([ys_outer, ys_inner[::-1], [ys_outer[0]]])
        ax.fill(xs, ys, color=seg.color, alpha=0.85, zorder=3)

        # Domain label
        mid_theta = (seg.theta_start + seg.theta_end) / 2
        label_r = ring_r + ring_width / 2 + 0.22
        lx = label_r * math.cos(mid_theta)
        ly = label_r * math.sin(mid_theta)
        ax.text(
            lx, ly, seg.domain,
            ha="center", va="center",
            fontsize=10, color=seg.color,
            fontweight="bold",
            bbox=dict(
                facecolor="#1e293b", edgecolor=seg.color,
                boxstyle="round,pad=0.2", alpha=0.8,
            ),
            zorder=5,
        )

    # Seed dots
    rng = np.random.default_rng(seed)
    n_dots = 40
    dot_angles = rng.uniform(0, 2 * math.pi, n_dots)
    dot_radii = rng.uniform(ring_r - ring_width / 2, ring_r + ring_width / 2, n_dots)
    dot_x = dot_radii * np.cos(dot_angles)
    dot_y = dot_radii * np.sin(dot_angles)
    ax.scatter(dot_x, dot_y, s=8, color="white", alpha=0.5, zorder=4)

    # Seal ring (thin outer border)
    seal_circle = mpatches.Circle(
        (0, 0), ring_r + ring_width / 2 + 0.04,
        fill=False, linewidth=1.2, edgecolor="#94a3b8", alpha=0.6, zorder=6,
    )
    ax.add_patch(seal_circle)

    # Center text: seed
    ax.text(
        0, 0.12, f"seed={seed}",
        ha="center", va="center", fontsize=9, color="#94a3b8",
        fontfamily="monospace",
    )
    ax.text(
        0, -0.12, f"{len(domains)} domains",
        ha="center", va="center", fontsize=9, color="#64748b",
    )

    # Title
    ax.text(
        0, 1.75, title,
        ha="center", va="center", fontsize=14, color="#f8fafc",
        fontweight="bold",
    )

    # Subtitle rule
    ax.plot([-1.2, 1.2], [1.58, 1.58], color="#334155", linewidth=1.0, zorder=2)
    ax.text(
        0, 1.48, subtitle,
        ha="center", va="center", fontsize=8, color="#94a3b8",
        style="italic",
    )

    # Author separator
    ax.plot([-0.6, 0.6], [-1.72, -1.72], color="#334155", linewidth=0.8, zorder=2)
    ax.text(
        0, -1.85, author,
        ha="center", va="center", fontsize=9, color="#64748b",
        fontfamily="monospace",
    )

    fig.tight_layout(pad=0)
    fig.savefig(out, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out
