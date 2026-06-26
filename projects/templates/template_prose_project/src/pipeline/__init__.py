"""Pure orchestration of the prose review pipeline.

This module is the only surface in ``src/`` that imports from
``infrastructure.prose.*``.  It receives a pre-analysed
:class:`ManuscriptReportLike` (produced by the calling script via
``infrastructure.prose.analyze_manuscript``), runs the configured checks,
and optionally writes the JSON artefacts to disk.

Public API:

* :class:`ProseRunArtifacts` — result dataclass returned to the caller.
* :func:`run_prose_pipeline` — the pipeline entry point.
* :data:`CHECK_REGISTRY` — the ordered tuple of registered checks.
* :class:`CheckResult` — outcome of one check.
* :func:`run_configured_checks` — run enabled checks from the registry.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..config import ProjectConfig
from ..prose_facade import ManuscriptReportLike
from .checks import (
    CHECK_REGISTRY,
    CheckResult,
    run_configured_checks,
)

__all__ = [
    "CHECK_REGISTRY",
    "CheckResult",
    "ProseRunArtifacts",
    "run_configured_checks",
    "run_prose_pipeline",
]


@dataclass
class ProseRunArtifacts:
    """Outputs of a single :func:`run_prose_pipeline` call.

    Attributes:
        manuscript_report: The aggregated prose analysis produced by
            ``infrastructure.prose.analyze_manuscript``.
        report_path: Path of the written ``manuscript_report.json`` file,
            or ``None`` when ``write_outputs=False``.
        checks: Ordered list of :class:`CheckResult` objects, one per
            enabled check in :data:`CHECK_REGISTRY`.
        all_passed: ``True`` if every check passed; ``False`` otherwise.
    """

    manuscript_report: ManuscriptReportLike
    report_path: Path | None = None
    checks: list[CheckResult] = field(default_factory=list)
    all_passed: bool = True

    @property
    def total_words(self) -> int:
        """Total word count across all manuscript files."""
        return self.manuscript_report.total_words

    def to_dict(self) -> dict[str, object]:
        """Serialise to a JSON-compatible dictionary.

        Returns a mapping with keys ``all_passed``, ``total_words``,
        ``report_path`` (string or ``null``), ``checks`` (list), and
        ``manuscript`` (the :meth:`ManuscriptReportLike.to_dict` payload).
        """
        return {
            "all_passed": self.all_passed,
            "total_words": self.total_words,
            "report_path": str(self.report_path) if self.report_path else None,
            "checks": [c.to_dict() for c in self.checks],
            "manuscript": self.manuscript_report.to_dict(),
        }


def run_prose_pipeline(
    config: ProjectConfig,
    *,
    project_root: Path | str,
    manuscript_report: ManuscriptReportLike,
    write_outputs: bool = True,
) -> ProseRunArtifacts:
    """Run configured checks over a pre-analyzed manuscript report."""
    root = Path(project_root)
    bib_path = (root / config.bibliography.references_path).resolve()
    checks = run_configured_checks(manuscript_report, config, bib_path=bib_path)
    all_passed = all(c.passed for c in checks)
    report_path: Path | None = None
    if write_outputs:
        report_path = (root / "output" / "manuscript_report.json").resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(manuscript_report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        checks_path = (root / "output" / "checks.json").resolve()
        checks_path.parent.mkdir(parents=True, exist_ok=True)
        checks_path.write_text(
            json.dumps([c.to_dict() for c in checks], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return ProseRunArtifacts(
        manuscript_report=manuscript_report,
        report_path=report_path,
        checks=checks,
        all_passed=all_passed,
    )
