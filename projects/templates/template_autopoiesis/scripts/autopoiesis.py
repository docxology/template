#!/usr/bin/env python3
"""CLI wrapper — delegates to src/template_autopoiesis/core/cli.py::main."""

from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
_BOOTSTRAP = importlib.util.spec_from_file_location(
    "autopoiesis_script_bootstrap", PROJECT_ROOT / "scripts/_bootstrap.py"
)
if _BOOTSTRAP is None or _BOOTSTRAP.loader is None:
    raise ImportError("actual project bootstrap is unavailable")
_bootstrap = importlib.util.module_from_spec(_BOOTSTRAP)
_BOOTSTRAP.loader.exec_module(_bootstrap)
_bootstrap.bootstrap_project(PROJECT_ROOT)

from template_autopoiesis.core.cli import main  # noqa: E402 - actual provider selection precedes own imports

if __name__ == "__main__":
    main()
