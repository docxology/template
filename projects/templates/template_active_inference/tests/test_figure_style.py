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
    assert "Figure 1." in md
    assert "../output/figures/ising_mi_curve.png" in md
    assert "{#fig:ising_mi_curve" in md


def test_render_section_figures_for_results_mi_sweep() -> None:
    root = Path(__file__).resolve().parents[1]
    from visualizations.figure_registry import render_section_figures

    md = render_section_figures(root, "results_mi_sweep")
    assert "ising_mi_curve.png" in md
    assert "Figure 2 (results)." in md
    assert len(md.split("\n\n")) >= 2


def test_render_figure_markdown_unlabeled_repeat() -> None:
    root = Path(__file__).resolve().parents[1]
    md = render_figure_markdown(root, "ising_mi_curve", labeled=False)
    assert "{#fig:ising_mi_curve" not in md
    assert "{width=" in md


def test_render_figure_markdown_no_duplicate_number_with_prefix() -> None:
    root = Path(__file__).resolve().parents[1]
    md = render_figure_markdown(
        root,
        "sheaf_layers_overview",
        figure_number=6,
        caption_prefix="Figure 6 (methods). ",
    )
    assert "Figure 6 (methods)." in md
    assert "Figure 6. Figure 6" not in md
