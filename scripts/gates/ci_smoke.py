#!/usr/bin/env python3
"""Emit or run the explicitly scoped public functional CI selection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from infrastructure.core.testing.ci_smoke import project_smoke_matrix, run_project_smoke  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--matrix", action="store_true")
    operation.add_argument("--project")
    args = parser.parse_args()
    if args.matrix:
        print(json.dumps(project_smoke_matrix(REPO), separators=(",", ":")))
        return 0
    return run_project_smoke(REPO, args.project)


if __name__ == "__main__":
    raise SystemExit(main())
