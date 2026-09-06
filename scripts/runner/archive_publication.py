#!/usr/bin/env python3
"""Archival publication stage orchestrator (Stage 15 — opt-in via [archival] tag).

Thin orchestrator that mirrors the executable bundle (produced by Stage 14)
to multiple independent archival providers (Zenodo, Software Heritage, IPFS).

Defaults to dry-run for safety — pass --commit to actually deposit. Reads
credentials from environment variables or
``~/.config/template-archival/credentials.json``.

This stage is OPT-IN — it does not run as part of the default core pipeline.
Enable via:

    ./run.sh --pipeline --project <name> --tags archival

or run standalone:

    uv run python scripts/runner/archive_publication.py --project <name>

Pass ``--check-status`` for a read-only refresh of the project origin's
public archival state from credential-free evidence (software_heritage
only; no bundle, no deposit).

Exit codes:
    0: All requested providers returned ok (or dry-run)
    1: At least one provider failed
    2: Bundle not found (graceful skip)
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

# parents[2] because this file is scripts/runner/archive_publication.py
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger, log_header, log_success  # noqa: E402
from infrastructure.publishing.archival import (  # noqa: E402
    IPFSPinataProvider,
    IPFSWeb3StorageProvider,
    SoftwareHeritageProvider,
    ZenodoProvider,
    archive_publication,
    check_publication_status,
    load_credentials,
    resolve_git_origin_url,
)

logger = get_logger(__name__)


_PROVIDER_CHOICES = ("zenodo", "software_heritage", "ipfs_pinata", "ipfs_web3storage")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mirror a project's executable bundle to archival targets.")
    parser.add_argument("--project", required=True, help="Project name under projects/")
    parser.add_argument(
        "--providers",
        nargs="+",
        choices=_PROVIDER_CHOICES,
        default=["software_heritage"],
        help="Providers to deposit to (default: software_heritage; safe, no token required)",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually perform deposits. Without this flag, runs in dry-run mode.",
    )
    parser.add_argument(
        "--check-status",
        action="store_true",
        help=(
            "Read-only refresh of the project origin's public archival state "
            "(software_heritage only; no bundle and no deposit)."
        ),
    )
    parser.add_argument(
        "--base-url",
        default="https://archive.softwareheritage.org/api/1",
        help="Status-check API base (software_heritage). Tests point this at a local server.",
    )
    args = parser.parse_args(argv)

    if args.check_status:
        return _run_status_check(args)

    repo_root = Path(__file__).resolve().parents[2]
    bundle_dir = repo_root / "output" / args.project / "executable_bundle"

    if not bundle_dir.exists():
        logger.warning(
            "Bundle not found at %s — run scripts/runner/bundle_executable.py first. Exiting 2 (graceful skip).",
            bundle_dir,
        )
        sys.exit(2)

    log_header(f"Stage: Archival Publication (project: {args.project}, commit: {args.commit})")

    credentials = load_credentials()
    providers: list = []
    for name in args.providers:
        if name == "zenodo":
            providers.append(ZenodoProvider(credentials.zenodo_token))
        elif name == "software_heritage":
            providers.append(SoftwareHeritageProvider())
        elif name == "ipfs_pinata":
            providers.append(IPFSPinataProvider(credentials.pinata_jwt))
        elif name == "ipfs_web3storage":
            providers.append(IPFSWeb3StorageProvider(credentials.web3_storage_token))

    receipts_out = bundle_dir / "ARCHIVAL_RECEIPTS.json"
    credential_sources = {
        "zenodo": "environment" if credentials.zenodo_token else "missing",
        "pinata": "environment" if credentials.pinata_jwt else "missing",
        "web3storage": "environment" if credentials.web3_storage_token else "missing",
    }

    run = archive_publication(
        bundle_dir,
        providers=providers,
        dry_run=not args.commit,
        output_receipts_path=receipts_out,
        repo_root=repo_root,
        project_name=args.project,
        credential_sources=credential_sources,
    )

    print(json.dumps(run.to_dict(), indent=2, sort_keys=True))

    if run.all_ok:
        log_success(f"All {len(run.receipts)} provider(s) ok. Receipts: {receipts_out}")
        return 0

    logger.error("Failed providers: %s", [r.provider for r in run.failed])
    return 1


def _run_status_check(args: argparse.Namespace) -> int:
    """Read-only archival status refresh for one project's origin remote."""
    if args.commit:
        raise SystemExit("--check-status performs no deposits; --commit is not valid")
    if args.providers != ["software_heritage"]:
        raise SystemExit("--check-status currently supports only: --providers software_heritage")

    repo_root = Path(__file__).resolve().parents[2]
    project_dir = repo_root / "projects" / args.project
    repo_url = resolve_git_origin_url(project_dir)
    if repo_url is None:
        raise SystemExit(f"Could not resolve an origin remote URL for {project_dir}")

    receipt = check_publication_status(repo_url, base_url=args.base_url)
    print(json.dumps(dataclasses.asdict(receipt), indent=2, sort_keys=True))
    return 0 if receipt.status == "ok" else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
