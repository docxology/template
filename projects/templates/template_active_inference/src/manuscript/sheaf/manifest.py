"""Sheaf manifest loading."""

from __future__ import annotations

from pathlib import Path, PureWindowsPath
from typing import cast

from yaml_io import load_yaml
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
    """Parse missing."""
    if value is None:
        return fallback
    try:
        return MissingTrackPolicy(str(value).strip().lower())
    except ValueError:
        return fallback


def validate_relative_path(
    value: str | Path,
    *,
    field: str,
    basename_only: bool = False,
) -> Path:
    """Return a portable relative path or fail closed on ambiguous input."""
    raw = str(value)
    path = Path(raw)
    windows_path = PureWindowsPath(raw)
    if (
        not raw
        or raw in {".", ".."}
        or path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or "\\" in raw
        or ".." in path.parts
        or ".." in windows_path.parts
    ):
        raise ValueError(f"{field} must be a portable project-relative path: {raw!r}")
    if basename_only and (len(path.parts) != 1 or path.name != raw):
        raise ValueError(f"{field} must be a basename, not a path: {raw!r}")
    return path


def resolve_project_relative_path(
    project_root: Path,
    value: str | Path,
    *,
    field: str,
    basename_only: bool = False,
) -> Path:
    """Resolve a declared path beneath ``project_root`` without following links."""
    root = project_root.resolve()
    rel = validate_relative_path(value, field=field, basename_only=basename_only)
    candidate = root
    for part in rel.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError(f"{field} must not contain symlink components: {value!s}")
    resolved = candidate.resolve(strict=False)
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"{field} escapes the project root: {value!s}")
    return candidate


def reject_symlink_components(path: Path, *, field: str) -> None:
    """Reject any existing symlink component in an arbitrary output path."""
    absolute = path.absolute()
    candidate = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError(f"{field} must not contain symlink components: {path}")


def load_manifest(
    manifest_path: Path,
    *,
    registry_path: Path | None = None,
    project_root: Path | None = None,
) -> SheafManifest:
    """Load manifest from a file."""
    manifest_path = manifest_path.resolve()
    if project_root is not None:
        root = project_root.resolve()
    elif manifest_path.parent.name == "sheaf" and manifest_path.parent.parent.name == "manuscript":
        root = manifest_path.parent.parent.parent
    else:
        root = manifest_path.parent
    registry = (
        validate_relative_path(registry_path, field="manifest registry_path")
        if registry_path is not None
        else DEFAULT_REGISTRY_REL
    )
    resolve_project_relative_path(root, registry, field="manifest registry_path")
    raw = load_yaml(manifest_path)
    defaults_raw = raw.get("defaults") or {}
    manifest_defaults = SheafDefaults(
        missing_track=parse_missing(defaults_raw.get("missing_track"), MissingTrackPolicy.SKIP),
    )
    sections: list[SheafSection] = []
    for entry in raw.get("sections") or []:
        section_id = str(entry["id"])
        tracks: dict[str, str] = {}
        for key, value in dict(entry.get("tracks") or {}).items():
            track_id = str(key)
            rel = str(value)
            resolve_project_relative_path(
                root,
                rel,
                field=f"{section_id}/{track_id} track path",
            )
            tracks[track_id] = rel
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
        output_name = str(entry.get("output_name", f"{entry['order']:02d}_{entry['id']}.md"))
        validate_relative_path(
            output_name,
            field=f"{section_id} output_name",
            basename_only=True,
        )
        sections.append(
            SheafSection(
                id=section_id,
                title=str(entry["title"]),
                short=str(entry.get("short", entry["id"])),
                order=int(entry["order"]),
                tracks=tracks,
                output_name=output_name,
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
    """Process default manifest path."""
    return project_root.resolve() / DEFAULT_MANIFEST_REL
