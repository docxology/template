#!/usr/bin/env python3
"""Unified project release orchestrator (GitHub + Zenodo + DOI → render).

Thin orchestrator: validates credentials, builds a release bundle, delegates
to ``infrastructure.publishing.release_workflow``.

Exit codes:
    0: Success
    1: Publish or render failure
    2: Missing PDF, credentials, or invalid inputs

These map to ``scripts.exit_codes.ExitCode`` (SUCCESS=0 / FAILURE=1 / SKIP=2).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

_REPO_ROOT = ensure_repo_root_on_path()

from infrastructure.core.credentials import ensure_dotenv_loaded  # noqa: E402
from infrastructure.core.exceptions import MetadataError, PublishingError  # noqa: E402
from infrastructure.core.logging.utils import (
    get_logger,
    log_header,
    log_success,
)  # noqa: E402
from infrastructure.publishing.release_workflow import (  # noqa: E402
    ReleaseRequest,
    resolve_combined_pdf,
    run_release_workflow,
)
from infrastructure.publishing.preflight import publishing_preflight  # noqa: E402
from infrastructure.publishing.release_cli import (  # noqa: E402
    build_release_parser,
    resolve_github_token,
    resolve_zenodo_token,
)

logger = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = build_release_parser()
    args = parser.parse_args(argv)

    # Pick up GITHUB_TOKEN / ZENODO_PROD_TOKEN / ZENODO_SANDBOX_TOKEN from .env
    # so a token that lives only in .env works without a manual `export`.
    # An explicit `export` (or --*-token flag) still wins.
    ensure_dotenv_loaded()

    repo_root = _REPO_ROOT
    sandbox = not args.production

    combined_pdf = resolve_combined_pdf(repo_root, args.project)
    if combined_pdf is None:
        logger.error(
            "Combined PDF not found for %s. Run scripts/pipeline/stage_03_render.py first.",
            args.project,
        )
        return 2

    github_repo = args.repo or os.getenv("GITHUB_REPO")
    if not args.skip_github and not args.dry_run and not github_repo:
        logger.error("Set --repo or GITHUB_REPO for GitHub release")
        return 2

    github_token = resolve_github_token(args)
    zenodo_token = resolve_zenodo_token(args, sandbox)

    if not args.skip_github and not args.dry_run and not github_token:
        logger.error("Set --github-token or GITHUB_TOKEN for GitHub release")
        return 2
    if not args.skip_zenodo and not args.dry_run and not zenodo_token:
        logger.error("Set --zenodo-token or ZENODO_SANDBOX_TOKEN / ZENODO_PROD_TOKEN / ZENODO_TOKEN")
        return 2

    if not args.dry_run:
        credential_sources = {
            "github": (
                "not-required"
                if args.skip_github
                else "cli"
                if args.github_token
                else "environment"
                if github_token
                else "missing"
            ),
            "zenodo": (
                "not-required"
                if args.skip_zenodo
                else "cli"
                if args.zenodo_token
                else "environment"
                if zenodo_token
                else "missing"
            ),
        }
        try:
            manifest = publishing_preflight(
                repo_root,
                args.project,
                [combined_pdf, repo_root / "projects" / args.project / "manuscript/config.yaml"],
                credential_sources,
            )
        except ValueError as exc:
            logger.error("Publishing preflight failed: %s", exc)
            return 2
        logger.info("Publishing preflight: %s", json.dumps(manifest, sort_keys=True))

    log_header(f"Project release: {args.project} ({args.tag})")

    request = ReleaseRequest(
        repo_root=repo_root,
        project_name=args.project,
        tag=args.tag,
        github_repo=github_repo or "owner/repo",
        sandbox=sandbox,
        new_version=args.new_version,
        skip_github=args.skip_github,
        skip_zenodo=args.skip_zenodo,
        skip_rerender=args.skip_rerender,
        reserve_doi_first=args.reserve_doi_first,
        dry_run=args.dry_run,
        allow_draft_abstract=args.allow_draft_abstract,
        release_name=args.release_name,
        github_token=github_token,
        zenodo_token=zenodo_token,
    )

    try:
        result = run_release_workflow(request)
    except (PublishingError, MetadataError) as exc:
        logger.error("Release failed: %s", exc)
        return 1

    if result.errors and not args.dry_run:
        for err in result.errors:
            logger.error("%s", err)
        return 1

    if result.github_release_url:
        logger.info("GitHub release: %s", result.github_release_url)
    if result.doi:
        logger.info("DOI: https://doi.org/%s", result.doi)
    if result.config_updated:
        logger.info("Updated manuscript config with DOI")
    if result.render_exit_code is not None:
        logger.info("Re-render exit code: %s", result.render_exit_code)

    log_success(f"Release receipt: {result.receipt_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
