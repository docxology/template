"""Exact Source-selected standalone TeX inputs in an owned reference tree.

Consumed hydration and generated images remain data. Their independent
production predicates belong to the enclosing complete Source graph.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.core.pipeline.fingerprints import tree_records
from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader
from infrastructure.transmission.transmission_bookends import is_transmission_bookend
from infrastructure.validation.output.render_formats import render_config_manuscript_dir
from infrastructure.validation.publication.rendered_provenance import validate_current_rendered_provenance


@dataclass(frozen=True)
class TexSectionInputs:
    """Frozen data selected by the live Source owner, never a receipt capability."""

    tex: Path
    compiler: str
    files: tuple[tuple[ArtifactSnapshot, ArtifactSnapshot, str], ...]
    directories: tuple[tuple[Path, tuple[tuple[str, str, str], ...]], ...]

    def manifest(self) -> list[dict[str, Any]]:
        return [
            {
                "path": original.relative,
                "role": role,
                "sha256": original.sha256,
                "bytes": len(original.content),
                "frozen": {"path": frozen.relative, "sha256": frozen.sha256},
            }
            for original, frozen, role in self.files
        ]

    def unchanged(self, reader: SnapshotReader, *, deadline: float) -> None:
        for directory, expected in self.directories:
            remaining(deadline)
            if tree_records(directory) != expected:
                raise ValueError("section Source input directory/name/body inventory changed")
        if not reader.unchanged():
            raise ValueError("section held Source/frozen inputs changed during compilation")
        remaining(deadline)


def freeze_tex_section_inputs(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
) -> TexSectionInputs:
    """Preserve authored and consumed manuscript/figure paths without rewriting TeX."""
    owner = current_native_producer_operation()
    if (
        owner is None
        or owner.source.bindings.current_root != root
        or reader.root != root
        or reader.native_producer_operation is not owner
        or owner.deadline != deadline
        or scope not in PUBLIC_PROJECT_NAMES
        or artifact.format != "pdf"
        or not artifact.id.startswith("section:")
        or not artifact.id.endswith(":pdf")
    ):
        raise ValueError("section input selection requires its genuine live Source owner")
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    if not validate_current_rendered_provenance(root, scope).valid:
        raise ValueError("section reference requires validated consumed hydration")
    project = root / "projects" / scope
    authored = resolve_source_manuscript_dir(project)
    consumed = render_config_manuscript_dir(project)
    name = artifact.id.removeprefix("section:").removesuffix(":pdf")
    selected = [path for path in discover_manuscript_files(consumed) if path.relative_to(consumed).as_posix() == name]
    if (
        len(selected) != 1
        or selected[0].suffix != ".tex"
        or is_transmission_bookend(selected[0])
        or artifact.path != f"projects/{scope}/output/pdf/{selected[0].stem}.pdf"
    ):
        raise ValueError("section reference differs from the exact current declared TeX artifact")
    config = reader.read((consumed / "config.yaml").relative_to(root).as_posix())
    parsed = yaml.safe_load(config.content)
    if not isinstance(parsed, dict):
        raise ValueError("section consumed render configuration is not a mapping")
    compiler = RenderingConfig.from_project_config(parsed, env=env).latex_compiler
    if compiler not in {"xelatex", "lualatex", "pdflatex"}:
        raise ValueError("section reference requires a supported Source-selected direct PDF TeX engine")
    directories = []
    held: dict[str, tuple[ArtifactSnapshot, ArtifactSnapshot, str]] = {}
    total = 0
    for base, role in (
        (authored, "authored"),
        (consumed, "consumed"),
        (project / "output/figures", "generated-figure"),
        (project / "output/audit_figures", "generated-audit-figure"),
    ):
        remaining(deadline)
        records = tree_records(base)
        directories.append((base, records))
        for relative, kind, digest in records:
            remaining(deadline)
            if kind in {"missing", "directory"}:
                continue
            if kind != "file":
                raise ValueError("section inputs contain an unsupported link or filesystem type")
            path = base if relative == "." else base / relative
            original = reader.read(path.relative_to(root).as_posix())
            if original.sha256 != digest:
                raise ValueError("section input changed during exact frozen selection")
            if role == "authored" and original.content != owner.source.reference.read(original.relative):
                raise ValueError("section authored input differs from the independently held Source")
            if original.relative in held:
                # Conventional nonhydrated rendering can select the authored
                # directory directly. One held file retains both roles.
                previous = held[original.relative]
                held[original.relative] = (previous[0], previous[1], "authored-consumed")
                continue
            total += len(original.content)
            if len(held) >= 10000 or total > 128 * 1024 * 1024:
                raise ValueError("section reference input tree exceeds its bounded native byte/entry budget")
            target = directory / "source" / original.relative
            atomic_write_bytes_confined(root, target, original.content, mode=0o600)
            frozen = reader.read(target.relative_to(root).as_posix())
            if frozen.content != original.content:
                raise ValueError("section frozen input differs from exact consumed bytes")
            held[original.relative] = original, frozen, role
    tex = directory / "source" / selected[0].relative_to(root)
    if not tex.is_file():
        raise ValueError("section reference omitted its selected consumed TeX")
    result = TexSectionInputs(tex, compiler, tuple(held[key] for key in sorted(held)), tuple(directories))
    result.unchanged(reader, deadline=deadline)
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    return result
