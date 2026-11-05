"""Small deterministic controls used by the accessible Reveal postprocessor."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser


_REVEAL_INITIALIZER_OPEN_RE = re.compile(
    r"\bReveal\s*\.\s*initialize\s*\(\s*\{",
    flags=re.IGNORECASE,
)
_SCROLL_ACTIVATION_KEY_RE = re.compile(
    r"(?<![\w$])scrollActivationWidth\s*:",
    flags=re.IGNORECASE,
)
_SCROLL_ACTIVATION_SIMPLE_RE = re.compile(
    r"(?<![\w$])scrollActivationWidth\s*:\s*(?:null|[-+]?\d+(?:\.\d+)?)",
    flags=re.IGNORECASE,
)
_SCROLL_ACTIVATION_DISABLED_RE = re.compile(
    r"(?<![\w$])scrollActivationWidth\s*:\s*null\b",
    flags=re.IGNORECASE,
)
_ACCESSIBLE_VIEWPORT = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
_ACCESSIBLE_VIEWPORT_CONTENT = "width=device-width,initial-scale=1.0"
_INTERACTIVE_KEYBOARD_GUARD = """<script data-template-interactive-keyboard-guard>
(function () {
  document.addEventListener("keydown", function (event) {
    var target = event.target;
    if (!(target instanceof Element)) return;
    var control = target.closest(
      ".reveal summary, .reveal button, .reveal [role='button'], " +
      ".reveal input[type='checkbox'], .reveal input[type='radio']"
    );
    if (!control || (event.key !== " " && event.key !== "Spacebar")) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    control.click();
  }, true);
}());
</script>"""


@dataclass
class _RenderedSlideState:
    depth: int
    divider: bool
    heading_depth: int = 0
    heading: list[str] = field(default_factory=list)
    visible_body: bool = False


@dataclass(frozen=True)
class _ViewportMetaElement:
    """One parsed viewport element and its exact source span."""

    start: int
    end: int
    attributes: tuple[tuple[str, str | None], ...]

    def values(self, name: str) -> tuple[str | None, ...]:
        """Return actual parsed attribute values without inspecting peers."""

        folded = name.casefold()
        return tuple(value for key, value in self.attributes if key.casefold() == folded)


class _ViewportMetaParser(HTMLParser):
    """Locate real viewport metadata without regexing quoted attribute values."""

    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=False)
        self._source = source
        self._line_offsets = [0]
        self._line_offsets.extend(match.end() for match in re.finditer(r"\n", source))
        self.viewport_elements: list[_ViewportMetaElement] = []
        self.head_close_start: int | None = None

    def _absolute_offset(self) -> int:
        line, column = self.getpos()
        return self._line_offsets[line - 1] + column

    def _record_meta(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "meta":
            return
        names = tuple(value for key, value in attrs if key.casefold() == "name")
        if not any((value or "").casefold() == "viewport" for value in names):
            return
        raw = self.get_starttag_text() or ""
        start = self._absolute_offset()
        self.viewport_elements.append(
            _ViewportMetaElement(
                start=start,
                end=start + len(raw),
                attributes=tuple(attrs),
            )
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record_meta(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record_meta(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "head" and self.head_close_start is None:
            self.head_close_start = self._absolute_offset()


def _parsed_viewport_metadata(content: str) -> _ViewportMetaParser:
    parser = _ViewportMetaParser(content)
    parser.feed(content)
    parser.close()
    return parser


def _reveal_initializer_object_span(content: str) -> tuple[int, int] | None:
    """Return the sole generated Reveal configuration object span."""

    initializers = tuple(_REVEAL_INITIALIZER_OPEN_RE.finditer(content))
    if len(initializers) != 1:
        return None
    start = initializers[0].end() - 1
    depth = 0
    quote = ""
    escaped = False
    line_comment = False
    block_comment = False
    index = start
    while index < len(content):
        character = content[index]
        following = content[index + 1] if index + 1 < len(content) else ""
        if line_comment:
            if character in "\r\n":
                line_comment = False
            index += 1
            continue
        if block_comment:
            if character == "*" and following == "/":
                block_comment = False
                index += 2
            else:
                index += 1
            continue
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = ""
            index += 1
            continue
        if character in {"'", '"', "`"}:
            quote = character
            index += 1
            continue
        if character == "/" and following == "/":
            line_comment = True
            index += 2
            continue
        if character == "/" and following == "*":
            block_comment = True
            index += 2
            continue
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return start, index + 1
        index += 1
    return None


class _RenderedSlideBodyParser(HTMLParser):
    """Collect non-divider Reveal slides with no visible non-heading body."""

    _VISIBLE_REPLACED_ELEMENTS = frozenset({"audio", "canvas", "img", "math", "svg", "table", "video"})
    _IGNORED_ELEMENTS = frozenset({"script", "style", "template"})
    _VOID_ELEMENTS = frozenset(
        {
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
        }
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._section_depth = 0
        self._ignored_depth = 0
        self._slides: list[_RenderedSlideState] = []
        self.title_only_headings: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.casefold()
        attributes = {name.casefold(): value or "" for name, value in attrs}
        classes = set(attributes.get("class", "").split())
        starts_ignored_subtree = (
            lowered in self._IGNORED_ELEMENTS
            or any(name.casefold() == "hidden" for name, _value in attrs)
            or "visually-hidden" in classes
            or (lowered == "aside" and "notes" in classes)
        )
        ignored = self._ignored_depth > 0 or starts_ignored_subtree
        if ignored and lowered not in self._VOID_ELEMENTS:
            self._ignored_depth += 1
        if lowered == "section":
            self._section_depth += 1
        if lowered == "section" and attributes.get("aria-roledescription", "").casefold() == "slide":
            self._slides.append(
                _RenderedSlideState(
                    depth=self._section_depth,
                    divider="section-divider" in classes,
                )
            )
        for slide in self._slides:
            if ignored:
                continue
            if lowered in {f"h{level}" for level in range(1, 7)}:
                slide.heading_depth += 1
            elif lowered in self._VISIBLE_REPLACED_ELEMENTS and slide.heading_depth == 0:
                slide.visible_body = True

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.casefold()
        if self._ignored_depth == 0:
            for slide in self._slides:
                if lowered in {f"h{level}" for level in range(1, 7)} and slide.heading_depth > 0:
                    slide.heading_depth -= 1
        if lowered == "section" and self._slides and self._slides[-1].depth == self._section_depth:
            slide = self._slides.pop()
            if not slide.divider and not slide.visible_body:
                heading = " ".join(slide.heading)
                self.title_only_headings.append(" ".join(heading.split()) or "<untitled>")
        if lowered == "section" and self._section_depth > 0:
            self._section_depth -= 1
        if lowered not in self._VOID_ELEMENTS and self._ignored_depth > 0:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not data.strip() or self._ignored_depth > 0:
            return
        for slide in self._slides:
            if slide.heading_depth > 0:
                slide.heading.append(data)
            else:
                slide.visible_body = True


def rendered_title_only_headings(content: str) -> tuple[str, ...]:
    """Return headings for non-divider slides without visible body content."""

    parser = _RenderedSlideBodyParser()
    parser.feed(content)
    parser.close()
    return tuple(parser.title_only_headings)


def normalize_reveal_viewport(content: str) -> str:
    """Replace all viewport declarations with one scalable declaration."""

    parsed = _parsed_viewport_metadata(content)
    insertion = parsed.head_close_start
    if insertion is None:
        return content
    normalized = content[:insertion] + _ACCESSIBLE_VIEWPORT + content[insertion:]
    inserted_length = len(_ACCESSIBLE_VIEWPORT)
    for element in reversed(parsed.viewport_elements):
        start = element.start
        end = element.end
        line_start = content.rfind("\n", 0, start) + 1
        following_newline = content.find("\n", end)
        if (
            not content[line_start:start].strip()
            and following_newline >= 0
            and not content[end:following_newline].strip()
        ):
            start = line_start
            end = following_newline + 1
        adjustment = inserted_length if start >= insertion else 0
        start += adjustment
        end += adjustment
        normalized = normalized[:start] + normalized[end:]
    return normalized


def add_interactive_keyboard_guard(content: str) -> str:
    """Activate Space-capable controls without triggering Reveal navigation."""

    if "data-template-interactive-keyboard-guard" in content:
        return content
    return content.replace("</body>", _INTERACTIVE_KEYBOARD_GUARD + "\n</body>", 1)


def disable_automatic_reveal_scroll(content: str) -> str:
    """Keep narrow responsive layout under the accessible profile's CSS.

    Reveal 5 automatically activates a fixed-canvas scroll view below 435 CSS
    pixels.  That view scales each 960 by 700 slide even when surrounding CSS
    reflows, making the declared point-size floors physically tiny.  ``null``
    is Reveal's documented type-level off switch: activation occurs only when
    the setting is numeric.  Normalize a simple existing setting or inject one
    deterministic setting into the generated object literal.
    """

    span = _reveal_initializer_object_span(content)
    if span is None:
        return content
    start, end = span
    body = content[start + 1 : end - 1]
    settings = tuple(_SCROLL_ACTIVATION_KEY_RE.finditer(body))
    if settings:
        normalized = _SCROLL_ACTIVATION_SIMPLE_RE.sub(
            "scrollActivationWidth: null",
            body,
            count=1,
        )
    else:
        normalized = "\n    scrollActivationWidth: null," + body
    return content[: start + 1] + normalized + content[end - 1 :]


def reveal_scroll_activation_issues(content: str) -> tuple[str, ...]:
    """Return issues that would restore Reveal's narrow fixed-canvas scale."""

    span = _reveal_initializer_object_span(content)
    if span is None:
        return ("Reveal automatic narrow scroll scaling is not disabled",)
    start, end = span
    body = content[start + 1 : end - 1]
    settings = tuple(_SCROLL_ACTIVATION_KEY_RE.finditer(body))
    if not settings:
        return ("Reveal automatic narrow scroll scaling is not disabled",)
    if len(settings) != 1:
        return (f"Reveal scrollActivationWidth appears {len(settings)} times",)
    if _SCROLL_ACTIVATION_DISABLED_RE.search(body) is None:
        return ("Reveal automatic narrow scroll scaling is not disabled",)
    return ()


def reveal_viewport_issues(content: str) -> tuple[str, ...]:
    """Return viewport multiplicity, empty-content, and zoom-blocking issues."""

    viewports = tuple(_parsed_viewport_metadata(content).viewport_elements)
    if not viewports:
        return ("Reveal viewport metadata is missing",)
    issues: list[str] = []
    if len(viewports) != 1:
        issues.append(f"Reveal viewport metadata appears {len(viewports)} times")
    for viewport in viewports:
        content_values = viewport.values("content")
        content_value = "" if not content_values else content_values[0] or ""
        if not content_value.strip():
            issues.append("Reveal viewport content is missing or empty")
            break
        normalized = re.sub(r"\s+", "", content_value.casefold())
        noncanonical = "Reveal viewport content is not the canonical responsive declaration"
        if normalized != _ACCESSIBLE_VIEWPORT_CONTENT and noncanonical not in issues:
            issues.append(noncanonical)
        if re.search(r"user-scalable=(?:no|0)(?:[,\"'>/]|$)", normalized):
            issues.append("Reveal viewport disables user zoom")
            break
        if "maximum-scale=" in normalized or "minimum-scale=" in normalized:
            issues.append("Reveal viewport constrains user zoom")
            break
    return tuple(issues)
