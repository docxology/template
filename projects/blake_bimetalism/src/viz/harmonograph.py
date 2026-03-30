
from .core import setup_figure, save_and_close, np
from pathlib import Path

def render_alchemical_bimetallism(output_path: Path):
    fig, ax = setup_figure(figsize=(12, 8), title="Procedural Alchemy: The Parametric Degeneration of Bimetallic Orbit")
    ax.axis('off')
    
    t = np.linspace(0, 10 * np.pi, 3000)
    xg = np.sin(1.1 * t) * np.exp(0.02 * t)
    yg = np.cos(1.1 * t) * np.exp(0.02 * t)
    xs = np.sin(1.5 * t + np.pi/4) * np.exp(0.03 * t) * 1.5
    ys = np.cos(0.8 * t) * np.exp(0.03 * t) * 1.5
    
    rupture_t = 8 * np.pi
    mask_harmony = t <= rupture_t
    mask_fracture = t > rupture_t
    
    ax.plot(xg[mask_harmony], yg[mask_harmony], color='gold', lw=2.5, alpha=0.8, label='Solar Metric (Gold Attractor)')
    ax.plot(xs[mask_harmony], ys[mask_harmony], color='silver', lw=2.5, alpha=0.8, label='Lunar Flux (Silver Arbitrage)')
    
    ax.plot(xg[mask_fracture]*0.1, yg[mask_fracture]*0.1, color='#d4af37', lw=1.5, alpha=0.8)
    escape_x = xs[mask_harmony][-1] + (t[mask_fracture] - rupture_t) * 4
    escape_y = ys[mask_harmony][-1] + np.sin(t[mask_fracture] * 5) * 0.5 + (t[mask_fracture] - rupture_t) * 2
    ax.plot(escape_x, escape_y, color='silver', lw=2, linestyle='--', alpha=0.9, label='1816: Demonetization & Flight')
    
    ax.text(0, -3.5, "BIMETALLIC ALCHEMY\n(Parametric Twofold Generation)", ha='center', va='center', fontsize=14, fontweight='bold', color='#ffffff',
            bbox=dict(facecolor='#1a365d', edgecolor='#4299e1', boxstyle='round,pad=0.6'))
            
    ax.text(escape_x[-1], escape_y[-1], "Gresham's Fracture\n(Arbitrage escape velocity)", ha='right', va='bottom', fontsize=12, fontweight='bold', color='#ffffff',
            bbox=dict(facecolor='#742a2a', edgecolor='#feb2b2', boxstyle='round,pad=0.5'))
    
    ax.vlines(xs[mask_harmony][-1], -4, escape_y[-1] + 2, color='#fc8181', linestyle=':', lw=3, label='1816 Coinage Act Singular Boundary')
    
    ax.legend(loc='upper left', frameon=True, fontsize=12, facecolor='#111111', edgecolor='#a0aec0', shadow=True)
    
    ax.set_xlim(-4, escape_x[-1] + 4)
    ax.set_ylim(-4, escape_y[-1] + 4)
    save_and_close(output_path)
