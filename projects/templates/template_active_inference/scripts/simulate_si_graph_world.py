#!/usr/bin/env python3
"""Write stub artifact for the opt-in graph-world SI extension track."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def main() -> int:
    from simulation.graph_world import write_graph_world_stub

    out = write_graph_world_stub(PROJECT_ROOT)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
