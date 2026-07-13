#!/usr/bin/env python3
"""Connector Search stage bootstrap (opt-in via the ``science`` tag).

All Stage 08 application logic lives in
``infrastructure.search.connectors.stage``; this file only makes the repository
importable when invoked by path and delegates to that module.

Usage::

    uv run python scripts/pipeline/stage_08_connector_search.py --project <name>
    uv run python scripts/pipeline/stage_08_connector_search.py --project <name> --connector arxiv --query "active inference"

Exit codes:
    0: All searches completed successfully.
    1: An unrecoverable error occurred.
    2: Graceful skip — no connectors configured or project not found.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.search.connectors.stage import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
