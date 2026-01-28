"""Figure management for scientific computing.

This module provides automatic figure numbering, caption generation,
cross-reference management, figure registry, and LaTeX integration.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class FigureMetadata:
    """Metadata for a figure."""

    figure_id: str
    filename: str
    caption: str
    label: str
    section: Optional[str] = None
    width: str = "0.8\\textwidth"
    placement: str = "h"
    generated_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FigureMetadata:
        """Create FigureMetadata from dictionary.

        Handles flexible field mapping between different registry formats.
        """
        data = dict(data)  # Copy to avoid mutation

        # Map 'parameters' to 'metadata' field
        if "parameters" in data:
            if "metadata" not in data:
                data["metadata"] = data.pop("parameters") or {}
            else:
                data.pop("parameters")

        # Generate figure_id from label if not present
        if "figure_id" not in data:
            label = data.get("label", "unknown")
            data["figure_id"] = label.replace("fig:", "figure_")

        # Filter to valid fields only
        valid_fields = {
            "figure_id",
            "filename",
            "caption",
            "label",
            "section",
            "width",
            "placement",
            "generated_by",
            "metadata",
        }
        data = {k: v for k, v in data.items() if k in valid_fields}

        # Ensure metadata is a dict
        if data.get("metadata") is None:
            data["metadata"] = {}

        return cls(**data)


class FigureManager:
    """Manages figures with automatic numbering and cross-referencing."""

    def __init__(self, registry_file: Optional[str] = None):
        """Initialize figure manager.

        Args:
            registry_file: Path to figure registry file
        """
        if registry_file is None:
            registry_file = "output/figures/figure_registry.json"

        self.registry_file = Path(registry_file)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.figures: Dict[str, FigureMetadata] = {}
        self.counter = 0

        # Load existing registry
        self._load_registry()

    def _load_registry(self) -> None:
        """Load figure registry from file.

        If the registry is corrupted, backs up the corrupted file and starts fresh.
        """
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r") as f:
                    data = json.load(f)
                    self.figures = {
                        fig_id: FigureMetadata.from_dict(fig_data)
                        for fig_id, fig_data in data.items()
                    }
                    # Update counter
                    if self.figures:
                        self.counter = (
                            max(
                                int(fig.figure_id.split("_")[-1])
                                for fig in self.figures.values()
                                if "_" in fig.figure_id
                                and fig.figure_id.split("_")[-1].isdigit()
                            )
                            + 1
                        )
                    logger.debug(f"Loaded {len(self.figures)} figures from registry")
            except json.JSONDecodeError as e:
                # Registry file is corrupted - backup and start fresh
                logger.warning(f"Figure registry corrupted (JSON decode error): {e}")
                self._backup_corrupted_registry()
                self.figures = {}
                self.counter = 0
            except Exception as e:
                # Other errors (e.g., malformed data structure)
                logger.warning(f"Figure registry corrupted (unexpected error): {e}")
                self._backup_corrupted_registry()
                self.figures = {}
                self.counter = 0

    def _backup_corrupted_registry(self) -> None:
        """Backup a corrupted registry file before resetting."""
        if self.registry_file.exists():
            # Generate unique backup filename with timestamp
            import time

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = self.registry_file.with_suffix(f".json.corrupted.{timestamp}")
            try:
                shutil.copy2(self.registry_file, backup_path)
                logger.info(f"Corrupted registry backed up to: {backup_path}")
            except Exception as backup_error:
                logger.error(f"Failed to backup corrupted registry: {backup_error}")

    def _save_registry(self) -> None:
        """Save figure registry to file."""
        data = {fig_id: fig.to_dict() for fig_id, fig in self.figures.items()}
        with open(self.registry_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def register_figure(
        self,
        filename: str,
        caption: str,
        label: Optional[str] = None,
        section: Optional[str] = None,
        width: str = "0.8\\textwidth",
        placement: str = "h",
        generated_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FigureMetadata:
        """Register a new figure.

        Args:
            filename: Figure filename
            caption: Figure caption
            label: Figure label (auto-generated if None)
            section: Section name
            width: Figure width in LaTeX
            placement: LaTeX placement (h, t, b, p, H)
            generated_by: Script that generated the figure
            metadata: Additional metadata

        Returns:
            FigureMetadata object
        """
        # Generate label if not provided
        if label is None:
            base_name = Path(filename).stem
            # Clean label (remove special chars, use underscores)
            label = f"fig:{base_name}"

        # Generate figure ID
        figure_id = f"figure_{self.counter:03d}"
        self.counter += 1

        # Create metadata
        fig_meta = FigureMetadata(
            figure_id=figure_id,
            filename=filename,
            caption=caption,
            label=label,
            section=section,
            width=width,
            placement=placement,
            generated_by=generated_by,
            metadata=metadata or {},
        )

        # Register
        self.figures[label] = fig_meta

        # Save registry
        self._save_registry()

        return fig_meta

    def get_figure(self, label: str) -> Optional[FigureMetadata]:
        """Get figure metadata by label.

        Args:
            label: Figure label

        Returns:
            FigureMetadata or None
        """
        return self.figures.get(label)

    def get_all_figures(self) -> List[FigureMetadata]:
        """Get all registered figures.

        Returns:
            List of FigureMetadata objects
        """
        return list(self.figures.values())

    def generate_latex_figure_block(self, label: str) -> str:
        """Generate LaTeX figure block.

        Args:
            label: Figure label

        Returns:
            LaTeX code for figure block
        """
        fig_meta = self.get_figure(label)
        if fig_meta is None:
            return f"% Figure {label} not found in registry"

        # Determine relative path (assuming figures are in output/figures/)
        figure_path = f"../output/figures/{fig_meta.filename}"

        latex = f"""\\begin{{figure}}[{fig_meta.placement}]
\\centering
\\includegraphics[width={fig_meta.width}]{{{figure_path}}}
\\caption{{{fig_meta.caption}}}
\\label{{{fig_meta.label}}}
\\end{{figure}}"""

        return latex

    def generate_reference(self, label: str) -> str:
        """Generate LaTeX reference to figure.

        Args:
            label: Figure label

        Returns:
            LaTeX reference code
        """
        return f"\\ref{{{label}}}"

    def generate_figure_list(self) -> str:
        """Generate list of all figures.

        Returns:
            Markdown list of figures
        """
        lines = ["## Figure List", ""]

        for fig_meta in sorted(self.figures.values(), key=lambda f: f.figure_id):
            lines.append(f"- **{fig_meta.label}**: {fig_meta.caption}")
            if fig_meta.section:
                lines.append(f"  - Section: {fig_meta.section}")
            lines.append(f"  - File: `{fig_meta.filename}`")
            lines.append("")

        return "\n".join(lines)

    def generate_table_of_figures(self) -> str:
        """Generate LaTeX table of figures.

        Returns:
            LaTeX code for table of figures
        """
        lines = ["\\listoffigures", "", "% Individual figures:", ""]

        for fig_meta in sorted(self.figures.values(), key=lambda f: f.figure_id):
            lines.append(self.generate_latex_figure_block(fig_meta.label))
            lines.append("")

        return "\n".join(lines)
