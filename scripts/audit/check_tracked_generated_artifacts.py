#!/usr/bin/env python3
"""Generated-artifact guard — thin CLI over infrastructure.project.git_guards."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.git_guards import (  # noqa: E402
    public_template_output_budget_findings,
    tracked_generated_artifacts,
    tracked_public_output_local_paths,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    offenders = tracked_generated_artifacts(repo_root)
    local_paths = tracked_public_output_local_paths(repo_root)
    budget_findings = public_template_output_budget_findings(repo_root)
    if not offenders and not local_paths and not budget_findings:
        print("No prohibited generated artifacts or canonical evidence-budget violations found.")
        return 0

    if offenders:
        print(
            "Tracked generated/local artifacts or oversized public template outputs found; "
            "untrack them with `git rm --cached`:"
        )
        for path in offenders:
            print(f"  {path}")
    if local_paths:
        print("Tracked public exemplar outputs contain machine-local home paths; regenerate or sanitize them:")
        for path in local_paths:
            print(f"  {path}")
    if budget_findings:
        print("Canonical project-local output budgets exceeded:")
        for finding in budget_findings:
            print(f"  {finding}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
