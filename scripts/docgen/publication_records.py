#!/usr/bin/env python3
"""Write publication record documentation for the public template exemplars."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from infrastructure.core.logging.utils import get_logger, log_header, log_success  # noqa: E402
from infrastructure.documentation.publication_records import (  # noqa: E402
    check_publication_records_doc,
    write_publication_records_doc,
)

logger = get_logger(__name__)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-external",
        action="store_true",
        help="Refresh GitHub and Zenodo status columns from public APIs.",
    )
    parser.add_argument(
        "--skip-github-readme",
        action="store_true",
        help="Write only docs/_generated/publication_records.md.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check generated publication docs without writing files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    log_header("Generate Publication Records Documentation", logger)
    if args.check:
        differences = check_publication_records_doc(
            REPO_ROOT,
            refresh_external=args.refresh_external,
            update_github_readme=not args.skip_github_readme,
        )
        if differences:
            for difference in differences:
                print(difference, file=sys.stderr)
            return 1
        log_success("publication_records.md: OK (in sync with public exemplar metadata)")
        return 0
    out_path, readme_path = write_publication_records_doc(
        REPO_ROOT,
        refresh_external=args.refresh_external,
        update_github_readme=not args.skip_github_readme,
    )
    log_success(f"Wrote {out_path}")
    if readme_path is not None:
        log_success(f"Updated {readme_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
