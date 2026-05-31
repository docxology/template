#!/usr/bin/env python3
"""Write deterministic graph-world SI extension artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def main() -> int:
    from simulation.graph_world import write_graph_world_artifacts

    for name, path in write_graph_world_artifacts(PROJECT_ROOT).items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
