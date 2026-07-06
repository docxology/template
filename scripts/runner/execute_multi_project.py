#!/usr/bin/env python3
"""Execute multi-project orchestration (thin wrapper)."""

from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from infrastructure.core.pipeline.multi_project_cli import main

if __name__ == "__main__":
    sys.exit(main(repo_root=repo_root))
