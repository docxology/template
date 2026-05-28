#!/usr/bin/env python3
"""Write publication record documentation for the public template exemplars."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from infrastructure.core.logging.utils import get_logger, log_header, log_success  # noqa: E402
from infrastructure.documentation.publication_records import write_publication_records_doc  # noqa: E402

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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    log_header("Generate Publication Records Documentation", logger)
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
