"""Source-level readiness contract for the Autopoiesis manuscript lane."""

from __future__ import annotations

from pathlib import Path
import re

REQUIRED_MANUSCRIPT_FILES: tuple[str, ...] = (
    "00_abstract.md",
    "01_introduction.md",
    "02_methods.md",
    "03_results.md",
    "04_honesty.md",
    "05_reproducibility.md",
    "06_limitations.md",
    "99_references.md",
    "preamble.md",
    "config.yaml",
)
PREAMBLE_START = "% BEGIN TEMPLATE_AUTOPOIESIS_PREAMBLE"
PREAMBLE_END = "% END TEMPLATE_AUTOPOIESIS_PREAMBLE"
REQUIRED_SPEC_PHASES = tuple(f"P{index}" for index in range(11))


def validate_phase10_contract(project_root: str | Path) -> list[str]:
    """Return actionable findings for the source-bound manuscript contract.

    This gate verifies the deterministic part of Phase 10.  Renderer/tool
    availability and visual QA remain explicit external or optional-tool
    evidence; source readiness must still be complete before those tools run.
    """
    root = Path(project_root)
    manuscript = root / "manuscript"
    issues: list[str] = []
    for relative in REQUIRED_MANUSCRIPT_FILES:
        path = manuscript / relative
        if not path.is_file():
            issues.append(f"missing manuscript file: {relative}")
        elif not path.read_text(encoding="utf-8").strip():
            issues.append(f"empty manuscript file: {relative}")

    preamble_path = manuscript / "preamble.md"
    if preamble_path.is_file():
        preamble = preamble_path.read_text(encoding="utf-8")
        if preamble.count(PREAMBLE_START) != 1 or preamble.count(PREAMBLE_END) != 1:
            issues.append("preamble must contain exactly one explicit start and end fence")
        elif preamble.index(PREAMBLE_START) > preamble.index(PREAMBLE_END):
            issues.append("preamble start fence must precede its end fence")
        if re.search(r"(?m)^\s*\\geometry\{", preamble):
            issues.append("preamble must not override config-driven geometry")

    spec_path = root / "SPEC.md"
    if not spec_path.is_file():
        issues.append("missing SPEC.md")
    else:
        spec = spec_path.read_text(encoding="utf-8")
        for phase in REQUIRED_SPEC_PHASES:
            if f"{phase} —" not in spec and f"{phase} --" not in spec:
                issues.append(f"SPEC.md is missing {phase} checklist")
        if "P10" in spec and "Phase 10" not in spec:
            issues.append("SPEC.md P10 heading must name Phase 10")

    return issues


__all__ = [
    "PREAMBLE_END",
    "PREAMBLE_START",
    "REQUIRED_MANUSCRIPT_FILES",
    "validate_phase10_contract",
]
