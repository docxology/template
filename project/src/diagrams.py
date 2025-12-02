"""Publication-Quality Diagrams for Boundary Logic.

This module provides tools for generating publication-ready figures
for academic papers on Containment Theory and Laws of Form.

Diagram types:
- Form structure diagrams
- Reduction sequence diagrams
- Comparison tables as figures
- Theorem proof diagrams
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Arrow
import numpy as np

from src.forms import Form, make_void, make_mark, enclose, juxtapose
from src.reduction import reduce_with_trace, ReductionTrace
from src.theorems import get_all_axioms, get_all_consequences


@dataclass
class DiagramStyle:
    """Style for publication diagrams.
    
    Attributes:
        font_family: Font family for text
        title_size: Title font size
        label_size: Label font size
        line_width: Line width
        colors: Color palette
    """
    font_family: str = "serif"
    title_size: int = 14
    label_size: int = 11
    line_width: float = 1.5
    colors: Dict[str, str] = None
    
    def __post_init__(self):
        if self.colors is None:
            self.colors = {
                "primary": "#2c3e50",
                "secondary": "#3498db",
                "accent": "#e74c3c",
                "background": "#ecf0f1",
                "mark": "#27ae60",
                "void": "#95a5a6",
            }


class PublicationDiagramGenerator:
    """Generator for publication-quality diagrams."""
    
    def __init__(self, style: DiagramStyle = None) -> None:
        """Initialize generator.
        
        Args:
            style: Diagram style configuration
        """
        self.style = style or DiagramStyle()
        plt.rcParams['font.family'] = self.style.font_family
    
    def create_axiom_figure(self, output_path: str = None) -> plt.Figure:
        """Create figure showing the two fundamental axioms.
        
        Args:
            output_path: Optional path to save figure
            
        Returns:
            matplotlib Figure
        """
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        
        # Axiom J1
        ax = axes[0]
        ax.text(0.5, 0.7, "Axiom J1 (Calling)", fontsize=self.style.title_size,
               ha='center', transform=ax.transAxes, fontweight='bold')
        ax.text(0.5, 0.5, r"$\langle\langle a \rangle\rangle = a$",
               fontsize=18, ha='center', transform=ax.transAxes)
        ax.text(0.5, 0.25, "Double crossing returns\nto the original state",
               fontsize=self.style.label_size, ha='center', transform=ax.transAxes,
               style='italic')
        ax.axis('off')
        
        # Axiom J2
        ax = axes[1]
        ax.text(0.5, 0.7, "Axiom J2 (Crossing)", fontsize=self.style.title_size,
               ha='center', transform=ax.transAxes, fontweight='bold')
        ax.text(0.5, 0.5, r"$\langle\ \rangle\langle\ \rangle = \langle\ \rangle$",
               fontsize=18, ha='center', transform=ax.transAxes)
        ax.text(0.5, 0.25, "Multiple marks condense\nto a single mark",
               fontsize=self.style.label_size, ha='center', transform=ax.transAxes,
               style='italic')
        ax.axis('off')
        
        plt.suptitle("The Two Axioms of Boundary Logic",
                    fontsize=self.style.title_size + 2, fontweight='bold')
        plt.tight_layout()
        
        if output_path:
            self._save_figure(fig, output_path)
        
        return fig
    
    def create_boolean_mapping_figure(self, output_path: str = None) -> plt.Figure:
        """Create figure showing Boolean algebra correspondence.
        
        Args:
            output_path: Optional path to save figure
            
        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create table data
        data = [
            ["Boolean", "Boundary Logic", "Description"],
            ["TRUE (1)", "⟨ ⟩ (mark)", "The marked state"],
            ["FALSE (0)", "∅ (void)", "Empty, unmarked"],
            ["NOT a", "⟨a⟩", "Enclosure negates"],
            ["a AND b", "ab", "Juxtaposition"],
            ["a OR b", "⟨⟨a⟩⟨b⟩⟩", "De Morgan form"],
            ["a → b", "⟨a⟨b⟩⟩", "Implication"],
        ]
        
        # Draw table
        ax.axis('off')
        table = ax.table(
            cellText=data[1:],
            colLabels=data[0],
            cellLoc='center',
            loc='center',
            colColours=[self.style.colors["background"]] * 3,
        )
        table.auto_set_font_size(False)
        table.set_fontsize(self.style.label_size)
        table.scale(1.2, 1.8)
        
        plt.title("Boolean Algebra ↔ Boundary Logic Correspondence",
                 fontsize=self.style.title_size, fontweight='bold', pad=20)
        
        if output_path:
            self._save_figure(fig, output_path)
        
        return fig
    
    def create_reduction_diagram(
        self,
        form: Form,
        output_path: str = None
    ) -> plt.Figure:
        """Create diagram showing reduction steps.
        
        Args:
            form: Form to reduce
            output_path: Optional output path
            
        Returns:
            matplotlib Figure
        """
        trace = reduce_with_trace(form)
        n_steps = len(trace.steps) + 2  # Original + steps + final
        
        fig, ax = plt.subplots(figsize=(12, 3))
        ax.set_xlim(-0.5, n_steps - 0.5)
        ax.set_ylim(-0.5, 1.5)
        ax.axis('off')
        
        # Draw original
        ax.text(0, 1, str(trace.original), fontsize=14, ha='center', va='center',
               fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor=self.style.colors["background"]))
        ax.text(0, 0.3, "Original", fontsize=10, ha='center', va='center')
        
        # Draw steps
        current_x = 1
        for i, step in enumerate(trace.steps):
            # Arrow
            ax.annotate('', xy=(current_x - 0.3, 1), xytext=(current_x - 0.7, 1),
                       arrowprops=dict(arrowstyle='->', color=self.style.colors["secondary"]))
            ax.text(current_x - 0.5, 0.7, step.rule.value, fontsize=8, ha='center',
                   color=self.style.colors["secondary"])
            
            # Form
            ax.text(current_x, 1, str(step.after), fontsize=14, ha='center', va='center',
                   fontfamily='monospace',
                   bbox=dict(boxstyle='round', facecolor=self.style.colors["background"]))
            ax.text(current_x, 0.3, f"Step {i+1}", fontsize=10, ha='center')
            
            current_x += 1
        
        # Final arrow and canonical form
        if trace.steps:
            ax.annotate('', xy=(current_x - 0.3, 1), xytext=(current_x - 0.7, 1),
                       arrowprops=dict(arrowstyle='->', color=self.style.colors["mark"]))
        
        canonical_str = str(trace.canonical) if not trace.canonical.is_void() else "∅"
        ax.text(current_x, 1, canonical_str, fontsize=16, ha='center', va='center',
               fontfamily='monospace', fontweight='bold',
               bbox=dict(boxstyle='round', facecolor=self.style.colors["mark"], alpha=0.3))
        ax.text(current_x, 0.3, "Canonical", fontsize=10, ha='center', fontweight='bold')
        
        plt.title(f"Reduction of {trace.original}", fontsize=self.style.title_size,
                 fontweight='bold')
        plt.tight_layout()
        
        if output_path:
            self._save_figure(fig, output_path)
        
        return fig
    
    def create_theorem_summary_figure(self, output_path: str = None) -> plt.Figure:
        """Create figure summarizing all theorems.
        
        Args:
            output_path: Optional output path
            
        Returns:
            matplotlib Figure
        """
        axioms = get_all_axioms()
        consequences = get_all_consequences()
        
        n_theorems = len(axioms) + len(consequences)
        fig, ax = plt.subplots(figsize=(12, max(8, n_theorems * 0.6)))
        ax.axis('off')
        
        y = 1.0
        y_step = 1.0 / (n_theorems + 3)
        
        # Title
        ax.text(0.5, y, "Theorems of Boundary Logic",
               fontsize=self.style.title_size + 2, ha='center',
               transform=ax.transAxes, fontweight='bold')
        y -= y_step * 1.5
        
        # Axioms section
        ax.text(0.1, y, "Axioms (Primitive)", fontsize=self.style.title_size,
               transform=ax.transAxes, fontweight='bold',
               color=self.style.colors["primary"])
        y -= y_step
        
        for theorem in axioms:
            theorem.verify()
            status = "✓" if theorem.status.value == "verified" else "✗"
            ax.text(0.15, y, f"{status} {theorem.name}:",
                   fontsize=self.style.label_size, transform=ax.transAxes)
            ax.text(0.45, y, f"{theorem.lhs} = {theorem.rhs}",
                   fontsize=self.style.label_size, transform=ax.transAxes,
                   fontfamily='monospace')
            y -= y_step
        
        # Consequences section
        y -= y_step * 0.5
        ax.text(0.1, y, "Consequences (Derived)", fontsize=self.style.title_size,
               transform=ax.transAxes, fontweight='bold',
               color=self.style.colors["primary"])
        y -= y_step
        
        for theorem in consequences:
            theorem.verify()
            status = "✓" if theorem.status.value == "verified" else "?"
            ax.text(0.15, y, f"{status} {theorem.name}:",
                   fontsize=self.style.label_size - 1, transform=ax.transAxes)
            ax.text(0.45, y, theorem.description[:50] + "...",
                   fontsize=self.style.label_size - 1, transform=ax.transAxes,
                   style='italic')
            y -= y_step
        
        plt.tight_layout()
        
        if output_path:
            self._save_figure(fig, output_path)
        
        return fig
    
    def create_comparison_figure(self, output_path: str = None) -> plt.Figure:
        """Create Set Theory vs Boundary Logic comparison figure.
        
        Args:
            output_path: Optional output path
            
        Returns:
            matplotlib Figure
        """
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        
        # Set Theory column
        ax = axes[0]
        ax.set_title("Set Theory (ZFC)", fontsize=self.style.title_size,
                    fontweight='bold', color=self.style.colors["primary"])
        ax.axis('off')
        
        set_theory_points = [
            "• 9+ axioms (ZFC system)",
            "• Primitive: membership (∈)",
            "• Prohibits self-reference",
            "• Complex axiom of choice",
            "• Requires infinity axiom",
            "• Universal mathematical standard",
        ]
        y = 0.9
        for point in set_theory_points:
            ax.text(0.1, y, point, fontsize=self.style.label_size,
                   transform=ax.transAxes)
            y -= 0.12
        
        # Boundary Logic column
        ax = axes[1]
        ax.set_title("Boundary Logic", fontsize=self.style.title_size,
                    fontweight='bold', color=self.style.colors["secondary"])
        ax.axis('off')
        
        boundary_points = [
            "• 2 axioms only (J1, J2)",
            "• Primitive: distinction (boundary)",
            "• Handles self-reference",
            "• No choice axiom needed",
            "• No infinity required",
            "• Direct spatial intuition",
        ]
        y = 0.9
        for point in boundary_points:
            ax.text(0.1, y, point, fontsize=self.style.label_size,
                   transform=ax.transAxes)
            y -= 0.12
        
        plt.suptitle("Foundational Comparison",
                    fontsize=self.style.title_size + 2, fontweight='bold')
        plt.tight_layout()
        
        if output_path:
            self._save_figure(fig, output_path)
        
        return fig
    
    def _save_figure(self, fig: plt.Figure, path: str) -> None:
        """Save figure to file.
        
        Args:
            fig: Figure to save
            path: Output path
        """
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')


