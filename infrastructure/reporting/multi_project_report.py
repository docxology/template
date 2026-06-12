"""Multi-project pipeline completion reporting (ASCII summaries)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from infrastructure.core.logging.constants import BANNER_WIDTH
from infrastructure.core.logging.utils import get_logger

if TYPE_CHECKING:
    from infrastructure.core.pipeline.multi_project import MultiProjectResult
    from infrastructure.project.project_info import ProjectInfo

logger = get_logger(__name__)


def _dir_size_mb(path: Path) -> float:
    """Best-effort total size of files under ``path`` in megabytes (0.0 on error)."""
    if not path.exists():
        return 0.0
    total = 0
    try:
        for p in path.rglob("*"):
            if p.is_file():
                try:
                    total += p.stat().st_size
                except OSError:
                    continue
    except OSError:
        return 0.0
    return total / (1024 * 1024)


def _fmt_duration(seconds: float) -> str:
    """Format seconds as ``9.4s`` or ``2m 6s``."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(round(seconds)), 60)
    return f"{m}m {s:02d}s"


def format_multi_project_detailed_report(
    ordered_projects: Sequence[ProjectInfo],
    result: MultiProjectResult,
    *,
    repo_root: Path | None = None,
    width: int = BANNER_WIDTH,
) -> list[str]:
    """Render a rich end-of-run summary for multi-project execution."""
    n = len(ordered_projects)
    succ = result.successful_projects
    failed = n - succ
    rate = (succ / n * 100.0) if n else 0.0
    total = float(result.total_duration or 0.0)
    avg = (total / n) if n else 0.0

    bar = "=" * width
    sep = "-" * width
    out: list[str] = []

    out.append(bar)
    out.append("MULTI-PROJECT EXECUTION SUMMARY".center(width))
    out.append(f"{n} projects  ·  {succ} succeeded  ·  {failed} failed  ·  {rate:.1f}% success".center(width))
    out.append(f"wall time {_fmt_duration(total)}  ·  avg/project {_fmt_duration(avg)}".center(width))
    if result.infra_test_duration and result.infra_test_duration > 0:
        out.append(f"infrastructure tests: {_fmt_duration(result.infra_test_duration)}".center(width))
    out.append(bar)

    pr = result.project_results
    rows: list[tuple[str, str, str, str, str, str]] = []
    project_durations: list[tuple[str, float]] = []
    for proj in ordered_projects:
        qn = proj.qualified_name
        stages = pr.get(qn) or []
        total_stages = len(stages)
        ok_stages = sum(1 for s in stages if getattr(s, "success", False))
        dur = sum(float(getattr(s, "duration", 0.0)) for s in stages)
        project_durations.append((qn, dur))
        if total_stages == 0:
            icon = "❌"
            fail_at = "no stages ran"
        elif ok_stages == total_stages:
            icon = "✅"
            fail_at = ""
        else:
            icon = "❌"
            first_bad = next(
                (s for s in stages if not getattr(s, "success", False)),
                None,
            )
            fail_at = getattr(first_bad, "stage_name", "unknown") if first_bad else "unknown"

        out_dir = (repo_root / "projects" / qn / "output") if repo_root is not None else Path()
        size_mb = _dir_size_mb(out_dir) if repo_root is not None else 0.0
        rows.append(
            (
                icon,
                qn,
                f"{ok_stages}/{total_stages} stages" if total_stages else "0 stages",
                _fmt_duration(dur),
                f"{size_mb:.2f} MB" if size_mb else "—",
                fail_at,
            )
        )

    out.append("")
    out.append("PROJECT STATUS")
    out.append(sep)
    name_w = max((len(r[1]) for r in rows), default=12)
    stages_w = max((len(r[2]) for r in rows), default=8)
    for icon, name, stages_str, dur, size, fail_at in rows:
        suffix = f"   failed at: {fail_at}" if fail_at else ""
        out.append(f" {icon}  {name:<{name_w}}  {stages_str:<{stages_w}}  {dur:>7}  out: {size:>9}{suffix}")

    out.append("")
    out.append("STAGE TIMING BREAKDOWN")
    out.append(sep)
    stage_stats: dict[str, dict[str, float]] = {}
    for proj in ordered_projects:
        for s in pr.get(proj.qualified_name, []) or []:
            name = getattr(s, "stage_name", "?")
            entry = stage_stats.setdefault(name, {"total": 0.0, "n": 0.0, "ok": 0.0})
            entry["total"] += float(getattr(s, "duration", 0.0))
            entry["n"] += 1.0
            entry["ok"] += 1.0 if getattr(s, "success", False) else 0.0

    if stage_stats:
        out.append(f" {'Stage':<28}  {'Avg':>7}  {'Total':>8}  {'Status':>14}")
        for stage_name in sorted(stage_stats.keys(), key=lambda k: stage_stats[k]["total"], reverse=True):
            e = stage_stats[stage_name]
            avg_s = e["total"] / e["n"] if e["n"] else 0.0
            status = f"{int(e['ok'])}/{int(e['n'])} ok"
            out.append(
                f" {stage_name[:28]:<28}  {_fmt_duration(avg_s):>7}  {_fmt_duration(e['total']):>8}  {status:>14}"
            )
    else:
        out.append("  (no stage data recorded)")

    if project_durations:
        ranked = sorted(project_durations, key=lambda kv: kv[1])
        fastest_name, fastest_dur = ranked[0]
        slowest_name, slowest_dur = ranked[-1]
        out.append("")
        out.append("PERFORMANCE HIGHLIGHTS")
        out.append(sep)
        out.append(f"  Fastest project: {fastest_name}  ({_fmt_duration(fastest_dur)})")
        out.append(f"  Slowest project: {slowest_name}  ({_fmt_duration(slowest_dur)})")

    failure_rows: list[tuple[str, str, str]] = []
    for proj in ordered_projects:
        qn = proj.qualified_name
        stages = pr.get(qn) or []
        if not stages:
            failure_rows.append((qn, "pipeline aborted before any stage ran", ""))
            continue
        if all(getattr(s, "success", False) for s in stages):
            continue
        first_bad = next((s for s in stages if not getattr(s, "success", False)), None)
        if first_bad is None:
            continue
        err = (getattr(first_bad, "error_message", "") or "").strip()
        if len(err) > 160:
            err = err[:159] + "…"
        failure_rows.append((qn, getattr(first_bad, "stage_name", "?"), err))

    if failure_rows:
        out.append("")
        out.append("FAILURE DETAILS")
        out.append(sep)
        for qn, stage_name, err in failure_rows:
            out.append(f"  ❌ {qn}")
            out.append(f"     Stage : {stage_name}")
            if err:
                out.append(f"     Error : {err}")
            if repo_root is not None:
                log_path = repo_root / "projects" / qn / "output" / "logs" / "pipeline.log"
                if log_path.exists():
                    try:
                        rel = log_path.relative_to(repo_root)
                    except ValueError:
                        rel = log_path
                    out.append(f"     Log   : {rel}")
                report_path = repo_root / "projects" / qn / "output" / "reports" / "test_results.md"
                if report_path.exists():
                    try:
                        rel = report_path.relative_to(repo_root)
                    except ValueError:
                        rel = report_path
                    out.append(f"     Report: {rel}")
            out.append("")

    if repo_root is not None:
        out.append("OUTPUT LOCATIONS")
        out.append(sep)
        summary_md = repo_root / "output" / "multi_project_summary" / "multi_project_summary.md"
        if summary_md.exists():
            try:
                rel = summary_md.relative_to(repo_root)
            except ValueError:
                rel = summary_md
            out.append(f"  Summary report : {rel}")
        for proj in ordered_projects:
            qn = proj.qualified_name
            stages = pr.get(qn) or []
            if not (stages and all(getattr(s, "success", False) for s in stages)):
                continue
            pdf_dir = repo_root / "output" / qn
            if pdf_dir.exists():
                pdfs = sorted(pdf_dir.glob("*.pdf"))
                for pdf in pdfs[:2]:
                    try:
                        rel = pdf.relative_to(repo_root)
                    except ValueError:
                        rel = pdf
                    out.append(f"  Output PDF     : {rel}")

        out.append("")
        out.append("NEXT STEPS")
        out.append(sep)
        if failure_rows:
            sample = failure_rows[0][0].split("/")[-1]
            out.append(f"  • Re-run a failed project: ./run.sh --project {sample} --pipeline --core-only --skip-infra")
            out.append("  • Inspect a failure log : cat projects/<name>/output/logs/pipeline.log")
        else:
            out.append("  • All projects passed. Inspect outputs under output/<project>/")

    out.append("")
    if failed == 0 and n > 0:
        out.append(bar)
        out.append(f"🎉 ALL {n} PROJECTS PASSED  ·  {_fmt_duration(total)}".center(width))
        out.append(bar)
    else:
        out.append(bar)
        out.append(f"⚠️  {succ}/{n} succeeded  ·  {failed} failed  ·  {_fmt_duration(total)}".center(width))
        out.append(bar)

    return out


def write_last_run_summary(summary_lines: list[str], repo_root: Path) -> Path | None:
    """Persist a rendered multi-project summary to ``docs/_generated/last-run-summary.md``."""
    try:
        from datetime import datetime, timezone

        generated_dir = repo_root / "docs" / "_generated"
        generated_dir.mkdir(parents=True, exist_ok=True)
        artifact = generated_dir / "last-run-summary.md"
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        artifact.write_text(
            "# Last Pipeline Run \u2014 Summary\n\n"
            "> Auto-generated by `infrastructure.reporting.multi_project_report.write_last_run_summary`. "
            "Do not edit manually.\n"
            f"> Generated: {stamp}\n\n"
            "```\n" + "\n".join(summary_lines) + "\n```\n"
        )
        return artifact
    except OSError as exc:
        logger.warning(f"last-run-summary write failed (non-fatal): {exc}")
        return None
