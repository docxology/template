"""Blake Active Inference Visualization Module.

Generates graphical abstracts and figures for the paper
"The Doors of Perception are the Threshold of Prediction."
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Infrastructure integration (optional)
try:
    repo_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(repo_root))
    from infrastructure.core import get_logger
    from infrastructure.documentation.figure_manager import FigureManager
    INFRASTRUCTURE_AVAILABLE = True
    logger = get_logger("blake_active_inference.visualization")
except ImportError:
    INFRASTRUCTURE_AVAILABLE = False
    logger = logging.getLogger("blake_active_inference.visualization")


# Color palette - accessible, professional
COLORS = {
    "external": "#2E4057",      # Dark blue - external world
    "sensory": "#048A81",       # Teal - sensory states
    "active": "#54C6EB",        # Light blue - active states
    "internal": "#8D0801",      # Dark red - internal states
    "blanket": "#F18F01",       # Orange - Markov blanket
    "background": "#FAFAFA",    # Off-white
    "text": "#1A1A1A",          # Near-black
    "vision_1": "#708090",      # Single vision - slate gray
    "vision_2": "#4169E1",      # Two-fold - royal blue
    "vision_3": "#9370DB",      # Three-fold - medium purple
    "vision_4": "#FFD700",      # Four-fold - gold
    # Zoa colors
    "urizen": "#8B4513",        # Brown - reason/limitation
    "urthona": "#6A0DAD",       # Purple - imagination
    "luvah": "#DC143C",         # Crimson - passion
    "tharmas": "#1E90FF",       # Dodger blue - body/instinct
    # State colors
    "pathology": "#B22222",     # Firebrick - pathological states
    "balanced": "#2E8B57",      # Sea green - balanced inference
    "rigid": "#696969",         # Dim gray - rigid states
    # Collective colors
    "shared": "#DAA520",        # Goldenrod - shared prior
    "agent_1": "#5F9EA0",       # Cadet blue
    "agent_2": "#CD853F",       # Peru
    "agent_3": "#7B68EE",       # Medium slate blue
    # Temporal colors
    "fast": "#FF6347",          # Tomato - fast timescale
    "mid": "#4682B4",           # Steel blue - mid timescale
    "slow": "#800080",          # Purple - slow timescale
    "deep": "#FFD700",          # Gold - deep/aeonic timescale
    # Atlas
    "theme_line": "#C0C0C0",    # Silver gray - connecting lines
}

# Minimum font sizes for print readability — significantly increased for
# clarity and accessibility. Titles stand out, labels are easily scannable.
FONTS = {
    'title': 28,           # Was 20 — prominent figure titles
    'section_label': 22,   # Was 16 — major section labels  
    'node_label': 18,      # Was 14 — node/element labels
    'sub_label': 16,       # Was 12 — sub-labels and descriptions
    'quote': 16,           # Was 11 — Blake quotations (readable)
    'annotation': 16,      # Was 11 — arrow labels and notes (min 16 for tests)
    'math': 18,            # Was 13 — mathematical expressions
    'caption': 16,         # Was 14 — figure captions (min 16 for standards)
}


def create_doors_of_perception_figure(
    output_path: Optional[Path] = None,
    figsize: tuple = (12, 8),
    dpi: int = 300
) -> plt.Figure:
    """Generate the 'Doors of Perception' graphical abstract.
    
    Visualizes the Markov blanket as Blake's 'doors' between
    internal states (imagination) and external states (infinite reality).
    
    Args:
        output_path: Path to save the figure. If None, figure is not saved.
        figsize: Figure dimensions (width, height) in inches.
        dpi: Resolution for saved figure.
        
    Returns:
        matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor=COLORS["background"])
    ax.set_facecolor(COLORS["background"])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis("off")
    
    # External world (left side)
    external_box = FancyBboxPatch(
        (0.5, 1), 3, 6,
        boxstyle="round,pad=0.1",
        facecolor=COLORS["external"],
        edgecolor="none",
        alpha=0.9
    )
    ax.add_patch(external_box)
    ax.text(2, 4, "EXTERNAL\nWORLD\n\n(η)",
            ha="center", va="center", fontsize=FONTS['section_label'], color="white", fontweight="bold")
    ax.text(2, 2, '"The Infinite"',
            ha="center", va="center", fontsize=FONTS['quote'], color="white", style="italic")
    
    # Internal world (right side)
    internal_box = FancyBboxPatch(
        (8.5, 1), 3, 6,
        boxstyle="round,pad=0.1",
        facecolor=COLORS["internal"],
        edgecolor="none",
        alpha=0.9
    )
    ax.add_patch(internal_box)
    ax.text(10, 4, "INTERNAL\nSTATES\n\n(μ)",
            ha="center", va="center", fontsize=FONTS['section_label'], color="white", fontweight="bold")
    ax.text(10, 2, '"The Cavern"',
            ha="center", va="center", fontsize=FONTS['quote'], color="white", style="italic")
    
    # The Markov Blanket / Doors of Perception (center)
    door_frame = FancyBboxPatch(
        (4.5, 0.5), 3, 7,
        boxstyle="round,pad=0.1",
        facecolor=COLORS["blanket"],
        edgecolor="none",
        alpha=0.3
    )
    ax.add_patch(door_frame)
    
    # Sensory states (upper door)
    sensory_box = FancyBboxPatch(
        (4.8, 4.5), 2.4, 2.5,
        boxstyle="round,pad=0.05",
        facecolor=COLORS["sensory"],
        edgecolor="none"
    )
    ax.add_patch(sensory_box)
    ax.text(6, 5.75, "SENSORY\nSTATES (s)",
            ha="center", va="center", fontsize=FONTS['sub_label'], color="white", fontweight="bold")
    
    # Active states (lower door)
    active_box = FancyBboxPatch(
        (4.8, 1), 2.4, 2.5,
        boxstyle="round,pad=0.05",
        facecolor=COLORS["active"],
        edgecolor="none"
    )
    ax.add_patch(active_box)
    ax.text(6, 2.25, "ACTIVE\nSTATES (a)",
            ha="center", va="center", fontsize=FONTS['sub_label'], color="white", fontweight="bold")
    
    # Title banner
    ax.text(6, 7.7, '"THE DOORS OF PERCEPTION"',
            ha="center", va="center", fontsize=FONTS['title'], color=COLORS["text"],
            fontweight="bold", style="italic")
    ax.text(6, 7.3, "= MARKOV BLANKET (B)",
            ha="center", va="center", fontsize=FONTS['node_label'], color=COLORS["text"])
    
    # Arrows: External → Sensory
    ax.annotate("", xy=(4.5, 5.75), xytext=(3.5, 5.75),
                arrowprops=dict(arrowstyle="->", color=COLORS["sensory"], lw=2))
    ax.text(4.0, 6.05, "Observations",
            ha="center", va="center", fontsize=FONTS['annotation'], color=COLORS["sensory"])

    # Arrows: Active → External
    ax.annotate("", xy=(3.5, 2.25), xytext=(4.5, 2.25),
                arrowprops=dict(arrowstyle="->", color=COLORS["active"], lw=2))
    ax.text(4.0, 1.95, "Actions",
            ha="center", va="center", fontsize=FONTS['annotation'], color=COLORS["active"])

    # Arrows: Sensory → Internal
    ax.annotate("", xy=(8.5, 5.75), xytext=(7.5, 5.75),
                arrowprops=dict(arrowstyle="->", color=COLORS["sensory"], lw=2))
    ax.text(8.0, 6.05, "Perception",
            ha="center", va="center", fontsize=FONTS['annotation'], color=COLORS["sensory"])

    # Arrows: Internal → Active
    ax.annotate("", xy=(7.5, 2.25), xytext=(8.5, 2.25),
                arrowprops=dict(arrowstyle="->", color=COLORS["active"], lw=2))
    ax.text(8.0, 1.95, "Decisions",
            ha="center", va="center", fontsize=FONTS['annotation'], color=COLORS["active"])
    
    # Blake quote at bottom
    ax.text(6, 0.15,
            '"If the doors of perception were cleansed every thing would appear to man as it is, Infinite."',
            ha="center", va="center", fontsize=FONTS['quote'], color=COLORS["text"], style="italic")
    ax.text(6, 0.05, "(The Marriage of Heaven and Hell, Plate 14)",
            ha="center", va="center", fontsize=FONTS['sub_label'], color=COLORS["text"], alpha=0.7)
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor=COLORS["background"])
    
    return fig


