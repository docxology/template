"""Deterministic graph-world SI extension artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast


def _graph_world_trace() -> list[dict[str, object]]:
    nodes = ("start", "cue", "choice", "goal")
    entropies = (1.3862943611198906, 1.0397207708399179, 0.5623351446188083, 0.0)
    actions = ("observe_cue", "advance", "commit_goal", "stay_goal")
    trace: list[dict[str, object]] = []
    for step, (node, entropy, action) in enumerate(zip(nodes, entropies, actions, strict=True)):
        trace.append(
            {
                "step": step,
                "node": node,
                "action": action,
                "belief_entropy": entropy,
                "goal_probability": round(step / (len(nodes) - 1), 6),
            }
        )
    return trace


def write_graph_world_artifacts(project_root: Path) -> dict[str, Path]:
    """Write deterministic graph-world summary and trace artifacts."""
    root = project_root.resolve()
    data_dir = root / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    trace = _graph_world_trace()
    entropy_values = [float(cast(int | float, row["belief_entropy"])) for row in trace]
    summary = {
        "status": "ok",
        "node_count": 4,
        "edge_count": 4,
        "steps": len(trace),
        "start": "start",
        "goal": "goal",
        "goal_reached": trace[-1]["node"] == "goal",
        "mean_belief_entropy": sum(entropy_values) / len(entropy_values),
        "policy": [row["action"] for row in trace],
    }
    summary_path = data_dir / "si_graph_world_summary.json"
    trace_path = data_dir / "si_graph_world_trace.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    trace_path.write_text(json.dumps({"steps": trace}, indent=2) + "\n", encoding="utf-8")
    return {"summary": summary_path, "trace": trace_path}


def write_graph_world_stub(project_root: Path) -> Path:
    """Backward-compatible wrapper returning the summary artifact path."""
    return write_graph_world_artifacts(project_root)["summary"]
