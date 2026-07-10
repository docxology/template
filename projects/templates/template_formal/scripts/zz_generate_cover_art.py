#!/usr/bin/env python3
"""Thin orchestrator: regenerate the manuscript's cover art.

All business logic (the actual drawing) lives in
:mod:`template_formal.colony.cover_art`. This script only wires up the
real on-disk path and prints it for manifest collection (mirrors
``template_gold_refinement/scripts/zz_generate_cover_visualization.py``).

Unlike the pipeline figures in ``02_run_analysis.py`` (written to the
disposable ``output/figures/`` tree), the cover art is committed static
content under ``manuscript/figures/`` -- the title page must render from
a fresh clone without first running the analysis pipeline, matching
``template_pools_rules_tools`` and ``template_textbook``'s convention for
authored design assets rather than data-derived figures.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (_PROJECT_ROOT, _PROJECT_ROOT / "src", _PROJECT_ROOT.parents[2]):
    path_text = str(_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)


def main() -> int:
    from template_formal.colony.cover_art import COVER_ART_FILENAME, require_cover_art

    output_path = _PROJECT_ROOT / "manuscript" / "figures" / COVER_ART_FILENAME
    written = require_cover_art(output_path, seed=42)
    print(str(written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
