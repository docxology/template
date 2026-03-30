import matplotlib.pyplot as plt
from pathlib import Path

def render_timeline(output_path: Path):
    """Renders a dual-axis chronology covering British and American financial events
    alongside Blake's prophetic output (1710-1900)."""
    financial_years = [1717, 1792, 1797, 1816, 1821, 1873, 1896]
    financial_labels = [
        "1717: Newton fixes Guinea\n(Bimetallic ratio 15.21:1)",
        "1792: US Coinage Act\n(Hamilton's ratio 15:1)",
        "1797: Bank Restriction\n(Suspension of Specie)",
        "1816: British Coinage Act\n(De jure Gold Standard)",
        "1821: Resumption\n(Peel's Act, 1819)",
        "1873: Crime of '73\n(US Silver Demonetized)",
        "1896: Cross of Gold\n(Bryan's Free Silver)"
    ]
    blake_years = [1789, 1793, 1794, 1804, 1820, 1827]
    blake_labels = [
        "1789: Book of Thel\n('Silver Rod/Golden Bowl')",
        "1793: America a Prophecy\n(Orc vs Urizen)",
        "1794: Songs of Experience\n('Mind-forg'd manacles')",
        "1797-1807: The Four Zoas\n(Vala & Urizenic War)",
        "1804-1820: Jerusalem\n('Allegoric riches')",
        "1827: Blake dies\n(Final Illuminations)"
    ]
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(18, 9), facecolor='#111111', constrained_layout=True)
    ax.set_facecolor('#111111')
    ax.set_title("Dual-Axis Chronology: Financial Collapse and Prophetic Ascent (1710–1900)",
                 fontsize=20, fontweight='bold', fontfamily='serif', pad=30, color='white')

    # Axis region labels
    ax.text(1712, 1.85, 'FINANCIAL EVENTS', fontsize=14, fontweight='bold',
            color='#63b3ed', fontstyle='italic', va='center', ha='left',
            bbox=dict(facecolor='#111111', edgecolor='#63b3ed', boxstyle='round,pad=0.4', alpha=0.85))
    ax.text(1712, -2.15, "BLAKE'S PROPHETIC WORKS", fontsize=14, fontweight='bold',
            color='#ed8936', fontstyle='italic', va='center', ha='left',
            bbox=dict(facecolor='#111111', edgecolor='#ed8936', boxstyle='round,pad=0.4', alpha=0.85))

    # Central timeline axis
    ax.hlines(0, 1710, 1900, color='#888888', linewidth=2, alpha=0.6)

    # Financial events (above axis)
    ax.vlines(financial_years, 0, 0.5, color='#a0aec0', linestyles='solid', alpha=0.9, linewidth=2.5)
    ax.plot(financial_years, [0.5]*len(financial_years), "o", color='#63b3ed', markersize=11, zorder=5)

    financial_heights = [0.7, 1.55, 0.9, 1.55, 0.7, 1.55, 0.9]
    for year, label, height in zip(financial_years, financial_labels, financial_heights):
        ax.vlines(year, 0.5, height - 0.05, color='#a0aec0', linestyles='dotted', alpha=0.8)
        fc = '#1e3a5f' if year < 1850 else '#3a1e2f'
        ec = '#63b3ed' if year < 1850 else '#ed64a6'
        ax.text(year, height, label, ha='center', va='bottom', fontsize=12,
                color='white', bbox=dict(facecolor=fc, edgecolor=ec, boxstyle='round,pad=0.5', alpha=0.92))

    # Blake events (below axis)
    ax.vlines(blake_years, -0.5, 0, color='#f6ad55', linestyles='solid', alpha=0.9, linewidth=2.5)
    ax.plot(blake_years, [-0.5]*len(blake_years), "o", color='#ed8936', markersize=11, zorder=5)

    # Three alternating heights to prevent overlap, especially for clustered 1789-1794 events
    blake_heights = [-0.7, -1.2, -1.7, -0.7, -1.2, -1.7]
    # Per-label horizontal alignment and offsets for crowded years
    blake_has = ['right', 'center', 'left', 'center', 'center', 'center']
    blake_x_offsets = [-2, 0, 2, 0, 0, 0]
    for year, label, height, ha, x_off in zip(blake_years, blake_labels, blake_heights, blake_has, blake_x_offsets):
        ax.vlines(year, -0.5, height + 0.05, color='#f6ad55', linestyles='dotted', alpha=0.8)
        ax.text(year + x_off, height, label, ha=ha, va='top', fontsize=10,
                color='black', bbox=dict(facecolor='#feebc8', edgecolor='#ed8936', boxstyle='round,pad=0.4', alpha=0.92))

    # Shaded era bands
    ax.axvspan(1797, 1821, alpha=0.07, color='#fc8181', zorder=0)
    ax.text(1809, -2.45, 'Bank Restriction Period (1797–1821)', ha='center', fontsize=11, color='#fc8181', fontstyle='italic')

    ax.axvspan(1862, 1879, alpha=0.07, color='#68d391', zorder=0)
    ax.text(1870.5, -2.45, 'US Greenback Era (1862–1879)', ha='center', fontsize=11, color='#68d391', fontstyle='italic')

    # Axis formatting
    ax.set_xlim(1710, 1900)
    ax.set_ylim(-2.7, 2.1)
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    ticks = list(range(1720, 1901, 20))
    ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
    for tick in ticks:
        ax.plot([tick, tick], [-0.05, 0.05], color='#aaaaaa', linewidth=2)
        ax.text(tick, -0.15, str(tick), ha='center', va='top', fontsize=12, fontweight='bold', color='#cccccc', alpha=0.9)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    plt.close()