def generate_all_figures(output_dir: str = "output/figures") -> Dict[str, Path]:
    """Generate all publication figures.
    
    Args:
        output_dir: Output directory
        
    Returns:
        Dictionary mapping figure names to paths
    """
    generator = PublicationDiagramGenerator()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    figures = {}
    
    # Axioms figure
    path = output_path / "axioms.png"
    generator.create_axiom_figure(str(path))
    figures["axioms"] = path
    
    # Boolean mapping
    path = output_path / "boolean_mapping.png"
    generator.create_boolean_mapping_figure(str(path))
    figures["boolean_mapping"] = path
    
    # Example reductions
    form1 = enclose(enclose(make_mark()))
    path = output_path / "reduction_calling.png"
    generator.create_reduction_diagram(form1, str(path))
    figures["reduction_calling"] = path
    
    form2 = juxtapose(make_mark(), make_mark(), make_mark())
    path = output_path / "reduction_crossing.png"
    generator.create_reduction_diagram(form2, str(path))
    figures["reduction_crossing"] = path
    
    # Theorem summary
    path = output_path / "theorem_summary.png"
    generator.create_theorem_summary_figure(str(path))
    figures["theorem_summary"] = path
    
    # Comparison
    path = output_path / "comparison.png"
    generator.create_comparison_figure(str(path))
    figures["comparison"] = path
    
    return figures

