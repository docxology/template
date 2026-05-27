"""High-level Zenodo publish workflow."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import PublishingError
from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing.models import AuthorRecord, PublicationMetadata

from .client import ZenodoClient
from .config import ZenodoConfig
from .models import PublishResult

logger = get_logger(__name__)

_PLACEHOLDER_ORCID = re.compile(r"^0000-0000-0000-\d{4}$")


def _creator_dict(author: AuthorRecord) -> dict[str, str]:
    payload: dict[str, str] = {"name": author.name}
    if author.affiliation:
        payload["affiliation"] = author.affiliation
    if author.orcid and not _PLACEHOLDER_ORCID.match(author.orcid):
        payload["orcid"] = author.orcid
    return payload


def _related_identifiers(metadata: PublicationMetadata) -> list[dict[str, str]]:
    related: list[dict[str, str]] = []
    gh_url = metadata.github_release_url
    if gh_url:
        related.append({"identifier": gh_url, "relation": "isSupplementTo", "resource_type": "software"})
    if metadata.repository_url and metadata.repository_url != gh_url:
        related.append(
            {
                "identifier": metadata.repository_url,
                "relation": "references",
                "resource_type": "software",
            }
        )
    return related


def deposition_metadata_dict(metadata: PublicationMetadata) -> dict[str, Any]:
    """Map ``PublicationMetadata`` to Zenodo deposit API metadata fields."""
    creators_source = metadata.author_records or [AuthorRecord(name=name) for name in metadata.authors]
    creators = [_creator_dict(author) for author in creators_source]

    payload: dict[str, Any] = {
        "title": metadata.title,
        "upload_type": "publication",
        "publication_type": "article",
        "description": metadata.deposit_description or metadata.abstract,
        "creators": creators,
        "keywords": metadata.keywords,
        "license": metadata.license.lower(),
    }

    if metadata.publication_date:
        payload["publication_date"] = metadata.publication_date

    version = metadata.paper_version or metadata.release_tag
    if version:
        payload["version"] = version.lstrip("vV")

    related = _related_identifiers(metadata)
    if related:
        payload["related_identifiers"] = related

    return payload


def patch_deposition_description(
    deposition_id: str,
    metadata: PublicationMetadata,
    access_token: str,
    *,
    sandbox: bool = True,
    base_url: str | None = None,
) -> None:
    """Patch the live deposition description after DOI mint (best-effort)."""
    description = metadata.deposit_description or metadata.abstract
    if not description:
        return

    config = ZenodoConfig(access_token=access_token, sandbox=sandbox, base_url=base_url)
    client = ZenodoClient(config)
    try:
        client.update_deposition_metadata(deposition_id, {"description": description})
    except PublishingError as exc:
        logger.warning(
            "Could not patch Zenodo description for deposition %s after publish: %s",
            deposition_id,
            exc,
        )


def publish_to_zenodo(
    metadata: PublicationMetadata,
    file_paths: list[Path],
    access_token: str,
    sandbox: bool = True,
    *,
    base_url: str | None = None,
) -> PublishResult:
    """Publish research artifacts to Zenodo and return DOI plus deposition id."""
    config = ZenodoConfig(access_token=access_token, sandbox=sandbox, base_url=base_url)
    client = ZenodoClient(config)

    dep_metadata = deposition_metadata_dict(metadata)
    deposition = client.create_deposition(dep_metadata)

    for path in file_paths:
        if path.exists():
            client.upload_file(deposition.bucket_url, path)
        else:
            logger.warning(f"Skipping non-existent file for Zenodo upload: {path}")

    doi = client.publish(deposition.deposition_id)
    return PublishResult(doi=doi, deposition_id=deposition.deposition_id)


def publish_new_version_to_zenodo(
    metadata: PublicationMetadata,
    file_paths: list[Path],
    access_token: str,
    existing_doi: str,
    sandbox: bool = True,
    *,
    base_url: str | None = None,
) -> PublishResult:
    """Create a new Zenodo version and return DOI plus deposition id."""
    config = ZenodoConfig(access_token=access_token, sandbox=sandbox, base_url=base_url)
    client = ZenodoClient(config)

    parent_id = client.resolve_deposition_id_from_doi(existing_doi)
    deposition = client.create_new_version(parent_id)
    removed = client.clear_deposition_files(deposition.deposition_id)
    if removed:
        logger.info(
            "Removed %d inherited file(s) from Zenodo draft %s: %s",
            len(removed),
            deposition.deposition_id,
            ", ".join(removed),
        )
    client.update_deposition_metadata(deposition.deposition_id, deposition_metadata_dict(metadata))

    for path in file_paths:
        if path.exists():
            client.upload_file(deposition.bucket_url, path)
        else:
            logger.warning(f"Skipping non-existent file for Zenodo upload: {path}")

    doi = client.publish(deposition.deposition_id)
    return PublishResult(doi=doi, deposition_id=deposition.deposition_id)
