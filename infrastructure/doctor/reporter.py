"""Render :class:`DoctorReport` to text, JSON, and exit codes.

The text renderer is plain ASCII so it survives ``less`` and CI log
collectors. JSON output is the agent-facing contract — exit code +
JSON body together describe everything a remediation agent needs to
plan its next step.

Exit codes (BSD-style, stable across versions):

* ``0``  — healthy (no findings worse than INFO).
* ``1``  — warnings present, no errors.
* ``2``  — at least one ERROR finding.
* ``3``  — at least one CRITICAL finding.
* ``4``  — fix applied but a follow-up issue is now CRITICAL.
* ``64`` — usage error (bad CLI args, BSD ``EX_USAGE``).
"""

import json
from collections.abc import Iterable

from infrastructure.doctor.models import (
    DoctorReport,
    Finding,
    MutateRecord,
    Severity,
)


__all__ = [
    "EXIT_HEALTHY",
    "EXIT_WARN",
    "EXIT_ERROR",
    "EXIT_CRITICAL",
    "EXIT_REGRESSION",
    "EXIT_USAGE",
    "compute_exit_code",
    "render_report_text",
    "render_report_json",
]


EXIT_HEALTHY = 0
EXIT_WARN = 1
EXIT_ERROR = 2
EXIT_CRITICAL = 3
EXIT_REGRESSION = 4
EXIT_USAGE = 64


def compute_exit_code(findings: Iterable[Finding]) -> int:
    """Map the worst finding severity into a stable exit code."""
    worst = Severity.INFO
    for f in findings:
        if f.healthy:
            continue
        if f.severity > worst:
            worst = f.severity
    if worst == Severity.CRITICAL:
        return EXIT_CRITICAL
    if worst == Severity.ERROR:
        return EXIT_ERROR
    if worst == Severity.WARN:
        return EXIT_WARN
    return EXIT_HEALTHY


# ---------------------------------------------------------------------------
# Text renderer
# ---------------------------------------------------------------------------


_BAR = "=" * 78


def _sev_badge(severity: Severity, healthy: bool) -> str:
    if healthy:
        return "[ OK ]"
    return {
        Severity.INFO: "[INFO]",
        Severity.WARN: "[WARN]",
        Severity.ERROR: "[ERR ]",
        Severity.CRITICAL: "[CRIT]",
    }[severity]


def render_report_text(report: DoctorReport) -> str:
    """Render the full report as a text block.

    Layout::

        ====== infrastructure.doctor ======
        score   : 87.4 / 100
        exit    : 1

        Dimension scores
          environment      : 100.0
          project_layout   :  85.0
          ...

        Findings (12)
          [WARN] DOC301 — 4 cache directories present
                fix: fix_clean_pycache (conservative)
                ...

        Applied (0)  Skipped (4)  Failed (0)
    """
    lines: list[str] = [_BAR, "infrastructure.doctor".center(78), _BAR, ""]

    lines.append(f"score   : {report.overall_score:6.2f} / 100")
    lines.append(f"exit    : {report.exit_code}")
    lines.append("")

    lines.append("Dimension scores")
    for dim, score in report.dimension_scores.items():
        lines.append(f"  {dim:<22s} : {score:6.2f}")
    lines.append("")

    lines.append(f"Findings ({len(report.findings)})")
    for f in report.findings:
        lines.append(f"  {_sev_badge(f.severity, f.healthy)} {f.code} — {f.title}")
        if not f.healthy:
            for rl in f.repair_levels:
                lines.append(f"        fix: {rl.fix_id} ({rl.level.label}) — {rl.description}")
            if f.description:
                lines.append(f"        {f.description}")
    lines.append("")

    if report.applied:
        lines.append(f"Applied ({len(report.applied)})")
        for r in report.applied:
            lines.append(f"  + {r.action_id} {r.fix_id} — {r.title}")
        lines.append("")
    if report.skipped:
        lines.append(f"Skipped ({len(report.skipped)})")
        for p in report.skipped:
            lines.append(f"  ~ {p.fix_id} ({p.therapy.label}) — {p.title}")
        lines.append("")
    if report.failed:
        lines.append(f"Failed ({len(report.failed)})")
        for r in report.failed:
            lines.append(f"  ! {r.action_id} {r.fix_id} — {r.error or ''}")
        lines.append("")

    lines.append(_BAR)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON renderer
# ---------------------------------------------------------------------------


def render_report_json(
    report: DoctorReport,
    *,
    indent: int | None = 2,
) -> str:
    """Render the report as JSON for agent consumption."""
    return json.dumps(report.to_jsonable(), indent=indent, sort_keys=True)


def _format_record_summary(record: MutateRecord) -> str:
    """Tiny helper used by the text renderer (kept for future verbose mode)."""
    status = "applied" if record.applied else f"failed: {record.error}"
    return f"{record.action_id} {record.fix_id} ({record.therapy}) — {status}"
