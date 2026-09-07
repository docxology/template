"""Fail-closed raw-TeX admission for the accessible slide profile."""

from __future__ import annotations

from dataclasses import dataclass
import html
import re
from typing import Any

from infrastructure.rendering._slides_accessibility_contracts import density_error


_RAW_TEX_COMMAND_RE = re.compile(r"\\([A-Za-z@]+|.)")
_SAFE_THEOREM_BLOCK_RE = re.compile(
    r"\A\s*\\begin\{(?P<environment>definition|lemma|proposition|theorem|corollary|hypothesis|proof|remark)\}"
    r"(?:\[(?P<title>[^\]\r\n]*)\])?\s*"
    r"(?:\\label\{(?P<label>[-:._A-Za-z0-9]+)\})?"
    r"(?P<body>.*?)"
    r"\\end\{(?P=environment)\}\s*\Z",
    re.DOTALL,
)
_SAFE_PROPOSITION_DECLARATION_RE = re.compile(
    r"\A\s*\\ifcsname\s+proposition\\endcsname\s*"
    r"\\else\s*\\newtheorem\{proposition\}\{Proposition\}\s*\\fi\s*\Z"
)
_SAFE_RAW_INLINE_RE = re.compile(r"\A\s*\\ref\{(?P<label>[-:._A-Za-z0-9]+)\}\s*\Z")
_TEXT_COMMAND_RE = re.compile(r"\\(?P<command>texttt|textbf|textit|emph|ref|label)\{(?P<argument>[^{}]*)\}")
_MAX_RAW_TEX_CHARACTERS = 65_536
_SAFE_TEXT_ESCAPES = frozenset({" ", "#", "%", "&", ",", "_", "{", "}"})
_UNESCAPED_TEXT_SPECIALS = frozenset({"#", "$", "%", "&", "_", "^", "{", "}"})
_UNESCAPED_MATH_SPECIALS = frozenset({"#", "%", "&"})
_SAFE_MATH_COMMANDS = frozenset(
    {
        ",",
        "_",
        "{",
        "}",
        "|",
        "alpha",
        "ast",
        "beta",
        "boldsymbol",
        "exp",
        "ge",
        "geq",
        "infty",
        "kappa",
        "label",
        "lambda",
        "le",
        "log",
        "mathcal",
        "mathrm",
        "operatorname",
        "pi",
        "ref",
        "rm",
        "sum",
        "tau",
        "textbf",
        "textit",
        "texttt",
        "to",
    }
)


@dataclass(frozen=True)
class _RawTexFormalBlock:
    """Validated theorem-like source retained for writer-specific projection."""

    environment: str
    title: str | None
    label: str | None
    body: str


@dataclass(frozen=True)
class _MathFragment:
    """One explicitly delimited TeX math fragment found in linear time."""

    start: int
    end: int
    body: str
    display: bool


def _next_unescaped_dollar(source: str, start: int) -> int | None:
    """Return the next dollar not immediately escaped by a backslash."""

    index = source.find("$", start)
    while index >= 0:
        if index == 0 or source[index - 1] != "\\":
            return index
        index = source.find("$", index + 1)
    return None


def _math_fragments(source: str) -> tuple[_MathFragment, ...]:
    r"""Return non-overlapping math fragments with one forward-only scan.

    The former alternation used a lazy wildcard for each possible opener. A
    run of unmatched openers therefore rescanned the remaining suffix once per
    opener. Fixed-delimiter searches consume every matched suffix exactly once;
    after an unmatched opener, validation treats the remainder as prose and
    fails it at the ordinary raw-TeX boundary.
    """

    fragments: list[_MathFragment] = []
    index = 0
    while index < len(source):
        opener_length = 0
        closer = ""
        display = False
        if source.startswith(r"\[", index):
            opener_length, closer, display = 2, r"\]", True
        elif source.startswith("$$", index):
            opener_length, closer, display = 2, "$$", True
        elif source.startswith(r"\(", index):
            opener_length, closer = 2, r"\)"
        elif source[index] == "$" and (index == 0 or source[index - 1] != "\\") and not source.startswith("$$", index):
            opener_length, closer = 1, "$"
        else:
            index += 1
            continue

        body_start = index + opener_length
        if closer == "$":
            closing = _next_unescaped_dollar(source, body_start)
        else:
            found = source.find(closer, body_start)
            closing = found if found >= 0 else None
        if closing is None:
            break
        end = closing + len(closer)
        fragments.append(
            _MathFragment(
                start=index,
                end=end,
                body=source[body_start:closing],
                display=display,
            )
        )
        index = end
    return tuple(fragments)


def _raw_tex_source(block: dict[str, Any]) -> str | None:
    """Return a top-level TeX raw-block source, if ``block`` is one."""

    content = block.get("c")
    if (
        block.get("t") != "RawBlock"
        or not isinstance(content, list)
        or len(content) != 2
        or str(content[0]).casefold() not in {"latex", "tex"}
        or not isinstance(content[1], str)
    ):
        return None
    return content[1]


