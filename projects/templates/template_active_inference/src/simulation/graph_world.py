"""Opt-in graph-world SI extension artifacts."""

from __future__ import annotations

import json
from pathlib import Path


def write_graph_world_stub(project_root: Path) -> Path:
    """Write the placeholder graph-world summary JSON for the extension track."""
    root = project_root.resolve()
    out = root / "output" / "data" / "si_graph_world_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "not_implemented",
        "message": "Graph-world SI is an opt-in extension; implement in a follow-up PR.",
    }
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out
