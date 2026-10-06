"""Run the full project verification flow in bounded, reproducible chunks."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _run_cli() -> int:
    """CLI entry point."""
    from orchestration.full_verification import run_coverage_only, run_verification
    from orchestration.verification_execution import (
        VerificationCommandFailed,
        VerificationDeadlineExceeded,
        VerificationRuntimeUnavailable,
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-chunks",
        action="store_true",
        help="Skip chunked pre-pass runs and continue with coverage verification.",
    )
    parser.add_argument(
        "--monolithic-coverage",
        action="store_true",
        help="Use one pytest coverage process instead of chunked coverage subprocesses.",
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
    except KeyboardInterrupt:
        print("\nINTERRUPTED: verification stopped by the controller")
        return 130
    except VerificationCommandFailed as exc:
        print(f"\nFAILED: {exc}")
        return exc.exit_code
    except VerificationRuntimeUnavailable as exc:
        print(f"\nBLOCKED: {exc}")
        return 75
    except VerificationDeadlineExceeded as exc:
        print(f"\nTIMEOUT: {exc}")
        return 124
    except RuntimeError as exc:
        print(f"\nERROR: {exc}")
        return 1
    except ValueError as exc:
        print(f"\nINVALID: {exc}")
        return 2
    print("\nVerification workflow completed successfully.")
    return 0


def main() -> int:
    """Import the controller from a fresh private cache before audited children."""
    prior = sys.pycache_prefix
    try:
        with tempfile.TemporaryDirectory(prefix="template-active-verifier-controller-") as temporary:
            sys.pycache_prefix = str(Path(temporary).resolve())
            return _run_cli()
    finally:
        sys.pycache_prefix = prior


if __name__ == "__main__":
    raise SystemExit(main())
