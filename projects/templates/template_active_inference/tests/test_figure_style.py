from io import BytesIO
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pytest
from PIL import Image

from visualizations.figure_io import image_render_metrics, save_figure_png
from visualizations.figure_registry import (
    _load_figures_yaml,
    _parse_figures_yaml_cached,
    figure_output_path,
    load_figure_registry,
    render_figure_markdown,
)
from visualizations.figure_style import apply_style, load_figure_style

ALLOWED_VISUAL_ROLES = {"trend", "comparison", "trace", "matrix", "diagram", "table", "flow", "dashboard"}
ALLOWED_EVIDENCE_ROLES = {"statistical", "source_mapped", "formal", "schematic", "scholarship", "sheaf"}
_ABSOLUTE_ESCAPE_FIGURE = str(Path(Path.cwd().anchor) / "tmp" / "escape.png")


def test_load_figure_style_defaults() -> None:
    root = Path(__file__).resolve().parents[1]
    style = load_figure_style(root)
    assert style.dpi == 160
    assert style.color("primary") == "#111827"
    assert style.text_size("title") >= 12.0
    assert style.text_size("axis_label") >= 10.0
    assert style.text_size("matrix_label_dense") >= 6.0
    assert style.layout_value("matrix_grid_width", 0.0) > 0.0


def test_load_figure_style_defaults_when_file_missing(tmp_path: Path) -> None:
    from visualizations.figure_style import DEFAULT_FIGURE_STYLE

    assert load_figure_style(tmp_path) == DEFAULT_FIGURE_STYLE


def test_load_figure_style_fallbacks_to_default_when_yaml_invalid(tmp_path: Path) -> None:
    from visualizations.figure_style import DEFAULT_FIGURE_STYLE

    figures_yaml = tmp_path / "figures.yaml"
    figures_yaml.write_text("{", encoding="utf-8")
    assert load_figure_style(tmp_path) == DEFAULT_FIGURE_STYLE


def test_load_figure_style_fallbacks_to_default_when_typography_is_malformed(tmp_path: Path) -> None:
    from visualizations.figure_style import DEFAULT_FIGURE_STYLE

    tmp_path.joinpath("figures.yaml").write_text(
        "typography:\n  title: not-a-number\n",
        encoding="utf-8",
    )
    assert load_figure_style(tmp_path) == DEFAULT_FIGURE_STYLE


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


def test_image_render_metrics_detects_blank_and_nonblank_png(tmp_path: Path) -> None:
    blank = tmp_path / "blank.png"
    nonblank = tmp_path / "nonblank.png"
    Image.new("RGB", (80, 40), "white").save(blank)
    image = Image.new("RGB", (80, 40), "white")
    image.putpixel((10, 10), (0, 0, 0))
    image.save(nonblank)

    blank_metrics = image_render_metrics(blank)
    nonblank_metrics = image_render_metrics(nonblank)

    assert blank_metrics["exists"] is True
    assert blank_metrics["nonblank"] is False
    assert nonblank_metrics["nonblank"] is True
    assert nonblank_metrics["aspect_ratio"] == 2.0

    changed = Image.new("RGB", (81, 40), "white")
    changed.putpixel((10, 10), (0, 0, 0))
    changed.save(blank)
    assert image_render_metrics(blank)["nonblank"] is True


def test_image_render_metrics_cache_tracks_content_not_restored_metadata(tmp_path: Path) -> None:
    path = tmp_path / "same-metadata.png"
    blank = Image.new("RGB", (40, 20), "white")
    nonblank = Image.new("RGB", (40, 20), "white")
    nonblank.putpixel((10, 10), (0, 0, 0))

    def png_bytes(image: Image.Image) -> bytes:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    blank_payload = png_bytes(blank)
    nonblank_payload = png_bytes(nonblank)
    size = max(len(blank_payload), len(nonblank_payload))
    blank_payload = blank_payload.ljust(size, b"\0")
    nonblank_payload = nonblank_payload.ljust(size, b"\0")
    path.write_bytes(blank_payload)
    before = path.stat()
    assert image_render_metrics(path)["nonblank"] is False

    path.write_bytes(nonblank_payload)
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    after = path.stat()
    assert after.st_size == before.st_size
    assert after.st_mtime_ns == before.st_mtime_ns
    assert image_render_metrics(path)["nonblank"] is True


