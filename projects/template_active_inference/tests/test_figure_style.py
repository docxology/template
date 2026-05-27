from pathlib import Path

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


def test_figure_registry_and_markdown() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = load_figure_registry(root)
    assert "ising_mi_curve" in registry
    assert len(registry["ising_mi_curve"].alt) >= 80
    md = render_figure_markdown(root, "ising_mi_curve", figure_number=1)
    assert "Figure 1." in md
    assert "../output/figures/ising_mi_curve.png" in md


def test_render_section_figures_for_results_mi_sweep() -> None:
    root = Path(__file__).resolve().parents[1]
    from visualizations.figure_registry import render_section_figures

    md = render_section_figures(root, "results_mi_sweep")
    assert "ising_mi_curve.png" in md
    assert "Figure 2 (results)." in md
    assert len(md.split("\n\n")) >= 2


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
