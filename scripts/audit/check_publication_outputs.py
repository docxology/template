#!/usr/bin/env python3
"""Sharded, parallel publication-output gate over the per-project audit.

Replaces a single all-public audit call with a selectable, shardable roster:

    # one project
    uv run python scripts/audit/check_publication_outputs.py --project templates/template_code_project
    # affected projects only, fast lane (shared changes widen to the full roster)
    uv run python scripts/audit/check_publication_outputs.py --changed --jobs 4
    # show the resolved roster without auditing
    uv run python scripts/audit/check_publication_outputs.py --changed --dry-run
    # release lane: every project, strict severity, one CI matrix shard
    uv run python scripts/audit/check_publication_outputs.py --all-public --strict --shard 0/4 --receipts receipts/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from infrastructure.validation.publication.gate import (  # noqa: E402
    GateMode,
    ProjectSelection,
    PublicationGateReport,
    changed_project_paths,
    format_gate_report,
    resolve_selection,
    run_publication_gate,
    shard_projects,
    write_receipts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--project", action="append", dest="projects", default=[], metavar="QUALIFIED_NAME")
    parser.add_argument("--all-public", action="store_true", help="Audit the whole canonical public roster.")
    parser.add_argument(
        "--changed", action="store_true", help="Restrict to projects with working-tree changes; shared changes widen."
    )
    parser.add_argument("--shard", metavar="INDEX/COUNT", help="Run one disjoint slice of the selection.")
    parser.add_argument("--strict", action="store_true", help="Fail on review_required findings as well as errors.")
    parser.add_argument("--jobs", type=int, default=1, help="Projects audited in parallel (default: 1).")
    parser.add_argument("--receipts", type=Path, help="Write one JSON receipt per audited project here.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print the resolved roster and selection reason without auditing."
    )
    args = parser.parse_args(argv)

    try:
        changed = changed_project_paths(args.repo_root) if args.changed else None
        selection = resolve_selection(projects=tuple(args.projects), all_public=args.all_public, changed=changed)
        if args.shard:
            selection = ProjectSelection(
                shard_projects(selection.projects, args.shard),
                f"{selection.reason}; shard {args.shard}",
                selection.widened,
            )
    except ValueError as error:
        parser.error(str(error))
    if args.dry_run:
        print(f"selection: {len(selection.projects)} project(s) ({selection.reason})")
        for name in selection.projects:
            print(name)
        return 0
    mode: GateMode = "strict" if args.strict else "blocking"
    if not selection.projects:
        print(
            format_gate_report(
                PublicationGateReport(mode=mode, results=(), selection=selection),
            )
        )
        return 0
    if args.jobs < 1:
        parser.error("--jobs must be a positive integer")

    report = run_publication_gate(
        args.repo_root,
        selection.projects,
        mode=mode,
        jobs=args.jobs,
        selection=selection,
    )
    print(format_gate_report(report))
    if args.receipts is not None:
        written = write_receipts(report, args.receipts)
        print(f"receipts: {len(written)} written to {args.receipts}")
    return 0 if not report.failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
