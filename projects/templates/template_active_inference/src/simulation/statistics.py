"""Statistics derived from pymdp simulation artifacts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _entropy_stats(trace_steps: list[dict[str, Any]]) -> dict[str, float]:
    entropies = [float(step.get("belief_entropy", 0.0)) for step in trace_steps]
    if not entropies:
        return {"entropy_min": 0.0, "entropy_max": 0.0, "entropy_mean": 0.0}
    return {
        "entropy_min": min(entropies),
        "entropy_max": max(entropies),
        "entropy_mean": sum(entropies) / len(entropies),
    }


def summarize_si_trace(trace: Mapping[str, Any], summary: Mapping[str, Any]) -> dict[str, Any]:
    steps = list(trace.get("steps") or [])
    actions = list(summary.get("actions") or [])
    observations = list(summary.get("observations") or [])
    goal_state = int((summary.get("config") or {}).get("tmaze", {}).get("num_obs", 2)) - 1
    goal_reached = bool(observations and int(observations[-1]) == goal_state)
    if "goal_reached" in summary:
        goal_reached = bool(summary["goal_reached"])
    stats = {
        "steps": int(summary.get("steps", len(steps))),
        "action_diversity": len(set(actions)),
        "goal_reached": goal_reached,
        **_entropy_stats(steps),
    }
    return stats


def load_si_artifacts(project_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    root = project_root.resolve()
    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    trace_path = root / "output" / "data" / "si_tmaze_trace.json"
    summary: dict[str, Any] = {}
    trace: dict[str, Any] = {"steps": []}
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if trace_path.exists():
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
    return summary, trace
