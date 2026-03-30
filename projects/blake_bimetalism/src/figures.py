"""
Thin Orchestrator Facade: Generates zero-mock visual artifacts mapping monetary history to Blakean poetics.
This module imports the 7 mathematical visualizations from the `src.viz` programmatic engine
to enforce architectural purity, exposing them to the `scripts/generate_figures.py` pipeline.
"""

from pathlib import Path
from projects.blake_bimetalism.src.viz import (
    render_timeline,
    render_fourfold_mapping,
    render_alchemical_bimetallism,
    render_topological_fracture,
    render_historic_ratio,
    render_historic_reserves,
    render_gsr_contemporary
)

__all__ = [
    'render_timeline',
    'render_fourfold_mapping',
    'render_alchemical_bimetallism',
    'render_topological_fracture',
    'render_historic_ratio',
    'render_historic_reserves',
    'render_gsr_contemporary'
]
