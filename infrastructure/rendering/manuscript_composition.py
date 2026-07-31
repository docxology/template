"""Render-boundary evidence for ordered manuscript composition."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from infrastructure.core.files.secure_write import atomic_write_text_confined
from infrastructure.core.pipeline.artifacts import compute_sha256
from infrastructure.core.project_paths import resolve_source_manuscript_dir

SCHEMA_VERSION = "template-manuscript-composition-v1"
COMPOSITION_RELATIVE_PATH = Path("output/reports/manuscript_composition.json")
COMBINED_RELATIVE_PATH = Path("output/web/_combined_manuscript.md")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class CompositionInput:
    """One ordered input consumed by the combined renderer."""

    ordinal: int
    path: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class ManuscriptComposition:
    """Exact ordered inputs and combined Markdown emitted at render time."""

    project: str
    input_root_kind: str
    ordered_inputs: tuple[CompositionInput, ...]
    ordered_inputs_sha256: str
    combined_path: str
    combined_size_bytes: int
    combined_sha256: str
    binding_sha256: str
    schema_version: str = SCHEMA_VERSION
    algorithm: str = "web-renderer-combine-v1"

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "schema_version": self.schema_version,
            "algorithm": self.algorithm,
            "project": self.project,
            "input_root_kind": self.input_root_kind,
            "ordered_inputs": [asdict(row) for row in self.ordered_inputs],
            "ordered_inputs_sha256": self.ordered_inputs_sha256,
            "combined_path": self.combined_path,
            "combined_size_bytes": self.combined_size_bytes,
            "combined_sha256": self.combined_sha256,
            "binding_sha256": self.binding_sha256,
        }


def _digest_rows(rows: tuple[CompositionInput, ...]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update(f"{row.ordinal}\0{row.path}\0{row.size_bytes}\0{row.sha256}\n".encode())
    return digest.hexdigest()


def _binding_digest(ordered_inputs_sha256: str, combined_path: str, combined_sha256: str) -> str:
    payload = f"{ordered_inputs_sha256}\0{combined_path}\0{combined_sha256}\n"
    return hashlib.sha256(payload.encode()).hexdigest()


def _relative_confined(project_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except (OSError, ValueError) as exc:
        raise ValueError(f"composition path escapes project: {path}") from exc


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError):
        return False
    return True


def build_manuscript_composition(
    project_root: Path,
    project: str,
    ordered_inputs: list[Path],
    combined_path: Path,
) -> ManuscriptComposition:
    """Build render-boundary evidence from the exact inputs just consumed."""
    expected_combined = project_root / COMBINED_RELATIVE_PATH
    if combined_path.absolute() != expected_combined.absolute():
        raise ValueError(f"combined composition path must be {COMBINED_RELATIVE_PATH.as_posix()}")
    if not ordered_inputs:
        raise ValueError("combined manuscript requires at least one ordered input")

    hydrated_root = project_root / "output" / "manuscript"
    source_root = resolve_source_manuscript_dir(project_root)
    if all(_is_within(path, hydrated_root) for path in ordered_inputs):
        input_root_kind = "hydrated"
    elif all(_is_within(path, source_root) for path in ordered_inputs):
        input_root_kind = "source"
    else:
        raise ValueError("composition inputs must all belong to one canonical source or hydrated root")
    rows = tuple(
        CompositionInput(
            ordinal=index,
            path=_relative_confined(project_root, path),
            size_bytes=path.stat().st_size,
            sha256=compute_sha256(path),
        )
        for index, path in enumerate(ordered_inputs, 1)
    )
    combined_relative = _relative_confined(project_root, combined_path)
    ordered_digest = _digest_rows(rows)
    combined_digest = compute_sha256(combined_path)
    return ManuscriptComposition(
        project=project,
        input_root_kind=input_root_kind,
        ordered_inputs=rows,
        ordered_inputs_sha256=ordered_digest,
        combined_path=combined_relative,
        combined_size_bytes=combined_path.stat().st_size,
        combined_sha256=combined_digest,
        binding_sha256=_binding_digest(ordered_digest, combined_relative, combined_digest),
    )


def write_manuscript_composition(
    project_root: Path,
    project: str,
    ordered_inputs: list[Path],
    combined_path: Path,
) -> ManuscriptComposition:
    """Write deterministic evidence at the actual web composition boundary."""
    composition = build_manuscript_composition(project_root, project, ordered_inputs, combined_path)
    target = project_root / COMPOSITION_RELATIVE_PATH
    content = json.dumps(composition.to_dict(), indent=2, sort_keys=True) + "\n"
    atomic_write_text_confined(project_root, target, content)
    return composition


def _required_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"composition {key} must be a non-empty string")
    return value


def _required_sha256(payload: Mapping[str, object], key: str) -> str:
    value = _required_string(payload, key)
    if _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"composition {key} must be 64 lowercase hexadecimal characters")
    return value


def _required_relative_path(payload: Mapping[str, object], key: str) -> str:
    value = _required_string(payload, key)
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts or candidate.as_posix() != value:
        raise ValueError(f"composition {key} must be a canonical relative path")
    return value


def read_manuscript_composition(path: Path) -> ManuscriptComposition:
    """Strictly parse one composition evidence file."""
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("composition evidence must be a mapping")
    expected = {
        "schema_version",
        "algorithm",
        "project",
        "input_root_kind",
        "ordered_inputs",
        "ordered_inputs_sha256",
        "combined_path",
        "combined_size_bytes",
        "combined_sha256",
        "binding_sha256",
    }
    if set(payload) != expected:
        raise ValueError("composition evidence has missing or unknown fields")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"composition schema_version must be {SCHEMA_VERSION}")
    if payload.get("algorithm") != "web-renderer-combine-v1":
        raise ValueError("composition algorithm is unsupported")
    root_kind = payload.get("input_root_kind")
    if root_kind not in {"source", "hydrated"}:
        raise ValueError("composition input_root_kind must be source or hydrated")
    raw_inputs = payload.get("ordered_inputs")
    if not isinstance(raw_inputs, list) or not raw_inputs:
        raise ValueError("composition ordered_inputs must be a non-empty list")
    rows: list[CompositionInput] = []
    for expected_ordinal, raw in enumerate(raw_inputs, 1):
        if not isinstance(raw, Mapping) or set(raw) != {"ordinal", "path", "size_bytes", "sha256"}:
            raise ValueError("composition input row has missing or unknown fields")
        ordinal = raw.get("ordinal")
        size_bytes = raw.get("size_bytes")
        if ordinal != expected_ordinal:
            raise ValueError("composition input ordinals must be contiguous and ordered")
        if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes < 0:
            raise ValueError("composition input size_bytes must be non-negative")
        rows.append(
            CompositionInput(
                ordinal=expected_ordinal,
                path=_required_relative_path(raw, "path"),
                size_bytes=size_bytes,
                sha256=_required_sha256(raw, "sha256"),
            )
        )
    combined_size_bytes = payload.get("combined_size_bytes")
    if not isinstance(combined_size_bytes, int) or isinstance(combined_size_bytes, bool) or combined_size_bytes < 0:
        raise ValueError("composition combined_size_bytes must be non-negative")
    composition = ManuscriptComposition(
        project=_required_string(payload, "project"),
        input_root_kind=root_kind,
        ordered_inputs=tuple(rows),
        ordered_inputs_sha256=_required_sha256(payload, "ordered_inputs_sha256"),
        combined_path=_required_relative_path(payload, "combined_path"),
        combined_size_bytes=combined_size_bytes,
        combined_sha256=_required_sha256(payload, "combined_sha256"),
        binding_sha256=_required_sha256(payload, "binding_sha256"),
    )
    prefixes = (
        ("output/manuscript/",) if composition.input_root_kind == "hydrated" else ("manuscript/", "docs/manuscript/")
    )
    matching_roots = [
        prefix for prefix in prefixes if all(row.path.startswith(prefix) for row in composition.ordered_inputs)
    ]
    if len(matching_roots) != 1:
        raise ValueError(f"composition {composition.input_root_kind} inputs must all use one canonical manuscript root")
    if composition.combined_path != COMBINED_RELATIVE_PATH.as_posix():
        raise ValueError(f"composition combined_path must be {COMBINED_RELATIVE_PATH.as_posix()}")
    if composition.ordered_inputs_sha256 != _digest_rows(composition.ordered_inputs):
        raise ValueError("composition ordered input digest is inconsistent")
    if composition.binding_sha256 != _binding_digest(
        composition.ordered_inputs_sha256,
        composition.combined_path,
        composition.combined_sha256,
    ):
        raise ValueError("composition binding digest is inconsistent")
    return composition


__all__ = [
    "COMBINED_RELATIVE_PATH",
    "COMPOSITION_RELATIVE_PATH",
    "CompositionInput",
    "ManuscriptComposition",
    "build_manuscript_composition",
    "read_manuscript_composition",
    "write_manuscript_composition",
]
