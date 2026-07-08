from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

_IMAGE_LABEL_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+\.png)\)\{#(fig:[-A-Za-z0-9_.:]+)(?:\s[^}]*)?\}")
_SKIPPED_DOCS = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})


@dataclass(frozen=True)
class FigureRegistryEntry:
    """Data container for FigureRegistryEntry."""

    label: str
    filename: str
    caption: str
    source_markdown: str
    generated_by: str


def collect_figure_registry_entries(manuscript_dir: Path, figures_dir: Path) -> tuple[FigureRegistryEntry, ...]:
    """Collect figure registry entries from a directory."""
    entries: dict[str, FigureRegistryEntry] = {}
    figures_root = figures_dir.resolve()
    for markdown_file in sorted(manuscript_dir.rglob("*.md")):
        if markdown_file.name in _SKIPPED_DOCS:
            continue
        text = markdown_file.read_text(encoding="utf-8")
        for caption, image_path, label in _IMAGE_LABEL_RE.findall(text):
            resolved = (markdown_file.parent / image_path).resolve()
            filename = _figure_filename(image_path, resolved, figures_root)
            entries.setdefault(
                label,
                FigureRegistryEntry(
                    label=label,
                    filename=filename,
                    caption=caption,
                    source_markdown=markdown_file.relative_to(manuscript_dir).as_posix(),
                    generated_by="scripts/generate_figures.py",
                ),
            )
    return tuple(entries[label] for label in sorted(entries))


def _figure_filename(image_path: str, resolved: Path, figures_root: Path) -> str:
    try:
        return resolved.relative_to(figures_root).as_posix()
    except ValueError:
        parts = Path(image_path).parts
        for index in range(len(parts) - 1):
            if parts[index : index + 2] == ("output", "figures"):
                return Path(*parts[index + 2 :]).as_posix()
        return Path(image_path).name


def write_figure_registry(manuscript_dir: Path, figures_dir: Path) -> Path:
    """Write the figure registry to a JSON file."""
    figures_dir.mkdir(parents=True, exist_ok=True)
    path = figures_dir / "figure_registry.json"
    payload = {
        "schema_version": "template-textbook-figure-registry-v1",
        "figures": [asdict(entry) for entry in collect_figure_registry_entries(manuscript_dir, figures_dir)],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


__all__ = ["FigureRegistryEntry", "collect_figure_registry_entries", "write_figure_registry"]
