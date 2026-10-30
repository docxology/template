"""Writer-specific placement of one admitted paper layout; no project semantics."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.files.secure_write import atomic_write_bytes_confined, atomic_write_text_confined
from infrastructure.rendering._paper_frontmatter import MARKER, PaperLayout
from infrastructure.rendering._pdf_title_page_config import _load_render_config
from infrastructure.rendering._pdf_title_page_images import _cover_image_alt, _cover_image_path
from infrastructure.rendering._pdf_figure_alts import _balanced_square_end


def place_frontmatter_latex(tex: str, layout: PaperLayout, height: str) -> str:
    """Keep complete headings, figures and captions in measured single-page boxes."""
    expected = [
        item for index in range(1, len(layout.frontmatter) + 1) for item in (f"begin:{index}", f"end:{index}")
    ] + ["body"]
    actual = re.findall(rf"(?m)^% {MARKER}-(.*)$", tex)
    if actual != expected or r"\tableofcontents" in tex:
        raise RenderingError("paper.frontmatter LaTeX boundaries are missing, duplicated or reordered")
    for index, page in enumerate(layout.frontmatter, 1):
        pattern = re.compile(rf"(?m)^% {MARKER}-begin:{index}\n(.*?)^% {MARKER}-end:{index}$", re.DOTALL)
        match = pattern.search(tex)
        if match is None:
            raise RenderingError("paper.frontmatter LaTeX region is missing")
        region = match[1]
        if (
            len(re.findall(r"\\begin\{figure\}(?:\[[^]]*\])?", region)) != 1
            or region.count(r"\caption{") != 1
            or region.count(r"\label{" + page.label + "}") != 1
            or tex.count(r"\label{" + page.label + "}") != 1
        ):
            raise RenderingError("paper.frontmatter requires one complete labeled captioned figure per page")
        region = re.sub(r"\\begin\{figure\}(?:\[[^]]*\])?", r"\\begin{figure}[H]", region)

        images = list(re.finditer(r"\\includegraphics", region))
        if len(images) != 1:
            raise RenderingError("paper.frontmatter region requires exactly one image")
        start = end = images[0].end()
        options = ""
        if region[start : start + 1] == "[":
            end = _balanced_square_end(region, start)
            options = region[start + 1 : end - 1]
        # Split only top-level option commas, preserving the complete alt bytes,
        # including bracket literals and dimension-like prose inside its braces.
        parts: list[str] = []
        depth = cursor = 0
        for position, character in enumerate(options):
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
            elif character == "," and depth == 0:
                parts.append(options[cursor:position])
                cursor = position + 1
        parts.append(options[cursor:])
        retained = [
            part
            for part in parts
            if part.strip() and part.strip().partition("=")[0] not in {"width", "height", "keepaspectratio"}
        ]
        bounded = rf"[width=\linewidth,height={height}\textheight,keepaspectratio"
        bounded += ("," + ",".join(retained) if retained else "") + "]"
        region = region[:start] + bounded + region[end:]
        boxed = (
            "\\clearpage\n\\begin{lrbox}{\\templatepaperfrontmatterbox}\n"
            "\\begin{minipage}{\\textwidth}\n" + region + "\n\\end{minipage}\n\\end{lrbox}\n"
            "\\ifdim\\dimexpr\\ht\\templatepaperfrontmatterbox+\\dp\\templatepaperfrontmatterbox\\relax>\\textheight\n"
            "\\PackageError{paperfrontmatter}{paper.frontmatter page overflow}"
            "{Shorten the authored region; text is never shrunk}\n"
            "\\fi\n\\noindent\\usebox{\\templatepaperfrontmatterbox}\n\\clearpage\n"
        )
        tex = tex[: match.start()] + boxed + tex[match.end() :]
    tex = tex.replace(f"% {MARKER}-body", "\\tableofcontents\n\\clearpage", 1)
    declaration = "\\usepackage{float}\n\\newsavebox{\\templatepaperfrontmatterbox}\n"
    if tex.count(r"\begin{document}") != 1:
        raise RenderingError("paper.frontmatter requires one LaTeX document")
    return tex.replace(r"\begin{document}", declaration + r"\begin{document}", 1)


@dataclass(frozen=True, slots=True)
class _Element:
    tag: str
    identifier: str
    start: int
    end: int
    parent: int


class _Structure(HTMLParser):
    """Locate actual element spans without serializing or rewriting their descendants."""

    def __init__(self, text: str) -> None:
        super().__init__(convert_charrefs=False)
        self.text = text
        self.offsets = [0] + [m.end() for m in re.finditer("\n", text)]
        self.stack: list[tuple[str, str, int, int]] = []
        self.elements: list[_Element] = []
        self.identifiers: set[str] = set()
        self.feed(text)
        self.close()
        if self.stack:
            raise RenderingError("paper.frontmatter HTML contains unclosed elements")

    def position(self) -> int:
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        identifier = dict(attrs).get("id") or ""
        if identifier:
            if identifier in self.identifiers:
                raise RenderingError(f"paper.frontmatter HTML contains duplicate id: {identifier}")
            self.identifiers.add(identifier)
        start = self.position()
        parent = self.stack[-1][2] if self.stack else -1
        if tag not in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }:
            self.stack.append((tag, identifier, start, parent))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        if not self.stack or self.stack[-1][0] != tag:
            raise RenderingError(f"paper.frontmatter HTML has an invalid closing element: {tag}")
        opened, identifier, start, parent = self.stack.pop()
        end = self.text.index(">", self.position()) + 1
        self.elements.append(_Element(opened, identifier, start, end, parent))

    def one(self, identifier: str) -> _Element:
        matches = [element for element in self.elements if element.identifier == identifier]
        if len(matches) != 1:
            raise RenderingError(f"paper.frontmatter HTML requires one structural {identifier} element")
        return matches[0]


def place_frontmatter_html(path: Path, layout: PaperLayout) -> None:
    """Place the real TOC and configured cover around existing whole-pass containers."""
    text = path.read_text(encoding="utf-8")
    parsed = _Structure(text)
    front, body, toc = (parsed.one(name) for name in ("paper-frontmatter", "paper-body", "TOC"))
    if (
        front.tag != "div"
        or body.tag != "div"
        or toc.tag != "nav"
        or not (toc.end <= front.start < front.end <= body.start)
    ):
        raise RenderingError("paper.frontmatter HTML container order is invalid")
    main = parsed.one("main-content")
    if front.parent != body.parent or front.parent != main.start or toc.parent != main.parent:
        raise RenderingError("paper.frontmatter HTML containers do not match the accessibility landmark structure")
    previous = front.start
    for index, page in enumerate(layout.frontmatter, 1):
        element = parsed.one(f"paper-frontmatter-{index}")
        figure = parsed.one(page.label)
        if (
            not (previous <= element.start < figure.start < figure.end < element.end < front.end)
            or element.parent != front.start
        ):
            raise RenderingError("paper.frontmatter HTML pages or labeled figures are missing or reordered")
        previous = element.end
    config, config_file = _load_render_config(layout.manuscript_dir)
    cover = ""
    if config is not None and config_file is not None:
        image, alt = _cover_image_path(config, config_file), _cover_image_alt(config)
        if image is not None:
            if not image.is_file() or image.is_symlink() or not alt:
                raise RenderingError("paper.frontmatter configured cover requires a real image and non-empty alt")
            asset = path.parent / "assets" / ("paper-cover" + image.suffix.lower())
            asset.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_bytes_confined(path.parent, asset, image.read_bytes())
            cover = (
                f'<div id="paper-cover" class="paper-cover"><img src="assets/{asset.name}" '
                f'alt="{html.escape(alt, quote=True)}" style="max-width:100%;height:auto" /></div>\n'
            )
    # Splice actual element spans. Descendant figures, registry associations and font assets remain exact.
    moved_toc = text[toc.start : toc.end]
    updated = (
        text[: toc.start]
        + text[toc.end : front.start]
        + cover
        + text[front.start : front.end]
        + "\n"
        + moved_toc
        + text[front.end :]
    )
    final = _Structure(updated)
    if not final.one("paper-frontmatter").end < final.one("TOC").start < final.one("paper-body").start:
        raise RenderingError("paper.frontmatter HTML final structural order is invalid")
    atomic_write_text_confined(path.parent, path, updated)