def create_fourfold_vision_figure(
    output_path: Optional[Path] = None,
    figsize: tuple = (10, 12),
    dpi: int = 300
) -> plt.Figure:
    """Generate the 'Four-Fold Vision' hierarchy diagram.
    
    Maps Blake's vision hierarchy to Active Inference levels.
    
    Args:
        output_path: Path to save the figure. If None, figure is not saved.
        figsize: Figure dimensions (width, height) in inches.
        dpi: Resolution for saved figure.
        
    Returns:
        matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor=COLORS["background"])
    ax.set_facecolor(COLORS["background"])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis("off")
    
    # Title
    ax.text(5, 11.5, "THE FOURFOLD VISION HIERARCHY",
            ha="center", va="center", fontsize=FONTS['title'], color=COLORS["text"], fontweight="bold")
    ax.text(5, 11.1, "Blake's Perceptual Levels ↔ Active Inference Hierarchy",
            ha="center", va="center", fontsize=FONTS['sub_label'], color=COLORS["text"])
    ax.text(5, 10.8, "(Source: Letter to Thomas Butts, 22 Nov 1802)",
            ha="center", va="center", fontsize=FONTS['annotation'], color=COLORS["text"], alpha=0.7)
    
    levels = [
        {
            "y": 9.5,
            "color": COLORS["vision_4"],
            "blake": "FOURFOLD VISION",
            "blake_sub": "Jerusalem / Supreme Delight",
            "ai": "Full Hierarchical Integration",
            "ai_sub": r"$\theta_4$: Unified prior model",
            "quote": '"Tis fourfold in my supreme delight"'
        },
        {
            "y": 7,
            "color": COLORS["vision_3"],
            "blake": "THREEFOLD VISION",
            "blake_sub": "Beulah / Imaginative Synthesis",
            "ai": "Narrative/Symbolic Level",
            "ai_sub": r"$\theta_3$: Temporal integration",
            "quote": '"Threefold in soft Beulah\'s night"'
        },
        {
            "y": 4.5,
            "color": COLORS["vision_2"],
            "blake": "TWOFOLD VISION",
            "blake_sub": "Generation / Emotional-Intellectual",
            "ai": "Semantic/Emotional Level",
            "ai_sub": r"$\theta_2$: Affective encoding",
            "quote": '"Twofold always"'
        },
        {
            "y": 2,
            "color": COLORS["vision_1"],
            "blake": "SINGLE VISION",
            "blake_sub": "Ulro / Newton's Sleep",
            "ai": "Sensory Registration",
            "ai_sub": r"$\theta_1$: Feature extraction",
            "quote": '"Single vision & Newton\'s sleep!"'
        },
    ]
    
    for level in levels:
        y = level["y"]
        color = level["color"]
        
        # Level box
        box = FancyBboxPatch(
            (0.5, y - 0.8), 9, 1.8,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor="none",
            alpha=0.85
        )
        ax.add_patch(box)
        
        # Blake side (left)
        ax.text(2.8, y + 0.3, level["blake"],
                ha="center", va="center", fontsize=FONTS['node_label'], color="white", fontweight="bold")
        ax.text(2.8, y - 0.1, level["blake_sub"],
                ha="center", va="center", fontsize=FONTS['sub_label'], color="white")
        ax.text(2.8, y - 0.5, level["quote"],
                ha="center", va="center", fontsize=FONTS['quote'], color="white", style="italic")

        # Divider
        ax.plot([5, 5], [y - 0.6, y + 0.6], color="white", linewidth=1, alpha=0.5)

        # Active Inference side (right)
        ax.text(7.2, y + 0.2, level["ai"],
                ha="center", va="center", fontsize=FONTS['sub_label'], color="white", fontweight="bold")
        ax.text(7.2, y - 0.2, level["ai_sub"],
                ha="center", va="center", fontsize=FONTS['sub_label'], color="white")
    
    # Vertical arrows between levels
    for i in range(3):
        y_start = levels[i+1]["y"] + 0.9
        y_end = levels[i]["y"] - 0.9
        ax.annotate("", xy=(5, y_end), xytext=(5, y_start),
                    arrowprops=dict(arrowstyle="->", color=COLORS["text"], lw=2))
    
    # Column headers — positioned just above the top level box, below source citation
    ax.text(2.8, 10.45, "BLAKE", ha="center", va="center", 
            fontsize=FONTS['sub_label'], color=COLORS["text"], fontweight="bold")
    ax.text(7.2, 10.45, "ACTIVE INFERENCE", ha="center", va="center", 
            fontsize=FONTS['sub_label'], color=COLORS["text"], fontweight="bold")
    
    # Bottom note
    ax.text(5, 0.5, "↑ Increasing hierarchical depth / precision integration",
            ha="center", va="center", fontsize=FONTS['annotation'], color=COLORS["text"])
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor=COLORS["background"])
    
    return fig


def create_perception_action_cycle_figure(
    output_path: Optional[Path] = None,
    figsize: tuple = (12, 12),
    dpi: int = 300
) -> plt.Figure:
    """Generate the Active Inference perception-action cycle.
    
    Circular diagram showing prediction → error → update cycle
    annotated with Blake quotations.
    
    Args:
        output_path: Path to save the figure. If None, figure is not saved.
        figsize: Figure dimensions (width, height) in inches.
        dpi: Resolution for saved figure.
        
    Returns:
        matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor=COLORS["background"])
    ax.set_facecolor(COLORS["background"])
    ax.set_xlim(-1.8, 1.8)
    ax.set_ylim(-1.8, 1.8)
    ax.set_aspect("equal")
    ax.axis("off")
    
    # Title
    ax.text(0, 1.55, "THE ACTIVE INFERENCE CYCLE",
            ha="center", va="center", fontsize=FONTS['title'], color=COLORS["text"], fontweight="bold")
    ax.text(0, 1.38, "Free Energy Minimization Through Perception and Action",
            ha="center", va="center", fontsize=FONTS['annotation'], color=COLORS["text"])
    
    # Central circle - the generative model
    center_circle = plt.Circle((0, 0), 0.35, color=COLORS["blanket"], alpha=0.9)
    ax.add_patch(center_circle)
    ax.text(0, 0.05, "GENERATIVE\nMODEL", ha="center", va="center",
            fontsize=FONTS['annotation'], color="white", fontweight="bold")
    ax.text(0, -0.2, r"$p(o,\theta)$", ha="center", va="center",
            fontsize=FONTS['annotation'], color="white", style="italic")
    
    # Outer nodes
    nodes = [
        {"pos": (0, 0.9), "label": "PREDICTION\n" + r"$\varepsilon = o - g(\theta)$", "color": COLORS["sensory"],
         "quote": '"What is now proved\nwas once imagined"'},
        {"pos": (0.78, 0.45), "label": "SENSORY\nINPUT", "color": COLORS["external"],
         "quote": '"The senses\ndiscover\'d the infinite"'},
        {"pos": (0.78, -0.45), "label": "PREDICTION\nERROR", "color": COLORS["internal"],
         "quote": '"Narrow chinks\nof his cavern"'},
        {"pos": (0, -0.9), "label": "MODEL\nUPDATE", "color": COLORS["vision_2"],
         "quote": '"Cleansed\nperception"'},
        {"pos": (-0.78, -0.45), "label": "ACTION\nSELECTION", "color": COLORS["active"],
         "quote": '"Mental Fight"'},
        {"pos": (-0.78, 0.45), "label": "WORLD\nCHANGE", "color": COLORS["vision_3"],
         "quote": '"Building\nJerusalem"'},
    ]
    
    for i, node in enumerate(nodes):
        x, y = node["pos"]
        circle = plt.Circle((x, y), 0.26, color=node["color"], alpha=0.85)
        ax.add_patch(circle)
        ax.text(x, y + 0.02, node["label"], ha="center", va="center",
                fontsize=FONTS['node_label'], color="white", fontweight="bold")
    
    # Blake quotes outside the cycle
    quote_radius = 1.3
    for i, node in enumerate(nodes):
        angle = np.pi/2 - i * np.pi/3
        x = quote_radius * np.cos(angle)
        y = quote_radius * np.sin(angle)
        ax.text(x, y, node["quote"], ha="center", va="center",
                fontsize=FONTS['quote'], color=COLORS["text"], style="italic")
    
    # Arrows between nodes (clockwise)
    for i in range(6):
        start = nodes[i]["pos"]
        end = nodes[(i + 1) % 6]["pos"]
        
        # Calculate arrow positions
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dist = np.sqrt(dx**2 + dy**2)
        
        # Offset start and end by node radius
        offset = 0.29
        start_adj = (start[0] + offset * dx/dist, start[1] + offset * dy/dist)
        end_adj = (end[0] - offset * dx/dist, end[1] - offset * dy/dist)
        
        ax.annotate("", xy=end_adj, xytext=start_adj,
                    arrowprops=dict(arrowstyle="->", color=COLORS["text"], 
                                    lw=1.5, connectionstyle="arc3,rad=0.1"))
    
    # Arrows to/from center
    for node in nodes:
        x, y = node["pos"]
        dist = np.sqrt(x**2 + y**2)
        if dist > 0:
            # Inward arrow
            ax.annotate("", xy=(x * 0.4, y * 0.4), xytext=(x * 0.65, y * 0.65),
                        arrowprops=dict(arrowstyle="->", color=COLORS["text"], 
                                        lw=0.8, alpha=0.5))
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor=COLORS["background"])
    
    return fig


