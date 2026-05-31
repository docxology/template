"""Data models for BibTeX-compatible citation entries.

These models mirror the syntax and semantics of the exemplar
``projects/templates/template_code_project/manuscript/references.bib`` file consumed by
``infrastructure/rendering/_pdf_combined_renderer.py`` via Pandoc's ``--natbib``
flag (with the ``pandoc-crossref`` filter handling ``[@fig:..]``/``[@tbl:..]``/
``[@eq:..]``/``[@sec:..]`` cross-references).

Design notes:

* :class:`BibEntry` is a thin, ordered, validated container for a single
  ``@type{key, ...}`` record. It does not interpret field semantics — that is
  the job of :mod:`infrastructure.reference.citation.bibtex_writer` (rendering)
  and :mod:`infrastructure.reference.citation.bibtex_parser` (parsing).
* Field order is preserved, because reproducible diffs against existing
  ``.bib`` files matter for academic projects.
* Keys are lowercase ASCII by BibTeX convention; the writer enforces this when
  emitting, but the model permits any non-empty string so that round-tripping
  hand-edited entries does not silently mutate them.
"""

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Mapping

# Canonical BibTeX entry types. Anything outside this set is permitted (the
# parser must accept it for round-tripping), but we expose the canonical set
# for callers that want to validate.
CANONICAL_ENTRY_TYPES: frozenset[str] = frozenset(
    {
        "article",
        "book",
        "booklet",
        "inbook",
        "incollection",
        "inproceedings",
        "conference",
        "manual",
        "mastersthesis",
        "phdthesis",
        "misc",
        "proceedings",
        "techreport",
        "unpublished",
        # Non-standard but widely used:
        "online",
        "software",
        "dataset",
        "preprint",
    }
)


@dataclass
class BibEntry:
    """A single BibTeX record.

    Attributes:
        entry_type: The BibTeX entry type (e.g. ``"article"``, ``"book"``).
        citation_key: The unique citation key (e.g. ``"nocedal2006numerical"``).
        fields: Ordered mapping of field name → field value. Values are stored
            as plain strings; LaTeX escaping is applied at render time.
        comment: Optional ``@comment{...}`` block emitted directly above the
            entry. Useful for preserving provenance notes.
    """

    entry_type: str
    citation_key: str
    fields: "OrderedDict[str, str]" = field(default_factory=OrderedDict)
    comment: str | None = None

    def __post_init__(self) -> None:
        if not self.entry_type or not self.entry_type.strip():
            raise ValueError("BibEntry.entry_type must be a non-empty string")
        if not self.citation_key or not self.citation_key.strip():
            raise ValueError("BibEntry.citation_key must be a non-empty string")
        # Normalise entry_type to lowercase to match BibTeX convention.
        self.entry_type = self.entry_type.strip().lower()
        self.citation_key = self.citation_key.strip()
        # Coerce arbitrary mappings into an OrderedDict to preserve order.
        if not isinstance(self.fields, OrderedDict):
            self.fields = OrderedDict(self.fields)

    def get(self, name: str, default: str | None = None) -> str | None:
        """Case-insensitive field lookup."""
        target = name.lower()
        for key, value in self.fields.items():
            if key.lower() == target:
                return value
        return default

    def set(self, name: str, value: str) -> None:
        """Set a field value, preserving the existing key casing if present."""
        target = name.lower()
        for key in list(self.fields.keys()):
            if key.lower() == target:
                self.fields[key] = value
                return
        self.fields[name] = value

    def has(self, name: str) -> bool:
        return self.get(name) is not None

    def keys(self) -> Iterator[str]:
        return iter(self.fields.keys())


@dataclass
class BibDatabase:
    """A collection of :class:`BibEntry` records preserving insertion order."""

    entries: list[BibEntry] = field(default_factory=list)
    preamble: str | None = None
    """Optional ``@comment{...}`` block emitted at the top of the file."""

    def add(self, entry: BibEntry) -> None:
        self.entries.append(entry)

    def extend(self, entries: Iterable[BibEntry]) -> None:
        for entry in entries:
            self.add(entry)

    def find(self, citation_key: str) -> BibEntry | None:
        for entry in self.entries:
            if entry.citation_key == citation_key:
                return entry
        return None

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self) -> Iterator[BibEntry]:
        return iter(self.entries)

    def keys(self) -> list[str]:
        return [entry.citation_key for entry in self.entries]

    def as_mapping(self) -> Mapping[str, BibEntry]:
        return {entry.citation_key: entry for entry in self.entries}