def _raw_tex_formal_block(block: dict[str, Any]) -> _RawTexFormalBlock | None:
    """Parse one allowlisted formal block without changing its TeX source."""

    source = _raw_tex_source(block)
    if source is None or (match := _SAFE_THEOREM_BLOCK_RE.fullmatch(source)) is None:
        return None
    title = match.group("title")
    label = match.group("label")
    return _RawTexFormalBlock(
        environment=match.group("environment"),
        title=title.strip() if title and title.strip() else None,
        label=label,
        body=match.group("body").strip(),
    )


def _raw_tex_is_nonvisible_declaration(block: dict[str, Any]) -> bool:
    """Return whether a safe TeX declaration has no projected slide content."""

    source = _raw_tex_source(block)
    return source is not None and _SAFE_PROPOSITION_DECLARATION_RE.fullmatch(source) is not None


def _plain_tex_text_to_html(source: str) -> str:
    """Escape the non-mathematical text subset admitted by the raw-TeX gate."""

    source = source.replace(r"\_", "_")
    source = source.replace(r"\%", "%")
    source = source.replace(r"\&", "&")
    source = source.replace(r"\#", "#")
    source = source.replace(r"\{", "{")
    source = source.replace(r"\}", "}")
    source = source.replace(r"\,", " ")
    source = source.replace(r"\ ", " ")
    source = source.replace("~", " ")
    return html.escape(re.sub(r"\s+", " ", source))


def _reference_html(label: str) -> str:
    """Emit a stable Reveal placeholder for strict AUX-backed resolution."""

    escaped_label = html.escape(label, quote=True)
    return (
        f'<span class="citation formal-reference" data-cites="{escaped_label}">'
        f"(<strong>{html.escape(label)}?</strong>)</span>"
    )


def _text_fragment_to_html(source: str) -> str:
    """Render allowlisted semantic text commands while escaping all source text."""

    fragments: list[str] = []
    cursor = 0
    for match in _TEXT_COMMAND_RE.finditer(source):
        fragments.append(_plain_tex_text_to_html(source[cursor : match.start()]))
        command = match.group("command")
        argument = match.group("argument")
        if command == "texttt":
            fragments.append(f"<code>{_plain_tex_text_to_html(argument)}</code>")
        elif command == "textbf":
            fragments.append(f"<strong>{_plain_tex_text_to_html(argument)}</strong>")
        elif command in {"textit", "emph"}:
            fragments.append(f"<em>{_plain_tex_text_to_html(argument)}</em>")
        elif command == "ref":
            fragments.append(_reference_html(argument))
        else:
            escaped_label = html.escape(argument, quote=True)
            fragments.append(f'<span id="{escaped_label}"></span>')
        cursor = match.end()
    fragments.append(_plain_tex_text_to_html(source[cursor:]))
    return "".join(fragments)


def _unsupported_plain_text(source: str) -> str | None:
    """Return the first construct unsafe across TeX and HTML text writers."""

    index = 0
    while index < len(source):
        character = source[index]
        if character == "\\":
            command_match = _RAW_TEX_COMMAND_RE.match(source, index)
            if command_match is None:
                return "trailing-backslash"
            command = command_match.group(1)
            if command not in _SAFE_TEXT_ESCAPES:
                return command
            index = command_match.end()
            continue
        if character in _UNESCAPED_TEXT_SPECIALS:
            return f"unescaped-text-special:{character}"
        index += 1
    return None


def _unsupported_text_fragment(source: str) -> str | None:
    """Validate text plus non-nested semantic text commands."""

    cursor = 0
    for match in _TEXT_COMMAND_RE.finditer(source):
        if (finding := _unsupported_plain_text(source[cursor : match.start()])) is not None:
            return finding
        if (finding := _unsupported_plain_text(match.group("argument"))) is not None:
            return finding
        cursor = match.end()
    return _unsupported_plain_text(source[cursor:])


def _unsupported_math_fragment(source: str) -> str | None:
    """Validate one already-delimited math fragment for both writers."""

    for matched_command in _RAW_TEX_COMMAND_RE.findall(source):
        command = str(matched_command)
        if command not in _SAFE_MATH_COMMANDS:
            return command
    return next(
        (f"unescaped-math-special:{character}" for character in source if character in _UNESCAPED_MATH_SPECIALS),
        None,
    )


def _unsupported_mixed_fragment(source: str) -> str | None:
    """Validate prose and explicitly delimited math without grammar migration."""

    cursor = 0
    for fragment in _math_fragments(source):
        if (finding := _unsupported_text_fragment(source[cursor : fragment.start])) is not None:
            return finding
        if (finding := _unsupported_math_fragment(fragment.body)) is not None:
            return finding
        cursor = fragment.end
    return _unsupported_text_fragment(source[cursor:])


def _tex_fragment_to_html(source: str) -> str:
    """Render mixed theorem prose and TeX math into a safe HTML fragment."""

    fragments: list[str] = []
    cursor = 0
    for fragment in _math_fragments(source):
        fragments.append(_text_fragment_to_html(source[cursor : fragment.start]))
        math = html.escape(fragment.body.strip())
        if fragment.display:
            fragments.append(f'<span class="math display">\\[{math}\\]</span>')
        else:
            fragments.append(f'<span class="math inline">\\({math}\\)</span>')
        cursor = fragment.end
    fragments.append(_text_fragment_to_html(source[cursor:]))
    return "".join(fragments).strip()


