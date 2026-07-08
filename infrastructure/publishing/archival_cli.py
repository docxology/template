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
    load_credentials,
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
        required=True,
        help="Path to the publication bundle (directory or single file)",
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


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
