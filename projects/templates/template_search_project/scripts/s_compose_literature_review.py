#!/usr/bin/env python3
"""Compose current deep-search output into a generated supplemental section.

Requires output/deep_search/producer_receipt.json with matching current disk
source/configuration and exact producer artifact bytes. This dependency record
is separate from audited unpaid-provider acceptance. Missing or stale custody
fails with exit1; absent deep output skips with exit2.

The default writes output/manuscript/S02_generated_literature_review.md plus
output/deep_search/composition_summary.json. The variable hydrator preserves the
generated supplement and projects extra citations from output/bibliography into
output/manuscript/generated_search.bib. Authored markdown and curated references
remain unchanged. Explicit --output authoring is available only through direct
invocation; this script is outside the default core analysis allowlist.

All parsing, validation, assembly, and artifact writes live in the project src
module; this script wires argparse and configuration to that implementation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
# Select the declared SDK before exposing domain source; no ancestor imports.
_original_import_paths = sys.path[:]
try:
    sys.path.insert(0, str(_project_root / "scripts"))
    from _search_sdk_bootstrap import select_platform_sdk

    select_platform_sdk(_project_root)
finally:
    sys.path[:] = _original_import_paths
sys.path.insert(0, str(_project_root / "src"))

from template_search_project.pipeline.composition import compose_literature_review
from template_search_project.publish.config import load_project_config
from template_search_project.pipeline.dotenv import load_dotenv

load_dotenv(_project_root / ".env")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--config",
        default=str(_project_root / "manuscript" / "config.yaml"),
    )
    parser.add_argument(
        "--project-root",
        default=str(_project_root),
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output markdown path (defaults to output/manuscript/S02_generated_literature_review.md).",
    )
    parser.add_argument("--enable", action="store_true", help="Match an explicit deep-producer --enable override.")
    parser.add_argument("--keyword", action="append", help="Match the producer's explicit keyword list.")
    parser.add_argument("--no-llm", action="store_true", help="Match an explicit deep-producer --no-llm override.")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).absolute()
    config = load_project_config(args.config)
    if args.enable:
        config.deep_search.enabled = True
    if args.keyword:
        config.deep_search.keywords = list(args.keyword)
    if args.no_llm:
        config.deep_search.llm_per_paper = False
    return compose_literature_review(project_root, config, args.output)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
