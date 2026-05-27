"""Build PublicationMetadata from manuscript config.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.config.loader import load_config
from infrastructure.core.exceptions import MetadataError
from infrastructure.core.logging.utils import get_logger
from infrastructure.prose.markdown import normalise_for_deposit
from infrastructure.publishing.deposit_filename import (
    DepositPublishContext,
    deposit_context_from_config,
)
from infrastructure.publishing.models import AuthorRecord, PublicationMetadata

logger = get_logger(__name__)


@dataclass(frozen=True)
class PublicationReleaseContext:
    """Single-parse manuscript config for release bundle preparation."""

    metadata: PublicationMetadata
    deposit_context: DepositPublishContext
    prior_doi: str | None


def _license_from_config(config: dict) -> str:
    metadata_block = config.get("metadata") or {}
    if isinstance(metadata_block, dict) and metadata_block.get("license"):
        return str(metadata_block["license"])
    publication = config.get("publication") or {}
    if isinstance(publication, dict) and publication.get("license"):
        return str(publication["license"])
    return "CC-BY-4.0"


def _author_records_from_config(config: dict) -> tuple[list[str], list[AuthorRecord]]:
    authors: list[str] = []
    records: list[AuthorRecord] = []
    raw_authors = config.get("authors") or []
    if isinstance(raw_authors, list):
        for author in raw_authors:
            if isinstance(author, dict) and author.get("name"):
                name = str(author["name"])
                authors.append(name)
                orcid = str(author["orcid"]).strip() if author.get("orcid") else None
                affiliation = str(author["affiliation"]).strip() if author.get("affiliation") else None
                email = str(author["email"]).strip() if author.get("email") else None
                records.append(
                    AuthorRecord(
                        name=name,
                        orcid=orcid or None,
                        affiliation=affiliation or None,
                        email=email or None,
                    )
                )
    if not authors:
        authors = ["Project Author"]
        records = [AuthorRecord(name="Project Author")]
    return authors, records


def _read_abstract_plaintext(abstract_path: Path) -> str:
    """Return a short plaintext abstract excerpt for citations and legacy fields."""
    try:
        text = abstract_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Could not read abstract from %s: %s", abstract_path, exc)
        return ""
    return normalise_for_deposit(text)


def _prior_doi_from_config(config: dict) -> str | None:
    publication = config.get("publication") or {}
    if not isinstance(publication, dict):
        return None
    existing_doi = publication.get("doi")
    doi_str = str(existing_doi).strip() if existing_doi else None
    return doi_str or None


def publication_metadata_from_config_dict(
    config: dict,
    config_path: Path,
    *,
    abstract_path: Path | None = None,
    allow_draft_abstract: bool = False,
) -> PublicationMetadata:
    """Build ``PublicationMetadata`` from a parsed config mapping."""
    paper = config.get("paper") or {}
    if not isinstance(paper, dict):
        paper = {}
    publication = config.get("publication") or {}
    if not isinstance(publication, dict):
        publication = {}

    title = str(paper.get("title") or "Untitled Research")
    authors, author_records = _author_records_from_config(config)

    keywords_raw = config.get("keywords") or []
    keywords = [str(k) for k in keywords_raw] if isinstance(keywords_raw, list) else []

    resolved_abstract_path = abstract_path
    if resolved_abstract_path is None:
        resolved_abstract_path = config_path.parent / "00_abstract.md"
    abstract = _read_abstract_plaintext(resolved_abstract_path) if resolved_abstract_path.exists() else ""
    if not abstract and not allow_draft_abstract:
        override = publication.get("zenodo_description")
        if not (isinstance(override, str) and override.strip()):
            raise MetadataError(
                "Abstract is required for Zenodo publication. "
                f"Add {resolved_abstract_path.name} or pass allow_draft_abstract=True."
            )
    if not abstract:
        logger.warning("Publishing with empty abstract (draft mode)")

    doi_str = _prior_doi_from_config(config)

    paper_date = str(paper["date"]).strip() if paper.get("date") else None
    pub_year = str(publication["year"]).strip() if publication.get("year") else None
    publication_date = paper_date or pub_year

    zenodo_override = publication.get("zenodo_description")
    zenodo_description_override = (
        str(zenodo_override).strip() if isinstance(zenodo_override, str) and zenodo_override.strip() else None
    )

    return PublicationMetadata(
        title=title,
        authors=authors,
        abstract=abstract,
        keywords=keywords,
        doi=doi_str,
        journal=str(publication["journal"]) if publication.get("journal") else None,
        publication_date=publication_date,
        license=_license_from_config(config),
        repository_url=str(publication["repository_url"]) if publication.get("repository_url") else None,
        author_records=author_records,
        paper_version=str(paper["version"]).strip() if paper.get("version") else None,
        zenodo_description_override=zenodo_description_override,
    )


def load_publication_release_context(
    config_path: Path,
    *,
    abstract_path: Path | None = None,
    allow_draft_abstract: bool = False,
) -> PublicationReleaseContext:
    """Load publication metadata, deposit context, and prior DOI in one parse."""
    config = load_config(config_path)
    if not config:
        raise MetadataError(f"Could not load config: {config_path}")

    metadata = publication_metadata_from_config_dict(
        config,
        config_path,
        abstract_path=abstract_path,
        allow_draft_abstract=allow_draft_abstract,
    )
    return PublicationReleaseContext(
        metadata=metadata,
        deposit_context=deposit_context_from_config(config),
        prior_doi=_prior_doi_from_config(config),
    )


def publication_metadata_from_config(
    config_path: Path,
    *,
    abstract_path: Path | None = None,
    allow_draft_abstract: bool = False,
) -> PublicationMetadata:
    """Load publication metadata from ``manuscript/config.yaml``.

    Args:
        config_path: Path to ``config.yaml``.
        abstract_path: Optional abstract markdown file; defaults to sibling ``00_abstract.md``.
        allow_draft_abstract: When False, raise if abstract text is empty after load.

    Returns:
        ``PublicationMetadata`` populated from config (and abstract file when present).
    """
    return load_publication_release_context(
        config_path,
        abstract_path=abstract_path,
        allow_draft_abstract=allow_draft_abstract,
    ).metadata
