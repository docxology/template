"""Source-bound root runtime cells; unresolved root case policy blocks execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from infrastructure.project.public_acceptance_cli import interpreter, positive_int
from infrastructure.project.public_acceptance_scope import MissingRootCasePolicy
from infrastructure.project.public_root_case_acceptance import run_root_case_acceptance


def run_root_acceptance(
    root: Path,
    interpreters: Mapping[str, Path],
    *,
    evidence_dir: Path | None = None,
    timeout_seconds: int = 7200,
    test_timeout_seconds: int = 120,
    mode: str = "core",
) -> dict[str, Any]:
    """Execute the complete source-owned case policy through its current producer."""
    return run_root_case_acceptance(
        root,
        interpreters,
        evidence_dir=evidence_dir,
        mode=mode,
        timeout_seconds=timeout_seconds,
        test_timeout_seconds=test_timeout_seconds,
    )


def main(argv: list[str] | None = None) -> int:
    """Run prepared supported interpreters; policy/tool blockers are explicit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--python", action="append", type=interpreter, default=[])
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--timeout", type=positive_int, default=7200)
    parser.add_argument("--test-timeout", type=positive_int, default=120)
    parser.add_argument("--mode", choices=("core", "live"), default="core")
    args = parser.parse_args(argv)
    if len(dict(args.python)) != len(args.python):
        parser.error("each root runtime may select only one prepared interpreter")
    try:
        result = run_root_acceptance(
            args.repo_root,
            dict(args.python),
            evidence_dir=args.evidence_dir,
            timeout_seconds=args.timeout,
            test_timeout_seconds=args.test_timeout,
            mode=args.mode,
        )
    except RuntimeError:
        return 1
    except MissingRootCasePolicy:
        print(json.dumps({"exit_code": 75, "diagnostic": "required source-owned Root case policy is unavailable"}))
        return 75
    except (OSError, ValueError, TypeError, KeyError):
        parser.error("Root acceptance source-owned invocation/configuration is invalid")
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
