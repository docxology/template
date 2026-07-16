#!/usr/bin/env python3
"""Run the literature exemplar's opt-in full-text enrichment stage."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _bootstrap import bootstrap_project

PROJECT_ROOT = bootstrap_project()

from literature.fulltext_download_cli import main as _main


def main() -> None:
    """Delegate to the covered source-level CLI implementation."""
    _main(project_root=PROJECT_ROOT)


if __name__ == "__main__":
    main()
