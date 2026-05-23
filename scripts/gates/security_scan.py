#!/usr/bin/env python3
"""Security scanning gate — thin CLI over infrastructure.validation.security_gate."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.validation.security_gate import run_security_scan  # noqa: E402


def main() -> int:
    try:
        _report, exit_code = run_security_scan(REPO_ROOT)
        return exit_code
    except KeyboardInterrupt:
        print("\nGate interrupted by user")
        return 130
    except OSError as exc:
        print(f"FATAL: Security gate crashed: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
