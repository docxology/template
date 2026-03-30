
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from pathlib import Path

# Generic visualization configuration
COLORS = {
    'gold': '#d4af37',
    'silver': '#c0c0c0',
    'primary': '#1D3557',
    'accent': '#E63946',
    'background': '#F1FAEE'
}

def setup_figure(figsize=(12, 8), title=None):
    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
    if title:
        ax.set_title(title, fontsize=16, fontweight='bold', fontfamily='serif', pad=25)
    return fig, ax

def save_and_close(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
