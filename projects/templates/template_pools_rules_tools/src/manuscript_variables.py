"""manuscript_variables.py — Derive manuscript token values from the integration demo.

Shared by ``scripts/03_generate_manuscript.py`` (analysis-stage JSON export)
and ``scripts/z_generate_manuscript_variables.py`` (pre-render token
hydration + injection), so the token computation lives in exactly one place.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from .figure_support import COVER_FIGURE_FILENAMES, INTEGRATION_FIGURE_SPECS, IntegrationFigureSpec
from .integration import run_integration_demo
from .type_defs import IntegrationResult

__all__ = ["generate_variables"]

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _filesystem_counts(project_root: Path) -> tuple[int, int, int]:
    """Count the project-owned Python source, test, and orchestration files."""
    source_modules = sum(
        path.is_file() and path.name != "__init__.py"
        for path in (project_root / "src").glob("*.py")
    )
    test_files = sum(path.is_file() for path in (project_root / "tests").glob("test_*.py"))
    orchestration_scripts = sum(
        path.is_file() and path.name != "__init__.py"
        for path in (project_root / "scripts").glob("*.py")
    )
    return source_modules, test_files, orchestration_scripts


def generate_variables(
    *,
    integration_runner: Callable[[], IntegrationResult] = run_integration_demo,
    content_figure_specs: Sequence[IntegrationFigureSpec] = INTEGRATION_FIGURE_SPECS,
    cover_figure_filenames: Sequence[str] = COVER_FIGURE_FILENAMES,
    project_root: Path = _PROJECT_ROOT,
) -> dict[str, str]:
    """Derive stringified manuscript token values from the integration demo results.

    Returns a flat ``{{UPPERCASE_KEY}}``-compatible mapping (all values
    stringified) suitable for
    :func:`infrastructure.rendering.manuscript_injection.write_resolved_manuscript_tree`.
    """
    results = integration_runner()
    summary = results["summary"]
    rules = results["rules"]
    content_figure_count = len(content_figure_specs)
    cover_figure_count = len(cover_figure_filenames)
    source_module_count, test_file_count, orchestration_script_count = _filesystem_counts(
        project_root
    )

    variables: dict[str, object] = {
        "FONDS_LOADED": summary["fonds_loaded"],
        "FONDS_EXPECTED": len(results["fonds"]),
        "RULES_SETS_OK": summary["rules_sets_ok"],
        "RULES_SETS_TOTAL": summary["rules_sets_total"],
        "TOOLS_DISCOVERED": summary["tools_discovered"],
        "TOOLS_VALID": summary["tools_valid"],
        "BIB_ENTRIES": summary["bib_entries"],
        "CONTACTS_COUNT": summary["contacts"],
        "DATASETS_COUNT": summary["datasets"],
        "STRONG_RULES_PROJECT": (
            rules["template_project_rules"]["strong_rules_count"]
            if "template_project_rules" in rules
            else 0
        ),
        "STRONG_RULES_MANUSCRIPT": (
            rules["template_manuscript_rules"]["strong_rules_count"]
            if "template_manuscript_rules" in rules
            else 0
        ),
        "CONTENT_FIGURES": content_figure_count,
        "COVER_FIGURES": cover_figure_count,
        "TOTAL_FIGURES": content_figure_count + cover_figure_count,
        "SRC_MODULES": source_module_count,
        "TEST_FILES": test_file_count,
        "ORCHESTRATION_SCRIPTS": orchestration_script_count,
        "TOOL_NAMES": ", ".join(t["name"] for t in results["tools"]),
    }

    return {key: str(value) for key, value in variables.items()}
