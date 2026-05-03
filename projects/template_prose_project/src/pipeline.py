"""Pure orchestration of the prose review pipeline.

* Reads the manuscript directory.
* Runs :func:`infrastructure.prose.analyze_manuscript` to produce a
  `ManuscriptReport`.
* Cross-checks `[@key]` citations against the bibliography
  (`infrastructure.reference.citation`).
* Evaluates configured thresholds and writes pass/fail flags.

There is no figure rendering or LLM call here — those live in the
script and `figures.py`.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from infrastructure.prose import ManuscriptReport, analyze_manuscript, write_report
from infrastructure.reference.citation import parse_bibfile

from .config import ProjectConfig


@dataclass
class CheckResult:
    """Outcome of one configured check."""

    name: str
    passed: bool
    message: str = ""
    details: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class ProseRunArtifacts:
    """Outputs of a single :func:`run_prose_pipeline` call.

    Attributes:
        manuscript_report: Raw `ManuscriptReport` from the prose module.
        report_path: Where ``manuscript_report.json`` was written.
        checks: One :class:`CheckResult` per configured threshold check.
        all_passed: Convenience flag — ``all(c.passed for c in checks)``.
    """

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


def _check_grade_level(report: ManuscriptReport, lo: float, hi: float) -> CheckResult:
    g = report.avg_flesch_kincaid_grade
    passed = lo <= g <= hi
    return CheckResult(
        name="grade_level_in_band",
        passed=passed,
        message=f"avg FKGL = {g} (target {lo}–{hi})",
        details={"value": g, "min": lo, "max": hi},
    )


def _check_citation_density(report: ManuscriptReport, threshold: float) -> CheckResult:
    n = max(1, report.total_words)
    density = round(1000.0 * len(report.citation_keys) / n, 2)
    passed = density >= threshold
    return CheckResult(
        name="citation_density_above_floor",
        passed=passed,
        message=f"density = {density}/1000 words (min {threshold})",
        details={
            "density_per_1000": density,
            "min": threshold,
            "citation_count": len(report.citation_keys),
            "word_count": report.total_words,
        },
    )


def _check_no_skipped_levels(report: ManuscriptReport) -> CheckResult:
    bad = [f.name for f in report.files if f.structure.has_skipped_level]
    return CheckResult(
        name="no_skipped_heading_levels",
        passed=len(bad) == 0,
        message=f"{len(bad)} file(s) with skipped levels"
        + (f": {', '.join(bad)}" if bad else ""),
        details={"offending_files": bad},
    )


def _check_h1_per_file(report: ManuscriptReport) -> CheckResult:
    bad = [f.name for f in report.files if not f.structure.has_h1]
    return CheckResult(
        name="every_file_has_h1",
        passed=len(bad) == 0,
        message=f"{len(bad)} file(s) missing H1"
        + (f": {', '.join(bad)}" if bad else ""),
        details={"offending_files": bad},
    )


def _check_bibliography(
    report: ManuscriptReport,
    bib_path: Path,
    *,
    fail_on_missing: bool,
    fail_on_unused: bool,
) -> CheckResult:
    if not bib_path.exists():
        return CheckResult(
            name="bibliography_consistency",
            passed=not fail_on_missing,
            message=f"bibliography not found at {bib_path}",
            details={"bib_path": str(bib_path)},
        )
    db = parse_bibfile(bib_path)
    bib_keys = set(db.keys())
    cited_keys = set(report.citation_keys)
    missing = sorted(cited_keys - bib_keys)
    unused = sorted(bib_keys - cited_keys)

    passed = True
    msgs: list[str] = []
    if missing and fail_on_missing:
        passed = False
        msgs.append(f"{len(missing)} cited key(s) missing from bib: {', '.join(missing)}")
    if unused and fail_on_unused:
        passed = False
        msgs.append(f"{len(unused)} unused bib entries: {', '.join(unused)}")
    if not msgs:
        msgs.append(
            f"{len(cited_keys)} cited / {len(bib_keys)} in bib · "
            f"{len(missing)} missing · {len(unused)} unused"
        )

    return CheckResult(
        name="bibliography_consistency",
        passed=passed,
        message=" · ".join(msgs),
        details={
            "missing": missing,
            "unused": unused,
            "cited_count": len(cited_keys),
            "bib_count": len(bib_keys),
        },
    )


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

    checks: list[CheckResult] = [
        _check_grade_level(
            report,
            config.prose.target_grade_level_min,
            config.prose.target_grade_level_max,
        ),
        _check_citation_density(report, config.prose.citation_density_min_per_1000),
    ]
    if config.prose.forbid_skipped_levels:
        checks.append(_check_no_skipped_levels(report))
    if config.prose.require_h1_per_section:
        checks.append(_check_h1_per_file(report))

    bib_path = (root / config.bibliography.references_path).resolve()
    checks.append(
        _check_bibliography(
            report,
            bib_path,
            fail_on_missing=config.bibliography.fail_on_missing,
            fail_on_unused=config.bibliography.fail_on_unused,
        )
    )

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
