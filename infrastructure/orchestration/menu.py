"""Interactive menu rendering and dispatch.

Replaces the menu logic that previously lived in ``run.sh``. Pure functions:

- :func:`render_menu` returns a deterministic string given a project name.
  Tests assert on the literal output rather than driving a TTY.
- :func:`parse_choice_sequence` mirrors the bash helper of the same name.
- :data:`MENU_OPTIONS` exposes the ordered display rows from the action catalog.

Interactive prompts and the menu redraw loop live in
``infrastructure.orchestration.cli`` (:func:`_interactive`).
"""

from collections.abc import Iterable
from dataclasses import dataclass, replace
from typing import Literal

from infrastructure.core.pipeline.stage_registry import MENU_KEY_TO_STAGE
from infrastructure.core.pipeline.stage_vocabulary import (
    menu_stage_names,
)

# Stage labels from ``infrastructure/core/pipeline/pipeline.yaml`` via stage_vocabulary.
STAGE_NAMES: tuple[str, ...] = menu_stage_names()

# Column width for the middle label field (monospace alignment).
_MENU_LABEL_WIDTH = 30

# Total width for ASCII frame rules and padded header rows (TTY-friendly).
_MENU_FRAME_WIDTH = 74

# Section dividers extend to match the widest menu row (~76 chars).
_SECTION_BAR_WIDTH = 76


@dataclass(frozen=True)
class MenuAction:
    """Display and invocation policy for one menu choice."""

    section: Literal["stage", "pipeline", "multi", "project"]
    label: str
    detail: str = ""
    stage: str | None = None
    mode: Literal["core", "live"] = "core"
    skip_infra: bool = False
    control: Literal["select", "info", "quit"] | None = None
    exit_when_alone: bool = False


_STAGE_ACTIONS: dict[str, MenuAction] = {
    "setup": MenuAction("stage", "Environment Setup", "stage_00_setup.py"),
    "project_tests": MenuAction("stage", "Run Project Tests", "stage_01_test.py (project only)"),
    "analysis": MenuAction("stage", "Run Analysis", "stage_02_analysis.py"),
    "render_pdf": MenuAction("stage", "Render PDF", "stage_03_render.py"),
    "validate": MenuAction("stage", "Validate Output", "stage_04_validate.py"),
    "copy": MenuAction("stage", "Copy Outputs", "stage_05_copy.py"),
    "llm_reviews": MenuAction("stage", "LLM Review", "stage_06_llm_review.py reviews (Ollama)", mode="live"),
    "llm_translations": MenuAction(
        "stage", "LLM Translations", "stage_06_llm_review.py translations (Ollama)", mode="live"
    ),
}


_MENU_ACTIONS: dict[str, MenuAction] = {
    **{key: replace(_STAGE_ACTIONS[stage], stage=stage) for key, stage in MENU_KEY_TO_STAGE.items()},
    "8": MenuAction("pipeline", "Core Pipeline", "current project · infra on · local stages"),
    "9": MenuAction("pipeline", "Live Pipeline", "current project · infra on · live stages", mode="live"),
    "f": MenuAction(
        "pipeline", "Live Pipeline (fast)", "current project · skip infra · LLM on", mode="live", skip_infra=True
    ),
    "a": MenuAction("multi", "All projects live", "all projects · infra on · LLM on · report", mode="live"),
    "b": MenuAction(
        "multi", "All projects live (fast)", "all projects · skip infra · LLM on · report", mode="live", skip_infra=True
    ),
    "c": MenuAction("multi", "All projects core", "all projects · infra on · LLM off · report"),
    "d": MenuAction(
        "multi",
        "All projects core (fast)",
        "all projects · skip infra · LLM off · report",
        skip_infra=True,
        exit_when_alone=True,
    ),
    "p": MenuAction("project", "Change Project", control="select"),
    "i": MenuAction("project", "Show Project Info", control="info"),
    "q": MenuAction("project", "Quit", control="quit"),
}

MENU_OPTIONS: tuple[tuple[str, str, str], ...] = tuple(
    (key, action.label, action.detail) for key, action in _MENU_ACTIONS.items()
)

_MENU_SECTIONS = (
    ("stage", "INDIVIDUAL STAGES", "one script per key"),
    ("pipeline", "ORCHESTRATION", "full DAG, current project"),
    ("multi", "MULTI-PROJECT", "every discovered project"),
    ("project", "PROJECT", ""),
)


def menu_action(key: str) -> MenuAction | None:
    """Look up a parsed menu choice."""
    return _MENU_ACTIONS.get(key)


def menu_keys() -> set[str]:
    """Return the set of valid single-character menu keys."""
    return set(_MENU_ACTIONS)


def _menu_row(key: str, label: str, detail: str) -> str:
    """One monospace-aligned menu line (key | label | detail)."""
    label_slot = label.ljust(_MENU_LABEL_WIDTH)
    if detail:
        return f"  {key:>2}  | {label_slot} | {detail}"
    return f"  {key:>2}  | {label_slot}"


def _section_header(title: str, subtitle: str = "") -> str:
    """Return a section divider padded to ``_SECTION_BAR_WIDTH`` (ASCII hyphens)."""
    label = f" {title} - {subtitle} " if subtitle else f" {title} "
    prefix = "  --"
    line = prefix + label
    fill = max(0, _SECTION_BAR_WIDTH - len(line))
    return line + ("-" * fill)


def _ascii_rule(char: str, width: int) -> str:
    """Repeat ``char`` to ``width`` (``char`` must be a single ASCII character)."""
    return char * width


def _box_top_bottom(width: int) -> str:
    """Top or bottom rule: ``+`` + ``=``*(width-2) + ``+``."""
    inner = max(1, width - 2)
    return "+" + ("=" * inner) + "+"


