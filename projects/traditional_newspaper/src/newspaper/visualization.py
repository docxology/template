"""Black-and-white matplotlib figures derived from manuscript metrics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from cycler import cycler  # noqa: E402


def configure_matplotlib_bw_style() -> None:
    """Apply monochrome defaults for print-friendly figures.

    Sets a grayscale prop cycle and gray colormap so incidental draws stay
    black-and-white unless callers override explicitly.
    """
    plt.rcParams.update(
        {
            "axes.prop_cycle": cycler("color", ["0", "0.25", "0.45", "0.65"]),
            "image.cmap": "gray",
            "savefig.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "black",
            "axes.labelcolor": "black",
            "xtick.color": "black",
            "ytick.color": "black",
            "text.color": "black",
            "grid.color": "0.5",
            "grid.linestyle": ":",
        }
    )


def wordcount_pairs_from_manuscript_stats(data: dict[str, Any]) -> list[tuple[str, int]]:
    """Build ``(label, words)`` rows from ``manuscript_stats.json`` payload.

    Args:
        data: Parsed JSON with ``files`` list of dicts containing ``path`` and ``words``.

    Returns:
        Ordered list of stem labels (filename without ``.md``) and word counts.
    """
    files = data.get("files")
    if not isinstance(files, list):
        return []
    out: list[tuple[str, int]] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        path_s = item.get("path")
        words = item.get("words")
        if not isinstance(path_s, str) or not isinstance(words, int):
            continue
        stem = Path(path_s).stem
        out.append((stem, words))
    return out


def load_manuscript_stats(path: Path) -> dict[str, Any]:
    """Load and parse ``manuscript_stats.json``."""
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("manuscript stats root must be a JSON object")
    return data


def render_wordcount_bar_chart_bw(
    path: Path,
    entries: Sequence[tuple[str, int]],
    *,
    dpi: int = 150,
    fig_width_in: float = 7.0,
    bar_face: str = "0.35",
    bar_edge: str = "black",
) -> Path:
    """Write a horizontal bar chart of word counts (grayscale only).

    Args:
        path: Output PNG path; parent directories are created.
        entries: ``(label, word_count)`` in display order (top to bottom).
        dpi: Rasterization resolution.
        fig_width_in: Figure width in inches; height scales with row count.
        bar_face: Grayscale matplotlib color spec for bars (default mid-gray).
        bar_edge: Edge color for bars.

    Returns:
        ``path`` after writing.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    configure_matplotlib_bw_style()

    labels = [e[0] for e in entries]
    values = [max(0, int(e[1])) for e in entries]
    n = len(labels)
    if n == 0:
        fig_h = 2.0
    else:
        fig_h = max(3.0, 0.22 * n + 1.2)

    fig, ax = plt.subplots(figsize=(fig_width_in, fig_h), dpi=dpi)
    y_pos = range(n)
    ax.barh(
        list(y_pos),
        values,
        height=0.65,
        color=bar_face,
        edgecolor=bar_edge,
        linewidth=0.6,
    )
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("Words")
    ax.set_title("Manuscript word counts by file (B&W)")
    ax.grid(axis="x", alpha=0.85)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(path, format="png", dpi=dpi, facecolor="white")
    plt.close(fig)
    return path


def render_wordcount_chart_from_stats_file(
    stats_json: Path,
    out_png: Path,
    *,
    dpi: int = 150,
) -> Path:
    """Load stats JSON and write the word-count bar chart PNG.

    Args:
        stats_json: Path to ``manuscript_stats.json``.
        out_png: Output PNG path.

    Returns:
        ``out_png`` after writing.
    """
    data = load_manuscript_stats(stats_json)
    pairs = wordcount_pairs_from_manuscript_stats(data)
    return render_wordcount_bar_chart_bw(out_png, pairs, dpi=dpi)