def create_thematic_atlas_figure(
    output_path: Optional[Path] = None,
    figsize: tuple = (14, 11),
    dpi: int = 300
) -> plt.Figure:
    """Generate the Thematic Atlas mapping Blake concepts to Active Inference.

    Two-column layout with Blake concepts (left) and Active Inference concepts
    (right), connected by colored arcs across 8 thematic rows.

    Args:
        output_path: Path to save the figure. If None, figure is not saved.
        figsize: Figure dimensions (width, height) in inches.
        dpi: Resolution for saved figure.

    Returns:
        matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor=COLORS["background"])
    ax.set_facecolor(COLORS["background"])
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Title
    ax.text(7, 9.5, "THEMATIC ATLAS: Blake <-> Active Inference",
            ha="center", va="center", fontsize=FONTS['title'],
            color=COLORS["text"], fontweight="bold")

    # Column headers
    ax.text(3, 8.8, "BLAKE", ha="center", va="center",
            fontsize=FONTS['section_label'], color=COLORS["text"], fontweight="bold")
    ax.text(11, 8.8, "ACTIVE INFERENCE", ha="center", va="center",
            fontsize=FONTS['section_label'], color=COLORS["text"], fontweight="bold")

    themes = [
        ("Boundary / Doors", "Markov Blanket", COLORS["blanket"]),
        ("Vision / Hierarchy", "Hierarchical Processing", COLORS["vision_2"]),
        ("States / Ulro", "Prior Dominance", COLORS["rigid"]),
        ("Imagination / Los", "Generative Model", COLORS["urthona"]),
        ("Time / Pulsation", "Temporal Horizons", COLORS["mid"]),
        ("Space / Vortex", "Spatial Inference", COLORS["tharmas"]),
        ("Action / Mental Fight", "Free Energy Minimization", COLORS["luvah"]),
        ("Collectives & Zoas", "Shared & Factorized Models", COLORS["shared"]),
    ]

    y_start = 8.0
    y_step = 0.95
    left_x = 3.0
    right_x = 11.0

    for i, (blake_label, aif_label, color) in enumerate(themes):
        y = y_start - i * y_step

        # Blake concept (left)
        box_left = FancyBboxPatch(
            (0.5, y - 0.3), 5, 0.6,
            boxstyle="round,pad=0.05",
            facecolor=color, edgecolor="none", alpha=0.85
        )
        ax.add_patch(box_left)
        ax.text(left_x, y, blake_label,
                ha="center", va="center", fontsize=FONTS['sub_label'],
                color="white", fontweight="bold")

        # Active Inference concept (right)
        box_right = FancyBboxPatch(
            (8.5, y - 0.3), 5, 0.6,
            boxstyle="round,pad=0.05",
            facecolor=color, edgecolor="none", alpha=0.85
        )
        ax.add_patch(box_right)
        ax.text(right_x, y, aif_label,
                ha="center", va="center", fontsize=FONTS['sub_label'],
                color="white", fontweight="bold")

        # Connecting arc between columns
        arc = FancyArrowPatch(
            (5.5, y), (8.5, y),
            connectionstyle="arc3,rad=0.15",
            arrowstyle="<->",
            color=color, lw=1.5, alpha=0.7
        )
        ax.add_patch(arc)

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight",
                    facecolor=COLORS["background"])

    return fig


def create_newtons_sleep_figure(
    output_path: Optional[Path] = None,
    figsize: tuple = (14, 8),
    dpi: int = 300
) -> plt.Figure:
    """Generate the Newton's Sleep vs. Cleansed Perception figure.

    Two-panel figure contrasting prior-dominated inference (Newton's Sleep)
    with balanced optimal inference (Cleansed Perception).

    Args:
        output_path: Path to save the figure. If None, figure is not saved.
        figsize: Figure dimensions (width, height) in inches.
        dpi: Resolution for saved figure.

    Returns:
        matplotlib Figure object.
    """
    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=figsize, facecolor=COLORS["background"])

    for ax in (ax_left, ax_right):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 8)
        ax.set_aspect("equal")
        ax.axis("off")

    # --- Left panel: Newton's Sleep ---
    ax_left.set_facecolor(COLORS["background"])
    # Background tint for rigidity
    rigid_bg = FancyBboxPatch(
        (0.2, 0.2), 9.6, 7.6,
        boxstyle="round,pad=0.1",
        facecolor=COLORS["rigid"], edgecolor="none", alpha=0.08
    )
    ax_left.add_patch(rigid_bg)

    ax_left.text(5, 7.2, "Newton's Sleep",
                 ha="center", va="center", fontsize=FONTS['section_label'],
                 color=COLORS["text"], fontweight="bold")
    ax_left.text(5, 6.6, "Prior Dominance",
                 ha="center", va="center", fontsize=FONTS['sub_label'],
                 color=COLORS["rigid"])

    # Tilted balance beam -- pivot at center, left side lower (heavier prior)
    pivot_x, pivot_y = 5.0, 3.5
    beam_half = 3.0
    tilt = 0.6  # vertical tilt amount

    # Left end (heavy prior) is lower, right end (weak sensory) is higher
    ax_left.plot(
        [pivot_x - beam_half, pivot_x + beam_half],
        [pivot_y - tilt, pivot_y + tilt],
        color=COLORS["text"], lw=3)
    # Pivot triangle
    triangle = plt.Polygon(
        [[pivot_x, pivot_y - 0.05], [pivot_x - 0.3, pivot_y - 0.6],
         [pivot_x + 0.3, pivot_y - 0.6]],
        facecolor=COLORS["text"], edgecolor="none")
    ax_left.add_patch(triangle)

    # Heavy prior box (left, large square for "weight")
    prior_box = plt.Rectangle(
        (pivot_x - beam_half - 0.8, pivot_y - tilt - 0.1), 1.6, 1.6,
        color=COLORS["pathology"], alpha=0.9)
    ax_left.add_patch(prior_box)
    ax_left.text(pivot_x - beam_half, pivot_y - tilt + 0.7, r"$\pi_{prior}$",
                 ha="center", va="center", fontsize=FONTS['math'],
                 color="white", fontweight="bold")
    ax_left.text(pivot_x - beam_half, pivot_y - tilt - 1.0, "RIGID",
                 ha="center", va="center", fontsize=FONTS['annotation'],
                 color=COLORS["pathology"], fontweight="bold")

    # Weak sensory circle (right, small)
    sensory_circle = plt.Circle(
        (pivot_x + beam_half, pivot_y + tilt + 0.4), 0.4,
        color=COLORS["sensory"], alpha=0.9)
    ax_left.add_patch(sensory_circle)
    ax_left.text(pivot_x + beam_half, pivot_y + tilt + 0.65, r"$\pi_{sensory}$",
                 ha="center", va="center", fontsize=FONTS['math'],
                 color=COLORS["text"])

    # --- Right panel: Cleansed Perception ---
    ax_right.set_facecolor(COLORS["background"])
    # Background tint for balance
    balanced_bg = FancyBboxPatch(
        (0.2, 0.2), 9.6, 7.6,
        boxstyle="round,pad=0.1",
        facecolor=COLORS["balanced"], edgecolor="none", alpha=0.08
    )
    ax_right.add_patch(balanced_bg)

    ax_right.text(5, 7.2, "Cleansed Perception",
                  ha="center", va="center", fontsize=FONTS['section_label'],
                  color=COLORS["text"], fontweight="bold")
    ax_right.text(5, 6.6, "Optimal Inference",
                  ha="center", va="center", fontsize=FONTS['sub_label'],
                  color=COLORS["balanced"])

    # Level balance beam
    ax_right.plot(
        [pivot_x - beam_half, pivot_x + beam_half],
        [pivot_y, pivot_y],
        color=COLORS["text"], lw=3)
    # Pivot triangle
    triangle_r = plt.Polygon(
        [[pivot_x, pivot_y - 0.05], [pivot_x - 0.3, pivot_y - 0.6],
         [pivot_x + 0.3, pivot_y - 0.6]],
        facecolor=COLORS["text"], edgecolor="none")
    ax_right.add_patch(triangle_r)

    # Equal prior box (square for visual consistency)
    prior_box_r = plt.Rectangle(
        (pivot_x - beam_half - 0.6, pivot_y - 0.1), 1.2, 1.2,
        color=COLORS["balanced"], alpha=0.9)
    ax_right.add_patch(prior_box_r)
    ax_right.text(pivot_x - beam_half, pivot_y + 0.5, r"$\pi_{prior}$",
                  ha="center", va="center", fontsize=FONTS['math'],
                  color="white", fontweight="bold")

    # Equal sensory box (square for visual consistency)
    sensory_box_r = plt.Rectangle(
        (pivot_x + beam_half - 0.6, pivot_y - 0.1), 1.2, 1.2,
        color=COLORS["sensory"], alpha=0.9)
    ax_right.add_patch(sensory_box_r)
    ax_right.text(pivot_x + beam_half, pivot_y + 0.5, r"$\pi_{sensory}$",
                  ha="center", va="center", fontsize=FONTS['math'],
                  color="white", fontweight="bold")

    # Overall title
    fig.suptitle("NEWTON'S SLEEP vs. CLEANSED PERCEPTION",
                 fontsize=FONTS['title'], color=COLORS["text"],
                 fontweight="bold", y=0.98)

    # Blake quote at bottom
    fig.text(0.5, 0.02,
             '"May God us keep / From Single vision & Newton\'s sleep!"',
             ha="center", va="center", fontsize=FONTS['quote'],
             color=COLORS["text"], style="italic")

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])

    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight",
                    facecolor=COLORS["background"])

    return fig


def create_four_zoas_figure(
    output_path: Optional[Path] = None,
    figsize: tuple = (12, 12),
    dpi: int = 300
) -> plt.Figure:
    """Generate the Four Zoas compass-rose figure.

    Compass-rose layout with four Zoas at cardinal positions, a central hub,
    and connecting arcs. Each Zoa shows name, function, AIF mapping, and
    failure mode.

    Args:
        output_path: Path to save the figure. If None, figure is not saved.
        figsize: Figure dimensions (width, height) in inches.
        dpi: Resolution for saved figure.

    Returns:
        matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor=COLORS["background"])
    ax.set_facecolor(COLORS["background"])
    ax.set_xlim(-6, 6)
    ax.set_ylim(-6, 6)
    ax.set_aspect("equal")
    ax.axis("off")

    # Title
    ax.text(0, 5.5, "THE FOUR ZOAS: A Factorized Model of Mind",
            ha="center", va="center", fontsize=FONTS['title'],
            color=COLORS["text"], fontweight="bold")

    # Central hub
    center = plt.Circle((0, 0), 1.0, color=COLORS["blanket"], alpha=0.9)
    ax.add_patch(center)
    ax.text(0, 0.15, "Unified", ha="center", va="center",
            fontsize=FONTS['node_label'], color="white", fontweight="bold")
    ax.text(0, -0.2, "Inference", ha="center", va="center",
            fontsize=FONTS['node_label'], color="white", fontweight="bold")

    # Zoa definitions: (angle_deg, name, function, aif_mapping, color_key, failure)
    zoas = [
        (270, "URIZEN", "Reason", r"Likelihood $p(o|\theta)$",
         "urizen", "Rigid certainty"),
        (90, "URTHONA / LOS", "Imagination", r"Prior model $p(\theta)$",
         "urthona", "Ungrounded fantasy"),
        (0, "LUVAH / ORC", "Passion", r"Precision $\pi$",
         "luvah", "Unchecked impulse"),
        (180, "THARMAS", "Body", r"Sensory $s$",
         "tharmas", "Dissociation"),
    ]

    radius = 3.5
    circle_r = 1.6  # Enlarged from 1.4 for longer dual-name labels

    for angle_deg, name, function, aif_mapping, color_key, failure in zoas:
        angle_rad = np.radians(angle_deg)
        cx = radius * np.cos(angle_rad)
        cy = radius * np.sin(angle_rad)

        # Zoa circle
        zoa_circle = plt.Circle(
            (cx, cy), circle_r,
            color=COLORS[color_key], alpha=0.9)
        ax.add_patch(zoa_circle)

        # Name (use slightly smaller font for long dual-name labels)
        ax.text(cx, cy + 0.45, name, ha="center", va="center",
                fontsize=FONTS['sub_label'], color="white", fontweight="bold")
        # Function
        ax.text(cx, cy + 0.05, function, ha="center", va="center",
                fontsize=FONTS['sub_label'], color="white")
        # AIF mapping
        ax.text(cx, cy - 0.35, aif_mapping, ha="center", va="center",
                fontsize=FONTS['annotation'], color="white")

        # Failure mode (small red text nearby, outside the circle)
        fail_offset = 1.5
        fx = cx + fail_offset * np.cos(angle_rad)
        fy = cy + fail_offset * np.sin(angle_rad)
        ax.text(fx, fy, failure, ha="center", va="center",
                fontsize=FONTS['annotation'], color=COLORS["pathology"],
                style="italic")

        # Connecting line from center to Zoa
        inner_r = 1.05
        outer_r = radius - circle_r - 0.05
        ax.annotate("",
                     xy=(outer_r * np.cos(angle_rad),
                         outer_r * np.sin(angle_rad)),
                     xytext=(inner_r * np.cos(angle_rad),
                             inner_r * np.sin(angle_rad)),
                     arrowprops=dict(arrowstyle="<->", color=COLORS["text"],
                                     lw=1.5, alpha=0.6))

    # Curved arcs between adjacent Zoas
    adj_pairs = [(0, 1), (1, 2), (2, 3), (3, 0)]
    for i, j in adj_pairs:
        a1 = np.radians(zoas[i][0])
        a2 = np.radians(zoas[j][0])
        x1 = radius * np.cos(a1)
        y1 = radius * np.sin(a1)
        x2 = radius * np.cos(a2)
        y2 = radius * np.sin(a2)
        arc = FancyArrowPatch(
            (x1, y1), (x2, y2),
            connectionstyle="arc3,rad=0.3",
            arrowstyle="-",
            color=COLORS["theme_line"], lw=1.2, alpha=0.5
        )
        ax.add_patch(arc)

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight",
                    facecolor=COLORS["background"])

    return fig


