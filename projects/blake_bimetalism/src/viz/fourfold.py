
from .core import setup_figure, save_and_close, patches
from pathlib import Path

def render_fourfold_mapping(output_path: Path):
    fig, ax = setup_figure(figsize=(10, 8), title="The Monetary Ascension: From Ulro Quantification to Edenic Qualification")
    
    levels = [
        {"y": 1, "title": "Single Vision (Ulro)", "monetary": "Monometallism (Gold)", "desc": "Absolute Quantification & Reduction (1816 Coinage Act)", "color": "#d9534f"},
        {"y": 2, "title": "Twofold Vision (Generation)", "monetary": "Bimetallism", "desc": "Meta-stable Generative Marriage & Arbitrage Tension", "color": "#f0ad4e"},
        {"y": 3, "title": "Threefold Vision (Beulah)", "monetary": "Social & Affective Credit", "desc": "Transition from Quantification to Qualification", "color": "#5bc0de"},
        {"y": 4, "title": "Fourfold Vision (Eden)", "monetary": "Regenerate 4-Fold Man", "desc": "Pure Qualitative Human Integration (Albion)", "color": "#5cb85c"}
    ]
    
    for lvl in levels:
        rect = patches.FancyBboxPatch((0.15, lvl["y"] - 0.3), 0.7, 0.6, 
                                      boxstyle="round,pad=0.1", 
                                      linewidth=2, edgecolor=lvl["color"], facecolor=lvl["color"], alpha=0.1)
        ax.add_patch(rect)
        
        ax.text(0.5, lvl["y"] + 0.15, lvl["title"], ha='center', va='center', fontsize=14, fontweight='bold', color=lvl["color"])
        ax.text(0.5, lvl["y"] - 0.05, lvl["monetary"], ha='center', va='center', fontsize=12, fontweight='bold', color='black')
        ax.text(0.5, lvl["y"] - 0.25, lvl["desc"], ha='center', va='center', fontsize=10, fontstyle='italic', color='#333333')
        
    for i in range(1, 4):
        ax.annotate('', xy=(0.5, i + 0.6), xytext=(0.5, i + 0.35),
            arrowprops=dict(facecolor='black', width=2, headwidth=10, alpha=0.5))
            
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 5)
    ax.axis('off')

    save_and_close(output_path)
