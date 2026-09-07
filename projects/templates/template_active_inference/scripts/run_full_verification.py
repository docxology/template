"""Run the full project verification flow in bounded, reproducible chunks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from orchestration.full_verification import run_coverage_only, run_verification


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-chunks",
        action="store_true",
        help="Skip chunked pre-pass runs and continue with coverage verification.",
    )
    parser.add_argument(
        "--monolithic-coverage",
        action="store_true",
        help="Use the legacy single pytest coverage process instead of chunked coverage subprocesses.",
    )
    parser.add_argument(
        "--coverage-only",
        action="store_true",
        help="Run only the coverage groups, omitting verifier-owned refresh and receipt phases.",
    )
    parser.add_argument(
        "--profile",
        choices=("quick", "release", "exhaustive"),
        default=None,
        help=(
            "Optionally select a typed pytest profile. Omitted preserves the historical full-verification selection."
        ),
    )
    args = parser.parse_args()
    if args.coverage_only and args.profile is None:
        parser.error("--coverage-only requires an explicit --profile")
    if args.coverage_only and (args.skip_chunks or args.monolithic_coverage):
        parser.error("--coverage-only cannot be combined with --skip-chunks or --monolithic-coverage")
    try:
        if args.coverage_only:
            run_coverage_only(PROJECT_ROOT, profile=args.profile)
        else:
            run_verification(
                PROJECT_ROOT,
                skip_chunks=args.skip_chunks,
                monolithic_coverage=args.monolithic_coverage,
                profile=args.profile,
            )
    except RuntimeError as exc:
        print(f"\nERROR: {exc}")
        return 1
    print("\nVerification workflow completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
