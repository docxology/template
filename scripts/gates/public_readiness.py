#!/usr/bin/env python3
"""Run all canonical public exemplar tests in isolated subprocesses."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from infrastructure.core.testing.pytest_orchestration import TEST_PROFILE_NAMES
from infrastructure.project.public_acceptance_cli import (
    interpreter as _interpreter,
    positive_int as _positive_int,
    project_workers as _project_workers,
    provider_wheel as _provider_wheel,
)
from infrastructure.project.public_readiness import (
    DEFAULT_TIMEOUT_SECONDS,
    format_public_readiness,
    run_public_readiness,
)
from infrastructure.project.public_acceptance import run_public_acceptance


def main(argv: list[str] | None = None) -> int:
    """Execute the public readiness gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--timeout",
        type=_positive_int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Outer seconds per project (default: {DEFAULT_TIMEOUT_SECONDS}); an explicit value overrides the Stage01 allowance.",
    )
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
        help="Allow explicitly skipped projects; individual test skips remain in Stage01 summaries.",
    )
    parser.add_argument("--json", action="store_true", help="Emit the machine-readable report.")
    parser.add_argument(
        "--acceptance-matrix",
        action="store_true",
        help="Run source-bound whole-collection tests and branch coverage across all supported runtimes.",
    )
    parser.add_argument("--python", action="append", type=_interpreter, default=[], metavar="MINOR=/PATH/bin/python")
    parser.add_argument(
        "--provider-wheel", action="append", type=_provider_wheel, default=[], metavar="SCOPE=/PATH/provider.whl"
    )
    parser.add_argument(
        "--project",
        action="append",
        help="Diagnostic canonical project subset; a subset never grants complete-matrix acceptance.",
    )
    parser.add_argument(
        "--evidence-dir", type=Path, help="Fresh receipt directory below this repository's output/readiness."
    )
    parser.add_argument(
        "--test-timeout",
        type=_positive_int,
        default=120,
        help="Finite default pytest item deadline; source-owned per-test limits still apply.",
    )
    args = parser.parse_args(argv)

    if args.acceptance_matrix:
        if args.allow_skips or args.profile != "release" or args.include_ollama_tests:
            parser.error("acceptance matrix uses whole selection and cannot allow skips or marker-profile exclusions")
        if len(dict(args.python)) != len(args.python):
            parser.error("each runtime may select only one interpreter")
        if len(dict(args.provider_wheel)) != len(args.provider_wheel):
            parser.error("each declared provider may bind only one current wheel")
        report_payload = run_public_acceptance(
            args.repo_root,
            dict(args.python),
            timeout_seconds=args.timeout,
            test_timeout_seconds=args.test_timeout,
            project_workers=args.project_workers,
            projects=args.project,
            evidence_dir=args.evidence_dir,
            provider_wheels=dict(args.provider_wheel),
        )
        print(json.dumps(report_payload, indent=2, sort_keys=True))
        return int(report_payload["exit_code"])
    if args.python or args.project or args.evidence_dir or args.provider_wheel:
        parser.error("--python, --project, --provider-wheel and --evidence-dir require --acceptance-matrix")

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
