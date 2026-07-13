#!/usr/bin/env python3
"""Run the formal-colony publication analysis and print its artifact paths."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (PROJECT_ROOT / "src", PROJECT_ROOT.parents[2]):
    path_text = str(_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from template_formal.colony.analysis import run_publication_analysis  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Execute the source-owned analysis service."""
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    artifacts = run_publication_analysis(PROJECT_ROOT)
    for path in artifacts.paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
