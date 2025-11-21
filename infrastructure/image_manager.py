"""Image management for scientific computing.

This module provides automatic insertion into markdown files,
caption management, label generation, cross-reference creation,
path management, and validation.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from figure_manager import FigureManager, FigureMetadata


class ImageManager:
    """Manages image insertion and cross-referencing in markdown files."""
    
    def __init__(self, figure_manager: Optional[FigureManager] = None):
        """Initialize image manager.
        
        Args:
            figure_manager: FigureManager instance (creates new if None)
        """
        self.figure_manager = figure_manager or FigureManager()
    
    def insert_figure(
        self,
        markdown_file: Path,
        figure_label: str,
        section: Optional[str] = None,
        position: str = "after_section"
    ) -> bool:
        """Insert figure into markdown file.
        
        Args:
            markdown_file: Path to markdown file
            figure_label: Label of figure to insert
            section: Section name to insert after
            position: Position strategy (after_section, before_section, end)
            
        Returns:
            True if insertion successful
        """
        fig_meta = self.figure_manager.get_figure(figure_label)
        if fig_meta is None:
            return False
        
        if not markdown_file.exists():
            return False
        
        # Read markdown file
        content = markdown_file.read_text(encoding='utf-8')
        
        # Check if figure already inserted
        if f"\\label{{{figure_label}}}" in content:
            return True  # Already inserted
        
        # Generate LaTeX figure block
        figure_block = self.figure_manager.generate_latex_figure_block(figure_label)
        
        # Find insertion point
        insertion_point = self._find_insertion_point(
            content, section, position
        )
        
        if insertion_point is None:
            # Insert at end
            content += f"\n\n{figure_block}\n"
        else:
            # Insert at found position
            content = (
                content[:insertion_point] +
                f"\n\n{figure_block}\n\n" +
                content[insertion_point:]
            )
        
        # Write back
        markdown_file.write_text(content, encoding='utf-8')
        
        return True
    
    def _find_insertion_point(
        self,
        content: str,
        section: Optional[str],
        position: str
    ) -> Optional[int]:
        """Find insertion point in markdown content.
        
        Args:
            content: Markdown content
            section: Section name
            position: Position strategy
            
        Returns:
            Insertion point index or None
        """
        if position == "end":
            return len(content)
        
        if section:
            # Find section header
            section_pattern = rf"^#+\s+{re.escape(section)}\s*$"
            matches = list(re.finditer(section_pattern, content, re.MULTILINE))
            
            if matches:
                match = matches[0]
                if position == "after_section":
                    # Find end of section (next section or end of file)
                    next_section = re.search(
                        r"^#+\s+", content[match.end():], re.MULTILINE
                    )
                    if next_section:
                        return match.end() + next_section.start()
                    else:
                        return len(content)
                elif position == "before_section":
                    return match.start()
        
        return None
    
    def insert_reference(
        self,
        markdown_file: Path,
        figure_label: str,
        text: Optional[str] = None,
        position: Optional[int] = None
    ) -> bool:
        """Insert figure reference in markdown text.
        
        Args:
            markdown_file: Path to markdown file
            figure_label: Figure label to reference
            text: Text to insert reference in (if None, finds suitable location)
            position: Character position to insert (if None, auto-finds)
            
        Returns:
            True if insertion successful
        """
        fig_meta = self.figure_manager.get_figure(figure_label)
        if fig_meta is None:
            return False
        
        if not markdown_file.exists():
            return False
        
        content = markdown_file.read_text(encoding='utf-8')
        
        # Check if reference already exists
        if f"\\ref{{{figure_label}}}" in content:
            return True  # Already referenced
        
        # Generate reference
        ref_text = f"Figure \\ref{{{figure_label}}}"
        if text:
            ref_text = f"{text} (see {ref_text})"
        
        # Find insertion point
        if position is None:
            # Find first paragraph after figure
            figure_pos = content.find(f"\\label{{{figure_label}}}")
            if figure_pos != -1:
                # Find next paragraph
                next_para = re.search(r"\n\n", content[figure_pos:])
                if next_para:
                    position = figure_pos + next_para.end()
                else:
                    position = len(content)
            else:
                # Insert at end
                position = len(content)
        
        # Insert reference
        content = content[:position] + f" {ref_text}." + content[position:]
        
        # Write back
        markdown_file.write_text(content, encoding='utf-8')
        
        return True
    
    def validate_figures(self, markdown_file: Path) -> List[Tuple[str, str]]:
        """Validate figures referenced in markdown file.
        
        Args:
            markdown_file: Path to markdown file
            
        Returns:
            List of (figure_label, error_message) tuples
        """
        if not markdown_file.exists():
            return [("", "Markdown file does not exist")]
        
        content = markdown_file.read_text(encoding='utf-8')
        errors = []
        
        # Find all figure references
        figure_pattern = r"\\includegraphics.*?\{([^}]+)\}"
        matches = re.finditer(figure_pattern, content)
        
        for match in matches:
            figure_path = match.group(1)
            
            # Check if path exists
            if figure_path.startswith("../"):
                # Relative path from manuscript/
                full_path = markdown_file.parent / figure_path
            else:
                full_path = Path(figure_path)
            
            if not full_path.exists():
                errors.append((figure_path, f"Figure file not found: {figure_path}"))
        
        # Find all figure labels
        label_pattern = r"\\label\{(fig:[^}]+)\}"
        label_matches = re.finditer(label_pattern, content)
        
        for match in label_matches:
            label = match.group(1)
            
            # Check if label is registered
            if self.figure_manager.get_figure(label) is None:
                errors.append((label, f"Figure label not registered: {label}"))
        
        return errors
    
    def get_figure_list(self, markdown_file: Path) -> List[str]:
        """Get list of figures referenced in markdown file.
        
        Args:
            markdown_file: Path to markdown file
            
        Returns:
            List of figure labels
        """
        if not markdown_file.exists():
            return []
        
        content = markdown_file.read_text(encoding='utf-8')
        
        # Find all figure labels
        label_pattern = r"\\label\{(fig:[^}]+)\}"
        labels = re.findall(label_pattern, content)
        
        return list(set(labels))  # Remove duplicates

