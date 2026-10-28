#!/usr/bin/env python3
"""Sharded, parallel publication-output gate over the per-project audit.

Replaces a single all-public audit call with a selectable, shardable roster:

    # one project
    uv run python scripts/audit/check_publication_outputs.py --project templates/template_code_project
    # affected projects only, fast lane
    uv run python scripts/audit/check_publication_outputs.py --changed --jobs 4
    # release lane: every project, strict severity, one CI matrix shard
    uv run python scripts/audit/check_publication_outputs.py --all-public --strict --shard 0/4 --receipts receipts/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from infrastructure.validation.publication.gate import (  # noqa: E402
    changed_project_paths,
    format_gate_report,
    run_publication_gate,
    select_projects,
    shard_projects,
    write_receipts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--project", action="append", dest="projects", default=[], metavar="QUALIFIED_NAME")
    parser.add_argument("--all-public", action="store_true", help="Audit the whole canonical public roster.")
    parser.add_argument("--changed", action="store_true", help="Restrict to projects with working-tree changes.")
    parser.add_argument("--shard", metavar="INDEX/COUNT", help="Run one disjoint slice of the selection.")
    parser.add_argument("--strict", action="store_true", help="Fail on review_required findings as well as errors.")
    parser.add_argument("--jobs", type=int, default=1, help="Projects audited in parallel (default: 1).")
    parser.add_argument("--receipts", type=Path, help="Write one JSON receipt per audited project here.")
    args = parser.parse_args(argv)

    try:
        changed = changed_project_paths(args.repo_root) if args.changed else ()
        selected = select_projects(projects=tuple(args.projects), all_public=args.all_public, changed=changed)
        if args.shard:
            selected = shard_projects(selected, args.shard)
    except ValueError as error:
        parser.error(str(error))
    if not selected:
        print("publication outputs: no project selected; nothing to audit")
        return 0
    if args.jobs < 1:
        parser.error("--jobs must be a positive integer")

    report = run_publication_gate(
        args.repo_root,
        selected,
        mode="strict" if args.strict else "blocking",
        jobs=args.jobs,
    )
    print(format_gate_report(report))
    if args.receipts is not None:
        written = write_receipts(report, args.receipts)
        print(f"receipts: {len(written)} written to {args.receipts}")
    return 0 if not report.failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