def _box_row(text: str, width: int) -> str:
    """One framed row ``|`` + padded text + ``|``; ``width`` is total line length."""
    inner = max(1, width - 4)  # "| " ... " |"
    body = text
    if len(body) > inner:
        body = body[: inner - 3] + "..."
    padded = body.ljust(inner)
    return "| " + padded + " |"


def render_menu(current_project: str) -> str:
    """Return a deterministic menu string for the given current project.

    The output omits ANSI colour codes so tests can assert on the literal
    contents. The shell wrapper does not consume this — interactive use
    prints this string from :func:`infrastructure.orchestration.cli._interactive`.

    Framing uses ASCII only (``+=|-``) for wide terminal/font compatibility.
    """
    lines: list[str] = []
    fw = _MENU_FRAME_WIDTH

    # Header — boxed title; "MANUSCRIPT PIPELINE" appears once (contract tests).
    lines.append(_box_top_bottom(fw))
    lines.append(
        _box_row("   MANUSCRIPT PIPELINE  ·  thin orchestrator template", fw),
    )
    lines.append(_box_row(f"   project > {current_project}", fw))
    lines.append(_box_top_bottom(fw))
    lines.append("")
    lines.append(
        "   Single stages 0-7   ·   Presets 8 / 9 / f   ·   Multi a-d   ·   p · i · q",
    )
    lines.append(
        "   Keys 0-5: setup, tests, analysis, render, validate, copy  |  "
        "6-7: LLM (Ollama)  |  8/9/f: pipelines  |  a-d: all projects",
    )
    lines.append(
        "   Flow:  [0..5] script chain  +  (6,7) LLM  |  8/9/f DAG presets  |  a-d multi-project",
    )
    lines.append("")
    lines.append("")

    for section, title, subtitle in _MENU_SECTIONS:
        lines.append(_section_header(title, subtitle))
        lines.append("")
        lines.extend(
            _menu_row(key, action.label, action.detail)
            for key, action in _MENU_ACTIONS.items()
            if action.section == section
        )
        lines.append("")

    # Legend — kept on stable wording so tests assert on literal substrings.
    footer_bar = _ascii_rule("-", fw)
    lines.append(footer_bar)
    lines.append("  Infrastructure verification runs once before multi-project execution; key 1 runs project tests.")
    lines.append("  Live: optional Ollama stages; unavailable capabilities require a validated skip receipt.")
    lines.append("  Executive reports follow each project’s declared pipeline; multi-project runs add a summary.")
    lines.append(footer_bar)
    lines.append("")
    lines.append("  Tip: chain stage digits (e.g. 234 = analyze -> render -> validate); comma or space also work.")
    lines.append(
        "       use  p  to switch project  ·  i  for current name  ·  q  to quit.",
    )
    lines.append("")

    # Opt-in workflows — not reachable via a menu key; invoked directly.
    lines.append(_section_header("OTHER WORKFLOWS", "opt-in, run directly (not in this menu)"))
    lines.append("")
    lines.append("  Secure + watermark  | ./secure_run.sh --project <name>            (steganography PDF)")
    lines.append("  Steganography only  | ./secure_run.sh --steganography-only        (re-watermark, no re-render)")
    lines.append("  Ebook formats       | uv run python scripts/pipeline/stage_11_ebook.py --project <name>")
    lines.append("  Metadata package    | uv run python scripts/pipeline/stage_12_metadata.py --project <name>")
    lines.append("  Executable bundle   | uv run python scripts/runner/bundle_executable.py --project <name>")
    lines.append(
        "  Archival deposit    | uv run python scripts/runner/archive_publication.py "
        "--project <name>  (dry-run by default)"
    )
    lines.append(
        "  Full release        | uv run python scripts/publish/publish_project_release.py "
        "--project <name> --repo owner/repo"
    )
    lines.append("  Credential check    | uv run python -m infrastructure.publishing.credential_check --env-file .env")
    lines.append("  Reproducible matrix | uv run python scripts/runner/run_matrix.py                (reads run.config)")
    lines.append("  Repro bundle        | uv run python scripts/runner/repro_bundle.py build <name>")
    lines.append("  See docs/guides/publishing-guide.md and docs/maintenance/archival-targets.md for details.")
    return "\n".join(lines)


def parse_choice_sequence(raw: str) -> list[str]:
    """Parse a menu input into a sequence of menu keys.

    Mirrors the bash helper of the same name:

    - ``"234"`` → ``["2", "3", "4"]``
    - ``"3,4,5"`` → ``["3", "4", "5"]``
    - ``"3 4 5"`` → ``["3", "4", "5"]``
    - ``"a"`` → ``["a"]``
    - ``""`` → ``[]``

    Raises:
        ValueError: when the input contains a token that isn't a valid
            menu key.
    """
    if raw is None:
        return []
    cleaned = raw.strip()
    if not cleaned:
        return []

    valid = menu_keys()

    # Concatenated digits (e.g. "234")
    if cleaned.isdigit() and len(cleaned) > 1:
        keys = list(cleaned)
        for k in keys:
            if k not in valid:  # pragma: no cover - all single digits 0-9 are valid menu keys
                raise ValueError(f"invalid menu key: {k!r}")
        return keys

    # Comma- or space-separated tokens
    tokens: Iterable[str]
    if "," in cleaned:
        tokens = (t.strip() for t in cleaned.split(","))
    elif " " in cleaned:
        tokens = cleaned.split()
    else:
        tokens = [cleaned]

    out: list[str] = []
    for tok in tokens:
        if not tok:
            continue
        if tok not in valid:
            raise ValueError(f"invalid menu key: {tok!r}")
        out.append(tok)
    return out
