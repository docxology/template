#!/usr/bin/env python3
"""Methods-plan gate — thin CLI over the canonical batch methods audit.

The static health runner uses source mode across all public exemplars. The
standalone default remains rendered mode so publication checks require the
``infrastructure.methods`` orchestrator validates a publication-critical
contract (every pipeline stage has a ``definition_of_done``, the manuscript
carries a methods/methodology section, and the artifact-manifest / evidence
registry surfaces exist) that nothing else enforces. This gate runs that
``plan --check`` validation for one project or every public exemplar and exits
non-zero when any blocking (``error``-severity) issue is found.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.methods import (  # noqa: E402
    audit_methods_projects,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES  # noqa: E402


def _check_project(project: str, repo_root: Path, *, artifact_mode: str = "rendered") -> int:
    """Validate one project's methods plan (mirrors ``plan --check``).

    Returns ``1`` when any ``error``-severity issue exists, ``0`` otherwise.
    Prints each blocking issue so the gate output is actionable without
    dumping the full plan markdown.
    """
    report = audit_methods_projects(repo_root, [project], artifact_mode=artifact_mode)
    errors = [issue for issue in report.projects[0].issues if issue.severity == "error"]
    for issue in errors:
        print(f"FAIL {project}: {issue.code} {issue.path}: {issue.message}")
    return 1 if errors else 0


def main(argv: list[str] | None = None) -> int:
    """Run the methods-plan gate (single project or all public exemplars)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root (defaults to the template repo root).",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--project",
        help="Single project under projects/ to check (e.g. templates/template_code_project).",
    )
    parser.add_argument(
        "--artifact-mode",
        choices=("source", "rendered"),
        default="rendered",
        help="Validate source contracts only or require rendered evidence artifacts.",
    )
    group.add_argument(
        "--all-public",
        action="store_true",
        help="Check every public template exemplar (default when --project is omitted).",
    )
    args = parser.parse_args(argv)

    projects = [args.project] if args.project else list(PUBLIC_PROJECT_NAMES)

    failures: list[str] = []
    for project in projects:
        try:
            exit_code = _check_project(project, args.repo_root, artifact_mode=args.artifact_mode)
        except KeyboardInterrupt:
            print("\nGate interrupted by user")
            return 130
        except (OSError, ValueError) as exc:
            print(f"FAIL {project}: methods gate crashed: {exc}")
            failures.append(project)
            continue
        if exit_code != 0:
            failures.append(project)

    if failures:
        print(f"\nFAIL methods-plan gate: {len(failures)} project(s) with blocking issues:")
        for project in failures:
            print(f"  - {project}")
        return 1

    print(f"OK methods-plan gate: {len(projects)} project(s) passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
