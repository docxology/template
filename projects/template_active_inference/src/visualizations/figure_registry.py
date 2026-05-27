"""Figure metadata registry (paths, captions, alt text)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from manuscript.hydrate import substitute_snake_case_tokens


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
) -> str:
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
    number_prefix = ""
    if figure_number is not None and not caption_prefix.strip():
        number_prefix = f"Figure {figure_number}. "
    return f"![{alt}]({rel})\n\n*{caption_prefix}{number_prefix}{caption}*"


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
        )
        for ref in refs
    ]
    return "\n\n".join(blocks)
