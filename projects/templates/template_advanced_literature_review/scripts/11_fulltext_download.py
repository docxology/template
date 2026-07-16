#!/usr/bin/env python3
"""Run the advanced exemplar's full-text enrichment stage."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _bootstrap import bootstrap_project

bootstrap_project()

main = importlib.import_module("literature.fulltext_download_cli").main


if __name__ == "__main__":
    main()
