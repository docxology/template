"""Offline exact-wheel installation smoke; publication is verified separately."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.publishing.pypi_release import TestPyPIError, verify_candidate_wheel  # noqa: E402


def main() -> int:
    """Require explicit original artifact custody instead of an unpinned index."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--sha256", required=True, help="original admitted wheel SHA-256")
    parser.add_argument("--timeout-seconds", type=float, default=600)
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                verify_candidate_wheel(
                    args.wheel, args.sha256, repo_root=REPO_ROOT, timeout_seconds=args.timeout_seconds
                ),
                sort_keys=True,
            )
        )
    except TestPyPIError as exc:
        print(f"Installed smoke {exc.state}: {exc}", file=sys.stderr)
        return exc.exit_code
    except (ValueError, TypeError) as exc:
        print(f"Invalid installed smoke invocation/configuration: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"Installed smoke failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
