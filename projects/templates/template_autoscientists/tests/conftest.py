"""Pytest configuration for template_autoscientists."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]

for path in (REPO_ROOT, PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT / "scripts"):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

# TEST-ISOLATION-SYSPATH-1: expose the unique nested source package.
import os as _os
import sys as _sys

_SRC = _os.path.join(_os.path.dirname(__file__), "..", "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

# TEST-ISOLATION-SYSPATH-1: expose the unique nested source package.
import os as _os
import sys as _sys

_SRC = _os.path.join(_os.path.dirname(__file__), "..", "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

# TEST-ISOLATION-SYSPATH-1: expose the unique nested source package.
import os as _os
import sys as _sys

_SRC = _os.path.join(_os.path.dirname(__file__), "..", "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)
