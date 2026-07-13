"""fonds_reader.py — Read fonds from fonds/templates/ exemplars.

All functions use graceful fallbacks: missing paths return ``None`` or empty
collections with a logged warning rather than raising.

Repo root is resolved relative to this file's location:
  src/fonds_reader.py is at projects/templates/template_pools_rules_tools/src/
  → up 4 levels → repo root
"""

from __future__ import annotations

import csv
import logging
import pathlib

import yaml

from .type_defs import (
    AllFondsResult,
    BibliographyFondResult,
    ContactsFondResult,
    DatasetsFondResult,
    FondsSummary,
)

__all__ = [
    "read_bibliography_fond",
    "read_contacts_fond",
    "read_datasets_fond",
    "read_all_fonds",
    "count_summary",
    "get_fonds_root",
]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Repo-root resolution
# ---------------------------------------------------------------------------


def _repo_root() -> pathlib.Path:
    """Return the repository root (4 levels above this file)."""
    return pathlib.Path(__file__).resolve().parents[4]


def _fonds_root() -> pathlib.Path:
    bundled = (
        pathlib.Path(__file__).resolve().parents[1] / "_template_resources" / "fonds" / "templates"
    )
    if bundled.is_dir():
        return bundled
    return _repo_root() / "fonds" / "templates"


# Expose for test use (not part of the main public API)
get_fonds_root = _fonds_root


# ---------------------------------------------------------------------------
# Bibliography fond
# ---------------------------------------------------------------------------


def read_bibliography_fond(
    fond_name: str = "template_bibliography",
    *,
    templates_root: pathlib.Path | None = None,
) -> BibliographyFondResult | None:
    """Read the bibliography fond manifest and data files.

    Returns a :class:`BibliographyFondResult` with keys:

    - ``manifest``: parsed fonds.yaml dict
    - ``bib_text``: raw BibTeX string
    - ``csv_rows``: list of dicts from references.csv

    Returns ``None`` if the fond directory or any required file is missing.
    """
    fond_root = templates_root if templates_root is not None else _fonds_root()
    fond_dir = fond_root / fond_name

    manifest_path = fond_dir / "fonds.yaml"
    bib_path = fond_dir / "data" / "references.bib"
    csv_path = fond_dir / "data" / "references.csv"

    for p in (manifest_path, bib_path, csv_path):
        if not p.exists():
            logger.warning("bibliography fond: missing %s", p)
            return None

    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        bib_text = bib_path.read_text(encoding="utf-8")
        with csv_path.open(encoding="utf-8") as fh:
            csv_rows: list[dict[str, str]] = list(csv.DictReader(fh))
    except (OSError, UnicodeDecodeError, yaml.YAMLError, csv.Error) as exc:
        logger.warning("bibliography fond: read error — %s", exc)
        return None

    return BibliographyFondResult(
        manifest=manifest,
        bib_text=bib_text,
        csv_rows=csv_rows,
    )


# ---------------------------------------------------------------------------
# Contacts fond
# ---------------------------------------------------------------------------


def read_contacts_fond(
    fond_name: str = "template_contacts",
    *,
    templates_root: pathlib.Path | None = None,
) -> ContactsFondResult | None:
    """Read the contacts fond manifest and data file.

    Returns a :class:`ContactsFondResult` with keys:

    - ``manifest``: parsed fonds.yaml dict
    - ``contacts``: list of contact dicts

    Returns ``None`` if the fond directory or any required file is missing.
    """
    fond_root = templates_root if templates_root is not None else _fonds_root()
    fond_dir = fond_root / fond_name
    manifest_path = fond_dir / "fonds.yaml"
    contacts_path = fond_dir / "data" / "contacts.yaml"

    for p in (manifest_path, contacts_path):
        if not p.exists():
            logger.warning("contacts fond: missing %s", p)
            return None

    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        contacts: list[object] = yaml.safe_load(contacts_path.read_text(encoding="utf-8")) or []
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        logger.warning("contacts fond: read error — %s", exc)
        return None

    return ContactsFondResult(manifest=manifest, contacts=contacts)


# ---------------------------------------------------------------------------
# Datasets fond
# ---------------------------------------------------------------------------


def read_datasets_fond(
    fond_name: str = "template_datasets",
    *,
    templates_root: pathlib.Path | None = None,
) -> DatasetsFondResult | None:
    """Read the datasets fond manifest and data file.

    Returns a :class:`DatasetsFondResult` with keys:

    - ``manifest``: parsed fonds.yaml dict
    - ``datasets``: list of dataset dicts

    Returns ``None`` if the fond directory or any required file is missing.
    """
    fond_root = templates_root if templates_root is not None else _fonds_root()
    fond_dir = fond_root / fond_name
    manifest_path = fond_dir / "fonds.yaml"
    datasets_path = fond_dir / "data" / "datasets.yaml"

    for p in (manifest_path, datasets_path):
        if not p.exists():
            logger.warning("datasets fond: missing %s", p)
            return None

    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        datasets: list[object] = yaml.safe_load(datasets_path.read_text(encoding="utf-8")) or []
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        logger.warning("datasets fond: read error — %s", exc)
        return None

    return DatasetsFondResult(manifest=manifest, datasets=datasets)


# ---------------------------------------------------------------------------
# Combined loader
# ---------------------------------------------------------------------------


def read_all_fonds() -> AllFondsResult:
    """Read all three public tracked fonds and return consolidated data.

    Returns an :class:`AllFondsResult` with ``bibliography``, ``contacts``,
    and ``datasets`` keys. Values are typed fond result dicts, or ``None``
    when the fond is absent.
    """
    return AllFondsResult(
        bibliography=read_bibliography_fond(),
        contacts=read_contacts_fond(),
        datasets=read_datasets_fond(),
    )


def count_summary(all_fonds: AllFondsResult | None = None) -> FondsSummary:
    """Return a high-level count summary across all three fonds.

    If *all_fonds* is ``None`` the function calls :func:`read_all_fonds`
    internally.

    Returns a :class:`FondsSummary` with:

    - ``bibliography_entries``: number of CSV rows in the bibliography fond
    - ``contacts_count``: number of entries in the contacts fond
    - ``datasets_count``: number of entries in the datasets fond
    - ``fonds_loaded``: how many of the three fonds were successfully loaded
    """
    if all_fonds is None:
        all_fonds = read_all_fonds()

    bib = all_fonds["bibliography"]
    contacts_fond = all_fonds["contacts"]
    datasets_fond = all_fonds["datasets"]

    bib_entries = len(bib["csv_rows"]) if bib is not None else 0
    contacts_count = len(contacts_fond["contacts"]) if contacts_fond is not None else 0
    datasets_count = len(datasets_fond["datasets"]) if datasets_fond is not None else 0
    fonds_loaded = sum(1 for v in (bib, contacts_fond, datasets_fond) if v is not None)

    return FondsSummary(
        bibliography_entries=bib_entries,
        contacts_count=contacts_count,
        datasets_count=datasets_count,
        fonds_loaded=fonds_loaded,
    )
