"""Declarative prose pipeline checks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol

from infrastructure.prose import ManuscriptReport
from infrastructure.reference.citation import parse_bibfile

from ..config import ProjectConfig


@dataclass
class CheckResult:
    """Outcome of one configured check."""

    name: str
    passed: bool
    message: str = ""
    details: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class CheckRunner(Protocol):
    def __call__(
        self,
        report: ManuscriptReport,
        config: ProjectConfig,
        *,
        bib_path: Path,
    ) -> CheckResult: ...


def _check_grade_level(report: ManuscriptReport, config: ProjectConfig, **_: object) -> CheckResult:
    lo = config.prose.target_grade_level_min
    hi = config.prose.target_grade_level_max
    g = report.avg_flesch_kincaid_grade
    passed = lo <= g <= hi
    return CheckResult(
        name="grade_level_in_band",
        passed=passed,
        message=f"avg FKGL = {g} (target {lo}–{hi})",
        details={"value": g, "min": lo, "max": hi},
    )


def _check_citation_density(report: ManuscriptReport, config: ProjectConfig, **_: object) -> CheckResult:
    threshold = config.prose.citation_density_min_per_1000
    n = max(1, report.total_words)
    citation_count = sum(f.quality.citation_count for f in report.files)
    density = round(1000.0 * citation_count / n, 2)
    passed = density >= threshold
    return CheckResult(
        name="citation_density_above_floor",
        passed=passed,
        message=f"density = {density}/1000 words (min {threshold})",
        details={
            "density_per_1000": density,
            "min": threshold,
            "citation_count": citation_count,
            "unique_keys": len(report.citation_keys),
            "word_count": report.total_words,
        },
    )


def _check_no_skipped_levels(report: ManuscriptReport, config: ProjectConfig, **_: object) -> CheckResult:
    # `config` is unused on purpose: it is retained so every check shares the
    # uniform CheckRunner signature (report, config, *, bib_path). This branch
    # depends only on report.files.
    bad = [f.name for f in report.files if f.structure.has_skipped_level]
    return CheckResult(
        name="no_skipped_heading_levels",
        passed=len(bad) == 0,
        message=f"{len(bad)} file(s) with skipped levels" + (f": {', '.join(bad)}" if bad else ""),
        details={"offending_files": bad},
    )


def _check_h1_per_file(report: ManuscriptReport, config: ProjectConfig, **_: object) -> CheckResult:
    # `config` is unused on purpose (see _check_no_skipped_levels): kept for the
    # uniform CheckRunner signature; this branch depends only on report.files.
    bad = [f.name for f in report.files if not f.structure.has_h1]
    return CheckResult(
        name="every_file_has_h1",
        passed=len(bad) == 0,
        message=f"{len(bad)} file(s) missing H1" + (f": {', '.join(bad)}" if bad else ""),
        details={"offending_files": bad},
    )


def _check_bibliography(
    report: ManuscriptReport,
    config: ProjectConfig,
    *,
    bib_path: Path,
) -> CheckResult:
    if not bib_path.exists():
        return CheckResult(
            name="bibliography_consistency",
            passed=not config.bibliography.fail_on_missing,
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
    if missing and config.bibliography.fail_on_missing:
        passed = False
        msgs.append(f"{len(missing)} cited key(s) missing from bib: {', '.join(missing)}")
    if unused and config.bibliography.fail_on_unused:
        passed = False
        msgs.append(f"{len(unused)} unused bib entries: {', '.join(unused)}")
    if not msgs:
        msgs.append(f"{len(cited_keys)} cited / {len(bib_keys)} in bib · {len(missing)} missing · {len(unused)} unused")

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


@dataclass(frozen=True)
class CheckSpec:
    """One registered pipeline check."""

    name: str
    enabled: Callable[[ProjectConfig], bool]
    run: CheckRunner


CHECK_REGISTRY: tuple[CheckSpec, ...] = (
    CheckSpec("grade_level_in_band", lambda _cfg: True, _check_grade_level),
    CheckSpec("citation_density_above_floor", lambda _cfg: True, _check_citation_density),
    CheckSpec(
        "no_skipped_heading_levels",
        lambda cfg: cfg.prose.forbid_skipped_levels,
        _check_no_skipped_levels,
    ),
    CheckSpec(
        "every_file_has_h1",
        lambda cfg: cfg.prose.require_h1_per_section,
        _check_h1_per_file,
    ),
    CheckSpec("bibliography_consistency", lambda _cfg: True, _check_bibliography),
)


def run_configured_checks(
    report: ManuscriptReport,
    config: ProjectConfig,
    *,
    bib_path: Path,
) -> list[CheckResult]:
    """Run every enabled check from :data:`CHECK_REGISTRY`."""
    checks: list[CheckResult] = []
    for spec in CHECK_REGISTRY:
        if not spec.enabled(config):
            continue
        checks.append(spec.run(report, config, bib_path=bib_path))
    return checks
