"""Validate same-page Pandoc citation links in the combined HTML reader."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import unquote

from infrastructure.rendering._pandoc_filters import CROSS_REFERENCE_KEY_PREFIXES

_CROSS_REFERENCE_IDS = tuple(f"ref-{prefix}" for prefix in CROSS_REFERENCE_KEY_PREFIXES)
_VOID_TAGS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
)
_INERT_CONTENT_TAGS = frozenset(
    {"iframe", "noembed", "noframes", "noscript", "script", "style", "template", "textarea", "title", "xmp"}
)
# A paragraph's end tag can be omitted before these HTML elements.
_PARAGRAPH_END_FOLLOWERS = frozenset(
    {
        "address",
        "article",
        "aside",
        "blockquote",
        "details",
        "dialog",
        "div",
        "dl",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hgroup",
        "hr",
        "main",
        "menu",
        "nav",
        "ol",
        "p",
        "pre",
        "search",
        "section",
        "table",
        "ul",
    }
)
_DEFINITION_END_FOLLOWERS = frozenset({"dt", "dd"})
_RUBY_END_FOLLOWERS = frozenset({"rp", "rt"})
_ROW_GROUP_END_FOLLOWERS = frozenset({"tbody", "tfoot"})
_ROW_END_FOLLOWERS = _ROW_GROUP_END_FOLLOWERS | {"tr"}
_CELL_END_FOLLOWERS = _ROW_END_FOLLOWERS | {"td", "th"}
_CAPTION_AND_COLUMN_GROUP_END_FOLLOWERS = _ROW_END_FOLLOWERS | {"colgroup", "thead"}
_OPTIONAL_END_FOLLOWERS = {
    "p": _PARAGRAPH_END_FOLLOWERS,
    "li": frozenset({"li"}),
    "dt": _DEFINITION_END_FOLLOWERS,
    "dd": _DEFINITION_END_FOLLOWERS,
    "rp": _RUBY_END_FOLLOWERS,
    "rt": _RUBY_END_FOLLOWERS,
    "td": _CELL_END_FOLLOWERS,
    "th": _CELL_END_FOLLOWERS,
    "tr": _ROW_END_FOLLOWERS,
    "caption": _CAPTION_AND_COLUMN_GROUP_END_FOLLOWERS,
    "colgroup": _CAPTION_AND_COLUMN_GROUP_END_FOLLOWERS,
    "thead": _ROW_GROUP_END_FOLLOWERS,
    "tbody": _ROW_GROUP_END_FOLLOWERS,
}


@dataclass(frozen=True, slots=True)
class _Element:
    tag: str
    inert_content: bool = False
    visible: bool = True
    bibliography: bool = False
    entry_id: str | None = None


class _CitationDocument(HTMLParser):
    """Collect real IDs and entries with visible text from the supported markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.identifiers: Counter[str] = Counter()
        self.citations: dict[str, int] = {}
        self.entries_with_text: set[str] = set()
        self._elements = [_Element("")]

    def _close_optional_elements(self, tag: str) -> None:
        while True:
            index = -1
            # A trailing paragraph can also end with its containing item or cell.
            if self._elements[-1].tag == "p" and tag not in _PARAGRAPH_END_FOLLOWERS:
                index = -2
            followers = _OPTIONAL_END_FOLLOWERS.get(self._elements[index].tag, ())
            if tag not in followers:
                return
            # A real enclosing element (such as a nested list) stops the cascade.
            del self._elements[index:]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._close_optional_elements(tag)
        parent = self._elements[-1]
        attributes = dict(reversed(attrs))  # HTML uses the first occurrence.
        identifier = attributes.get("id")
        if identifier is not None and not parent.inert_content:
            self.identifiers[identifier] += 1

        inert_content = parent.inert_content or tag in _INERT_CONTENT_TAGS
        visible = (
            parent.visible
            and not inert_content
            and tag != "head"
            and "hidden" not in attributes
            and (attributes.get("aria-hidden") or "").lower() != "true"
        )
        roles = (attributes.get("role") or "").split()
        href = (attributes.get("href") or "").strip(" \t\r\n\f")
        if visible and tag == "a" and "doc-biblioref" in roles and href.startswith("#"):
            self.citations.setdefault(href, self.getpos()[0])

        if tag in _VOID_TAGS:
            return
        classes = (attributes.get("class") or "").split()
        bibliography = (
            parent.bibliography or identifier == "refs" or "csl-bib-body" in classes or "doc-bibliography" in roles
        )
        entry_id = identifier if parent.bibliography and "csl-entry" in classes else parent.entry_id
        self._elements.append(_Element(tag, inert_content, visible, bibliography, entry_id))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag in {"math", "svg"}:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self._elements) - 1, 0, -1):
            element = self._elements[index]
            if element.tag == tag:
                del self._elements[index:]
                return
            if element.tag in _INERT_CONTENT_TAGS:
                return

    def handle_data(self, data: str) -> None:
        current = self._elements[-1]
        if current.entry_id is not None and current.visible and data.strip():
            self.entries_with_text.add(current.entry_id)


def web_citation_issues(content: str) -> list[str]:
    """Return failures for emitted bibliography links with unusable destinations."""

    document = _CitationDocument()
    document.feed(content)
    document.close()

    issues: list[str] = []
    for href, line in document.citations.items():
        identifier = unquote(href[1:])
        # Citeproc can label unresolved cross-references as bibliography links
        # when their optional resolver is unavailable.
        if identifier.startswith(_CROSS_REFERENCE_IDS):
            continue
        count = document.identifiers[identifier]
        if count == 0:
            reason = f"targets missing ID {identifier!r}"
        elif count > 1:
            reason = f"targets duplicate ID {identifier!r}"
        elif not identifier or identifier not in document.entries_with_text:
            reason = f"does not target a nonempty visible bibliography entry with ID {identifier!r}"
        else:
            continue
        issues.append(f"Bibliography link {href!r} at line {line} {reason}")
    return issues
