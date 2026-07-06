#!/usr/bin/env python3
"""Run a reproducible project × stage matrix declared in ``run.config``.

Thin orchestrator over :mod:`infrastructure.core.pipeline.run_matrix`. The
deterministic, version-controllable alternative to the interactive menu:

    uv run python scripts/runner/run_matrix.py                 # uses ./run.config
    uv run python scripts/runner/run_matrix.py --config my.yaml
    uv run python scripts/runner/run_matrix.py --dry-run        # print the plan, run nothing
    uv run python scripts/runner/run_matrix.py --fail-fast      # stop at first failure

Exit code is 0 only if every (project, stage) step succeeded.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger  # noqa: E402
from infrastructure.core.pipeline.run_matrix import (  # noqa: E402
    RunConfigError,
    execute_run_plan,
    find_run_config,
    format_report,
    parse_run_config,
    resolve_run_plan,
)

logger = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=None, help="Path to run.config (default: ./run.config[.yaml])")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved plan and exit without running")
    parser.add_argument("--fail-fast", action="store_true", help="Stop at the first failing stage")
    parser.add_argument("--repo-root", type=Path, default=None, help="Repository root (default: auto-detected)")
    ns = parser.parse_args(argv)

    repo_root = (ns.repo_root or Path(__file__).resolve().parent.parent).resolve()
    config_path = ns.config or find_run_config(repo_root)
    if config_path is None:
        print("ERROR: no run.config found (looked for run.config, run.config.yaml).", file=sys.stderr)
        print("Create one — see docs/RUN_GUIDE.md, or run.config.example.yaml.", file=sys.stderr)
        return 2
    if not config_path.is_file():
        print(f"ERROR: run.config not found at {config_path}", file=sys.stderr)
        return 2

    try:
        config = parse_run_config(config_path.read_text(encoding="utf-8"))
        plan = resolve_run_plan(config, repo_root)
    except RunConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not plan.steps:
        print("run.config resolved to zero steps — nothing to run.")
        return 0

    print(f"Resolved {len(plan.steps)} step(s) from {config_path.name}:")
    for step in plan.steps:
        print(f"  {step.project} · {step.stage}")
    for warning in plan.warnings:
        print(f"  warning: {warning}", file=sys.stderr)

    if ns.dry_run:
        print("--dry-run: not executing.")
        return 0

    results = execute_run_plan(plan, repo_root, fail_fast=ns.fail_fast)
    print(format_report(results))
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
