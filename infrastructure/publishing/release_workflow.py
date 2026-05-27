"""Unified GitHub + Zenodo release workflow for project manuscripts."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import MetadataError, PublishingError
from infrastructure.core.files.operations import calculate_file_hash
from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing.abstract_plaintext import (
    DepositCrossLinks,
    build_deposit_description,
    build_github_release_body,
    github_release_url,
    render_abstract_plaintext,
    resolve_abstract_source,
    resolve_variables_path,
    zenodo_record_url_from_doi,
)
from infrastructure.publishing.config_doi import update_publication_doi
from infrastructure.publishing.deposit_filename import build_deposit_filename
from infrastructure.publishing.github.release import create_github_release
from infrastructure.publishing.metadata_from_config import (
    PublicationReleaseContext,
    load_publication_release_context,
)
from infrastructure.publishing.models import PublicationMetadata
from infrastructure.publishing.package import create_publication_package
from infrastructure.publishing.zenodo.models import PublishResult
from infrastructure.publishing.zenodo.publish import (
    patch_deposition_description,
    publish_new_version_to_zenodo,
    publish_to_zenodo,
)
from infrastructure.project.discovery import resolve_project_root

logger = get_logger(__name__)

RenderFn = Callable[[Path, str], int]

_TAG_PATTERN = re.compile(r"^[^\s/]+$")


@dataclass
class ReleaseRequest:
    """Inputs for a unified project release."""

    repo_root: Path
    project_name: str
    tag: str
    github_repo: str
    sandbox: bool = True
    new_version: bool = False
    skip_github: bool = False
    skip_zenodo: bool = False
    skip_rerender: bool = False
    dry_run: bool = False
    allow_draft_abstract: bool = False
    release_name: str | None = None
    github_token: str | None = None
    zenodo_token: str | None = None
    github_api_base_url: str = "https://api.github.com"
    zenodo_base_url: str | None = None


@dataclass
class ReleaseBundle:
    """On-disk release bundle prepared for upload."""

    bundle_dir: Path
    pdf_path: Path
    metadata: PublicationMetadata
    manifest: dict[str, Any]
    pdf_sha256: str


@dataclass
class ReleaseResult:
    """Outcome of :func:`run_release_workflow`."""

    bundle_dir: Path
    github_release_url: str | None
    doi: str | None
    config_updated: bool
    render_exit_code: int | None
    receipt_path: Path
    dry_run: bool = False
    errors: list[str] = field(default_factory=list)
    pdf_sha256: str | None = None


def resolve_combined_pdf(repo_root: Path, project_name: str) -> Path | None:
    """Locate the combined manuscript PDF for a project."""
    candidates = [
        repo_root / "output" / project_name / "pdf" / f"{project_name}_combined.pdf",
        repo_root / "projects" / project_name / "output" / "pdf" / f"{project_name}_combined.pdf",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def resolve_config_path(repo_root: Path, project_name: str) -> Path:
    """Return the manuscript config path for a project."""
    return repo_root / "projects" / project_name / "manuscript" / "config.yaml"


def validate_release_tag(tag: str) -> None:
    """Reject empty or whitespace-containing release tags."""
    if not tag or not _TAG_PATTERN.match(tag):
        raise PublishingError(f"Invalid release tag: {tag!r}")


def _enrich_metadata_for_release(
    metadata: PublicationMetadata,
    request: ReleaseRequest,
    *,
    pdf_sha256: str,
    doi: str | None = None,
) -> PublicationMetadata:
    """Attach deposit description, integrity hash, and release linkage fields."""
    config_path = resolve_config_path(request.repo_root, request.project_name)
    abstract_source = resolve_abstract_source(
        request.repo_root,
        request.project_name,
        manuscript_abstract=config_path.parent / "00_abstract.md",
    )
    variables_path = resolve_variables_path(request.repo_root, request.project_name)
    gh_url = github_release_url(request.github_repo, request.tag)

    cross_links = DepositCrossLinks(
        project=request.project_name,
        tag=request.tag,
        github_repo=request.github_repo,
        pdf_sha256=pdf_sha256,
        doi=doi or metadata.doi,
        zenodo_record_url=zenodo_record_url_from_doi(doi) if doi else None,
        github_release_url=gh_url,
        release_name=request.release_name,
    )

    metadata.pdf_sha256 = pdf_sha256
    metadata.release_tag = request.tag
    metadata.github_release_url = gh_url
    metadata.deposit_description = build_deposit_description(
        abstract_source=abstract_source,
        variables_path=variables_path,
        cross_links=cross_links,
        override_text=metadata.zenodo_description_override,
    )
    return metadata


def prepare_release_bundle(
    request: ReleaseRequest,
    *,
    release_context: PublicationReleaseContext | None = None,
) -> ReleaseBundle:
    """Copy the combined PDF and write metadata/manifest into a release bundle directory."""
    pdf_source = resolve_combined_pdf(request.repo_root, request.project_name)
    if pdf_source is None:
        raise PublishingError(
            f"Combined PDF not found for {request.project_name}. "
            "Run the render pipeline first (scripts/03_render_pdf.py)."
        )

    config_path = resolve_config_path(request.repo_root, request.project_name)
    if release_context is None:
        release_context = load_publication_release_context(
            config_path,
            allow_draft_abstract=request.allow_draft_abstract,
        )

    metadata = release_context.metadata

    bundle_dir = request.repo_root / "output" / request.project_name / "release_bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    for stale_pdf in bundle_dir.glob("*.pdf"):
        stale_pdf.unlink()

    pdf_sha256 = calculate_file_hash(pdf_source) or ""
    if not pdf_sha256:
        raise PublishingError(f"Could not compute SHA-256 for {pdf_source}")

    source_pdf_name = pdf_source.name
    deposit_name = build_deposit_filename(
        metadata=metadata,
        pdf_sha256=pdf_sha256,
        project_name=request.project_name,
        release_tag=request.tag,
        publish_context=release_context.deposit_context,
    )
    pdf_dest = bundle_dir / deposit_name
    shutil.copy2(pdf_source, pdf_dest)

    dest_sha256 = calculate_file_hash(pdf_dest) or ""
    if dest_sha256 != pdf_sha256:
        raise PublishingError(f"Release bundle hash mismatch for {pdf_dest}: expected {pdf_sha256}, got {dest_sha256}")

    existing_doi = release_context.prior_doi
    metadata = _enrich_metadata_for_release(
        metadata,
        request,
        pdf_sha256=pdf_sha256,
        doi=existing_doi,
    )

    metadata_path = bundle_dir / "publication_metadata.json"
    metadata_path.write_text(
        json.dumps(asdict(metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    output_dir = pdf_source.parent.parent
    manifest = create_publication_package(output_dir, metadata)
    manifest["bundle_pdf"] = str(pdf_dest)
    manifest["pdf_sha256"] = pdf_sha256
    manifest["deposit_filename"] = deposit_name
    manifest["source_pdf_name"] = source_pdf_name
    manifest_path = bundle_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return ReleaseBundle(
        bundle_dir=bundle_dir,
        pdf_path=pdf_dest,
        metadata=metadata,
        manifest=manifest,
        pdf_sha256=pdf_sha256,
    )


def run_github_release(
    request: ReleaseRequest,
    bundle: ReleaseBundle,
    *,
    doi: str | None = None,
) -> str:
    """Create a GitHub release and attach the bundle PDF."""
    if request.dry_run:
        logger.info("Dry run: would create GitHub release %s on %s", request.tag, request.github_repo)
        return github_release_url(request.github_repo, request.tag)

    if not request.github_token:
        raise PublishingError("GitHub token is required (--github-token or GITHUB_TOKEN)")

    release_name = request.release_name or f"{bundle.metadata.title} ({request.tag})"
    abstract_source = resolve_abstract_source(
        request.repo_root,
        request.project_name,
        manuscript_abstract=resolve_config_path(request.repo_root, request.project_name).parent / "00_abstract.md",
    )
    abstract_plain = render_abstract_plaintext(
        abstract_source,
        variables_path=resolve_variables_path(request.repo_root, request.project_name),
        override_text=bundle.metadata.zenodo_description_override,
    )
    gh_url = github_release_url(request.github_repo, request.tag)
    version = bundle.metadata.paper_version or request.tag
    description = build_github_release_body(
        project_name=request.project_name,
        tag=request.tag,
        abstract_plaintext=abstract_plain,
        doi=doi,
        pdf_sha256=bundle.pdf_sha256,
        zenodo_record_url=zenodo_record_url_from_doi(doi) if doi else None,
        github_release_url=gh_url,
        version=version,
    )

    return create_github_release(
        request.tag,
        release_name,
        description,
        [bundle.pdf_path],
        request.github_token,
        request.github_repo,
        base_url=request.github_api_base_url,
    )


def run_zenodo_publish(
    request: ReleaseRequest,
    metadata: PublicationMetadata,
    file_paths: list[Path],
    *,
    existing_doi: str | None = None,
) -> PublishResult:
    """Publish to Zenodo (new deposition or new version)."""
    if request.dry_run:
        logger.info("Dry run: would publish to Zenodo (sandbox=%s)", request.sandbox)
        return PublishResult(
            doi=existing_doi or "10.5281/zenodo.dryrun",
            deposition_id="dryrun",
        )

    if not request.zenodo_token:
        raise PublishingError("Zenodo token is required (--zenodo-token, ZENODO_SANDBOX_TOKEN, or ZENODO_PROD_TOKEN)")

    use_new_version = request.new_version or bool(existing_doi)
    if use_new_version and existing_doi:
        return publish_new_version_to_zenodo(
            metadata,
            file_paths,
            request.zenodo_token,
            existing_doi,
            sandbox=request.sandbox,
            base_url=request.zenodo_base_url,
        )

    return publish_to_zenodo(
        metadata,
        file_paths,
        request.zenodo_token,
        sandbox=request.sandbox,
        base_url=request.zenodo_base_url,
    )


def default_render_fn(repo_root: Path, project_name: str) -> int:
    """Re-render the project PDF via the standard pipeline script."""
    cmd = [
        "uv",
        "run",
        "python",
        str(repo_root / "scripts" / "03_render_pdf.py"),
        "--project",
        project_name,
    ]
    result = subprocess.run(cmd, cwd=repo_root, check=False)
    return int(result.returncode)


def _write_receipt(receipt_path: Path, payload: dict[str, Any]) -> None:
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _update_transmission_artifacts(
    request: ReleaseRequest,
    *,
    doi: str | None,
    github_url: str | None,
    pdf_sha256: str,
    errors: list[str],
) -> None:
    """Append the release ledger and regenerate transmission bookends when enabled."""
    if errors and not request.dry_run:
        return

    project_root = resolve_project_root(request.repo_root, request.project_name)
    receipt_stub = {
        "project": request.project_name,
        "tag": request.tag,
        "github_repo": request.github_repo,
        "github_release_url": github_url,
        "doi": doi,
        "pdf_sha256": pdf_sha256,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sandbox": request.sandbox,
        "dry_run": request.dry_run,
    }
    try:
        from infrastructure.publishing.publication_ledger import append_release_entry, ledger_path_for_project
        from infrastructure.publishing.transmission_bookends import write_transmission_bookends

        append_release_entry(ledger_path_for_project(project_root), receipt_stub)
        write_transmission_bookends(project_root, request.project_name, repo_root=request.repo_root)
    except Exception as exc:  # noqa: BLE001 — bookends must not block release
        logger.warning("Transmission artifact update skipped: %s", exc)


def _persist_bundle_metadata(bundle: ReleaseBundle) -> None:
    """Rewrite ``publication_metadata.json`` after post-publish enrichment."""
    metadata_path = bundle.bundle_dir / "publication_metadata.json"
    metadata_path.write_text(
        json.dumps(asdict(bundle.metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_release_workflow(
    request: ReleaseRequest,
    *,
    render_fn: RenderFn | None = None,
) -> ReleaseResult:
    """Execute Zenodo publish, GitHub release, DOI config update, and optional re-render."""
    validate_release_tag(request.tag)
    renderer = render_fn or default_render_fn

    config_path = resolve_config_path(request.repo_root, request.project_name)
    release_context = load_publication_release_context(
        config_path,
        allow_draft_abstract=request.allow_draft_abstract,
    )
    bundle = prepare_release_bundle(request, release_context=release_context)
    existing_doi = release_context.prior_doi

    github_url: str | None = None
    doi: str | None = existing_doi
    config_updated = False
    render_exit_code: int | None = None
    errors: list[str] = []

    if not request.skip_zenodo:
        try:
            publish_result = run_zenodo_publish(
                request,
                bundle.metadata,
                [bundle.pdf_path],
                existing_doi=existing_doi if (request.new_version or existing_doi) else None,
            )
            doi = publish_result.doi
            if doi and not request.dry_run:
                bundle.metadata = _enrich_metadata_for_release(
                    bundle.metadata,
                    request,
                    pdf_sha256=bundle.pdf_sha256,
                    doi=doi,
                )
                _persist_bundle_metadata(bundle)
                patch_deposition_description(
                    publish_result.deposition_id,
                    bundle.metadata,
                    request.zenodo_token or "",
                    sandbox=request.sandbox,
                    base_url=request.zenodo_base_url,
                )
        except PublishingError as exc:
            errors.append(f"zenodo: {exc}")
            if not request.dry_run:
                raise

    if not request.skip_github:
        try:
            github_url = run_github_release(request, bundle, doi=doi)
        except PublishingError as exc:
            errors.append(f"github: {exc}")
            if not request.dry_run:
                raise

    if doi and doi != existing_doi:
        try:
            config_updated = update_publication_doi(
                config_path,
                doi,
                dry_run=request.dry_run,
            )
        except MetadataError as exc:
            errors.append(f"config: {exc}")
            if not request.dry_run:
                raise

    _update_transmission_artifacts(
        request,
        doi=doi,
        github_url=github_url,
        pdf_sha256=bundle.pdf_sha256,
        errors=errors,
    )

    if config_updated and not request.skip_rerender and not request.dry_run:
        render_exit_code = renderer(request.repo_root, request.project_name)
        if render_exit_code != 0:
            errors.append(f"render: exit code {render_exit_code}")

    receipt_path = bundle.bundle_dir / "RELEASE_RECEIPT.json"
    receipt = {
        "project": request.project_name,
        "tag": request.tag,
        "github_repo": request.github_repo,
        "github_release_url": github_url,
        "doi": doi,
        "config_updated": config_updated,
        "render_exit_code": render_exit_code,
        "dry_run": request.dry_run,
        "sandbox": request.sandbox,
        "bundle_dir": str(bundle.bundle_dir),
        "pdf_path": str(bundle.pdf_path),
        "deposit_filename": bundle.manifest.get("deposit_filename"),
        "source_pdf_name": bundle.manifest.get("source_pdf_name"),
        "pdf_sha256": bundle.pdf_sha256,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "errors": errors,
    }
    _write_receipt(receipt_path, receipt)

    return ReleaseResult(
        bundle_dir=bundle.bundle_dir,
        github_release_url=github_url,
        doi=doi,
        config_updated=config_updated,
        render_exit_code=render_exit_code,
        receipt_path=receipt_path,
        dry_run=request.dry_run,
        errors=errors,
        pdf_sha256=bundle.pdf_sha256,
    )
