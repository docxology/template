#!/usr/bin/env python3
"""Write stub artifact for the opt-in graph-world SI extension track."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    out = PROJECT_ROOT / "output" / "data" / "si_graph_world_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "not_implemented",
        "message": "Graph-world SI is an opt-in extension; implement in a follow-up PR.",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
