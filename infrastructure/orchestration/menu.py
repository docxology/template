"""Interactive menu rendering and dispatch.

Replaces the menu logic that previously lived in ``run.sh``. Pure functions:

- :func:`render_menu` returns a deterministic string given a project name.
  Tests assert on the literal output rather than driving a TTY.
- :func:`parse_choice_sequence` mirrors the bash helper of the same name.
- :data:`MENU_OPTIONS` is the canonical ordered list of menu actions.

Interactive prompts and the menu redraw loop live in
``infrastructure.orchestration.cli`` (:func:`_interactive`).
"""

from collections.abc import Iterable

# Stage labels — kept in sync with the names in
# ``infrastructure/core/pipeline/pipeline.yaml``. Used for human-facing
# banners; the executor's authoritative stage list comes from the YAML.
STAGE_NAMES: tuple[str, ...] = (
    "Environment Setup",
    "Infrastructure Tests",
    "Project Tests",
    "Project Analysis",
    "PDF Rendering",
    "Output Validation",
    "LLM Scientific Review",
    "LLM Translations",
    "Copy Outputs",
)

# Column width for the middle label field (monospace alignment).
_MENU_LABEL_WIDTH = 30

# Total width for ASCII frame rules and padded header rows (TTY-friendly).
_MENU_FRAME_WIDTH = 74

# Section dividers extend to match the widest menu row (~76 chars).
_SECTION_BAR_WIDTH = 76

# Canonical menu options. Each tuple is (key, label, description).
MENU_OPTIONS: tuple[tuple[str, str, str], ...] = (
    ("0", "Environment Setup", "00_setup_environment.py"),
    ("1", "Run Tests", "01_run_tests.py (infra + project)"),
    ("2", "Run Analysis", "02_run_analysis.py"),
    ("3", "Render PDF", "03_render_pdf.py"),
    ("4", "Validate Output", "04_validate_output.py"),
    ("5", "Copy Outputs", "05_copy_outputs.py"),
    ("6", "LLM Review", "06_llm_review.py reviews (Ollama)"),
    ("7", "LLM Translations", "06_llm_review.py translations (Ollama)"),
    ("8", "Core Pipeline", "current project · infra on · LLM off · 8 stages"),
    ("9", "Full Pipeline", "current project · infra on · LLM on · 10 stages"),
    ("f", "Full Pipeline (fast)", "current project · skip infra · LLM on"),
    ("a", "All projects full", "all projects · infra on · LLM on · report"),
    ("b", "All projects full (fast)", "all projects · skip infra · LLM on · report"),
    ("c", "All projects core", "all projects · infra on · LLM off · report"),
    ("d", "All projects core (fast)", "all projects · skip infra · LLM off · report"),
    ("p", "Change Project", ""),
    ("i", "Show Project Info", ""),
    ("q", "Quit", ""),
)


def menu_keys() -> set[str]:
    """Return the set of valid single-character menu keys."""
    return {key for key, _, _ in MENU_OPTIONS}


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

    # Individual stages — one script per key.
    lines.append(_section_header("INDIVIDUAL STAGES", "one script per key"))
    lines.append("")
    for key, label, desc in MENU_OPTIONS[:8]:
        lines.append(_menu_row(key, label, desc))
    lines.append("")

    # Orchestration — full DAG against the currently-selected project.
    lines.append(_section_header("ORCHESTRATION", "full DAG, current project"))
    lines.append("")
    for key, label, desc in MENU_OPTIONS[8:11]:
        lines.append(_menu_row(key, label, desc))
    lines.append("")

    # Multi-project — sweep every discovered project.
    lines.append(_section_header("MULTI-PROJECT", "every discovered project"))
    lines.append("")
    for key, label, desc in MENU_OPTIONS[11:15]:
        lines.append(_menu_row(key, label, desc))
    lines.append("")

    # Project controls.
    lines.append(_section_header("PROJECT"))
    lines.append("")
    for key, label, _ in MENU_OPTIONS[15:]:
        lines.append(_menu_row(key, label, ""))
    lines.append("")

    # Legend — kept on stable wording so tests assert on literal substrings.
    footer_bar = _ascii_rule("-", fw)
    lines.append(footer_bar)
    lines.append("  Infra tests: Layer-1 pytest (tests/infra_tests/), then project tests.")
    lines.append("  LLM: optional Ollama stages; pipeline skips them when Ollama is unavailable.")
    lines.append("  Executive report: written after all projects finish (keys a-d only).")
    lines.append(footer_bar)
    lines.append("")
    lines.append("  Tip: chain stage digits (e.g. 234 = analyze -> render -> validate); comma or space also work.")
    lines.append(
        "       use  p  to switch project  ·  i  for current name  ·  q  to quit.",
    )
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
