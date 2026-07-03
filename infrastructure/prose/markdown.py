"""Markdown front-matter / fence-stripping helpers.

Prose analysers operate on plain text. The functions here strip
front-matter (YAML/TOML) and fenced code blocks so the metrics reflect
prose, not embedded code or metadata.
"""

import re
from pathlib import Path

_FRONT_MATTER_RE = re.compile(r"^\s*---\s*\n.*?\n\s*---\s*\n", re.DOTALL)
_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^\)]+\)")
_MARKDOWN_HEADER_RE = re.compile(r"^#+\s*", re.MULTILINE)
# A leading ``# Abstract`` heading (optionally with a Pandoc ``{#id}`` attribute),
# optionally followed by a ``:``-separated subtitle that just restates the paper
# title (e.g. ``# Abstract: A Field Map of Entomological Law``). Matched before
# header markers are stripped so the redundant label can be dropped whole rather
# than surviving as bare body text (e.g. a Zenodo/GitHub deposit description
# opening with the literal word "Abstract:"). A colon is required for the
# subtitle case specifically so this stays narrow: ``# Abstract and Outlook``
# has no colon after "abstract" and is deliberately left untouched — "and"
# signals a compound heading covering real additional content, not a restated
# subtitle.
_LEADING_ABSTRACT_HEADING_RE = re.compile(
    r"\A\s*#{1,6}[ \t]+abstract(?:[ \t]*:[ \t]*[^\n{}]*)?[ \t]*(?:\{[^}]*\})?[ \t]*(?:\n+|\Z)",
    re.IGNORECASE,
)
_PANDOC_ATTR_RE = re.compile(r"\s*\{#[^}]+\}")
_PANDOC_CARET_ATTR_RE = re.compile(r"\s*\{\^[^}]+\}")
_CITATION_RE = re.compile(r"\[@([^\]]+)\]")
_HRULE_RE = re.compile(r"^\s*---+\s*$", re.MULTILINE)
_PANDOC_RAW_LATEX_ATTR_RE = re.compile(r"\{=latex\}")
_HYPERREF_VISIBLE_RE = re.compile(r"\\hyperref\[[^\]]*\]\{([^}]*)\}")
_WHITESPACE_RE = re.compile(r"[ \t]+\n")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")


def strip_front_matter(text: str) -> str:
    """Remove a leading YAML front-matter block, if any."""
    return _FRONT_MATTER_RE.sub("", text, count=1)


def strip_fences(text: str) -> str:
    """Remove fenced code blocks (``` ... ```)."""
    return _FENCE_RE.sub("", text)


def strip_inline_code(text: str) -> str:
    """Remove inline code spans (`...`)."""
    return _INLINE_CODE_RE.sub("", text)


def unwrap_inline_code(text: str) -> str:
    """Replace inline code spans with their inner text."""
    return _INLINE_CODE_RE.sub(r"\1", text)


def strip_links_to_text(text: str) -> str:
    """Replace ``[label](url)`` with ``label`` and drop ``![alt](url)``."""
    text = _IMAGE_RE.sub("", text)
    text = _LINK_RE.sub(r"\1", text)
    return text


def links_to_label_paren_url(text: str) -> str:
    """Replace ``[label](url)`` with ``label (url)`` and drop images."""
    text = _IMAGE_RE.sub("", text)

    def _replace(match: re.Match[str]) -> str:
        label = match.group(1).strip()
        url = match.group(2).strip()
        return f"{label} ({url})"

    return _LINK_RE.sub(_replace, text)


def strip_pandoc_attributes(text: str) -> str:
    """Remove Pandoc header/span attribute blocks such as ``{#id}`` or ``{^fn}``."""
    text = _PANDOC_ATTR_RE.sub("", text)
    return _PANDOC_CARET_ATTR_RE.sub("", text)


def strip_markdown_headers(text: str) -> str:
    """Remove ATX markdown header markers."""
    return _MARKDOWN_HEADER_RE.sub("", text)


