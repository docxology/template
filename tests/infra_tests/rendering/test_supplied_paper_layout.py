"""Supplied layouts cannot replace current real-file admission at writer boundaries."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Literal

import pytest
import yaml
from PIL import Image

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.diagnostic import DiagnosticReporter
from infrastructure.rendering import RenderManager
from infrastructure.rendering._combined_exports import prepare_shared_combined_markdown, render_combined_outputs
from infrastructure.rendering._paper_frontmatter import PaperLayout, combine_layout, resolve_paper_layout
from infrastructure.rendering._pdf_markdown_combine import combine_manuscript_markdown_sections
from infrastructure.rendering.config import RenderingConfig

type Consumer = Literal["web", "pdf", "shared", "markdown", "outputs"]


def _project(tmp_path: Path) -> tuple[Path, list[Path], RenderManager]:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    Image.new("RGB", (20, 10), "white").save(manuscript / "image.png")
    files = [manuscript / name for name in ("abstract.md", "plate.md", "body.md")]
    for source, body in zip(
        files,
        ("# Abstract\n\nText.\n", "# Plate\n\n![Caption.](image.png){#fig:plate}\n", "# Body\n\nText.\n"),
        strict=True,
    ):
        source.write_text(body, encoding="utf-8")
    (manuscript / "config.yaml").write_text(
        "paper:\n  title: Admission fixture\n  frontmatter: [plate.md]\n", encoding="utf-8"
    )
    output = tmp_path / "output"
    manager = RenderManager(
        RenderingConfig(
            manuscript_dir=str(manuscript),
            figures_dir=str(manuscript),
            output_dir=str(output),
            web_dir=str(output / "web"),
            pdf_dir=str(output / "pdf"),
        )
    )
    return manuscript, files, manager


def _consume(
    consumer: Consumer, manager: RenderManager, files: list[Path], manuscript: Path, layout: PaperLayout
) -> None:
    if consumer == "web":
        manager.render_combined_web(files, manuscript, "admission", paper_layout=layout)
    elif consumer == "pdf":
        manager.render_combined_pdf(files, manuscript, "admission", paper_layout=layout)
    elif consumer == "shared":
        prepare_shared_combined_markdown(manager, files, manuscript, "admission", paper_layout=layout)
    elif consumer == "markdown":
        combine_manuscript_markdown_sections(files, paper_layout=layout)
    else:
        manager.config.enable_pdf = manager.config.enable_html = manager.config.enable_slides = False
        render_combined_outputs(
            manager, files, manuscript, "admission", DiagnosticReporter("admission"), 0, paper_layout=layout
        )


@pytest.mark.timeout(90)
@pytest.mark.parametrize("consumer", ["web", "pdf", "shared", "markdown", "outputs"])
@pytest.mark.parametrize(
    "change",
    ["duplicate", "body-order", "omitted", "invalid-config", "disabled-config", "changed-heading", "foreign-layout"],
)
def test_supplied_layout_refuses_current_input_or_declaration_mismatch(
    tmp_path: Path, consumer: Consumer, change: str
) -> None:
    manuscript, files, manager = _project(tmp_path)
    layout = resolve_paper_layout(manuscript, tuple(files))
    if change == "duplicate":
        files.append(files[-1])
    elif change == "body-order":
        files[0], files[2] = files[2], files[0]
    elif change == "omitted":
        files.pop()
    elif change in {"invalid-config", "disabled-config"}:
        value = "invalid" if change == "invalid-config" else []
        (manuscript / "config.yaml").write_text(yaml.safe_dump({"paper": {"frontmatter": value}}), encoding="utf-8")
    elif change == "changed-heading":
        files[1].write_text(
            files[1].read_text(encoding="utf-8").replace("# Plate", "# Updated plate"), encoding="utf-8"
        )
    else:
        layout = replace(layout, manuscript_dir=tmp_path)
    before = {str(path.relative_to(tmp_path)): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    with pytest.raises(RenderingError):
        _consume(consumer, manager, files, manuscript, layout)
    after = {str(path.relative_to(tmp_path)): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assert after == before, "Admission must fail before creating or replacing writer outputs"


@pytest.mark.parametrize("change", ["duplicate", "invalid-config", "changed-heading"])
def test_direct_layout_reader_readmits_current_files(tmp_path: Path, change: str) -> None:
    manuscript, files, _ = _project(tmp_path)
    layout = resolve_paper_layout(manuscript, tuple(files))
    if change == "duplicate":
        layout = replace(layout, body=layout.body + (layout.body[-1],))
    elif change == "invalid-config":
        (manuscript / "config.yaml").write_text("paper: {frontmatter: invalid}\n", encoding="utf-8")
    else:
        files[1].write_text(files[1].read_text(encoding="utf-8").replace("# Plate", "# Changed"), encoding="utf-8")
    with pytest.raises(RenderingError):
        combine_layout(layout)


def test_valid_supplied_layout_keeps_declared_partition_and_exact_restoration(tmp_path: Path) -> None:
    manuscript, files, manager = _project(tmp_path)
    layout = resolve_paper_layout(manuscript, tuple(files))
    original = (manuscript / "config.yaml").read_bytes()
    direct = combine_layout(layout)
    assert direct.index("# Plate") < direct.index("# Abstract") < direct.index("# Body")
    _consume("shared", manager, files, manuscript, layout)
    _consume("web", manager, files, manuscript, layout)
    assert (tmp_path / "output/web/index.html").is_file()
    (manuscript / "config.yaml").write_text("paper: {frontmatter: invalid}\n", encoding="utf-8")
    with pytest.raises(RenderingError):
        combine_layout(layout)
    (manuscript / "config.yaml").write_bytes(original)
    assert resolve_paper_layout(manuscript, tuple(files)) == layout
    assert combine_layout(layout) == direct


def test_tex_image_without_options_still_gets_measured_bounds(tmp_path: Path) -> None:
    from infrastructure.rendering._paper_frontmatter_render import place_frontmatter_latex

    manuscript, files, _ = _project(tmp_path)
    layout = resolve_paper_layout(manuscript, tuple(files))
    source = (
        "\\begin{document}\n% template-paper-frontmatter-begin:1\n"
        "\\begin{figure}\n\\includegraphics{image.png}\n\\caption{Caption.}\\label{fig:plate}\n"
        "\\end{figure}\n% template-paper-frontmatter-end:1\n% template-paper-frontmatter-body\n"
        "Body.\n\\end{document}\n"
    )
    result = place_frontmatter_latex(source, layout, "0.5")
    assert r"\includegraphics[width=\linewidth,height=0.5\textheight,keepaspectratio]{image.png}" in result
    assert result.count(r"\tableofcontents") == 1
    assert "\\caption{Caption.}\\label{fig:plate}" in result


def test_self_closing_html_does_not_change_the_following_structural_parent() -> None:
    from infrastructure.rendering._paper_frontmatter_render import _Structure

    parsed = _Structure('<main id="main-content"><span/><br/><div id="paper-body">Body</div></main>')
    assert parsed.one("paper-body").parent == parsed.one("main-content").start


@pytest.mark.parametrize("change", ["figure-outside-page", "missing-cover"])
def test_html_transform_refuses_displaced_figure_or_removed_cover(tmp_path: Path, change: str) -> None:
    from infrastructure.rendering._paper_frontmatter_render import place_frontmatter_html

    manuscript, files, _ = _project(tmp_path)
    config = manuscript / "config.yaml"
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings["paper"]["cover"] = {"image": "image.png", "alt": "Engineering cover"}
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    layout = resolve_paper_layout(manuscript, tuple(files))
    figure = '<figure id="fig:plate"></figure>'
    content = f'<div id="paper-frontmatter-1">{figure}</div>'
    if change == "figure-outside-page":
        content = '<div id="paper-frontmatter-1"></div>' + figure
    else:
        (manuscript / "image.png").unlink()
    source = (
        '<html><body><nav id="TOC">Contents</nav><main id="main-content">'
        f'<div id="paper-frontmatter">{content}</div><div id="paper-body">Body</div>'
        "</main></body></html>"
    )
    target = tmp_path / "index.html"
    target.write_text(source, encoding="utf-8")
    with pytest.raises(RenderingError, match="figures|cover"):
        place_frontmatter_html(target, layout)
    assert target.read_text(encoding="utf-8") == source
