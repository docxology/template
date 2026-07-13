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

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

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

logger = get_logger(__name__)


def _resolve_zenodo_token(args: argparse.Namespace, sandbox: bool) -> str | None:
    zenodo_token = getattr(args, "zenodo_token", None)
    if zenodo_token:
        return str(zenodo_token)
    if sandbox:
        return os.getenv("ZENODO_SANDBOX_TOKEN") or os.getenv("ZENODO_TOKEN")
    return os.getenv("ZENODO_PROD_TOKEN") or os.getenv("ZENODO_TOKEN")


def _resolve_github_token(args: argparse.Namespace) -> str | None:
    github_token = getattr(args, "github_token", None)
    return str(github_token) if github_token else os.getenv("GITHUB_TOKEN")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publish a project release to GitHub and Zenodo, update DOI, and re-render.",
    )
    parser.add_argument("--project", required=True, help="Project name under projects/")
    parser.add_argument("--tag", required=True, help="Git tag for the GitHub release")
    parser.add_argument(
        "--repo",
        help="GitHub repository owner/name (default: GITHUB_REPO env)",
    )
    parser.add_argument("--release-name", help="GitHub release title (default: paper title + tag)")
    parser.add_argument(
        "--production",
        action="store_true",
        help="Use production Zenodo (default: sandbox)",
    )
    parser.add_argument(
        "--new-version",
        action="store_true",
        help="Force a new Zenodo version when publication.doi is already set",
    )
    parser.add_argument("--skip-github", action="store_true", help="Skip GitHub release")
    parser.add_argument("--skip-zenodo", action="store_true", help="Skip Zenodo deposit")
    parser.add_argument(
        "--skip-rerender",
        action="store_true",
        help="Skip PDF re-render after DOI update",
    )
    parser.add_argument(
        "--reserve-doi-first",
        action="store_true",
        help=(
            "Reserve a Zenodo DOI before building the final bundle, write "
            "concept/version DOI fields, re-render, then upload the "
            "DOI-bearing PDF to the same draft"
        ),
    )
    parser.add_argument(
        "--allow-draft-abstract",
        action="store_true",
        help="Allow empty abstract (Zenodo may reject in production)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Prepare bundle and receipt without API calls",
    )
    parser.add_argument("--github-token", help="GitHub token (default: GITHUB_TOKEN)")
    parser.add_argument("--zenodo-token", help="Zenodo token (default: env-based)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Pick up GITHUB_TOKEN / ZENODO_PROD_TOKEN / ZENODO_SANDBOX_TOKEN from .env
    # so a token that lives only in .env works without a manual `export`.
    # An explicit `export` (or --*-token flag) still wins.
    ensure_dotenv_loaded()

    repo_root = Path(__file__).resolve().parent.parent
    sandbox = not args.production

    if resolve_combined_pdf(repo_root, args.project) is None:
        logger.error(
            "Combined PDF not found for %s. Run scripts/pipeline/stage_03_render.py first.",
            args.project,
        )
        return 2

    github_repo = args.repo or os.getenv("GITHUB_REPO")
    if not args.skip_github and not args.dry_run and not github_repo:
        logger.error("Set --repo or GITHUB_REPO for GitHub release")
        return 2

    github_token = _resolve_github_token(args)
    zenodo_token = _resolve_zenodo_token(args, sandbox)

    if not args.skip_github and not args.dry_run and not github_token:
        logger.error("Set --github-token or GITHUB_TOKEN for GitHub release")
        return 2
    if not args.skip_zenodo and not args.dry_run and not zenodo_token:
        logger.error("Set --zenodo-token or ZENODO_SANDBOX_TOKEN / ZENODO_PROD_TOKEN / ZENODO_TOKEN")
        return 2

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
