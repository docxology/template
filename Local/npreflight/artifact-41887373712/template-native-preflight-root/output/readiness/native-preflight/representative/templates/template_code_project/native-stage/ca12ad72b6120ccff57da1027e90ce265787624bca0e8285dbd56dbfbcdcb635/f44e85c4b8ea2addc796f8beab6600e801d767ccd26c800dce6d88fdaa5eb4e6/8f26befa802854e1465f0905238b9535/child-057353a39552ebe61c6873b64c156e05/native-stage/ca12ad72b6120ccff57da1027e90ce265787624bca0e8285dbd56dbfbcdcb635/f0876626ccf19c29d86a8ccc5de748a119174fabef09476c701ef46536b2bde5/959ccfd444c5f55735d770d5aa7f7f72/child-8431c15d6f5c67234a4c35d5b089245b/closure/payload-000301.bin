"""Deterministic registries for figures emitted by project pipelines.

Project figure code owns the labels, filenames, captions, and generator names.
This module supplies the reusable fail-closed persistence step: every declared
figure must be present on disk before a registry can be written.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol


class FigureSpecLike(Protocol):
    """Structural contract for project-owned figure specifications."""

    @property
    def label(self) -> str:
        """Pandoc-crossref label, including the ``fig:`` prefix."""
        ...

    @property
    def filename(self) -> str:
        """Generated figure basename."""
        ...

    @property
    def caption(self) -> str:
        """Human-readable figure caption."""
        ...

    @property
    def generated_by(self) -> str:
        """Qualified source function or pipeline entry point."""
        ...


class FigureRegistryError(ValueError):
    """Raised when generated figures cannot satisfy their registry contract."""


def build_generated_figure_registry(
    specs: Iterable[FigureSpecLike],
    generated_paths: Iterable[Path],
    *,
    schema_version: str,
) -> dict[str, object]:
    """Build a deterministic registry after checking every declared figure.

    Args:
        specs: Project-owned figure specifications.
        generated_paths: Files produced by the current figure pipeline run.
        schema_version: Non-empty project registry schema identifier.

    Returns:
        An envelope-shaped registry accepted by the output validator.

    Raises:
        FigureRegistryError: If the schema, specifications, or generated files
            are incomplete, duplicated, or inconsistent.
    """
    if not schema_version.strip():
        raise FigureRegistryError("figure registry schema_version must not be empty")

    ordered_specs = sorted(tuple(specs), key=lambda spec: spec.label)
    if not ordered_specs:
        raise FigureRegistryError("figure registry must declare at least one figure")

    labels = [spec.label for spec in ordered_specs]
    filenames = [spec.filename for spec in ordered_specs]
    _require_unique(labels, "figure label")
    _require_unique(filenames, "figure filename")

    for spec in ordered_specs:
        if not spec.label.startswith("fig:"):
            raise FigureRegistryError(f"figure label must start with 'fig:': {spec.label!r}")
        if Path(spec.filename).name != spec.filename:
            raise FigureRegistryError(f"figure filename must be a basename: {spec.filename!r}")
        if not spec.caption.strip():
            raise FigureRegistryError(f"figure caption must not be empty: {spec.label}")
        if not spec.generated_by.strip():
            raise FigureRegistryError(f"figure generated_by must not be empty: {spec.label}")

    generated_by_name: dict[str, Path] = {}
    for raw_path in generated_paths:
        path = Path(raw_path)
        if path.name in generated_by_name:
            raise FigureRegistryError(f"duplicate generated figure filename: {path.name}")
        generated_by_name[path.name] = path

    missing = sorted(set(filenames) - set(generated_by_name))
    if missing:
        raise FigureRegistryError(f"missing generated figure file(s): {', '.join(missing)}")

    absent = sorted(filename for filename in filenames if not generated_by_name[filename].is_file())
    if absent:
        raise FigureRegistryError(f"generated figure path(s) do not exist: {', '.join(absent)}")

    def _record(spec: FigureSpecLike) -> dict[str, object]:
        record: dict[str, object] = {
            "caption": spec.caption,
            "filename": spec.filename,
            "generated_by": spec.generated_by,
            "label": spec.label,
        }
        alt_text = str(getattr(spec, "alt_text", "") or "").strip()
        if alt_text:
            record["metadata"] = {"alt_text": alt_text}
        return record

    return {
        "schema_version": schema_version,
        "figures": [_record(spec) for spec in ordered_specs],
    }


def write_generated_figure_registry(
    registry_path: Path,
    specs: Iterable[FigureSpecLike],
    generated_paths: Iterable[Path],
    *,
    schema_version: str,
) -> Path:
    """Validate generated files and atomically write their registry JSON."""
    payload = build_generated_figure_registry(
        specs,
        generated_paths,
        schema_version=schema_version,
    )
    path = Path(registry_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


def publish_generated_figures(
    output_dir: Path,
    specs: Iterable[FigureSpecLike],
    generated_paths: Iterable[Path],
    *,
    schema_version: str,
) -> list[Path]:
    """Validate, mirror, and register a complete generated figure set.

    The source set is validated before the destination directory is created,
    so an incomplete analysis run cannot publish a partial registry. Extra
    generated files (for example unreferenced cover art) are mirrored but are
    not represented as manuscript evidence unless a project spec declares them.
    """
    declared = tuple(specs)
    generated = tuple(Path(path) for path in generated_paths)
    build_generated_figure_registry(declared, generated, schema_version=schema_version)
    destination_dir = Path(output_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    mirrored: list[Path] = []
    for source in generated:
        destination = destination_dir / source.name
        if source.resolve() != destination.resolve():
            shutil.copy2(source, destination)
        mirrored.append(destination)
    registry = write_generated_figure_registry(
        destination_dir / "figure_registry.json",
        declared,
        mirrored,
        schema_version=schema_version,
    )
    return [*mirrored, registry]


def _require_unique(values: list[str], description: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise FigureRegistryError(f"duplicate {description}(s): {', '.join(duplicates)}")


__all__ = [
    "FigureRegistryError",
    "FigureSpecLike",
    "build_generated_figure_registry",
    "publish_generated_figures",
    "write_generated_figure_registry",
]
