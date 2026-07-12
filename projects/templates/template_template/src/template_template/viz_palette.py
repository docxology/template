"""Shared palette and drawing helpers for architecture figures."""

from __future__ import annotations

import matplotlib.colors as mcolors

from .introspection import ModuleInfo, PipelineStage

ARCH_VIZ_COLORS = {
    "infra": "#0072B2",
    "infra_dark": "#004F7F",
    "project": "#D55E00",
    "project_dark": "#A34500",
    "pipeline": "#009E73",
    "accent": "#CC79A7",
    "neutral": "#666666",
    "bg_infra": "#ddeeff",
    "bg_project": "#fff0e0",
    "bg_pipeline": "#e8f5e9",
    "white": "#ffffff",
    "text_dark": "#1a1a1a",
    "text_light": "#555555",
    "shadow": "#cccccc",
    "divider": "#bbbbbb",
}

# Publication-policy constants live here so figures, tests, and manuscript
# metrics all read the same values.  Keeping the render resolution beside the
# palette also removes four independent ``dpi=...`` literals from the figure
# builders.
FONT_FLOOR = 16
FIGURE_DPI = 200

_TAG_COLORS = {
    "core": ARCH_VIZ_COLORS["pipeline"],
    "llm": ARCH_VIZ_COLORS["accent"],
    "bundle": "#E69F00",
    "archival": "#56B4E9",
    "clean": ARCH_VIZ_COLORS["neutral"],
    "tests": "#0072B2",
}


def stage_color(stage: PipelineStage) -> tuple[float, float, float, float]:
    """Pick a fill colour from the first recognised stage tag."""
    for tag in stage.tags:
        if tag in _TAG_COLORS:
            return mcolors.to_rgba(_TAG_COLORS[tag])
    return mcolors.to_rgba(ARCH_VIZ_COLORS["pipeline"])


def short_stage_label(name: str) -> str:
    """Compact label for pipeline boxes."""
    overrides = {
        "Clean Output Directories": "Clean",
        "Environment Setup": "Setup",
        "Infrastructure Tests": "Infra Tests",
        "Project Tests": "Proj Tests",
        "Project Analysis": "Analysis",
        "PDF Rendering": "Render PDF",
        "Output Validation": "Validate",
        "LLM Scientific Review": "LLM Review",
        "LLM Translations": "LLM Trans",
        "Copy Outputs": "Copy Out",
        "Executable Bundle": "Bundle",
        "Archival Publication": "Archive",
    }
    return overrides.get(name, name)


def doc_badge(module: ModuleInfo) -> str:
    """Build a compact 4-letter doc-coverage badge for *module*."""
    parts = [
        "A" if module.has_agents_md else "·",
        "R" if module.has_readme_md else "·",
        "S" if module.has_skill_md else "·",
        "P" if module.has_pai_md else "·",
    ]
    return "".join(parts)
