"""Real-writer regressions for formal content in accessible slide pairs."""

from __future__ import annotations

import html
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import (
    AccessibleSlidePolicy,
    compose_accessible_pandoc_document,
    load_and_compose_pandoc_json,
)
from infrastructure.rendering._slides_crossref import resolve_cross_deck_references
from infrastructure.rendering._slides_reveal_content import resolve_reveal_cross_references
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer


_SECTION_RE = re.compile(r"<section\b(?P<attrs>[^>]*)>(?P<body>.*?)</section>", re.IGNORECASE | re.DOTALL)
_OPENING_HEADING_RE = re.compile(r"\s*<h[1-6]\b[^>]*>.*?</h[1-6]>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


def _header(title: str, *, level: int = 2) -> dict[str, Any]:
    return {
        "t": "Header",
        "c": [level, ["", [], []], [{"t": "Str", "c": title}]],
    }


def _document(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": blocks,
    }


def _declaration() -> dict[str, Any]:
    return {
        "t": "RawBlock",
        "c": [
            "latex",
            "\\ifcsname proposition\\endcsname\n\\else\n\\newtheorem{proposition}{Proposition}\n\\fi",
        ],
    }


def _anchor(identifier: str) -> dict[str, Any]:
    return {
        "t": "Para",
        "c": [{"t": "Span", "c": [[identifier, [], []], []]}],
    }


def _paragraph(text: str) -> dict[str, Any]:
    words = text.split()
    inlines: list[dict[str, Any]] = []
    for index, word in enumerate(words):
        if index:
            inlines.append({"t": "Space"})
        inlines.append({"t": "Str", "c": word})
    return {"t": "Para", "c": inlines}


def _walk(value: object) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [node for item in value for node in _walk(item)]
    if not isinstance(value, dict):
        return []
    return [value, *_walk(value.get("c"))]


def _empty_nonddivider_sections(content: str) -> list[str]:
    empty: list[str] = []
    for match in _SECTION_RE.finditer(content):
        attributes = match.group("attrs")
        if "section-divider" in attributes:
            continue
        heading = _OPENING_HEADING_RE.match(match.group("body"))
        if heading is None:
            continue
        remainder = match.group("body")[heading.end() :]
        visible = " ".join(html.unescape(_TAG_RE.sub(" ", remainder)).split())
        if not visible:
            empty.append(attributes)
    return empty


def test_identifier_and_declaration_blocks_are_retained_without_owning_frames() -> None:
    composition = compose_accessible_pandoc_document(
        _document(
            [
                _header("Methods", level=1),
                _anchor("sec:methodology"),
                _declaration(),
                _paragraph("Visible method content."),
            ]
        ),
        policy=AccessibleSlidePolicy(),
        source="manuscript/methods.md",
    )

    headers = [node for node in composition.document["blocks"] if node.get("t") == "Header"]
    assert composition.frame_count == 2
    assert len(headers) == 2
    assert "section-divider" in headers[0]["c"][1][1]
    assert "prose-slide" in headers[1]["c"][1][1]
    nodes = _walk(composition.document["blocks"])
    assert sum(node.get("t") == "Span" and node["c"][0][0] == "sec:methodology" for node in nodes) == 1
    assert sum(node == _declaration() for node in nodes) == 1


@pytest.mark.parametrize(
    "environment",
    ["theorem", "definition", "lemma", "proposition", "corollary", "hypothesis", "proof", "remark"],
)
def test_every_allowlisted_formal_environment_gets_an_html_writer_fallback(environment: str) -> None:
    source = (
        f"\\begin{{{environment}}}[Named statement]\\label{{thm:{environment}}} "
        r"Visible formal content with \texttt{solver} and \(q>0\). "
        f"\\end{{{environment}}}"
    )
    raw = {"t": "RawBlock", "c": ["tex", source]}

    composition = compose_accessible_pandoc_document(
        _document([_header("Formal result"), raw]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/formalism.md",
    )

    raw_blocks = [node for node in composition.document["blocks"] if node.get("t") == "RawBlock"]
    assert raw_blocks[0] == raw
    assert raw_blocks[1]["c"][0] == "html"
    fallback = raw_blocks[1]["c"][1]
    assert f'class="formal-statement formal-{environment}"' in fallback
    assert f'id="thm:{environment}"' in fallback
    assert "Visible formal content" in fallback
    assert "<code>solver</code>" in fallback
    assert '<span class="math inline">\\(q&gt;0\\)</span>' in fallback


@pytest.mark.parametrize("auxiliary", [_anchor("sec:orphan"), _declaration()])
def test_nonvisible_auxiliary_only_heading_fails_closed(auxiliary: dict[str, Any]) -> None:
    with pytest.raises(RenderingError, match=r"\[slides\.structure\.title-only\]"):
        compose_accessible_pandoc_document(
            _document([_header("Orphan heading"), auxiliary]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/orphan.md",
        )


def test_nested_environment_in_formal_title_fails_before_writer_dispatch() -> None:
    raw = {
        "t": "RawBlock",
        "c": [
            "latex",
            r"\begin{theorem}[\begin{x}\end{x}] Visible body. \end{theorem}",
        ],
    }

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-raw-geometry\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Formal result"), raw]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/formalism.md",
        )

    assert exc_info.value.context["unsupported_command"] == "nested-environment"


@pytest.mark.parametrize(
    ("fragment", "diagnostic"),
    (
        (r"A \sum B.", "sum"),
        (r"A \log B.", "log"),
        (r"A \to B.", "to"),
        (r"A \mathrm{B}.", "mathrm"),
        (r"\textbf{A \emph{B}}.", "textbf"),
        (r"Evidence \cite{smith2026}.", "cite"),
        (r"Valid prose with $x \cite{source}$.", "cite"),
        (r"Valid prose with $x \emph{y}$.", "emph"),
        ("A % B.", "unescaped-text-special:%"),
        ("A # B.", "unescaped-text-special:#"),
        ("A & B.", "unescaped-text-special:&"),
        ("A_bad.", "unescaped-text-special:_"),
        ("A^bad.", "unescaped-text-special:^"),
    ),
)
def test_formal_prose_rejects_writer_divergent_tex(fragment: str, diagnostic: str) -> None:
    raw = {
        "t": "RawBlock",
        "c": ["latex", rf"\begin{{theorem}}{fragment}\end{{theorem}}"],
    }

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-raw-geometry\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Formal result"), raw]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/formalism.md",
        )

    assert exc_info.value.context["unsupported_command"] == diagnostic


def test_real_pandoc_writers_preserve_beamer_tex_and_reveal_formal_content(tmp_path: Path) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("Pandoc not installed")
    source = tmp_path / "formal.md"
    raw_json = tmp_path / "formal.json"
    composed_json = tmp_path / "formal-accessible.json"
    source.write_text(
        "# Formal methods {#sec:formal}\n\n"
        "[]{#sec:formal-alias}\n\n"
        "```{=latex}\n"
        "\\ifcsname proposition\\endcsname\n"
        "\\else\n"
        "\\newtheorem{proposition}{Proposition}\n"
        "\\fi\n"
        "```\n\n"
        "Visible introductory content.\n\n"
        "\\begin{proposition}[Finite support]\\label{prop:finite}\n"
        "Finite support is retained for $q \\to \\infty$ by \\texttt{solver} and "
        "(\\ref{eq:bound}).\n"
        "\\end{proposition}\n\n"
        "Visible closing content.\n",
        encoding="utf-8",
    )
    subprocess.run(
        [pandoc, str(source), "-t", "json", "-o", str(raw_json)],
        check=True,
        capture_output=True,
        text=True,
    )
    composition = load_and_compose_pandoc_json(
        raw_json,
        policy=AccessibleSlidePolicy(),
        source=str(source),
    )
    composed_json.write_text(json.dumps(composition.document), encoding="utf-8")

    reveal = subprocess.run(
        [pandoc, str(composed_json), "-f", "json", "-t", "revealjs", "--standalone", "--slide-level=2"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    beamer = subprocess.run(
        [pandoc, str(composed_json), "-f", "json", "-t", "beamer", "--standalone", "--slide-level=2"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    reveal = resolve_reveal_cross_references(reveal, {"eq:bound": "7"}, strict=True)
    beamer, replaced, unresolved = resolve_cross_deck_references(beamer, {"eq:bound": "7"})

    assert _empty_nonddivider_sections(reveal) == []
    assert 'id="sec:formal-alias"' in reveal
    assert 'class="formal-statement formal-proposition"' in reveal
    assert 'id="prop:finite"' in reveal
    assert "Finite support is retained" in reveal
    assert r"q \to \infty" in reveal
    assert "<code>solver</code>" in reveal
    assert '<span class="cross-reference">7</span>' in reveal
    assert "eq:bound" not in re.sub(r"<[^>]+>", "", reveal)
    assert r"\begin{proposition}" not in reveal

    assert beamer.count(r"\ifcsname proposition\endcsname") == 1
    assert beamer.count(r"\begin{proposition}[Finite support]\label{prop:finite}") == 1
    assert r"q \to \infty" in beamer
    assert replaced == 1
    assert unresolved == []
    assert "(7)" in beamer
    assert "formal-statement formal-proposition" not in beamer


def test_real_authored_raw_html_fails_before_either_slide_derivative(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / "raw-html.md"
    source.write_text(
        "## Invisible override\n\n<style>\n.reveal section { height: 200vh !important; }\n</style>\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-raw-geometry\]") as exc_info:
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert exc_info.value.context["unsupported_command"] == "raw-format:html"
    assert not (slides / "raw-html_slides.pdf").exists()
    assert not (slides / "raw-html_slides.html").exists()


def test_real_writer_divergent_formal_tex_fails_before_either_slide_derivative(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / "writer-divergence.md"
    source.write_text(
        "## Formal boundary\n\n\\begin{theorem}An unwrapped \\sum must not migrate grammars.\\end{theorem}\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-raw-geometry\]") as exc_info:
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert exc_info.value.context["unsupported_command"] == "sum"
    assert not (slides / "writer-divergence_slides.pdf").exists()
    assert not (slides / "writer-divergence_slides.html").exists()


def test_real_raw_inline_reference_is_visible_in_both_writers(tmp_path: Path) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("Pandoc not installed")
    source = tmp_path / "inline-reference.md"
    raw_json = tmp_path / "inline-reference.json"
    composed_json = tmp_path / "inline-reference-accessible.json"
    source.write_text(
        "## Reference parity\n\nSee \\ref{eq:bound} for the bound.\n",
        encoding="utf-8",
    )
    subprocess.run(
        [pandoc, str(source), "-t", "json", "-o", str(raw_json)],
        check=True,
        capture_output=True,
        text=True,
    )
    composition = load_and_compose_pandoc_json(
        raw_json,
        policy=AccessibleSlidePolicy(),
        source=str(source),
    )
    composed_json.write_text(json.dumps(composition.document), encoding="utf-8")

    reveal = subprocess.run(
        [pandoc, str(composed_json), "-f", "json", "-t", "revealjs", "--standalone", "--slide-level=2"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    beamer = subprocess.run(
        [pandoc, str(composed_json), "-f", "json", "-t", "beamer", "--standalone", "--slide-level=2"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    with pytest.raises(RenderingError, match=r"\[slides\.crossref\.reveal-unresolved\]"):
        resolve_reveal_cross_references(reveal, {}, strict=True)
    reveal = resolve_reveal_cross_references(reveal, {"eq:bound": "7"}, strict=True)
    beamer, replaced, unresolved = resolve_cross_deck_references(beamer, {"eq:bound": "7"})

    assert _empty_nonddivider_sections(reveal) == []
    assert '<span class="cross-reference">Equation (7)</span>' in reveal
    assert r"\ref{eq:bound}" not in reveal
    assert "See 7 for the bound." in beamer
    assert replaced == 1
    assert unresolved == []
