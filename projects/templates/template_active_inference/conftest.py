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
# Only add a site-packages directory built for the *running* interpreter's
# Python version; a venv built for a different version (e.g. a standalone
# 3.14 venv picked up by a 3.12 repo run) ships incompatible C-extensions
# (numpy's _multiarray_umath) and would break import on a version mismatch.
VENV_SITE = PROJECT_ROOT / ".venv" / "lib"
if VENV_SITE.is_dir():
    _pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site = VENV_SITE / _pyver / "site-packages"
    if site.is_dir():
        site_str = str(site)
        if site_str not in sys.path:
            sys.path.insert(0, site_str)