def _raw_tex_reveal_fallback(block: dict[str, Any]) -> dict[str, Any] | None:
    """Return an HTML-only formal block beside the untouched Beamer TeX node."""

    formal = _raw_tex_formal_block(block)
    if formal is None:
        return None
    attributes = [
        'class="formal-statement formal-' + formal.environment + '"',
        'data-formal-kind="' + formal.environment + '"',
    ]
    if formal.label is not None:
        attributes.append(f'id="{html.escape(formal.label, quote=True)}"')
    display_name = formal.environment.capitalize()
    heading = f"<strong>{display_name}</strong>"
    if formal.title is not None:
        heading += f' <span class="formal-statement-name">({_tex_fragment_to_html(formal.title)})</span>'
    paragraphs = [part for part in re.split(r"\n\s*\n", formal.body) if part.strip()]
    rendered_body = "".join(f"<p>{_tex_fragment_to_html(paragraph)}</p>" for paragraph in paragraphs)
    rendered = f'<div {" ".join(attributes)}><p class="formal-statement-label">{heading}</p>{rendered_body}</div>'
    return {"t": "RawBlock", "c": ["html", rendered]}


def _raw_tex_inline_reveal_fallback(inline: dict[str, Any]) -> dict[str, Any] | None:
    """Return the HTML peer for one allowlisted TeX reference inline."""

    content = inline.get("c")
    if (
        inline.get("t") != "RawInline"
        or not isinstance(content, list)
        or len(content) != 2
        or str(content[0]).casefold() not in {"latex", "tex"}
        or not isinstance(content[1], str)
        or (match := _SAFE_RAW_INLINE_RE.fullmatch(content[1])) is None
    ):
        return None
    return {"t": "RawInline", "c": ["html", _reference_html(match.group("label"))]}


def _unsupported_raw_tex_command(raw_source: str) -> str | None:
    """Return why a raw block is outside the explicit safe projection subset."""

    if _SAFE_PROPOSITION_DECLARATION_RE.fullmatch(raw_source) is not None:
        return None
    theorem_match = _SAFE_THEOREM_BLOCK_RE.fullmatch(raw_source)
    if theorem_match is None:
        commands = _RAW_TEX_COMMAND_RE.findall(raw_source)
        return next((command for command in commands if command not in {"begin", "end"}), "raw-block-shape")
    theorem_fragments = (
        theorem_match.group("title") or "",
        theorem_match.group("body"),
    )
    for fragment in theorem_fragments:
        finding = _unsupported_mixed_fragment(fragment)
        if finding in {"begin", "end"}:
            return "nested-environment"
        if finding is not None:
            return finding
    return None


def _first_unsupported_raw_tex(value: object) -> tuple[str, str] | None:
    if isinstance(value, list):
        return next(
            (finding for item in value if (finding := _first_unsupported_raw_tex(item)) is not None),
            None,
        )
    if not isinstance(value, dict):
        return None
    content = value.get("c")
    if value.get("t") in {"RawBlock", "RawInline"} and isinstance(content, list) and len(content) == 2:
        source_format, raw_source = content
        normalized_format = str(source_format).casefold()
        if normalized_format not in {"latex", "tex"}:
            return str(raw_source), f"raw-format:{normalized_format or '<empty>'}"
        if not isinstance(raw_source, str):
            return repr(raw_source), "raw-source-schema"
        if len(raw_source) > _MAX_RAW_TEX_CHARACTERS:
            return raw_source[:160] + "...", "raw-source-limit"
        # TeX expands every ``^^`` lexical-translation form before it tokenizes
        # commands.  A payload such as ``^^5cinput`` therefore contains no
        # backslash for the command allowlist to see, but becomes ``\input`` at
        # the Beamer writer. Reject the entire lexical mechanism before either
        # writer fallback is created; ordinary single-caret superscripts remain
        # admitted inside delimited mathematics.
        if "^^" in raw_source:
            return raw_source, "tex-lexical-translation"
        if value.get("t") == "RawInline":
            if _SAFE_RAW_INLINE_RE.fullmatch(raw_source) is not None:
                return None
            commands = _RAW_TEX_COMMAND_RE.findall(raw_source)
            return raw_source, next(iter(commands), "raw-inline-shape")
        unsupported = _unsupported_raw_tex_command(raw_source)
        if unsupported is not None:
            return raw_source, unsupported
    return _first_unsupported_raw_tex(content)


def _validate_raw_tex_geometry(value: object, *, source: str, heading: str) -> None:
    """Admit only raw content with safe geometry and both-writer semantics."""

    finding = _first_unsupported_raw_tex(value)
    if finding is None:
        return
    raw_source, command = finding
    raise density_error(
        "slides.density.unsupported-raw-geometry",
        "raw content is outside the explicit accessible projection allowlist",
        source=source,
        heading=heading,
        raw_source=raw_source,
        unsupported_command=command,
    )
