"""Typed, fail-closed validation for fonds, rules, and tools manifests."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

REQUIRED_MANIFEST_KEYS = ("type", "description", "version", "license")


def validate_resource_manifest(manifest: object, resource_kind: str) -> tuple[str, ...]:
    """Validate one manifest without importing or executing the resource."""
    if not isinstance(manifest, Mapping):
        return ("manifest must be a mapping",)
    issues = [
        f"missing required manifest key: {key}"
        for key in REQUIRED_MANIFEST_KEYS
        if key not in manifest
    ]
    for key in ("description", "version", "license"):
        if key in manifest and (not isinstance(manifest[key], str) or not manifest[key].strip()):
            issues.append(f"manifest {key} must be non-empty")
    allowed_types = {
        "fond": {"bibliography", "contacts", "datasets"},
        "rules": {"project", "manuscript"},
        "tools": None,
    }.get(resource_kind)
    if allowed_types is None and resource_kind == "tools":
        if not isinstance(manifest.get("type"), str) or not str(manifest.get("type", "")).strip():
            issues.append("tool manifest type must be non-empty")
    elif allowed_types is None:
        issues.append(f"unknown resource kind: {resource_kind}")
    elif manifest.get("type") not in allowed_types:
        issues.append(f"manifest type {manifest.get('type')!r} is not valid for {resource_kind}")
    tags = manifest.get("tags")
    if tags is not None and (
        not isinstance(tags, list) or not all(isinstance(tag, str) and tag.strip() for tag in tags)
    ):
        issues.append("manifest tags must be a list of non-empty strings")
    if resource_kind == "tools":
        entrypoints = manifest.get("entrypoints")
        if (
            not isinstance(entrypoints, list)
            or not entrypoints
            or not all(isinstance(item, str) and item.strip() for item in entrypoints)
        ):
            issues.append("tool manifest entrypoints must be a non-empty string list")
    return tuple(issues)


def validate_resource_directory(path: Path, resource_kind: str) -> tuple[str, ...]:
    """Validate a resource directory's manifest and declared files."""
    root = Path(path)
    manifest_name = {
        "fond": "fonds.yaml",
        "rules": "rules.yaml",
        "tools": "tools.yaml",
    }.get(resource_kind)
    if manifest_name is None:
        return (f"unknown resource kind: {resource_kind}",)
    manifest_path = root / manifest_name
    if not manifest_path.is_file():
        return (f"missing {manifest_name}",)
    try:
        import yaml

        manifest: object = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        return (f"cannot read {manifest_name}: {exc}",)
    issues = list(validate_resource_manifest(manifest, resource_kind))
    if resource_kind == "tools" and isinstance(manifest, Mapping):
        entrypoints = manifest.get("entrypoints")
        if not isinstance(entrypoints, list):
            return tuple(issues)
        for entrypoint in entrypoints:
            if not isinstance(entrypoint, str):
                continue
            candidate = root / entrypoint
            if candidate.is_symlink():
                issues.append(f"symlinked tool entrypoint is not allowed: {entrypoint}")
                continue
            resolved = candidate.resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                issues.append(f"entrypoint escapes resource root: {entrypoint}")
            else:
                if not resolved.is_file():
                    issues.append(f"missing tool entrypoint: {entrypoint}")
    return tuple(issues)


def build_resource_schema_receipt(resources: list[tuple[str, Path, str]]) -> dict[str, object]:
    """Return a deterministic receipt for a resource manifest inventory."""
    rows: list[dict[str, object]] = []
    for name, path, kind in sorted(resources, key=lambda row: row[0]):
        issues = validate_resource_directory(path, kind)
        rows.append(
            {
                "name": name,
                "kind": kind,
                "status": "pass" if not issues else "fail",
                "issues": list(issues),
            }
        )
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "schema_version": "template-pools-resource-schema-receipt-v1",
        "resource_count": len(rows),
        "status": "pass" if rows and all(row["status"] == "pass" for row in rows) else "fail",
        "resources": rows,
        "digest": hashlib.sha256(canonical).hexdigest(),
    }


__all__ = [
    "REQUIRED_MANIFEST_KEYS",
    "build_resource_schema_receipt",
    "validate_resource_directory",
    "validate_resource_manifest",
]
