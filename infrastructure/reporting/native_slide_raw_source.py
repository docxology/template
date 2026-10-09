"""Finite exact lexical witnesses for the configured raw slide source forms."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

from infrastructure.reporting.native_format_content_contracts import text_tokens


@dataclass(frozen=True)
class RawSlideSegment:
    start: int
    end: int
    kind: str
    source: str
    tokens: tuple[str, ...] = ()
    target: str = ""


PROSE_COMMANDS = frozenset(
    {"emph", "texttt", "textbf", "textit", "textsl", "textsf", "textrm", "textsc", "mbox", "text", "caption"}
)
ESCAPES = {
    "_": "_",
    "%": "%",
    "#": "#",
    "&": "&",
    "{": "{",
    "}": "}",
    "$": "$",
    "textasciitilde": "~",
    "textbackslash": "\\",
}


def raw_slide_segments(
    source: str, kind: str, *, references: Mapping[str, str] | None = None
) -> tuple[tuple[RawSlideSegment, ...], tuple[str, ...]]:
    """Every painted raw byte has a text/math/reference witness or explicit blocker.

    Commands are a closed vocabulary established by actual configured-source
    inventory. Unknown commands never inherit support from their environment.
    Reference displays need independently source-derived label numbers/names.
    """
    if len(source.encode()) > 512 * 1024:
        raise ValueError("raw slide source exceeds original bounded lexical input")
    if re.search(r"\\(?:input|include|openin|openout|read|write|catcode|special|csname)\b", source):
        return (), ("raw slide source expands outside its original lexical scope",)
    segments: list[RawSlideSegment] = []
    blockers: list[str] = []
    ref = {} if references is None else references

    def balanced(start: int, opening: str = "{", closing: str = "}") -> tuple[int, int, int]:
        if start >= len(source) or source[start] != opening:
            raise ValueError("raw slide command has no exact lexical argument")
        depth, pos = 1, start + 1
        while pos < len(source):
            if source[pos] == "\\":
                pos += 2
                continue
            if source[pos] == opening:
                depth += 1
            elif source[pos] == closing:
                depth -= 1
                if depth == 0:
                    return start + 1, pos, pos + 1
            pos += 1
        raise ValueError("raw slide source has an unclosed original lexical argument")

    def add(start: int, end: int, tag: str, visible: str = "", target: str = "") -> None:
        if tag != "text" or text_tokens(visible):
            segments.append(RawSlideSegment(start, end, tag, source[start:end], text_tokens(visible), target))

    def scan(begin: int, end: int) -> None:
        pos = begin
        while pos < end:
            if source[pos] in "{}":
                if source[pos] == "{":
                    a, b, nxt = balanced(pos)
                    scan(a, b)
                    pos = nxt
                else:
                    raise ValueError("raw slide source has an unmatched lexical brace")
                continue
            if source.startswith(r"\(", pos) or source.startswith(r"\[", pos) or source[pos] == "$":
                opening = source[pos : pos + 2] if source[pos] == "\\" else "$"
                close = {r"\(": r"\)", r"\[": r"\]", "$": "$"}[opening]
                last = source.find(close, pos + len(opening))
                if last < 0 or last + len(close) > end:
                    raise ValueError("raw slide mathematical delimiter is unclosed")
                add(pos + len(opening), last, "math")
                pos = last + len(close)
                continue
            if source[pos] == "\\":
                match = re.match(r"\\([A-Za-z]+|.)", source[pos:end], re.DOTALL)
                if match is None:
                    raise ValueError("raw slide source has an invalid lexical command")
                command = match[1]
                after = pos + len(match[0])
                if command in ESCAPES:
                    add(pos, after, "text", ESCAPES[command])
                    pos = after
                    continue
                while after < end and source[after].isspace():
                    after += 1
                if command in PROSE_COMMANDS:
                    if command == "caption" and after < end and source[after] == "[":
                        _, _, after = balanced(after, "[", "]")
                    a, b, nxt = balanced(after)
                    scan(a, b)
                    pos = nxt
                    continue
                if command in {"label", "cref", "Cref", "ref", "eqref"}:
                    a, b, nxt = balanced(after)
                    label = source[a:b]
                    if command != "label":
                        display = ref.get(label)
                        if display is None:
                            blockers.append(f"independent source reference display required for {label}")
                            display = ""
                        add(pos, nxt, "reference", display, label)
                    pos = nxt
                    continue
                if command in {
                    "centering",
                    "hfill",
                    "medskip",
                    "smallskip",
                    "bigskip",
                    "noindent",
                    "par",
                    "newline",
                    "\\",
                }:
                    pos = after
                    continue
                blockers.append(f"unadmitted raw slide command {command}")
                pos = after
                continue
            nxt = pos
            while nxt < end and source[nxt] not in "\\{}$":
                nxt += 1
            visible = source[pos:nxt].replace("~", " ")
            add(pos, nxt, "text", visible)
            pos = nxt

    if kind == "raw-math":
        match = re.fullmatch(
            r"\s*\\begin\{(?:equation\*?|align\*?|gather\*?)\}(.*?)\\end\{[^}]+\}\s*", source, re.DOTALL
        )
        if match is None:
            raise ValueError("raw source math differs from its configured lexical form")
        add(match.start(1), match.end(1), "math")
    elif kind == "raw-formalism":
        match = re.fullmatch(
            r"\s*\\begin\{(definition|proposition|hypothesis|theorem|lemma|corollary|proof)\}(?:\[([^]]*)\])?(.*?)\\end\{\1\}\s*",
            source,
            re.DOTALL,
        )
        if match is None:
            raise ValueError("raw source formalism differs from its configured lexical form")
        if match[2]:
            scan(match.start(2), match.end(2))
        scan(match.start(3), match.end(3))
    elif kind == "raw-table":
        match = re.fullmatch(r"\s*\\begin\{table\}(?:\[[^]]*\])?(.*?)\\end\{table\}\s*", source, re.DOTALL)
        if match is None:
            raise ValueError("raw source table differs from its configured lexical form")
        scan(match.start(1), match.end(1))
    else:
        raise ValueError("raw source lexical admission requires an inventoried visible form")
    if not segments or len(segments) > 10_000:
        raise ValueError("raw source has no complete finite painted lexical segment set")
    return tuple(segments), tuple(blockers)
