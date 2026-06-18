"""Run the full project verification flow in bounded, reproducible chunks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from orchestration.full_verification import run_verification


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-chunks",
        action="store_true",
        help="Skip chunked pre-pass runs and jump directly to the full-suite pass.",
    )
    args = parser.parse_args()
    try:
        run_verification(PROJECT_ROOT, skip_chunks=args.skip_chunks)
    except RuntimeError as exc:
        print(f"\nERROR: {exc}")
        return 1
    print("\nVerification workflow completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
