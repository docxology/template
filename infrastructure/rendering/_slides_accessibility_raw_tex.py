"""Fail-closed raw-TeX admission for the accessible slide profile."""

from __future__ import annotations

import re

from infrastructure.rendering._slides_accessibility_contracts import density_error


_RAW_TEX_COMMAND_RE = re.compile(r"\\([A-Za-z@]+|.)")
_SAFE_THEOREM_BLOCK_RE = re.compile(
    r"\A\s*\\begin\{(?P<environment>definition|lemma|proposition|theorem|corollary|hypothesis|proof|remark)\}"
    r"(?:\[[^\]\r\n]*\])?\s*"
    r"(?:\\label\{[-:._A-Za-z0-9]+\})?"
    r"(?P<body>.*?)"
    r"\\end\{(?P=environment)\}\s*\Z",
    re.DOTALL,
)
_SAFE_PROPOSITION_DECLARATION_RE = re.compile(
    r"\A\s*\\ifcsname\s+proposition\\endcsname\s*"
    r"\\else\s*\\newtheorem\{proposition\}\{Proposition\}\s*\\fi\s*\Z"
)
_SAFE_RAW_INLINE_RE = re.compile(r"\A\s*\\ref\{[-:._A-Za-z0-9]+\}\s*\Z")
_SAFE_THEOREM_COMMANDS = frozenset(
    {
        "(",
        ")",
        ",",
        "_",
        "{",
        "}",
        "|",
        "alpha",
        "ast",
        "begin",
        "beta",
        "boldsymbol",
        "cite",
        "emph",
        "end",
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


def _unsupported_raw_tex_command(raw_source: str) -> str | None:
    """Return why a raw block is outside the explicit safe projection subset."""

    if _SAFE_PROPOSITION_DECLARATION_RE.fullmatch(raw_source) is not None:
        return None
    theorem_match = _SAFE_THEOREM_BLOCK_RE.fullmatch(raw_source)
    if theorem_match is None:
        commands = _RAW_TEX_COMMAND_RE.findall(raw_source)
        return next((command for command in commands if command not in _SAFE_THEOREM_COMMANDS), "raw-block-shape")
    if re.search(r"\\(?:begin|end)\{", theorem_match.group("body")):
        return "nested-environment"
    return next(
        (command for command in _RAW_TEX_COMMAND_RE.findall(raw_source) if command not in _SAFE_THEOREM_COMMANDS),
        None,
    )


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
        if str(source_format).casefold() in {"latex", "tex"} and isinstance(raw_source, str):
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
    """Admit only declared theorem blocks whose commands have modeled geometry."""

    finding = _first_unsupported_raw_tex(value)
    if finding is None:
        return
    raw_source, command = finding
    raise density_error(
        "slides.density.unsupported-raw-geometry",
        "raw TeX is outside the explicit accessible projection allowlist",
        source=source,
        heading=heading,
        raw_source=raw_source,
        unsupported_command=command,
    )