def strip_leading_abstract_heading(text: str) -> str:
    """Drop a redundant leading ``# Abstract`` heading from deposit text.

    Manuscript abstracts open with a ``# Abstract`` heading, sometimes with a
    ``:``-separated subtitle that just restates the paper title (e.g.
    ``# Abstract: A Field Map of Entomological Law``). Deposit targets
    (Zenodo, GitHub releases) already label the field "Abstract", so the
    heading is redundant — and because :func:`strip_markdown_headers` keeps
    the header *text*, it would otherwise survive as the literal first word(s)
    of the description (``"Abstract: A Field Map...\\n\\nThis paper..."``).
    A standalone heading whose text is "Abstract" or "Abstract: <subtitle>" is
    removed; ``# Abstract and Outlook`` (a compound heading covering real
    additional content, not a restated subtitle) or an abstract body that
    genuinely begins with the word are left untouched.
    """
    return _LEADING_ABSTRACT_HEADING_RE.sub("", text, count=1)


def strip_emphasis_asterisk(text: str) -> str:
    """Remove ``*`` / ``**`` emphasis markers, keeping inner text."""

    def _replace(match: re.Match[str]) -> str:
        for group in match.groups():
            if group is not None:
                return group
        return match.group(0)

    return re.sub(r"\*\*([^*]+)\*\*|\*([^*]+)\*", _replace, text)


def strip_citations(text: str) -> str:
    """Remove Pandoc citation markers ``[@key]``."""
    return _CITATION_RE.sub("", text)


def strip_horizontal_rules(text: str) -> str:
    """Remove markdown horizontal rules (``---``) that are not deposit prose."""
    return _HRULE_RE.sub("", text)


def strip_raw_latex_inline(text: str) -> str:
    """Reduce Pandoc raw-LaTeX spans to their visible text for deposit metadata."""
    text = _PANDOC_RAW_LATEX_ATTR_RE.sub("", text)
    return _HYPERREF_VISIBLE_RE.sub(r"\1", text)


def collapse_whitespace(text: str) -> str:
    """Normalise trailing spaces and excessive blank lines."""
    text = _WHITESPACE_RE.sub("\n", text)
    return _MULTI_NEWLINE_RE.sub("\n\n", text).strip()


def normalise_for_deposit(text: str) -> str:
    """Convert manuscript markdown to plaintext suitable for Zenodo/GitHub deposits."""
    out = strip_front_matter(text)
    out = strip_fences(out)
    out = strip_leading_abstract_heading(out)
    out = strip_markdown_headers(out)
    out = strip_pandoc_attributes(out)
    out = unwrap_inline_code(out)
    out = strip_raw_latex_inline(out)
    out = links_to_label_paren_url(out)
    out = strip_emphasis_asterisk(out)
    out = strip_citations(out)
    out = strip_horizontal_rules(out)
    return collapse_whitespace(out)


def normalise_for_prose(text: str) -> str:
    """Apply all stripping passes in canonical order."""
    out = strip_front_matter(text)
    out = strip_fences(out)
    out = strip_inline_code(out)
    out = strip_links_to_text(out)
    return out


def read_manuscript_dir(
    manuscript_dir: Path | str,
    *,
    include: str = "*.md",
    exclude_filenames: tuple[str, ...] = (
        "preamble.md",
        "config.yaml.example",
        "AGENTS.md",
        "README.md",
        "SYNTAX.md",
    ),
) -> dict[str, str]:
    """Read every Markdown file in *manuscript_dir* into a ``{name: text}`` map.

    Files whose name appears in *exclude_filenames* are skipped (their
    content is documentation/scaffolding, not prose worth analysing).
    """
    base = Path(manuscript_dir)
    out: dict[str, str] = {}
    for path in sorted(base.glob(include)):
        if path.name in exclude_filenames:
            continue
        out[path.name] = path.read_text(encoding="utf-8")
    return out