def create_temporal_horizons_figure(
    output_path: Optional[Path] = None,
    figsize: tuple = (12, 10),
    dpi: int = 300
) -> plt.Figure:
    """Generate the Temporal Horizons of Inference figure.

    Stacked horizontal trapezoid bands widening from bottom to top,
    representing four timescales of inference from fast sensory to deep aeonic.

    Args:
        output_path: Path to save the figure. If None, figure is not saved.
        figsize: Figure dimensions (width, height) in inches.
        dpi: Resolution for saved figure.

    Returns:
        matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor=COLORS["background"])
    ax.set_facecolor(COLORS["background"])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Title
    ax.text(6, 9.5, "TEMPORAL HORIZONS OF INFERENCE",
            ha="center", va="center", fontsize=FONTS['title'],
            color=COLORS["text"], fontweight="bold")

    bands = [
        ("Fast: Sensory", "Milliseconds", COLORS["fast"]),
        ("Mid: Emotional", "Seconds to Minutes", COLORS["mid"]),
        ("Slow: Narrative", "Hours to Years", COLORS["slow"]),
        ("Deep: Aeonic", "Lifetimes to Eternity", COLORS["deep"]),
    ]

    n = len(bands)
    band_height = 1.5
    y_base = 1.5
    center_x = 5.5
    min_half_width = 2.0
    max_half_width = 5.0

    for i, (label, timescale, color) in enumerate(bands):
        y_bottom = y_base + i * band_height
        y_top = y_bottom + band_height

        # Trapezoid: wider at top for higher bands
        hw_bottom = min_half_width + (max_half_width - min_half_width) * (i / n)
        hw_top = min_half_width + (max_half_width - min_half_width) * ((i + 1) / n)

        trap = plt.Polygon([
            [center_x - hw_bottom, y_bottom],
            [center_x + hw_bottom, y_bottom],
            [center_x + hw_top, y_top],
            [center_x - hw_top, y_top],
        ], facecolor=color, edgecolor="white", alpha=0.85, lw=1)
        ax.add_patch(trap)

        # Label and timescale
        y_mid = (y_bottom + y_top) / 2
        ax.text(center_x, y_mid + 0.2, label,
                ha="center", va="center", fontsize=FONTS['node_label'],
                color="white", fontweight="bold")
        ax.text(center_x, y_mid - 0.25, timescale,
                ha="center", va="center", fontsize=FONTS['sub_label'],
                color="white")

    # Vertical arrow on the right
    arrow_x = 11.2
    ax.annotate("",
                xy=(arrow_x, y_base + n * band_height + 0.3),
                xytext=(arrow_x, y_base - 0.3),
                arrowprops=dict(arrowstyle="->", color=COLORS["text"], lw=2.5))
    ax.text(arrow_x + 0.3, (y_base + y_base + n * band_height) / 2,
            "Temporal Depth",
            ha="center", va="center", fontsize=FONTS['sub_label'],
            color=COLORS["text"], rotation=90)

    # Blake quote at bottom
    ax.text(6, 0.5,
            ('"Every Time less than a pulsation of the artery\n'
             'Is equal in its period & value to Six Thousand Years"'),
            ha="center", va="center", fontsize=FONTS['quote'],
            color=COLORS["text"], style="italic")

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight",
                    facecolor=COLORS["background"])

    return fig


def create_collective_jerusalem_figure(
    output_path: Optional[Path] = None,
    figsize: tuple = (14, 10),
    dpi: int = 300
) -> plt.Figure:
    """Generate the Building Jerusalem collective generative model figure.

    Three agent circles at the bottom with Markov blanket boundaries,
    connected upward to a large shared Jerusalem circle, with a Mental Fight
    zone in between.

    Args:
        output_path: Path to save the figure. If None, figure is not saved.
        figsize: Figure dimensions (width, height) in inches.
        dpi: Resolution for saved figure.

    Returns:
        matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor=COLORS["background"])
    ax.set_facecolor(COLORS["background"])
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Title
    ax.text(7, 9.5, "BUILDING JERUSALEM: Collective Generative Models",
            ha="center", va="center", fontsize=FONTS['title'],
            color=COLORS["text"], fontweight="bold")

    # Jerusalem circle (top center)
    jerusalem_r = 1.8
    jx, jy = 7, 7.0
    jerusalem = plt.Circle(
        (jx, jy), jerusalem_r,
        color=COLORS["shared"], alpha=0.9)
    ax.add_patch(jerusalem)
    ax.text(jx, jy + 0.4, "JERUSALEM", ha="center", va="center",
            fontsize=FONTS['section_label'], color="white", fontweight="bold")
    ax.text(jx, jy - 0.15, "Shared Generative Model", ha="center", va="center",
            fontsize=FONTS['sub_label'], color="white")
    ax.text(jx, jy - 0.65, r"$\theta_{shared}$", ha="center", va="center",
            fontsize=FONTS['math'], color="white")

    # Mental Fight zone label
    ax.text(7, 4.5, '"Mental Fight"', ha="center", va="center",
            fontsize=FONTS['sub_label'], color=COLORS["luvah"],
            style="italic", fontweight="bold")

    # Three agents in a semicircle at the bottom
    agent_colors = [COLORS["agent_1"], COLORS["agent_2"], COLORS["agent_3"]]
    agent_xs = [3.5, 7.0, 10.5]
    agent_y = 2.0
    agent_r = 0.9

    for i, (ax_pos, color) in enumerate(zip(agent_xs, agent_colors)):
        # Markov blanket boundary (dashed ring)
        blanket = plt.Circle(
            (ax_pos, agent_y), agent_r + 0.25,
            facecolor="none", edgecolor=COLORS["blanket"],
            linestyle="--", lw=1.5, alpha=0.7)
        ax.add_patch(blanket)

        # Agent circle
        agent_circle = plt.Circle(
            (ax_pos, agent_y), agent_r,
            color=color, alpha=0.9)
        ax.add_patch(agent_circle)
        ax.text(ax_pos, agent_y + 0.2, f"Agent {i + 1}",
                ha="center", va="center", fontsize=FONTS['node_label'],
                color="white", fontweight="bold")
        ax.text(ax_pos, agent_y - 0.25, r"$\theta_{%d}$" % (i + 1),
                ha="center", va="center", fontsize=FONTS['math'],
                color="white")

        # Arrow from agent up to Jerusalem
        ax.annotate("",
                     xy=(jx + (ax_pos - jx) * 0.3,
                         jy - jerusalem_r - 0.1),
                     xytext=(ax_pos,
                             agent_y + agent_r + 0.3),
                     arrowprops=dict(arrowstyle="->", color=COLORS["text"],
                                     lw=1.5, alpha=0.6,
                                     connectionstyle="arc3,rad=0.0"))

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight",
                    facecolor=COLORS["background"])

    return fig


