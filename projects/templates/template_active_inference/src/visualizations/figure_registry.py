"""Figure metadata registry (paths, captions, alt text)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from manuscript.hydrate import substitute_snake_case_tokens

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FigureSpec:
    figure_id: str
    filename: str
    alt: str
    caption: str
    width: float = 0.9


@dataclass(frozen=True)
class SectionFigureRef:
    figure_id: str
    number: int | None = None
    caption_prefix: str = ""
    labeled: bool = True


def _figures_yaml_path(project_root: Path) -> Path:
    return project_root.resolve() / "figures.yaml"


def _load_figures_yaml(project_root: Path) -> dict[str, Any]:
    path = _figures_yaml_path(project_root)
    if not path.is_file():
        raise FileNotFoundError(f"missing figure registry: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_figure_registry(project_root: Path) -> dict[str, FigureSpec]:
    raw = _load_figures_yaml(project_root)
    figures_raw = raw.get("figures") or {}
    registry: dict[str, FigureSpec] = {}
    for figure_id, entry in figures_raw.items():
        if not isinstance(entry, dict):
            logger.warning("figures.yaml entry %s is not a mapping; skipped", figure_id)
            continue
        fid = str(figure_id)
        registry[fid] = FigureSpec(
            figure_id=fid,
            filename=str(entry.get("filename", f"{fid}.png")),
            alt=str(entry.get("alt", fid)),
            caption=str(entry.get("caption", "")),
            width=float(entry.get("width", 0.9)),
        )
    if not registry:
        raise ValueError("figures.yaml must declare at least one figure entry")
    return registry


def load_section_figures(project_root: Path) -> dict[str, tuple[SectionFigureRef, ...]]:
    raw = _load_figures_yaml(project_root)
    section_raw = raw.get("section_figures") or {}
    mapping: dict[str, tuple[SectionFigureRef, ...]] = {}
    for section_id, entries in section_raw.items():
        refs: list[SectionFigureRef] = []
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, str):
                refs.append(SectionFigureRef(figure_id=entry))
            elif isinstance(entry, dict):
                refs.append(
                    SectionFigureRef(
                        figure_id=str(entry["id"]),
                        number=int(entry["number"]) if entry.get("number") is not None else None,
                        caption_prefix=str(entry.get("caption_prefix", "")),
                        labeled=bool(entry.get("labeled", True)),
                    )
                )
        mapping[str(section_id)] = tuple(refs)
    return mapping


def figure_output_path(project_root: Path, figure_id: str) -> Path:
    spec = load_figure_registry(project_root)[figure_id]
    return project_root.resolve() / "output" / "figures" / spec.filename


def render_figure_markdown(
    project_root: Path,
    figure_id: str,
    *,
    figure_number: int | None = None,
    caption_prefix: str = "",
    variables: dict[str, str] | None = None,
    labeled: bool = True,
) -> str:
    # `figure_number` / `caption_prefix` are retained for signature back-compat but are
    # intentionally unused: pandoc-crossref owns figure numbering (single source of truth).
    # Hand-written "Figure N (section)." prefixes previously double-numbered every figure
    # against pandoc's auto-caption — see manuscript/SYNTAX.md and src/visualizations/AGENTS.md.
    del figure_number, caption_prefix
    spec = load_figure_registry(project_root)[figure_id]
    rel = f"../output/figures/{spec.filename}"
    alt = spec.alt
    caption = spec.caption
    if variables:
        alt, unresolved_alt = substitute_snake_case_tokens(alt, variables)
        caption, unresolved_cap = substitute_snake_case_tokens(caption, variables)
        unresolved = sorted(set(unresolved_alt + unresolved_cap))
        if unresolved:
            raise ValueError(f"unresolved figure tokens for {figure_id}: {', '.join(unresolved)}")
    width_pct = int(round(spec.width * 100))
    if labeled:
        # The caption is the image alt text, so pandoc-crossref emits exactly one
        # numbered "Figure N: {caption}". The verbose description rides along as fig-alt
        # for accessibility without producing a second caption.
        fig_alt = alt.replace('"', "'")
        return f'![{caption}]({rel}){{#fig:{figure_id} width={width_pct}% fig-alt="{fig_alt}"}}'
    # Reused figure: empty alt → unnumbered graphic (no second "Figure N"); cite the
    # canonical labeled occurrence so the reader is pointed at the authoritative number.
    return f"![]({rel}){{width={width_pct}%}}\n\n*Reproduced from [@fig:{figure_id}]. {caption}*"


def render_section_figures(
    project_root: Path,
    section_id: str,
    *,
    variables: dict[str, str] | None = None,
) -> str:
    refs = load_section_figures(project_root).get(section_id, ())
    if not refs:
        return ""
    blocks = [
        render_figure_markdown(
            project_root,
            ref.figure_id,
            figure_number=ref.number,
            caption_prefix=ref.caption_prefix,
            variables=variables,
            labeled=ref.labeled,
        )
        for ref in refs
    ]
    return "\n\n".join(blocks)


def build_figure_registry_payload(project_root: Path) -> dict[str, dict[str, object]]:
    """Build validator-facing registry JSON keyed by ``fig:{id}`` labels."""
    registry = load_figure_registry(project_root)
    payload: dict[str, dict[str, object]] = {}
    for figure_id, spec in registry.items():
        label = f"fig:{figure_id}"
        payload[label] = {
            "label": label,
            "figure_id": figure_id,
            "filename": spec.filename,
            "alt": spec.alt,
            "caption": spec.caption,
            "width": spec.width,
            "generated_by": f"visualizations.figures::{figure_id}",
        }
    return payload


def write_figure_registry_json(project_root: Path) -> Path:
    """Write ``output/figures/figure_registry.json`` from ``figures.yaml``."""
    root = project_root.resolve()
    out = root / "output" / "figures" / "figure_registry.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(build_figure_registry_payload(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out
