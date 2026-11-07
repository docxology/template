"""Read-only admission of project-declared generated rendering inputs."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import yaml

from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.validation.content.manuscript_config import (
    GENERATED_ORDERING_MARKER,
    has_generated_manuscript_ordering,
    unresolved_config_tokens,
)
from infrastructure.validation.rendered_snapshot._scan import RenderedSnapshotError


def _enabled(entry: Mapping[str, object], key: str = "enabled", default: bool = True) -> bool:
    value = entry.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"generated manuscript {key} must be a boolean")
    return value


def _list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"generated manuscript {label} must be a list")
    return value


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"generated manuscript {label} must be a string-keyed mapping")
    return value


def _declared_files(
    entries: object,
    roots: tuple[Path, ...],
    *,
    skip_preface: bool = False,
) -> None:
    for entry in _list(entries, "files"):
        if isinstance(entry, dict):
            mapped = _mapping(entry, "file entry")
            if not _enabled(mapped):
                continue
            name = mapped.get("file")
        else:
            name = entry
        if not isinstance(name, str) or not name:
            raise ValueError("generated manuscript file entry must name a file")
        if skip_preface and name == "preface.md":
            continue
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != name:
            raise ValueError("generated manuscript file must use a canonical relative path")
        if not any((root / relative).is_file() for root in roots):
            raise ValueError(f"generated manuscript configured file is missing: {name}")


def _validate_ordering(loaded: Mapping[str, object], root: Path) -> None:
    """Reject declarations that discovery would otherwise silently omit/coerce."""
    if "front_matter" in loaded:
        front = _mapping(loaded["front_matter"], "front_matter")
        if _enabled(front, "include_front_matter"):
            _declared_files(
                front.get("files", []),
                (root,),
                skip_preface=not _enabled(front, "include_preface"),
            )
    for raw in _list(loaded.get("units", []), "units"):
        unit = _mapping(raw, "unit")
        if not _enabled(unit):
            continue
        directory = unit.get("directory") or unit.get("id")
        if not isinstance(directory, str) or not directory:
            raise ValueError("generated manuscript unit must name a directory or id")
        relative = Path(directory)
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != directory:
            raise ValueError("generated manuscript unit must use a canonical relative directory")
        _declared_files(unit.get("chapters", []), (root / relative,))
    if "appendices" not in loaded:
        return
    appendices = _mapping(loaded["appendices"], "appendices")
    for group in ("labs", "questions"):
        if not _enabled(appendices, f"include_{group}", False):
            continue
        for raw in _list(appendices.get(group, []), group):
            bundle = _mapping(raw, f"{group} bundle")
            if not _enabled(bundle):
                continue
            unit = bundle.get("unit")
            if not isinstance(unit, str) or not unit:
                raise ValueError(f"generated manuscript {group} bundle must name its unit")
            relative = Path(unit)
            if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != unit:
                raise ValueError("generated manuscript appendix unit must use a canonical relative directory")
            _declared_files(bundle.get("files", []), (root / group / relative,))
    if _enabled(appendices, "include_reference", False):
        _declared_files(appendices.get("reference", []), (root / "appendices", root))


def _require_marker_comment(text: str, marker: str) -> None:
    positions: set[int] = set()
    offset = 0
    for line in text.splitlines(keepends=True):
        if line.rstrip("\r\n") == marker:
            positions.add(offset)
        offset += len(line)
    # YAML token spans are half-open: a following comment is not scalar content.
    for token in yaml.scan(text):
        if isinstance(token, yaml.tokens.ScalarToken):
            positions = {
                position for position in positions if not token.start_mark.index <= position < token.end_mark.index
            }
    if not positions:
        raise ValueError("generated ordering must be declared by its standalone comment marker")


def declared_generated_manuscript_inputs(project_root: Path) -> tuple[Path, ...] | None:
    """Return the renderer-selected generated roster, or None without its opt-in.

    The existing generated-ordering marker declares ownership of the manuscript
    roster. Project-resolved configuration alone declares only config ownership;
    neither declaration establishes authorship or source-to-output freshness.
    This reader never refreshes config or otherwise invokes the render resolver.
    """

    manuscript_root = project_root / "output" / "manuscript"
    config = manuscript_root / "config.yaml"
    try:
        if not has_generated_manuscript_ordering(config):
            return None
        text = config.read_text(encoding="utf-8")
        _require_marker_comment(text, GENERATED_ORDERING_MARKER)
        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict) or not loaded:
            raise ValueError("generated manuscript config must be a non-empty mapping")
        _validate_ordering(_mapping(loaded, "config"), manuscript_root)
        if unresolved_config_tokens(config):
            raise ValueError("generated manuscript config contains unresolved hydration tokens")
        # Match resolve_manuscript_dir's selection without its config-copy side
        # effects. Nested-only/TeX-only output is not selected by that resolver.
        if not any(manuscript_root.glob("*.md")):
            raise ValueError("generated manuscript directory is not selected by the renderer")
        paths = tuple(discover_manuscript_files(manuscript_root))
        if not paths:
            raise ValueError("generated manuscript declaration selects no render inputs")
        root = manuscript_root.resolve(strict=True)
        root.relative_to(project_root.resolve(strict=True))
        config.resolve(strict=True).relative_to(root)
        for path in paths:
            path.resolve(strict=True).relative_to(root)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
        raise RenderedSnapshotError("GENERATED_MANUSCRIPT_INVALID", str(exc)) from exc
    return paths
