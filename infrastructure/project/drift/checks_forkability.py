"""Forkability contract drift checks for public template exemplars."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.files.serialization import relative_or_self as _rel
from infrastructure.project.domain_profile import load_domain_profile
from infrastructure.project.drift.checks_exemplar import _read
from infrastructure.project.drift.models import Report
from infrastructure.project.experiment_plan import load_experiment_plan, validate_experiment_plan

_UNSAFE_RAW_COPY_RE = re.compile(
    r"\bcp\s+-[A-Za-z]*[rR][A-Za-z]*\s+[^`\n]*projects/templates/",
)
_UNSAFE_RSYNC_RE = re.compile(
    r"\brsync\s+-[A-Za-z]*\s+[^`\n]*projects/templates/",
)


def check_forkability_contract(project_root: Path, report: Report, project: str) -> None:
    """Public exemplars must be clean-copy forkable and carry valid overlays."""
    standalone = project_root / "STANDALONE.md"
    if not standalone.is_file():
        report.add(
            "ERROR",
            project,
            "missing_standalone_doc",
            f"{project}/STANDALONE.md is missing — exemplar lacks a standalone fork guide",
        )

    profile_path = project_root / "domain_profile.yaml"
    if not profile_path.is_file():
        report.add(
            "ERROR",
            project,
            "missing_domain_profile",
            f"{project}/domain_profile.yaml is missing — exemplar lacks a project metadata overlay",
        )
    else:
        try:
            profile = load_domain_profile(project_root)
        except ValueError as exc:
            report.add("ERROR", project, "invalid_domain_profile", f"{project}/domain_profile.yaml: {exc}")
        else:
            if profile.domain == "generic":
                report.add(
                    "ERROR",
                    project,
                    "generic_domain_profile",
                    f"{project}/domain_profile.yaml still declares the generic profile",
                )

    plan_path = project_root / "experiment_plan.yaml"
    if not plan_path.is_file():
        report.add(
            "ERROR",
            project,
            "missing_experiment_plan",
            f"{project}/experiment_plan.yaml is missing — exemplar lacks a design plan overlay",
        )
    else:
        try:
            plan = load_experiment_plan(project_root)
            validation = validate_experiment_plan(plan)
        except ValueError as exc:
            report.add("ERROR", project, "invalid_experiment_plan", f"{project}/experiment_plan.yaml: {exc}")
        else:
            if not validation.valid:
                report.add(
                    "ERROR",
                    project,
                    "invalid_experiment_plan",
                    f"{project}/experiment_plan.yaml is invalid: {list(validation.issues)}",
                )

    for md in _fork_doc_candidates(project_root):
        text = _read(md)
        for match in _UNSAFE_RAW_COPY_RE.finditer(text):
            report.add(
                "ERROR",
                project,
                "unsafe_fork_copy",
                (
                    f"{_rel(md, project_root)} recommends raw recursive copy near "
                    f"{match.group(0)!r}; use scripts/copy_exemplar.py or rsync exclusions"
                ),
            )
        for match in _UNSAFE_RSYNC_RE.finditer(text):
            report.add(
                "ERROR",
                project,
                "unsafe_fork_copy",
                (
                    f"{_rel(md, project_root)} recommends rsync without exclusions near "
                    f"{match.group(0)!r}; use scripts/copy_exemplar.py or rsync exclusions"
                ),
            )


def _fork_doc_candidates(project_root: Path) -> list[Path]:
    candidates = sorted(project_root.glob("*.md"))
    docs = project_root / "docs"
    if docs.is_dir():
        candidates.extend(sorted(docs.rglob("*.md")))
    return candidates


__all__ = ["check_forkability_contract"]
