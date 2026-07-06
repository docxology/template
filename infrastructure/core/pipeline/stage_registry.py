"""Canonical stage-key dispatch for single-stage pipeline runs.

Single source of truth for ``execute_pipeline.py --stage``, ``single_stage.py``,
and the interactive orchestration menu (via :data:`MENU_KEY_TO_STAGE`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

__all__ = [
    "MENU_KEY_TO_STAGE",
    "STAGE_DISPATCH",
    "StageDispatch",
    "known_stage_keys",
    "normalize_stage_key",
    "script_argv_for_stage",
]


@dataclass(frozen=True, slots=True)
class StageDispatch:
    """Relative script path under the repo root plus fixed CLI args."""

    script: str
    args: tuple[str, ...] = ()


# Note: there is no ``"clean"`` key. "Clean Output Directories" (stage 0 in the
# vocabulary) is an executor built-in (``_run_clean_outputs``), not a standalone
# script — a ``"clean"`` dispatch here previously pointed at 00_setup_environment.py
# and so ``--stage clean`` silently ran *setup* and cleaned nothing. Single-stage
# dispatch only covers stages backed by a runnable script.
STAGE_DISPATCH: Final[dict[str, StageDispatch]] = {
    "setup": StageDispatch("scripts/pipeline/stage_00_setup.py"),
    "infra_tests": StageDispatch(
        "scripts/pipeline/stage_01_test.py",
        ("--infra-only", "--verbose", "--infra-scope", "pipeline-smoke"),
    ),
    "project_tests": StageDispatch("scripts/pipeline/stage_01_test.py", ("--project-only", "--verbose")),
    "tests": StageDispatch("scripts/pipeline/stage_01_test.py", ("--verbose", "--infra-scope", "pipeline-smoke")),
    "analysis": StageDispatch("scripts/pipeline/stage_02_analysis.py"),
    "render_pdf": StageDispatch("scripts/pipeline/stage_03_render.py"),
    "validate": StageDispatch("scripts/pipeline/stage_04_validate.py"),
    "copy": StageDispatch("scripts/pipeline/stage_05_copy.py"),
    "llm_reviews": StageDispatch("scripts/pipeline/stage_06_llm_review.py", ("--reviews-only",)),
    "llm_translations": StageDispatch("scripts/pipeline/stage_06_llm_review.py", ("--translations-only",)),
    "executive_report": StageDispatch("scripts/pipeline/stage_07_executive_report.py"),
    "ebook_generation": StageDispatch("scripts/pipeline/stage_11_ebook.py"),
    "metadata_package": StageDispatch("scripts/pipeline/stage_12_metadata.py"),
}

MENU_KEY_TO_STAGE: Final[dict[str, str]] = {
    "0": "setup",
    "1": "tests",
    "2": "analysis",
    "3": "render_pdf",
    "4": "validate",
    "5": "copy",
    "6": "llm_reviews",
    "7": "llm_translations",
}


def known_stage_keys() -> frozenset[str]:
    """Return valid ``--stage`` / ``execute_single_stage`` keys."""
    return frozenset(STAGE_DISPATCH)


def normalize_stage_key(stage: str) -> str:
    return stage.strip().lower()


def script_argv_for_stage(stage: str) -> tuple[str, ...]:
    """Return ``(script_rel, *args)`` for *stage* or raise ``SystemExit``."""
    key = normalize_stage_key(stage)
    if key not in STAGE_DISPATCH:
        valid = ", ".join(sorted(STAGE_DISPATCH))
        raise SystemExit(f"Unknown stage '{stage}'. Valid: {valid}")
    dispatch = STAGE_DISPATCH[key]
    return (dispatch.script, *dispatch.args)
