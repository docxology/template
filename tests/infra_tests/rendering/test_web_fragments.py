"""Split-page navigation through real Pandoc and the normal web renderer."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._web_postprocess import resolve_split_page_fragments
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.web_renderer import WebRenderer


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
