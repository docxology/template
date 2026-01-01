"""Minimal figure management utilities for the Ento-Linguistic Research Project.

This module provides basic figure registration functionality.
"""
import json
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class FigureMetadata:
    """Metadata for a registered figure."""
    filename: str
    caption: str
    label: Optional[str] = None
    section: Optional[str] = None
    generated_by: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class FigureManager:
    """Minimal figure manager for registering figures."""

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
        self._load_registry()

    def register_figure(
        self,
        filename: str,
        caption: str,
        label: Optional[str] = None,
        section: Optional[str] = None,
        generated_by: Optional[str] = None,
        **kwargs
    ) -> FigureMetadata:
        """Register a figure.

        Args:
            filename: Figure filename
            caption: Figure caption
            label: Figure label (auto-generated if None)
            section: Section where figure appears
            generated_by: Script that generated the figure
            **kwargs: Additional parameters

        Returns:
            FigureMetadata object
        """
        # Generate label if not provided
        if label is None:
            base_name = Path(filename).stem
            label = f"fig:{base_name}"

        # Create metadata
        metadata = FigureMetadata(
            filename=filename,
            caption=caption,
            label=label,
            section=section,
            generated_by=generated_by,
            parameters=kwargs if kwargs else None
        )

        # Register
        self.figures[label] = metadata
        self._save_registry()

        return metadata

    def get_figure(self, label: str) -> Optional[FigureMetadata]:
        """Get figure metadata by label.

        Args:
            label: Figure label

        Returns:
            FigureMetadata if found, None otherwise
        """
        return self.figures.get(label)

    def _load_registry(self) -> None:
        """Load figure registry from file."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                    for label, fig_data in data.items():
                        self.figures[label] = FigureMetadata(**fig_data)
            except Exception:
                # Start fresh if registry is corrupted
                self.figures = {}

    def _save_registry(self) -> None:
        """Save figure registry to file."""
        data = {label: fig.to_dict() for label, fig in self.figures.items()}
        with open(self.registry_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)