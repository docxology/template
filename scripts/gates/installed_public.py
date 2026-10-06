#!/usr/bin/env python3
"""Build and execute source-bound installed wheels outside public source checkouts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from infrastructure.project.installed_acceptance import run_installed_acceptance
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--python", action="append", default=[], metavar="MINOR=EXECUTABLE")
    parser.add_argument("--project", action="append", choices=("root", *PUBLIC_PROJECT_NAMES))
    parser.add_argument("--project-workers", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args(argv)
    interpreters = {}
    for item in args.python:
        minor, separator, path = item.partition("=")
        if not separator or not path or minor in interpreters:
            parser.error("--python requires one unique MINOR=EXECUTABLE per selected runtime")
        interpreters[minor] = Path(path)
    report = run_installed_acceptance(
        args.repo_root,
        interpreters,
        projects=args.project,
        project_workers=args.project_workers,
        timeout_seconds=args.timeout,
        evidence_dir=args.evidence_dir,
    )
    print(
        json.dumps(
            {
                "receipt": report["receipt"],
                "matrix": report["installed_matrix"]["counts"],
                "source_current": report["installed_matrix"]["source_current"],
            },
            sort_keys=True,
        )
    )
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
