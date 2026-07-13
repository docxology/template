"""Unified BibTeX export for the literature corpus.

Converts :class:`literature.models.Paper` records into BibTeX entries and
renders them to a single ``.bib``-formatted string. This module is a NEW,
standalone export path — it does not read from or write to the manuscript's
hand-maintained ``manuscript/references.bib`` (that file backs the
manuscript's own ``\\citep{}`` keys and must stay untouched).

Cross-boundary import note — SELF-CONTAINED BY NECESSITY.

This project's ``src/`` is a separate package root from the top-level
``infrastructure/`` package (``infrastructure/reference/citation/{models,
bibtex_writer,converter}.py``), which was the intended reuse target for
``BibEntry``/``render_entries``/``generate_citation_key``. That import does
NOT resolve under this project's own documented test invocation. Verified
directly:

* ``uv run python -c "import infrastructure"`` run from *inside*
  ``projects/templates/template_literature_meta_analysis/`` (this project's
  own uv-managed venv) fails with
  ``ModuleNotFoundError: No module named 'infrastructure'`` — the project's
  ``pyproject.toml`` declares no dependency on / path wiring to the repo-root
  ``infrastructure`` package.
* The bare documented test command,
  ``uv run pytest projects/templates/template_literature_meta_analysis/tests/literature/test_bibliography.py -q``
  (run from the repo root, using the repo-root ``uv`` environment), *also*
  fails the same way: pytest resolves this project's own
  ``projects/templates/template_literature_meta_analysis/pyproject.toml``
  (which declares ``[tool.pytest.ini_options] pythonpath = ["src"]``) as the
  effective rootdir/config *before* reaching the repo-root ``pyproject.toml``
  / ``conftest.py``, so the repo-root ``conftest.py``'s
  ``sys.path.insert(0, ROOT)`` never runs and ``infrastructure`` stays
  unimportable. This is a **pre-existing** condition, not one introduced
  here: the same failure reproduces today for the existing
  ``src/deep_research/deep_research_adapter.py``, which imports
  ``infrastructure.search.deep_research`` at module level — running
  ``uv run pytest projects/templates/template_literature_meta_analysis/tests/test_deep_research_adapter.py -q``
  from the repo root raises the identical
  ``ModuleNotFoundError: No module named 'infrastructure'``. (That module
  only becomes importable when the officially-wired test runner,
  ``infrastructure.core.pytest_orchestration.make_coverage_subprocess_env``,
  explicitly injects ``PYTHONPATH=<repo_root>`` into the pytest subprocess
  environment — a mechanism this project's plain, directly-invoked pytest
  command does not go through.)

Given that, this module inlines a small, self-contained citation-key
generator and BibTeX renderer with NO external dependency on
``infrastructure``. Only the *field-mapping* and *citation-key* CONVENTIONS
from ``infrastructure/reference/citation/converter.py`` /
``infrastructure/core/text_slug.py`` are reused as a style reference (same
``<surname><year><title-word>`` key shape, same field order, same
"url is redundant when doi is present" rule, same two-space-indented
``@type{key,\\n  field={value},\\n}`` BibTeX layout) — none of their code is
imported.
"""

from __future__ import annotations

import re
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass, field
from io import StringIO
from typing import Iterable, Iterator

from .corpus import Corpus
from .models import Paper

# ---------------------------------------------------------------------------
# Minimal, self-contained citation-key generation (style-mirrors
# infrastructure/core/text_slug.py + infrastructure/reference/citation/
# converter.py's generate_citation_key, without importing either).
# ---------------------------------------------------------------------------

_TITLE_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "nor",
        "of",
        "on",
        "in",
        "at",
        "to",
        "from",
        "for",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "as",
        "into",
        "via",
    }
)


