"""Generate citation and archival metadata files from ``manuscript/config.yaml``."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.config.loader import load_config
from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing.repository_metadata import normalized_repository_url

logger = get_logger(__name__)

_DOI_PREFIX_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.IGNORECASE)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SPDX_URLS: dict[str, str] = {
    "MIT": "https://spdx.org/licenses/MIT",
    "Apache-2.0": "https://spdx.org/licenses/Apache-2.0",
    "BSD-3-Clause": "https://spdx.org/licenses/BSD-3-Clause",
    "GPL-3.0-only": "https://spdx.org/licenses/GPL-3.0-only",
    "CC-BY-4.0": "https://spdx.org/licenses/CC-BY-4.0",
    "CC0-1.0": "https://spdx.org/licenses/CC0-1.0",
}


@dataclass(frozen=True)
class _ParsedAuthor:
    """Structured author metadata parsed from config."""

    given_names: str
    family_name: str
    orcid: str | None
    affiliation: str | None
    email: str | None
    corresponding: bool

    @property
    def zenodo_name(self) -> str:
        """Return the Zenodo creator name."""
        if self.given_names:
            return f"{self.family_name}, {self.given_names}"
        return self.family_name


@dataclass(frozen=True)
class _WorkMetadata:
    """Title/version/date fields shared by paper- and book-schema projects."""

    title: object
    version: object
    release_date: object


def build_citation_cff(
    config: dict,
    *,
    repo_url: str | None = None,
    released_date: str | None = None,
) -> str:
    """Build a CFF 1.2.0 citation file from a parsed config mapping.

    Args:
        config: Parsed ``manuscript/config.yaml`` mapping.
        repo_url: Optional repository URL override.
        released_date: Optional ``YYYY-MM-DD`` release date for deterministic output.

    Returns:
        YAML string for ``CITATION.cff`` with a trailing newline.
    """
    work = _work_metadata(config)
    citation: dict[str, Any] = {
        "cff-version": "1.2.0",
        "message": "If you use this software, please cite it using the metadata from this file.",
        "title": _string_or_default(work.title, "Untitled Research"),
        "authors": [_citation_author(author) for author in _authors_from_config(config)],
        "version": _string_or_default(work.version, "0.0.0"),
        "date-released": _resolve_released_date(work.release_date, released_date),
        "license": _license_from_config(config),
        "keywords": _keywords_from_config(config),
        "type": "software",
    }

    normalized_doi = _normalize_doi(_mapping(config.get("publication")).get("doi"))
    if normalized_doi:
        citation["doi"] = normalized_doi

    resolved_repo_url = repo_url or _resolve_repo_url(config)
    if resolved_repo_url:
        citation["repository-code"] = resolved_repo_url

    return yaml.safe_dump(
        citation,
        sort_keys=True,
        allow_unicode=True,
        default_flow_style=False,
    )


def build_codemeta(
    config: dict,
    *,
    repo_url: str | None = None,
    released_date: str | None = None,
) -> dict[str, Any]:
    """Build a CodeMeta / schema.org mapping from a parsed config mapping.

    Args:
        config: Parsed ``manuscript/config.yaml`` mapping.
        repo_url: Optional repository URL override.
        released_date: Optional ``YYYY-MM-DD`` release date for deterministic output.

    Returns:
        Dictionary ready to serialize as ``codemeta.json``.
    """
    work = _work_metadata(config)
    codemeta: dict[str, Any] = {
        "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
        "@type": "SoftwareSourceCode",
        "author": [_codemeta_author(author) for author in _authors_from_config(config)],
        "dateModified": _resolve_released_date(work.release_date, released_date),
        "keywords": _keywords_from_config(config),
        "license": _spdx_url(_license_from_config(config)),
        "name": _string_or_default(work.title, "Untitled Research"),
        "version": _string_or_default(work.version, "0.0.0"),
    }

    normalized_doi = _normalize_doi(_mapping(config.get("publication")).get("doi"))
    if normalized_doi:
        codemeta["identifier"] = normalized_doi

    resolved_repo_url = repo_url or _resolve_repo_url(config)
    if resolved_repo_url:
        codemeta["codeRepository"] = resolved_repo_url

    return codemeta


def build_codemeta_json(
    config: dict,
    *,
    repo_url: str | None = None,
    released_date: str | None = None,
) -> str:
    """Build the serialized ``codemeta.json`` payload.

    Args:
        config: Parsed ``manuscript/config.yaml`` mapping.
        repo_url: Optional repository URL override.
        released_date: Optional ``YYYY-MM-DD`` release date for deterministic output.

    Returns:
        JSON string with a trailing newline.
    """
    return _json_dumps(build_codemeta(config, repo_url=repo_url, released_date=released_date))


def build_zenodo(config: dict) -> dict[str, Any]:
    """Build Zenodo deposition metadata from a parsed config mapping.

    Args:
        config: Parsed ``manuscript/config.yaml`` mapping.

    Returns:
        Dictionary ready to serialize as ``.zenodo.json``.
    """
    work = _work_metadata(config)
    publication = _mapping(config.get("publication"))
    title = _string_or_default(work.title, "Untitled Research")
    normalized_doi = _normalize_doi(publication.get("doi"))
    publication_year = _string_or_none(publication.get("year"))
    description = f"Source code for {title}"
    if publication_year:
        description = f"{description} ({publication_year})"
    description = f"{description}."

    zenodo: dict[str, Any] = {
        "title": title,
        "upload_type": "software",
        "description": description,
        "creators": [_zenodo_creator(author) for author in _authors_from_config(config)],
        "version": _string_or_default(work.version, "0.0.0"),
        "license": _license_from_config(config),
        "keywords": _keywords_from_config(config),
    }
    if normalized_doi:
        zenodo["related_identifiers"] = [
            {
                "relation": "isVersionOf",
                "identifier": normalized_doi,
                "scheme": "doi",
            }
        ]
    return zenodo


def build_zenodo_json(config: dict) -> str:
    """Build the serialized ``.zenodo.json`` payload.

    Args:
        config: Parsed ``manuscript/config.yaml`` mapping.

    Returns:
        JSON string with a trailing newline.
    """
    return _json_dumps(build_zenodo(config))


def write_metadata_files(
    config: dict,
    out_dir: Path,
    *,
    repo_url: str | None = None,
    released_date: str | None = None,
) -> list[Path]:
    """Write citation and archival metadata files into ``out_dir``.

    Args:
        config: Parsed ``manuscript/config.yaml`` mapping.
        out_dir: Directory to receive the metadata files.
        repo_url: Optional repository URL override.
        released_date: Optional ``YYYY-MM-DD`` release date for deterministic output.

    Returns:
        Sorted paths to the written metadata files.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {
        out_dir / "CITATION.cff": build_citation_cff(
            config,
            repo_url=repo_url,
            released_date=released_date,
        ),
        out_dir / "codemeta.json": build_codemeta_json(
            config,
            repo_url=repo_url,
            released_date=released_date,
        ),
        out_dir / ".zenodo.json": build_zenodo_json(config),
    }
    for path, content in written.items():
        path.write_text(content, encoding="utf-8")
        logger.info("Wrote metadata export: %s", path)
    return sorted(written)


