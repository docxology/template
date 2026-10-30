"""Real-file contracts for generic paper-frontmatter admission and whole-pass placement."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml
from PIL import Image

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._paper_frontmatter import (
    MARKER,
    combine_layout,
    compose_frontmatter,
    declared_frontmatter,
    resolve_paper_layout,
)
from infrastructure.rendering._paper_frontmatter_render import _Structure, place_frontmatter_latex
from infrastructure.rendering._pdf_markdown_combine import combine_manuscript_markdown_sections
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files


def _fixture(tmp_path: Path) -> tuple[Path, list[Path], dict]:
    m = tmp_path / "manuscript"
    m.mkdir()
    Image.new("RGB", (20, 10), "white").save(m / "image.png")
    sources = [m / name for name in ("00_abstract.md", "00a_plate.md", "00b_plate.md", "01_body.md")]
    for index, source in enumerate(sources):
        content = f"# Heading {index}\n\nBody.\n"
        if index in (1, 2):
            content = f"# Plate {index}\n\n![Complete caption {index}.](image.png){{#fig:plate-{index} width=100%}}\n"
        source.write_text(content)
    settings = {"paper": {"frontmatter": ["00b_plate.md", "00a_plate.md"]}, "rendering": {"section_breaks": False}}
    (m / "config.yaml").write_text(yaml.safe_dump(settings))
    return m, sources, settings


def test_declared_order_partitions_complete_inputs_once(tmp_path: Path) -> None:
    # Given real sources whose declared order differs from lexical order.
    m, files, _ = _fixture(tmp_path)
    # When discovered through the actual public function.
    result = discover_manuscript_files(m)
    # Then frontmatter is ordered once and abstract/body retain their order.
    assert result == [files[2], files[1], files[0], files[3]]
    layout = resolve_paper_layout(m, tuple(result))
    assert layout.body == (files[0], files[3])
    assert layout.complete == tuple(result)


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "plate.md",
        {},
        [None],
        [""],
        [" "],
        [1],
        ["/absolute.md"],
        ["../outside.md"],
        ["./00a_plate.md"],
        ["00a_plate.MD"],
        ["a\\b.md"],
        ["README.md"],
        ["preamble.md"],
        ["00a_plate.md", "00a_plate.md"],
    ],
)
def test_malformed_or_unsafe_declaration_refuses(raw) -> None:
    # Given an invalid untrusted declaration; when parsed; then refuse it.
    with pytest.raises(RenderingError):
        declared_frontmatter({"paper": {"frontmatter": raw}})


@pytest.mark.parametrize(
    "extra", [{"book": {"title": "Book"}}, {"publication": {"transmission_bookends": {"enabled": True}}}]
)
def test_incompatible_book_configuration_refuses(extra) -> None:
    # Given a paper with incompatible book semantics; when parsed; then refuse.
    with pytest.raises(RenderingError, match="incompatible"):
        declared_frontmatter({"paper": {"frontmatter": ["plate.md"]}, **extra})


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "omitted",
        "duplicate",
        "hardlink",
        "symlink",
        "escape",
        "marker",
        "stray",
        "caption",
        "heading",
        "image",
        "label",
    ],
)
def test_real_file_refusals_preserve_restoration(tmp_path: Path, mutation: str) -> None:
    # Given real files and a retained source snapshot.
    m, files, settings = _fixture(tmp_path)
    original = {p: p.read_bytes() for p in files}
    chosen = files.copy()
    if mutation == "missing":
        files[1].unlink()
    elif mutation == "omitted":
        chosen.remove(files[1])
    elif mutation == "duplicate":
        chosen.append(files[1])
    elif mutation == "hardlink":
        os.link(files[1], m / "alias.md")
        chosen.append(m / "alias.md")
    elif mutation in {"symlink", "escape"}:
        target = files[1] if mutation == "symlink" else tmp_path / "outside.md"
        if mutation == "escape":
            target.write_bytes(original[files[1]])
        files[1].unlink()
        files[1].symlink_to(files[2] if mutation == "symlink" else target)
    elif mutation == "marker":
        files[0].write_text(MARKER)
    elif mutation == "stray":
        (m / "00_00_transmission_begin.md").write_text("stale")
    elif mutation == "caption":
        files[1].write_text("# Plate\n\n![](image.png){#fig:plate-1}\n")
    elif mutation == "heading":
        files[1].write_text("Unmodeled prose.\n" + files[1].read_text())
    elif mutation == "image":
        files[1].write_text(files[1].read_text().replace("image.png", "absent.png"))
    elif mutation == "label":
        files[1].write_text(files[1].read_text().replace("plate-1", "plate-2"))
    # When resolving the mutated inventory; then the actual boundary refuses.
    with pytest.raises(RenderingError):
        resolve_paper_layout(m, tuple(chosen))
    # Given exact retained bytes restored; when resolved again; then original layout passes.
    for path, data in original.items():
        if path.is_symlink():
            path.unlink()
        path.write_bytes(data)
    (m / "00_00_transmission_begin.md").unlink(missing_ok=True)
    assert resolve_paper_layout(m, tuple(files)).body == (files[0], files[3])


def test_absent_frontmatter_retains_legacy_combination(tmp_path: Path) -> None:
    # Given the same files with the opt-in absent.
    m, files, _ = _fixture(tmp_path)
    (m / "config.yaml").write_text("paper: {title: Legacy}\n")
    # When resolved and combined; then supported legacy source bytes remain exact.
    layout = resolve_paper_layout(m, tuple(files))
    assert layout.complete == tuple(files) and not layout.frontmatter
    assert combine_manuscript_markdown_sections(files, section_breaks=False) == "\n\n".join(
        p.read_text().rstrip() + "\n" for p in files
    )


@pytest.mark.parametrize("web", [False, True])
def test_opt_in_combination_keeps_complete_captions_without_body_duplication(tmp_path: Path, web: bool) -> None:
    # Given an admitted source partition with section breaks disabled.
    m, files, _ = _fixture(tmp_path)
    layout = resolve_paper_layout(m, tuple(files))
    # When composed as one whole document; then each source appears once in order.
    result = combine_layout(layout, web=web)
    assert result.index("Plate 2") < result.index("Plate 1") < result.index("Body.")
    assert result.count("Complete caption 1.") == result.count("Complete caption 2.") == 1
    assert result.count(f"% {MARKER}-body") == 1
    assert "\\newpage" not in result


@pytest.mark.parametrize("count,bodies", [(0, (b"x",)), (2, (b"x",)), (1, (MARKER.encode(),))])
def test_held_composition_refuses_invalid_partition_or_marker(count, bodies) -> None:
    with pytest.raises(RenderingError):
        compose_frontmatter(bodies, count, "")


def _tex(layout) -> str:
    pages = []
    for index, page in enumerate(layout.frontmatter, 1):
        pages.append(
            f"% {MARKER}-begin:{index}\n\\section{{Plate}}\n\\begin{{figure}}\n"
            f"\\includegraphics[width=1\\linewidth]{{image.png}}\n\\caption{{Full caption}}"
            f"\\label{{{page.label}}}\n\\end{{figure}}\n% {MARKER}-end:{index}"
        )
    return "\\begin{document}\n" + "\n".join(pages) + f"\n% {MARKER}-body\n\\end{{document}}"


@pytest.mark.parametrize(
    "mutation", ["none", "missing", "reordered", "duplicate", "figure", "caption", "image", "document", "toc"]
)
def test_latex_boundary_admission(tmp_path: Path, mutation: str) -> None:
    m, files, _ = _fixture(tmp_path)
    layout = resolve_paper_layout(m, tuple(files))
    tex = _tex(layout)
    replacements = {
        "missing": (f"% {MARKER}-end:1", ""),
        "reordered": ("begin:1", "begin:2"),
        "duplicate": (f"% {MARKER}-body", f"% {MARKER}-body\n% {MARKER}-body"),
        "figure": ("\\begin{figure}", "\\begin{table}"),
        "caption": ("\\caption{", "\\other{"),
        "image": ("\\includegraphics", "\\other"),
        "document": ("\\begin{document}", ""),
        "toc": ("\\end{document}", "\\tableofcontents\\end{document}"),
    }
    if mutation != "none":
        old, new = replacements[mutation]
        with pytest.raises(RenderingError):
            place_frontmatter_latex(tex.replace(old, new, 1), layout, "0.5")
    restored = place_frontmatter_latex(tex, layout, "0.5")
    assert restored.count("\\tableofcontents") == 1 and "[H]" in restored
    assert "paper.frontmatter page overflow" in restored and MARKER not in restored


@pytest.mark.parametrize("text", ['<div id="x"></div><p id="x"></p>', "<div></nav>", '<div id="other"></div>'])
def test_html_structure_refuses_duplicate_invalid_or_missing_regions(text: str) -> None:
    with pytest.raises(RenderingError):
        _Structure(text).one("paper-body")


@pytest.mark.parametrize("mutation", ["blank-alt", "missing", "escape", "symlink"])
def test_configured_cover_refuses_before_combined_output(tmp_path: Path, mutation: str) -> None:
    m, files, settings = _fixture(tmp_path)
    image = "image.png"
    if mutation == "missing":
        image = "missing.png"
    elif mutation == "escape":
        Image.new("RGB", (20, 10), "white").save(tmp_path.parent / (tmp_path.name + "-outside.png"))
        image = str(tmp_path.parent / (tmp_path.name + "-outside.png"))
    elif mutation == "symlink":
        (m / "cover.png").symlink_to(m / "image.png")
        image = "cover.png"
    settings["paper"]["cover"] = {"image": image, "alt": "" if mutation == "blank-alt" else "Cover description"}
    (m / "config.yaml").write_text(yaml.safe_dump(settings))
    with pytest.raises(RenderingError, match="cover"):
        resolve_paper_layout(m, tuple(files))


@pytest.mark.parametrize("mutation", ["none", "order", "parent", "page", "unclosed", "missing"])
def test_html_element_placement_uses_structural_regions(tmp_path: Path, mutation: str) -> None:
    from infrastructure.rendering._paper_frontmatter_render import place_frontmatter_html

    m, files, settings = _fixture(tmp_path)
    settings["paper"]["cover"] = {"image": "image.png", "alt": "A real engineering test image"}
    (m / "config.yaml").write_text(yaml.safe_dump(settings))
    layout = resolve_paper_layout(m, tuple(files))
    pages = "".join(
        f'<div id="paper-frontmatter-{i}"><figure id="{page.label}"></figure></div>'
        for i, page in enumerate(layout.frontmatter, 1)
    )
    front = f'<div id="paper-frontmatter">{pages}</div>'
    body = '<div id="paper-body"><h1>Body</h1></div>'
    toc = '<nav id="TOC"><a href="#paper-body">Body</a></nav>'
    text = f'<html><body>{toc}<main id="main-content">{front}{body}</main></body></html>'
    if mutation == "order":
        text = text.replace(front + body, body + front)
    elif mutation == "parent":
        text = text.replace(toc + '<main id="main-content">', '<main id="main-content">' + toc)
    elif mutation == "page":
        text = text.replace("paper-frontmatter-1", "paper-frontmatter-absent")
    elif mutation == "unclosed":
        text = text.removesuffix("</html>")
    elif mutation == "missing":
        text = text.replace(toc, "")
    target = tmp_path / "output/web/index.html"
    target.parent.mkdir(parents=True)
    target.write_text(text)
    if mutation == "none":
        place_frontmatter_html(target, layout)
        structure = _Structure(target.read_text())
        assert structure.one("paper-cover").start < structure.one("paper-frontmatter").start
        assert structure.one("paper-frontmatter").end < structure.one("TOC").start < structure.one("paper-body").start
        assert (target.parent / "assets/paper-cover.png").read_bytes() == (m / "image.png").read_bytes()
    else:
        with pytest.raises(RenderingError):
            place_frontmatter_html(target, layout)


def test_hydrated_frontmatter_uses_existing_confined_figure_alias(tmp_path: Path) -> None:
    import shutil

    m, files, _ = _fixture(tmp_path)
    figures = tmp_path / "output/figures"
    figures.mkdir(parents=True)
    shutil.copyfile(m / "image.png", figures / "plate.png")
    for file in files[1:3]:
        file.write_text(file.read_text().replace("image.png", "../output/figures/plate.png"))
    hydrated = tmp_path / "output/manuscript"
    shutil.copytree(m, hydrated)
    supplied = tuple(hydrated / p.name for p in files)
    layout = resolve_paper_layout(hydrated, supplied)
    assert all(page.image == figures / "plate.png" for page in layout.frontmatter)
    assert layout.body == (supplied[0], supplied[3])


def test_latex_bounds_retain_complete_bracket_and_dimension_like_alt(tmp_path: Path) -> None:
    m, files, _ = _fixture(tmp_path)
    layout = resolve_paper_layout(m, tuple(files))
    alt = r"alt={A [square],height=literal,width=literal {nested} description.}"
    tex = _tex(layout).replace(r"width=1\linewidth", r"width=1\linewidth," + alt)
    rendered = place_frontmatter_latex(tex, layout, "0.5")
    assert rendered.count(alt) == len(layout.frontmatter)
    assert rendered.count(r"height=0.5\textheight") == len(layout.frontmatter)


@pytest.mark.parametrize("raw", [[], ["unexpected"], "invalid root", 3])
def test_nonmapping_manuscript_configuration_refuses(tmp_path: Path, raw) -> None:
    m, files, _ = _fixture(tmp_path)
    (m / "config.yaml").write_text(yaml.safe_dump(raw))
    with pytest.raises(RenderingError, match="configuration must be a mapping"):
        resolve_paper_layout(m, tuple(files))


def test_paper_schema_declares_frontmatter_without_changing_book() -> None:
    from infrastructure.core.config.schema import generate_manuscript_config_schema

    schema = generate_manuscript_config_schema()
    paper = schema["properties"]["paper"]["properties"]
    assert paper["frontmatter"]["type"] == "array"
    assert paper["frontmatter"]["uniqueItems"] is True
    assert paper["frontmatter"]["items"] == {"type": "string", "minLength": 1}
    assert "frontmatter" not in schema["properties"]["book"]["properties"]


def _native_project(tmp_path: Path, *, overflow: bool = False):
    """Author actual engineering inputs; no scientific results or custody fixtures."""
    import json
    from PIL import ImageDraw
    from infrastructure.rendering import RenderManager
    from infrastructure.rendering.config import RenderingConfig

    manuscript = tmp_path / "manuscript"
    figures = tmp_path / "output" / "figures"
    manuscript.mkdir()
    figures.mkdir(parents=True)
    registry = {}
    names = []
    for index, name in enumerate(("Alpha", "Beta", "Gamma")):
        image = Image.new("RGB", (480, 240), "white")
        draw = ImageDraw.Draw(image)
        color = ("#196a87", "#a85729", "#326d46")[index]
        draw.rounded_rectangle((20, 20, 460, 220), radius=15, fill=color)
        draw.text((45, 65), f"Panel {name}", fill="white", font_size=36)
        filename = f"plate-{name.lower()}.png"
        image.save(figures / filename)
        source_name = f"00{chr(97 + index)}_plate.md"
        names.append(source_name)
        caption = f"Engineering panel {name}. Complete caption retained at ordinary text size. Terminal caption {name}."
        if overflow and index == 0:
            caption += " Overflow content must fail rather than shrink or clip." * 220
        (manuscript / source_name).write_text(
            f"# Panel {name}\n\n![{caption}](../output/figures/{filename}){{#fig:plate-{name.lower()}}}\n",
            encoding="utf-8",
        )
        registry[f"fig:plate-{name.lower()}"] = {
            "filename": filename,
            "alt": f"Concise alternative for {name}.",
            "long_description": f"Complete first paragraph for {name}.\n\nComplete second paragraph for {name}.",
        }
    (figures / "figure_registry.json").write_text(json.dumps(registry), encoding="utf-8")
    (manuscript / "01_body.md").write_text("# Engineering body\n\nThis is only a renderer fixture.\n", encoding="utf-8")
    settings = {
        "paper": {
            "title": "Engineering frontmatter",
            "frontmatter": names,
            "cover": {"image": "output/figures/plate-alpha.png", "alt": "Engineering cover alternative."},
        },
        "authors": [{"name": "Engineering fixture"}],
        "rendering": {"include_date": False, "section_breaks": False, "front_matter_figure_height_fraction": 0.4},
    }
    (manuscript / "config.yaml").write_text(yaml.safe_dump(settings), encoding="utf-8")
    manager = RenderManager(
        RenderingConfig(
            manuscript_dir=str(manuscript),
            figures_dir=str(figures),
            output_dir=str(tmp_path / "output"),
            pdf_dir=str(tmp_path / "output/pdf"),
            web_dir=str(tmp_path / "output/web"),
        )
    )
    return manuscript, manager


@pytest.mark.requires_latex
@pytest.mark.timeout(120)
def test_real_pdf_and_html_keep_three_complete_pages_before_contents(tmp_path: Path) -> None:
    from html.parser import HTMLParser
    from pypdf import PdfReader

    manuscript, manager = _native_project(tmp_path)
    sources = discover_manuscript_files(manuscript)
    pdf = manager.render_combined_pdf(sources, manuscript, "frontmatter_fixture")
    web = manager.render_combined_web(sources, manuscript, "frontmatter_fixture")
    pages = PdfReader(pdf).pages
    assert len(pages) == 6
    texts = [" ".join(page.extract_text().split()) for page in pages]
    assert "Engineering frontmatter" in texts[0]
    for index, name in enumerate(("Alpha", "Beta", "Gamma"), 1):
        assert f"Panel {name}" in texts[index]
        assert f"Terminal caption {name}." in texts[index]
        assert len(pages[index].images) == 1
        source = Image.open(tmp_path / "output/figures" / f"plate-{name.lower()}.png").convert("RGB")
        assert pages[index].images[0].image.convert("RGB").tobytes() == source.tobytes()
    assert "Contents" in texts[4]
    assert "Engineering body" in texts[5]

    class Reader(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.ids: list[str] = []
            self.alts: list[str] = []
            self.text_parts: list[str] = []

        def handle_data(self, data: str) -> None:
            self.text_parts.append(data)

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            attributes = dict(attrs)
            if attributes.get("id"):
                self.ids.append(str(attributes["id"]))
            if tag == "img":
                self.alts.append(str(attributes.get("alt")))

    text = web.read_text(encoding="utf-8")
    parsed = Reader()
    parsed.feed(text)
    plain = " ".join(" ".join(parsed.text_parts).split())
    ordered = ["paper-cover", "paper-frontmatter-1", "paper-frontmatter-2", "paper-frontmatter-3", "TOC", "paper-body"]
    assert all(parsed.ids.count(identifier) == 1 for identifier in ordered)
    assert [parsed.ids.index(identifier) for identifier in ordered] == sorted(parsed.ids.index(i) for i in ordered)
    assert "Engineering cover alternative." in parsed.alts
    for name in ("Alpha", "Beta", "Gamma"):
        assert f"Concise alternative for {name}." in parsed.alts
        assert f"Complete first paragraph for {name}." in text
        assert f"Complete second paragraph for {name}." in text
        caption = f"Engineering panel {name}. Complete caption retained at ordinary text size. Terminal caption {name}."
        assert caption in plain


@pytest.mark.requires_latex
@pytest.mark.timeout(120)
def test_real_tex_overflow_is_a_failed_render(tmp_path: Path) -> None:
    manuscript, manager = _native_project(tmp_path, overflow=True)
    with pytest.raises(RenderingError):
        manager.render_combined_pdf(discover_manuscript_files(manuscript), manuscript, "overflow_fixture")
    log = tmp_path / "output/pdf/_combined_manuscript.log"
    assert "paper.frontmatter page overflow" in log.read_text(encoding="utf-8")
