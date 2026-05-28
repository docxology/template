"""Sheaf manifest loading."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml

from .models import (
    DEFAULT_MANIFEST_REL,
    DEFAULT_REGISTRY_REL,
    ImradBlock,
    MissingTrackPolicy,
    SectionKind,
    SheafDefaults,
    SheafManifest,
    SheafSection,
)


def parse_missing(value: str | None, fallback: MissingTrackPolicy) -> MissingTrackPolicy:
    if value is None:
        return fallback
    try:
        return MissingTrackPolicy(str(value).strip().lower())
    except ValueError:
        return fallback


def load_manifest(
    manifest_path: Path,
    *,
    registry_path: Path | None = None,
    project_root: Path | None = None,
) -> SheafManifest:
    manifest_path = manifest_path.resolve()
    if project_root is not None:
        root = project_root.resolve()
    elif manifest_path.parent.name == "sheaf" and manifest_path.parent.parent.name == "manuscript":
        root = manifest_path.parent.parent.parent
    else:
        root = manifest_path.parent
    registry = registry_path or (root / DEFAULT_REGISTRY_REL)
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    defaults_raw = raw.get("defaults") or {}
    manifest_defaults = SheafDefaults(
        missing_track=parse_missing(defaults_raw.get("missing_track"), MissingTrackPolicy.SKIP),
    )
    sections: list[SheafSection] = []
    for entry in raw.get("sections") or []:
        tracks = {str(k): str(v) for k, v in dict(entry.get("tracks") or {}).items()}
        include = entry.get("include_tracks")
        exclude = entry.get("exclude_tracks")
        order_override = entry.get("track_order")
        kind_raw = str(entry.get("kind", "section")).strip().lower()
        kind: SectionKind = "group" if kind_raw == "group" else "section"
        imrad_raw = str(entry.get("imrad", "methods")).strip().lower()
        imrad: ImradBlock = (
            cast(ImradBlock, imrad_raw)
            if imrad_raw
            in {
                "introduction",
                "methods",
                "results",
                "discussion",
                "appendix",
            }
            else "methods"
        )
        depth = int(entry.get("depth", 0 if kind == "group" else 1))
        compose_raw = entry.get("compose")
        if compose_raw is None:
            compose = kind == "section"
        else:
            compose = bool(compose_raw)
        sections.append(
            SheafSection(
                id=str(entry["id"]),
                title=str(entry["title"]),
                short=str(entry.get("short", entry["id"])),
                order=int(entry["order"]),
                tracks=tracks,
                output_name=str(entry.get("output_name", f"{entry['order']:02d}_{entry['id']}.md")),
                kind=kind,
                imrad=imrad,
                depth=depth,
                compose=compose,
                track_order=tuple(str(t) for t in order_override) if order_override else None,
                include_tracks=tuple(str(t) for t in include) if include else None,
                exclude_tracks=tuple(str(t) for t in exclude) if exclude else None,
            )
        )
    return SheafManifest(
        defaults=manifest_defaults,
        sections=tuple(sorted(sections, key=lambda s: s.order)),
        registry_path=registry,
    )


def default_manifest_path(project_root: Path) -> Path:
    return project_root.resolve() / DEFAULT_MANIFEST_REL
