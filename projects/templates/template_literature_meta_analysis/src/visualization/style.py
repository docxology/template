"""Visualization style configuration with colorblind-safe palette.

Uses the Wong (2011) colorblind-safe palette as the default color scheme,
ensuring figures are accessible to readers with color vision deficiencies.
All visualization modules reference VIZ_CONFIG for consistent styling.
"""

from __future__ import annotations

from pathlib import Path

import yaml

VIZ_CONFIG: dict = {
    "figure_size": (12, 7),
    "dpi": 300,
    "font_size": 18,
    "tick_size": 16,
    "title_size": 22,
    "palette": [
        "#0072B2",  # Blue
        "#E69F00",  # Orange
        "#009E73",  # Green
        "#CC79A7",  # Pink
        "#56B4E9",  # Light blue
        "#D55E00",  # Red-orange
        "#F0E442",  # Yellow
        "#000000",  # Black
    ],
    "subfield_colors": {
        "clinical_sleep": "#D55E00",
        "cognition": "#0072B2",
        "pharmacology": "#E69F00",
        "psychiatry": "#CC79A7",
        "safety": "#009E73",
        "neuroscience": "#56B4E9",
    },
    "grid_alpha": 0.4,
    "edge_color": "#b0b0b0",
}

# Human-readable subfield names for figure labels
SUBFIELD_NAMES: dict[str, str] = {
    "clinical_sleep": "Clinical Sleep",
    "cognition": "Cognition",
    "pharmacology": "Pharmacology",
    "psychiatry": "Psychiatry",
    "safety": "Safety",
    "neuroscience": "Neuroscience",
}

# Human-readable hypothesis names for figure labels
HYPOTHESIS_NAMES: dict[str, str] = {
    "H1": "Wakefulness Efficacy",
    "H2": "Cognitive Enhancement",
    "H3": "Low Abuse Liability",
    "H4": "Dopaminergic Mechanism",
    "H5": "Off-label Psychiatric Utility",
    "H6": "Tolerability",
    "H7": "Domain Extension",
    "H8": "Residual Evidence",
}


def load_viz_labels_from_config(project_root: Path) -> None:
    """Overlay subfield and hypothesis labels from manuscript config when present."""
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.exists():
        return
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    project_config = cfg.get("project_config", {})
    for key in project_config.get("subfield_keywords") or {}:
        SUBFIELD_NAMES[key] = key.replace("_", " ").title()
    for hypothesis_id, hypothesis in (project_config.get("hypothesis_definitions") or {}).items():
        if isinstance(hypothesis, dict) and hypothesis.get("name"):
            HYPOTHESIS_NAMES[hypothesis_id] = str(hypothesis["name"])


def apply_visual_style() -> None:
    """Apply global matplotlib style config to enforce accessibility standards.

    Strictly enforces a 16pt font size floor for all textual elements in
    figures ensure colorblind-safe and accessibility compliance.
    """
    import matplotlib.pyplot as plt

    plt.rc("font", size=max(16, VIZ_CONFIG["font_size"]))
    plt.rc("axes", titlesize=max(16, VIZ_CONFIG["title_size"]), labelsize=max(16, VIZ_CONFIG["font_size"]))
    plt.rc("xtick", labelsize=max(16, VIZ_CONFIG["tick_size"]))
    plt.rc("ytick", labelsize=max(16, VIZ_CONFIG["tick_size"]))
    plt.rc("legend", fontsize=max(16, VIZ_CONFIG["font_size"] - 2))
    plt.rc("figure", titlesize=max(16, VIZ_CONFIG["title_size"]))
