from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

from visualizations.figure_io import save_figure_png
from visualizations.figure_registry import load_figure_registry, render_figure_markdown
from visualizations.figure_style import apply_style, load_figure_style


def test_load_figure_style_defaults() -> None:
    root = Path(__file__).resolve().parents[1]
    style = load_figure_style(root)
    assert style.dpi == 160
    assert style.color("primary") == "#111827"


def test_apply_style_restores_active() -> None:
    root = Path(__file__).resolve().parents[1]
    style = load_figure_style(root)
    from visualizations.figure_style import active_style

    before = active_style()
    with apply_style(style):
        assert active_style() is style
    assert active_style() is before


def test_save_figure_png_normalizes_rgb_atomically(tmp_path: Path) -> None:
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])

    out = tmp_path / "figures" / "line.png"
    assert save_figure_png(fig, out, dpi=72) == out

    with Image.open(out) as img:
        assert img.mode == "RGB"
        assert img.size[0] > 0
        assert img.size[1] > 0
    assert not list(out.parent.glob(".line.*.png"))


def test_save_figure_png_can_skip_rgb_normalization(tmp_path: Path) -> None:
    fig, ax = plt.subplots()
    ax.scatter([0, 1], [1, 0])

    out = tmp_path / "transparent.png"
    assert save_figure_png(fig, out, dpi=72, transparent=True, normalize_rgb=False) == out

    with Image.open(out) as img:
        assert img.mode in {"RGBA", "LA", "P"}


def test_figure_registry_and_markdown() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = load_figure_registry(root)
    assert "ising_mi_curve" in registry
    assert len(registry["ising_mi_curve"].alt) >= 80
    md = render_figure_markdown(root, "ising_mi_curve", figure_number=1)
    # pandoc-crossref owns numbering: a single label, the caption in the alt slot, no hand number.
    assert "Figure 1." not in md
    assert "*Figure" not in md
    assert "../output/figures/ising_mi_curve.png" in md
    assert md.count("{#fig:ising_mi_curve") == 1
    assert "Closed-form" in md


def test_render_section_figures_for_results_mi_sweep() -> None:
    root = Path(__file__).resolve().parents[1]
    from visualizations.figure_registry import render_section_figures

    md = render_section_figures(root, "results_mi_sweep")
    assert "ising_mi_curve.png" in md
    # results reuses the methods figure: unnumbered, cited back to the canonical label.
    assert "Figure 2 (results)." not in md
    assert "Reproduced from [@fig:ising_mi_curve]" in md
    assert len(md.split("\n\n")) >= 2


def test_render_figure_markdown_unlabeled_repeat() -> None:
    root = Path(__file__).resolve().parents[1]
    md = render_figure_markdown(root, "ising_mi_curve", labeled=False)
    assert "{#fig:ising_mi_curve" not in md
    assert "{width=" in md


def test_render_figure_markdown_pandoc_owns_numbering() -> None:
    """A labeled figure emits exactly one pandoc-crossref label and NO hand-written number.

    Regression guard for the triple-numbering defect: render_figure_markdown must not emit
    any ``Figure N`` / ``*Figure ...*`` hand label even when a legacy caption_prefix/number
    is passed; pandoc-crossref is the single source of figure numbers.
    """
    root = Path(__file__).resolve().parents[1]
    md = render_figure_markdown(
        root,
        "sheaf_layers_overview",
        figure_number=6,
        caption_prefix="Figure 6 (methods). ",
    )
    assert "{#fig:sheaf_layers_overview" in md
    assert md.count("#fig:sheaf_layers_overview") == 1
    assert "Figure 6" not in md
    assert "*Figure" not in md
    # The clean caption rides the image alt slot so pandoc numbers it once.
    assert "Sheaf layers overview" in md


def test_no_orphan_hand_figure_labels_in_composed_manuscript() -> None:
    """No composed section may carry a hand-written ``*Figure N ...*`` caption line.

    Render-aware guard (not source-blind): pandoc-crossref numbers figures, so a leftover
    italic ``*Figure ...*`` line means a double-number regression slipped back in.
    """
    import re as _re

    from manuscript.sheaf import compose_all_sections

    root = Path(__file__).resolve().parents[1]
    compose_all_sections(root)
    offenders = []
    for md in sorted((root / "manuscript").glob("[0-9][0-9]_*.md")):
        for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if _re.match(r"\*Figure\s+[0-9IMA]", line.strip()):
                offenders.append(f"{md.name}:{i}:{line.strip()[:50]}")
    assert not offenders, f"orphan hand Figure labels: {offenders}"
