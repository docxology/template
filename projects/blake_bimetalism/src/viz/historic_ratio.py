import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def render_historic_ratio(output_path: Path):
    """Renders empirical divergence between Newton's 1717 Mint Ratio, Hamilton's US ratio,
    and the European Market Ratio, showing the transatlantic arbitrage dynamics."""
    # British data: London Bullion Market historical ratios, 1717-1816
    years_uk = [1717, 1720, 1730, 1740, 1750, 1760, 1770, 1780, 1790, 1800, 1810, 1814, 1816]
    market_ratio = [15.13, 15.04, 14.81, 14.94, 14.55, 14.14, 14.62, 14.72, 14.90, 15.68, 15.77, 15.04, 15.20]
    mint_ratio_uk = [15.21] * len(years_uk)

    # US data: Hamilton's 15:1 (1792-1834), revised to 16:1 (1834-1873)
    years_us = [1792, 1800, 1810, 1820, 1830, 1834, 1840, 1850, 1860, 1870, 1873]
    mint_ratio_us = [15.0, 15.0, 15.0, 15.0, 15.0, 16.0, 16.0, 16.0, 16.0, 16.0, 16.0]

    # Extended market ratio through 1873
    years_market_ext = [1717, 1720, 1730, 1740, 1750, 1760, 1770, 1780, 1790, 1800,
                        1810, 1820, 1830, 1840, 1850, 1860, 1870, 1873]
    market_ratio_ext = [15.13, 15.04, 14.81, 14.94, 14.55, 14.14, 14.62, 14.72, 14.90,
                        15.68, 15.77, 15.35, 15.80, 15.85, 15.70, 15.30, 15.57, 15.92]

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(14, 8), facecolor='#111111')
    ax.set_facecolor('#111111')

    # Plot lines
    ax.plot(years_market_ext, market_ratio_ext, label='European Market Ratio (Silver:Gold)',
            color='#ecc94b', linewidth=3, marker='o', markersize=7, zorder=4)
    ax.plot(years_uk, mint_ratio_uk, label="Newton's English Mint Ratio (15.21:1)",
            color='#e2e8f0', linestyle='--', linewidth=2.5, zorder=3)
    ax.plot(years_us, mint_ratio_us, label="Hamilton's US Mint Ratio (15:1 → 16:1)",
            color='#68d391', linestyle='-.', linewidth=2.5, marker='s', markersize=6, zorder=3)

    # Highlight zones
    ax.fill_between(years_uk, mint_ratio_uk, [market_ratio[i] for i in range(len(years_uk))],
                    where=(np.array(market_ratio) < np.array(mint_ratio_uk)),
                    interpolate=True, color='#e2e8f0', alpha=0.12, label='Silver Undervalued → Exported')
    ax.fill_between(years_uk, mint_ratio_uk, [market_ratio[i] for i in range(len(years_uk))],
                    where=(np.array(market_ratio) > np.array(mint_ratio_uk)),
                    interpolate=True, color='#ecc94b', alpha=0.12, label='Gold Undervalued → Imported')

    # Labels & Styling
    ax.set_title("Transatlantic Arbitrage: British, American, and Market Ratios (1717–1873)",
                 color='white', pad=25, fontsize=19, fontweight='bold', fontfamily='serif')
    ax.set_xlabel("Year", color='#e2e8f0', fontsize=14, labelpad=10)
    ax.set_ylabel("Ounces of Silver per Ounce of Gold", color='#e2e8f0', fontsize=14, labelpad=10)

    ax.grid(True, color='#2d3748', linestyle=':')
    ax.spines['bottom'].set_color('#4a5568')
    ax.spines['left'].set_color('#4a5568')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(colors='#e2e8f0', labelsize=13)

    # Key events
    events = [
        (1792, '#68d391', 'US Coinage Act\n(Hamilton 15:1)'),
        (1797, '#fc8181', 'Bank Restriction\n(27 Feb 1797)'),
        (1816, '#63b3ed', 'British Coinage Act\n(Gold Standard)'),
        (1834, '#b794f4', 'US Ratio Revised\n(16:1)'),
        (1873, '#ed64a6', '"Crime of 1873"\n(Silver Demonetized)')
    ]
    text_y_positions = [14.1, 14.25, 14.1, 14.25, 14.1]
    for (yr, col, lbl), ty in zip(events, text_y_positions):
        ax.axvline(x=yr, color=col, linestyle=':', alpha=0.8, linewidth=1.8)
        ax.text(yr + 1.5, ty, lbl, color=col, rotation=90, va='bottom', fontsize=11, fontweight='bold')

    ax.legend(loc='upper left', facecolor='#1a202c', edgecolor='#4a5568', labelcolor='white', fontsize=11)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    plt.close(fig)
