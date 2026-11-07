"""Read one complete ARL original cell; never aggregate or authorize publication."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
import time

from infrastructure.project.public_acceptance_evidence import MissingAuxiliaryProvider, write_json
from infrastructure.project.public_acceptance_literature_group import validate_invocation


def main() -> int:
    """Independently inspect original bytes inside a fresh finite reader budget."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    args = parser.parse_args()
    if not 1 <= args.timeout_seconds <= 600:
        parser.error("reader timeout must be within [1, 600]")
    root = args.repo_root.resolve(strict=True)
    deadline = time.monotonic() + args.timeout_seconds
    receipt = args.receipt if args.receipt.is_absolute() else root / args.receipt
    output = args.output if args.output.is_absolute() else root / args.output
    if os.path.lexists(output):
        parser.error("diagnostic output must be a new unoccupied readiness path")
    try:
        result = validate_invocation(root, receipt, deadline)
        if time.monotonic() >= deadline:
            raise TimeoutError("literature independent reader deadline exhausted before positive publication")
    except (OSError, ValueError, TypeError, KeyError, TimeoutError, MissingAuxiliaryProvider) as error:
        result = {
            "schema_version": "template-arl-capability-diagnostic-v1",
            "status": "failed",
            "diagnostic": str(error),
            "aggregate_acceptance_granted": False,
            "release_authorized": False,
        }
    if os.path.lexists(output):
        parser.error("diagnostic output became occupied during readback; preserving it")
    if result["status"] == "passed" and time.monotonic() >= deadline:
        result = {
            "schema_version": "template-arl-capability-diagnostic-v1",
            "status": "failed",
            "diagnostic": "literature independent reader deadline exhausted before positive publication",
            "aggregate_acceptance_granted": False,
            "release_authorized": False,
        }
    binding = write_json(root, output, result)
    sys.stdout.write(json.dumps({**result, "receipt": binding}, sort_keys=True) + "\n")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
