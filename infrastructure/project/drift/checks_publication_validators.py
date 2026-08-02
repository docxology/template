"""Standalone publication-metadata validators and one self-contained check.

Extracted from ``checks_publication`` to keep that module under the line-count
advisory threshold.  The pure data-normalization utilities carry no ``Report``
dependency; ``check_publishing_status_block_current`` is a self-contained README
block validator re-exported by ``checks_publication`` for public-API stability.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

import yaml

from infrastructure.core.files.serialization import load_yaml_mapping as _load_yaml_mapping
from infrastructure.core.files.serialization import relative_or_self as _rel
from infrastructure.project.drift.models import Report


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


_ZENODO_DOI_RE = re.compile(r"^10\.5281/zenodo\.\d+$")


def _is_canonical_template(project: str) -> bool:
    return project.startswith("templates/template_") and "/" not in project.removeprefix("templates/")


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _as_mapping(value: object) -> dict[str, object]:
    """Narrow one YAML value to the mapping shape used by publication checks."""
    if not isinstance(value, dict):
        return {}
    return cast(dict[str, object], value)


def _normalize_doi(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower().startswith("https://doi.org/"):
        return text[len("https://doi.org/") :]
    return text


_PEP440_RELEASE_RE = re.compile(r"^\d+(?:\.\d+)*$")


def _version_key(value: object) -> tuple[int, ...] | str:
    """Return a PEP 440-comparable key so `0.1` and `0.1.0` do not read as drift.

    PEP 440 zero-pads release segments, meaning `0.1 == 0.1.0 == 0.1.0.0`.
    CITATION.cff (YAML) and pyproject.toml are written by different hands and
    legitimately disagree on trailing zeros; only a *semantic* difference is
    drift. Anything that is not a plain dotted-numeric release (pre/post/dev
    suffixes, calendar strings, git describes) falls back to exact string
    comparison rather than being silently normalized into equality.
    """
    text = str(value or "").strip().strip("'\"")
    if not _PEP440_RELEASE_RE.match(text):
        return text
    parts = [int(segment) for segment in text.split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def _cff_author_names(cff: dict[str, object]) -> list[str]:
    """Return display names for a CITATION.cff `authors:` list.

    Handles both person entries (`given-names` + `family-names`) and entity
    entries (`name`), which CFF 1.2.0 allows interchangeably.
    """
    raw = cff.get("authors")
    names: list[str] = []
    if not isinstance(raw, list):
        return names
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        given = str(entry.get("given-names") or "").strip()
        family = str(entry.get("family-names") or "").strip()
        person = " ".join(part for part in (given, family) if part)
        display = person or str(entry.get("name") or "").strip()
        if display:
            names.append(display)
    return names


def _fold_name(value: str) -> str:
    """Case- and whitespace-insensitive form used to compare author names."""
    return " ".join(str(value or "").split()).casefold()


def _normalize_orcid(value: object) -> str:
    """Strip an orcid.org URL prefix so bare and URL ORCID forms compare equal.

    CFF files historically carry `https://orcid.org/0000-...` while the current
    generator emits the bare identifier; both name the same person and must not
    read as authorship drift. Handles http/https schemes, an optional `www.`
    host prefix, and a trailing slash.
    """
    original = str(value or "").strip()
    text = original.rstrip("/")
    lowered = text.lower()
    for prefix in ("https://", "http://"):
        if lowered.startswith(prefix):
            text = text[len(prefix) :]
            lowered = lowered[len(prefix) :]
            break
    for host in ("www.orcid.org/", "orcid.org/"):
        if lowered.startswith(host):
            return text[len(host) :]
    return original


def _author_rows(entries: object, keys: tuple[str, ...]) -> list[tuple[str, ...]]:
    """Project an authors/creators list onto stripped, ORCID-normalized string tuples."""
    rows: list[tuple[str, ...]] = []
    if not isinstance(entries, list):
        return rows
    for entry in entries:
        if isinstance(entry, dict):
            rows.append(tuple(_normalize_orcid(str(entry.get(key) or "").strip()) for key in keys))
    return rows


def _zenodo_concept_identifier(payload: object) -> str:
    """Return the normalized isVersionOf DOI from a .zenodo.json-shaped mapping."""
    related = payload.get("related_identifiers") if isinstance(payload, dict) else None
    if not isinstance(related, list):
        return ""
    for entry in related:
        if isinstance(entry, dict) and str(entry.get("relation", "")).strip() == "isVersionOf":
            return _normalize_doi(entry.get("identifier"))
    return ""


_PLACEHOLDER_AUTHOR_NAMES = frozenset({"research template author", "project author", "your name"})
_PLACEHOLDER_ORCIDS = frozenset({"0000-0000-0000-0000", "0000-0000-0000-1234"})
_KNOWN_AUTHOR_KEYS = frozenset({"name", "orcid", "email", "affiliation", "corresponding"})


def check_publishing_status_block_current(project_root: Path, report: Report, project: str) -> None:
    """README's generated `PUBLISHING-STATUS` block must exist and be in sync.

    `infrastructure.publishing.status_report` compiles `manuscript/config.yaml`
    + the platform registry into a marker-delimited block; this check is the
    enforcement that makes that surfacing durable rather than a one-time edit
    that silently drifts the next time `config.yaml` changes.
    """
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return
    readme_path = project_root / "README.md"
    if not readme_path.is_file():
        return

    from infrastructure.publishing.status_report import (
        BLOCK_START,
        compile_publishing_status,
        status_report_is_current,
    )

    readme_text = _read(readme_path)
    if BLOCK_START not in readme_text:
        report.add(
            "WARNING",
            project,
            "publishing_status_block_missing",
            (
                f"{project}/README.md has no PUBLISHING-STATUS block — run "
                "`uv run python -m infrastructure.publishing.status_report "
                f"--project projects/{project} --write "
                '--init-after "## Publication and rendering"` to surface the '
                "cross-platform publishing surface (see docs/guides/publishing-guide.md)."
            ),
        )
        return

    try:
        compiled = compile_publishing_status(project_root)
    except yaml.YAMLError as exc:
        report.add(
            "ERROR",
            project,
            "publishing_status_config_unparseable",
            f"{_rel(config_path, project_root)} is not valid YAML — cannot compile publishing status: {exc}",
        )
        return

    if not status_report_is_current(readme_text, compiled):
        report.add(
            "WARNING",
            project,
            "publishing_status_block_stale",
            (
                f"{project}/README.md PUBLISHING-STATUS block is out of sync with manuscript/config.yaml — "
                "regenerate with `uv run python -m infrastructure.publishing.status_report "
                f"--project projects/{project} --write`."
            ),
        )


def check_config_author_placeholders(project_root: Path, report: Report, project: str) -> None:
    """Scaffold authorship in manuscript/config.yaml must not ride into derived metadata.

    The export-consistency checks bind derived CITATION.cff/.zenodo.json/codemeta.json
    back to config.yaml, so a placeholder author in config.yaml ITSELF passes them
    green — the derived files faithfully agree with the bad source. This check
    inspects the source of truth directly. Scoped to manuscript/config.yaml only;
    config.yaml.example is expected to hold placeholders and is never scanned.
    """
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return
    config = _load_yaml_mapping(config_path)
    raw_authors = config.get("authors")
    authors = [entry for entry in raw_authors if isinstance(entry, dict)] if isinstance(raw_authors, list) else []

    if not authors:
        publication = config.get("publication", {}) if isinstance(config.get("publication"), dict) else {}
        if _normalize_doi(publication.get("doi", "")):
            report.add(
                "WARNING",
                project,
                "config_authors_missing_with_doi",
                (
                    f"{_rel(config_path, project_root)} declares publication.doi but has no authors block — "
                    "metadata export falls back to the 'Project Author' placeholder, which would ride "
                    "into a real Zenodo deposit"
                ),
            )
        return

    for idx, author in enumerate(authors):
        name = str(author.get("name", "")).strip()
        if " ".join(name.lower().split()) in _PLACEHOLDER_AUTHOR_NAMES:
            report.add(
                "ERROR",
                project,
                "config_author_placeholder_name",
                (
                    f"{_rel(config_path, project_root)} authors[{idx}].name is the scaffold "
                    f"placeholder {name!r} — replace with a real author before publication"
                ),
            )
        orcid = _normalize_orcid(author.get("orcid"))
        if orcid in _PLACEHOLDER_ORCIDS:
            report.add(
                "ERROR",
                project,
                "config_author_placeholder_orcid",
                (
                    f"{_rel(config_path, project_root)} authors[{idx}].orcid is the example "
                    f"value {orcid!r} — replace with the author's real ORCID or remove the key"
                ),
            )
        unknown_keys = sorted(str(key) for key in author if str(key) not in _KNOWN_AUTHOR_KEYS)
        if unknown_keys:
            report.add(
                "ERROR",
                project,
                "config_author_unknown_keys",
                (
                    f"{_rel(config_path, project_root)} authors[{idx}] has unrecognized key(s) "
                    f"{unknown_keys} — the metadata generator silently ignores keys outside "
                    f"{sorted(_KNOWN_AUTHOR_KEYS)} (a plural 'affiliations:' once dropped an "
                    "affiliation from public metadata)"
                ),
            )
