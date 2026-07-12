#!/usr/bin/env python3
"""Thin entrypoint for the repository mock-policy audit.

The default lexical gate and the advisory ``--inventory`` mode live in
``infrastructure.validation.output.no_mock_audit``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.validation.output.no_mock_audit import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