def write_metadata_for_config_path(
    config_path: Path,
    out_dir: Path,
    *,
    repo_url: str | None = None,
    released_date: str | None = None,
) -> list[Path]:
    """Load a config file and write the metadata exports.

    Args:
        config_path: Path to ``manuscript/config.yaml``.
        out_dir: Directory to receive the metadata files.
        repo_url: Optional repository URL override.
        released_date: Optional ``YYYY-MM-DD`` release date for deterministic output.

    Returns:
        Sorted paths to the written metadata files.

    Raises:
        ValueError: If the config could not be loaded.
    """
    config = load_config(config_path)
    if config is None:
        raise ValueError(f"Could not load config: {config_path}")
    return write_metadata_files(
        config,
        out_dir,
        repo_url=repo_url,
        released_date=released_date,
    )


def _work_metadata(config: dict) -> _WorkMetadata:
    """Resolve paper fields first, then fall back field-by-field to ``book``."""
    paper = _mapping(config.get("paper"))
    book = _mapping(config.get("book"))
    return _WorkMetadata(
        title=paper.get("title") or book.get("title"),
        version=paper.get("version") or book.get("version"),
        release_date=paper.get("date") or book.get("date") or book.get("year"),
    )


def _authors_from_config(config: dict) -> list[_ParsedAuthor]:
    # Deliberately parse the config mapping directly here instead of importing sibling private helpers.
    raw_authors = config.get("authors")
    authors: list[_ParsedAuthor] = []
    if isinstance(raw_authors, list):
        for raw_author in raw_authors:
            if not isinstance(raw_author, dict):
                continue
            name = _string_or_none(raw_author.get("name"))
            if not name:
                continue
            given_names, family_name = _split_name(name)
            authors.append(
                _ParsedAuthor(
                    given_names=given_names,
                    family_name=family_name,
                    orcid=_string_or_none(raw_author.get("orcid")),
                    affiliation=_string_or_none(raw_author.get("affiliation")),
                    email=_string_or_none(raw_author.get("email")),
                    corresponding=_bool_from_value(raw_author.get("corresponding")),
                )
            )
    if authors:
        return authors
    given_names, family_name = _split_name("Project Author")
    return [
        _ParsedAuthor(
            given_names=given_names,
            family_name=family_name,
            orcid=None,
            affiliation=None,
            email=None,
            corresponding=False,
        )
    ]


