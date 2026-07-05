"""Interactive HTML dashboard for the gold-refinement exemplar.

Generates a self-contained HTML dashboard showing refinery metrics,
purity progression, token distribution, and evidence registry status.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .parsing import build_timestamp as _build_timestamp
    from .refinery import run_refinery
except ImportError:
    from parsing import build_timestamp as _build_timestamp  # type: ignore[no-redef]
    from refinery import run_refinery  # type: ignore[no-redef]

import logging

logger = logging.getLogger(__name__)


def _esc(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _refinery_snapshot(result: Any) -> dict[str, Any]:
    return {
        "stage_count": result.stage_count,
        "final_purity": result.final_purity,
        "final_karat": result.final_karat.label,
        "total_purity_gain": result.total_purity_gain,
        "is_nine_nines_certified": result.is_nine_nines_certified,
        "purity_sequence": list(result.purity_sequence),
        "stages": [
            {
                "order": stage.order,
                "name": stage.name,
                "input_purity": stage.input_purity,
                "output_purity": stage.output_purity,
                "karat": stage.karat_grade.label,
                "metallurgical_operation": stage.metallurgical_operation,
                "manuscript_operation": stage.manuscript_operation,
            }
            for stage in result.stages
        ],
    }


def _merge_refinery_snapshot(fallback: dict[str, Any], refinement: dict[str, Any] | None) -> dict[str, Any]:
    if not refinement:
        return fallback
    snapshot = dict(fallback)
    for key, value in refinement.items():
        if key == "stages" and not value:
            continue
        if value is not None:
            snapshot[key] = value
    if not isinstance(snapshot.get("stages"), list) or not snapshot["stages"]:
        snapshot["stages"] = fallback["stages"]
    return snapshot


def build_dashboard_html(
    project_root: Path,
    *,
    refinery_data: dict[str, Any] | None = None,
    token_data: dict[str, Any] | None = None,
    evidence_data: dict[str, Any] | None = None,
) -> str:
    """Build a self-contained HTML dashboard string."""
    fallback_snapshot = _refinery_snapshot(run_refinery())

    # Load data files if not provided
    if refinery_data is None:
        rp = project_root / "output" / "data" / "refinery_results.json"
        if rp.exists():
            with rp.open("r") as f:
                refinery_data = json.load(f)
        else:
            refinery_data = {}

    if token_data is None:
        tp = project_root / "output" / "reports" / "token_plan.json"
        if tp.exists():
            with tp.open("r") as f:
                token_data = json.load(f)
        else:
            token_data = {}

    if evidence_data is None:
        ep = project_root / "output" / "reports" / "claim_support_registry.json"
        if ep.exists():
            with ep.open("r") as f:
                evidence_data = json.load(f)
        else:
            evidence_data = {}

    refinery_snapshot = _merge_refinery_snapshot(fallback_snapshot, refinery_data)

    # Build stage rows
    stage_rows = ""
    for stage in refinery_snapshot.get("stages", []):
        stage_rows += (
            f"<tr>"
            f"<td>{stage['order']}</td>"
            f"<td>{_esc(str(stage.get('name', '')))}</td>"
            f"<td>{float(stage.get('output_purity', 0.0)):.6f}</td>"
            f"<td>{_esc(str(stage.get('karat', stage.get('karat_grade', ''))))}</td>"
            f"<td>{_esc(str(stage.get('metallurgical_operation', '')))}</td>"
            f"</tr>"
        )

    # Build token category rows
    cat_rows = ""
    for cat, count in sorted((token_data or {}).get("category_counts", {}).items()):
        cat_rows += f"<tr><td>{_esc(cat)}</td><td>{count}</td></tr>"

    # Evidence rows
    evidence_rows = ""
    total = (evidence_data or {}).get("total_claims", 0)
    supported = (evidence_data or {}).get("supported_claims", 0)
    for entry in (evidence_data or {}).get("entries", []):
        status = "✅" if entry.get("supported") else "❌"
        evidence_rows += (
            f"<tr>"
            f"<td>{status}</td>"
            f"<td>{_esc(entry.get('claim_name', ''))}</td>"
            f"<td>{_esc(entry.get('evidence_source', ''))}</td>"
            f"<td>{_esc(entry.get('boundary', ''))}</td>"
            f"</tr>"
        )

    timestamp = _build_timestamp()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Gold Refinement Dashboard</title>
<style>
  body {{ font-family: -apple-system, sans-serif; margin: 2em; background: #fafafa; }}
  h1 {{ color: #8B4513; }}
  h2 {{ color: #1e3a8a; border-bottom: 2px solid #FFD700; padding-bottom: 0.3em; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
  th, td {{ border: 1px solid #ddd; padding: 0.5em; text-align: left; }}
  th {{ background: #FFD700; color: #333; }}
  tr:nth-child(even) {{ background: #fffde6; }}
  .metric {{ display: inline-block; margin: 1em; padding: 1em; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
  .metric-value {{ font-size: 2em; font-weight: bold; color: #8B4513; }}
  .metric-label {{ color: #666; font-size: 0.9em; }}
  .footer {{ margin-top: 2em; color: #999; font-size: 0.8em; }}
</style>
</head>
<body>
<h1>⛏️ Gold Refinement Dashboard</h1>

<div>
  <div class="metric">
    <div class="metric-value">{refinery_snapshot["stage_count"]}</div>
    <div class="metric-label">Refinery Stages</div>
  </div>
  <div class="metric">
    <div class="metric-value">{float(refinery_snapshot["final_purity"]) * 100:.4f}%</div>
    <div class="metric-label">Final Purity ({_esc(str(refinery_snapshot["final_karat"]))})</div>
  </div>
  <div class="metric">
    <div class="metric-value">{(token_data or {}).get("total_tokens", 0)}</div>
    <div class="metric-label">Generated Tokens</div>
  </div>
  <div class="metric">
    <div class="metric-value">{supported}/{total}</div>
    <div class="metric-label">Evidence Claims Supported</div>
  </div>
</div>

<h2>Refinery Stages</h2>
<table>
<tr><th>#</th><th>Stage</th><th>Output Purity</th><th>Karat</th><th>Operation</th></tr>
{stage_rows}
</table>

<h2>Token Distribution by Category</h2>
<table>
<tr><th>Category</th><th>Count</th></tr>
{cat_rows}
</table>

<h2>Evidence Registry</h2>
<table>
<tr><th>Status</th><th>Claim</th><th>Evidence Source</th><th>Boundary</th></tr>
{evidence_rows}
</table>

<div class="footer">Generated: {timestamp}</div>
</body>
</html>"""


def write_dashboard(
    project_root: Path,
    output_path: Path | None = None,
) -> Path:
    """Write the HTML dashboard to output/dashboard.html."""
    if output_path is None:
        output_path = project_root / "output" / "dashboard.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = build_dashboard_html(project_root)
    output_path.write_text(html, encoding="utf-8")
    logger.info("Wrote dashboard to %s", output_path)
    return output_path


__all__ = ["build_dashboard_html", "write_dashboard"]
