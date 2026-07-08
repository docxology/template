"""Zenodo reserve-first and publish helpers for :mod:`release_workflow`."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.exceptions import PublishingError
from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing.config_doi import (
    update_publication_doi,
    update_publication_version_doi,
    zenodo_record_url_for_doi,
)
from infrastructure.publishing.metadata_from_config import (
    PublicationReleaseContext,
    load_publication_release_context,
)
from infrastructure.publishing.models import PublicationMetadata
from infrastructure.publishing.zenodo.models import DepositionResult, PublishResult
from infrastructure.publishing.zenodo.publish import (
    publish_reserved_deposition_to_zenodo,
    publish_new_version_to_zenodo,
    publish_to_zenodo,
    reserve_zenodo_deposition,
)

RenderFn = Callable[[Path, str], int]

logger = get_logger(__name__)


@dataclass
class ReserveDoiPhaseResult:
    """State produced by the reserve-first pre-bundle phase."""

    concept_doi: str | None
    version_doi: str | None
    doi: str | None
    config_updated: bool
    render_exit_code: int | None
    reserved_deposition: DepositionResult | None
    release_context: PublicationReleaseContext
    existing_doi: str | None


def _reserve_doi_dry_run(existing_doi: str | None) -> tuple[str, str]:
    concept_doi = existing_doi or "10.5281/zenodo.1000000"
    version_doi = "10.5281/zenodo.1000001"
    return concept_doi, version_doi


def reserve_zenodo_doi_pair(
    *,
    dry_run: bool,
    zenodo_token: str | None,
    sandbox: bool,
    zenodo_base_url: str | None,
    new_version: bool,
    metadata: PublicationMetadata,
    existing_doi: str | None,
) -> tuple[str, str, DepositionResult | None]:
    """Reserve Zenodo concept and version DOI fields before the PDF bundle is built."""
    if dry_run:
        concept_doi, version_doi = _reserve_doi_dry_run(existing_doi)
        logger.info(
            "Dry run: would reserve Zenodo concept DOI %s and version DOI %s",
            concept_doi,
            version_doi,
        )
        return concept_doi, version_doi, None

    if not zenodo_token:
        raise PublishingError(
            "Zenodo token is required (--zenodo-token, ZENODO_SANDBOX_TOKEN, ZENODO_PROD_TOKEN, or ZENODO_TOKEN)"
        )

    if existing_doi and not new_version:
        raise PublishingError(
            "--reserve-doi-first is for first releases unless --new-version "
            "is supplied; existing publication.doi is already set"
        )
    if new_version and existing_doi:
        raise PublishingError(
            "Reserve-first new-version publishing is not implemented; use the "
            "existing --new-version flow for already-published concept DOIs"
        )

    deposition = reserve_zenodo_deposition(
        metadata,
        zenodo_token,
        sandbox=sandbox,
        base_url=zenodo_base_url,
    )
    version_doi = deposition.reserved_doi
    concept_doi = deposition.concept_doi or existing_doi
    if not version_doi:
        raise PublishingError("Zenodo draft did not return metadata.prereserve_doi.doi")
    if not concept_doi:
        raise PublishingError("Zenodo draft did not return concept DOI information (conceptdoi or conceptrecid)")
    return concept_doi, version_doi, deposition


def write_reserved_dois_to_config(
    config_path: Path,
    *,
    concept_doi: str,
    version_doi: str,
    dry_run: bool,
) -> bool:
    """Write reserved DOIs to the project config."""
    concept_changed = update_publication_doi(
        config_path,
        concept_doi,
        dry_run=dry_run,
    )
    version_changed = update_publication_version_doi(
        config_path,
        version_doi,
        version_record=zenodo_record_url_for_doi(version_doi),
        dry_run=dry_run,
    )
    return bool(concept_changed or version_changed)


def run_reserve_doi_first_phase(
    *,
    config_path: Path,
    release_context: PublicationReleaseContext,
    dry_run: bool,
    zenodo_token: str | None,
    sandbox: bool,
    zenodo_base_url: str | None,
    new_version: bool,
    skip_rerender: bool,
    allow_draft_abstract: bool,
    repo_root: Path,
    project_name: str,
    renderer: RenderFn,
) -> ReserveDoiPhaseResult:
    """Reserve DOIs, write config, optionally re-render, and reload release context."""
    existing_doi = release_context.prior_doi
    concept_doi, version_doi, reserved_deposition = reserve_zenodo_doi_pair(
        dry_run=dry_run,
        zenodo_token=zenodo_token,
        sandbox=sandbox,
        zenodo_base_url=zenodo_base_url,
        new_version=new_version,
        metadata=release_context.metadata,
        existing_doi=existing_doi,
    )
    doi = version_doi
    config_updated = write_reserved_dois_to_config(
        config_path,
        concept_doi=concept_doi,
        version_doi=version_doi,
        dry_run=dry_run,
    )
    render_exit_code: int | None = None
    if config_updated and not skip_rerender and not dry_run:
        render_exit_code = renderer(repo_root, project_name)
        if render_exit_code != 0:
            raise PublishingError(f"Pre-upload render after DOI reservation failed with exit code {render_exit_code}")
    if not dry_run:
        release_context = load_publication_release_context(
            config_path,
            allow_draft_abstract=allow_draft_abstract,
        )
        existing_doi = release_context.prior_doi
    return ReserveDoiPhaseResult(
        concept_doi=concept_doi,
        version_doi=version_doi,
        doi=doi,
        config_updated=config_updated,
        render_exit_code=render_exit_code,
        reserved_deposition=reserved_deposition,
        release_context=release_context,
        existing_doi=existing_doi,
    )


def publish_zenodo_for_release(
    *,
    reserve_doi_first: bool,
    dry_run: bool,
    zenodo_token: str | None,
    sandbox: bool,
    zenodo_base_url: str | None,
    new_version: bool,
    metadata: PublicationMetadata,
    file_paths: list[Path],
    existing_doi: str | None,
    concept_doi: str | None,
    version_doi: str | None,
    reserved_deposition: DepositionResult | None,
    doi: str | None,
) -> PublishResult:
    """Publish to Zenodo using reserve-first or standard/new-version paths."""
    if reserve_doi_first:
        if dry_run:
            return PublishResult(
                doi=doi or "10.5281/zenodo.dryrun",
                deposition_id="dryrun",
                concept_doi=concept_doi,
            )
        if reserved_deposition is None:
            raise PublishingError("Reserve-first publish has no reserved deposition")
        publish_result = publish_reserved_deposition_to_zenodo(
            metadata,
            file_paths,
            zenodo_token or "",
            reserved_deposition,
            sandbox=sandbox,
            base_url=zenodo_base_url,
        )
        if version_doi and publish_result.doi != version_doi:
            raise PublishingError(
                f"Published Zenodo DOI differs from reserved DOI: {publish_result.doi} != {version_doi}"
            )
        return publish_result

    if dry_run:
        logger.info("Dry run: would publish to Zenodo (sandbox=%s)", sandbox)
        return PublishResult(
            doi=existing_doi or "10.5281/zenodo.dryrun",
            deposition_id="dryrun",
        )

    if not zenodo_token:
        raise PublishingError("Zenodo token is required (--zenodo-token, ZENODO_SANDBOX_TOKEN, or ZENODO_PROD_TOKEN)")

    use_new_version = new_version or bool(existing_doi)
    if use_new_version and existing_doi:
        return publish_new_version_to_zenodo(
            metadata,
            file_paths,
            zenodo_token,
            existing_doi,
            sandbox=sandbox,
            base_url=zenodo_base_url,
        )

    return publish_to_zenodo(
        metadata,
        file_paths,
        zenodo_token,
        sandbox=sandbox,
        base_url=zenodo_base_url,
    )
