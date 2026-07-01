#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT.parents[2]))


def main() -> int:
    from cover_visualization import COVER_REPORT, write_cover_visualization

    image_path = write_cover_visualization(_PROJECT_ROOT)
    report_path = _PROJECT_ROOT / "output" / "reports" / COVER_REPORT
    print(f"Wrote {image_path}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
