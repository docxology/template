"""Pure orchestration of the prose review pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from infrastructure.prose import ManuscriptReport, analyze_manuscript, write_report

from ..config import ProjectConfig
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
    """Outputs of a single :func:`run_prose_pipeline` call."""

    manuscript_report: ManuscriptReport
    report_path: Path | None = None
    checks: list[CheckResult] = field(default_factory=list)
    all_passed: bool = True

    @property
    def total_words(self) -> int:
        return self.manuscript_report.total_words

    def to_dict(self) -> dict[str, object]:
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
    write_outputs: bool = True,
) -> ProseRunArtifacts:
    """Run the configured prose review pipeline."""
    root = Path(project_root)
    manuscript_dir = (root / config.manuscript_dir).resolve()
    report = analyze_manuscript(
        manuscript_dir,
        long_sentence_threshold=config.prose.long_sentence_threshold,
    )

    bib_path = (root / config.bibliography.references_path).resolve()
    checks = run_configured_checks(report, config, bib_path=bib_path)
    all_passed = all(c.passed for c in checks)
    report_path: Path | None = None
    if write_outputs:
        report_path = (root / "output" / "manuscript_report.json").resolve()
        write_report(report, report_path)

        checks_path = (root / "output" / "checks.json").resolve()
        checks_path.parent.mkdir(parents=True, exist_ok=True)
        checks_path.write_text(
            json.dumps([c.to_dict() for c in checks], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return ProseRunArtifacts(
        manuscript_report=report,
        report_path=report_path,
        checks=checks,
        all_passed=all_passed,
    )
