"""Human-readable harness report formatting."""

from __future__ import annotations

import json
from pathlib import Path

from skill_eval import config

BANNER_WIDTH = 80


def load_baseline_benchmark() -> dict | None:
    """Load benchmark.json from the pinned baseline run directory."""
    path = config.BASELINE_DIR / "benchmark.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _pct(rate: float) -> str:
    return f"{rate * 100:.0f}%"


def _pp_delta(a: float, b: float) -> str:
    delta = (a - b) * 100.0
    if abs(delta) < 0.05:
        return "—"
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.0f}%"


def _gaps_label(failed: list[str]) -> str:
    if not failed:
        return "—"
    if len(failed) == 1:
        return failed[0][:40] + ("…" if len(failed[0]) > 40 else "")
    return f"{len(failed)} failed"


def format_eval_row(
    name: str,
    ws_rate: float,
    wo_rate: float,
    failed: list[str],
    *,
    name_width: int = 30,
) -> str:
    """Format one positive-eval table row."""
    gaps = _gaps_label(failed)
    return f"  {name:<{name_width}} {_pct(ws_rate):>6} {_pct(wo_rate):>8} {_pp_delta(ws_rate, wo_rate):>6}   {gaps}"


def _eval_rates_by_name(benchmark: dict, config: str) -> dict[str, float]:
    for block in benchmark.get("configurations", []):
        if block.get("name") == config:
            return {row["eval_name"]: row["pass_rate"] for row in block.get("evals", [])}
    return {}


def _failed_expectations(grading: dict) -> list[str]:
    return [item["text"] for item in grading.get("expectations", []) if not item.get("passed")]


def format_compare_section(current: dict, baseline: dict) -> list[str]:
    """Per-eval with_skill delta vs the pinned baseline benchmark."""
    baseline_label = baseline.get("run_dir", "baseline")
    cur_ws = _eval_rates_by_name(current, "with_skill")
    prev_ws = _eval_rates_by_name(baseline, "with_skill")
    lines = [
        "",
        f"COMPARE (vs {baseline_label} with_skill)",
    ]
    regressions: list[str] = []
    for name in sorted(cur_ws):
        cur = cur_ws[name]
        prev = prev_ws.get(name)
        if prev is None:
            lines.append(f"  {name}: new eval (with_skill {_pct(cur)})")
            continue
        delta = cur - prev
        if delta < -0.001 or (prev >= 1.0 and cur < 1.0):
            regressions.append(name)
            lines.append(f"  {name}: REGRESSION {_pct(prev)} → {_pct(cur)} ({_pp_delta(cur, prev)})")
        elif delta > 0.001:
            lines.append(f"  {name}: improved {_pct(prev)} → {_pct(cur)} ({_pp_delta(cur, prev)})")
    if not regressions and all(abs(cur_ws[n] - prev_ws.get(n, cur_ws[n])) < 0.001 for n in cur_ws if n in prev_ws):
        lines.append("  No with_skill regressions.")
    return lines


def format_harness_report(
    benchmark: dict,
    workspace: Path,
    *,
    gradings_by_eval: dict[str, dict[str, dict]],
    review_path: Path | None = None,
    compare_benchmark: dict | None = None,
    mode_line: str | None = None,
) -> str:
    """Build multi-line ASCII harness report."""
    summary = benchmark["summary"]
    run_dir = benchmark.get("run_dir", workspace.name)
    pos_count = summary.get("positive_eval_count", 0)
    neg_count = summary.get("negative_eval_count", 0)
    total_evals = pos_count + neg_count
    total_runs = total_evals * 2

    bar = "=" * BANNER_WIDTH
    lines: list[str] = [
        bar,
        "SKILL EVAL HARNESS".center(BANNER_WIDTH),
        bar,
        f"Run directory: {run_dir}",
        f"Workspace: {workspace}",
    ]
    if mode_line:
        lines.append(f"Mode: {mode_line}")
    lines.extend(
        [
            f"Evals: {total_evals} ({pos_count} positive · {neg_count} negative) · {total_runs} grading runs",
            "",
            "SUMMARY",
            f"  with_skill (all):             {summary['with_skill_mean_pass_rate'] * 100:6.1f}%",
            f"  with_skill (positive only):   {summary['with_skill_positive_only_pass_rate'] * 100:6.1f}%",
            f"  without_skill (positive):     {summary['without_skill_positive_only_pass_rate'] * 100:6.1f}%",
            f"  delta (positive only):        {summary['delta_positive_only_pass_rate'] * 100:+6.1f} pp",
            "",
            "PER-EVAL (positive)",
            "  eval_name                      with  without      Δ  with_skill gaps",
            "  ------------------------------ ------ -------- ------ -----------------",
        ]
    )

    ws_rates = _eval_rates_by_name(benchmark, "with_skill")
    wo_rates = _eval_rates_by_name(benchmark, "without_skill")
    neg_names = {name for name, modes in gradings_by_eval.items() if modes.get("with_skill", {}).get("negative")}

    for name in sorted(ws_rates):
        if name in neg_names:
            continue
        ws_grading = gradings_by_eval.get(name, {}).get("with_skill", {})
        failed = _failed_expectations(ws_grading)
        lines.append(format_eval_row(name, ws_rates[name], wo_rates.get(name, 0.0), failed))

    lines.extend(["", "NEGATIVE (with_skill must route out-of-scope)"])
    for name in sorted(neg_names):
        ws = gradings_by_eval.get(name, {}).get("with_skill", {})
        summary_row = ws.get("summary", {})
        passed = summary_row.get("passed", 0)
        total = summary_row.get("total", 0)
        rate = summary_row.get("pass_rate", 0.0)
        status = "PASS" if rate >= 1.0 else "FAIL"
        lines.append(f"  {name:<30} {status} ({passed}/{total})")

    lines.extend(["", "ARTIFACTS"])
    lines.append(f"  benchmark.json → {workspace / 'benchmark.json'}")
    if review_path is not None:
        lines.append(f"  review.html    → {review_path}")

    if compare_benchmark is not None:
        lines.extend(format_compare_section(benchmark, compare_benchmark))

    lines.append(bar)
    return "\n".join(lines)
