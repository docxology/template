"""Build PublicationMetadata from manuscript config.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.config.loader import load_config
from infrastructure.core.exceptions import MetadataError
from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing.abstract_plaintext import render_abstract_plaintext
from infrastructure.publishing.deposit_filename import (
    DepositPublishContext,
    deposit_context_from_config,
)
from infrastructure.publishing.models import AuthorRecord, PublicationMetadata

logger = get_logger(__name__)

#: Typed lifecycle subfolders that sit between ``projects/`` and a project dir.
#: Keep in sync with discovery.NON_RENDERED_SUBDIRS plus the rendered
#: ``active``/``templates`` pools.
_TYPED_PROJECT_SUBDIRS: frozenset[str] = frozenset(
    {"active", "working", "ongoing", "published", "archive", "other", "templates"}
)


def _repo_root_and_qualified_name(project_root: Path) -> tuple[Path, str] | None:
    """Return ``(repo_root, qualified_name)`` for a project source tree.

    Handles both the flat ``projects/<name>`` layout and the typed-subfolder
    layout ``projects/<type>/<name>`` (e.g. ``projects/templates/<name>``),
    where the output tree lives at ``output/<qualified_name>``.
    """
    parent = project_root.parent
    if parent.name == "projects":
        return parent.parent, project_root.name
    if parent.name in _TYPED_PROJECT_SUBDIRS and parent.parent.name == "projects":
        return parent.parent.parent, f"{parent.name}/{project_root.name}"
    return None


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


def _default_variables_path(config_path: Path) -> Path | None:
    """Return generated manuscript variables next to or above a project config."""
    project_root = config_path.parent.parent
    candidates = [project_root / "output" / "data" / "manuscript_variables.json"]
    if config_path.parent.name == "manuscript":
        resolved = _repo_root_and_qualified_name(project_root)
        if resolved is not None:
            repo_root, qualified_name = resolved
            candidates.append(repo_root / "output" / qualified_name / "data" / "manuscript_variables.json")
    for path in candidates:
        if path.is_file():
            return path
    return None


def _default_abstract_path(config_path: Path) -> Path:
    """Prefer hydrated output abstract when a config belongs to a project tree."""
    project_root = config_path.parent.parent
    candidates = [project_root / "output" / "manuscript" / "00_abstract.md"]
    if config_path.parent.name == "manuscript":
        resolved = _repo_root_and_qualified_name(project_root)
        if resolved is not None:
            repo_root, qualified_name = resolved
            candidates.append(repo_root / "output" / qualified_name / "manuscript" / "00_abstract.md")
    candidates.append(config_path.parent / "00_abstract.md")
    for path in candidates:
        if path.is_file():
            return path
    return candidates[-1]


def _read_abstract_plaintext(abstract_path: Path, *, variables_path: Path | None = None) -> str:
    """Return a short plaintext abstract excerpt for citations and legacy fields."""
    return render_abstract_plaintext(abstract_path, variables_path=variables_path)


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
    variables_path: Path | None = None,
    allow_draft_abstract: bool = False,
) -> PublicationMetadata:
    """Build ``PublicationMetadata`` from a parsed config mapping."""
    paper = config.get("paper") or {}
    if not isinstance(paper, dict):
        paper = {}
    # Book-length exemplars (e.g. template_textbook) carry their title under
    # ``book:`` rather than ``paper:``; fall back so they don't publish as
    # "Untitled Research".
    book = config.get("book") or {}
    if not isinstance(book, dict):
        book = {}
    publication = config.get("publication") or {}
    if not isinstance(publication, dict):
        publication = {}

    title = str(paper.get("title") or book.get("title") or "Untitled Research")
    authors, author_records = _author_records_from_config(config)

    keywords_raw = config.get("keywords") or []
    keywords = [str(k) for k in keywords_raw] if isinstance(keywords_raw, list) else []

    resolved_abstract_path = abstract_path
    if resolved_abstract_path is None:
        resolved_abstract_path = _default_abstract_path(config_path)
    resolved_variables_path = variables_path if variables_path is not None else _default_variables_path(config_path)
    abstract = (
        _read_abstract_plaintext(resolved_abstract_path, variables_path=resolved_variables_path)
        if resolved_abstract_path.exists()
        else ""
    )
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
    if pub_year is None and book.get("year"):
        pub_year = str(book["year"]).strip()
    publication_date = paper_date or pub_year

    # Book-length exemplars carry their deposit version under ``book.version``;
    # fall back so the Zenodo ``version`` field is the clean "0.1.1" rather than
    # the "v0.1.1" tag string (mirrors the ``book.title`` fallback above).
    paper_version = None
    if paper.get("version"):
        paper_version = str(paper["version"]).strip()
    elif book.get("version"):
        paper_version = str(book["version"]).strip()

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
        paper_version=paper_version,
        zenodo_description_override=zenodo_description_override,
    )


def load_publication_release_context(
    config_path: Path,
    *,
    abstract_path: Path | None = None,
    variables_path: Path | None = None,
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
        variables_path=variables_path,
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
    variables_path: Path | None = None,
    allow_draft_abstract: bool = False,
) -> PublicationMetadata:
    """Load publication metadata from ``manuscript/config.yaml``.

    Args:
        config_path: Path to ``config.yaml``.
        abstract_path: Optional abstract markdown file; defaults to sibling ``00_abstract.md``.
        variables_path: Optional manuscript variables JSON used to hydrate abstract tokens.
        allow_draft_abstract: When False, raise if abstract text is empty after load.

    Returns:
        ``PublicationMetadata`` populated from config (and abstract file when present).
    """
    return load_publication_release_context(
        config_path,
        abstract_path=abstract_path,
        variables_path=variables_path,
        allow_draft_abstract=allow_draft_abstract,
    ).metadata
