#!/usr/bin/env python3
"""Sync public exemplars into their standalone publication repositories.

Thin orchestrator: all behaviour lives in
:mod:`infrastructure.publishing.standalone_mirror`, which documents the two
properties that matter (update-only, and symlink dereferencing) and why.

Dry-run by default — reviewing the per-repository delta before touching a public
repository is the point.

USAGE (from the repo root)::

    uv run python scripts/publish/sync_standalone_mirrors.py
    uv run python scripts/publish/sync_standalone_mirrors.py --project template_formal
    uv run python scripts/publish/sync_standalone_mirrors.py --commit
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.public_scope import public_project_names  # noqa: E402
from infrastructure.publishing._standalone_mirror_source import clean_source_revision  # noqa: E402
from infrastructure.publishing.standalone_install_projection import GitInstallProvider  # noqa: E402
from infrastructure.publishing.standalone_mirror import sync_exemplar  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Report or apply standalone-mirror syncs for the public exemplars."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--commit", action="store_true", help="perform real commits and pushes")
    parser.add_argument("--project", help="limit to a single exemplar name")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--resources-only", action="store_true", help="refresh only the declared mirror resources")
    mode.add_argument(
        "--install-projection",
        action="store_true",
        help="review or publish an explicitly Git-pinned installation projection",
    )
    parser.add_argument("--meta-provider", type=Path, help="prepared canonical Meta standalone checkout for Advanced")
    parser.add_argument("--meta-commit", help="existing full Meta provider commit")
    parser.add_argument("--removal-plan", type=Path, help="reviewed publication removal plan JSON")
    parser.add_argument("--reviewed-plan-sha256", help="SHA-256 of the exact reviewed plan")
    parser.add_argument("--quarantine-root", type=Path, help="existing directory for retained removed files")
    args = parser.parse_args(argv)
    removal_args = (args.removal_plan, args.reviewed_plan_sha256, args.quarantine_root)
    removal_plan = None
    if any(value is not None for value in removal_args):
        if not all(removal_args) or not args.commit or not args.project:
            parser.error("reviewed removal requires all three options, --project and --commit")
        try:
            removal_plan = json.loads(args.removal_plan.read_bytes())
        except (OSError, ValueError) as error:
            parser.error(f"cannot read the publication removal plan: {error}")
        if not isinstance(removal_plan, dict):
            parser.error("the publication removal plan must be a JSON object")
    if bool(args.meta_provider) != bool(args.meta_commit) or (args.meta_provider and not args.install_projection):
        parser.error("--meta-provider and --meta-commit require each other and --install-projection")
    meta = GitInstallProvider(args.meta_provider.absolute(), args.meta_commit) if args.meta_provider else None

    try:
        revision = clean_source_revision(REPO_ROOT)
    except (ValueError, RuntimeError):
        print("REFUSING: source HEAD and a clean monorepo must be verified before synchronization.", file=sys.stderr)
        return 1

    qualified = [name for name in public_project_names(REPO_ROOT) if name.startswith("templates/")]
    names = [args.project] if args.project else [name.split("/", 1)[1] for name in qualified]

    print(f"source: {revision} | exemplars: {len(names)} | mode: {'COMMIT' if args.commit else 'DRY-RUN'}\n")
    results = []
    for name in names:
        result = sync_exemplar(
            REPO_ROOT,
            name,
            commit=args.commit,
            source_revision=revision,
            install_projection=args.install_projection,
            meta_provider=meta,
            resources_only=args.resources_only,
            removal_plan=removal_plan,
            reviewed_plan_sha256=args.reviewed_plan_sha256,
            quarantine_root=args.quarantine_root,
        )
        results.append(result)
        delta = f" (+{result.added} ~{result.modified} -{result.deleted})" if result.changed else ""
        print(f"  {name:42} {result.status}{delta}")
        if result.install_projection_sha256 or result.export_kind == "resources" and result.source_export_sha256:
            print(f"  source-export-sha256: {result.source_export_sha256}")
        if result.install_projection_sha256:
            print(f"  install-projection-sha256: {result.install_projection_sha256}")
        if result.status.startswith("REVIEW REQUIRED"):
            print(f"  removal-plan-sha256: {result.removal_plan_sha256}")
            print(json.dumps(result.removal_plan, sort_keys=True, indent=2))
        sys.stdout.flush()

    print()
    accepted = ("SYNCED", "WOULD SYNC", "up to date", "SKIP: no declared resources")
    for status in accepted:
        count = sum(1 for result in results if result.status == status)
        if count:
            print(f"  {status}: {count}")
    problems = [r for r in results if r.status not in accepted]
    for result in problems:
        print(f"  PROBLEM {result.exemplar}: {result.status}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
