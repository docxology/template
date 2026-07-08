#!/usr/bin/env python3
"""Thin orchestrator: fail when a package's AGENTS.md omits public modules.

Logic lives in ``infrastructure.validation.docs.module_coverage``. This gate
complements the doc-pair linter (which only checks the AGENTS.md/README.md pair
exists) by checking the docs actually enumerate the functional modules.

Exit codes:
    0: every package's public modules are referenced in its folder docs
    1: at least one package has undocumented public modules
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.validation.docs.module_coverage import (  # noqa: E402
    CODE_DOC_ROOTS,
    find_module_doc_gaps,
)


def main(argv: list[str] | None = None) -> int:
    """Report packages whose AGENTS.md omits public modules."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root to scan (default: this checkout).",
    )
    parser.add_argument(
        "--root",
        dest="roots",
        action="append",
        help=(f"Restrict scanning to this top-level root (repeatable). Default: {', '.join(CODE_DOC_ROOTS)}."),
    )
    args = parser.parse_args(argv)

    roots = tuple(args.roots) if args.roots else CODE_DOC_ROOTS
    gaps = find_module_doc_gaps(args.repo_root, roots=roots)

    if not gaps:
        print("module-doc-coverage: all public modules referenced in their package docs")
        return 0

    missing_total = sum(len(gap.undocumented) for gap in gaps)
    print(f"module-doc-coverage: {missing_total} undocumented public module(s) across {len(gaps)} package(s):")
    for gap in gaps:
        print(f"  {gap.format()}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
