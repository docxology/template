#!/usr/bin/env python3
"""Run all canonical public exemplar tests in isolated subprocesses."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from infrastructure.core.pytest_orchestration import TEST_PROFILE_NAMES, parse_project_workers
from infrastructure.project.public_readiness import (
    DEFAULT_TIMEOUT_SECONDS,
    format_public_readiness,
    run_public_readiness,
)


def _positive_int(raw: str) -> int:
    """Parse a strictly positive integer for a subprocess timeout."""
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return value


def _project_workers(raw: str) -> int:
    """Parse the outer project-matrix worker count."""
    try:
        return parse_project_workers(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def main(argv: list[str] | None = None) -> int:
    """Execute the public readiness gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--timeout", type=_positive_int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--profile", choices=TEST_PROFILE_NAMES, default="release")
    parser.add_argument(
        "--project-workers",
        type=_project_workers,
        default=1,
        help="Bounded outer project concurrency; use 'serial' for one worker.",
    )
    parser.add_argument(
        "--include-ollama-tests",
        action="store_true",
        help="Include tests requiring a running Ollama service.",
    )
    parser.add_argument(
        "--allow-skips",
        action="store_true",
        help="Report skips without failing; use only for explicitly optional service lanes.",
    )
    parser.add_argument("--json", action="store_true", help="Emit the machine-readable report.")
    args = parser.parse_args(argv)

    report = run_public_readiness(
        args.repo_root,
        timeout_seconds=args.timeout,
        include_ollama_tests=args.include_ollama_tests,
        profile=args.profile,
        project_workers=args.project_workers,
    )
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_public_readiness(report))
    return report.exit_code(allow_skips=args.allow_skips)


if __name__ == "__main__":
    raise SystemExit(main())
