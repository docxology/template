"""Interactive menu rendering and dispatch.

Replaces the menu logic that previously lived in ``run.sh``. Pure functions:

- :func:`render_menu` returns a deterministic string given a project name.
  Tests assert on the literal output rather than driving a TTY.
- :func:`parse_choice_sequence` mirrors the bash helper of the same name.
- :data:`MENU_OPTIONS` is the canonical ordered list of menu actions.
"""

from __future__ import annotations

from collections.abc import Iterable

# Stage labels — kept in sync with the names in
# ``infrastructure/core/pipeline/pipeline.yaml``. Used for human-facing
# banners; the executor's authoritative stage list comes from the YAML.
STAGE_NAMES: tuple[str, ...] = (
    "Setup Environment",
    "Infrastructure Tests",
    "Project Tests",
    "Project Analysis",
    "PDF Rendering",
    "Output Validation",
    "LLM Scientific Review",
    "LLM Translations",
    "Copy Outputs",
)


# Canonical menu options. Each tuple is (key, label, description).
MENU_OPTIONS: tuple[tuple[str, str, str], ...] = (
    ("0", "Setup Environment", "00_setup_environment.py"),
    ("1", "Run Tests", "01_run_tests.py (infra + project)"),
    ("2", "Run Analysis", "02_run_analysis.py"),
    ("3", "Render PDF", "03_render_pdf.py"),
    ("4", "Validate Output", "04_validate_output.py"),
    ("5", "Copy Outputs", "05_copy_outputs.py"),
    ("6", "LLM Review", "06_llm_review.py (requires Ollama)"),
    ("7", "LLM Translations", "06_llm_review.py (requires Ollama)"),
    ("8", "Core Pipeline", "[+infra] [-LLM] Core stages"),
    ("9", "Full Pipeline", "[+infra] [+LLM] All 10 stages"),
    ("f", "Full Pipeline (fast)", "[-infra] [+LLM] Skip infra tests"),
    ("a", "All projects full", "[+infra] [+LLM] [+report]"),
    ("b", "All projects full (fast)", "[-infra] [+LLM] [+report]"),
    ("c", "All projects core", "[+infra] [-LLM] [+report]"),
    ("d", "All projects core (fast)", "[-infra] [-LLM] [+report]"),
    ("p", "Change Project", ""),
    ("i", "Show Project Info", ""),
    ("q", "Quit", ""),
)


def menu_keys() -> set[str]:
    """Return the set of valid single-character menu keys."""
    return {key for key, _, _ in MENU_OPTIONS}


def render_menu(current_project: str) -> str:
    """Return a deterministic menu string for the given current project.

    The output omits ANSI colour codes so tests can assert on the literal
    contents. The shell wrapper does not consume this — interactive
    rendering is performed by :func:`run_interactive_menu` below.
    """
    lines: list[str] = []
    lines.append("=" * 64)
    lines.append("  MANUSCRIPT PIPELINE")
    lines.append(f"  Project: {current_project}")
    lines.append("=" * 64)
    lines.append("")
    lines.append("INDIVIDUAL STAGES")
    for key, label, desc in MENU_OPTIONS[:8]:
        suffix = f"  ({desc})" if desc else ""
        lines.append(f"  {key}  {label}{suffix}")
    lines.append("")
    lines.append("ORCHESTRATION")
    for key, label, desc in MENU_OPTIONS[8:11]:
        suffix = f"  ({desc})" if desc else ""
        lines.append(f"  {key}  {label}{suffix}")
    lines.append("")
    lines.append("MULTI-PROJECT")
    for key, label, desc in MENU_OPTIONS[11:15]:
        suffix = f"  ({desc})" if desc else ""
        lines.append(f"  {key}  {label}{suffix}")
    lines.append("")
    lines.append("PROJECT")
    for key, label, _ in MENU_OPTIONS[15:]:
        lines.append(f"  {key}  {label}")
    lines.append("")
    lines.append("Tip: chain digits (e.g. '234' = analyze → render → validate)")
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
