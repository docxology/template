"""Argument and credential-source helpers for the release entrypoint."""

from __future__ import annotations

import argparse
import os


def build_release_parser() -> argparse.ArgumentParser:
    """Build the stable public CLI for project releases."""
    parser = argparse.ArgumentParser(
        description="Publish a project release to GitHub and Zenodo, update DOI, and re-render.",
    )
    parser.add_argument("--project", required=True, help="Project name under projects/")
    parser.add_argument("--tag", required=True, help="Git tag for the GitHub release")
    parser.add_argument("--repo", help="GitHub repository owner/name (default: GITHUB_REPO env)")
    parser.add_argument("--release-name", help="GitHub release title (default: paper title + tag)")
    parser.add_argument("--production", action="store_true", help="Use production Zenodo (default: sandbox)")
    parser.add_argument(
        "--new-version",
        action="store_true",
        help="Force a new Zenodo version when publication.doi is already set",
    )
    parser.add_argument("--skip-github", action="store_true", help="Skip GitHub release")
    parser.add_argument("--skip-zenodo", action="store_true", help="Skip Zenodo deposit")
    parser.add_argument("--skip-rerender", action="store_true", help="Skip PDF re-render after DOI update")
    parser.add_argument(
        "--reserve-doi-first",
        action="store_true",
        help="Reserve a DOI, re-render, then upload the DOI-bearing PDF to the same draft",
    )
    parser.add_argument("--allow-draft-abstract", action="store_true", help="Allow an empty abstract")
    parser.add_argument("--dry-run", action="store_true", help="Prepare bundle and receipt without API calls")
    parser.add_argument("--github-token", help="GitHub token (default: GITHUB_TOKEN)")
    parser.add_argument("--zenodo-token", help="Zenodo token (default: env-based)")
    return parser


def resolve_zenodo_token(args: argparse.Namespace, sandbox: bool) -> str | None:
    """Resolve a Zenodo token without exposing its value."""
    if args.zenodo_token:
        return str(args.zenodo_token)
    if sandbox:
        return os.getenv("ZENODO_SANDBOX_TOKEN") or os.getenv("ZENODO_TOKEN")
    return os.getenv("ZENODO_PROD_TOKEN") or os.getenv("ZENODO_TOKEN")


def resolve_github_token(args: argparse.Namespace) -> str | None:
    """Resolve a GitHub token without exposing its value."""
    return args.github_token or os.getenv("GITHUB_TOKEN")
