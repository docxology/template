"""Readable cross-reference and math integrity for accessible Reveal decks."""

from __future__ import annotations

import html
import re
from collections.abc import Mapping

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._web_postprocess import (
    MATHJAX_URL,
    _MATHJAX_CONFIG_SCRIPT,
    _MATHJAX_INTEGRITY,
)


ACCESSIBLE_REVEAL_VERSION = "5.2.1"
ACCESSIBLE_REVEAL_URL = f"https://unpkg.com/reveal.js@{ACCESSIBLE_REVEAL_VERSION}"
_REFERENCE_KINDS = {
    "alg": "Algorithm",
    "cor": "Corollary",
    "def": "Definition",
    "eq": "Equation",
    "ex": "Example",
    "fig": "Figure",
    "lem": "Lemma",
    "lst": "Listing",
    "prop": "Proposition",
    "rem": "Remark",
    "sec": "Section",
    "subsec": "Section",
    "tbl": "Table",
    "thm": "Theorem",
}
_REFERENCE_PREFIXES = "|".join(re.escape(prefix) for prefix in _REFERENCE_KINDS)
_CITATION_SPAN_RE = re.compile(
    r"(?P<nbsp>~)?(?P<authored_open>\()?"
    r"<span\b(?P<attrs>(?=[^>]*\bclass\s*=\s*[\"'][^\"']*\bcitation\b[^\"']*[\"'])"
    r"(?=[^>]*\bdata-cites\s*=\s*[\"'][^\"']+[\"'])[^>]*)>(?P<body>.*?)</span>",
    flags=re.IGNORECASE | re.DOTALL,
)
_DATA_CITES_RE = re.compile(r"\bdata-cites\s*=\s*[\"'](?P<cites>[^\"']+)[\"']", flags=re.IGNORECASE)
_HTML_ID_RE = re.compile(r"\bid\s*=\s*[\"'](?P<id>[^\"']+)[\"']", flags=re.IGNORECASE)
_DISPLAY_MATH_RE = re.compile(
    r"<span\b(?P<attrs>(?=[^>]*\bclass\s*=\s*[\"'][^\"']*\bmath\b[^\"']*\bdisplay\b[^\"']*[\"'])"
    r"[^>]*)>(?P<body>.*?)</span>",
    flags=re.IGNORECASE | re.DOTALL,
)
_DISPLAY_MATH_LABEL_RE = re.compile(
    r"(?P<open><span\b(?P<attrs>(?=[^>]*\bclass\s*=\s*[\"'][^\"']*\bmath\b[^\"']*\bdisplay\b[^\"']*[\"'])"
    r"[^>]*)>)(?P<body>.*?)</span>\s*\{#(?P<label>[A-Za-z][A-Za-z0-9_-]*:[A-Za-z0-9_.:-]+)\}",
    flags=re.IGNORECASE | re.DOTALL,
)
_INLINE_MATH_REFERENCE_RE = re.compile(
    r"(?P<nbsp>~)?"
    r"(?P<authored_open>\()?"
    r"<span\b(?P<attrs>(?=[^>]*\bclass\s*=\s*[\"'][^\"']*\bmath\b[^\"']*\binline\b[^\"']*[\"'])"
    r"[^>]*)>\s*\\\(\s*\\(?P<command>eqref|ref)\{"
    r"(?P<label>[A-Za-z][A-Za-z0-9_-]*:[A-Za-z0-9_.:-]+)\}\s*\\\)\s*</span>",
    flags=re.IGNORECASE | re.DOTALL,
)
_VISIBLE_REFERENCE_PLACEHOLDER_RE = re.compile(
    rf"(?:<strong>\s*)?(?:{_REFERENCE_PREFIXES}):[A-Za-z0-9_.:-]+\?(?:\s*</strong>)?",
    flags=re.IGNORECASE,
)
_VISIBLE_LABEL_SUFFIX_RE = re.compile(
    rf"\{{#(?:{_REFERENCE_PREFIXES}):[A-Za-z0-9_.:-]+\}}",
    flags=re.IGNORECASE,
)
_RAW_TEX_REFERENCE_RE = re.compile(
    r"\\(?:ref|eqref|autoref|cref|Cref|pageref|nameref|subref)\{[^{}]+\}",
)
_SCRIPT_OR_STYLE_RE = re.compile(r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>", flags=re.IGNORECASE | re.DOTALL)
_CODE_OR_PRE_RE = re.compile(
    r"<(?P<tag>pre|code)\b[^>]*>.*?</(?P=tag)>",
    flags=re.IGNORECASE | re.DOTALL,
)
_MATHJAX_ANY_SCRIPT_RE = re.compile(
    r"<script\b(?=[^>]*\bsrc\s*=\s*[\"']" + re.escape(MATHJAX_URL) + r"(?:[?#][^\"']*)?[\"'])[^>]*>.*?</script>",
    flags=re.IGNORECASE | re.DOTALL,
)
_MATHJAX_SCRIPT_RE = re.compile(
    r"<script\b(?=[^>]*\bsrc\s*=\s*[\"']"
    + re.escape(MATHJAX_URL)
    + r"[\"'])(?=[^>]*\bintegrity\s*=\s*[\"']"
    + re.escape(_MATHJAX_INTEGRITY)
    + r"[\"'])"
    r"(?=[^>]*\bcrossorigin\s*=\s*[\"']anonymous[\"'])[^>]*>\s*</script>",
    flags=re.IGNORECASE | re.DOTALL,
)
_REVEAL_MATH_PLUGIN_RE = re.compile(
    r"<script\b[^>]*\bsrc\s*=\s*[\"']"
    + re.escape(f"{ACCESSIBLE_REVEAL_URL}/plugin/math/math.js")
    + r"[\"'][^>]*></script>",
    flags=re.IGNORECASE,
)
_REVEAL_MATH_CONFIG_RE = re.compile(
    r"\bmathjax\s*:\s*[\"']" + re.escape(MATHJAX_URL) + r"[\"']",
    flags=re.IGNORECASE,
)
_REVEAL_MATH_INITIALIZER_RE = re.compile(
    r"\bplugins\s*:\s*\[[^\]]*\bRevealMath\b[^\]]*\]",
    flags=re.IGNORECASE | re.DOTALL,
)
_REVEAL_MATH_CONFIG_BLOCK_RE = re.compile(
    r"\n\s*math\s*:\s*\{.*?\n\s*\},\s*\n\s*// reveal\.js plugins",
    flags=re.IGNORECASE | re.DOTALL,
)
_REVEAL_MATH_PLUGIN_ENTRY_RE = re.compile(r"^\s*RevealMath,\s*$", flags=re.IGNORECASE | re.MULTILINE)
_REVEAL_MATH_PLUGIN_TAG_PATTERN = (
    r"<script\b[^>]*\bsrc\s*=\s*[\"'][^\"']*/plugin/math/math\.js(?:[^\"']*)?[\"'][^>]*></script>"
)
_ANY_REVEAL_MATH_PLUGIN_RE = re.compile(
    _REVEAL_MATH_PLUGIN_TAG_PATTERN,
    flags=re.IGNORECASE,
)
_STANDALONE_REVEAL_MATH_PLUGIN_RE = re.compile(
    r"^[ \t]*" + _REVEAL_MATH_PLUGIN_TAG_PATTERN + r"[ \t]*(?:\r?\n|$)",
    flags=re.IGNORECASE | re.MULTILINE,
)


def activate_hardened_reveal_mathjax(content: str) -> str:
    """Replace Pandoc's legacy RevealMath2 loader with the shared SRI path.

    Pandoc's Reveal template activates the legacy ``RevealMath`` alias, whose
    plugin appends a MathJax-2 ``?config=...`` query even when given the
    project's MathJax-4 URL. Accessible mode keeps Pandoc's MathJax-formatted
    ``\\[...\\]`` output but loads the pinned shared runtime directly with the
    same SRI/configuration boundary used by the canonical HTML manuscript.
    """

    if MATHJAX_URL not in content:
        return content
    # Pandoc indents plugin tags on otherwise empty physical lines.  Consume
    # the whole line before the general inline replacement so the removed
    # legacy loader cannot leave a whitespace-only line in committed decks.
    content = _STANDALONE_REVEAL_MATH_PLUGIN_RE.sub("", content)
    content = _ANY_REVEAL_MATH_PLUGIN_RE.sub("", content)
    content = _REVEAL_MATH_PLUGIN_ENTRY_RE.sub("", content)
    content = _REVEAL_MATH_CONFIG_BLOCK_RE.sub("\n\n        // reveal.js plugins", content, count=1)
    # Normalize every pre-existing direct loader to one canonical tag. The
    # shared hardener adds the exact SRI digest and configuration after this
    # transform; retaining even a second unpinned loader would execute the
    # same remote dependency outside that integrity boundary.
    content = _MATHJAX_ANY_SCRIPT_RE.sub("", content)
    loader = f'<script src="{html.escape(MATHJAX_URL, quote=True)}"></script>'
    content = content.replace("</head>", f"{loader}\n</head>", 1)
    return content


def _set_attribute(tag: str, name: str, value: str) -> str:
    """Set one escaped HTML attribute without changing unrelated attributes."""

    escaped = html.escape(value, quote=True)
    pattern = re.compile(
        rf"(?<!\S){re.escape(name)}\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
        flags=re.IGNORECASE,
    )
    if pattern.search(tag):
        return pattern.sub(lambda _match: f'{name}="{escaped}"', tag, count=1)
    return tag[:-1].rstrip() + f' {name}="{escaped}">' if tag.endswith(">") else tag


def promote_display_math_labels(content: str) -> str:
    """Attach source equation labels to their display spans instead of printing them."""

    def _replace(match: re.Match[str]) -> str:
        opening = _set_attribute(match.group("open"), "id", match.group("label"))
        return f"{opening}{match.group('body')}</span>"

    return _DISPLAY_MATH_LABEL_RE.sub(_replace, content)


def _reference_markup(
    label: str,
    number: str | None,
    local_ids: set[str],
    *,
    include_kind: bool = True,
    equation_parentheses: bool = True,
) -> str:
    """Return one readable, non-placeholder reference."""

    prefix, _, identifier = label.partition(":")
    kind = _REFERENCE_KINDS[prefix.casefold()]
    if number is not None:
        if include_kind:
            visible = f"{kind} ({number})" if prefix.casefold() == "eq" and equation_parentheses else f"{kind} {number}"
        else:
            visible = f"({number})" if prefix.casefold() == "eq" and equation_parentheses else number
        if label in local_ids:
            return (
                '<a class="cross-reference" href="#'
                + html.escape(label, quote=True)
                + '">'
                + html.escape(visible)
                + "</a>"
            )
        return f'<span class="cross-reference">{html.escape(visible)}</span>'

    readable = " ".join(part for part in re.split(r"[-_.]+", identifier) if part)
    visible = f"{readable} {kind.casefold()}" if include_kind and readable else readable or kind
    return f'<span class="cross-reference cross-reference-fallback">{html.escape(visible)}</span>'


def _preceded_by_reference_kind(content: str, start: int, kind: str) -> bool:
    """Return whether visible prose immediately before a citation names its kind."""

    fragment = content[max(0, start - 256) : start]
    visible = re.sub(r"<[^>]+>", "", fragment)
    visible = " ".join(html.unescape(visible).split())
    return re.search(r"\b" + re.escape(kind) + r"\s*$", visible, flags=re.IGNORECASE) is not None


def resolve_reveal_cross_references(
    content: str,
    label_numbers: Mapping[str, str] | None = None,
    *,
    strict: bool = False,
) -> str:
    """Replace Pandoc/citeproc's missing-label HTML with readable references.

    Canonical strict rendering requires every cross-reference to be present in
    the retained combined-manuscript AUX map. Standalone accessible renders
    remain useful before that map exists by emitting a deterministic readable
    fallback; neither path exposes citeproc's ``label?`` placeholder.
    """

    numbers = dict(label_numbers or {})
    local_ids = {match.group("id") for match in _HTML_ID_RE.finditer(content)}
    unresolved: set[str] = set()
    unrendered: set[str] = set()

    def _replace(match: re.Match[str]) -> str:
        cites_match = _DATA_CITES_RE.search(match.group("attrs"))
        if cites_match is None:
            return match.group(0)
        identifiers = cites_match.group("cites").split()
        references = [
            identifier for identifier in identifiers if identifier.partition(":")[0].casefold() in _REFERENCE_KINDS
        ]
        if not references:
            return match.group(0)
        join = "\N{NO-BREAK SPACE}" if match.group("nbsp") else ""
        authored_open = match.group("authored_open") or ""
        after = content[match.end() :].lstrip()
        authored_parentheses = bool(authored_open and after.startswith(")"))
        all_equations = all(identifier.partition(":")[0].casefold() == "eq" for identifier in references)
        missing = [identifier for identifier in references if identifier not in numbers]
        unresolved.update(missing)
        rendered: dict[str, str] = {}
        for index, identifier in enumerate(references):
            prefix = identifier.partition(":")[0].casefold()
            include_kind = not (
                (prefix == "eq" and authored_parentheses and all_equations)
                or (index == 0 and _preceded_by_reference_kind(content, match.start(), _REFERENCE_KINDS[prefix]))
            )
            rendered[identifier] = _reference_markup(
                identifier,
                numbers.get(identifier),
                local_ids,
                include_kind=include_kind,
                equation_parentheses=not authored_parentheses,
            )
        if len(references) == len(identifiers):
            return join + authored_open + "; ".join(rendered[identifier] for identifier in references)

        # Preserve resolved bibliographic citations in a mixed span while
        # replacing either citeproc's strong-tagged placeholder or Pandoc's
        # raw ``@label`` token. The latter occurs when a standalone source has
        # no bibliography/citeproc pass. Remove resolved cross-reference keys
        # from ``data-cites`` so output validation can fail closed on any key
        # that did not receive readable markup.
        body = match.group("body")
        for identifier, replacement in rendered.items():
            placeholder = re.compile(
                r"(?:\(\s*<strong>\s*"
                + re.escape(identifier)
                + r"\?\s*</strong>\s*\)|<strong>\s*"
                + re.escape(identifier)
                + r"\?\s*</strong>)",
                flags=re.IGNORECASE,
            )
            body, placeholder_count = placeholder.subn(replacement, body)
            raw_token = re.compile(
                r"(?<![A-Za-z0-9_.:-])@" + re.escape(identifier) + r"(?![A-Za-z0-9_.:-])",
                flags=re.IGNORECASE,
            )
            body, raw_count = raw_token.subn(replacement, body)
            raw_question = re.compile(
                r"(?<![A-Za-z0-9_.:-])" + re.escape(identifier) + r"\?(?![A-Za-z0-9_.:-])",
                flags=re.IGNORECASE,
            )
            body, question_count = raw_question.subn(replacement, body)
            if placeholder_count + raw_count + question_count == 0:
                unrendered.add(identifier)

        attributes = match.group("attrs")
        if not any(identifier in unrendered for identifier in references):
            bibliographic = [identifier for identifier in identifiers if identifier not in references]
            escaped_cites = html.escape(" ".join(bibliographic), quote=True)
            attributes = _DATA_CITES_RE.sub(f'data-cites="{escaped_cites}"', attributes, count=1)
        return join + authored_open + f"<span{attributes}>{body}</span>"

    resolved = _CITATION_SPAN_RE.sub(_replace, content)
    inline_source = resolved

    def _replace_inline_math_reference(match: re.Match[str]) -> str:
        label = match.group("label")
        prefix = label.partition(":")[0].casefold()
        if prefix not in _REFERENCE_KINDS:
            unrendered.add(label)
            return match.group(0)
        number = numbers.get(label)
        if number is None:
            unresolved.add(label)
        after = inline_source[match.end() :].lstrip()
        authored_open = match.group("authored_open") or ""
        equation_has_authored_parentheses = prefix == "eq" and bool(authored_open and after.startswith(")"))
        include_kind = not (
            equation_has_authored_parentheses
            or _preceded_by_reference_kind(
                inline_source,
                match.start(),
                _REFERENCE_KINDS[prefix],
            )
        )
        replacement = _reference_markup(
            label,
            number,
            local_ids,
            include_kind=include_kind,
            equation_parentheses=(
                match.group("command").casefold() == "eqref" and not equation_has_authored_parentheses
            ),
        )
        # A prose ``~`` immediately joining a reference is LaTeX's
        # nonbreaking-space notation, not content to expose in the browser.
        join = "\N{NO-BREAK SPACE}" if match.group("nbsp") else ""
        return join + authored_open + replacement

    resolved = _INLINE_MATH_REFERENCE_RE.sub(_replace_inline_math_reference, inline_source)
    if strict and (unresolved or unrendered):
        raise RenderingError(
            "[slides.crossref.reveal-unresolved] Accessible Reveal cannot resolve references from the current AUX",
            context={
                "diagnostic_code": "slides.crossref.reveal-unresolved",
                "unresolved_labels": sorted(unresolved | unrendered),
            },
        )
    return resolved


def reveal_reference_and_math_issues(content: str) -> tuple[str, ...]:
    """Return visible placeholder and unrendered-display-math defects."""

    issues: list[str] = []
    visible = _SCRIPT_OR_STYLE_RE.sub("", content)
    # Literal TeX examples inside projected code are teaching content, not
    # unresolved navigation. The prose/math surface remains fail-closed.
    visible = _CODE_OR_PRE_RE.sub("", visible)
    if _VISIBLE_REFERENCE_PLACEHOLDER_RE.search(visible):
        issues.append("Reveal deck contains an unresolved cross-reference placeholder")
    if _VISIBLE_LABEL_SUFFIX_RE.search(visible):
        issues.append("Reveal deck exposes a source cross-reference label")
    if _RAW_TEX_REFERENCE_RE.search(visible):
        issues.append("Reveal deck contains a raw TeX cross-reference command")
    for match in _CITATION_SPAN_RE.finditer(visible):
        cites_match = _DATA_CITES_RE.search(match.group("attrs"))
        if cites_match is None:
            continue
        if any(
            identifier.partition(":")[0].casefold() in _REFERENCE_KINDS
            for identifier in cites_match.group("cites").split()
        ):
            issues.append("Reveal deck retains an unresolved cross-reference citation")
            break

    direct_loaders = list(_MATHJAX_ANY_SCRIPT_RE.finditer(content))
    exact_loader_attributes = bool(
        len(direct_loaders) == 1
        and all(
            len(re.findall(r"\b" + attribute + r"\s*=", direct_loaders[0].group(0), flags=re.IGNORECASE)) == 1
            for attribute in ("src", "integrity", "crossorigin")
        )
    )
    canonical_config_count = content.count(_MATHJAX_CONFIG_SCRIPT)
    config_precedes_loader = bool(
        direct_loaders
        and canonical_config_count == 1
        and content.index(_MATHJAX_CONFIG_SCRIPT) < direct_loaders[0].start()
    )
    direct_hardened_mathjax = (
        len(direct_loaders) == 1
        and _MATHJAX_SCRIPT_RE.search(content) is not None
        and exact_loader_attributes
        and content.count("data-template-mathjax-config") == 1
        and canonical_config_count == 1
        and config_precedes_loader
    )
    legacy_reveal_math = (
        _ANY_REVEAL_MATH_PLUGIN_RE.search(content) is not None
        or _REVEAL_MATH_INITIALIZER_RE.search(content) is not None
        or _REVEAL_MATH_CONFIG_RE.search(content) is not None
    )
    executable_math_backend = direct_hardened_mathjax and not legacy_reveal_math
    if MATHJAX_URL in content:
        if len(direct_loaders) != 1:
            issues.append("Reveal deck must contain exactly one pinned MathJax loader")
        if len(direct_loaders) == 1 and (_MATHJAX_SCRIPT_RE.search(content) is None or not exact_loader_attributes):
            issues.append("Reveal MathJax loader does not use the exact pinned SRI and crossorigin attributes")
        if (
            content.count("data-template-mathjax-config") != 1
            or canonical_config_count != 1
            or not config_precedes_loader
        ):
            issues.append("Reveal deck must contain one canonical MathJax configuration before its loader")
    if legacy_reveal_math:
        issues.append("Reveal deck retains a competing legacy RevealMath loader or configuration")

    display_spans = list(_DISPLAY_MATH_RE.finditer(visible))
    for match in display_spans:
        body = html.unescape(match.group("body"))
        if "$$" in body:
            issues.append("Reveal display math retains literal $$ delimiters")
            break
    tex_display = any(
        re.search(
            r"\\begin\{(?:aligned|align\*?|equation\*?|gather\*?|multline\*?)\}|\\\[",
            html.unescape(match.group("body")),
        )
        for match in display_spans
    )
    if tex_display and not executable_math_backend:
        issues.append("Reveal display math contains an unrendered TeX environment without an executable math backend")

    without_display_spans = _DISPLAY_MATH_RE.sub("", visible)
    if re.search(r"\\begin\{(?:aligned|align\*?|equation\*?|gather\*?|multline\*?)\}", without_display_spans):
        issues.append("Reveal deck contains a TeX display environment outside a math span")
    return tuple(dict.fromkeys(issues))


__all__ = [
    "ACCESSIBLE_REVEAL_URL",
    "ACCESSIBLE_REVEAL_VERSION",
    "activate_hardened_reveal_mathjax",
    "promote_display_math_labels",
    "resolve_reveal_cross_references",
    "reveal_reference_and_math_issues",
]
