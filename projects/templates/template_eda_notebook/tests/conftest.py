"""Select the declared SDK before exposing this exemplar's own source."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

# The declared environment supplies a checkout or installed SDK; parent folder
# guesses must not replace that provider in an exported project.
import infrastructure  # noqa: E402,F401

_SRC = str(Path(__file__).resolve().parents[1] / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
