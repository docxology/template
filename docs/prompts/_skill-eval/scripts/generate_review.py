#!/usr/bin/env python3
"""Generate static review.html for a skill-eval iteration directory."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from skill_eval.review import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
