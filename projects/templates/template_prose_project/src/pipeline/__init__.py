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
    "EVIDENCE_SUMMARY_SCHEMA_VERSION",
    "ProseRunArtifacts",
    "build_evidence_summary",
    "run_configured_checks",
    "run_prose_pipeline",
]

EVIDENCE_SUMMARY_SCHEMA_VERSION = "template-prose/evidence-summary/1"


def build_evidence_summary(
    manuscript_report: ManuscriptReportLike,
    checks: list[CheckResult],
) -> dict[str, object]:
    """Build a machine-readable diagnostic summary without publication claims.

    The summary deliberately keeps readability, citations, bibliography, and
    structure separate. It is evidence about the configured review run, not an
    approval or quality certification.
    """
    files = manuscript_report.files
    quality = {
        "long_sentence_count": sum(f.quality.long_sentence_count for f in files),
        "passive_count": sum(f.quality.passive_count for f in files),
        "hedge_count": sum(f.quality.hedge_count for f in files),
    }
    structure = {
        "files_with_h1": sum(f.structure.has_h1 for f in files),
        "files_with_skipped_levels": sum(f.structure.has_skipped_level for f in files),
        "heading_count": sum(len(f.structure.headings) for f in files),
    }
    bibliography = next((check.details for check in checks if check.name == "bibliography_consistency"), {})
    citation_count = sum(f.quality.citation_count for f in files)
    citations = {
        "unique_keys": len(manuscript_report.citation_keys),
        "citation_count": citation_count,
        "density_per_1000": round(1000.0 * citation_count / max(1, manuscript_report.total_words), 2),
    }
    return {
        "schema_version": EVIDENCE_SUMMARY_SCHEMA_VERSION,
        "status": "pass" if all(check.passed for check in checks) else "fail",
        "diagnostic_only": True,
        "metrics": {
            "readability": {
                "avg_flesch_reading_ease": manuscript_report.avg_flesch_reading_ease,
                "avg_flesch_kincaid_grade": manuscript_report.avg_flesch_kincaid_grade,
                "avg_gunning_fog": manuscript_report.avg_gunning_fog,
            },
            "citations": citations,
            "bibliography": bibliography,
            "structure": structure,
            "quality_flags": quality,
        },
        "checks": [check.to_dict() for check in checks],
    }


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
    evidence_summary_path: Path | None = None
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
            "evidence_summary_path": str(self.evidence_summary_path) if self.evidence_summary_path else None,
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
    evidence_summary_path: Path | None = None
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

        evidence_summary_path = (root / "output" / "evidence_summary.json").resolve()
        evidence_summary_path.write_text(
            json.dumps(build_evidence_summary(manuscript_report, checks), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return ProseRunArtifacts(
        manuscript_report=manuscript_report,
        report_path=report_path,
        checks=checks,
        all_passed=all_passed,
        evidence_summary_path=evidence_summary_path,
    )
