import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def render_historic_reserves(output_path: Path):
    """
    Renders empirical divergence between Bank of England Note Issuance and Physical Reserves (1790-1821).
    """
    # Estimated scholarly data points (in Millions £) - based on Bank of England historical ledgers
    years = [1790, 1795, 1797, 1800, 1805, 1810, 1814, 1816, 1821]
    notes = [10.0, 14.0, 16.5, 16.0, 17.5, 24.0, 28.5, 27.0, 20.5]
    reserves = [8.0, 6.5, 1.1, 5.5, 6.0, 3.5, 2.0, 3.0, 11.8]

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 7), facecolor='#111111')
    ax.set_facecolor('#111111')

    # Fill areas
    ax.fill_between(years, notes, color='#e53e3e', alpha=0.35, label='Fictional Paper Credit (Notes Issued)')
    ax.fill_between(years, reserves, color='#d69e2e', alpha=0.6, label='Physical Gold Subsistence')

    # Plot lines
    ax.plot(years, notes, color='#fc8181', linewidth=3, marker='o', markersize=8)
    ax.plot(years, reserves, color='#f6e05e', linewidth=3, marker='o', markersize=8)

    # Styling
    ax.set_title("The Flight of Credit: Bank of England Note Issuance vs. Gold Reserves (1790-1821)", color='white', pad=25, fontsize=18, fontweight='bold', fontfamily='serif')
    ax.set_xlabel("Year", color='#e2e8f0', fontsize=14, labelpad=10)
    ax.set_ylabel("Millions (£ Sterling)", color='#e2e8f0', fontsize=14, labelpad=10)
    
    ax.grid(True, color='#2d3748', linestyle=':')
    ax.spines['bottom'].set_color('#4a5568')
    ax.spines['left'].set_color('#4a5568')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(colors='#e2e8f0', labelsize=12)

    # Key events annotations
    ax.axvline(x=1797, color='#fc8181', linestyle=':', alpha=0.9, linewidth=2)
    ax.text(1797.5, 22, '1797 Suspension of Specie', color='#fc8181', rotation=90, va='center', fontsize=12, fontweight='bold')
    
    ax.axvline(x=1821, color='#63b3ed', linestyle=':', alpha=0.9, linewidth=2)
    ax.text(1820.5, 22, '1821 Resumption', color='#63b3ed', rotation=90, va='center', fontsize=12, fontweight='bold')

    # Conceptual Annotations
    ax.text(1812, 16.5, "Urizen's Allegoric Riches", color='white', style='italic', fontsize=14, ha='center', bbox=dict(facecolor='#1a202c', edgecolor='#e53e3e', boxstyle='round,pad=0.4', alpha=0.7))

    ax.legend(loc='upper left', facecolor='#1a202c', edgecolor='#4a5568', labelcolor='white', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#111111')
    plt.close(fig)
