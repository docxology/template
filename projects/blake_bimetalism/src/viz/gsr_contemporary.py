"""
Gold-to-Silver Ratio (GSR) Contemporary Visualization (2010–2026).

Renders the empirical GSR trajectory from 2010 through Q1 2026, annotating
structurally significant events: COVID panic peak (125.45:1, March 2020),
Silver Squeeze (February 2021), G7 Russian reserve freeze (March 2022),
BRICS+ Johannesburg summit (August 2023), and the silver all-time nominal
high / GSR floor (January 2026). Supports the Eq. gsr_modernity formalism
in manuscript section 05f_contemporary_metal_resurgence.md.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path


def render_gsr_contemporary(output_path: Path) -> None:
    """Renders the contemporary Gold-to-Silver Ratio (2010-2026) with Blakean annotations.

    Data sourced from LBMA monthly benchmark averages and Silver Institute
    World Silver Survey 2025 / World Gold Council Gold Demand Trends 2024.
    Monthly approximations used for illustrative scholarly visualization.
    """
    # Monthly GSR approximations (annual midpoints + key event snapshots)
    # Sources: LBMA, Silver Institute, World Gold Council
    years = [
        2010.0, 2011.0, 2011.5, 2012.0, 2013.0, 2014.0, 2015.0,
        2016.0, 2017.0, 2018.0, 2019.0,
        2020.0, 2020.25, 2020.5, 2020.75, 2021.0, 2021.25, 2021.5,
        2022.0, 2022.25, 2022.5, 2022.75, 2023.0, 2023.5,
        2024.0, 2024.25, 2024.75, 2025.0, 2025.5, 2025.75,
        2026.0, 2026.08, 2026.25
    ]
    gsr = [
        68.0, 41.0, 44.0, 53.0, 62.0, 65.0, 74.0,
        72.0, 77.0, 82.0, 86.0,
        89.0, 125.45, 101.0, 79.0, 69.0, 68.0, 73.0,
        79.0, 80.0, 91.0, 83.0, 82.0, 79.0,
        88.0, 82.0, 85.0, 90.0, 80.0, 65.0,
        55.0, 46.0, 63.0
    ]

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(16, 9), facecolor='#0d1117')
    ax.set_facecolor('#0d1117')

    # Shade the COVID fiat expansion era
    ax.axvspan(2020.0, 2021.0, alpha=0.13, color='#fc8181', zorder=0,
               label='Maximum Fiat Expansion (Fed: $4.2T→$9.0T)')

    # Historical 15:1 Newtonian reference line
    ax.axhline(y=15.21, color='#f6e05e', linestyle=':', linewidth=1.4, alpha=0.5)
    ax.text(2010.15, 17.5, "Newton's 1717 Mint Ratio (15.21:1)",
            color='#f6e05e', fontsize=10, alpha=0.7, fontstyle='italic')

    # Historical 1:16 US Mint reference line
    ax.axhline(y=16.0, color='#68d391', linestyle=':', linewidth=1.0, alpha=0.35)

    # Main GSR line
    ax.plot(years, gsr, color='#e2e8f0', linewidth=3.0, zorder=4,
            label='Gold-to-Silver Ratio (monthly approx.)')
    ax.fill_between(years, gsr, 15.21, where=[g > 15.21 for g in gsr],
                    interpolate=True, color='#4a5568', alpha=0.25)

    # Key event annotations
    events = [
        (2020.25, 125.45, '#fc8181', 'COVID Panic Peak\n125.45:1 (Mar 2020)', 'right', -2),
        (2021.0,  69.0,   '#63b3ed', 'Silver Squeeze\n(Feb 2021)', 'right', -2),
        (2022.25, 80.0,   '#ed8936', "G7 Freezes Russia\u2019s\n$300B Reserves (Mar 2022)", 'left', 0.05),
        (2023.5,  79.0,   '#b794f4', 'BRICS+ Johannesburg\nSummit (Aug 2023)', 'right', -0.1),
        (2026.08, 46.0,   '#ecc94b', 'GSR Floor ~46:1\nAg ATH $121/oz (Jan 2026)', 'left', 0.05),
    ]

    for (xv, yv, col, label, ha, x_offset) in events:
        ax.axvline(x=xv, color=col, linestyle='--', alpha=0.65, linewidth=1.6, zorder=3)
        ax.plot(xv, yv, 'o', color=col, markersize=10, zorder=6)
        ax.annotate(
            label,
            xy=(xv, yv),
            xytext=(xv + x_offset, yv + 12),
            fontsize=10, color=col, fontweight='bold',
            ha=ha, va='bottom',
            arrowprops=dict(arrowstyle='->', color=col, lw=1.4),
            bbox=dict(facecolor='#1a202c', edgecolor=col, boxstyle='round,pad=0.4', alpha=0.9)
        )

    # GSR range bands with Blakean labels
    ax.axhspan(0, 50, alpha=0.07, color='#ecc94b')
    ax.axhspan(80, 130, alpha=0.07, color='#fc8181')
    ax.text(2025.5, 25, 'Bimetallic\nEquilibrium Zone', ha='center', va='center',
            fontsize=10, color='#ecc94b', alpha=0.8, fontstyle='italic')
    ax.text(2010.5, 110, 'Urizenic\nOverextension', ha='center', va='center',
            fontsize=10, color='#fc8181', alpha=0.8, fontstyle='italic')

    # Styling
    ax.set_title(
        "Gold-to-Silver Ratio (2010–2026): From Fiat Panic to Industrial Rebalancing",
        color='white', fontsize=18, fontweight='bold', fontfamily='serif', pad=20
    )
    ax.set_xlabel("Year", color='#e2e8f0', fontsize=14, labelpad=10)
    ax.set_ylabel("Ounces of Silver per Ounce of Gold (GSR)", color='#e2e8f0', fontsize=13, labelpad=10)
    ax.set_xlim(2009.5, 2026.5)
    ax.set_ylim(0, 140)
    ax.tick_params(colors='#e2e8f0', labelsize=12)
    ax.grid(True, color='#2d3748', linestyle=':', alpha=0.6)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['bottom', 'left']:
        ax.spines[spine].set_color('#4a5568')

    legend = ax.legend(
        loc='upper left', facecolor='#1a202c', edgecolor='#4a5568',
        labelcolor='white', fontsize=11, framealpha=0.92
    )

    # Equation annotation
    ax.text(
        0.01, 0.03,
        r"$\mathrm{GSR}(t) = P_{\mathrm{Au}}(t)\,/\,P_{\mathrm{Ag}}(t)$"
        "\n(Eq. gsr_modernity; sources: LBMA, Silver Institute WSS 2025, WGC 2024)",
        transform=ax.transAxes, fontsize=9, color='#718096',
        va='bottom', ha='left', fontstyle='italic'
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#0d1117')
    plt.close(fig)
