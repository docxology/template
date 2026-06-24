"""Visualization style configuration with colorblind-safe palette.

Uses the Wong (2011) colorblind-safe palette as the default color scheme,
ensuring figures are accessible to readers with color vision deficiencies.
All visualization modules reference VIZ_CONFIG for consistent styling.
"""

from __future__ import annotations

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
        "A1_formal": "#D55E00",
        "A2_philosophy": "#0072B2",
        "B_tools": "#E69F00",
        "C1_neuroscience": "#CC79A7",
        "C2_robotics": "#009E73",
        "C3_language": "#000000",
        "C4_psychiatry": "#56B4E9",
        "C5_biology": "#F0E442",
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
    "A1_formal": "A1: Formal Theory",
    "A2_philosophy": "A2: Philosophy",
    "B_tools": "B: Tools & Translation",
    "C1_neuroscience": "C1: Neuroscience",
    "C2_robotics": "C2: Robotics",
    "C3_language": "C3: Language",
    "C4_psychiatry": "C4: Psychiatry",
    "C5_biology": "C5: Biology",
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
