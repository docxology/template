"""Read exact bounded readiness artifact references from an existing snapshot."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_hosted_transport_archive import MAX_MEMBERS, MAX_TOTAL
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader, json_value_from_bytes


def artifact_graph_paths(
    root: Path, receipt: str, reader: SnapshotReader, *, deadline: float, strict_bindings: bool = False
) -> dict[str, str]:
    """Walk exact artifact bindings; preserve strict public or native payload labels."""
    pending: list[tuple[str, str | None, int | None]] = [(receipt, None, None)]
    paths: dict[str, str] = {}
    total = 0

    def walk(value: object, parent: Path) -> None:
        remaining(deadline)
        if isinstance(value, dict):
            path, digest = value.get("path"), value.get("sha256")
            sized = set(value) == {"path", "sha256", "bytes"}
            size = value.get("bytes") if sized else None
            if sized and (
                not isinstance(path, str) or not isinstance(digest, str) or type(size) is not int or size < 0
            ):
                raise ValueError("bundle sized artifact binding is malformed")
            exact = set(value) in (
                {"path", "sha256"},
                {"path", "sha256", "bytes"},
                {"path", "sha256", "width_px", "height_px", "variance"},
            )
            if isinstance(path, str) and isinstance(digest, str) and exact:
                label = Path(path)
                if strict_bindings:
                    pending.append((path, digest, size))
                elif label.is_absolute():
                    if label.is_relative_to(root):
                        pending.append((label.relative_to(root).as_posix(), digest, size))
                elif label.name == path and path.startswith("payload-"):
                    pending.append(((parent / path).relative_to(root).as_posix(), digest, size))
                else:
                    pending.append((path, digest, size))
            if isinstance(value.get("artifact"), str) and isinstance(value.get("artifact_sha256"), str):
                pending.append((value["artifact"], value["artifact_sha256"], None))
            for item in value.values():
                walk(item, parent)
        elif isinstance(value, list):
            for item in value:
                walk(item, parent)

    while pending:
        remaining(deadline)
        label, expected, expected_size = pending.pop()
        reader.public_path(label)
        prior = paths.get(label)
        if prior is not None and expected is not None and prior != expected:
            raise ValueError("candidate graph has conflicting exact artifact bindings")
        held = reader.read(label)
        remaining(deadline)
        if expected is not None and held.sha256 != expected:
            raise ValueError(
                "bundle artifact differs from its original reference"
                if strict_bindings
                else "candidate graph bytes differ from the verified binding"
            )
        if expected_size is not None and len(held.content) != expected_size:
            raise ValueError("bundle artifact differs from its original size")
        if not Path(label).is_relative_to("output/readiness"):
            continue
        if prior is not None:
            continue
        paths[label] = held.sha256
        total += len(held.content)
        if len(paths) > MAX_MEMBERS or total > MAX_TOTAL:
            raise ValueError("candidate evidence exceeds its Source-native whole-transport member/byte census")
        if label.endswith(".json"):
            from infrastructure.project.public_root_census_encoding import SCHEMA as CENSUS_ENCODING_SCHEMA, decode

            payload = json_value_from_bytes(held.content)
            if isinstance(payload, dict) and payload.get("schema_version") == CENSUS_ENCODING_SCHEMA:
                payload = decode(payload)
            walk(payload, held.path.parent)
        remaining(deadline)
        if not reader.unchanged():
            raise ValueError("candidate graph member changed during packing census")
        remaining(deadline)
    remaining(deadline)
    return paths
