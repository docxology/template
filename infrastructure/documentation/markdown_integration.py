"""Markdown integration for scientific computing.

This module provides LaTeX figure block generation, section detection,
reference insertion, table of figures generation, and figure list maintenance.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .figure_manager import FigureManager
from .image_manager import ImageManager


class MarkdownIntegration:
    """Integrates figures and references into markdown files."""
    
    def __init__(
        self,
        manuscript_dir: Optional[Path] = None,
        figure_manager: Optional[FigureManager] = None
    ):
        """Initialize markdown integration.
        
        Args:
            manuscript_dir: Directory containing markdown files
            figure_manager: FigureManager instance
        """
        if manuscript_dir is None:
            manuscript_dir = Path("manuscript")
        
        self.manuscript_dir = Path(manuscript_dir)
        self.figure_manager = figure_manager or FigureManager()
        self.image_manager = ImageManager(self.figure_manager)
    
    def detect_sections(self, markdown_file: Path) -> List[Dict[str, Any]]:
        """Detect sections in markdown file.
        
        Args:
            markdown_file: Path to markdown file
            
        Returns:
            List of section dictionaries with name, level, and position
        """
        if not markdown_file.exists():
            return []
        
        content = markdown_file.read_text(encoding='utf-8')
        sections = []
        
        # Find all section headers
        section_pattern = r"^(#+)\s+(.+?)\s*(?:\{#([^}]+)\})?\s*$"
        matches = re.finditer(section_pattern, content, re.MULTILINE)
        
        for match in matches:
            level = len(match.group(1))
            name = match.group(2).strip()
            anchor = match.group(3)
            
            sections.append({
                "name": name,
                "level": level,
                "anchor": anchor,
                "position": match.start(),
                "line_number": content[:match.start()].count('\n') + 1
            })
        
        return sections
    
    def insert_figure_in_section(
        self,
        markdown_file: Path,
        figure_label: str,
        section_name: str,
        position: str = "after"
    ) -> bool:
        """Insert figure in specific section.
        
        Args:
            markdown_file: Path to markdown file
            figure_label: Figure label
            section_name: Section name
            position: Position relative to section (before, after)
            
        Returns:
            True if successful
        """
        return self.image_manager.insert_figure(
            markdown_file,
            figure_label,
            section=section_name,
            position=f"{position}_section"
        )
    
    def generate_table_of_figures(self, output_file: Optional[Path] = None) -> Path:
        """Generate table of figures markdown file.
        
        Args:
            output_file: Output file path (auto-generated if None)
            
        Returns:
            Path to generated file
        """
        if output_file is None:
            output_file = self.manuscript_dir / "00_table_of_figures.md"
        
        content = self.figure_manager.generate_table_of_figures()
        
        # Convert LaTeX to markdown format
        markdown_content = "# Table of Figures\n\n"
        markdown_content += "This document lists all figures in the manuscript.\n\n"
        
        for fig_meta in sorted(
            self.figure_manager.get_all_figures(),
            key=lambda f: f.figure_id
        ):
            markdown_content += f"## {fig_meta.label}\n\n"
            markdown_content += f"**Caption**: {fig_meta.caption}\n\n"
            if fig_meta.section:
                markdown_content += f"**Section**: {fig_meta.section}\n\n"
            markdown_content += f"**File**: `{fig_meta.filename}`\n\n"
            markdown_content += f"**LaTeX Block**:\n\n```latex\n"
            markdown_content += self.figure_manager.generate_latex_figure_block(fig_meta.label)
            markdown_content += "\n```\n\n"
        
        output_file.write_text(markdown_content, encoding='utf-8')
        
        return output_file
    
    def update_all_references(self, markdown_file: Path) -> int:
        """Update all figure references in markdown file.
        
        Args:
            markdown_file: Path to markdown file
            
        Returns:
            Number of references updated
        """
        if not markdown_file.exists():
            return 0
        
        content = markdown_file.read_text(encoding='utf-8')
        updated = 0
        
        # Find all figure labels
        label_pattern = r"\\label\{(fig:[^}]+)\}"
        labels = set(re.findall(label_pattern, content))
        
        # For each label, ensure reference exists
        for label in labels:
            # Check if reference exists
            ref_pattern = rf"\\ref\{{{re.escape(label)}\}}"
            if not re.search(ref_pattern, content):
                # Insert reference after figure
                figure_pos = content.find(f"\\label{{{label}}}")
                if figure_pos != -1:
                    # Find end of figure block
                    figure_end = content.find("\\end{figure}", figure_pos)
                    if figure_end != -1:
                        # Insert reference in next paragraph
                        next_para = re.search(r"\n\n", content[figure_end:])
                        if next_para:
                            insert_pos = figure_end + next_para.end()
                            ref_text = f"See Figure \\ref{{{label}}}."
                            content = (
                                content[:insert_pos] +
                                f" {ref_text}" +
                                content[insert_pos:]
                            )
                            updated += 1
        
        # Write back
        markdown_file.write_text(content, encoding='utf-8')
        
        return updated
    
    def validate_manuscript(self) -> Dict[str, List[Tuple[str, str]]]:
        """Validate all figures in manuscript.
        
        Returns:
            Dictionary mapping file paths to list of (label, error) tuples
        """
        validation_results = {}
        
        # Find all markdown files
        for md_file in self.manuscript_dir.glob("*.md"):
            errors = self.image_manager.validate_figures(md_file)
            if errors:
                validation_results[str(md_file)] = errors
        
        return validation_results
    
    def get_figure_statistics(self) -> Dict[str, Any]:
        """Get statistics about figures in manuscript.
        
        Returns:
            Dictionary with statistics
        """
        all_figures = self.figure_manager.get_all_figures()
        
        # Count figures by section
        figures_by_section: Dict[str, int] = {}
        for fig in all_figures:
            section = fig.section or "unknown"
            figures_by_section[section] = figures_by_section.get(section, 0) + 1
        
        # Count figures by generator
        figures_by_generator: Dict[str, int] = {}
        for fig in all_figures:
            generator = fig.generated_by or "unknown"
            figures_by_generator[generator] = figures_by_generator.get(generator, 0) + 1
        
        return {
            "total_figures": len(all_figures),
            "figures_by_section": figures_by_section,
            "figures_by_generator": figures_by_generator,
            "registered_labels": [fig.label for fig in all_figures]
        }

