"""TestPyPI upload and installation verification orchestrator."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# The wheel ships only `infrastructure` ([tool.hatch.build.targets.wheel]
# packages), so `scripts/` is never installed into the venv; each script must put
# the repo root on sys.path before importing `infrastructure`. This file lives two
# levels below the root (scripts/publish/).
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.publishing.pypi_release import TestPyPIError, _redact, run_test_pypi_release  # noqa: E402


def main() -> int:
    """Run the TestPyPI release verification flow."""
    parser = argparse.ArgumentParser(description="Explicit TestPyPI sandbox transfer and exact installed smoke")
    parser.add_argument("--timeout-seconds", type=float, default=600)
    args = parser.parse_args()
    token = os.environ.get("TEST_PYPI_API_TOKEN", "")
    try:
        run_test_pypi_release(token, repo_root=REPO_ROOT, timeout_seconds=args.timeout_seconds)
    except TestPyPIError as exc:
        print(_redact(f"TestPyPI {exc.state}: {exc}", (token,)), file=sys.stderr)
        return exc.exit_code
    except (ValueError, TypeError) as exc:
        print(_redact(f"Invalid TestPyPI invocation/configuration: {exc}", (token,)), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("TestPyPI interrupted", file=sys.stderr)
        return 130
    except Exception as exc:
        print(_redact(f"TestPyPI failed: {exc}", (token,)), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
