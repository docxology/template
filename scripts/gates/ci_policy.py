#!/usr/bin/env python3
"""Emit the source-owned complete CI aggregate job selection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from infrastructure.core.ci_policy import required_ci_jobs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--workflow", choices=("ci.yml", "hardening.yml"), default="ci.yml")
    args = parser.parse_args()
    try:
        jobs = required_ci_jobs(args.repo_root, args.workflow)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(jobs, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
