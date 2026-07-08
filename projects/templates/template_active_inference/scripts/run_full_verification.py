"""Run the full project verification flow in bounded, reproducible chunks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from orchestration.full_verification import run_verification


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
    args = parser.parse_args()
    try:
        run_verification(
            PROJECT_ROOT,
            skip_chunks=args.skip_chunks,
            monolithic_coverage=args.monolithic_coverage,
        )
    except RuntimeError as exc:
        print(f"\nERROR: {exc}")
        return 1
    print("\nVerification workflow completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
