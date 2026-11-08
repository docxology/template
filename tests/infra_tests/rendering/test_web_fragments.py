"""Split-page navigation through real Pandoc and the normal web renderer."""

import shutil
from collections.abc import Iterator
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._web_postprocess import resolve_split_page_fragments
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.web_renderer import WebRenderer
from infrastructure.transmission.transmission_bookends import BEGIN_FILENAME, END_FILENAME


class _Document(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: dict[str, str] = {}
        self.images: list[str] = []
        self.feed(path.read_text(encoding="utf-8"))
        self.close()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        identifier = values.get("id")
        if identifier is not None:
            self.ids.append(identifier)
        proof = values.get("data-proof")
        href = values.get("href")
        if tag == "a" and proof is not None and href is not None:
            self.links[proof] = href
        source = values.get("src")
        if tag == "img" and source is not None:
            self.images.append(source)

    handle_startendtag = handle_starttag


def _assert_resolves(page: Path, href: str) -> Path:
    parsed = urlsplit(href)
    target = page.parent / unquote(parsed.path) if parsed.path else page
    assert unquote(parsed.fragment) in _Document(target).ids
    return target


@pytest.mark.parametrize("namespace", ["", "paper-one-"])
def test_normal_web_output_binds_only_real_cross_page_fragments(tmp_path: Path, namespace: str) -> None:
    """Standalone and namespaced volume sections use the same source-derived pass."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    output = tmp_path / "output"
    figures = output / "figures"
    figures.mkdir(parents=True)
    (figures / "proof.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>',
        encoding="utf-8",
    )
    local = f"sec:{namespace}local"
    remote = f"sec:{namespace}remote"
    ambiguous = f"sec:{namespace}ambiguous"
    unusual = f"sec:{namespace}percent%:café & detail"
    encoded = f"#sec%3A{namespace}percent%25%3Acaf%C3%A9%20%26%20detail"
    source_texts = [
        f"# Introduction {{#{local}}}\n\n"
        f'<a data-proof="local" href="#{local}">Local</a>\n'
        f'<a data-proof="encoded-local" href="#sec%3A{namespace}local">Local encoded</a>\n'
        f'<a data-proof="cross" href="#{remote}">Next section</a>\n'
        f'<a data-proof="encoded" href="{encoded}">Encoded target</a>\n'
        '<a data-proof="index-only" href="#TOC">Combined contents</a>\n'
        '<a data-proof="missing" href="#unbound:target">Missing target remains visible</a>\n'
        '<a data-proof="stale" href="#stale:target">Not in this edition</a>\n'
        f'<a data-proof="ambiguous" href="#{ambiguous}">Ambiguous target</a>\n'
        '<a data-proof="external" href="https://example.org/paper#section">External</a>\n'
        '<a data-proof="asset" href="../figures/proof.svg#view">Figure file</a>\n'
        '<a data-proof="document" href="other.html#section">Explicit document</a>\n'
        '<img src="../figures/proof.svg" alt="Authored square">\n'
        f'<!-- <a href="#{remote}">Comment stays literal</a> -->\n'
        f"<script>const example = '<a href=\"#{remote}\">Literal</a>';</script>\n",
        f"# Target {{#{remote}}}\n\n"
        f'<span id="sec:{namespace}percent%:café &amp; detail">Unusual target</span>\n'
        f'<div id="{ambiguous}">First duplicate</div>\n',
        f'# Another section\n\n<div id="{ambiguous}">Second duplicate</div>\n',
    ]
    sources = []
    for index, text in enumerate(source_texts, 1):
        source = manuscript / f"{index:02}_{namespace}section.md"
        source.write_text(text, encoding="utf-8")
        sources.append(source)
    web = output / "web"
    web.mkdir()
    # Existing unrelated output must not become a definition in the current edition.
    (web / "stale__section.html").write_text('<p id="stale:target">Old output</p>', encoding="utf-8")
    (web / "other.html").write_text('<p id="section">Explicit target</p>', encoding="utf-8")
    renderer = WebRenderer(RenderingConfig(web_dir=str(web), output_dir=str(output), figures_dir=str(figures)))
    pages = [renderer.render(source) for source in sources]
    assert _Document(pages[0]).links["cross"] == f"#{remote}"
    index = renderer.render_combined(sources, manuscript, "fragment-proof")
    first = _Document(pages[0])
    combined = _Document(index)

    assert first.links["local"] == f"#{local}"
    assert first.links["encoded-local"] == f"#sec%3A{namespace}local"
    assert _assert_resolves(pages[0], first.links["local"]) == pages[0]
    assert _assert_resolves(pages[0], first.links["encoded-local"]) == pages[0]
    assert first.links["cross"] == f"{pages[1].name}#{remote}"
    assert _assert_resolves(pages[0], first.links["cross"]) == pages[1]
    assert first.links["encoded"] == pages[1].name + encoded
    assert _assert_resolves(pages[0], first.links["encoded"]) == pages[1]
    assert unusual in _Document(pages[1]).ids
    assert first.links["index-only"] == "index.html#TOC"
    assert _assert_resolves(pages[0], first.links["index-only"]) == index
    assert first.links["missing"] == "#unbound:target"
    assert not any("unbound:target" in _Document(page).ids for page in [*pages, index])
    assert first.links["stale"] == "#stale:target"
    assert first.links["ambiguous"] == f"#{ambiguous}"
    assert first.links["external"] == "https://example.org/paper#section"
    assert first.links["asset"] == "../figures/proof.svg#view"
    assert first.links["document"] == "other.html#section"
    assert first.images == ["../figures/proof.svg"]
    assert combined.links["cross"] == f"#{remote}"
    assert combined.links["encoded"] == encoded
    _assert_resolves(index, combined.links["cross"])
    _assert_resolves(index, combined.links["encoded"])
    content = pages[0].read_text(encoding="utf-8")
    assert f'<!-- <a href="#{remote}">Comment stays literal</a> -->' in content
    assert f"<script>const example = '<a href=\"#{remote}\">Literal</a>';</script>" in content
    assert [source.read_text(encoding="utf-8") for source in sources] == source_texts


@pytest.mark.parametrize("namespace", ["", "paper-one-"], ids=["ordinary", "namespaced"])
def test_normal_web_fragment_destinations_match_navigation_contract(tmp_path: Path, namespace: str) -> None:
    """Produced hrefs retain explicit local destinations and bind only live remote ones."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    output = tmp_path / "output"
    web = output / "web"
    figures = output / "figures"
    figures.mkdir(parents=True)
    asset = figures / "proof.svg"
    asset_bytes = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>'
    asset.write_bytes(asset_bytes)
    remote = f"sec:{namespace}remote"
    literal_local = f"sec%3A{namespace}remote"
    literal_remote = f"sec%3A{namespace}literal-remote"
    literal_ambiguous = f"amb%3A{namespace}remote"
    named_literal = f"name%3A{namespace}remote"
    local_template = (
        '<template><p id="inert-local">Not a local destination</p>'
        '<a name="inert-name"></a>'
        f'<a data-proof="inert-href" href="#{remote}">Inert navigation</a></template>'
    )
    remote_template = (
        '<template id="visible-template"><p id="TOC">Inert contents</p>'
        '<p id="ghost-id">Inert ID</p><a name="ghost-name"></a>'
        '<template><p id="ghost-nested">Nested inert ID</p></template>'
        '<p id="ghost-after-nested">Still inert</p>'
        '<script>const closingTemplate = "</template>";</script>'
        f'<a data-proof="inert-href" href="#{remote}">Inert navigation</a></template>\n'
        '<p id="after-template">Live after nested templates</p>\n'
        '<template/><p id="ghost-slash">The HTML self-closing flag is ignored</p></template>\n'
        '<p id="after-selfclosing">Live after a self-closing template start</p>'
    )
    local_hrefs = {
        "literal-local": f"#{literal_local}",
        "unicode-literal-local": "#café",
        "named-local": "#note",
        "encoded-name": "#no%74e",
        "literal-name": f"#{named_literal}",
        "top": "#top",
        "mixed-top": "#ToP",
        "encoded-top": "#%54%4F%50",
    }
    remote_hrefs = {
        "literal-remote": f"#{literal_remote}",
        "remote-name": "#legacy-remote",
        "inert-local": "#inert-local",
        "inert-name": "#inert-name",
        "template-element": "#visible-template",
        "after-template": "#after-template",
        "after-selfclosing": "#after-selfclosing",
        "index-only": "#TOC",
    }
    unknown_hrefs = {
        "ghost-id": "#ghost-id",
        "ghost-name": "#ghost-name",
        "ghost-nested": "#ghost-nested",
        "ghost-after-nested": "#ghost-after-nested",
        "ghost-slash": "#ghost-slash",
        "literal-ambiguous": f"#{literal_ambiguous}",
        "unknown": "#still-unknown",
    }
    source_texts = [
        "# Local section\n\n```{=html}\n"
        f'<p id="{literal_local}">Literal local ID</p>\n'
        '<p id="caf%C3%A9">Serialized Unicode literal local ID</p>\n'
        f'<a name="note"></a><a name="{named_literal}"></a>\n'
        + "\n".join(
            f'<a data-proof="{proof}" href="{href}">{proof}</a>'
            for proof, href in {**local_hrefs, **remote_hrefs, **unknown_hrefs}.items()
        )
        + '\n<a data-proof="asset" href="../figures/proof.svg#view">Figure file</a>\n'
        + '<img src="../figures/proof.svg" alt="Authored square">\n'
        + f'{local_template}\n<div style="height:2000px"></div>\n```\n',
        "# Remote section\n\n```{=html}\n"
        f'<p id="{remote}">Decoded remote, not the literal local target</p>\n'
        '<p id="café">Decoded Unicode remote cannot override a literal local ID</p>\n'
        f'<p id="{literal_remote}">Literal remote wins over a decoded remote</p>\n'
        f'<p id="{literal_ambiguous}">First ambiguous literal</p>\n'
        f'<p id="amb:{namespace}remote">Unique decoded target cannot hide literal ambiguity</p>\n'
        f'<p id="name:{namespace}remote">Decoded remote cannot override a local name</p>\n'
        '<p id="note">Remote cannot override a local name</p>\n'
        '<p id="top">Remote cannot override page top</p>\n'
        '<p id="ToP">Nor mixed-case top</p><p id="TOP">Nor encoded top</p>\n'
        '<a name="legacy-remote"></a><p id="inert-local">Real remote ID</p><a name="inert-name"></a>\n'
        f"{remote_template}\n```\n",
        "# Other section\n\n```{=html}\n"
        f'<p id="sec:{namespace}literal-remote">Decoded alternative</p>\n'
        f'<p id="{literal_ambiguous}">Second ambiguous literal</p>\n```\n',
    ]
    sources = []
    for number, text in enumerate(source_texts, 1):
        source = manuscript / f"{number:02}_{namespace}browser.md"
        source.write_text(text, encoding="utf-8")
        sources.append(source)
    renderer = WebRenderer(RenderingConfig(web_dir=str(web), output_dir=str(output), figures_dir=str(figures)))
    pages = [renderer.render(source) for source in sources]
    assert local_template in pages[0].read_text(encoding="utf-8")
    assert remote_template in pages[1].read_text(encoding="utf-8")
    index = renderer.render_combined(sources, manuscript, "browser-fragment-proof")
    # Inert hrefs and authored source bytes must survive the real finalization.
    assert local_template in pages[0].read_text(encoding="utf-8")
    assert remote_template in pages[1].read_text(encoding="utf-8")
    assert [source.read_text(encoding="utf-8") for source in sources] == source_texts

    # These destinations are authored fixture facts, not a second fragment resolver.
    # In particular, literal ambiguity must not fall through to a unique decoded ID.
    first = _Document(pages[0])
    assert first.links == {
        "literal-local": f"#sec%3A{namespace}remote",
        "unicode-literal-local": "#café",
        "named-local": "#note",
        "encoded-name": "#no%74e",
        "literal-name": f"#name%3A{namespace}remote",
        "top": "#top",
        "mixed-top": "#ToP",
        "encoded-top": "#%54%4F%50",
        "literal-remote": f"{pages[1].name}#sec%3A{namespace}literal-remote",
        "remote-name": f"{pages[1].name}#legacy-remote",
        "inert-local": f"{pages[1].name}#inert-local",
        "inert-name": f"{pages[1].name}#inert-name",
        "template-element": f"{pages[1].name}#visible-template",
        "after-template": f"{pages[1].name}#after-template",
        "after-selfclosing": f"{pages[1].name}#after-selfclosing",
        "index-only": "index.html#TOC",
        "ghost-id": "#ghost-id",
        "ghost-name": "#ghost-name",
        "ghost-nested": "#ghost-nested",
        "ghost-after-nested": "#ghost-after-nested",
        "ghost-slash": "#ghost-slash",
        "literal-ambiguous": f"#amb%3A{namespace}remote",
        "unknown": "#still-unknown",
        "asset": "../figures/proof.svg#view",
        "inert-href": f"#{remote}",
    }
    assert first.images == ["../figures/proof.svg"]
    assert asset.read_bytes() == asset_bytes
    assert _Document(pages[1]).links == {"inert-href": f"#{remote}"}
    # The combined reader has all live definitions; it must keep authored hrefs.
    assert _Document(index).links == {
        "literal-local": f"#sec%3A{namespace}remote",
        "unicode-literal-local": "#café",
        "named-local": "#note",
        "encoded-name": "#no%74e",
        "literal-name": f"#name%3A{namespace}remote",
        "top": "#top",
        "mixed-top": "#ToP",
        "encoded-top": "#%54%4F%50",
        "literal-remote": f"#sec%3A{namespace}literal-remote",
        "remote-name": "#legacy-remote",
        "inert-local": "#inert-local",
        "inert-name": "#inert-name",
        "template-element": "#visible-template",
        "after-template": "#after-template",
        "after-selfclosing": "#after-selfclosing",
        "index-only": "#TOC",
        "ghost-id": "#ghost-id",
        "ghost-name": "#ghost-name",
        "ghost-nested": "#ghost-nested",
        "ghost-after-nested": "#ghost-after-nested",
        "ghost-slash": "#ghost-slash",
        "literal-ambiguous": f"#amb%3A{namespace}remote",
        "unknown": "#still-unknown",
        "asset": "../figures/proof.svg#view",
        "inert-href": f"#{remote}",
    }


def test_fragment_resolution_quotes_document_names_and_preserves_markup(tmp_path: Path) -> None:
    index = tmp_path / "index.html"
    index.write_text('<p id="sec:remote">Combined</p>', encoding="utf-8")
    target = tmp_path / 'section & "quote".html'
    target.write_text('<p id="sec:remote">Target</p>', encoding="utf-8")
    page = tmp_path / "first.html"
    original = (
        '<!-- <a href="#sec:remote">Not an element</a> -->\n'
        "<script>const example = '<a href=\"#sec:remote\">Not an element</a>';</script>\n"
        '<p data-href="#sec:remote">Prose &amp; markup</p>\n'
        '<a class="authored" data-note=" href=\'#do-not-touch\'" '
        'data-href="#sec:remote" href="#sec%3Aremote">Read</a>\n'
    )
    page.write_text(original, encoding="utf-8")
    resolve_split_page_fragments(index, (page, target))
    expected = original.replace(' href="#sec%3Aremote"', ' href="section%20%26%20%22quote%22.html#sec%3Aremote"')
    assert page.read_text(encoding="utf-8") == expected
    assert _assert_resolves(page, "section%20%26%20%22quote%22.html#sec%3Aremote") == target


@pytest.mark.parametrize("unsafe", ["escape", "symlink"])
def test_fragment_resolution_refuses_unsafe_produced_pages(tmp_path: Path, unsafe: str) -> None:
    web = tmp_path / "web"
    web.mkdir()
    index = web / "index.html"
    index.write_text('<p id="sec:remote">Combined</p>', encoding="utf-8")
    outside = tmp_path / "outside.html"
    outside.write_text('<p id="sec:remote">Outside</p>', encoding="utf-8")
    page = outside
    if unsafe == "symlink":
        page = web / "section.html"
        page.symlink_to(outside)
    with pytest.raises(RenderingError, match="unsafe|leaves output/web"):
        resolve_split_page_fragments(index, (page,))
    assert outside.read_text(encoding="utf-8") == '<p id="sec:remote">Outside</p>'


@dataclass
class _HtmlNode:
    tag: str
    attrs: dict[str, str | None] = field(default_factory=dict)
    children: list["_HtmlNode | str"] = field(default_factory=list)

    def nodes(self) -> Iterator["_HtmlNode"]:
        yield self
        for child in self.children:
            if isinstance(child, _HtmlNode):
                yield from child.nodes()

    def text(self) -> str:
        return "".join(child if isinstance(child, str) else child.text() for child in self.children)


class _ReferenceDocument(HTMLParser):
    """Small DOM reader for visible labels and their actual produced anchors."""

    def __init__(self, page: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _HtmlNode("document")
        self.stack = [self.root]
        self.feed(page.read_text(encoding="utf-8"))
        self.close()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _HtmlNode(tag, dict(attrs))
        self.stack[-1].children.append(node)
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
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack[-1].children.append(_HtmlNode(tag, dict(attrs)))

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)

    def element(self, identifier: str) -> _HtmlNode:
        matches = [node for node in self.root.nodes() if node.attrs.get("id") == identifier]
        assert len(matches) == 1, (identifier, len(matches))
        return matches[0]


def _reference_links(node: _HtmlNode) -> list[tuple[str, str]]:
    return [
        (str(child.attrs["href"]), " ".join(child.text().split()))
        for child in node.nodes()
        if child.tag == "a" and child.attrs.get("href") is not None
    ]


def _reference_renderer(tmp_path: Path) -> tuple[Path, WebRenderer]:
    if shutil.which("pandoc") is None:
        pytest.skip("pandoc not available on PATH")
    # A qualified project path must not leak into browser-relative destinations.
    project = tmp_path / "projects" / "working" / "reference-proof"
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    output = project / "output"
    renderer = WebRenderer(
        RenderingConfig(
            web_dir=str(output / "web"),
            output_dir=str(output),
            figures_dir=str(output / "figures"),
        )
    )
    return manuscript, renderer


def test_finalized_split_formalism_uses_global_numbers_and_preserves_citation_groups(tmp_path: Path) -> None:
    """Forward/back references and independent counters span real source boundaries."""
    manuscript, renderer = _reference_renderer(tmp_path)
    opaque = (
        "<!-- [@def:fourth] -->\n"
        '<script>const citation = "[@def:fourth]";</script>\n'
        '<style>.example::after { content: "[@def:fourth]"; }</style>\n'
        '<template><a href="#def:fourth">[@def:fourth]</a></template>'
    )
    texts = [
        "# Opening {#sec:opening}\n\n"
        "::: {#forward}\n"
        "Compare [see @def:fourth, p. 7; @prop:later] and @def:third.\n"
        ":::\n\n"
        "::: {.definition #def:first}\nFirst body.\n:::\n\n"
        "::: {.definition #def:second}\nSecond body.\n:::\n\n"
        "::: {#mixed}\nPrior work [@def:third; @doe2020, p. 12; @roe2021].\n:::\n\n"
        "::: {#narrative}\n@doe2020 introduced the method.\n:::\n\n"
        "Opening note.[^opening]\n\n[^opening]: Opening footnote body.\n\n"
        "```{#literal-code}\n[@def:fourth]\n```\n\n"
        "```{=html}\n" + opaque + "\n```\n",
        "# Middle {#sec:middle}\n\n"
        "::: {.proposition #prop:later}\nProposition body.\n:::\n\n"
        "::: {.definition #def:third}\nThird body.\n:::\n\n"
        "::: {#backward}\nReturn to [@def:first; @def:second] and [@def:third].\n:::\n\n"
        "Middle note.[^middle]\n\n[^middle]: Middle footnote body.\n",
        "# Closing {#sec:closing}\n\n"
        "::: {.definition #def:fourth}\nFourth body.\n:::\n\n"
        "::: {#closing-refs}\nUse [@def:third] and [@prop:later] with [@def:fourth].\n:::\n",
    ]
    # Equal basenames in distinct source directories must retain distinct owners.
    sources = [manuscript / part / "01_section.md" for part in ("opening", "middle", "closing")]
    for source, text in zip(sources, texts, strict=True):
        source.parent.mkdir()
        source.write_text(text, encoding="utf-8")
    (manuscript / "references.bib").write_text(
        "@book{doe2020, author={Doe, Jane}, title={Global Context}, year={2020}, publisher={Example}}\n",
        encoding="utf-8",
    )
    (manuscript / "z_supplemental.bib").write_text(
        "@book{roe2021, author={Roe, Richard}, title={Stable Destinations}, year={2021}, publisher={Example}}\n",
        encoding="utf-8",
    )
    pages = [renderer.render(source) for source in sources]
    index = renderer.render_combined(sources, manuscript, "working/reference-proof")
    documents = [_ReferenceDocument(page) for page in pages]
    combined = _ReferenceDocument(index)

    expected = [
        (
            "forward",
            0,
            [(2, "def:fourth", "Definition 4"), (1, "prop:later", "Proposition 1"), (1, "def:third", "Definition 3")],
        ),
        (
            "backward",
            1,
            [(0, "def:first", "Definition 1"), (0, "def:second", "Definition 2"), (1, "def:third", "Definition 3")],
        ),
        (
            "closing-refs",
            2,
            [(1, "def:third", "Definition 3"), (1, "prop:later", "Proposition 1"), (2, "def:fourth", "Definition 4")],
        ),
    ]
    for identifier, owner, references in expected:
        split_links = _reference_links(documents[owner].element(identifier))
        assert split_links == [
            (f"#{label}" if target == owner else f"{pages[target].name}#{label}", number)
            for target, label, number in references
        ]
        assert _reference_links(combined.element(identifier)) == [
            (f"#{label}", number) for _, label, number in references
        ]
        for (href, _), (target, _, _) in zip(split_links, references, strict=True):
            assert _assert_resolves(pages[owner], href) == pages[target]
    assert "see Definition 4, p. 7" in " ".join(documents[0].element("forward").text().split())
    for owner, label, heading in [
        (0, "def:first", "Definition 1."),
        (0, "def:second", "Definition 2."),
        (1, "def:third", "Definition 3."),
        (1, "prop:later", "Proposition 1."),
        (2, "def:fourth", "Definition 4."),
    ]:
        assert documents[owner].element(label).text().strip().startswith(heading)
        assert combined.element(label).text().strip().startswith(heading)

    for document, page in [(documents[0], pages[0]), (combined, index)]:
        mixed = document.element("mixed")
        assert "Definition 3" in mixed.text()
        for word in ("Doe", "2020", "12", "Roe", "2021"):
            assert word in mixed.text()
        assert "@" not in mixed.text()
        bibliography_links = [href for href, _ in _reference_links(mixed) if urlsplit(href).fragment.startswith("ref-")]
        assert {urlsplit(href).fragment for href in bibliography_links} == {"ref-doe2020", "ref-roe2021"}
        for href in bibliography_links:
            target = _assert_resolves(page, href)
            assert target == index
            entry = _ReferenceDocument(target).element(urlsplit(href).fragment).text()
            assert ("Global Context" if href.endswith("ref-doe2020") else "Stable Destinations") in entry
        narrative = document.element("narrative")
        assert "Doe" in narrative.text() and "2020" in narrative.text()
        assert "@" not in narrative.text()
        assert len(_reference_links(narrative)) == 1
        assert _assert_resolves(page, _reference_links(narrative)[0][0]) == index

    for owner, number, body in [(0, "1", "Opening footnote body."), (1, "2", "Middle footnote body.")]:
        for document, page in [(documents[owner], pages[owner]), (combined, index)]:
            notes = [node for node in document.root.nodes() if node.attrs.get("role") == "doc-noteref"]
            # The combined reader contains both notes; each split page contains its own.
            note = next(node for node in notes if node.text().strip() == number)
            target = _assert_resolves(page, str(note.attrs["href"]))
            assert target == index
            target_document = _ReferenceDocument(target)
            assert body in target_document.element(urlsplit(str(note.attrs["href"])).fragment).text()
            for backlink, _ in _reference_links(target_document.element(urlsplit(str(note.attrs["href"])).fragment)):
                _assert_resolves(target, backlink)
    assert opaque in pages[0].read_text(encoding="utf-8")
    assert documents[0].element("literal-code").text().strip() == "[@def:fourth]"
    assert [source.read_text(encoding="utf-8") for source in sources] == texts


def test_finalized_split_crossref_numbers_figures_tables_equations_and_sections_globally(tmp_path: Path) -> None:
    """Real optional pandoc-crossref resolves forward/back references, not label guesses."""
    if shutil.which("pandoc-crossref") is None:
        pytest.skip("pandoc-crossref not available on PATH")
    manuscript, renderer = _reference_renderer(tmp_path)
    (manuscript / "config.yaml").write_text(
        "paper:\n  title: Cross-reference publication\nmetadata:\n  language: en-US\n",
        encoding="utf-8",
    )
    figures = Path(renderer.config.figures_dir)
    figures.mkdir(parents=True)
    (figures / "square.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>',
        encoding="utf-8",
    )
    sources = []
    for number, (name, other) in enumerate([("first", "second"), ("second", "first")], 1):
        source = manuscript / f"0{number}_{name}.md"
        source.write_text(
            f"# {name.title()} {{#sec:{name}}}\n\n"
            f"::: {{#references-{name}}}\n"
            f"See [@fig:{other}; @tbl:{other}; @eq:{other}; @sec:{other}]. "
            f"Local [@fig:{name}].\n:::\n\n"
            f"::: {{#narrative-{name}}}\n@fig:{other} illustrates the other source.\n:::\n\n"
            f"![Authored square {name}.](../output/figures/square.svg){{#fig:{name}}}\n\n"
            "| Value | Result |\n|-------|--------|\n| 1 | 2 |\n"
            f": Outcomes {name}. {{#tbl:{name}}}\n\n"
            f"$$x_{number} = {number}$$ {{#eq:{name}}}\n",
            encoding="utf-8",
        )
        sources.append(source)
    pages = [renderer.render(source) for source in sources]
    index = renderer.render_combined(sources, manuscript, "working/reference-proof")
    combined = _ReferenceDocument(index)
    for owner, (name, other, other_number) in enumerate([("first", "second", "2"), ("second", "first", "1")]):
        document = _ReferenceDocument(pages[owner])
        labels = [f"{kind}:{other}" for kind in ("fig", "tbl", "eq", "sec")] + [f"fig:{name}"]
        expected_numbers = [other_number] * 4 + [str(owner + 1)]
        for reader, page in [(document, pages[owner]), (combined, index)]:
            links = _reference_links(reader.element(f"references-{name}"))
            assert [urlsplit(href).fragment for href, _ in links] == labels
            assert [text.strip("()") for _, text in links] == expected_numbers
            assert "@" not in reader.element(f"references-{name}").text()
            for position, (href, _) in enumerate(links):
                target = index if page == index else pages[owner if position == 4 else 1 - owner]
                assert _assert_resolves(page, href) == target
            narrative = _reference_links(reader.element(f"narrative-{name}"))
            assert len(narrative) == 1
            assert narrative[0][1] == other_number
            assert _assert_resolves(page, narrative[0][0]) == (index if page == index else pages[1 - owner])
        # Numbered captions and headings must agree with references, not just each other.
        assert f"Figure {owner + 1}:" in " ".join(document.element(f"fig:{name}").text().split())
        assert f"Table {owner + 1}:" in " ".join(document.element(f"tbl:{name}").text().split())
        assert document.element(f"sec:{name}").text().strip().startswith(str(owner + 1))


@pytest.mark.parametrize("bom", ["", "\ufeff"])
def test_combined_only_call_produces_a_resolved_single_source_page_with_yaml_metadata(tmp_path: Path, bom: str) -> None:
    """Source ownership must not displace leading YAML or require a preview call."""
    manuscript, renderer = _reference_renderer(tmp_path)
    source = manuscript / "01_contract.md"
    content = (
        bom + "---\n"
        "title: Single Source Context\n"
        "formalism_kinds:\n"
        "  definition: Contract\n"
        "---\n\n"
        "# Scope {#sec:scope}\n\n"
        "::: {#single-forward}\nSee [@def:second].\n:::\n\n"
        "::: {.definition #def:first}\nFirst contract.\n:::\n\n"
        "::: {.definition #def:second}\nSecond contract.\n:::\n"
    )
    source.write_text(content, encoding="utf-8")
    index = renderer.render_combined([source], manuscript, "working/reference-proof")
    pages = [page for page in index.parent.glob("*.html") if page != index]
    assert len(pages) == 1
    for page in [pages[0], index]:
        document = _ReferenceDocument(page)
        assert document.element("def:first").text().strip().startswith("Contract 1.")
        assert document.element("def:second").text().strip().startswith("Contract 2.")
        assert _reference_links(document.element("single-forward")) == [("#def:second", "Contract 2")]
        assert _assert_resolves(page, "#def:second") == page
        titles = [node.text() for node in document.root.nodes() if node.tag == "title"]
        assert titles == ["Single Source Context"]
    assert source.read_text(encoding="utf-8") == content


def test_finalized_pages_keep_generated_transmission_bookends_combined_only(tmp_path: Path) -> None:
    """Project finalization must not add section artifacts excluded by the existing pipeline."""
    manuscript, renderer = _reference_renderer(tmp_path)
    texts = [
        "# Opening transmission {#bookend:opening}\n\nOpening boundary.\n",
        '# Body {#sec:body}\n\n<a data-proof="opening" href="#bookend:opening">Opening</a>\n'
        '<a data-proof="closing" href="#bookend:closing">Closing</a>\n',
        "# Closing transmission {#bookend:closing}\n\nClosing boundary.\n",
    ]
    sources = []
    for name, text in zip((BEGIN_FILENAME, "01_body.md", END_FILENAME), texts, strict=True):
        source = manuscript / name
        source.write_text(text, encoding="utf-8")
        sources.append(source)
    index = renderer.render_combined(sources, manuscript, "working/reference-proof")
    pages = [page for page in index.parent.glob("*.html") if page != index]
    assert len(pages) == 1
    section = _Document(pages[0])
    combined = _Document(index)
    assert {"bookend:opening", "bookend:closing"} <= set(combined.ids)
    assert not ({"bookend:opening", "bookend:closing"} & set(section.ids))
    assert _assert_resolves(pages[0], section.links["opening"]) == index
    assert _assert_resolves(pages[0], section.links["closing"]) == index
    assert [source.read_text(encoding="utf-8") for source in sources] == texts
