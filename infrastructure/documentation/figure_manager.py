"""Figure management for scientific computing.

This module stores figure metadata, assigns registry identifiers, and persists
caption, source, and project-specific fields. Manuscript figure numbering and
cross-references are owned by Pandoc and pandoc-crossref.
"""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


@dataclass
class FigureMetadata:
    """Metadata for a figure."""

    figure_id: str
    filename: str
    caption: str
    label: str
    section: str | None = None
    width: str = "0.8\\textwidth"
    placement: str = "h"
    generated_by: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FigureMetadata:
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
    """Register, retrieve, and persist figure metadata by label."""

    def __init__(self, registry_file: str | None = None):
        """Initialize figure manager.

        Args:
            registry_file: Path to figure registry file
        """
        if registry_file is None:
            registry_file = "output/figures/figure_registry.json"

        self.registry_file = Path(registry_file)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.figures: dict[str, FigureMetadata] = {}
        self.counter = 0
        self._load_registry()

    def _load_registry(self) -> None:
        """Load figure registry from file.

        If the registry is corrupted, backs up the corrupted file and starts fresh.
        """
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.figures = {fig_id: FigureMetadata.from_dict(fig_data) for fig_id, fig_data in data.items()}
                    # Update counter from max numeric suffix; default=0 guards against
                    # non-standard IDs that lack a numeric suffix
                    if self.figures:
                        self.counter = (
                            max(
                                (
                                    int(fig.figure_id.split("_")[-1])
                                    for fig in self.figures.values()
                                    if "_" in fig.figure_id and fig.figure_id.split("_")[-1].isdigit()
                                ),
                                default=0,
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
            except (ValueError, KeyError, TypeError, OSError) as e:
                # Other errors (e.g., malformed data structure)
                logger.warning(f"Figure registry corrupted (unexpected error): {e}")
                self._backup_corrupted_registry()
                self.figures = {}
                self.counter = 0

    def _backup_corrupted_registry(self) -> None:
        """Backup a corrupted registry file before resetting."""
        if self.registry_file.exists():
            # Generate unique backup filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = self.registry_file.with_suffix(f".json.corrupted.{timestamp}")
            try:
                shutil.copy2(self.registry_file, backup_path)
                logger.info(f"Corrupted registry backed up to: {backup_path}")
            except (OSError, shutil.Error) as backup_error:
                logger.error(f"Failed to backup corrupted registry: {backup_error}")

    def _save_registry(self) -> None:
        """Save figure registry to file (atomic write to prevent corruption)."""
        data = {fig_id: fig.to_dict() for fig_id, fig in self.figures.items()}
        tmp = self.registry_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        tmp.replace(self.registry_file)

    def register_figure(
        self,
        filename: str,
        caption: str,
        label: str | None = None,
        section: str | None = None,
        width: str = "0.8\\textwidth",
        placement: str = "h",
        generated_by: str | None = None,
        metadata: dict[str, Any] | None = None,
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
        if label is None:
            base_name = Path(filename).stem
            label = f"fig:{base_name}"

        figure_id = f"figure_{self.counter:03d}"
        self.counter += 1

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

        self.figures[label] = fig_meta
        self._save_registry()

        return fig_meta

    def get_figure(self, label: str) -> FigureMetadata | None:
        """Get figure metadata by label."""
        return self.figures.get(label)

    def get_all_figures(self) -> list[FigureMetadata]:
        """Get all registered figures."""
        return list(self.figures.values())

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
