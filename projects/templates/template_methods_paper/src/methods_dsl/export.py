"""Plan exporters: worklist markdown, CSV, Mermaid graph, canonical JSON.

Mirrors BPL's export surface ("CSV/XLSX worklists, workflow graphs
(Mermaid/JSON/ReactFlow)") at a scope appropriate for a template exemplar:
CSV and Mermaid text, plus the canonical JSON the plan hash is computed over
(so a reader can independently verify :data:`Plan.plan_hash`).
"""

from __future__ import annotations

import json
from pathlib import Path

from .compiler import Plan


def to_worklist_markdown(plan: Plan) -> str:
    """Render *plan* as a numbered, human-readable worklist."""
    lines = [f"# Worklist: {plan.method_name} v{plan.method_version} ({plan.target})", ""]
    for step in plan.steps:
        lines.append(f"{step.order + 1}. **{step.name}** — `{step.kind}` on `{step.target}` (step_id={step.step_id})")
    return "\n".join(lines) + "\n"


def to_csv_rows(plan: Plan) -> list[str]:
    """Return *plan* as CSV lines (header first), ready to join with ``\\n``."""
    rows = ["order,step_id,name,kind,target"]
    for step in plan.steps:
        safe_name = step.name.replace('"', '""')
        rows.append(f'{step.order},{step.step_id},"{safe_name}",{step.kind},{step.target}')
    return rows


def write_csv(plan: Plan, path: Path) -> Path:
    """Write *plan* as CSV to *path* and return the resolved path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(to_csv_rows(plan)) + "\n", encoding="utf-8")
    return path


def to_mermaid(plan: Plan) -> str:
    """Render *plan* as a Mermaid ``flowchart TD`` showing scheduled order."""
    lines = ["flowchart TD"]
    for step in plan.steps:
        node_id = f"S{step.step_id}"
        label = step.name.replace('"', "'")
        lines.append(f'    {node_id}["{step.order + 1}. {label}"]')
    for earlier, later in zip(plan.steps, plan.steps[1:]):
        lines.append(f"    S{earlier.step_id} --> S{later.step_id}")
    return "\n".join(lines) + "\n"


def to_json(plan: Plan) -> str:
    """Return the canonical JSON encoding :data:`Plan.plan_hash` was computed over."""
    return json.dumps(plan.to_canonical_dict(), sort_keys=True, indent=2) + "\n"


def write_json(plan: Plan, path: Path) -> Path:
    """Write *plan*'s canonical JSON to *path* and return the resolved path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_json(plan), encoding="utf-8")
    return path


def write_json_report(payload: dict[str, object] | list[dict[str, object]], path: Path) -> Path:
    """Write an arbitrary JSON-serializable *payload* to *path* and return it.

    Generic counterpart to :func:`write_json` for non-:class:`Plan` report
    payloads (gate counts, the compiled-plan summary, the trust-chain demo
    report) that ``scripts/methods_analysis.py`` writes under ``output/reports/``
    and ``output/data/``.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_all_exports(plan: Plan, data_dir: Path) -> list[Path]:
    """Write worklist markdown, CSV, Mermaid, and canonical JSON for *plan* under *data_dir*.

    The four filenames are derived from ``plan.method_name.lower()``. Returns
    the four written paths in worklist/CSV/Mermaid/JSON order — the single
    call orchestration scripts use instead of writing each format inline.
    """
    slug = plan.method_name.lower()
    data_dir.mkdir(parents=True, exist_ok=True)
    worklist_path = data_dir / f"{slug}_worklist.md"
    worklist_path.write_text(to_worklist_markdown(plan), encoding="utf-8")
    csv_path = write_csv(plan, data_dir / f"{slug}_plan.csv")
    mermaid_path = data_dir / f"{slug}_graph.mmd"
    mermaid_path.write_text(to_mermaid(plan), encoding="utf-8")
    json_path = write_json(plan, data_dir / f"{slug}_plan.json")
    return [worklist_path, csv_path, mermaid_path, json_path]
