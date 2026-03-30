import matplotlib.pyplot as plt
from .core import setup_figure, save_and_close, np
from pathlib import Path

def render_topological_fracture(output_path: Path):
    plt.style.use('dark_background')
    fig, ax = setup_figure(figsize=(14, 9), title="Gresham's Phase-Space: Topological Fracture of the 1816 Coinage Act")
    
    Y, X = np.mgrid[-3:3:100j, -3:3:100j]
    V = 0.5 * Y + Y * (X**2)
    U = -X + 2*Y**2
    
    speed = np.sqrt(U**2 + V**2)
    strm = ax.streamplot(X, Y, U, V, color=speed, linewidth=2.0, cmap='magma', density=1.5)
    
    cbar = fig.colorbar(strm.lines, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Arbitrage Escape Velocity', rotation=270, labelpad=20, fontsize=14, fontweight='bold')
    cbar.ax.tick_params(labelsize=12)
    
    ax.plot([0], [0], marker='o', color='#ecc94b', markersize=26, markeredgecolor='white', markeredgewidth=3, zorder=5)
    ax.plot([-2, 2], [-2, 2], marker='X', color='#e2e8f0', linestyle='none', markersize=20, markeredgecolor='white', markeredgewidth=2, zorder=5, alpha=0.9)
    
    ax.text(0, 0.4, "Monometallic Attractor\n(The Gold Standard/Ulro)", ha='center', va='bottom', fontsize=14, fontweight='bold', color='#ffffff', bbox=dict(facecolor='#111111', alpha=0.9, edgecolor='#ecc94b', boxstyle='round,pad=0.5', lw=2))
    ax.text(2, -2.4, "Lunar Flight\n(Silver Escape Trajectory)", ha='center', va='top', fontsize=14, fontweight='bold', color='#ffffff', bbox=dict(facecolor='#2d3748', alpha=0.9, edgecolor='#e2e8f0', boxstyle='round,pad=0.5', lw=2))
    
    ax.set_xlabel("Gold Intensity Matrix (Static)", fontsize=16, fontweight='bold')
    ax.set_ylabel("Silver Flux Dispersion (Volatile)", fontsize=16, fontweight='bold')
    ax.tick_params(axis='both', which='major', labelsize=12)
    
    ax.grid(color='#2d3748', linestyle='--', linewidth=0.5, alpha=0.5)
    save_and_close(output_path)