def _bool_from_value(value: object) -> bool:
    return value is True


def _citation_author(author: _ParsedAuthor) -> dict[str, str]:
    citation_author = {"family-names": author.family_name}
    if author.given_names:
        citation_author["given-names"] = author.given_names
    if author.orcid:
        citation_author["orcid"] = author.orcid
    if author.affiliation:
        citation_author["affiliation"] = author.affiliation
    return citation_author


def _codemeta_author(author: _ParsedAuthor) -> dict[str, Any]:
    codemeta_author: dict[str, Any] = {
        "@type": "Person",
        "familyName": author.family_name,
        "givenName": author.given_names,
    }
    if author.orcid:
        codemeta_author["@id"] = _orcid_url(author.orcid)
    if author.affiliation:
        codemeta_author["affiliation"] = {
            "@type": "Organization",
            "name": author.affiliation,
        }
    return codemeta_author


def _zenodo_creator(author: _ParsedAuthor) -> dict[str, str]:
    creator = {"name": author.zenodo_name}
    if author.orcid:
        creator["orcid"] = author.orcid
    if author.affiliation:
        creator["affiliation"] = author.affiliation
    return creator


def _split_name(name: str) -> tuple[str, str]:
    tokens = [token for token in name.split() if token]
    if not tokens:
        return "", "Project Author"
    if len(tokens) == 1:
        return "", tokens[0]
    return " ".join(tokens[:-1]), tokens[-1]


def _resolve_repo_url(config: dict) -> str | None:
    publication = _mapping(config.get("publication"))
    return normalized_repository_url(publication)


def _normalize_doi(value: object) -> str | None:
    raw = _string_or_none(value)
    if not raw:
        return None
    normalized = _DOI_PREFIX_RE.sub("", raw, count=1).strip()
    return normalized or None


def _spdx_url(license_id: str) -> str:
    return _SPDX_URLS.get(license_id, license_id)


def _resolve_released_date(configured_date: object, released_date: str | None) -> str:
    if released_date:
        return released_date
    configured = _string_or_none(configured_date)
    if configured and _DATE_RE.match(configured):
        return configured
    return date.today().isoformat()


def _license_from_config(config: dict) -> str:
    metadata = _mapping(config.get("metadata"))
    metadata_license = _string_or_none(metadata.get("license"))
    if metadata_license:
        return metadata_license
    publication = _mapping(config.get("publication"))
    publication_license = _string_or_none(publication.get("license"))
    if publication_license:
        return publication_license
    return "CC-BY-4.0"


def _keywords_from_config(config: dict) -> list[str]:
    raw_keywords = config.get("keywords")
    if not isinstance(raw_keywords, list):
        return []
    keywords = [_string_or_none(keyword) for keyword in raw_keywords]
    return [keyword for keyword in keywords if keyword]


def _orcid_url(orcid: str) -> str:
    normalized = orcid.strip()
    if normalized.startswith("http://") or normalized.startswith("https://"):
        return normalized
    return f"https://orcid.org/{normalized}"


def _mapping(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_or_default(value: object, default: str) -> str:
    return _string_or_none(value) or default


def _json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
