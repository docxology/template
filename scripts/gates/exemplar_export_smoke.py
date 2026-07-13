#!/usr/bin/env python3
"""Clean-install and import-smoke every public exemplar export."""

from __future__ import annotations

import argparse
from pathlib import Path

from infrastructure.project.export_smoke import smoke_public_exemplars
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--project", action="append", choices=PUBLIC_PROJECT_NAMES)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args(argv)
    projects = tuple(args.project) if args.project else PUBLIC_PROJECT_NAMES
    results = smoke_public_exemplars(args.repo_root.resolve(), projects, timeout_seconds=args.timeout)
    for result in results:
        imports = ", ".join(result.import_targets)
        print(f"PASS {result.project_name}: {result.manifest_files} files; imports: {imports}")
    print(f"Clean export smoke passed for {len(results)} public exemplar(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