def test_figure_yaml_cache_tracks_content_not_restored_metadata(tmp_path: Path) -> None:
    path = tmp_path / "figures.yaml"
    original = ("figures:\n  example:\n    filename: example.png\n    alt: One\n    caption: Cache control.\n").encode()
    changed = original.replace(b"alt: One", b"alt: Two")
    assert len(changed) == len(original)
    path.write_bytes(original)
    before = path.stat()
    assert load_figure_registry(tmp_path)["example"].alt == "One"

    path.write_bytes(changed)
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    after = path.stat()
    assert after.st_size == before.st_size
    assert after.st_mtime_ns == before.st_mtime_ns
    assert load_figure_registry(tmp_path)["example"].alt == "Two"


def test_figure_yaml_cache_reuses_exact_bytes_without_sharing_mutable_payload(tmp_path: Path) -> None:
    path = tmp_path / "figures.yaml"
    path.write_text(
        "figures:\n  example:\n    filename: example.png\n    alt: Original\n    caption: Cache isolation.\n",
        encoding="utf-8",
    )
    _parse_figures_yaml_cached.cache_clear()
    first = _load_figures_yaml(tmp_path)
    first_info = _parse_figures_yaml_cached.cache_info()
    first["figures"]["example"]["alt"] = "Mutated"

    second = _load_figures_yaml(tmp_path)
    second_info = _parse_figures_yaml_cached.cache_info()

    assert second["figures"]["example"]["alt"] == "Original"
    assert second_info.misses == first_info.misses
    assert second_info.hits == first_info.hits + 1


def test_figure_yaml_cache_does_not_bypass_symlink_rejection(tmp_path: Path) -> None:
    path = tmp_path / "figures.yaml"
    payload = (
        "figures:\n  example:\n    filename: example.png\n    alt: Example\n    caption: Symlink control.\n"
    ).encode()
    path.write_bytes(payload)
    assert load_figure_registry(tmp_path)["example"].alt == "Example"
    outside = tmp_path / "outside-figures.yaml"
    outside.write_bytes(payload)
    path.unlink()
    path.symlink_to(outside)

    with pytest.raises(ValueError, match="must not be a symlink"):
        load_figure_registry(tmp_path)

    assert outside.read_bytes() == payload


@pytest.mark.parametrize(
    "filename",
    ["../escape.png", "nested/escape.png", _ABSOLUTE_ESCAPE_FIGURE, "escape.txt", r"nested\\escape.png"],
)
def test_figure_registry_rejects_unconfined_or_non_image_filename(tmp_path: Path, filename: str) -> None:
    if filename == _ABSOLUTE_ESCAPE_FIGURE:
        assert Path(filename).is_absolute()
    tmp_path.joinpath("figures.yaml").write_text(
        f"figures:\n  unsafe:\n    filename: {filename!r}\n    alt: Unsafe figure.\n    caption: Unsafe figure.\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="filename"):
        load_figure_registry(tmp_path)


def test_figure_output_path_rejects_symlinked_output_component(tmp_path: Path) -> None:
    tmp_path.joinpath("figures.yaml").write_text(
        "figures:\n  example:\n    filename: example.png\n    alt: Example figure.\n    caption: Example figure.\n",
        encoding="utf-8",
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "output").mkdir()
    (tmp_path / "output" / "figures").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="must not contain symlinks"):
        figure_output_path(tmp_path, "example")

    assert not (outside / "example.png").exists()


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


def test_figure_registry_declares_intent_metadata() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = load_figure_registry(root)
    assert len(registry) == 23
    for figure_id, spec in registry.items():
        assert spec.visual_role in ALLOWED_VISUAL_ROLES, figure_id
        assert spec.evidence_role in ALLOWED_EVIDENCE_ROLES, figure_id
        assert len(spec.paper_claim.split()) >= 6, figure_id


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
