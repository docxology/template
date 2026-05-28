"""Track fragment renderers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .models import ManifestIssue, SheafSection, TrackRegistry, TrackSpec

Renderer = Callable[[Path], str]
GeneratedResolver = Callable[
    [SheafSection, str, Path, Path, TrackRegistry, TrackSpec],
    str,
]
GENERATED_RENDERERS = frozenset({"section_figures", "layers_report"})


def _render_ontology(path: Path) -> str:
    from ontology.bindings import load_section_ontology

    entries = load_section_ontology(path)
    lines = ["### Ontology bindings", ""]
    for symbol, term in sorted(entries.items()):
        lines.append(f"- `{symbol}` → **{term}**")
    lines.append("")
    return "\n".join(lines)


RENDERERS: dict[str, Renderer] = {
    "markdown": lambda path: path.read_text(encoding="utf-8").strip(),
    "ontology_yaml": _render_ontology,
}


def _require_track_spec(registry: TrackRegistry, track_id: str) -> TrackSpec:
    spec = registry.tracks.get(track_id)
    if spec is None:
        raise KeyError(f"unknown sheaf track `{track_id}` — not in registry")
    return spec


def render_track_body(track: TrackSpec, path: Path) -> str:
    if track.renderer in GENERATED_RENDERERS:
        raise ValueError(f"Renderer `{track.renderer}` for track `{track.id}` requires resolve_track_body()")
    if track.renderer not in RENDERERS:
        raise ValueError(f"Unknown renderer `{track.renderer}` for track `{track.id}`")
    return RENDERERS[track.renderer](path)


def _resolve_section_figures(
    section: SheafSection,
    track_id: str,
    track_path: Path,
    project_root: Path,
    registry: TrackRegistry,
    spec: TrackSpec,
) -> str:
    from visualizations.figure_registry import render_section_figures

    body: str = render_section_figures(project_root, section.id)
    if body:
        return body
    return render_track_body(
        TrackSpec(track_id, spec.order, "markdown", spec.label, spec.optional),
        track_path,
    )


def _resolve_layers_report(
    section: SheafSection,
    track_id: str,
    track_path: Path,
    project_root: Path,
    registry: TrackRegistry,
    spec: TrackSpec,
) -> str:
    del section, track_id, track_path, registry, spec
    from .layers_report import render_sheaf_layers_markdown

    return render_sheaf_layers_markdown(project_root)


_GENERATED_RESOLVERS: dict[str, GeneratedResolver] = {
    "section_figures": _resolve_section_figures,
    "layers_report": _resolve_layers_report,
}


def resolve_track_body(
    section: SheafSection,
    track_id: str,
    track_path: Path,
    project_root: Path,
    registry: TrackRegistry,
) -> str:
    """Resolve composed markdown for one bound track."""
    spec = _require_track_spec(registry, track_id)
    generated = _GENERATED_RESOLVERS.get(spec.renderer)
    if generated is not None:
        return generated(section, track_id, track_path, project_root, registry, spec)
    return render_track_body(spec, track_path)


def validate_renderer_specs(registry: TrackRegistry, issues: list[ManifestIssue]) -> None:
    known = set(RENDERERS) | GENERATED_RENDERERS
    for track in registry.tracks.values():
        if track.renderer not in known:
            issues.append(
                ManifestIssue(
                    "error",
                    "unknown_renderer",
                    f"track `{track.id}` uses unregistered renderer `{track.renderer}`",
                )
            )
    for renderer_name in registry.renderer_suffixes:
        if renderer_name not in RENDERERS:
            issues.append(
                ManifestIssue(
                    "error",
                    "unknown_renderer_metadata",
                    f"renderers block declares `{renderer_name}` but no Python renderer exists",
                )
            )
