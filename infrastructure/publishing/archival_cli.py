"""CLI entry point for ``infrastructure.publishing.archival``.

Usage::

    # Dry-run (default — safe; shows what would be deposited):
    uv run python -m infrastructure.publishing.archival_cli \\
        --bundle output/template_code_project/executable_bundle \\
        --providers zenodo software_heritage ipfs_pinata ipfs_web3storage

    # Real deposit (requires credentials via env or ~/.config/template-archival/credentials.json):
    uv run python -m infrastructure.publishing.archival_cli \\
        --bundle output/template_code_project/executable_bundle \\
        --providers zenodo software_heritage \\
        --commit
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

from infrastructure.publishing.archival import (
    ArchivalCredentials,
    ArchivalProvider,
    IPFSPinataProvider,
    IPFSWeb3StorageProvider,
    SoftwareHeritageProvider,
    ZenodoProvider,
    archive_publication,
    check_publication_status,
    load_credentials,
    resolve_git_origin_url,
)


_PROVIDER_CHOICES = ("zenodo", "software_heritage", "ipfs_pinata", "ipfs_web3storage")


def _build_providers(names: list[str], credentials: ArchivalCredentials) -> list[ArchivalProvider]:
    providers: list[ArchivalProvider] = []
    for name in names:
        if name == "zenodo":
            providers.append(ZenodoProvider(credentials.zenodo_token))
        elif name == "software_heritage":
            providers.append(SoftwareHeritageProvider())
        elif name == "ipfs_pinata":
            providers.append(IPFSPinataProvider(credentials.pinata_jwt))
        elif name == "ipfs_web3storage":
            providers.append(IPFSWeb3StorageProvider(credentials.web3_storage_token))
        else:
            raise SystemExit(f"Unknown provider: {name!r}. Choose from {_PROVIDER_CHOICES}.")
    return providers


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.publishing.archival_cli",
        description="Mirror a publication bundle to multiple archival targets.",
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        required=False,
        default=None,
        help="Path to the publication bundle (directory or single file)",
    )
    parser.add_argument(
        "--check-status",
        action="store_true",
        help=(
            "Read-only refresh of a provider's public archival state; performs "
            "no deposit. Requires --repo-url or --git-dir; only software_heritage "
            "supports status checks."
        ),
    )
    parser.add_argument(
        "--repo-url",
        default=None,
        help="Repository URL for --check-status (e.g. https://github.com/org/repo).",
    )
    parser.add_argument(
        "--git-dir",
        type=Path,
        default=None,
        help="Git working tree whose origin remote supplies the URL for --check-status.",
    )
    parser.add_argument(
        "--base-url",
        default="https://archive.softwareheritage.org/api/1",
        help="Status-check API base (software_heritage). Tests point this at a local server.",
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        choices=_PROVIDER_CHOICES,
        required=True,
        help="Which archival providers to deposit to (one or more).",
    )
    parser.add_argument(
        "--receipts-out",
        type=Path,
        default=None,
        help="Optional path to write the archival receipts JSON.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually perform the deposits. Without this flag, runs in dry-run mode.",
    )

    args = parser.parse_args(argv)

    if args.check_status:
        return _run_status_check(args)

    if not args.bundle:
        parser.error("--bundle is required unless --check-status is given")
    if args.repo_url or args.git_dir or args.base_url != parser.get_default("base_url"):
        parser.error("--repo-url/--git-dir/--base-url are only valid with --check-status")

    credentials = load_credentials()
    providers = _build_providers(list(args.providers), credentials)
    run = archive_publication(
        args.bundle,
        providers=providers,
        dry_run=not args.commit,
        output_receipts_path=args.receipts_out,
    )

    print(json.dumps(run.to_dict(), indent=2, sort_keys=True))
    return 0 if run.all_ok else 1


def _run_status_check(args: argparse.Namespace) -> int:
    """Execute the read-only status refresh and print the receipt."""
    if args.commit:
        raise SystemExit("--check-status performs no deposits; --commit is not valid")
    if args.providers != ["software_heritage"]:
        raise SystemExit("--check-status currently supports only: --providers software_heritage")
    sources = [flag for flag, value in (("--repo-url", args.repo_url), ("--git-dir", args.git_dir)) if value]
    if len(sources) != 1:
        raise SystemExit("--check-status requires exactly one of --repo-url or --git-dir")

    if args.repo_url:
        repo_url = args.repo_url.strip()
        if not repo_url.startswith(("http://", "https://", "git@")):
            raise SystemExit(f"--repo-url must be a repository URL, got {repo_url!r}")
    else:
        resolved = resolve_git_origin_url(args.git_dir)
        if resolved is None:
            raise SystemExit(f"Could not resolve an origin remote URL for {args.git_dir}")
        repo_url = resolved

    receipt = check_publication_status(repo_url, base_url=args.base_url)
    print(json.dumps(dataclasses.asdict(receipt), indent=2, sort_keys=True))
    return 0 if receipt.status == "ok" else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
