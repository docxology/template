#!/usr/bin/env python3
"""Validate the complete public claim-binding inventory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.validation.claims import build_claim_binding_receipt, validate_claim_bindings  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Run the claim-binding gate and print its deterministic receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=REPO_ROOT / "tests/regression/claim_bindings.json")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a compact status line.")
    args = parser.parse_args(argv)
    report = validate_claim_bindings(REPO_ROOT, args.manifest)
    receipt = build_claim_binding_receipt(report)
    payload = receipt.to_dict()
    summary = report.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"claim bindings: projects={summary['project_count']} bound={summary['bound_count']} "
            f"not_applicable={summary['not_applicable_count']} external_data={summary['external_data_count']} "
            f"status={summary['status']} digest={receipt.manifest_sha256}"
        )
        for error in report.errors:
            print(f"ERROR {error}")
    return 0 if not report.errors else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
