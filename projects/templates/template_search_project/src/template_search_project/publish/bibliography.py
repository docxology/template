"""Project-owned projection of generated citations beside curated references.

The full search database belongs in output/bibliography. Rendering receives only
new entries, because every renderer requires citation keys to be unique across
its bibliography union. Curated annotations remain authored source material.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from infrastructure.core.files.secure_write import (
    atomic_write_text_confined,
    read_bytes_confined,
)
from infrastructure.reference.citation import BibDatabase, BibEntry, parse_bibtex, render_database

GENERATED_BIB_NAME = "generated_search.bib"
GENERATED_SUPPLEMENT_NAME = "S02_generated_literature_review.md"


def generated_path(project_root: Path, configured_path: str) -> Path:
    """Require generated bibliographies to remain under the project's output."""
    root = project_root.absolute()
    path = Path(configured_path)
    candidate = path.absolute() if path.is_absolute() else root / path
    try:
        relative = candidate.relative_to(root / "output")
    except ValueError as exc:
        raise ValueError("Generated bibliography must be under project output/") from exc
    if not relative.parts or ".." in relative.parts or candidate.suffix != ".bib":
        raise ValueError("Generated bibliography must name an output .bib file without traversal")
    return candidate


def _normalise(field: str, value: str) -> str:
    if field == "url":
        # URL paths and queries may be case-sensitive even when the host is not.
        parts = urlsplit(" ".join(value.split()))
        return urlunsplit((parts.scheme.casefold(), parts.netloc.casefold(), parts.path, parts.query, parts.fragment))
    text = " ".join(value.replace("{", "").replace("}", "").split()).casefold()
    if field == "author":
        names = []
        for name in text.split(" and "):
            if "," in name:
                last, first = name.split(",", 1)
                name = f"{first.strip()} {last.strip()}"
            names.append(" ".join(name.replace(".", "").split()))
        return " and ".join(names)
    if field == "doi":
        return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", text)
    if field == "pages":
        return re.sub(r"[-–—]+", "--", text)
    return text


def _assert_same_work(existing: BibEntry, generated: BibEntry) -> None:
    """Compare bibliographic identity while preserving curated extra annotations."""
    fields = (
        "title",
        "author",
        "year",
        "doi",
        "url",
        "journal",
        "booktitle",
        "volume",
        "number",
        "pages",
        "publisher",
        "edition",
        "isbn",
    )
    differences = []
    if existing.citation_key != generated.citation_key:
        differences.append("citation-key casing")
    if existing.entry_type != generated.entry_type:
        differences.append("entry type")
    for field in fields:
        left, right = existing.get(field), generated.get(field)
        # Abstracts and keywords are annotations, not work identity. Missing
        # optional locators may be supplied by enrichment without contradicting
        # an existing entry. Identity fields must agree when either is present.
        compare = field in {"title", "author", "year"} or (left is not None and right is not None)
        if compare and _normalise(field, left or "") != _normalise(field, right or ""):
            differences.append(field)
    if differences:
        raise ValueError(
            f"Bibliography collision for {generated.citation_key!r}: conflicting " + ", ".join(differences)
        )


def _curated(project_root: Path) -> tuple[dict[str, BibEntry], dict[Path, bytes]]:
    snapshot: dict[Path, bytes] = {}
    entries: dict[str, BibEntry] = {}
    for path in sorted((project_root / "manuscript").glob("*.bib")):
        if path.name == GENERATED_BIB_NAME:
            raise ValueError(f"Authored bibliography uses reserved generated name: {path.name}")
        raw = read_bytes_confined(project_root, path)
        snapshot[path] = raw
        for entry in parse_bibtex(raw.decode("utf-8")):
            key = entry.citation_key.casefold()
            if key in entries:
                raise ValueError(f"Duplicate curated bibliography key: {entry.citation_key}")
            entries[key] = entry
    return entries, snapshot


def _unchanged(root: Path, snapshot: dict[Path, bytes]) -> None:
    if set((root / "manuscript").glob("*.bib")) != set(snapshot):
        raise ValueError("Authored bibliography file set changed during projection")
    for path, raw in snapshot.items():
        if read_bytes_confined(root, path) != raw:
            raise ValueError("Authored bibliography changed during projection")


def write_generated_bibliography(root: Path, configured_path: str, database: BibDatabase) -> Path:
    """Validate collisions, then atomically write output without authoring edits."""
    root = root.absolute()
    target = generated_path(root, configured_path)
    curated, snapshot = _curated(root)
    seen: set[str] = set()
    for entry in database:
        key = entry.citation_key.casefold()
        if key in seen:
            raise ValueError(f"Duplicate generated bibliography key: {entry.citation_key}")
        seen.add(key)
        if key in curated:
            _assert_same_work(curated[key], entry)
    atomic_write_text_confined(root, target, render_database(database))
    _unchanged(root, snapshot)
    return target


def project_bibliographies(
    root: Path,
    configured_paths: tuple[str, ...],
    *,
    admitted_sources: dict[Path, bytes] | None = None,
) -> Path:
    """Hydrate the renderer's additional database and its exact-byte custody record."""
    root = root.absolute()
    curated, snapshot = _curated(root)
    selected = dict(curated)
    projected = BibDatabase()
    sources: dict[str, str] = {}
    generated_snapshot: dict[Path, bytes] = {}
    origins: dict[str, list[str]] = {}
    for configured_path in configured_paths:
        path = generated_path(root, configured_path)
        if not path.exists():
            continue
        raw = (
            admitted_sources[path]
            if admitted_sources is not None and path in admitted_sources
            else read_bytes_confined(root, path)
        )
        generated_snapshot[path] = raw
        relative = path.relative_to(root).as_posix()
        sources[relative] = hashlib.sha256(raw).hexdigest()
        local_keys: set[str] = set()
        for entry in parse_bibtex(raw.decode("utf-8")):
            key = entry.citation_key.casefold()
            if key in local_keys:
                raise ValueError(f"Duplicate generated bibliography key: {entry.citation_key}")
            local_keys.add(key)
            origins.setdefault(entry.citation_key, []).append(relative)
            if key in selected:
                _assert_same_work(selected[key], entry)
            else:
                selected[key] = entry
                projected.add(entry)
    target = root / "output" / "manuscript" / GENERATED_BIB_NAME
    text = render_database(projected) or "% No additional generated bibliography entries.\n"
    atomic_write_text_confined(root, target, text)
    receipt = {
        "schema_version": 1,
        "kind": "generated-bibliography-projection",
        "generated_sources": sources,
        "authored_sources": {
            path.relative_to(root).as_posix(): hashlib.sha256(raw).hexdigest() for path, raw in snapshot.items()
        },
        "key_origins": origins,
        "projected_keys": projected.keys(),
        "projected_path": target.relative_to(root).as_posix(),
        "projected_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
    atomic_write_text_confined(
        root,
        root / "output" / "bibliography_projection.json",
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
    )
    for path, raw in generated_snapshot.items():
        if read_bytes_confined(root, path) != raw:
            raise ValueError("Generated bibliography changed during projection")
    _unchanged(root, snapshot)
    return target