def generate_all_figures(output_dir: Path) -> dict:
    """Generate all paper figures.
    
    Args:
        output_dir: Directory to save figures.
        
    Returns:
        Dictionary mapping figure names to output paths.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    figures = {}

    # Figure 0: Thematic Atlas
    path0 = output_dir / "fig0_thematic_atlas.png"
    create_thematic_atlas_figure(path0)
    figures["thematic_atlas"] = path0
    plt.close()

    # Figure 1: Doors of Perception
    path1 = output_dir / "fig1_doors_of_perception.png"
    create_doors_of_perception_figure(path1)
    figures["doors_of_perception"] = path1
    plt.close()

    # Figure 2: Fourfold Vision
    path2 = output_dir / "fig2_fourfold_vision.png"
    create_fourfold_vision_figure(path2)
    figures["fourfold_vision"] = path2
    plt.close()

    # Figure 3: Perception-Action Cycle
    path3 = output_dir / "fig3_perception_action_cycle.png"
    create_perception_action_cycle_figure(path3)
    figures["perception_action_cycle"] = path3
    plt.close()

    # Figure 4: Newton's Sleep
    path4 = output_dir / "fig4_newtons_sleep.png"
    create_newtons_sleep_figure(path4)
    figures["newtons_sleep"] = path4
    plt.close()

    # Figure 5: Four Zoas
    path5 = output_dir / "fig5_four_zoas.png"
    create_four_zoas_figure(path5)
    figures["four_zoas"] = path5
    plt.close()

    # Figure 6: Temporal Horizons
    path6 = output_dir / "fig6_temporal_horizons.png"
    create_temporal_horizons_figure(path6)
    figures["temporal_horizons"] = path6
    plt.close()

    # Figure 7: Collective Jerusalem
    path7 = output_dir / "fig7_collective_jerusalem.png"
    create_collective_jerusalem_figure(path7)
    figures["collective_jerusalem"] = path7
    plt.close()

    return figures


if __name__ == "__main__":
    # Default output directory
    output_dir = Path(__file__).parent.parent / "output" / "figures"

    # Allow override from command line
    if len(sys.argv) > 1:
        output_dir = Path(sys.argv[1])

    logger.info(f"Generating figures to: {output_dir}")
    figures = generate_all_figures(output_dir)

    for name, path in figures.items():
        logger.info(f"  {name}: {path}")

    logger.info(f"Generated {len(figures)} figures successfully.")
