#!/usr/bin/env python3
"""Clean-copy a public template exemplar into a fork workspace."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.copy_exemplar import main


if __name__ == "__main__":
    raise SystemExit(main())
