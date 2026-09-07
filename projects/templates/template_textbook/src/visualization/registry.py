from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

_IMAGE_LABEL_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+\.png)\)\{#(fig:[-A-Za-z0-9_.:]+)(?:\s[^}]*)?\}")
_SKIPPED_DOCS = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})

FIGURE_ALT_TEXT: dict[str, str] = {
    "fig:gallery_bar": (
        "A vertical bar chart compares several labeled categories, with bar height encoding each category's value."
    ),
    "fig:gallery_errorbar": (
        "Six condition means rise from left to right; every point has a vertical standard-error interval."
    ),
    "fig:gallery_line": (
        "Three sinusoidal curves share one time axis, with progressively higher oscillation frequency."
    ),
    "fig:gallery_media": (
        "A rectangular heatmap uses a light-to-dark color scale to encode values across rows and columns."
    ),
    "fig:gallery_multipanel": ("A two-by-two composite contains a line chart, scatter plot, bar chart, and histogram."),
    "fig:gallery_pie": ("A circular chart is divided into labeled slices whose angles encode category proportions."),
    "fig:part_0_orientation": (
        "A bordered placeholder overview panel labeled Orientation to the Field, awaiting a subject-specific illustration."
    ),
    "fig:part_0_core_methods": (
        "A bordered placeholder overview panel labeled Core Methods and Tools, awaiting a subject-specific illustration."
    ),
    "fig:part_0_quantitative_foundations": (
        "A bordered placeholder overview panel labeled Quantitative Foundations, awaiting a subject-specific illustration."
    ),
    "fig:part_I_first_principles": (
        "Three S-shaped logistic-growth curves approach the horizontal carrying-capacity line at 100; higher growth rates rise sooner."
    ),
    "fig:part_I_building_blocks": (
        "A bordered placeholder overview panel labeled Building Blocks, awaiting a subject-specific illustration."
    ),
    "fig:part_I_structure_and_form": (
        "A bordered placeholder overview panel labeled Structure and Form, awaiting a subject-specific illustration."
    ),
    "fig:part_II_systems_overview": (
        "A bordered placeholder overview panel labeled Systems Overview, awaiting a subject-specific illustration."
    ),
    "fig:part_II_dynamics_and_change": (
        "A bordered placeholder overview panel labeled Dynamics and Change, awaiting a subject-specific illustration."
    ),
    "fig:part_II_regulation_and_control": (
        "A bordered placeholder overview panel labeled Regulation and Control, awaiting a subject-specific illustration."
    ),
    "fig:part_III_applied_models": (
        "A bordered placeholder overview panel labeled Applied Models, awaiting a subject-specific illustration."
    ),
    "fig:part_III_case_studies": (
        "Six pilot measurements increase across control, low-treatment, and high-treatment conditions; each point has a vertical standard-error interval."
    ),
    "fig:part_III_frontiers": (
        "A bordered placeholder overview panel labeled Frontiers and Open Problems, awaiting a subject-specific illustration."
    ),
}


@dataclass(frozen=True)
class FigureRegistryEntry:
    """One figure cross-referenced from manuscript prose to its generated file.

    Captures the label used in `{#fig:...}` markdown attributes, the figure's
    filename relative to `output/figures/`, its caption text, the manuscript
    file that references it, and the script responsible for generating it —
    the row shape written into `figure_registry.json`.
    """

    label: str
    filename: str
    caption: str
    alt: str
    source_markdown: str
    generated_by: str


def collect_figure_registry_entries(manuscript_dir: Path, figures_dir: Path) -> tuple[FigureRegistryEntry, ...]:
    """Collect figure registry entries from a directory."""
    entries: dict[str, FigureRegistryEntry] = {}
    filename_owners: dict[str, str] = {}
    figures_root = figures_dir.resolve()
    for markdown_file in sorted(manuscript_dir.rglob("*.md")):
        if markdown_file.name in _SKIPPED_DOCS:
            continue
        text = markdown_file.read_text(encoding="utf-8")
        for caption, image_path, label in _IMAGE_LABEL_RE.findall(text):
            resolved = (markdown_file.parent / image_path).resolve()
            filename = _figure_filename(image_path, resolved, figures_root)
            existing_owner = filename_owners.get(filename)
            if existing_owner is not None and existing_owner != label:
                raise ValueError(
                    f"Figure filename {filename!r} is claimed by multiple labels: {existing_owner}, {label}"
                )
            filename_owners[filename] = label
            try:
                alt = FIGURE_ALT_TEXT[label]
            except KeyError as exc:
                raise ValueError(f"Missing explicit alt-text specification for manuscript figure: {label}") from exc
            entries.setdefault(
                label,
                FigureRegistryEntry(
                    label=label,
                    filename=filename,
                    caption=caption,
                    alt=alt,
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


__all__ = [
    "FIGURE_ALT_TEXT",
    "FigureRegistryEntry",
    "collect_figure_registry_entries",
    "write_figure_registry",
]
