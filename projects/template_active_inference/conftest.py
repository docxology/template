"""Project pytest configuration — ensure local src and pymdp env."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC = PROJECT_ROOT / "src"
TESTS = PROJECT_ROOT / "tests"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

os.environ.setdefault("MPLBACKEND", "Agg")

# Prefer this project's venv site-packages when root pytest delegates here.
VENV_SITE = PROJECT_ROOT / ".venv" / "lib"
if VENV_SITE.is_dir():
    for site in sorted(VENV_SITE.glob("python*/site-packages")):
        site_str = str(site)
        if site_str not in sys.path:
            sys.path.insert(0, site_str)
