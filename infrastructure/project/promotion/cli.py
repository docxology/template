"""CLI adapters for private-project promotion contracts."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from infrastructure.project.promotion.attestation import load_promotion_attestation
from infrastructure.project.promotion.security_gate import check_private_project_promotion, render_promotion_report


def build_parser() -> argparse.ArgumentParser:
    """Build the explicit promotion-contract parser."""
    parser = argparse.ArgumentParser(description="Validate private-project promotion evidence")
    sub = parser.add_subparsers(dest="command", required=True)

    attestation = sub.add_parser("attestation", help="Validate the orchestration attestation")
    attestation.add_argument("path", type=Path)
    attestation.add_argument("--as-of", type=date.fromisoformat, default=None)

    candidate = sub.add_parser("candidate", help="Validate a candidate checkout and security attestation")
    candidate.add_argument("--project-root", required=True, type=Path)
    candidate.add_argument("--attestation", type=Path, default=None)
    candidate.add_argument("--as-of", type=date.fromisoformat, default=None)
    candidate.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run an explicit subcommand or the compatible legacy positional form."""
    raw = list(argv) if argv is not None else sys.argv[1:]
    if raw and raw[0] not in {"attestation", "candidate"}:
        raw.insert(0, "attestation")
    args = build_parser().parse_args(raw)
    if args.command == "attestation":
        try:
            result = load_promotion_attestation(args.path, as_of=args.as_of)
        except ValueError as exc:
            print(json.dumps({"approved": False, "error": str(exc)}, sort_keys=True))
            return 1
        print(json.dumps(result.to_dict(), sort_keys=True))
        return 0

    report = check_private_project_promotion(
        args.project_root,
        attestation_path=args.attestation,
        as_of=args.as_of,
    )
    print(json.dumps(report.to_dict(), sort_keys=True) if args.json else render_promotion_report(report))
    return 0 if report.eligible else 1


__all__ = ["build_parser", "main"]
