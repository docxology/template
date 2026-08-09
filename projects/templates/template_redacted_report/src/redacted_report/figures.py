"""Deterministic redaction-exemplar figures (SVG + PNG companions).

Business logic for the two declared figure types (``redaction_flow`` and
``disclosure_control_matrix``, matching ``domain_profile.yaml``
``figure_types``). Every figure is derived from the same invented fixture and
the same visual-profile constants as the proof matrix, so the published
figures never disagree with the release-audit source of truth.

Matplotlib is imported lazily inside the builder functions so module import
stays cheap for tests that only need the registry helpers. The Agg backend is
forced before any pyplot use so figure generation works headless and is
byte-deterministic within a fixed rendering environment.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from redacted_report.profiles import PDF_BACKGROUND_MODES, REDACTION_VISUAL_STYLES

_CANVAS_INCHES = (10.0, 5.4)
_DPI = 150
_MAX_PX_HEIGHT = 1600

FIGURE_SPECS: tuple[dict[str, str], ...] = (
    {
        "name": "redaction_flow",
        "label": "fig:redaction_flow",
        "caption": (
            "Release-review pipeline: the disclosure-control layer audits the invented fixture "
            "against the public ceiling and builds an in-memory sanitized packet, the evidence "
            "layer projects text-free audit and hashed-ledger JSON, and the visual layer renders "
            "the 4x4 proof matrix with optional steganography and Kmyth TPM sidecars."
        ),
        "alt_text": (
            "Two-layer flow diagram. Layer one runs disclosure control: typed fixture load, "
            "classification ceiling and span validation, orphan and coverage checks, then an "
            "in-memory sanitized packet. Layer two projects a text-free audit and hashed release "
            "ledger, then renders the 4x4 visual proof matrix with steganography and optional "
            "Kmyth TPM sidecar sealing."
        ),
        "section": "Architecture",
        "generated_by": "redacted_report.figures.build_figures",
    },
    {
        "name": "disclosure_control_matrix",
        "label": "fig:disclosure_control_matrix",
        "caption": (
            "Development proof matrix: four redaction styles (blackout, whiteout, grayout, blur) "
            "rendered across four PDF backgrounds (white, gray, black, blur). Every one of the "
            "sixteen cells applies the identical source-safe redaction decisions, so visual "
            "presentation stays orthogonal to the release gate."
        ),
        "alt_text": (
            "A four-by-four grid of redaction style tokens (blackout, whiteout, grayout, blur) "
            "on PDF backgrounds (white, gray, black, blur), with the note that all sixteen "
            "variants apply identical source-safe redaction decisions."
        ),
        "section": "Results",
        "generated_by": "redacted_report.figures.build_figures",
    },
)

_REGISTRY_FIELDS = ("label", "filename", "caption", "section", "width", "placement", "generated_by")


def _spec_by_name(name: str) -> dict[str, str]:
    for spec in FIGURE_SPECS:
        if spec["name"] == name:
            return spec
    raise KeyError(f"unknown figure spec: {name}")


def _rgb(profile_rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    return tuple(channel / 255.0 for channel in profile_rgb)  # type: ignore[return-value]


def _inject_svg_accessibility(svg_text: str, title: str, desc: str) -> str:
    """Add role/title/desc accessibility markup to a matplotlib SVG string."""
    import re

    escaped = desc.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # matplotlib stamps a live <dc:date> into the SVG metadata; drop it so the
    # companion SVG is byte-deterministic across runs (the PNG writer does not
    # embed a timestamp).
    svg_text = re.sub(r"\s*<dc:date>[^<]*</dc:date>", "", svg_text)
    svg_text = svg_text.replace(
        "<svg ",
        '<svg role="img" aria-labelledby="fig-title fig-desc" ',
        1,
    )
    markup = f'<title id="fig-title">{title}</title>\n<desc id="fig-desc">{escaped}</desc>'
    return svg_text.replace("<defs>", f"<defs>\n{markup}", 1)


def _draw_flow_figure(spec: Mapping[str, str], output_png: Path, output_svg: Path) -> None:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    matplotlib.use("Agg", force=True)
    # Fixed salt makes matplotlib's SVG element ids deterministic across runs
    # (ids are otherwise derived from object memory addresses).
    matplotlib.rcParams["svg.hashsalt"] = "template_redacted_report"
    fig, ax = plt.subplots(figsize=_CANVAS_INCHES, dpi=_DPI)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.4)
    ax.axis("off")

    def box(x: float, y: float, w: float, h: float, text: str, *, fill: tuple[float, float, float]) -> None:
        """Draw one rounded flow-chart box with centered wrapped text."""
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02",
            linewidth=1.1,
            edgecolor=(0.15, 0.15, 0.15),
            facecolor=fill,
        )
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.2, wrap=True)

    def arrow(x1: float, y1: float, x2: float, y2: float) -> None:
        """Draw one directed flow-chart connector between two coordinates."""
        ax.add_patch(
            FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle="-|>",
                mutation_scale=11,
                linewidth=1.0,
                color=(0.25, 0.25, 0.25),
            )
        )

    ax.text(5, 5.12, "Layer 1 - disclosure control", ha="center", fontsize=9.5, fontweight="bold")
    box(0.3, 4.35, 2.1, 0.55, "Typed fixture\n(data/example_segments.json)", fill=(0.92, 0.95, 0.98))
    arrow(2.4, 4.62, 2.95, 4.62)
    box(2.95, 4.35, 2.9, 0.55, "Classification ceiling + span / overlap / orphan checks", fill=(0.88, 0.94, 0.97))
    arrow(5.85, 4.62, 6.4, 4.62)
    box(6.4, 4.35, 2.2, 0.55, "Source-control coverage + mosaic-risk score", fill=(0.88, 0.94, 0.97))
    arrow(8.6, 4.62, 9.15, 4.62)
    box(9.15, 4.35, 0.7, 0.55, "Gate?", fill=(0.95, 0.9, 0.82))

    box(2.0, 3.2, 3.0, 0.6, "In-memory sanitized release packet", fill=(0.9, 0.98, 0.92))
    arrow(4.35, 4.35, 4.35, 3.82)
    arrow(3.0, 3.2, 1.6, 2.5)
    arrow(5.0, 3.2, 6.6, 2.5)

    ax.text(5, 2.85, "Layer 2 - evidence and visual proof", ha="center", fontsize=9.5, fontweight="bold")
    box(0.2, 1.85, 2.7, 0.6, "output/reports/redaction_audit.json\ntext-free audit", fill=(0.97, 0.95, 0.93))
    box(4.6, 1.85, 2.7, 0.6, "output/data/release_ledger.json\nhashed ledger", fill=(0.97, 0.95, 0.93))
    box(8.0, 1.85, 1.8, 0.6, "review gate\n3 roles", fill=(0.97, 0.95, 0.93))
    arrow(1.55, 1.85, 1.55, 1.5)
    arrow(5.95, 1.85, 5.95, 1.5)
    arrow(8.9, 1.85, 8.9, 1.5)
    box(0.2, 0.75, 2.7, 0.6, "4x4 visual proof matrix\n(styles x backgrounds)", fill=(0.93, 0.9, 0.97))
    arrow(2.9, 1.05, 3.85, 1.05)
    box(3.85, 0.75, 2.6, 0.6, "Steganography\n(9 security methods)", fill=(0.93, 0.9, 0.97))
    arrow(6.45, 1.05, 7.4, 1.05)
    box(7.4, 0.75, 2.4, 0.6, "Kmyth TPM .ski sidecars\n(optional)", fill=(0.93, 0.9, 0.97))

    fig.tight_layout(pad=0.4)
    fig.savefig(output_png, format="png")
    fig.savefig(output_svg, format="svg")
    plt.close(fig)


def _draw_matrix_figure(spec: Mapping[str, str], output_png: Path, output_svg: Path) -> None:
    import matplotlib
    import matplotlib.pyplot as plt

    matplotlib.use("Agg", force=True)
    # Fixed salt makes matplotlib's SVG element ids deterministic across runs
    # (ids are otherwise derived from object memory addresses).
    matplotlib.rcParams["svg.hashsalt"] = "template_redacted_report"
    fig, ax = plt.subplots(figsize=_CANVAS_INCHES, dpi=_DPI)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.4)
    ax.axis("off")

    styles = REDACTION_VISUAL_STYLES
    backgrounds = PDF_BACKGROUND_MODES
    n_rows = len(styles)
    cell_w = 1.7
    cell_h = 0.78
    x0 = 1.55
    y0 = 2.4

    ax.text(5, 5.05, "Redaction style x PDF background proof matrix", ha="center", fontsize=10, fontweight="bold")

    for col, background in enumerate(backgrounds):
        ax.text(
            x0 + col * cell_w + cell_w / 2,
            y0 + n_rows * cell_h + 0.22,
            background.label,
            ha="center",
            va="center",
            fontsize=8.5,
            fontweight="bold",
        )
    for row, style in enumerate(styles):
        ax.text(
            x0 - 0.28,
            y0 + (n_rows - 1 - row) * cell_h + cell_h / 2,
            style.label,
            ha="right",
            va="center",
            fontsize=8.5,
            fontweight="bold",
        )
    for row, style in enumerate(styles):
        for col, background in enumerate(backgrounds):
            x = x0 + col * cell_w
            y = y0 + (n_rows - 1 - row) * cell_h
            cell_fill = _rgb(background.fill_rgb)
            ax.add_patch(
                plt.Rectangle(
                    (x, y),
                    cell_w,
                    cell_h,
                    facecolor=cell_fill,
                    edgecolor=(0.2, 0.2, 0.2),
                    linewidth=0.9,
                )
            )
            # Faithful preview: an inset redaction bar in the style's fill with
            # the style's token text, on the page background (mirrors the
            # proof-PDF composition in redacted_report._proof_renderer).
            bar_x = x + cell_w * 0.12
            bar_w = cell_w * 0.76
            bar_y = y + cell_h * 0.14
            bar_h = cell_h * 0.52
            ax.add_patch(
                plt.Rectangle(
                    (bar_x, bar_y),
                    bar_w,
                    bar_h,
                    facecolor=_rgb(style.fill_rgb),
                    edgecolor=_rgb(style.border_rgb),
                    linewidth=0.8,
                )
            )
            ax.text(
                bar_x + bar_w / 2,
                bar_y + bar_h / 2,
                style.token,
                ha="center",
                va="center",
                fontsize=6.6,
                color=_rgb(style.text_rgb),
            )
            label_color = (0.12, 0.12, 0.12) if background.fill_rgb != (0, 0, 0) else (0.92, 0.92, 0.92)
            ax.text(
                x + cell_w / 2,
                y + cell_h * 0.12,
                f"{background.name} background",
                ha="center",
                va="center",
                fontsize=6.0,
                color=label_color,
            )

    ax.text(
        5,
        1.55,
        "All sixteen variants apply the identical source-safe redaction decisions;"
        "\nonly the visual token and page background differ.",
        ha="center",
        va="center",
        fontsize=8.0,
        color=(0.25, 0.25, 0.25),
    )

    legend_items = [f"{style.label}: {style.token}" for style in styles]
    ax.text(
        5,
        0.75,
        "Styles: " + "  |  ".join(legend_items),
        ha="center",
        va="center",
        fontsize=7.2,
        color=(0.3, 0.3, 0.3),
    )

    fig.tight_layout(pad=0.4)
    fig.savefig(output_png, format="png")
    fig.savefig(output_svg, format="svg")
    plt.close(fig)


def _build_one(spec: Mapping[str, str], output_dir: Path) -> None:
    name = str(spec["name"])
    png_path = output_dir / f"{name}.png"
    svg_path = output_dir / f"{name}.svg"
    if name == "redaction_flow":
        _draw_flow_figure(spec, png_path, svg_path)
    elif name == "disclosure_control_matrix":
        _draw_matrix_figure(spec, png_path, svg_path)
    else:  # pragma: no cover - guarded by the spec table itself
        raise KeyError(f"no builder for figure: {name}")
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        _inject_svg_accessibility(svg_text, title=str(spec["caption"]), desc=str(spec["alt_text"])),
        encoding="utf-8",
    )


def build_figure_registry() -> dict[str, dict[str, object]]:
    """Return the deterministic figure registry for this exemplar."""
    registry: dict[str, dict[str, object]] = {}
    for index, spec in enumerate(FIGURE_SPECS):
        name = str(spec["name"])
        registry[str(spec["label"])] = {
            "figure_id": f"figure_{index:03d}",
            "filename": f"{name}.png",
            "caption": str(spec["caption"]),
            "label": str(spec["label"]),
            "section": str(spec["section"]),
            "width": "0.9\\textwidth",
            "placement": "h",
            "generated_by": str(spec["generated_by"]),
            "metadata": {
                "alt_text": str(spec["alt_text"]),
                "source": "template_redacted_report analysis pipeline",
            },
        }
    return registry


def build_figures(output_dir: Path) -> dict[str, dict[str, object]]:
    """Write both figures (PNG + SVG companions) and the registry.

    Deterministic for a fixed matplotlib version: no randomness, fixed canvas,
    fixed palette from :mod:`redacted_report.profiles`. Returns the registry.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for spec in FIGURE_SPECS:
        _build_one(spec, output_dir)
    registry = build_figure_registry()
    registry_path = output_dir / "figure_registry.json"
    registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return registry


def _height_px(png_path: Path) -> int:
    import matplotlib.image as mpimg

    image = mpimg.imread(str(png_path))
    return int(image.shape[0])


__all__ = [
    "FIGURE_SPECS",
    "build_figure_registry",
    "build_figures",
    "_height_px",
]
