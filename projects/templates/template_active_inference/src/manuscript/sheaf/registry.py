"""Track registry loading and section ordering."""

from __future__ import annotations

from pathlib import Path

import yaml

from manuscript.sheaf.models import TrackRegistry, TrackSpec


def load_track_registry(registry_path: Path) -> TrackRegistry:
    """Load track registry from a file."""
    raw = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    tracks_raw = raw.get("tracks") or {}
    specs: dict[str, TrackSpec] = {}
    for track_id, meta in tracks_raw.items():
        entry = meta or {}
        renderer = str(entry.get("renderer", "markdown"))
        specs[str(track_id)] = TrackSpec(
            id=str(track_id),
            order=int(entry.get("order", 999)),
            renderer=renderer,
            label=str(entry.get("label", track_id)),
            optional=bool(entry.get("optional", False)),
            paper_role=str(entry.get("paper_role", "")),
            paper_use=str(entry.get("paper_use", "")),
        )
    renderers_raw = raw.get("renderers") or {}
    suffixes: dict[str, tuple[str, ...]] = {}
    for name, meta in renderers_raw.items():
        entry = meta or {}
        suffixes[str(name)] = tuple(str(s) for s in entry.get("suffixes") or ())
    return TrackRegistry(tracks=specs, renderer_suffixes=suffixes)


def track_order_for_section(
    section,
    registry: TrackRegistry | dict[str, TrackSpec],
) -> list[str]:
    """Process track order for section."""
    specs = registry.tracks if isinstance(registry, TrackRegistry) else registry
    if section.track_order:
        return list(section.track_order)
    bound = set(section.tracks)
    if section.include_tracks:
        bound &= set(section.include_tracks)
    if section.exclude_tracks:
        bound -= set(section.exclude_tracks)
    return sorted(
        bound,
        key=lambda tid: specs.get(tid, TrackSpec(tid, 999, "markdown", tid)).order,
    )


def list_registered_tracks(project_root: Path) -> list[TrackSpec]:
    """Process list registered tracks."""
    from manuscript.sheaf.models import DEFAULT_REGISTRY_REL

    registry_path = project_root / DEFAULT_REGISTRY_REL
    return sorted(load_track_registry(registry_path).tracks.values(), key=lambda t: t.order)
