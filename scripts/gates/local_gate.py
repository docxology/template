#!/usr/bin/env python3
"""One local entry point for the commands CI runs, offline by default.

The stage definitions live in ``infrastructure.core.testing.local_gate`` so this
file stays a thin orchestrator; see that module for the stage semantics.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from infrastructure.core.testing.local_gate import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
