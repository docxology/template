import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_viz():
    # Setup directory using pipeline environment or relative path
    project_dir = Path(os.environ.get("PROJECT_DIR", Path(__file__).parent.parent))
    output_dir = project_dir / "output" / "figures"
    os.makedirs(output_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Styles
    infra_color = "#e3f2fd"
    project_color = "#fff3e0"
    edge_color = "#1565c0"

    # Infrastructure Box
    ax.add_patch(patches.Rectangle((10, 60), 80, 30, facecolor=infra_color, edgecolor=edge_color, alpha=0.5))
    ax.text(50, 85, "INFRASTRUCTURE LAYER (Modules)", weight='bold', ha='center', size=14)
    
    modules = ["Core", "Steganography", "Rendering", "LLM", "Scientific", "Validation"]
    for i, mod in enumerate(modules):
        x = 15 + i*13
        ax.add_patch(patches.Circle((x, 72), 5, facecolor='white', edgecolor=edge_color))
        ax.text(x, 72, mod, ha='center', va='center', size=8)

    # Pipeline Arrow
    ax.annotate("", xy=(50, 40), xytext=(50, 60), arrowprops=dict(arrowstyle="->", lw=2, color=edge_color))
    ax.text(52, 50, "7-Stage Pipeline", weight='bold', color=edge_color)

    # Project Box
    ax.add_patch(patches.Rectangle((20, 10), 60, 30, facecolor=project_color, edgecolor='#e65100', alpha=0.5))
    ax.text(50, 35, "PROJECT LAYER (Workspaces)", weight='bold', ha='center', size=14)
    
    ax.text(50, 22, "manuscript/ (Prose)\nscripts/ (Logic)\ndata/ (Results)\noutput/ (PDF)", ha='center', va='center', size=10)

    # Final Output
    ax.annotate("Final Secured PDF", xy=(90, 20), xytext=(80, 20), arrowprops=dict(arrowstyle="->", lw=2, color='green'))

    plt.title("The Docxology Template Architecture", size=18, pad=20)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/architecture_viz.png", dpi=300, bbox_inches='tight')
    print(f"Visualization saved to {output_dir}/architecture_viz.png")

if __name__ == "__main__":
    generate_viz()