def _slugify_token(text: str) -> str:
    """ASCII-fold *text* and strip non-alphanumerics. Lowercased."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", ascii_text.lower())


def _extract_surname(author: str) -> str:
    """Extract surname from ``Last, First`` or ``First Last`` author strings."""
    if not author:
        return ""
    if "," in author:
        return author.split(",", 1)[0].strip()
    parts = [part for part in re.split(r"\s+", author.strip()) if part]
    return parts[-1] if parts else ""


def _title_key_word(title: str) -> str:
    """Return the first non-stop-word slug from *title*."""
    if not title:
        return ""
    for raw in re.split(r"\s+", title.strip()):
        slug = _slugify_token(raw)
        if slug and slug not in _TITLE_STOP_WORDS:
            return slug
    return ""


def generate_citation_key(
    *,
    authors: list[str],
    year: int | str | None,
    title: str,
    fallback: str = "anon",
) -> str:
    """Build a citation key: ``<author_surname_slug><year><title_first_word>``.

    Falls back to *fallback* when there are no authors. Mirrors
    ``infrastructure.reference.citation.converter.generate_citation_key``
    exactly (same algorithm), reimplemented locally — see the module
    docstring for why the original could not be imported directly.
    """
    surname = _slugify_token(_extract_surname(authors[0])) if authors else ""
    year_str = str(year) if year is not None else ""
    title_word = _title_key_word(title)
    head = surname or fallback
    pieces = [piece for piece in (head, year_str, title_word) if piece]
    key = "".join(pieces) or fallback
    return key


def _disambiguate_key(base_key: str, used_keys: set[str]) -> str:
    """Return *base_key*, or a suffixed variant if it already exists in *used_keys*.

    Disambiguation appends "a", "b", "c", ... (then "26", "27", ... past the
    alphabet) until a unique key is found. The final key is added to
    *used_keys* before returning.
    """
    if base_key not in used_keys:
        used_keys.add(base_key)
        return base_key
    suffix_index = 0
    while True:
        suffix = chr(ord("a") + suffix_index) if suffix_index < 26 else str(suffix_index)
        candidate = f"{base_key}{suffix}"
        if candidate not in used_keys:
            used_keys.add(candidate)
            return candidate
        suffix_index += 1


# ---------------------------------------------------------------------------
# Minimal, self-contained BibEntry model + BibTeX renderer (style-mirrors
# infrastructure/reference/citation/{models,bibtex_writer}.py, without
# importing either).
# ---------------------------------------------------------------------------

# Canonical BibTeX entry types this module cares about. "preprint" is
# non-standard but widely used (also present in infrastructure's
# CANONICAL_ENTRY_TYPES set — verified by reading
# infrastructure/reference/citation/models.py directly, since it cannot be
# imported here).
_PREPRINT_ENTRY_TYPE = "preprint"

# Fields whose values are verbatim (not LaTeX-escaped): DOIs and URLs already
# have valid BibTeX syntax.
_VERBATIM_FIELDS: frozenset[str] = frozenset({"year", "doi", "url"})

_LATEX_SPECIALS: dict[str, str] = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _escape_latex(text: str) -> str:
    """Escape BibTeX/LaTeX special characters in *text*; unicode is preserved."""
    if not text:
        return text
    return "".join(_LATEX_SPECIALS.get(ch, ch) for ch in text)


@dataclass
class BibEntry:
    """A single, minimal BibTeX record (mirrors the shape of
    ``infrastructure.reference.citation.models.BibEntry`` without importing
    it — see the module docstring).

    Attributes:
        entry_type: The BibTeX entry type (e.g. ``"article"``, ``"preprint"``).
        citation_key: The unique citation key.
        fields: Ordered mapping of field name -> field value.
    """

    entry_type: str
    citation_key: str
    fields: "OrderedDict[str, str]" = field(default_factory=OrderedDict)

    def get(self, name: str, default: str | None = None) -> str | None:
        """Case-insensitive field lookup."""
        target = name.lower()
        for key, value in self.fields.items():
            if key.lower() == target:
                return value
        return default

    def has(self, name: str) -> bool:
        """Return True if a key is present."""
        return self.get(name) is not None

    def keys(self) -> Iterator[str]:
        """Return all field names."""
        return iter(self.fields.keys())


def render_entry(entry: BibEntry) -> str:
    """Render a single :class:`BibEntry` to a BibTeX string."""
    if not entry.fields:
        return f"@{entry.entry_type}{{{entry.citation_key}\n}}\n"

    buf = StringIO()
    buf.write(f"@{entry.entry_type}{{{entry.citation_key},\n")
    items = list(entry.fields.items())
    last_index = len(items) - 1
    for i, (name, raw_value) in enumerate(items):
        formatted = raw_value if name in _VERBATIM_FIELDS else _escape_latex(raw_value)
        suffix = "," if i < last_index else ""
        buf.write(f"  {name}={{{formatted}}}{suffix}\n")
    buf.write("}\n")
    return buf.getvalue()


def render_entries(entries: Iterable[BibEntry]) -> str:
    """Render an iterable of :class:`BibEntry` records, separated by a blank line."""
    entry_list = list(entries)
    buf = StringIO()
    for i, entry in enumerate(entry_list):
        buf.write(render_entry(entry))
        if i < len(entry_list) - 1:
            buf.write("\n")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Paper -> BibEntry mapping (the actual task-specific logic).
# ---------------------------------------------------------------------------


def paper_to_bibentry(paper: Paper, *, used_keys: set[str] | None = None) -> BibEntry:
    """Convert one :class:`Paper` into a :class:`BibEntry`.

    Args:
        paper: The paper to convert.
        used_keys: Optional shared set of citation keys already emitted in
            this export run. When given and the generated key collides with
            an existing entry, the key is disambiguated by appending
            "a", "b", "c", ... and the final key is added to the set.

    Returns:
        A populated :class:`BibEntry` with entry_type "preprint" for
        preprints (per ``Paper.is_preprint``), else "article".
    """
    entry_type = _PREPRINT_ENTRY_TYPE if paper.is_preprint else "article"

    base_key = generate_citation_key(
        authors=[a.name for a in paper.authors],
        year=paper.year,
        title=paper.title,
    )
    citation_key = _disambiguate_key(base_key, used_keys) if used_keys is not None else base_key

    fields: "OrderedDict[str, str]" = OrderedDict()
    if paper.title:
        fields["title"] = paper.title
    if paper.authors:
        author_str = " and ".join(a.name.strip() for a in paper.authors if a.name and a.name.strip())
        if author_str:
            fields["author"] = author_str
    if paper.venue:
        fields["journal"] = paper.venue
    if paper.year is not None:
        fields["year"] = str(paper.year)
    if paper.doi:
        fields["doi"] = paper.doi
    if paper.pdf_url and not paper.doi:
        # DOI, when present, is redundant with the URL — mirrors the
        # convention in infrastructure/reference/citation/converter.py.
        fields["url"] = paper.pdf_url
    if paper.abstract:
        fields["abstract"] = paper.abstract

    return BibEntry(entry_type=entry_type, citation_key=citation_key, fields=fields)


def corpus_to_bibtex(corpus: Corpus) -> str:
    """Render an entire :class:`Corpus` to a single BibTeX string.

    Papers are visited in stable ``canonical_id`` order for deterministic
    output. Citation keys are disambiguated against a single shared set
    across the whole corpus. An empty corpus returns an empty string.
    """
    used_keys: set[str] = set()
    entries: list[BibEntry] = [
        paper_to_bibentry(paper, used_keys=used_keys) for paper in sorted(corpus.papers, key=lambda p: p.canonical_id)
    ]
    return render_entries(entries)
