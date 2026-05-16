"""LaTeX render-log quality checks.

The rendering pipeline treats fatal LaTeX errors separately during
compilation.  This module covers the quieter class of problems that still
matter for reviewer-facing artifacts: layout boxes and unresolved references.
Projects opt into failing the render stage on these findings via
``rendering.fail_on_latex_warnings: true`` in ``manuscript/config.yaml``.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class LatexLogFinding:
    """One policy-relevant finding from a LaTeX log."""

    log_file: Path
    line_number: int
    kind: str
    message: str


_LAYOUT_WARNING_RE = re.compile(r"^(?P<state>Overfull|Underfull) \\(?P<box>[hv]box)\b(?P<detail>.*)$")
_UNDEFINED_REFERENCE_RE = re.compile(
    r"^(?:LaTeX Warning: (?:Reference|Citation).*undefined|"
    r"LaTeX Warning: There were undefined references|"
    r"Package natbib Warning: Citation .* undefined)",
    re.IGNORECASE,
)
_MISSING_FILE_RE = re.compile(
    r"(?:LaTeX Error: File `[^`]+` not found|! LaTeX Error: File .* not found|File `[^`]+` not found)",
    re.IGNORECASE,
)

DEFAULT_BLOCKED_LAYOUT_KINDS = frozenset(
    {
        r"Overfull \hbox",
        r"Overfull \vbox",
        r"Underfull \hbox",
    }
)


def parse_latex_log_findings(
    log_file: Path | str,
    *,
    blocked_layout_kinds: Iterable[str] = DEFAULT_BLOCKED_LAYOUT_KINDS,
) -> list[LatexLogFinding]:
    """Return policy-relevant findings from a single ``.log`` file."""
    path = Path(log_file)
    if not path.exists():
        return []

    blocked = set(blocked_layout_kinds)
    findings: list[LatexLogFinding] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        stripped = line.strip()
        layout_match = _LAYOUT_WARNING_RE.match(stripped)
        if layout_match:
            kind = rf"{layout_match.group('state')} \{layout_match.group('box')}"
            if kind in blocked:
                findings.append(
                    LatexLogFinding(
                        log_file=path,
                        line_number=line_number,
                        kind=kind,
                        message=stripped,
                    )
                )
            continue

        if _UNDEFINED_REFERENCE_RE.search(stripped):
            findings.append(
                LatexLogFinding(
                    log_file=path,
                    line_number=line_number,
                    kind="Undefined reference/citation",
                    message=stripped,
                )
            )
            continue

        if _MISSING_FILE_RE.search(stripped):
            findings.append(
                LatexLogFinding(
                    log_file=path,
                    line_number=line_number,
                    kind="Missing LaTeX file",
                    message=stripped,
                )
            )

    return findings


def collect_latex_log_findings(log_files: Iterable[Path | str]) -> list[LatexLogFinding]:
    """Parse all logs and return every policy finding."""
    findings: list[LatexLogFinding] = []
    for log_file in log_files:
        findings.extend(parse_latex_log_findings(log_file))
    return findings


def summarize_latex_findings(findings: Iterable[LatexLogFinding]) -> Counter[str]:
    """Count findings by kind."""
    return Counter(finding.kind for finding in findings)


def format_latex_findings(findings: Iterable[LatexLogFinding], *, max_examples: int = 12) -> str:
    """Format findings for a compact render-stage error message."""
    items = list(findings)
    counts = summarize_latex_findings(items)
    lines = ["LaTeX log quality findings:"]
    for kind, count in sorted(counts.items()):
        lines.append(f"  {kind}: {count}")
    if items:
        lines.append("Examples:")
        for finding in items[:max_examples]:
            lines.append(f"  {finding.log_file.name}:{finding.line_number}: {finding.kind}: {finding.message}")
        if len(items) > max_examples:
            lines.append(f"  ... {len(items) - max_examples} more")
    return "\n".join(lines)
